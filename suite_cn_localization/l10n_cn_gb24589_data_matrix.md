# GB/T 24589.1 国标导出 — 数据元可得性矩阵（Odoo 19 侧，六模块）

> **🗄️ 归档（R19，2026-08-05）**：国标导出线（端口层）转归档——本项目当前做「账」不做「证」（`l10n_cn_design.md` §0.2 / §12.2）。本矩阵与 R17/R18 结论**材料齐备、保留在案**，作为网站文章与客户询问时的现成弹药。**解冻条件** = §0.4 三项外部输入到位 **且** 真实买单客群信号出现。归档期间不买原文、不申请采集工具试用、不再查源码。内容不删。

版本：R18（2026-08-05，替换 R17 骨架版）　状态：**归档（R19）**，只读探查产出，未立项
配套：`l10n_cn_design.md` §13
标准结构来源：GB/T 24589.1-2024 目录与前言（英译预览页，`observed`，待中文原文核对）

---

## 使用须知（先读）

1. **三栏语义**：`直接可得`=有 store 字段直接映射；`需映射可得`=有源但需变换/查代码表/组合；`无源`=Odoo 侧**完全无对应物**。
   **「无源」栏是底座模块的需求规格下界，本轮不设计、不提方案**——它是下一轮输入。
2. **数据元一栏来源标注**：`目录/前言`=R18 已知标准结构；`待原文`=GB/T 24589.1-2024 正文 pp.3–96 未到、元素与必填性待校订。
3. **标准=六模块**（2024 版）：基础档案 / 总账 / 财务报告 / 应收应付 / 固定资产 / 职工薪酬。会计科目、辅助核算 2024 已由总账**移入基础档案**。
4. 证据分级：`verified`=R18 实测（`_fields` 遍历 / 造分录 / 程序化 `_get_lines` / grep-source）；`observed`=源码所得未跑基准。
   模块未安装于本 dev 库者（`account_asset`/`hr_payroll`/`hr.department`/`suite_cn_cashflow`）字段来自 R18 源码实读，标 `verified(source)`。
5. 字段默认 `account.move`(mv,209 字段)/`account.move.line`(ml,120 字段)，store=True 除非注明。

---

## 模块 1 — 基础档案（会计科目 / 辅助核算 / 新增档案表）

### 1a 会计科目（2024 移入本模块）

| 数据元（目录/前言） | 直接可得 | 需映射可得 | 无源 |
|---|---|---|---|
| 科目编码 / 名称 | `account.account.code`/`name`（zh_CN jsonb，M1 已用） |  |  |
| 科目级次 / 上级 |  | M1 `account.group` 分级树 + 点号前缀（M1 verified） |  |
| 科目类别 / 余额方向 |  | `account_type`→国标大类（M1 DALEI）；方向由类型推导 |  |
| 外币 / 数量核算标志 |  | `currency_id` 有无 / 行有无 `quantity` |  |

### 1b 辅助核算（2024 移入本模块）— **数据模型分叉 B3（未决）**

> R17-B3 verified：资产负债类行设 `analytic_distribution` **确实**生成 `account.analytic.line`；`account.analytic.applicability` 有 `applicability=mandatory`+`account_prefix`（按前缀强制必填）。载体 analytic vs 自建 m2o **未决**。下表按「若走 analytic」填。

| 数据元 | 直接可得 | 需映射可得 | 无源 |
|---|---|---|---|
| 辅助核算类别（往来/部门/项目/个人/存货） |  | `account.analytic.plan`（一 plan=一类，无硬上限 observed） |  |
| 辅助项编码 / 名称 |  | `account.analytic.account.code`/`name` |  |
| 分录行↔辅助项 |  | `ml.analytic_distribution`（jsonb，verified；百分比分摊多账户，单值须取唯一键） |  |
| 「往来科目必挂往来单位」 |  | `account.analytic.applicability`(mandatory+account_prefix, verified) |  |
| 存货辅助核算带数量 |  |  | **无源**（analytic 无数量维；走自建载体才可另设）待原文 |

### 1c 往来单位 / 材料 / 单位 / 银行等档案

| 数据元 | 直接可得 | 需映射可得 | 无源 |
|---|---|---|---|
| 往来单位编码/名称/税号 | `res.partner` id/`name`/`vat` |  |  |
| 客户类型 / 供应商类型 |  | `customer_rank`/`supplier_rank` + `res.partner.category`（verified） |  |
| 付款条件 | `account.payment.term`（verified） |  |  |
| 计量单位 | `uom.uom.name`（verified） | + GB/T 17295 国际贸易计量单位码映射（待建代码表） |  |
| 材料 / 材料类型 | `product.product` / `product.category`（verified） |  |  |
| 税种 | `account.tax` / `account.tax.group`（verified） |  |  |
| 项目 |  | `account.analytic.account`（project plan） |  |
| 银行账户 | `res.partner.bank.acc_number`/`bank_id`（verified） | + ISO 9362 BIC / GB/T 12406 货币码 |  |
| 票据类型 |  |  | **无源**（无原生票据类型档案表）待原文 |
| 税务监管（信息） |  |  | **无源**（无原生税务监管档案表）待原文 |

### 1d 用户数据表（2024 新增，「三员」官方位置）

| 数据元 | 直接可得 | 需映射可得 | 无源 |
|---|---|---|---|
| 登录名 / 有效性 / 创建时间 | `res.users.login`/`active`/`create_date`（verified） |  |  |
| 姓名 | `res.users.name`（compute，store=False，来自 partner） |  |  |
| 权限组 |  | `res.users.group_ids`/`all_group_ids`（m2m，verified） |  |
| 个人信息处理范围 |  |  | 待原文明确必填范围（本轮只探可得性，不设计） |

### 1e 业务部门与部门结构（2024 以此替代原部门表）

| 数据元 | 直接可得 | 需映射可得 | 无源 |
|---|---|---|---|
| 部门 / 部门层级 |  | `hr.department`（parent_id 层级，需装 hr；本库未装 verified）**或** analytic plan（本库 3 个 verified） | Odoo 无「会计意义独立部门维度」原生体——与 B3 载体分叉合并（待原文定部门↔辅助核算关系） |

---

## 模块 2 — 总账

| 数据元 | 直接可得（verified `_fields`） | 需映射可得 | 无源 |
|---|---|---|---|
| 凭证编号 / 日期 | `mv.name`/`sequence_prefix`+`sequence_number`/`date` |  |  |
| 凭证字（记/收/付/转） |  |  | **无源**（Odoo 无凭证字，M3 冻结）→退化取值/空，待原文 |
| 分录行（科目/借/贷/摘要/往来/数量/币种/核销号/税） | ml `account_id`/`debit`/`credit`/`name`/`partner_id`/`quantity`/`amount_currency`/`currency_id`/`full_reconcile_id`/`matching_number`/`tax_ids` |  | 摘要：往来(payment_term)行 `name`=空（R17-B2）→须由 `mv.ref`/`name` 合成 |
| **凭证来源表**（2024 新增） |  | `journal_id`+`move_type`+`invoice_origin`+`ref`（另有 source_id/auto_post_origin_id 等，verified） |  |
| **试算平衡表**（2024 新增） |  | **程序化 `_get_lines` 零取数（verified）**：`env.ref('account_reports.trial_balance_report').get_options({})`+`_get_lines(opts)`→49 行/4 列/no_format 数值，无需 UI；M1 已中文化+分级 |  |
| **凭证扩展信息表**（2024 替原基本信息表）附单据数 |  | `mv.attachment_ids` 计数（store o2m，verified；`message_attachment_count` store=False） |  |
| 凭证扩展：制单/记账 |  | `create_uid`（语义偏差，R17）/`write_uid`（近似） |  |
| 凭证扩展：审核人 |  |  | **无源**（无审核人专字段；有 `checked` bool + `audit_trail_message_ids`）待原文 |
| **现金流量凭证数据表**（2024 更名） |  | `ml.cn_cash_flow_item_id`（suite_cn_cashflow，M2 已有；本库未装，字段结构 verified R11-R13）—**待原文逐字段比对**（见 §13 J4，潜在价值最高） |  |

---

## 模块 3 — 财务报告（2024 独立成模块）

| 数据元 | 直接可得 | 需映射可得 | 无源 |
|---|---|---|---|
| 报表集 + 报表项目 |  | `account.report`(50f)/`account.report.line`(27f)/`account.report.expression`(18f) 三层可枚举（verified）；映射为报表集+项目 |  |
| 某报表/某期间/某行取值 |  | **程序化 `_get_lines`（verified）**：BS root→变体（资产负债表·小企业会计准则 id42）→59 行、「30 资产总计」=19611.61 中文行名；同 J2 一条调用路径。M1 已在三层做过加列 |  |

---

## 模块 4 — 应收应付（2024 整体重做，粒度到发票行/核销）

> Odoo 数据齐全但**模型形态与国标表结构差异最大**：发票与会计凭证是**同一条 `account.move`**（F1 verified）。

| 国标表 | 直接可得（verified） | 需映射可得 | 无源 |
|---|---|---|---|
| 应收/应付_发票表 | 同一 `account.move`（`move_type` ∈ out_invoice/in_invoice/out_receipt/in_receipt/…7 值） | 「凭证表」与「发票表」对同一 move 双投影、键=move id/name（取数层主查询形态） |  |
| 发票明细表 | `account.move.line`（display_type 过滤记账行） |  |  |
| 调整表 / 调整明细表 | `move_type` ∈ out_refund/in_refund；`reversed_entry_id`(m2o)+`reversal_move_ids`(o2m) 可识别红字/冲销 |  | 折让/坏账核销**无专用字段**，须业务规则区分（待原文定调整口径） |
| 未结算账款表 | `ml.amount_residual`/`amount_residual_currency`（store compute）/`date_maturity` | 或复用 `account.aged.receivable/payable.report.handler`（本库 present verified） |  |
| 已收（付）资金表 | `account.payment`（81 字段：`move_id`/`payment_type`/`partner_type`/`amount`/`date`/`outstanding_account_id`/`destination_account_id`，verified） | 现金集合与 §11.5 路线甲一致（Outstanding 清算户） |  |
| **资金核销表**（审计最关注） | **逐笔可还原（verified，非硬缺口）**：`account.partial.reconcile`={`debit_move_id`,`credit_move_id`,`amount`,`debit/credit_amount_currency`,`max_date`,`create_date`,`full_reconcile_id`}；`account.full.reconcile`={`partial_reconcile_ids`,`reconciled_line_ids`} | 核销时点近似取 `max_date`(匹配行最大日期,compute)/`create_date`(动作时刻) | 无「专用核销业务日期」字段（近似取值，待原文定必填） |

---

## 模块 5 — 固定资产（模块 `account_asset`，本库未装，字段 verified(source)）

| 国标表 | 直接可得（verified source） | 需映射可得 | 无源 |
|---|---|---|---|
| 资产主数据 | `account.asset`：`original_value`/`salvage_value`/`value_residual`/`book_value`/`acquisition_date`/`prorata_date`/`disposal_date`/`method`(linear/degressive…)/`method_number`/`method_period`/`account_asset_id`/`account_depreciation_id`/`account_depreciation_expense_id`/`state`(model/draft/open/paused/close/cancelled) |  |  |
| **固定资产折旧表**（2024 新增） | 折旧=`account.move`（带 `asset_id`/`depreciation_value`/`asset_remaining_value`/`asset_depreciated_value`/`asset_depreciation_beginning_date`）；posted/draft 由 `move.state` | 查 `asset_id!=NULL & state=posted` 的 move 逐期列出（无独立 line 模型） |  |
| **固定资产增加表**（2024 新增） |  | 购入/在建转固=asset 创建 + `parent_id` 增值子资产（verified source） | 无「增加」专用标志字段，按 action/state 规则区分（待原文） |
| 固定资产减少表 |  | 处置/报废=`asset.modify` wizard（dispose/sell）→`set_to_close`→`state=close`+`disposal_date` | 无「减少」专用标志字段 |
| 固定资产变动表 |  | 原值/年限调整=`asset.modify`(modify/pause) | 无「变动」专用标志字段 |
| 资产分类（GB/T 14885） |  | `account.asset.group`（纯组织，无码，verified source） | **分类码本身无源**（须扩展字段挂 GB/T 14885），待原文 |

> **G5 跨版本暴露（verified source）**：master 重构新增 `account.depreciation.model`（折旧参数从 asset 外移、新增 `method_mode`/`method_rate`+唯一索引）→ 依赖 asset 折旧参数字段的导出层跨版本维护成本高 → **固定资产模块交付顺序后置**，以 `model_id` 作向后兼容锚点。

---

## 模块 6 — 职工薪酬 — **整体无源**

| 国标表 | 直接可得 | 需映射可得 | 无源 |
|---|---|---|---|
| 薪酬相关全部表 |  | `hr.payslip`/`hr.payslip.line`（通用引擎，数据层，verified source） | **无中国薪酬本地化**（enterprise 有 `hr_payroll` 但无 `l10n_cn*payroll`；无社保/个税/五险一金规则）→ **首版显式声明不覆盖职工薪酬模块**（同 E1 写死边界） |

---

## 交付形态（L 组）

| 项 | 结论 |
|---|---|
| 多文件包 | **trivial**（verified source）：DATEV `tempfile`+`zipfile` 打 3 CSV、polizas `io.BytesIO`+`zipfile` 打月度 XML；返回 `{file_name,file_content,file_type:'zip'}`；`account.report.export_file` 泛型助手；`ir.attachment` base64 全量（非流式，大包须注意内存）。命名/单vs多文件规则待原文 5.3/5.4 |
| 字符编码 GB 18030 | **可达**（verified）：编码在 str→bytes 边界（`.encode()` 默认 utf-8，FEC/polizas/DATEV 三处）；Python stdlib 有 `gb18030` codec；在 `file_content` 边界改 `.encode('gb18030')` 即可（QWeb 不强制上游编码）。JSON 输出（2024 新增约定）同理 |

---

## 「无源」栏汇总（下一轮输入，不在本轮设计；待 GB/T 24589.1-2024 原文校订必填性）

1. **凭证字（记/收/付/转）** — Odoo 无（M3 冻结）。
2. **审核人** — 无专字段（有 `checked`/`audit_trail_message_ids` 近似）。
3. **票据类型 / 税务监管档案表** — 无原生专表。
4. **辅助核算余额带数量**（存货类，若走 analytic 载体）。
5. **资金核销 / 固定资产增减变动的「专用业务标志/日期字段」** — 现按 state/action/max_date 规则推导（非专字段）。
6. **固定资产 GB/T 14885 分类码** — 须扩展字段挂载。
7. **职工薪酬模块整体** — 无中国薪酬本地化。

> 以上是「底座模块需求规格」候选。**是否真需、必填与否，以 GB/T 24589.1-2024 原文 + 采集工具（中普/鼎信诺）导入验收为准**（§0.4）。
> 验收范围可先缩小到「基础档案 + 总账」两模块的包能否被读入。本轮不为其设计、不提方案。

---

## 交付子集判断（供参考，非结论）

- SAP S/4HANA 的 `CN_GBT24589_COMMON/GL/APAR/AA` 四类只覆盖六模块中的四个（**缺财务报告 + 职工薪酬**）→ 「首版交付子集」有外部先例。
- 本矩阵实测支持的**低成本子集** = 基础档案(1a/1c/1d) + 总账(试算平衡表/凭证/来源) + 财务报告（程序化 `_get_lines` 零取数）+ 应收应付（核销逐笔可还原）。固定资产后置（G5）、职工薪酬不覆盖。
- 子集是否被采集工具接受，由 §0.4-3 验收回答。**本轮不立项。**
