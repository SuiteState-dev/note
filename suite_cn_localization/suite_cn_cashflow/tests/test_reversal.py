# -*- coding: utf-8 -*-
"""R23-T5-1 — a reversal keeps the original cash-flow classification.

Root-cause guard, asserted at the journal-item level (portable — no CN report /
chart needed): reversing an entry must copy each line's `cn_cash_flow_item_id`
onto the reversal line and NOT re-derive it from the flipped debit/credit sign.
Without the guard a reversed 收到其他现金 (credit → S2) flips to a debit and
re-derives to the debit-side default (S6), so the original inflow is never undone
AND a phantom outflow appears — net is right, the two line totals are not.
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReversalKeepsClassification(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        item = cls.env['cash.flow.item']
        # Global (company-less) statutory items shipped by the module.
        cls.s_recv = item.search([('code', '=', 'S2')], limit=1)  # 收到其他现金 (inflow)
        cls.s_pay = item.search([('code', '=', 'S6')], limit=1)   # 支付其他现金 (outflow)
        cls.cash = cls.env['account.account'].create({
            'name': 'Test Cash', 'code': 'ZZCASH', 'account_type': 'asset_cash',
        })
        # Double-direction account: DEBIT default S6, CREDIT default S2 — so a
        # re-derivation after the reversal's sign flip would visibly change S2→S6.
        cls.other = cls.env['account.account'].create({
            'name': 'Test Other', 'code': 'ZZOTHER', 'account_type': 'asset_current',
            'cn_default_cash_flow_item_debit_id': cls.s_pay.id,
            'cn_default_cash_flow_item_credit_id': cls.s_recv.id,
        })
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', cls.company.id)], limit=1)

    def test_reversal_keeps_original_item(self):
        # Receipt: Dr Cash 1000 / Cr Other 1000 — the Other line is on the credit
        # side, so it auto-fills the credit default S2.
        move = self.env['account.move'].create({
            'move_type': 'entry', 'journal_id': self.journal.id, 'date': '2026-06-15',
            'line_ids': [
                (0, 0, {'account_id': self.cash.id, 'debit': 1000, 'credit': 0}),
                (0, 0, {'account_id': self.other.id, 'debit': 0, 'credit': 1000}),
            ],
        })
        move.action_post()
        orig = move.line_ids.filtered(lambda l: l.account_id == self.other)
        self.assertEqual(orig.cn_cash_flow_item_id, self.s_recv,
                         "receipt counterpart should auto-fill the credit default S2")

        reversal = move._reverse_moves(default_values_list=[{'date': '2026-06-20'}])
        reversal.action_post()
        rev_line = reversal.line_ids.filtered(lambda l: l.account_id == self.other)

        # The reversal line flipped to the DEBIT side; without the guard it would
        # re-derive to the debit default S6. The guard keeps the copied S2.
        self.assertEqual(
            rev_line.cn_cash_flow_item_id, self.s_recv,
            "reversal must keep the original classification (S2), not re-derive to "
            "the opposite-side default (S6) — otherwise the statement double-inflates")
        self.assertEqual(rev_line.balance, 1000.0, "reversal line balance is flipped")

    def test_manual_direction_edit_still_re_derives(self):
        # Guard boundary: a NON-reversal line must still follow account+direction.
        # Editing an ordinary auto-filled line's direction re-derives as before.
        move = self.env['account.move'].create({
            'move_type': 'entry', 'journal_id': self.journal.id, 'date': '2026-06-15',
            'line_ids': [
                (0, 0, {'account_id': self.cash.id, 'debit': 0, 'credit': 1000}),
                (0, 0, {'account_id': self.other.id, 'debit': 1000, 'credit': 0}),
            ],
        })
        line = move.line_ids.filtered(lambda l: l.account_id == self.other)
        # Debit side → debit default S6.
        self.assertEqual(line.cn_cash_flow_item_id, self.s_pay)
        # Flip to credit (ordinary edit, not a reversal) → re-derives to S2.
        move.write({'line_ids': [
            (1, line.id, {'debit': 0, 'credit': 1000, 'balance': -1000, 'amount_currency': -1000}),
            (1, (move.line_ids - line).id, {'debit': 1000, 'credit': 0, 'balance': 1000, 'amount_currency': 1000}),
        ]})
        self.assertEqual(line.cn_cash_flow_item_id, self.s_recv,
                         "an ordinary direction edit must still re-derive (guard is "
                         "reversal-only)")
