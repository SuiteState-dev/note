# -*- coding: utf-8 -*-
"""account.account 余额方向字段 (R48-T1)。

科目余额表的期初/期末余额落哪一栏,由【科目自身的余额方向属性】决定,不随数值符号
迁移(二姐实务口径 observed:「属于贷方科目,亏损了就是负数」「借贷方不会自动挪」)。

本字段是【运行时载体 / 客户自建覆盖层】——为空时不代表"无方向",而是让 handler 走
发行件(ASSBE_CHART 方向列,我方标准科目的权威值)或 account_type 推导兜底(客户自建)。
🔴 惯例31:给官方模型【并排挂一列我方字段】(_inherit 扩展),不改任何既有字段值、不动
官方引擎 ⇒ 落在允许侧(R48-Q2 裁定)。绝不 unlink/改写客户既有 account.account。
"""
from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    cn_balance_direction = fields.Selection(
        [('debit', '借'), ('credit', '贷')],
        string='余额方向',
        help='中式科目余额表用:期初/期末余额固定落此栏,实际净额在反向时于本栏写负数。'
             '留空 ⇒ handler 依次回落我方发行件方向、再 account_type 推导(推导时随件告警,'
             'R48-Q5)。仅【客户自建科目】需要在此手工指定;我方发行科目的权威方向在'
             'suite_cn_coa 的 ASSBE_CHART 方向列(唯一 home)。')
