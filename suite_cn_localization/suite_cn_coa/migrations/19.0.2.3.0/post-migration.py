# -*- coding: utf-8 -*-
"""R37-T4-b:发行台账新增 action 字段(created/claimed)——回填既有行为 'created'。

背景:R37 前台账【只在 create 分支写】(认领不写,正是缺陷#3),故既有台账行全部是【新建】。
新字段 action required=True default='created';Odoo 加列时会给既有行套默认值,本迁移是【显式
兜底】(防某些路径下默认未回填导致 NULL,scan 依赖 action 正确)。claimed_* 快照字段对既有行
留空(它们当年是新建、无认领前快照),符合语义。
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("""
        UPDATE suite_cn_coa_published_account
           SET action = 'created'
         WHERE action IS NULL
    """)
