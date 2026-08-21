# -*- coding: utf-8 -*-
"""发行台账 —— 记录本模块往每个公司发行过哪些 account.account (R33-A §4.8.3).

为什么要这张表:
  * 发行走【纯 ORM create、不写 ir.model.data】(§4.8.3, R22-T2 教训:挂我方 xmlid
    卸载路径可能动到客户在用的记录)。没有 xmlid 就没有官方的"哪些是我建的"记号,
    升级/卸载判定全靠这张自建台账。
  * 卸载【不删科目】(§4.9.1),故本表主要服务【升级路径】:将来骨架改版(如财会
    〔2026〕11号)要判"哪些码是我方发的、可安全更名/补建",靠本表。
  * 幂等发行按 (company, code) 查重,本表是那次判定的持久记录。

科目本身卸载不动 —— 本 ledger 行随模块卸载删除(标准 uninstall),科目留库。
"""
from odoo import fields, models


class CoaPublishedAccount(models.Model):
    _name = 'suite.cn.coa.published.account'
    _description = 'China COA — 已发行科目台账 (升级/幂等追踪)'

    company_id = fields.Many2one(
        'res.company', string='公司', required=True,
        index=True, ondelete='cascade')
    code = fields.Char(string='编码', required=True, index=True)
    account_id = fields.Many2one(
        'account.account', string='科目', required=True, ondelete='cascade',
        help='本模块发行时创建的 account.account。ondelete=cascade:客户若删该科目,'
             '台账行随之消失(与"科目留库"不冲突——留库指卸载模块时不删,客户主动删是另一回事)。')
    taxpayer = fields.Selection(
        [('common', '通用'), ('general', '一般纳税人'), ('small', '小规模纳税人')],
        string='发行档', required=True, default='common')

    # —— R37-T4-b (缺陷#3): 认领留痕 ——————————————————————————————————————————
    # 跨准则碰撞已实测 14 条 (如 4001 ASSBE=生产成本 / ASBE=实收资本 —— R37-T5 S5 verified)。
    # 认领【不改名不改 type】(§4.8.3),事后完全无迹可查 → 污染盘点无从下手。故认领分支也写台账,
    # 快照【认领前】的名称/type,并标 action 区分新建 vs 认领。时间用内建 create_date。
    action = fields.Selection(
        [('created', '新建'), ('claimed', '认领'), ('collision', '撞号跳过')],
        string='发行动作', required=True, default='created',
        help="created:本模块 create 的新科目;claimed:编码已存在,本模块认领(不改名/type);"
             "collision:我方号段(2221.51–.99)目标码已被他人占用 → 不覆盖、跳过、留痕(R43-T1c)。")
    claimed_name = fields.Char(
        string='认领前名称',
        help="action=claimed 时,认领【当刻】该科目的既有名称(我方不改它,仅快照留痕)。")
    claimed_type = fields.Char(
        string='认领前 account_type',
        help="action=claimed 时,认领当刻该科目的既有 account_type。跨准则碰撞(4001 等)"
             "凭此可事后辨识。")
    claimed_same_name = fields.Boolean(
        string='与我方同名',
        help="认领前名称是否与本模块该编码的发行名一致。False = 客户自有命名(可能是"
             "跨准则碰撞或客户改名),是盘点重点。")

    _company_code_uniq = models.Constraint(
        'unique(company_id, code)',
        '同一公司同一编码只能发行一次。')
