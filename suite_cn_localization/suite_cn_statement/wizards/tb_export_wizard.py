# -*- coding: utf-8 -*-
"""科目余额表 中式版式导出向导 (R47-T1).

控件是【列集单选：六栏 / 八栏】——与 BS/PL 向导的期间单选同构，但轴不同：六栏八栏都要
毛额发生额，选的是「本年累计发生额」两列显不显（八=显，六=不显）。默认【八栏】(超集)。

为什么走向导而非报表内选择器：与 export_wizard 同理——account_reports 的 options 模板/JS
是官方升级会动的那层，向导完全解耦，`-u` / 框架 bump 碰不到（§铁律8）。
"""
import json

from odoo import api, fields, models


class CnTrialBalanceExport(models.TransientModel):
    _name = 'suite.cn.tb.export'
    _description = '科目余额表 中式版式导出'

    report_id = fields.Many2one(
        'account.report', string='报表', required=True, readonly=True)
    columns_mode = fields.Selection(
        [('eight', '八栏（含本年累计发生额）'), ('six', '六栏（不含本年累计）')],
        string='列集', default='eight', required=True,
        help='六 / 八栏是同一张报表的两种列集。八栏=期初借贷｜本期发生借贷｜本年累计借贷｜'
             '期末借贷；六栏=去掉本年累计发生额两列。')
    options_json = fields.Text(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        opts = self.env.context.get('cn_export_options')
        if opts is not None and 'options_json' in fields_list:
            res['options_json'] = json.dumps(opts)
        return res

    def action_export(self):
        self.ensure_one()
        options = json.loads(self.options_json) if self.options_json else {}
        result = self.report_id.export_to_cn_tb_xlsx(options, self.columns_mode)
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
