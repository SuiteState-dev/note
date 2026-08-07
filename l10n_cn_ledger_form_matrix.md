# 中式账簿与凭证版式矩阵（金蝶星辰打印模板解析）

来源：一手材料——金蝶 AI 星辰旗舰版打印模板导出件 15 份（`.prtx` + `.xml`），2026-08-06 取得
用途：M3（记账凭证）、§11.7 账簿类待评估项的版式与字段来源；中式账簿差集的锚点
证据等级：**verified（解析自模板定义文件本身，非截图转录）**。几何、字段绑定、纸张参数逐项从 XML 提取

---

## 0. 使用须知

1. 模板导出件的 `prt_metedata/*.xml` 内含完整布局定义：毫米坐标、字段绑定、字体、边框、合并配置。`.prtx` 为语种资源，`.xlsx` 导出件为打印结果的表格渲染，**无版式信息，不作材料**。
2. 本文件记录**金蝶侧的版式与字段**，不记录 Odoo 侧实现方案。差集表（§5）只判定「有/无/近似」，不设计方案。
3. 套打号前缀区分：`KZ-J1xx` = 账簿类，`KP-J1xx` = 凭证类。`KZ-J104`（科目余额表）与 `KP-J104`（数量外币凭证）编号相同、含义无关。
4. 材料覆盖账簿与凭证，**不覆盖报表**（BS/PL/CF 版式见 `assbe_statement_rows.md`）。

---

## 1. 材料清单

| 模板编码 | 名称 | 类别 |
|---|---|---|
| `kdprint_gl_voucherprt_a4_print2_NEW` | 记账凭证 A4 纸打印 2 张 | 凭证 |
| `kdprint_gl_voucherprt_kpj104_NEW` | 数量外币记账凭证 KP-J104 | 凭证 |
| `kdprint_gl_rpt_vouchersum_prt_s_NEW` | 凭证汇总表 | 凭证 |
| `kdprint_gl_rpt_acctbalance_prt_s_kzj104_1` | 科目余额表 KZ-J104 | 账簿 |
| `kdprint_gl_rpt_subledger_prt_s_NEW` | 明细账套打 297×210 | 账簿 |
| `kdprint_gl_rpt_subledger_prt_cover` | 明细账套打（封面） | 账簿 |
| `kdprint_gl_rpt_subledger_contents_prtpl01` | 明细账目录 | 账簿 |
| `kdprint_gl_rpt_generalledge_prt_s3_NEW` | 总分类账套打 KZ-J101（不打印固定文本） | 账簿 |
| `gl_rpt_generalledge_prt_s2_NEW_copy` | 总账（白纸） | 账簿 |
| `kdprint_gl_rpt_tabularledger_prtpl1` | 多栏明细账 KZ-J107（综合本位币-借方） | 账簿 |
| `kdprint_gl_rpt_tabularledger_prtpl2` | 多栏明细账 KZ-J107（综合本位币-贷方） | 账簿 |
| `kdprint_gl_rpt_qtydetail_prt_kzj105` | 数量金额明细账 KZ-J105 | 账簿 |
| `kdprint_gl_rpt_assistdetail_prt_s_NEW` | 核算项目明细账 | 账簿 |
| `kdprint_gl_rpt_assistdetail_all_NEW` | 核算项目明细账（显示科目） | 账簿 |
| `kdprint_gl_rpt_assistgroup_prtpl` | 核算项目组合表 | 账簿 |

未取得：数量金额总账、核算项目多栏账、核算项目明细表、核算项目综合表、核算项目余额表、费用明细表、调汇历史信息表。

---

## 2. 纸张与排版参数

单位毫米。`splice` = 一页拼版多张。

| 模板 | 纸张 | 方向 | 边距 T/B/L/R | splice | 数据区 W×H @(x,y) | 固定行数 | 字体 |
|---|---|---|---|---|---|---|---|
| 记账凭证 A4-2张 | 210×297 | 竖 | 0/0/0/0 | 是 | 173×98.5 @(27.3, 37) | 5 | 宋体 14 |
| 数量外币凭证 KP-J104 | **240×140** | 竖 | 0/0/0/0 | 是 | LayoutGrid（见 §3.2） | — | — |
| 凭证汇总表 | 210×297 | 竖 | 15/15/19/19 | 否 | 172×24 @(0, 41) | 3 | 宋体 12 |
| 科目余额表 KZ-J104 | 297×210 | 横 | 0/0/0/0 | 否 | 257.5×15 @(30, 30) | 30 | 宋体 12 |
| 明细账套打 | 297×210 | 横 | 10/10/20/5 | 否 | 243×16 @(9.6, 47.6) | 1 | 宋体 12 |
| 明细账封面 | 210×297 | 竖 | 0/0/0/0 | 是 | 无数据区 | — | — |
| 明细账目录 | 210×297 | 竖 | 0/0/0/0 | 是 | 189.5×19.6 @(6.9, 26.4) | 22 | 宋体 12 |
| 总分类账 KZ-J101 | 297×210 | 横 | 0/0/0/0 | 否 | 258.4×15 @(32, 30) | 3 | 宋体 12 |
| 总账（白纸） | 297×210 | 横 | 10/10/19/19 | 否 | 255×16 @(0, 41) | 3 | 宋体 12 |
| 多栏明细账 KZ-J107 | 297×210 | 横 | 0/0/0/0 | 是 | 257×15 @(30, 30.5)，**5 个并存网格** | 3 | 宋体 11 |
| 数量金额明细账 KZ-J105 | 297×210 | 横 | 0/2/0/0 | 是 | 257×15 @(31, 30) | 30 | 宋体 12 |
| 核算项目明细账 | 297×210 | 横 | 10/10/19/19 | 否 | 255×16 @(0, 34) | 3 | 宋体 12 |
| 核算项目明细账（显示科目） | 297×210 | 横 | 10/10/19/19 | 否 | 258.4×16 @(0, 35) | 3 | 宋体 12 |
| 核算项目组合表 | 297×210 | 横 | 10/10/0/0 | 是 | 280.6×20.3 @(9.5, 26.3)，2 个并存网格 | 3 | 宋体 11 |

边框统一 0.5mm 实线 `#212121`。

**两种打印模式并存**：边距为 0 的模板印在预印刷账页上（套打）；边距 10/19 的模板印在白纸上。二者不可合并为同一纸张配置。

---

## 3. 凭证版式

### 3.1 简式（A4 打印 2 张）

构造：`DataGrid` 单表，`dataSource = gl_voucher.entries`，`fixedRowCount = 5`。

| 绑定 | 中文 | 层级 |
|---|---|---|
| `voucherno` | 凭证字号 | 单据 |
| `date` | 记账日期 | 单据 |
| `attachments` | 附件数 | 单据 |
| `explanation` | 摘要 | 分录 |
| `acctdetail` | 科目编码_科目名称_辅助核算 | 分录 |
| `debitamount` / `creditamount` | 借方 / 贷方 | 分录 |
| `debittotal` / `credittotal` | 借方总金额 / 贷方总金额 | 单据 |
| `creatorid.name` | 制单人 | 单据 |
| `auditorid.name` | 审核人 | 单据 |
| `cashierid.name` | 复核人 | 单据 |

页眉另有 `getCompanyName()`、`getPageNumber()/getPageTotal()`。

### 3.2 数量外币式（KP-J104）

构造：**`LayoutGrid`×2 + `CardGrid`×1 + `LayoutCell`×35**，非 `DataGrid`。每条分录为一个卡片块，含 5 个布局子行，行高 8 / 8 / 7 / 7 / 9 mm。

分录区列布局（两子行，摘要/科目/借方/贷方纵向合并跨行）：

```
摘要 │ 科目 │ 币别 │ 汇率 │ 原币金额 │ 借方 │ 贷方
     │      │ 单位 │ 单价 │ 数量     │      │
```

较简式新增的分录级绑定：`currency.name`、`exchangerate`、`amountfor`（原币金额）、`measureunit.name`、`price`、`quantity`。

### 3.3 凭证的两项观察

1. **签字栏五格中仅三格有绑定**。`制单` / `审核` / `复核` 由系统填充；`核准` / `过账` 为静态文本，手签。
2. **大写金额无绑定字段**，为渲染期格式化产物。实测输出为「贰仟玖佰捌拾点零零」「壹点零零」，未按元角分转换。样本 2 例，`observed`。

### 3.4 凭证汇总表

绑定：`acctid.number`、`acctname`、`debitamount`、`creditamount`。
过滤：`vouchergroup`（凭证字）、`periodrange`（期间范围）、`vchnorange`（凭证号范围）。

---

## 4. 账簿类字段绑定

### 4.1 科目余额表 KZ-J104

`begindebit` / `begincredit` / `debit` / `credit` / `enddebit` / `endcredit` —— 期初、本期、期末各拆借贷两栏，共六栏。科目编码与名称为 `label` 型（固定区），非数据列。

### 4.2 三栏式明细账

`month` / `day` / `vchnum`（凭证字号） / `explanation` / `debit` / `credit` / `dc`（方向） / `endbal`。
表头：`firstaccount`（科目）、`periodrange`（期间）、`filter.combo_currency`（币别）。

### 4.3 明细账封面与目录

- 封面绑定：`getCompanyName()`、`periodrange`、`filteraccount`（过滤科目信息）。无数据区。
- 目录绑定：`firstaccount`（科目）、`dot`（引导点）、`page`（页码），`fixedRowCount = 22`。

三者（封面 / 目录 / 正文）为独立模板，构成装订成册的账簿。

### 4.4 总分类账 KZ-J101

`month` / `day` / `acctname` / `explanation` / `debitamount` / `creditamount` / `balancedc`（方向） / `balanceamount`。

### 4.5 多栏明细账 KZ-J107

绑定字段与三栏式明细账同构：`month` / `day` / `type` / `explanation` / `debit` / `credit` / `dc` / `balance` / `seq`。

分析栏无绑定字段——66 个 `DataColumn` 均无 `bindField`，为运行时生成。模板含 5 个并存 `DataGrid`，对应不同分析栏数量的布局变体。

**借方版与贷方版为两个独立模板**，分析栏在单侧展开。

### 4.6 数量金额明细账 KZ-J105

借 / 贷 / 余三组，每组三栏：
`debitqty` / `debitprice` / `debitamount`、`creditqty` / `creditprice` / `creditamount`、`balanceqty` / `balanceprice` / `balanceamount`。
另有 `month` / `day` / `type` / `explanation`。

### 4.7 核算项目明细账（两版）

| | 不显示科目版 | 显示科目版 |
|---|---|---|
| 数据列 | `date` / `type` / `explanation` / `debitamount` / `creditamount` / `balancedc` / `balanceamount` | 同左，**另加** `acctnumber` / `acctname` |
| 表头 | `firstaccount` + `detail` | 仅 `detail` |

即：前者固定科目、展开核算项目；后者固定核算项目、横跨科目。

### 4.8 核算项目组合表

唯一数据绑定为 `rowname`（辅助核算）。其余 18 个 `DataColumn` 无绑定，运行时生成。
表头：`acctlongnameandnumber`（科目长名称含编码）、`periodrange`、`filter.cmb_currency`。

---

## 5. 与 Odoo 19 Enterprise 原生的差集

判定口径：`有` = 原生报表已具备该形态；`近似` = 原生有引擎能力但呈现形态不同；`无` = 原生不存在。

| 中式账表 | Odoo 原生 | 判定 | 说明 |
|---|---|---|---|
| 科目余额表（六栏式） | Trial Balance：期初余额单列、本期借贷、期末余额单列 | **近似** | 期初、期末未拆借贷。加列不可行，须新建报表（§11.7 已列） |
| 三栏式明细账 | General Ledger | **近似** | 缺方向栏；缺封面 / 目录 / 分科目页码 |
| 明细账封面与目录 | 无 | **无** | 原生无「按科目分页、编页码、生成目录、装订成册」概念 |
| 总分类账 | 无独立报表 | **无** | TB 折叠可近似汇总，形态不同 |
| 多栏明细账 | 无 | **无** | 需动态分析栏，借贷分版 |
| 数量金额明细账 | 无 | **无** | 见 §6.3 |
| 数量金额总账 | 无 | **无** | 材料未取得 |
| 核算项目明细账（两版） | `filter_analytic_groupby` 原生 2D | **近似** | 两版对应该 2D 的两个方向（R19-T1 已实测） |
| 核算项目组合表 | 无 | **无** | 需维度×维度，非科目×维度 |
| 记账凭证（简式 / 数量外币式） | 无中式凭证模板（C1 已实测） | **无** | M3 |
| 凭证汇总表（科目汇总表） | 无 | **无** | — |

---

## 6. 结构性发现

### 6.1 方向栏出现在四张账表上

`dc` / `balancedc` 见于三栏式明细账、总分类账、多栏明细账、核算项目明细账。中式账簿在余额侧恒有借 / 贷 / 平方向字，Odoo 以带符号数值表达同一信息。

该项为计算列，不改变取数路径。

### 6.2 明细账为装订册，非单张报表

封面、目录、正文三模板并存，目录含每科目起始页码。该形态服务于存档与稽查调阅场景。

### 6.3 数量、计量单位、单价为同一缺口

`KP-J104`（凭证）与 `KZ-J105`（账簿）所需的分录级 `quantity` / `measureunit` / `price`，在金蝶为凭证分录的一等字段，任何分录均可填。

Odoo `account.move.line` 具备 `quantity` / `price_unit` / `product_uom_id`，但仅发票行填充；存货计价、工资、手工分录为空。材料样例（暂估采购入库：1405 库存商品 / 2202004 应付账款_暂估应付）正属该类。

二者为同一 L1 加维度缺口，非两项。

**约束**：不得直接写入 `account.move.line.quantity` / `price_unit`——该二字段承载 Odoo 自身发票语义，覆写威胁 P-01。载体须为独立字段。

### 6.4 打印审计痕迹

除凭证外的全部账簿模板页脚含 `getUserName()`（打印人）与 `now()`（打印时间）。

---

## 7. 待办

- [ ] 取数量金额总账、核算项目多栏账 / 明细表 / 综合表 / 余额表四张模板，补全核算项目六张形态
- [ ] 大写金额转换缺陷（§3.3-2）扩大样本至 10 例以上后方可定级
- [ ] 多栏账分析栏的展开规则未知（按下级科目 or 按核算项目）——模板不含该信息，须从产品界面另查
- [ ] 核算项目两版与 `filter_analytic_groupby` 的逐项对照，产出「原生可覆盖 / 需中文化 / 需自建」三态表
- [ ] §5 判定表中「近似」三项，须在真实客户库上验证中国会计是否「认得出」

---

## 8. 材料保管

模板导出件为金蝶产品的配置文件，仅作版式与字段来源参考，不得复制其布局文件或将其内容写入交付物。本文件记录的是版式事实（纸张尺寸、栏目构成、字段语义），该类事实为中国会计法定账簿的通用形态，非金蝶专有。
