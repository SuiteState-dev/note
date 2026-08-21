# -*- coding: utf-8 -*-
"""R36-T1 缺陷#2 修复的升级迁移:①清陈旧台账 ②重放官方 5 条覆盖。

背景(见 report_override.py 头注):R36-T1 起,我方 3 条国标口径(行11/行12 年初列、PL 本年
累计列)改由 suite_cn_statement 源头 XML 自产,随 ``-u`` 重载即变新值;官方原生 5 条仍由本
模块 Python 覆盖(``_apply_all``),而 B-67 使 post_init **不随 ``-u`` 重跑** → 官方 5 条在纯
``-u`` 下不重放。

⇒ 升级后会出现【半应用】:我方 3 条已是国标值(经 -u XML),官方 5 条仍是原值 → 年初列 4001
   两侧脱钩(资产侧 wip.bal_begin=4001 含它,权益侧 prev_year balance_domain=-4 仍吃它)→ 破
   30=53(R36-T1 实测:test_dir_split_double_column 差 500)。

故本迁移显式重放官方 5 条,把 ``-u`` 路径拉回自洽。``_apply_all`` 幂等(cur==new 跳过)且有
基线漂移哨兵守护(官方若在 patch/20.0 改了公式则登记+不硬改),安全。

① 另清掉 2.1.0 及之前 ``labels=None`` 误登记的我方 ``bal_begin``/``ytd`` 台账行——否则卸载
   ``_restore_all`` 会把旧原值写回我方 exp_253 等,反噬源头修复(R36-T1 改动5)。
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Override = env['suite.cn.coa.report.override']

    # ① 清陈旧台账(我方 bal_begin/ytd 不该由本模块管)。
    Override.search([('expr_label', 'in', ['bal_begin', 'ytd'])]).unlink()

    # ② 重放官方 5 条覆盖,消除 -u 半应用不一致(缩为 balance×3 + balance_domain + hide_if_zero)。
    Override._apply_all()
