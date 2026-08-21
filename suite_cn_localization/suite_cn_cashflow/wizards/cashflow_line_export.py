# -*- coding: utf-8 -*-
"""P-05 可移交性 — 分录级现金流量项目归属 的导出 / 回填通道 (R27-T3).

Distinct from `cashflow_config` (R25-T3), which round-trips the *configuration*
(cash.flow.item master + per-account defaults). THIS wizard round-trips the
*transaction-level classification* itself — i.e. WHICH journal item carries WHICH
cash-flow item (`account.move.line.cn_cash_flow_item_id`).

Why a dedicated channel (design §2 P-05, §3 残留现状第 1 条):
  `cn_cash_flow_item_id` is a real column added to `account.move.line`. Uninstalling
  DROPS it (see the module ``uninstall_hook``), so the per-line classifications are
  lost irreversibly — this is the ONE dimension this suite adds that, until now, had
  no export channel of its own. R25 argued the native list export covered it; that is
  true for an ad-hoc dump but is NOT a channel the *product* provides, and it does not
  survive an uninstall/reinstall round-trip on the same DB without the user knowing to
  do it first. 财会〔2024〕12号 §41 makes providing a data-export interface a statutory
  obligation on the software service provider (用户数据归用户所有，不得拒绝导出请求),
  so P-05 here is not merely self-imposed. This closes the last P-05 gap.

Format = CSV (UTF-8 with BOM), NOT xlsx — the acceptance rule (task §6.3-T3) is
「导出件用文本编辑器打开可读」, and an xlsx is a binary zip. A BOM'd UTF-8 CSV opens
correctly in a plain text editor AND in Excel (Chinese intact), and any other system
can read it. The cash-flow item travels as 编码 + 名称 (双列), never as a DB id, so the
file is meaningful without this module installed (P-05 第②条).

Re-import (回填) join key = 分录ID (the `account.move.line` id). It is stable across an
uninstall→reinstall on the SAME database (uninstall only drops the column; the aml rows
and their ids are untouched — that is the exact disaster this closes). Across a DIFFERENT
database the ids differ, so the file stays human-readable but is not auto-importable
there; that limitation is documented in the README. Import only BACKFILLS the
classification onto existing lines — it never creates journal items — and reports every
row it could not apply (aml not found / wrong company / item code unknown): a silent skip
would be as wrong as a silent overwrite (§7.0 铁律1：检查跑了 ≠ 有人看见).
"""
import base64
import csv
import io
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# CSV header (Chinese, human + foreign-system readable). 分录ID first = the re-import
# join key; the rest give a human enough context to eyeball a row without this module.
_COLS = ['分录ID', '日期', '凭证号', '科目编码', '科目名称',
         '借贷', '金额', '现金流量项目编码', '现金流量项目名称']


class CashflowLineExport(models.TransientModel):
    _name = 'suite.cn.cashflow.line.export'
    _description = 'Cash Flow Line Classification Export / Backfill (P-05 可移交性)'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company,
        help="导出/回填以此公司口径。多公司环境下请确认选的是中国公司"
             "(默认公司可能非中国)。")
    date_from = fields.Date(
        string='Date From',
        help="可选。留空=不限起始日期。按分录日期(date)过滤。")
    date_to = fields.Date(
        string='Date To', help="可选。留空=不限结束日期。")

    # -- export side --
    export_file = fields.Binary(string='Export File', readonly=True, attachment=False)
    export_filename = fields.Char(readonly=True)

    # -- import side --
    import_file = fields.Binary(string='Import File')
    import_filename = fields.Char()
    result = fields.Text(string='Result', readonly=True)

    # ------------------------------------------------------------------ helpers
    def _line_domain(self):
        """Journal items carrying a cash-flow classification, in this company/range.
        Only classified lines are exported — an un-tagged line has nothing to carry
        away and re-derives from the account default on reinstall anyway."""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('cn_cash_flow_item_id', '!=', False),
        ]
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        return domain

    def _find_item(self, code):
        """Cash-flow item by code, global or this company's (mirrors R25 wizard).
        active_test=False so an archived-but-referenced item still resolves."""
        code = (str(code).strip() if code is not None else '')
        if not code:
            return self.env['cash.flow.item']
        return self.env['cash.flow.item'].with_context(active_test=False).search(
            ['&', ('code', '=', code),
             '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)],
            limit=1)

    # ------------------------------------------------------------------ export
    def action_export(self):
        self.ensure_one()
        lines = self.env['account.move.line'].search(
            self._line_domain(), order='date, move_id, id')
        # csv writer → text buffer → utf-8-sig bytes (BOM) so Excel shows 中文 and a
        # plain text editor reads it too.
        sio = io.StringIO()
        writer = csv.writer(sio)
        writer.writerow(_COLS)
        for line in lines:
            debit, credit = line.debit, line.credit
            if debit and not credit:
                dc, amount = '借', debit
            elif credit and not debit:
                dc, amount = '贷', credit
            else:
                # zero line or (defensively) a two-sided one — fall back to balance
                dc = '借' if line.balance >= 0 else '贷'
                amount = abs(line.balance)
            item = line.cn_cash_flow_item_id
            writer.writerow([
                line.id,
                fields.Date.to_string(line.date) or '',
                line.move_id.name or '',
                line.account_id.code or '',
                line.account_id.name or '',
                dc,
                amount,
                item.code or '',
                item.name or '',
            ])
        data = sio.getvalue().encode('utf-8-sig')
        fname = '现金流量项目归属_%s.csv' % (self.company_id.name or '')
        self.write({
            'export_file': base64.b64encode(data),
            'export_filename': fname,
        })
        _logger.info("suite_cn_cashflow line export: %d classified line(s), company %s",
                     len(lines), self.company_id.display_name)
        # Reload so the download link (binary field) shows — in-UI, no dev mode.
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    # ------------------------------------------------------------------ import
    def _read_rows(self):
        """Parse the uploaded CSV into a list of dicts keyed by the Chinese header.
        Tolerates the UTF-8 BOM and files re-saved by Excel."""
        try:
            raw = base64.b64decode(self.import_file)
            text = raw.decode('utf-8-sig')
        except Exception as e:  # noqa: BLE001 — surface a friendly UserError
            raise UserError(_("无法读取该文件，请确认是本向导导出的 UTF-8 CSV：%s", e))
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return []
        header = [(h or '').strip() for h in rows[0]]
        out = []
        for raw_row in rows[1:]:
            if not any((c or '').strip() for c in raw_row):
                continue
            rec = {header[i]: raw_row[i] for i in range(min(len(header), len(raw_row)))}
            out.append(rec)
        return out

    def action_import(self):
        self.ensure_one()
        if not self.import_file:
            raise UserError(_("请先上传要回填的 CSV 文件。"))
        rows = self._read_rows()
        Aml = self.env['account.move.line']

        updated = 0
        not_found = []       # 分录ID not in this DB / company
        unknown_item = []    # 项目编码 not resolvable
        blank_id = 0
        for rec in rows:
            raw_id = (str(rec.get('分录ID') or '').strip())
            if not raw_id:
                blank_id += 1
                continue
            try:
                line_id = int(float(raw_id))  # tolerate '123.0' from Excel
            except (TypeError, ValueError):
                not_found.append(raw_id)
                continue
            line = Aml.browse(line_id).exists()
            if not line or line.company_id != self.company_id:
                not_found.append(raw_id)
                continue
            code = (str(rec.get('现金流量项目编码') or '').strip())
            item = self._find_item(code)
            if code and not item:
                unknown_item.append('%s→%s' % (raw_id, code))
                continue
            # An empty code clears the classification (an explicit un-tag round-trips).
            if line.cn_cash_flow_item_id.id != (item.id or False):
                line.cn_cash_flow_item_id = item.id or False
                updated += 1

        msg = [_("回填完成（公司：%s）。", self.company_id.display_name)]
        msg.append(_("更新 %(u)s 条分录的现金流量项目归属。", u=updated))
        if blank_id:
            msg.append(_("有 %(n)s 行缺「分录ID」，已跳过。", n=blank_id))
        if not_found:
            msg.append(_(
                "⚠ 有 %(n)s 个「分录ID」在本公司账套中不存在，已跳过"
                "（换库回填只在导出的同一数据库有效，见 README）：\n  %(l)s",
                n=len(not_found), l='、'.join(not_found[:50])
                + ('…' if len(not_found) > 50 else '')))
        if unknown_item:
            msg.append(_(
                "⚠ 有 %(n)s 行的「现金流量项目编码」在本公司项目表中找不到，已跳过"
                "（请先用「现金流量配置 导出/导入」建好项目再回填）：\n  %(l)s",
                n=len(unknown_item), l='、'.join(unknown_item[:50])
                + ('…' if len(unknown_item) > 50 else '')))
        if not (blank_id or not_found or unknown_item):
            msg.append(_("全部行均已应用，无跳过项。"))
        self.write({'result': '\n'.join(msg)})
        _logger.info("suite_cn_cashflow line backfill: %d updated, %d not-found, "
                     "%d unknown-item, %d blank-id", updated, len(not_found),
                     len(unknown_item), blank_id)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }
