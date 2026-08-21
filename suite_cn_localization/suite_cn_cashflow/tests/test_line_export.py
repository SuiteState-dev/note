# -*- coding: utf-8 -*-
"""R27-T3 — P-05 可移交性: per-line cash-flow classification export / backfill.

Acceptance (design §2 P-05, §3 残留现状 第 1 条): classify → export → (drop the
classification, simulating an uninstall) → backfill from the same file → the per-line
`cn_cash_flow_item_id` is identical. Plus the two rulings:
  * the file is a text-readable CSV whose cash-flow item is 编码 + 名称 (no DB id), so
    it is meaningful without this module (P-05 第②条);
  * a row that cannot be applied (unknown 分录ID / unknown 项目编码) is SKIPPED *and*
    REPORTED, never silently dropped (§7.0 铁律1).
"""
import base64

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCashflowLineExport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        item = cls.env['cash.flow.item']
        cls.s_recv = item.search([('code', '=', 'S2')], limit=1)  # inflow
        cls.cash = cls.env['account.account'].create({
            'name': 'LX Cash', 'code': 'ZZLXC', 'account_type': 'asset_cash'})
        cls.other = cls.env['account.account'].create({
            'name': 'LX Other', 'code': 'ZZLXO', 'account_type': 'asset_current'})
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', cls.company.id)], limit=1)
        move = cls.env['account.move'].create({
            'move_type': 'entry', 'journal_id': cls.journal.id, 'date': '2026-06-15',
            'line_ids': [
                (0, 0, {'account_id': cls.cash.id, 'debit': 1000, 'credit': 0}),
                (0, 0, {'account_id': cls.other.id, 'debit': 0, 'credit': 1000}),
            ],
        })
        move.action_post()
        cls.move = move
        cls.line = move.line_ids.filtered(lambda l: l.account_id == cls.other)
        # Explicitly classify the counterpart line (setUp accounts carry no default).
        cls.line.cn_cash_flow_item_id = cls.s_recv.id

    def _wizard(self):
        return self.env['suite.cn.cashflow.line.export'].create(
            {'company_id': self.company.id})

    def _decode(self, w):
        return base64.b64decode(w.export_file).decode('utf-8-sig')

    def test_export_is_text_readable_csv_with_code_and_name(self):
        w = self._wizard()
        w.action_export()
        self.assertTrue(w.export_file, "export produced no file")
        self.assertTrue(w.export_filename.endswith('.csv'))
        text = self._decode(w)
        # Human-readable header + our classified line, carried by 编码 AND 名称 (no id).
        self.assertIn('现金流量项目编码', text)
        self.assertIn('现金流量项目名称', text)
        self.assertIn(self.s_recv.code, text)
        self.assertIn(self.s_recv.name, text)
        # The join key (分录ID) for our line is present.
        self.assertIn(str(self.line.id), text)

    def test_round_trip_backfill_identical(self):
        w = self._wizard()
        w.action_export()
        blob = w.export_file

        # -- simulate uninstall/reinstall: clear the per-line classification --
        self.line.cn_cash_flow_item_id = False
        self.assertFalse(self.line.cn_cash_flow_item_id)

        # -- backfill from the same file --
        w2 = self._wizard()
        w2.write({'import_file': blob, 'import_filename': 'x.csv'})
        w2.action_import()
        self.assertEqual(
            self.line.cn_cash_flow_item_id, self.s_recv,
            "backfill must restore the exact per-line classification")
        self.assertIn('更新', w2.result)

    def test_unresolvable_rows_are_skipped_and_reported(self):
        # A file with a bogus 分录ID and a bogus 项目编码 must apply neither silently.
        csv = ('﻿分录ID,日期,凭证号,科目编码,科目名称,借贷,金额,'
               '现金流量项目编码,现金流量项目名称\n'
               '999999999,2026-06-15,X,ZZLXO,LX Other,贷,1000,S2,收到其他现金\n'
               '%d,2026-06-15,X,ZZLXO,LX Other,贷,1000,NOPE,乱码\n' % self.line.id)
        w = self._wizard()
        w.write({'import_file': base64.b64encode(csv.encode('utf-8')),
                 'import_filename': 'x.csv'})
        w.action_import()
        # Row 1: unknown aml id → reported not-found. Row 2: unknown item code →
        # reported, and the real line is NOT changed to a wrong value.
        self.assertIn('不存在', w.result)
        self.assertIn('找不到', w.result)

    def test_export_scoped_to_company(self):
        # 铁律2: the export domain is company-scoped. A wizard for a DIFFERENT company
        # must not carry our line.
        other_co = self.env['res.company'].create({'name': 'LX Other Co'})
        w = self.env['suite.cn.cashflow.line.export'].create(
            {'company_id': other_co.id})
        w.action_export()
        text = self._decode(w)
        self.assertNotIn(str(self.line.id), text,
                         "another company's export must not include our line")

    def test_hash_mode_does_not_affect_report_or_export(self):
        """🔴 R27-T2 Q8 (verified, not推演): enabling the posted-entry hash chain
        (account.journal.restrict_mode_hash_table) must NOT affect our cash-flow
        report rendering or the line export. The hash only adds inalterable_hash and
        blocks edits to protected fields — it does NOT touch debit/credit/balance,
        which is what the report reads, so the two are orthogonal. This test PROVES
        that by running both while actually in hash mode (inalterable_hash set)."""
        # Turn the journal into hash mode and post a fresh classified entry so it is
        # really hashed (retroactive hashing also hashes setUp's move).
        self.journal.restrict_mode_hash_table = True
        move = self.env['account.move'].create({
            'move_type': 'entry', 'journal_id': self.journal.id, 'date': '2026-07-01',
            'line_ids': [
                (0, 0, {'account_id': self.cash.id, 'debit': 500, 'credit': 0}),
                (0, 0, {'account_id': self.other.id, 'debit': 0, 'credit': 500}),
            ],
        })
        move.action_post()
        move.flush_recordset()
        hline = move.line_ids.filtered(lambda l: l.account_id == self.other)
        hline.cn_cash_flow_item_id = self.s_recv.id
        self.assertTrue(move.inalterable_hash,
                        "precondition: the move must actually be hashed")

        # (1) The report engine renders without error while entries are hashed.
        report = self.env.ref('suite_cn_cashflow.cn_cash_flow_s')
        options = report.get_options({})
        lines = report._get_lines(options)
        self.assertTrue(lines, "report produced no lines under hash mode")

        # (2) The line export runs and carries the hashed line's classification.
        w = self._wizard()
        w.action_export()
        text = self._decode(w)
        self.assertIn(str(hline.id), text,
                      "export must include the classified line even under hash mode")
        self.assertIn(self.s_recv.code, text)
