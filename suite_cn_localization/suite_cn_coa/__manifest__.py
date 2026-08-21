# -*- coding: utf-8 -*-
{
    'name': 'China - Chart of Accounts Publisher (科目表发行)',
    'version': '19.0.3.0.3',
    'category': 'Accounting/Localizations/Reporting',
    'summary': 'Publishes the national ASSBE (小企业会计准则) chart of accounts so a '
               'Chinese company gets a ready-to-post skeleton with correct code '
               'ranges, plus the Chinese account-group hierarchy (科目分级)',
    'description': """
R33-A: `suite_cn_coa` 由「科目分级树生成器」升级为「**科目表发行方**」(design §R33-A)。
Read-only over ACCOUNTING DATA — no journal item or balance is modified; it CREATES the
skeleton chart of accounts a fresh Chinese company needs.

0. **ASSBE 科目表发行** (R33-A, NEW) — 发行国标小企业会计准则(财会〔2011〕17号)的
   68 一级 + 32 明细科目到装 ``cn`` chart 的公司,使中国客户【装机即得】一套编码号段正确、
   我方 BS/PL 四张 form 取得到数、会计认得出的账。
   * post_init 自动发【通用 88 条】;wizard *会计 → 发行中国科目表* 按【纳税人身份】(一般/
     小规模)补税费档。认领优先(编码已存在则不改名/type/reconcile)、幂等、纯 ORM(不写
     ir.model.data)、另记发行台账。
   * 🔴 装机顺序:【先装语言(中文 zh_CN)、再建公司 / 装科目表】。R38-T3:发行前 zh_CN 未激活
     则拒绝(科目名会只落 en_US 单键、事后无法回填——我方账户是运行时用户数据,不同于官方
     chart 走模块翻译在激活语言时自动回填)。
   * 编码是取数键(R33-T0 / B-64:BS/PL 只按 account_codes 前缀取数,不看 account_type);
     唯一 type 硬约束 = 货币资金 1001/1002/1012 必须 asset_cash(CF 靠它判现金)。
   * 二选一(§4.10):星辰国标编号与官方 cn 编号在存货/研发段有 1 处碰撞(1406),故对官方
     ASSBE 报表做【4 条 formula + 1 条 hide_if_zero】外科覆盖(在产品 1406→4001 等),
     先存原值,卸载写回。验证:缺 PL 那处覆盖会破 30=53 差 6000(tests V6,守卫非静默抓到)。
   * 卸载:发行的【科目留库】(无 xmlid,等同手工建);官方报表 formula 【主动写回原值】。
   * 🔴 3.0 起(R43):科目编码改【点分】(2221.02…),与官方 l10n_cn 对齐 → `code` 判据自然
     命中、同义重复走认领消失。注意点分=统一到 Odoo 形态,【不是】中国国标(实务传统是连号)。
     2.x 装过的库【不提供自动迁移】(会 unlink 客户 account.account 的迁移破「科目留库」承诺,
     服务 0 客户):升 3.0 后仅【告警】旧连号残留、建议重建库,连号旧科目不删不改。我方自建
     地方税负债侧 6 条走号段 2221.51–.56(撞号哨兵护)、默认归档(active=False)。

1. **account.group hierarchy** (科目分级, 原有 §3 不动) — 大类 / 一级 / 明细 group tree for
   the official ``cn`` / ``cn_common`` / ``cn_large_bis`` charts. Official charts ship no
   groups. Built per company via ``post_init_hook`` + re-runnable wizard.

1. **account.group hierarchy** (科目分级) — builds a 大类 / 一级 / 明细 group tree for
   the official ``cn`` (小企业会计准则), ``cn_common`` and ``cn_large_bis``
   (企业会计准则) charts, so the Trial Balance and every group-aware report folds
   the Chinese way. Official charts ship no groups. Built per company via a
   ``post_init_hook`` (existing companies) and a re-runnable wizard
   *Accounting → 生成中国科目分级* (companies created later / chart switch / rebuild).

2. **Trial Balance = 科目余额表** — no code: the native Trial Balance already renders
   期初余额｜借方｜贷方｜期末余额 in Chinese (official ``account_reports`` zh_CN
   translations) and folds by the groups from part 1. Requires the Chinese language pack.

3. **General Ledger = 三栏式明细账** — no code: the native General Ledger is already a
   Chinese 三栏式明细账 — per account 日期｜借方｜贷方｜余额 with a true running balance
   and an 期初余额 (Initial Balance) opening row (both native, verified R19-T2), folded
   by the groups from part 1. Extra dedicated columns (凭证号 / 摘要 / 方向) and the
   数量金额式 form would need a GL custom-handler rewrite — out of scope (design §11.7).

This module was named ``suite_cn_ledger`` through R19; R20 renamed it to ``suite_cn_coa``
and moved the year-begin / YTD report columns to ``suite_cn_statement``, so the stateful
group builder (this module) and the pure report-presentation data live apart (design §11.2).

Uninstall is clean and reversible (R22-T2): module-created groups are removed, while
**manual** groups the builder *adopted* (claimed + renamed because they sat on a target
prefix) are restored to their original name (all languages) and parent, and kept — never
deleted. ``account.account.group_id`` is a non-stored compute so accounts keep zero residue.
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'OPL-1',
    # l10n_cn_reports: R33-A 发行 ASSBE 科目表 + 对官方 ASSBE 报表做国标口径覆盖,
    # 二者都要求官方 cn chart 与 ASSBE 报表已在库(l10n_cn_reports → l10n_cn 传递依赖)。
    'depends': ['account', 'account_reports', 'l10n_cn_reports'],
    'countries': ['cn'],
    'data': [
        'security/ir.model.access.csv',
        'data/override_health_action.xml',
        'wizard/generate_cn_groups_views.xml',
        'wizard/publish_cn_coa_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'auto_install': False,
}
