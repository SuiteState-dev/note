# -*- coding: utf-8 -*-
"""R38-T1 阶段B:ASBE 存货口径 backport 的升级重放(4处同步之一,惯例18)。

R38-T1 给 REPORT_OVERRIDES 新增【官方原生 3 条】(ASBE 存货/营业成本/往年未分配),而 B-67:
post_init 不随 ``-u`` 重跑 → 官方这几条在纯 ``-u`` 下【不重放】。同时我方 bal_begin/ytd 2 条经
suite_cn_statement 的 data XML(noupdate=0)随 ``-u`` 自动变新值 ⇒ 若不重放官方 3 条会【半应用】:
存货年初列已含 5001/5101/5201、期末列仍不含 → 同表两列打架、且权益侧脱钩破 30=53
(R36 已用 500 破口付过一次学费,惯例18:部分重放比完全不重放更坏)。

故本迁移显式 ``_apply_all()`` 重放全部 8 条。幂等:既有 5 条 ASSBE cur==new 跳过;新增 3 条
ASBE cur==原值 → 记台账+套新值。基线漂移哨兵(E7)守护:官方若在 patch 改了这几条则登记+不硬改。
_apply_all 末尾还带 R37-T3 覆盖生效自检(非空即 ERROR),装/升即自查。
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['suite.cn.coa.report.override']._apply_all()
