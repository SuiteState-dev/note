# China – Financial Statement Presentation (`suite_cn_statement`)

Presentation-layer localisation (呈现层, L0) that shapes the **official** Chinese Balance
Sheet / Profit & Loss into the Chinese reporting form (报送形态). Read-only over
accounting data — no journal item, balance or account is ever modified.

Depends on `account`, `account_reports`, **`l10n_cn_reports`** (Enterprise). It extends the
official `l10n_cn_reports` report records, so it depends on that module explicitly.

## Scope

### Year-begin / YTD columns (年初余额 / 本年累计) — R20

Appends a second column to the four official Chinese reports:

| Report | Added column | Expression |
|---|---|---|
| Balance Sheet `l10n_cn_assbe_bs` / `l10n_cn_asbe_bs` | 年初余额 | `to_beginning_of_fiscalyear` |
| Profit & Loss `l10n_cn_assbe_pl` / `l10n_cn_asbe_pl` | 本年累计金额 | `from_fiscalyear` |

Additive only — no official record is modified, so the columns survive `-u` of
`l10n_cn_reports` (verified R16, re-verified R20). The unaffected-earnings lines are
handled explicitly (本年利润 year-begin is 0 by definition; 以前年度未分配 re-scopes its
sub-formulas to the fiscal-year start).

### This version (R21) — Chinese reporting-form XLSX export

A **中式版式 XLSX** export button appears on the Chinese Balance Sheet / Profit & Loss
(and, when the cash-flow bridge is installed, the Cash Flow Statement). It renders the
official report values into the PRC statutory reporting form: 行次 (row numbers), the
报送口径 row names, the two-column Balance-Sheet layout, the header (编制单位 / 期间 /
单位) and the three signature boxes.

The layout is data-driven by three renderer-private models (they are **not** written onto
the official report records, so `-u l10n_cn_reports` is unaffected — verified R21):

- `suite.cn.statement.form` — one per official report: `title`, `layout`
  (single / two_column), `period_mode` (point `YYYY-MM-DD` / range `YYYY年M期`),
  `has_row_no` (whether a 行次 column is printed — the tax-bureau ASBE P&L has none, R24-T2).
- `suite.cn.statement.column` — the reporting columns and their order. This order
  **overrides** the on-screen column sequence, so the P&L shows 本年累计 before 本月 even
  though the year-to-date column sits at on-screen `sequence=900`. `column_group`
  (`primary` / `comparison`) picks which report column **group** the value is read from —
  `comparison` is the prior comparable period (上期金额), see R24 below.
- `suite.cn.statement.row` — each 行次 line (or an un-numbered section-title row): `row_no`,
  `name` (报送口径), `report_line_id` (the official line whose value feeds it, may be empty),
  `section` (left/right for the Balance Sheet).

Values come from the official report via `_get_lines(options)` (the verified R18/R21 path),
so **every exported figure equals the on-screen report for the same period** — that is the
acceptance criterion, and it was verified row-by-row (0 mismatches).

Column bindings: ASSBE Balance Sheet 期末余额 = `balance`, 年初余额 = `bal_begin`; ASSBE
Profit & Loss 本年累计 = `ytd`, 本月 = `balance`; Cash Flow 本月 = `balance`, 本年累计 = `ytd`.
ASBE Balance Sheet 期末余额 = `balance` / 上年年末余额 = `bal_begin` (both `primary` group);
ASBE Profit & Loss 本期金额 = `balance` (`primary`) / 上期金额 = `balance` (`comparison`).

Row numbers are **renderer-private** (they do not appear as an on-screen report column):
no report engine emits a cheap constant, so a 行次 column would need 85+ constant
expressions plus a custom handler — not worth it (R21-B1). They live only in the export.

### R23 — reachability / button / generator-guard fixes

Bug fixes surfaced by a browser end-to-end walkthrough (prior rounds only ran figures
programmatically). No new feature.

- **Generator self-check (`hooks._log_dangling_expressions`)** — the year-begin / YTD
  columns are a static, offline-generated set of expressions. If a generated aggregation
  formula references a `CODE.label` that does not exist, the report raises *"Could not
  expand term"* the moment it is opened — invisible to any `_get_lines` smoke test that
  does not hit that line. The self-check scans this module's aggregation expressions at
  install (`post_init_hook`) and upgrade (migration `19.0.1.3.0`) and logs a WARNING for
  every dangling term. A regression is now caught at install time, not by a user.
  (R23-T2 retired one such orphan, `CN_TCI.ytd`, whose 综合收益总额 = 净利润 + 其他综合收益税后净额
  references the `external`-engine OCI line that has no derivable YTD.)
- **中式版式 XLSX button now in the main button bar** — it was collapsed into the cog /
  overflow menu because it lacked `always_show` (the button bar only shows `always_show`
  buttons). It now carries `always_show=True` and `sequence=5`, so it sits first, before
  the official PDF / XLSX — the Chinese-form XLSX is the only export Chinese clients use.
- **Button gate is company-independent** — the short-circuit that skips the form lookup on
  non-Chinese reports now keys on the **report's own** `country_id`, not `env.company`.
  The old chart-template gate hid the button when the default company was non-CN (e.g. a
  Chicago default with `chart_template=False`) even while opening a CN report with a CN
  company selected. (R23-T4-2)
- **Tests** — `tests/test_reporting_forms.py` asserts (1) each export column's 行次 is
  strictly increasing (Balance-Sheet left/right independently — completeness ≠ order,
  R23-T4-1) and (2) no generated aggregation expression is dangling (R23-T2).

### R24 — ASBE (已执行新三准则) Balance Sheet + P&L unfrozen

The two tax-bureau ASBE reporting forms (资产负债表 72 rows / 利润表 43 rows, **已执行 version
only**) are now delivered to XLSX. Two mechanism additions made them possible:

- **`has_row_no` (T2)** — the tax-bureau ASBE **P&L has no 行次 column at all**. `has_row_no=False`
  makes the single-layout renderer drop the row-number column and shift 项目 + values left. The
  Balance Sheet and all ASSBE forms keep it `True`. The ordering test branches on this flag
  (False ⇒ asserts every row's `row_no` is empty) and now also asserts row numbers are
  **contiguous** (no gap), not merely increasing — the tax-bureau importer positions rows by 行次.
- **上期金额 via a comparison column group (T1)** — the ASBE P&L second column is **上期金额**
  (prior comparable period), which is a *different column group* than 本期金额, not a different
  expression label (both read `balance`). A column with `column_group='comparison'` reads that
  second group; the export forces a **`same_last_year`** comparison so the group exists. One path
  serves both statutory cadences: `same_last_year` lands on the **prior fiscal year** for an
  annual filing and the **same quarter last year** for a quarterly filing (verified) — *not*
  `previous_period`, which would wrongly give the *previous* quarter.

Row names are transcribed **verbatim from the tax-bureau screenshots**, never copied from the
Kingdee statutory XLSX (full-width vs half-width `.` / `．` trap).

**PDF** (a QWeb print template with the same signature boxes) is designed for but not yet
shipped — the format-agnostic prepare step already drives it; it lands next round (design §D2).

### Empty-value policy (读我，别反复追问)

Several statutory rows are kept even though they render **blank or zero**:

- **Section-title rows** (流动资产：, 非流动资产：, …) carry a 行次-less title and no value.
- **P&L "其中：" breakdown rows** — 税金及附加 sub-rows (消费税 / 城建税 / 资源税 / …),
  管理费用 / 销售费用 / 财务费用 sub-rows — exist in the reporting form but the ASSBE chart
  does **not** split those (税金及附加 is one account, expenses are not sub-classified). Their
  official line therefore computes **0**, and the XLSX shows 0 — consistent with the on-screen
  report. We deliberately **keep the 行次 and 行名 and do not touch the chart of accounts** to
  fill them. On real reporting forms these rows are usually blank too (the bookkeeper leaves
  them empty). This is by design, not a bug.

- **ASBE P&L rows with no official source (R24)** — the tax-bureau ASBE P&L (43 rows) has
  **14 data rows the official report (29 lines) has no source for**: 投资收益「其中」明细
  (rows 12/13), the 12 OCI breakdown rows (29–32 / 34–39), and the 2 EPS rows (42/43). These
  render **blank** (`report_line_id` empty). This is **not** a capability gap: the Kingdee
  statutory report-item table gives these same rows *no* expression either (取数来源=科目,
  关系表达式=空), and the official parent OCI lines are `external`-engine (manual entry). EPS
  needs a share count (not in the ledger) and 外币报表折算差额 only enters the consolidated
  statement. **Do not "complete" these rows** — blank is the industry-baseline manual treatment.

Rows with no official source line at all render with an empty value — never a crash, never a
collapsed row (ASSBE/CF have none; ASBE P&L has the 14 above by design).

### Cross-foot self-check (表内勾稽) — R24

A reporting form must pass **three orthogonal** acceptance dimensions, not two: **① 行次**
(complete + ordered + no-gap), **② 取值** (every figure = the official on-screen report), and
**③ 表内勾稽** (each 合计 row = the sum of its shown detail rows). The tax-bureau importer
validates the third; earlier rounds only checked the first two.

The subtotal rows bind to the **official aggregation lines**, which still include the
`官方有·报送无` rows the form drops. So if such a dropped row carries a balance, the subtotal
exceeds the sum of the shown detail by exactly that balance — a break the tax bureau would
reject. Two known cases: BS `流动资产合计` includes `买入返售金融资产` (`cn_faur`); PL `净利润`
includes `以前年度损益调整` (`cn_pyia`). Both are structurally 0 for a general enterprise on the
new standard (a non-zero balance means the data belongs on a *different* statutory form).

When a break is found, `export_to_cn_xlsx` surfaces it on **two** channels — a server-log
WARNING **and a red line rendered into the xlsx itself**, above the signature boxes ("⚠ 本表
存在 N 处表内勾稽差异 … 行 XX 合计 ≠ Σ明细，差 YYY"). The in-file line matters: the accountant
clicking Export never reads the server log (§7.0 铁律1 — self-check found ≠ user saw), and the
warning must travel with the file to the bookkeeper / tax bureau. It is a **pre-upload self-check**.

**Two break kinds, worded differently (R25).** Sharing one message would make the accountant
think the report is broken when the fix is trivial, so a rule carries a `kind`:

- **`structural`** (default) — a dropped 官方有·报送无 row (买入返售 `cn_faur` / 以前年度损益调整
  `cn_pyia`) carries a balance. Rare; the data belongs on a *different* statutory form. Message:
  "本表可能不适用于该主体，请核对是否选错报送主体/报表". Travels to the tax bureau.
- **`unclassified`** — the CF `未分类现金流量` (`cn_cf_s_unc`) is non-zero, i.e. N 元 of cash flow
  was never tagged. **Common, fixable, internal-only** (the Cash Flow form is not filed). Message:
  "有 N 元现金流未分类，请到 现金流量项目/分录 补标后重新导出（此为数据质量提示，非报表错误）".
  This is the副作用 of a deliberately good design (the unclassified line is *visible*, R5), not a bug.

**`test_crossfoot_live`'s "zero break" is a promise about the TEST FIXTURE, not a customer DB.**
In a real ledger 漏标 is normal, so `cn_cf_s_unc` is almost always non-zero and the CF form will
legitimately break `20 = 7+13+19` — that is a **data-quality signal, not a code defect**. Do not
chase a customer-lib CF cross-foot break in the code; classify the flow instead.

Coverage: `_CN_CROSSFOOT` holds a rule set **per reporting form** (their row layouts differ) —
ASSBE BS/PL, ASBE BS/PL and the Cash Flow form, all calibrated against the live report (造数复跑).
Two sign traps were found and fixed live: ASSBE `减：累计折旧` is stored **negative**, so 账面
价值 = 原价 **+** 累计折旧; CF outflow rows are stored negative, so each 净额 is a plain sum. The
CF 现金净增加额 subtotal includes the dropped `未分类现金流量` (cn_cf_s_unc) — its own dropped-row
break, surfacing unclassified cash. Any new reporting form MUST add its `_CN_CROSSFOOT` entry in
the same round (else `test_crossfoot_live` can't cover it). Tests: `test_crossfoot_evaluator`
(synthetic, checks the math) and `test_crossfoot_live` (every form with a rule set cross-foots on
clean data for both CN companies). See design §15.3 / §12.3.

### R26 — export cell-aligned to the official template + ASSBE annual form

**Structure aligned to the tax-bureau template (T1).** The 财报导入 importer accepts a file
by **template format, not by vendor** — anything that is not the official layout falls to
manual 财报转换. So the export target moved from "looks like the template" to "**is** the
template, cell-for-cell". The header block was rebuilt (superseding the R21 编制单位/期间/单位
header):

- a **blank column A** — the whole data block sits one column right (the earlier "8 columns,
  no gap" spec had missed column A: it is a right-shift, not a dropped column);
- **项目 before 行次** (was 行次 | 项目);
- the two-column Balance Sheet has **no gap column** between the two sides — 8 data columns
  B..I, left head `资 产`, right head `负债和所有者权益`;
- rows: `0` 表名+适用说明 / `1` 表号+单位 / `2` 纳税人识别号+名称 / `3` 所属期起+止 /
  `4` column headers / `5+` data.

表名 suffix (适用说明), 表号 and worksheet name are **per-form** (会小企 vs 会企 wording
differs) → `suite.cn.statement.form.title_suffix` / `form_no` / `sheet_name`, never hard-coded.
`资 产` / `负债和所有者权益` are two-column **layout invariants**. Taxpayer identity comes from
`options['companies'][0]` (**not** `env.company`, which may be a non-CN default — 铁律2). The
纳税人识别号 reads `res.company.vat` (base Tax ID = the 18-digit 统一社会信用代码 in China;
`company_registry` fallback); demo CN companies leave it empty, so a real customer must fill it.

Cell-for-cell alignment is verified by **parsing the official `.xls` templates as test
fixtures** (`test_template_alignment`, skipped until the fixtures are uploaded to
`tests/fixtures/`) — never by transcribing the spec into the test (the prose spec was wrong
once). `test_template_geometry_single` / `_two_column` guard our renderer's geometry meanwhile.

**ASSBE annual reporting form (T2).** The same official report now carries **two** forms — a
月季报 (本期 | 本年累计) and a 年报 (本年累计 | 上年金额) — so the form key became three-dim:

- `period_scope` (`monthly_quarterly` / `annual` / `any`) and `standard_version`
  (`na` / `executed` / `not_executed`, only ASBE has the switch), with
  `unique(report_id, period_scope, standard_version)` replacing `unique(report_id)`.
- The **Balance Sheet is cell-identical** across cadences (no period suffix) → one
  `period_scope='any'` form serves both. PL/CF get a dedicated 年报 form whose rows are
  **borrowed** from the 月季报 sibling via `rows_from_id` (single source of truth — the two
  cadences can never drift). 本年累计 = `ytd` (primary); 上年金额 = `balance` from the
  `same_last_year` comparison group (the R24 machinery).

**报送期间 selector = a wizard, not an in-report control.** The 中式版式 XLSX button now opens
`suite.cn.statement.export`, whose single 报送期间 radio (月季报 / 年报, default 月季报, **not
sticky**) is isomorphic to the tax-bureau 报送期间 单选. A wizard is decoupled from the
`account_reports` options template/JS — the layer that breaks on official upgrades — so it is
upgrade-safe (§铁律8). Cost: +1 click, ~5×/year.

🔴 **No silent fallback.** A report that has a 月季报 form but **no** 年报 form (ASBE — its
annual column layout has no source material) resolves to **empty**, and the wizard raises an
explicit *"该准则的年报版式尚未支持"*. It must never fall back to the 月季报 form — that would
ship 季报 column semantics under an 年报 filing. Annual PL/CF share their report's xmlid, so
`_CN_CROSSFOOT` covers them automatically (§12.3).

🔴 **No mislabeled half-year either (period axis).** The rule above guards *form missing*; the
other path is *form right, period wrong*. An 年报 form over a partial period (e.g. Jan–Jun) yields
本年累计半年 | 上年同期半年 — self-consistent columns that are **not** an annual filing, exported
under the 年报 表名/表号. `_cn_assert_annual_period` requires the options period to cover the **full
fiscal year** (`company.compute_fiscalyear_dates`) when `period_scope='annual'`, else raises
(monthly forms exempt). Same silent-wrong-口径 class, period axis instead of form axis.

## Provenance (R20 move)

These columns shipped inside `suite_cn_ledger` through R19. R20 split the localization
so that the **stateful** part (the `account.group` builder with its `post_init_hook` and
per-company master-data writes) stays in the group module (renamed `suite_cn_coa`), while
the **pure presentation data** (these columns) lives here. See design §11.2.

The move is pure data: the `account.report.column` / `account.report.expression` records
are re-created identically under this module's namespace. Deleting and re-creating them
loses zero accounting data (they carry no balances — they are report definitions).

## Uninstall

Clean. The added columns and expressions carry this module's `ir.model.data`, so uninstall
removes them and the official reports revert to their single `Balance` column (P-01).
