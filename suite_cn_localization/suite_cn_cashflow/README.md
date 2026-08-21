# China – SME Cash Flow Statement (`suite_cn_cashflow`)

Direct-method Cash Flow Statement (22 statutory lines) for the PRC *Accounting
Standard for Small Business Enterprises* (财会〔2011〕17 号).

## Why a dedicated classification field

Under the PRC standard, cash-flow classification is an **independent input
dimension**: two entries with an identical account structure (e.g. Dr Bank /
Cr A/R) can belong to different cash-flow lines depending on business substance.
It cannot be derived from the journal-entry structure.

Odoo's built-in Cash Flow Statement classifies by three account **tags**
(operating / investing / financing) on the counterpart account. That granularity
is one order of magnitude coarser than the 22 statutory lines, so reusing it would
only produce "populated but wrong" figures. This module therefore adds a per-line
field `cn_cash_flow_item_id` and a pure-data `account.report` driven by it.

## How it works

- **`cash.flow.item`** — the taggable statutory items (shipped as global data). **One
  set ships**: ASSBE (小企业会计准则, code prefix `S`, 16 items). A `standard` field is
  kept for UI grouping and future sets.
  - *现金流量表（小企业会计准则）* — the single delivered report. Line items transcribed
    verbatim from a real statutory filing; legal line numbering; section headers inline;
    **two static columns** (本月金额 / 本年累计金额) via `date_scope`, reconciling in both.
    Reachable from **Accounting → Reporting → Cash Flow Statement**: it is registered as a
    CN country variant of the official report (`root_report_id`), so a CN company opening
    that menu is auto-switched to it, with the official report still selectable in the
    variant dropdown (R23-T1). It carries no custom handler, so the variant renders through
    its own domain-engine lines — the official Cash Flow handler does not touch the figures.
  - An ASBE (企业会计准则) draft (report + A* items) is kept in `data/draft/` **but not
    loaded** — it awaits first-hand ASBE material before entering scope, so the module
    ships exactly one cash-flow statement.
- **Multi-company** — items with an empty company are shared by all companies; a
  company-specific item is visible only to that company (`ir.rule`).
- **`account.move.line.cn_cash_flow_item_id`** — classification of a line. Set it
  on the **counterpart** of a cash/bank line. A cash/bank account may **not** carry a
  default item (the statement classifies the counterpart, not the cash line).
- **Per-account default, split by direction** (`cn_default_cash_flow_item_debit_id`
  / `cn_default_cash_flow_item_credit_id`) — auto-filled onto a line from the side its
  **balance sign** falls on (R22). A **double-direction** account classifies its debit
  and credit sides differently (e.g. 预付账款: 支付… on debit / 收到… on credit); a
  **single-direction** account simply takes the **same item on both** fields. Auto-fill
  works in the UI, on import and via the API (stored computed field). Switching a line's
  account **or flipping its direction** re-derives an auto-filled value from the new
  account+direction, but keeps a value you set by hand. (The former single field
  `cn_default_cash_flow_item_id` was superseded by these two in R22; it was kept one
  release for the value-preserving 19.0.1.5.0 migration and **removed in 19.0.1.7.0**.)
- **Reversals keep the original classification (R23-T5-1)** — reversing an entry
  (*红冲* / 反过账 through **Add Reversal Entry**, i.e. `_reverse_moves`) copies each
  line's cash-flow item onto the reversal line and does **not** re-derive it from the
  flipped debit/credit direction. A reversal is the negation of the original entry, so
  it cancels the original on the **same** statement line (e.g. a reversed 收到其他现金
  nets that line back to 0) instead of pulling the opposite-side default and inflating
  two lines. This relies on the field's explicit `copy=True`.
  - **Boundary — two red-ink forms this does NOT cover.** The guard fires only when the
    entry carries `reversed_entry_id` (set by *Add Reversal Entry*). It does **not**
    fire for **(a)** a red-ink entry you **build by hand**, nor **(b)** a normal entry
    where you simply **key a negative amount** — neither is linked to an original entry,
    so each line follows the account's own default like any ordinary line. Separately,
    Odoo's `debit`/`credit` are **non-negative**, so a 借方红字 is stored as a 贷方蓝字 —
    that red-ink form cannot be represented natively at all (a framework limitation, not
    something this module can fix). Do not read "reversals are handled" as covering these.
- **Optional per-company constraint** (*Settings → Accounting → Require Cash Flow
  Item*, off by default): posting an entry that touches cash requires the item on
  every counterpart line.
- **Unclassified line (19)** — a diagnostic line that surfaces any cash flow whose
  counterpart is not tagged, so gaps are **visible** rather than silently
  mis-classified.

## Reconciliation guarantees (verified)

For a fiscal-year period the report satisfies:

- line **22** *Ending cash* = Balance Sheet *Monetary Funds* (period-end column);
- line **20** *Net increase in cash* = Balance Sheet *Monetary Funds*
  (period-end − year-begin);
- operating + investing + financing + unclassified = net increase (to the cent).

## Uninstall behaviour — read before uninstalling

This module adds a real column (`cn_cash_flow_item_id`) to `account.move.line`.

- **Journal data is safe**: `debit`, `credit` and `account_id` of every line are
  **unchanged** by uninstalling (verified — trial balance identical).
- **Classification data is lost unless exported first**: uninstalling **drops the
  column**, so all cash-flow classifications entered on journal items are deleted.
  **Export them first** via *Accounting → Configuration → 现金流量项目归属 导出/回填*
  (a plain UTF-8 CSV, re-importable onto the same DB after reinstall — see below).
  Separately, the *configuration* behind them (statutory items + per-account defaults)
  is taken away through the *config* export further down (P-05).

## Config export / import — take the configuration with you (P-05, R25-T3)

*Accounting → Configuration → 现金流量配置 导出/导入* is a wizard that round-trips the
**configuration** through one plain, human-readable XLSX so a client can leave Odoo or
change implementer without losing it (design **P-05** 可移交性 — no lock-in):

- **Export** writes **one workbook, two sheets** with Chinese headers + code columns
  (nothing proprietary, any consultant or other system can read it):
  *现金流量项目* (编码 / 名称 / 类别 / 准则 / 序号) and *科目默认映射*
  (科目编码 / 科目名称 / 借方项目编码·名称 / 贷方项目编码·名称).
- **Import** reads the same file back (库-change / new implementer / disaster restore).
  It is an **incremental upsert** — items match by `code`, accounts by `code`; it never
  mirror-deletes. Whatever exists in the DB but is **not** in the file is **kept and
  listed in the result** so a human decides (a silent keep would be as wrong as a silent
  delete — same principle as the report cross-foot warning). Acceptance: export → wipe /
  reinstall → import → configuration identical (`tests/test_config_export.py`).
- **Scope note**: a *new* item code in the file is created as a **global** statutory
  item (company_id empty), matching the shipped set; company-specific custom items
  re-import as global. Statutory items and per-account mappings round-trip exactly.
- **Line-level classifications have their OWN channel** (see below) — the config export
  covers the *setup*, the line export covers *which journal item carries which item*.

## Line-classification export / backfill — take the per-line data with you (P-05, R28-T3)

*Accounting → Configuration → 现金流量项目归属 导出/回填* round-trips the **transaction-level**
classification (`account.move.line.cn_cash_flow_item_id`) — WHICH journal item carries WHICH
cash-flow item — closing the last P-05 gap (design §3 残留现状 第 1 条). 财会〔2024〕12号 §41
makes providing a data-export interface a statutory obligation on the software provider
(用户数据归用户所有，不得拒绝导出请求), so this is not merely self-imposed.

- **Format = plain UTF-8 CSV** (BOM'd), so a text editor reads it AND Excel shows 中文 —
  columns: `分录ID / 日期 / 凭证号 / 科目编码 / 科目名称 / 借贷 / 金额 / 现金流量项目编码 /
  现金流量项目名称`. The cash-flow item travels as **编码 + 名称**, never a DB id, so the file
  is meaningful without this module (P-05 第②条).
- **Backfill** re-imports the same file after an uninstall→reinstall. The join key is the
  **分录ID** (`account.move.line` id), which is stable on the **same** database (uninstall only
  drops the column; the journal items and their ids are untouched — the exact disaster this
  closes). It **only backfills existing lines, never creates journal items**, and reports every
  row it could not apply (分录ID not found / 项目编码 unknown) so a human decides — a silent skip
  would be as wrong as a silent overwrite.
- **Cross-database limitation**: on a *different* DB the ids differ, so the file stays
  human-readable but is not auto-importable there. Bring the config across first via the config
  export, then re-classify. Acceptance: classify → export → uninstall/reinstall → backfill →
  classifications identical (`tests/test_line_export.py`).

This is unlike a chart-of-accounts module (e.g. the official `l10n_cn`): its
accounts are owned by the `account` module's XML ids, so uninstalling a
localisation layer leaves the accounts in place. Here "clean uninstall" means
*your accounting is untouched*, **not** *your classifications are kept*.

To retire a cash-flow item without losing history, **archive** it (`active=False`)
instead of deleting it — the statement matches items by `code` and is not
active-filtered, so archived items keep their historical figures. A referenced
item cannot be deleted (`ondelete='restrict'`).

## Dependencies

`account`, `account_reports` (Enterprise). **No chart-template dependency** — works on
any Chinese chart of accounts, including the official `l10n_cn` `cn` chart. Verified on
the official `cn` chart: the statement reconciles to the balance sheet in both columns
(ending cash = monetary funds; net increase = period-end − year-begin).
