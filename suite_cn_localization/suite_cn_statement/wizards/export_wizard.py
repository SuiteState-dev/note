# -*- coding: utf-8 -*-
"""中式版式导出向导 (R26-T2).

The 中式版式 XLSX report button opens THIS wizard instead of downloading directly.
Its single control is the 报送期间 单选 (月季报 / 年报) — isomorphic to the
tax-bureau「报送期间：季报 / 年报」radio the accountant already faces on 财报导入,
so the mental model carries over. The chosen cadence selects which reporting-form
(``suite.cn.statement.form``) the renderer uses: the same official report feeds a
月季报 form (本期|本年累计) and a 年报 form (本年累计|上年金额).

Why a wizard and not an in-report options selector: a selector inside the
``account_reports`` options template/JS is the layer that breaks on official Odoo
upgrades (background §7 records two such traps). A wizard is fully decoupled →
``-u l10n_cn_reports`` / a framework bump can never touch it (§铁律8). The cost is
+1 click, paid ~5×/yr (4 quarterly + 1 annual); the asymmetry is decisive.

Deliberately NOT sticky: the default is always 月季报, never "what you picked last
time". Sticky is exactly the「去年选了年报、今年三月导季报忘了切」错-口径 cause; the
asymmetric cost (月季报 4×/yr, 年报 1×/yr) makes 月季报 the only safe default.
"""
import json

from odoo import api, fields, models


class CnStatementExport(models.TransientModel):
    _name = 'suite.cn.statement.export'
    _description = '中式版式导出'

    report_id = fields.Many2one(
        'account.report', string='报表', required=True, readonly=True)
    period_scope = fields.Selection(
        [('monthly_quarterly', '月季报'), ('annual', '年报')],
        string='报送期间', default='monthly_quarterly', required=True,
        help='与税局「报送期间」单选同构。默认月季报（一年四次），年报每年一次。'
             '刻意不记住上次选择——sticky 会造成「去年选年报、今年三月忘切」的错口径。')
    # The report options are carried verbatim from the button so the render uses the
    # exact on-screen period / company selection (no re-derivation). JSON on a
    # TransientCase field survives the wizard's own reload; not user-editable.
    options_json = fields.Text(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        opts = self.env.context.get('cn_export_options')
        if opts is not None and 'options_json' in fields_list:
            res['options_json'] = json.dumps(opts)
        return res

    def action_export(self):
        """Render the chosen form to XLSX and hand it back as a download.

        ``export_to_cn_xlsx`` raises a UserError (该准则的<期间>版式尚未支持) when the
        report has no form for the chosen cadence — e.g. selecting 年报 on ASBE,
        whose 年报 column 口径 has no source material. That is the intended, VISIBLE
        stop; it must never silently fall back to the 月季报 form (🔴 R26-T2)."""
        self.ensure_one()
        options = json.loads(self.options_json) if self.options_json else {}
        result = self.report_id.export_to_cn_xlsx(options, self.period_scope)
        attachment = self.env['ir.attachment'].create({
            'name': result['file_name'],
            'raw': result['file_content'],
            'mimetype': ('application/vnd.openxmlformats-officedocument.'
                         'spreadsheetml.sheet'),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
