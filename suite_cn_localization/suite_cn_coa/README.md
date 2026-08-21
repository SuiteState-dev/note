# China – Chart of Accounts Publisher (`suite_cn_coa`)

> **R33-A：模块定位由「科目分级树生成器」升级为「科目表发行方」。** 分级树部分(下方 Parts
> 1–3)保持不动(design §3),存废随 §6.10-A 另定。

新增主职责:**发行国标小企业会计准则(财会〔2011〕17号)科目表**,使装 `cn` chart 的中国公司
【装机即得】一套编码号段正确、我方 BS/PL 四张 form 取得到数、会计认得出的账。

Depends on `account`, `account_reports`, `l10n_cn_reports` (Enterprise).

## Part 0. ASSBE 科目表发行 (R33-A)

**数据** — `models/assbe_chart_data.py` 内嵌 100 条(68 一级 + 32 明细,由 note 仓库
`l10n_cn_assbe_chart_R33A.csv` 确定性生成)。编码=国标号段;`account_type` 唯一硬约束 = 货币
资金 `1001/1002/1012` 必须 `asset_cash`(CF 靠它判现金;其余 type 建错不影响我方 BS/PL——
R33-T0/B-64:BS/PL 只按 `account_codes` 前缀取数、不看 type)。

**两件套** — `post_init_hook` 自动发【通用 88 条】;wizard *会计 → 发行中国科目表* 按
【纳税人身份】(一般 → 三级增值税树 2221001+10 明细 / 小规模 → 二级增值税 2221010)补发。

**发行语义** — 认领优先:按 `(company, code)` 查,已存在则**不改名/type/reconcile**;不存在
则建。幂等、纯 ORM(**不写 `ir.model.data`**,R22-T2 教训:挂我方 xmlid 卸载可能动客户记录),
另记发行台账 `suite.cn.coa.published.account`。§4.7 发行后校验每公司无「有记录无 code」科目
(F3/B-63 静默错报防线)。

**二选一 + 国标口径报表覆盖 (§4.10)** — 星辰国标编号与官方 `cn` 编号在存货段有 1 处碰撞
(`1406`:国标=发出商品 vs Odoo=在产品)。取数口径以我方 101 为准 → 对官方 ASSBE 报表做
**5 处外科覆盖**(改单条 `account.report.expression.formula`/`hide_if_zero`,不 fork 整表):

| # | 报表行 | 改动 |
|---|---|---|
| 1 | BS 行11 在产品 | `1406` → `4001`(国标:在产品=生产成本期末借方=存货) |
| 2 | BS 行12 库存商品 | 补 `1406`(发出商品仍属存货) |
| 3 | PL 行2 营业成本 | `40` → `40\(4001)`(4001 从损益摘掉) |
| 4 | BS 往年未分配利润 | `- 4` → `- 4\(4001)`(4001 从权益摘掉;V6 逼出) |
| 5 | BS 行26 研发费用 | `hide_if_zero=True`(国标 ASSBE BS 无此行) |

🔴 3+4 成对:4001 必须从【损益】和【权益】两处一起摘,才是"只当存货"的完整闭合。**验证**:
`Dr 4001 / Cr 1403 6000` 缺任一处 → 破 `30=53` 差 6000,且我方 crossfoot 守卫【非静默】抓到
(tests `test_v6_balance_regression`)。刻意**不动**:行14/28 排除表(1406 仍属存货应排除、1802
非国标概念)、PL `41`/`44`(4101 制造费用期末应结零、4401 工程施工在 ASSBE BS 无落点,既有
B-60-lite、非本轮引入)。

**卸载语义 (§4.9)** — 🔴 报表 formula **主动写回原值**(`uninstall_hook`;Odoo 不回滚字段值,
残留会让客户卸载后官方报表仍读我方口径且看似正常,比科目被删更隐蔽);发行的**科目留库**
(无 xmlid,卸载器看不见,等同手工建)。发行台账/覆盖台账随模块删。

---
## 分级树部分(原有,§3 本轮不动)

Presentation-layer localisation (呈现层, L0) that also builds the Chinese account-group
hierarchy (科目分级) for the official charts.

> **Renamed in R20.** This module was `suite_cn_ledger` through R19. R20 renamed it to
> `suite_cn_coa` and moved the year-begin / YTD report columns out to `suite_cn_statement`,
> so the **stateful** group builder (this module) and the **pure presentation data** live
> apart. See design §11.2. The wizard models are now `suite.cn.coa.group.builder` and
> `suite.cn.coa.generate`.

## Parts

### 1. `account.group` hierarchy (科目分级)

Official Chinese charts ship **zero** account groups, so the Trial Balance and every
group-aware report render as a flat list. This module builds a
**大类 / 一级科目 / 明细科目** tree:

- **大类** (L1) — one group per statutory top-level category (资产类 / 负债类 /
  共同类 / 所有者权益类 / 成本类 / 损益类), named per chart (a digit means different
  things across charts, e.g. `4` = 生产成本 in `cn` but 实收资本 in `cn_large_bis`).
- **一级 / 明细** — derived from the account codes: any dot-prefix that parents ≥1
  account becomes a group (应交税费 `2221` → 应交增值税 `2221.01` → 销项税额 `2221.01.01`).
  Only the levels a chart actually has are materialised.

`account.group.parent_id` is auto-maintained by Odoo from the prefix nesting, so only the
prefixes are set. Group names copy the account's translations, so they stay bilingual.

**Built two ways:**
- `post_init_hook` — every already-existing company on a supported chart, at install.
- Wizard *Accounting → Configuration → 生成中国科目分级* — the main entry, for companies
  created later, chart switches, or a forced rebuild. Three modes: **新建** (create
  missing), **重建** (wipe & recreate), **仅校验** (report the diff, zero writes).

Idempotent: keyed on `(company, code_prefix)`, never duplicates, safe to re-run and to `-u`.

### 2. Trial Balance = 科目余额表 (no code)

With the groups from part 1 and the Chinese language pack installed, the **native** Trial
Balance already renders 试算表 with 期初余额 ｜ 借方 ｜ 贷方 ｜ 期末余额, folded by
account group — a recognisable Chinese 科目余额表. The strict six-column form (期初/期末 split
by debit/credit direction) is a future optional feature, not in this first version.

### 3. General Ledger = 三栏式明细账 (no code)

Same story as part 2, for the account-detail ledger. With the groups from part 1 and the
Chinese language pack, the **native** General Ledger already is a recognisable Chinese
三栏式明细账: per account it renders 日期 ｜ 借方 ｜ 贷方 ｜ **余额**, where the 余额 column is a
true **running balance** (accumulated line by line) and each account opens with an
**期初余额 (Initial Balance)** row — both native, no code (verified R19-T2:
`account.general.ledger.report.handler` accumulates the balance per line;
`balance_line_{account_id}` is the opening row). This module supplies only the group tree
so it folds the Chinese way.

Not in this version (would require rewriting the GL custom handler / a new report — see
design §11.7): extra dedicated columns (凭证号 / 摘要 / 方向) and the quantity-value
(数量金额式) ledger form. The voucher number and narration already appear *inside* the
detail-line label, just not as separate columns.

## Adopted (manual) groups (R22-T2)

If a **manual** `account.group` you created (or dev residue) already sits on a prefix this
module targets, the builder **adopts** it: it registers its `ir.model.data` on that group
and **renames** it to the Chinese label, rather than duplicating the prefix (which the
no-overlap constraint forbids). The wizard result lists exactly which manual groups were
adopted. Before renaming, the pre-adoption **name (all languages)** and **parent** are
recorded in `suite.cn.coa.adopted.group`, so the change is fully reversible.

A group **owned by another module** (it already has a non-`suite_cn_coa` `ir.model.data`)
is never touched — neither adopted nor renamed.

## Uninstall

Clean, and it restores what it adopted:

- **Module-created groups** — deleted with their `ir.model.data` (zero residue).
- **Adopted (manual) groups** — **kept**; their original name (every language slot our
  rename touched is reset, not just overwritten) and parent chain are **restored**. Uninstall
  releases our ownership instead of deleting the group, so your own分组 survive with their
  original names.

`account.group.parent_id` is `ondelete='cascade'`, so before deleting our created groups the
hook **detaches** any surviving group parented under them — otherwise cascade would take an
adopted child down with its created parent. Parent chains are prefix-derived, so they rebuild
themselves once our groups are gone. `account.account.group_id` is a non-stored compute, so
accounts keep zero residue.

Verified (R16/R20: trial balance identical before install and after uninstall; R22-T2:
adopted group survives an uninstall→reinstall with its original name, no duplicate groups,
cascade never deletes a user's group).

## Notes

- `cn_common` is a **parent** chart template (base of `cn` and `cn_large_bis`), not a
  chart a company can use directly; supported companies are those on `cn` / `cn_large_bis`.
- The Chinese Trial Balance rendering requires the **zh_CN language pack** to be installed
  (a normal step in any Chinese deployment); the translations are shipped by Odoo, not here.
