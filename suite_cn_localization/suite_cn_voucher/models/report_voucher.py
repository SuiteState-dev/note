# -*- coding: utf-8 -*-
"""中式记账凭证打印 —— docs 顺序显式重排 (R43-T3)。

🔴 为什么需要:官方模板 `l10n_cn.report_voucher` 用 `t-foreach docs` 一凭证一页,docs 顺序
来自 recordset;而 `account.move._order` 默认 `date desc, name desc, id desc`(【倒序】)。
中式凭证装订【必须按凭证号正序】。「按月份全选 → 打印」若依赖默认 _order 会产出一叠【倒着】
的凭证,而这种错【只有打印出来才发现】。故打印时按(公司 × 凭证字 × 凭证号)【正序】显式重排。

本 AbstractModel 名 = `report.` + 报表 report_name(`l10n_cn.report_voucher`),渲染时被
自动调用以提供 docs;官方 l10n_cn 未定义它(默认按 docids 顺序),本模块补上排序。
"""
from odoo import api, models


class ReportVoucherCn(models.AbstractModel):
    _name = 'report.l10n_cn.report_voucher'
    _description = '中式记账凭证打印（docs 按凭证号正序重排）'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids).sorted(
            key=lambda m: (m.company_id.id,
                           m.l10n_cn_voucher_word or '',
                           m.l10n_cn_voucher_number or 0,
                           m.id))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'account.move',
            'docs': docs,
        }
