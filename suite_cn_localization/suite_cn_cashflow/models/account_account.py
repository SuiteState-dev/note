# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    # -- Direction-split defaults (R22-T1) -------------------------------------
    # A double-direction account carries a DIFFERENT cash-flow item on its debit
    # and credit sides. Verified from the 金蝶 266-科目 export, which ships
    # `debitcashflow.name` / `creditcashflow.name` as two independent fields
    # (231 accounts configured): e.g. 1124 预付账款 = 支付其他与经营活动有关的现金
    # on the debit side, 收到其他与经营活动有关的现金 on the credit side. A
    # single-direction account simply carries the same item on both sides.
    cn_default_cash_flow_item_debit_id = fields.Many2one(
        'cash.flow.item', string='Default Cash Flow Item (Debit)',
        help="Pre-filled on a journal item of this account whose balance is on "
             "the DEBIT side (balance >= 0). For a single-direction account, set "
             "the same item on both the debit and the credit field.")
    cn_default_cash_flow_item_credit_id = fields.Many2one(
        'cash.flow.item', string='Default Cash Flow Item (Credit)',
        help="Pre-filled on a journal item of this account whose balance is on "
             "the CREDIT side (balance < 0). For a single-direction account, set "
             "the same item on both the debit and the credit field.")

    # The deprecated single field `cn_default_cash_flow_item_id` (R22-T1, kept one
    # release for the value-preserving 19.0.1.5.0 migration) was removed in
    # 19.0.1.7.0 (R23-T5-3); its column is dropped by that version's pre-migration.

    @api.constrains('cn_default_cash_flow_item_debit_id',
                    'cn_default_cash_flow_item_credit_id',
                    'account_type')
    def _check_cn_default_cash_flow_item(self):
        """A cash/bank account must never carry a default item on EITHER side:
        the statement classifies the *counterpart* line, not the cash line
        itself. Setting a default here would double-count the cash movement
        (R11-T1/P2; extended R22-T1 to both direction fields)."""
        for acc in self:
            if acc.account_type == 'asset_cash' and (
                    acc.cn_default_cash_flow_item_debit_id
                    or acc.cn_default_cash_flow_item_credit_id):
                raise ValidationError(_(
                    "A cash/bank account must not carry a default Cash Flow Item: "
                    "the statement classifies the counterpart line, not the cash "
                    "line."))
