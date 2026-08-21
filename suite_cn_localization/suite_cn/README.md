# China Localization Suite (`suite_cn`)

One-click install of the SuiteState China localization set.

## What it is

A **dependency aggregator**. Installing `suite_cn` installs every SuiteState
China localization module in a single step.

## Hard boundary — never put code here

`suite_cn` contains **no code, models, fields, data, views, security rules,
reports, assets, hooks or wizards**. It is only a `depends` list, and it must
stay that way.

- Each child module (`suite_cn_coa`, `suite_cn_statement`, `suite_cn_cashflow`, …)
  attaches **directly** to the official base
  (`account` / `account_reports` / `l10n_cn_reports`).
- Each child **installs independently** and does **not** depend on this
  aggregator. The one deliberate sibling link is the `auto_install` bridge
  `suite_cn_cashflow_statement` (that is its whole purpose).
- There is **no shared code layer**. If common behaviour is ever needed, it
  extends the official base *inside the module that needs it* — never here.

This is deliberate. It keeps the localization out of the `l10n_cn_sme` trap: a
shared base层 that every module was forced to depend on, which could not evolve
without breaking dependents. See `l10n_cn_design.md` §11.5 and §C3.

> If you are about to add a file under `suite_cn/` other than this README, the
> manifest and `__init__.py`: **stop**. It belongs in a child module.

## Contents (current)

| Child module | Purpose | In `depends`? |
|---|---|---|
| `suite_cn_coa` | 科目分级 → 科目余额表 / 三栏式明细账 折叠（呈现层） | yes |
| `suite_cn_statement` | BS/PL 年初/累计列（版式渲染 R21 起） | yes |
| `suite_cn_cashflow` | 现金流量表（小企业会计准则，直接法 22 行） | yes |
| `suite_cn_cashflow_statement` | 桥：现金流量 × 版式行次映射（R21 起有内容） | no — `auto_install` |

The bridge is **not** in `depends`: it `auto_install`s once its two sides are present.
Install only the pieces you need, or install `suite_cn` to get everything.
