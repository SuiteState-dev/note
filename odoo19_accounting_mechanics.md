# Odoo 19 会计机制实测库 · Odoo 19 Accounting Mechanics — Verified Behaviours

> **性质 / Nature** — 活文档。每踩一个新坑加一条。
> 只收录**官方文档没有写、或写了但与实机行为不符**的行为。
> A living document. One entry per pitfall. Only behaviours the official documentation does not
> describe — or describes incorrectly.

| | |
|---|---|
| **版本锁定 / Version** | Odoo 19 (Enterprise + `mrp_account`) — 所有条目仅对 v19 有效 |
| **维护者 / Maintainer** | SuiteState |
| **域 / Scope** | **Odoo accounting 的系统机制。** 目前覆盖两个场景:**① 存货估值 ↔ 总账**(B-01 ~ B-35, B-47, B-49, B-57 ~ B-59)、**② 制造成本**(B-34, B-36 ~ B-52)。<br>脊梁是 **[B-13](#b-13) 总定理**(两本账 / 三道门)—— 两个场景都是它的推论落地。 |
| **编号约定 / Numbering** | **`B-xx` 是稳定 ID,永不重编。** 章节号只是导航层。外部引用一律用 `B-xx`。 |
| **合并说明** | **2026-07-15** — 原 `odoo19_verified_behaviours.md` + `odoo19_manufacturing_cost.md` + `odoo19_index.md` **三文件合并为本文件**。理由:决策问题天然跨场景(例:"生产库位配什么科目" = B-13 门② + B-39 + B-47 + B-51),分文件必然发漏上下文。`B-xx` ID 与锚点全部沿用,零迁移成本。测试规格(`odoo19_test_specs.md`,面向开发分支)是不同受众,**仍独立**。 |
| **最后更新 / Updated** | **2026-07-19** — 新增 **B-57 / B-58 / B-59**（landed cost 零库存幽灵单价 + 重估过的账单撤销 + 开票早于发货的成本发散）。**B-13 / B-17 / B-27 打修订标**（见「旧条目修订」表）。B-17 原文「差异科目」措辞作废，落点定论为 **LC 成本行 `account_id`**。<br>**2026-07-15** — 合并 + 新增 **B-47 ~ B-56**(periodic 完整机制 + real_time 回填/跨期人工错期:T-10 ~ T-18)。**B-13 / B-35 / B-39 / B-45 / B-46 / B-47 / B-51 打修订标**(见两个「增补」章 + 「旧条目修订」表)。**`real_time` 跨期人工错期这条线正式闭合**(机制根因 [B-54](#b-54) → 对策可行性 → 对策边界 [B-55](#b-55))。 |

---

## 图例 · Legend

| 符号 | 含义 CN | Meaning EN |
|---|---|---|
| 🔴 | 高危:静默产生永久性错误,系统不报警 | Critical: silent, permanent corruption, no warning |
| 🟡 | 中:需要操作纪律,否则数据失真 | Medium: requires discipline or data degrades |
| 🟢 | 低:需知道,但不易出事 | Low: worth knowing, unlikely to bite |
| ✅ | 已实机验证 | Verified on a live instance |
| 📖 | 已源码确证 | Confirmed against source code |
| 🔬 | 待验证(推论) | Inferred — not yet tested |

---

## 🔴 阅读顺序 · Reading order

> **[B-13](#b-13) 是【总定理】。全库所有条目都是它的推论。**
> **不先读 B-13,后面全部读不懂。**

---
---

# 决策速查 · Decision Index

> **这一章是本库的入口。碰到决策问题,先在这里定位,再点进 `B-xx` 看机制。**
> **每条答案都随【`periodic` / `real_time`】分叉 —— 这是 v19 会计机制的第一根轴。**

---

## Q1 · 生产库位配什么 `account_type`?

| 你的情况 | 配法 | 依据 |
|---|---|---|
| **不做制造** | 不配。但要知道:**MO 全程零 GL**,生产车间在总账上是黑洞 | [B-34](#b-34) |
| **制造 + `real_time`** | **`expense_direct_cost`**,命名 `Manufacturing Cost Variance`。它是**纯差异容器**(里面没有真 WIP)。AVCO/FIFO 下恒 0;Standard 下差异自动落 COGS 段,零手工分录 | [B-39](#b-39) [B-46](#b-46) |
| **制造 + `periodic`** | 🔴 **不能照搬上面。** periodic 下这个科目是**吸收科目**,不是差异容器,会挂逐月累积的贷方(负成本)→ 毛利虚高。**正解:新建一个隔离的 overhead 科目**(`expense_direct_cost`),生产人员 payroll 转拨进它、关账吸收贷方也落它 → 自然对冲 | [B-48](#b-48) [B-51](#b-51) |

> **一句话:`real_time` 下它装差异,`periodic` 下它装「吸收 − 归集」。类型都用 `expense_direct_cost`,但 periodic 必须隔一层、把工资归集也引进来。**

## Q2 · `periodic` 还是 `real_time`?

| 你的情况 | 选 | 为什么 |
|---|---|---|
| **做制造** | 🔴 **必须 `real_time`** | periodic 下 ① 人工永不进 GL([B-45](#b-45)) ② **连按单 COGS 行都不存在**([B-47](#b-47))——整个"按单成本"概念在总账上消失 |
| **要按单 / 按台毛利**(哪怕不制造) | 🔴 **必须 `real_time`** | 同上,[B-47](#b-47):periodic = 真·定期盘存制,COGS 是隐式的(采购费用化 − 关账资本化未售存货) |
| **存货非主要资产、不做制造、不看按单毛利**(耗材/包材/办公品) | `periodic` 可以 | 省掉实时估值开销;代价是关账那台橡皮擦成为**唯一**入口([B-31](#b-31)) |

> **`real_time` = 你有三个地方会出错,但每处留痕;`periodic` = 你只有一个地方出错,但它不留痕。**

> ⚠️ **`real_time` 仍是制造/按单毛利的唯一可行选项**(periodic 连人工和 COGS 都没有,是更根本的残缺)。**但它只解决了「人工进不进 GL」,没解决「人工进对期」** —— labour GL 硬编码今天([B-54](#b-54)),工资跨期(月底发工资、天天生产 = 制造业常态)时人工成本按月**结构性错期**,关账不拉平([B-55](#b-55))。对策=会计手工可逆预提,不是 mrp WIP 向导。

## Q3 · 成本法选 Standard / AVCO / FIFO?

**先看约束(机制,不是偏好):**
- 开了 **lot 估值** → **AVCO 与 FIFO 对任何 lot 产出完全相同的成本**(lot 内无 FIFO 层,[B-20](#b-20))→ 这道题退化成**「Standard 还是不 Standard」**
- 🔴 **原料和成品必须【一起】用 Standard**([B-38](#b-38) 修订记录 / T-03):混搭 → 采购价差涌进 WIP,与制造差异永久不可分

| 你的情况 | 选 |
|---|---|
| 贸易/分销 + 序列号(ElectroState) | **AVCO 或 FIFO**(lot 估值下等价),开 lot 估值 |
| 制造 + 没有专职成本会计 | **AVCO** |
| 制造 + 有人**每月真的**打开差异科目看 | **Standard**(原料+成品一起),接受"差异不可分解" |
| 想用 Standard 但没人看差异 | 🔴 **别用。** 没人看的差异 ≡ 没有差异,此时 Standard **严格劣于** AVCO(你只多买了"每月清 WIP"的负担) |
| 🔴 `periodic` + `Standard` | **最差组合。** 5 的标准差异和 30 的人工混进同一个数(−25),连剥都剥不出来 → [B-48](#b-48) |

## Q4 · 想要「按品类 / 按台」的颗粒度?

> **唯一杠杆 = 给每个品类分派【不同的估值科目】。**([B-35](#b-35))
> 关账凭证按估值科目聚合,共用科目 = 混成一坨;拆科目 = 天然分行。
> **⚠️ 上线期决策,补做要迁移历史科目余额,代价极高。**

## Q5 · 混用 `periodic` / `real_time`,估值科目能共用吗?

> 🔴 **不能共用,必须拆。**([B-35](#b-35) 修订 / T-11)
> 共用科目下关账凭证能按【组件】拆(库位重分类 vs Stock Variation,各带 label),**但不能按【品类】拆** —— `Stock Variation Global` 那一行是全公司聚合,两个品类的差额混在同一行。
> 拆开后:periodic 的活动全落它自己的科目,real_time 的科目关账零行,天然按品类分离。

## Q6 · 关账能修数据差异吗?

> 🔴🔴 **不能。关账是橡皮擦,不是校正器。**([B-31](#b-31))
> 它把一切 L1/L2 背离**不加区分**扫进 Stock Variation。结构性错误(退货没开贷记单、开票≠发货、删已过账账单、超额开票)**一旦扫进去就被合法化成一笔费用,线索永久消失。**
> **铁律:结构性错误必须在按 Generate Entry 之前,用【已过账口径】的数量勾稽清掉。**

## Q7 · 上了 Manufacturing,总账里却没有 WIP / 生产成本?

> **默认就是这样。**([B-34](#b-34))
> 生产库位默认不配估值科目 → 整段 MO 零 GL,存货余额从原料直接跳到成品,WIP 从没存在过,关账一把扫平,没人发现。
> 要让制造进 GL → 显式配生产库位 `valuation_account_id`(见 Q1)。想在总账看到**真·在制品**(跨期未完工)→ 库位科目抓不到,只能用 `account_production_wip_account_id` 的【手工预提+次日红冲】向导([B-46](#b-46) 补注)。

## Q8 · 人工 / 机器折旧怎么进成品成本?

> `costs_hour` 是**预定制造费用吸收率**,纯手工填,Odoo 不从折旧倒算([B-42](#b-42))。
> **通则**([B-51](#b-51)):**转换成本的归集科目必须 = 吸收贷方的科目**,才能自然对冲。
> - `real_time`:吸收贷方落 `workcenter.expense_account_id` → 把 payroll/折旧归集到同一科目
> - `periodic`:吸收贷方落**生产库位科目** → 把 payroll/折旧归集到那个隔离 overhead 科目(Q1)
> 一台设备 = 一个工作中心 = 一个费用科目([B-41](#b-41));`costs_hour` 需季度复核 SOP([B-42](#b-42))。
> ⚠️ **跨期免责**:`real_time` 下 labour GL 锁今天([B-54](#b-54)),工资跨期时人工成本按月错期,payroll 对冲 SOP **只在 `periodic` 严格成立**([B-55](#b-55) [B-56](#b-56))。`real_time` 需回填过去期生产 → 用会计手工可逆预提兜底,mrp WIP 向导补不了(状态过滤 + 科目解耦两个死因)。

---
---

# 总索引 · Master Index

> **`B-xx` → 场景 / 章节。ID 全局唯一,永不重编。**

### 场景 ① · 存货估值 ↔ 总账

| ID | 条目 | 等级 |
|---|---|---|
| **[B-13](#b-13)** | 🔴 **总定理:GL 的入口** —— 单据 ∪ 库位科目 ∪ 期末关账。门②(库位科目)只对 `real_time` 生效;`periodic` 塌缩进门③ | 🔴 |
| **[B-01](#b-01)** | 账单价格 ≠ PO 价格 | 🟡 |
| **[B-03](#b-03)** | 重新开票 → 估值自动更新 | 🟢 |
| **[B-47](#b-47)** | 🔴 **`periodic` = 真·定期盘存制:账单进 P&L,卖出无 COGS 行**(增补) | 🔴🔴 |
| **[B-02](#b-02)** | 删除已过账账单 → 总账与库存永久分裂 | 🔴 |
| **[B-59](#b-59)** | 🔴🔴 **开票早于物理发货 → COGS 与出库价值取两套成本，永久发散（无人犯错）**（新增） | 🔴🔴 |
| **[B-58](#b-58)** | 🔴 **停留在撤销状态的已重估账单 → 成本层粘住、GL 回滚；存货科目现贷方余额**（新增） | 🔴 |
| **[B-04](#b-04)** | 收 10 开 20 → 总账进 20,库存进 10 | 🔴 |
| **[B-14](#b-14)** | 账单晚于发货 + 价格变动 → 差额进 Stock Variation,总数不错、分类错 | 🔴 |
| **[B-27](#b-27)** | 客户发票晚于供应商账单 → COGS 仍锁死在旧成本 | 🔴 |
| **[B-16](#b-16)** | 价差科目是 Standard 专属;同一条 move 上住着两个成本 | 🟡 |
| **[B-05](#b-05)** | Lot 估值确实进会计链路 | 🟡 |
| **[B-20](#b-20)** | 同一 lot 多次收货 → 成本坍缩为加权平均 | 🟡 |
| **[B-21](#b-21)** | 🔴 `lot.avg_cost` 是在库均价,不是成本 —— lot 发空即归零 | 🔴 |
| **[B-17](#b-17)** | LC 按 move 级分摊 = 每 lot 一份;已发货部分按设计留【LC 成本行科目】(⚠️ 措辞修订 2026-07-19) | 🟡 |
| **[B-57](#b-57)** | 🔴🔴 **LC 对 `remaining_qty=0` 的收货 move 仍重算估值 → 零库存幽灵单价**（新增） | 🔴🔴 |
| **[B-18](#b-18)** | 不开 lot 估值,后到运费污染早批次成本 | 🔴 |
| **[B-15](#b-15)** | 🔴 报废/盘亏出不出分录,取决于库位有没有配科目(默认不配) | 🔴 |
| **[B-19](#b-19)** | Adjust Valuation 没被移除,它搬家了 —— 但它 ⊥ GL | 🔴 |
| **[B-28](#b-28)** | 手工估值写入全部只动报表侧 | 🔴 |
| **[B-09](#b-09)** | 寄售:仓库侧干净,异常在开票那一刻 | 🔴 |
| **[B-06](#b-06)** | Stock Valuation 报表 Unit Cost 是产品级,价值侧是 lot 级 | 🟡 |
| **[B-07](#b-07)** | Lot 维度无任何标准报表支持 | 🟡 |
| **[B-10](#b-10)** | Margins 晚启用 → 历史订单毛利永久错误 | 🟡 |
| **[B-11](#b-11)** | 发货前毛利是估计值,发货后才锁定 | 🟢 |
| **[B-08](#b-08)** | Stock Variation 对方科目取值链;配错则静默失效 | 🔴 |
| **[B-12](#b-12)** | Stock Variation 是净额,掩盖大额对冲错误 | 🔴 |
| **[B-29](#b-29)** | 关账凭证是永久增量分录,无红冲 | 🟡 |
| **[B-30](#b-30)** | 🔴 `real_time` 公司的自动关账 cron 永远不跑 | 🔴 |
| **[B-31](#b-31)** | 🔴🔴 关账是橡皮擦,不是校正器 | 🔴🔴 |
| **[B-32](#b-32)** | 盘点 `Accounting Date` 填了才倒填得动 | 🟡 |
| **[B-33](#b-33)** | 三个虚拟库位;报废库位靠 `min(id)` 抽签 | 🟡 |
| **[B-35](#b-35)** | 🔴 关账凭证按【估值科目】聚合 —— 唯一颗粒度杠杆(⚠️ 混用拆科目见增补) | 🔴 |
| **[B-49](#b-49)** | **`action_close_stock_valuation` 对未来期不过账 → 凭证卡 draft**(增补) | 🟡 |
| **[B-22](#b-22)** | 🔴 `qty_invoiced` 包含草稿账单 | 🔴 |
| **[B-23](#b-23)** | 🔴 PO 的 `invoice_status` 公式里根本没有收货量 | 🔴 |
| **[B-24](#b-24)** | 删除已对账的银行对账行 → 付款变孤儿 | 🔴 |
| **[B-25](#b-25)** | `to_refund` 决定退货扣不扣 `qty_received` | 🟡 |
| **[B-26](#b-26)** | 🔴 `parse_version` 剥尾零 → 补零升位 = migrations 静默不跑 | 🔴 |

### 场景 ② · 制造成本

| ID | 条目 | 等级 |
|---|---|---|
| **[B-34](#b-34)** | 🔴 生产库位不配估值科目 → 整段 MO 零 GL(Odoo 默认) | 🔴 |
| **[B-36](#b-36)** | 🔴 工时成本进 GL 的三个必要条件 | 🔴 |
| **[B-37](#b-37)** | GL 路径 ⊥ 分析路径 | 🟡 |
| **[B-38](#b-38)** | 🔴 Standard 在 MRP 里是硬约束;差额滞留 WIP | 🔴 |
| **[B-39](#b-39)** | 🔴 生产库位科目 = 纯差异科目;余额随成本法变(⚠️ periodic 例外见增补) | 🔴 |
| **[B-40](#b-40)** | `periodic`:MO 时零 GL,价值流月末才被扫进 GL | 🟡 |
| **[B-41](#b-41)** | 拆科目 = 拆工作中心 | 🟡 |
| **[B-42](#b-42)** | 🔴 `costs_hour` 是预定制造费用吸收率 —— 纯手工填 | 🔴 |
| **[B-43](#b-43)** | 🔴 吸收差异 ⊥ 库存关账 | 🔴 |
| **[B-44](#b-44)** | 🔴🔴 关账不扫 `real_time` 的 WIP 标准差异 | 🔴🔴 |
| **[B-45](#b-45)** | 🔴 `periodic` 的库位重分类只抓料件价值流(⚠️ 见增补) | 🔴 |
| **[B-46](#b-46)** | 🗑️ 已作废 —— 科目里只有差异,没有真 WIP(⚠️ 限 real_time,见增补) | 🗑️ |

### 🆕 场景 ①②交汇 · 2026-07-15 增补(periodic 完整机制)

| ID | 条目 | 等级 |
|---|---|---|
| **[B-47](#b-47)** | 🔴🔴 `periodic` = 真·定期盘存制:采购即费用化,卖出无 COGS 行 | 🔴🔴 |
| **[B-48](#b-48)** | 🔴 `periodic` 的生产库位科目 = 转换成本吸收科目,不是差异容器 | 🔴 |
| **[B-49](#b-49)** | `action_close_stock_valuation` 对未来期不过账,凭证卡 draft | 🟡 |
| **[B-50](#b-50)** | `expense` 型科目可挂 `location.valuation_account_id`,Odoo 无约束/报错/警告 | 🟡 |
| **[B-51](#b-51)** | 🔴 `costs_hour` 是两模式共用吸收率;通则:归集科目 = 吸收贷方科目(⚠️ real_time 跨期对冲失效见 [B-55](#b-55)) | 🔴 |
| **[B-52](#b-52)** | 🔴(测试纪律)回填月份关账,单据链上所有 move 必须同期回填 | 🔴 |
| **[B-53](#b-53)** | 🔴 `real_time` 存货 GL 入账日 = `force_period_date or today`,与 `move.date` 解耦 | 🔴 |
| **[B-54](#b-54)** | 🔴🔴 `_post_labour` GL 日期硬编码 today,人工成本无法回填到过去期 | 🔴🔴 |
| **[B-55](#b-55)** | 🔴🔴 [B-51](#b-51) payroll 对冲只在 `periodic` 成立;`real_time` 跨期人工错期结构性、关账不可修;对策=手工可逆预提(mrp WIP 向导补不了) | 🔴🔴 |
| **[B-56](#b-56)** | `periodic` 跨期 OVH 摆动对称(工资早+90/生产早−90);SOP 双向警告,看累计 | 🟡 |

---
---

# 方法论 · Methodology

> **六条,血换的。反复用得上。**

1. **错误的模型也能自洽地解释全部实测数据。** 跨大版本问题:**先确认架构,再解释数据。**
2. 🔴 **非判别性证据不能验证假设。** 一组在两个假设下会给出**相同结果**的数据,不能用来验证其中一个。**测试必须存在一种能让假设【死掉】的结果。** → B-34 和早期几轮 MRP 测试都栽在这。
3. 🔴 **手工 `write` 到一个【本该由系统算出来】的字段上,就切断了那条链路的重算 —— 然后你观察到的是【自己造的假象】。** → B-34(手工 `mark_done` 跳过 `action_assign()`)、B-17(手工写 `lot.standard_price`)。**测试必须走真实业务路径:真 PO、真收货、真计价。**
4. **专家的通用失败模式:手里握着能推翻自己结论的事实,却没把推理走完。** → B-13 的源码块里 `valuation == 'real_time'` 从第一天就抄进来了,但定理表格没写,于是所有人照表格推错好几天。**抄了源码 ≠ 读懂源码。源码块与结论表格必须逐条对齐。**
5. 🔴 **不要用【未验证的推论】去作废一个【已验证的结论】。** → B-46 就是这么诞生又这么死掉的。**这比推理不足更糟,是纯粹的倒退。**
6. 🔴 **被污染的输出,不能当【任何】假设的支持证据 —— 哪怕只当一条旁证。** → B-44 修正记录:拿被 62 万存货污染的共享库输出当旁证。**「先跑再信」是唯一防线。**

---
---

---
---

# 场景 ① · 存货估值 ↔ 总账
## Scenario ① · Inventory valuation ↔ the GL

# 第一章 · 估值架构基线：v19 在什么时候记账
## Chapter 1 · The valuation baseline — when v19 actually books

> v19 的 Perpetual 是 **at invoicing**。收货不产生任何会计分录，**供应商账单是估值的唯一来源文档**。
本章三条确立这个基线 —— 后面所有的坑，都是这个基线的推论。

In v19, Perpetual means *at invoicing*. Receipt posts nothing; the **vendor bill is the sole
valuation source document**. Everything else in this library follows from that.

---

<a name="b-13"></a>
## 1.1 · B-13 · 🔴 总定理：GL 只有三条入口
### The master theorem: only three roads write to the GL

| | |
|---|---|
| **等级** | 🔴（**本库所有条目的地基**） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |
| **修订** | **2026-07-14 — 从「收货零分录」升级为总定理。** 原版只说了「收发货不落账」，没说清**什么才落账** |

### 🎯 定理 / The theorem

> **v19 里，库存估值（L1）和总账（L2）是两本各自独立的账。**
>
> **L1 · 估值子账** —— `stock.move.value` / `remaining_qty` / `lot.standard_price` /
> `product.standard_price` / `quant.value` / `product.value`。
> 取值按优先级链现算：**`manual > bill/inv > po/so > std price`**。
> **它自己永远不写 `account.move`。**
>
> **L2 · 总账** —— `account.move` / `account.move.line`。
> **只有三条路能写它：**

| # | 入口 | 触发条件 | 载体 |
|---|---|---|---|
| **①** | **单据** | 供应商账单 / 客户发票**过账**，且 `valuation == 'real_time'` | `account.move` |
| **②** | **库位科目** | move 的**两端库位里有一端挂了 `valuation_account_id`**<br>🔴 **且 `product.valuation == 'real_time'`** —— 见下方分叉 | `stock.move.account_move_id` |
| **③** | **期末关账** | 手工 Generate Entry 或 cron（[B-29](#b-29)） | `res.company.action_close_stock_valuation` |

> **除此之外，任何物理移动、任何估值变更，都不产生一条会计分录。**
>
> Outside these three roads, no physical movement and no valuation change ever books anything.

### 🔴🔴 门② 的分叉：`real_time` 才有三条路，`periodic` 只有两条

**2026-07-14 · T-02 实测。这是对本定理的重大修正。**

| 产品估值 | 门② 的行为 |
|---|---|
| **`real_time`** | ✅ **独立入口。** 移动发生的**那一刻**即时出分录 |
| **`periodic`** | 🔴 **移动时零分录。** 门② **塌缩进门③** —— 价值在**期末关账**时，由「库位重分类」(*Closing: Location Reclassification*) 聚合搬入 |

**实测 / Observed（Scrap 库位已配 `valuation_account_id = 191000`）：**

```
real_time 产品报废：  scrap move value=100  |  account_move_id = True
                          Dr 191000 报废库位科目  100
                          Cr 110100 存货科目           100      ← 门② 即时触发 ✅

periodic  产品报废：  scrap move value=100  |  account_move_id = False   ← 🔴 零分录
关账后：              关账凭证在 191000 上：Dr 100                        ← 这时才落地
                      periodic scrap move 的 account_move_id（复查）= False
                      （价值靠【聚合】搬入，不挂回原 move）
```

> ## **所以：v19 的 GL 入口不是「三条」，是「`real_time` 三条 / `periodic` 两条」。**
>
> **这也解释了 B-45：关账的库位重分类之所以只扫 `periodic`
> (`_get_location_valuation_vals` 的域 `('product_id.valuation','=','periodic')`)，
> 不是因为关账偏心 —— 而是因为 `periodic` 的库位价值流【本来就没进过 GL】，
> 关账是它【唯一】的入口。**

### 📌c 2026-07-19 补 · 门② 分叉在 landed cost 上的落点 📖

`stock_landed_costs/models/stock_landed_cost.py:124` —— `button_validate` 的分录循环开头：

```python
if product.valuation != "real_time":
    continue          # ← periodic 产品做 LC：零 GL 分录
```

但同一个方法末尾的 `:152` 重算估值【不带任何过滤】：

```python
cost.valuation_adjustment_lines.move_id._set_value()
```

> **所以 periodic 产品做 LC = 估值层照调、GL 零分录** —— 门② 分叉在 LC 上的直接落点，
> 价值要等到期末关账才被扫进 GL（门③）。
>
> 🔴 **而 `:152` 的【无条件】正是 [B-57](#b-57) 的同一个根：
> GL 侧有门控（`remaining_qty` / `valuation`），成本层侧一律全额写入。**

### ⚠️ 修正记录：源码一直在，是我们没读

> **上面的源码块里，`and self.product_id.valuation == 'real_time'` 这一行【从第一天就抄进来了】。**
> **但定理表格的门② 那一行没写上去，于是所有后续推理都照着表格走。**
>
> **教训：源码块与结论表格必须【逐条对齐】。抄了源码 ≠ 读懂了源码。**

### 源码 / Source 📖

`stock_account/models/stock_move.py:651`：

```python
def _should_create_account_move(self):
    return self.product_id.is_storable and self.is_valued \
        and (self.location_dest_id.valuation_account_id       # ← 关键闸门
             or self.location_id.valuation_account_id) \
        and not float_is_zero(self.quantity, ...) \
        and self.product_id.valuation == 'real_time'
```

`Vendors → Stock` 和 `Stock → Customers` 的**两端库位都没有 `valuation_account_id`**
→ 闸门关闭 → **零分录**。这就是「收货不出分录」的真正机制。

`stock_account/models/stock_move.py:220` —— 落账时的方向：

```python
if self.location_id.valuation_account_id:          # 货【从】挂科目的库位来（盘盈）
    debit_acc  = product._get_product_accounts()['stock_valuation']   # Dr 110100
    credit_acc = self.location_id.valuation_account_id                # Cr Loss
else:                                              # 货【去】挂科目的库位（盘亏/报废/货转固资）
    debit_acc  = self.location_dest_id.valuation_account_id           # Dr Loss/固资
    credit_acc = product._get_product_accounts()['stock_valuation']   # Cr 110100
```

日记账 = `company.account_stock_journal_id`；`sudo()` 创建；**当场 `_post()`**。

**✅ 两个方向均已实测（2026-07-14 · T-06 补齐盘盈方向）：**

```
盘亏 / 报废 / 货转固资（货【去】挂科目的库位）：
    Dr  <库位科目>          Cr  110100 存货
盘盈（货【从】挂科目的库位来）：
    Dr  110100 存货         Cr  <库位科目>       ← 与盘亏严格相反 ✅
```

**盘盈单价 = 产品 `standard_price`**（AVCO 下）；**开了 lot 估值的产品则取 lot cost。**
**双边落实科目、`real_time` 即时过账、报表与 GL 同步 → 对期末差额【零贡献】。** ✅

### 30 秒确认动作 / The 30-second check

**在目标实例上收一次货，然后看 Journal Items。**

| 结果 | 含义 |
|---|---|
| **零分录** | ✅ 确认是 v19 的 Perpetual (at invoicing) 架构 |
| **有分录** | ❌ 不是 v19 的 at-invoicing 模式 —— 本库全部条目的前提不成立 |

### 🔴 三个直接推论 / Three corollaries

**① 两本账之间唯一的自由度是【数量】。**

```
L2(GL)  存货借方 = 【已过账开票数量】 × 账单价
L1(子账) 存货价值 = 【实收数量】       × 成本
                                         ↑
              「账单价 = 成本」（B-01 / B-16：AVCO/FIFO 下账单价就是估值价）
              → 价格两边同源 → 唯一可能分裂的只剩【数量】
```

**这就是为什么数据完整性守卫必须锚在数量上，而不是价格上。**
唯一的例外是**时点**（[B-14](#b-14)）：货先走了，账单价的回写只能补到还在库的那部分。

**② 报表 ≠ 会计报表。**
「库存估值报表」在 v19 里是一张**成本报表**。它和总账**应该**相等 —— 但那是个**结果**，
不是**约束**。系统既不强制，也不告警。

**③ 「哪些动作出分录」从死记变成可推导。**
问三个问题：**是不是单据过账？两端库位有没有挂科目？是不是期末关账？**
三个都不是 → **不出分录。**

---

<a name="b-01"></a>
## 1.2 · B-01 · 账单价格 ≠ PO 价格
### Bill price differs from PO price


| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 实机验证 |
| **前提** | v19 · Perpetual (at invoicing) · Bill Control = Received quantities |

### 场景 / Scenario
PO 单价 100，供应商实际开票单价 120。

### 实测结果 / Observed
库存估值 = **已收货数量 × 账单价格**（不是 PO 价格）。

Inventory valuation = *received quantity* × ***bill price*** — not the PO price.

### 机制 / Mechanism
v19 的 Perpetual 是 **at invoicing**：收货不产生任何会计分录，估值的唯一来源文档就是**供应商账单**。
所以账单价格天然就是估值价格 —— 这不是"重估"，v19 里根本没有"先按 PO 价入账再重估"这一步。

In v19 Perpetual, the vendor **bill is the valuation source document**. There is no
"book at PO price, then revalue" step — that concept belonged to v18 and earlier.

### 后果 / Consequence
正常行为，不是 bug。但如果你的团队习惯了 v18 的心智模型（收货即入账），会对时点产生误判。

### 对策 / Mitigation
无需处理。理解机制即可。

---

<a name="b-03"></a>
## 1.3 · B-03 · 重新开票 → 估值自动更新
### Re-billing refreshes the valuation


| | |
|---|---|
| **等级** | 🟢 |
| **状态** | ✅ 实机验证 |

### 实测结果 / Observed
删除账单后，若对同一 PO 重新开票并过账，库存估值**自动更新为新账单的价格**。

After deletion, re-billing the same PO and posting refreshes the valuation to the new bill price.

### 后果 / Consequence
B-02 的缺口是**可自愈的** —— 但只有在重新开票的前提下。这正是 B-02 危险的地方：
补救动作存在，但没有任何机制**提醒你去做**。

The B-02 gap self-heals *if* you re-bill. The danger is that nothing prompts you to.

---


# 第二章 · 🔴 开票异常：总账与库存分裂的六条路
## Chapter 2 · Billing anomalies — six ways to split the GL from stock

> 本章各条都是**静默的、永久的、无告警的**数据腐蚀。
它们的共同点：分录已经过账，而库存子账走了另一条路，**没有任何机制会回头修正**。

> ⚠️ **注意末两条（[B-58](#b-58) / [B-59](#b-59)）的性质不同：**
> 前四条都需要有人做了一个可指认的动作（多开票、删单、手工改数量）；
> **B-59 不需要任何人犯错** —— 收货、开票、发货三步全对，发散照样产生。

All entries here are silent, permanent and unalerted. The entry is posted; the stock sub-ledger
went elsewhere; nothing will ever reconcile them for you.

---

<a name="b-02"></a>
## 2.1 · B-02 · 删除已过账账单 → 总账与库存永久分裂
### Deleting a posted vendor bill splits the GL from the stock report


| | |
|---|---|
| **等级** | 🔴 **高危** |
| **状态** | ✅ 实机验证 |
| **前提** | v19 · Perpetual (at invoicing) |

### 场景 / Scenario
一张已过账的供应商账单被 Reset to Draft 后删除。

### 实测结果 / Observed
```
账单过账     GL: Dr 131100 / Cr AP        库存估值报表: +价值    ✅ 两侧一致
删除该账单   GL: 分录消失，131100 掉了      库存估值报表: 不变      ❌ 出现缺口
```

**库存估值不回落。总账掉了，库存侧没掉。系统不发出任何警告。**

The stock valuation does **not** roll back. The GL loses the entry, the stock side keeps it.
No warning is raised anywhere.

### 后果 / Consequence
若删除后**没有重新开票**，这个缺口就是**永久的**，且会被后续的正常业务掩盖。
这是 GL/库存差异的一号成因。

If the bill is never re-issued, the gap is permanent and gets buried by subsequent activity.
This is the #1 cause of GL-vs-stock divergence.

### 对策 / Mitigation
> **SOP：已过账的供应商账单一律用贷记单（Credit Note）冲销。**
> **禁止 Reset to Draft 后删除。**
>
> **SOP: reverse posted vendor bills with a Credit Note. Never reset-to-draft and delete.**

审计动作：查 `account.move` 序列是否断号；查 chatter 里的删除记录。

---

<a name="b-04"></a>
## 2.2 · B-04 · 收 10 开 20 → 总账进 20，库存进 10
### Over-billing: the GL takes the full amount, stock takes only what was received


| | |
|---|---|
| **等级** | 🔴 **高危** |
| **状态** | ✅ 实机验证（干净测试库） |
| **前提** | v19 · Perpetual (at invoicing) |

### 场景 / Scenario
PO 订 20 台 @ 100，**实收 10 台**，供应商账单开 **20 台** @ 100。

### 实测结果 / Observed
```
BILL/2026/07/0001
    Dr 131100 Inventory      2,000.00   ← 全额！20 × 100
       Cr 201002 Payables               2,000.00
```

| | 金额 |
|---|---|
| **总账 131100** | **2,000**（按账单数量 20） |
| **库存估值报表** | **1,000**（按已收数量 10） |
| **Stock Variation 差额** | **1,000** |

**总账吃下全部 20 台的钱，库存侧只认已收的 10 台。**

The GL absorbs the full billed amount. The stock side only recognises what was physically received.

### 机制 / Mechanism
账单行的科目由**产品类别的 Stock Valuation Account** 决定，Odoo 按**账单行数量**记账。
而库存估值跟随 `stock.move`，只认**已收数量**。两条轨道独立计算。

The bill line posts to the category's stock valuation account at the **billed** quantity.
The stock valuation follows `stock.move` at the **received** quantity. Two independent tracks.

### 后果 / Consequence
- **不会**被第二次收货自动冲销
- 差额沉淀在 Stock Variation，靠期末结转补
- 若结转机制失效（见 B-08），差额永久失真且无告警

### ⚠️ v19 比 v18 更危险 / v19 removed the safety net

| | v18 及以前 | **v19** |
|---|---|---|
| 多开的 1,000 落在哪 | **卡在 GRNI / 收货暂估科目**，变成一笔借方挂账 | **直接冲进 `131100 Inventory`** |
| 可见性 | 挂账科目余额异常，**看得见、查得到、有人会去清** | **静默虚增存货资产**，只在 Stock Variation 净额里留一个影子 |

v18 有一个专门的中间科目当缓冲垫。**v19 取消了暂估科目（[B-13](#b-13)），这层安全网没了。**

v18 parked the mismatch in a dedicated interim account — ugly, but visible and reviewable.
**v19 removed interim accounts entirely. The excess now inflates the inventory asset silently.**

### 对策 / Mitigation
- Bill Control 设为 **Received quantities**（v19 实物商品默认）
- 3-way matching 只对 `received` 策略生效
- 月结前核对 GRNI 清零
- **数量校验必须前移到开票动作本身** —— v19 事后无科目可查

---

<a name="b-14"></a>
## 2.3 · B-14 · 账单晚于发货 + 价格变动 → 差额进 Stock Variation，总数不错、分类错
### Bill after delivery + a price change → the difference lands in Stock Variation, not COGS

> ⚠️ **2026-07-14 重大修订。** 原版结论「差额永久卡在存货科目、是死账」**已作废** ——
> 期末关账会扫掉它（[B-29](#b-29)）。**真正的伤害是【分类】，不是【总额】。**


| | |
|---|---|
| **等级** | 🔴🔴 **最高危**（静默、永久、双向、且是许多贸易企业的常态路径） |
| **状态** | ✅ 实机验证（干净测试库，两种顺序对照跑通） |
| **前提** | v19 · Perpetual (at invoicing) · **AVCO / FIFO**（Standard 不受影响，见 [B-16](#b-16)） |

### 场景 / Scenario

同一批货、同样的涨价，**只有"卖"和"收到账单"的先后顺序不同**。

**情形 A —— 先卖，后收到更高的账单（问题顺序）**

| 步骤 | 库存子账 (`stock.move`) | GL 分录 |
|---|---|---|
| ① 收货 10 @ 100 | 1,000 | 无 |
| ② 发货 10 | 0 | 无（COGS 也拖到开票） |
| ③ 开客户发票 | 0 | `Dr COGS 1,000` / `Cr 存货 1,000` / `Cr 销售 3,000` |
| ④ 供应商账单 @200 | 0 | `Dr 存货 2,000` / `Cr 应付 2,000` |

```
终局：存货 GL = −1,000 + 2,000 = +1,000 借方
      实物库存 = 0
      COGS 锁死在 1,000（旧成本）
```

**情形 B —— 先收到账单，后卖（正常顺序）**

| 步骤 | 库存子账 | GL 分录 |
|---|---|---|
| ① 收货 10 @ 100 | 1,000 | 无 |
| ② 供应商账单 @200（**货在库**） | **2,000** | `Dr 存货 2,000` / `Cr 应付 2,000` → **库存重估到 200/件** |
| ③ 卖 + 开客户发票 | 0 | `Dr COGS 2,000` / `Cr 存货 2,000` / `Cr 销售 3,000` |

```
终局：存货 GL = 0  ✅ 与实物一致
      COGS = 2,000（真实成本）✅
```

### 对照 / Side by side

| | COGS | 存货 GL 残留 | 毛利 | 结果 |
|---|---|---|---|---|
| **A · 先卖后账单** | **1,000（偏低）** | **+1,000 幽灵借方** | **虚高 1,000** | ❌ 错配 |
| **B · 先账单后卖** | 2,000（正确） | **0** | 正确 | ✅ 干净 |

### 机制 / Mechanism 📖

开票时 `_set_value` 想按账单价重估那批入库 move，
**但已被发货消耗掉的那部分，在 v19 的数据模型里已经不存在了 —— 没有货可以重估。**

而 AVCO/FIFO 下差额**也没有被路由到 COGS 或价差科目**：
`purchase_stock/models/account_invoice.py:44`

```python
if not line._eligible_for_stock_account() or line.product_id.cost_method != 'standard':
    continue        # ← 只有 Standard 才做价差修正。AVCO / FIFO 直接跳过
```

**→ 差额三条路全堵：无层可重估、无价差科目、无暂估科目（[B-13](#b-13)）。**

### 🔴 部分发货：更阴的版本 / The partial-shipment variant

**收 100 @ 10 → 发 50 → 供应商账单 100 @ 12 过账 → 那 50 台开客户发票**

| 步骤 | 库存子账 | GL 存货 110100 | GL COGS |
|---|---|---|---|
| ① 收货 100 @ 10 | 100 台 / 1,000 | 0 | 0 |
| ② 发货 50（`move.value` 钉死 = 500） | 50 台 / 500 | 0 | 0 |
| ③ 供应商账单 100 @ 12 过账 | 50 台 / **600**（单价 12）| **Dr 1,200** | 0 |
| ④ 那 50 台开客户发票 | 50 台 / 600 | Cr 500 → **余额 700** | **Dr 500** |

```
账单总价差 200 = 100 台 × 2，被劈成两半：
    还在库的 50 台 → +100  ✅ 正常重估进存货（单价 10 → 12）
    已发出的 50 台 → +100  🔴 无处可去

终局：实物 50 台 · 子账 600 · GL 700 · 差 100 · COGS = 500（@10，不是 @12）
```

> **⚠️ 这个版本比全发完更阴：在库 50 台、单价 12、库存估值报表完美正确，谁看都没毛病。**
> **唯一的症状是 GL(700) ≠ 子账(600)。**

### ⚠️ 2026-07-14 · 「永久滞留 / 死账」的说法已作废

**原版说这 100 是「永久滞留、无处可去、不进损益」。这个措辞错了。**

它**不是死账，它是等关账**（[B-29](#b-29)）：

```
Accounting → Review → Inventory Valuation → Generate Entry
    Dr 610000 Stock Variation   100
       Cr 110100 Stock Valuation        100      ← 把滞留的 110100 抹回 0
```

### 🔴 那真正的伤害是什么？—— **总数不错，分类错**

| | 应该 | 实际 |
|---|---|---|
| 那 100 落在 | **COGS**（它就是已售商品的成本） | **Stock Variation** |
| GL 总额 | 正确 | ✅ 正确（关账后） |
| **毛利率** | 正确 | ⚠️ **取决于 Stock Variation 的 `account_type`**（[B-08](#b-08)） |
| **按 lot / 按台的成本** | 正确 | 🔴 **永远偏低 2 AED/台 —— 无法修复** |

> **聚合毛利可以救**（把 Stock Variation 设成 `expense_direct_cost`，落在 COGS 段内）。
> **按 SKU / 按 lot / 按台的成本分解救不了** —— 那笔钱进了一个不带产品维度的桶。
>
> **对 `suite_po_profit` 这类按台算利润的模块：每台会虚赚 (账单价 − 收货价)。**

### 触发条件 / Trigger（两个，同时满足）

```
① 供应商账单晚于发货到达
② 账单价 ≠ 收货时的 PO 价
```

**⚠️ 对「验机后议价 / 供应商月结开票」的行业，这不是边缘场景，是主流程。**

### 🔴 双向，且会互相抵消

| 事后 | 110100 残留 | 后果 |
|---|---|---|
| 账单**涨价** | **借方** | 存货资产虚增，COGS 少计，毛利虚高 |
| 账单**降价 / 压价** | **贷方** | 存货资产虚减，COGS 多计，毛利虚低 |

**两个方向在净额里互相抵消** → [B-12](#b-12) 的「小数字掩盖大问题」在这里达到极致。

### 对策 / Mitigation

> **一线 SOP：供应商账单必须在这批货发出之前过账。**
>
> **做不到 → 月结按 [B-31](#b-31) 的顺序处理：先清结构性错误，再按 Generate Entry。**

**⚠️ 别用 Adjust Valuation 修它。** 那只会改子账 —— 而子账（600）本来就是对的，
错的是 GL（700）。改子账等于**把对的那一边也弄错**。→ [B-28](#b-28)

**量化公式（可 SQL 化）：**

```
残留 = Σ（对每张 PO 的每个产品行）
         开票前已被发货消耗掉的数量  ×  （账单单价 − 收货时 PO 单价）
```

### 修正记录 / Correction Log

| 日期 | 曾经的结论 | 为什么错 |
|---|---|---|
| **2026-07-14** | 「差额永久卡在存货科目 / 死账 / 不进损益」 | **期末关账会扫掉它**（[B-29](#b-29)）。真正的伤害是**分类**（进 Stock Variation 而非 COGS），不是总额 |

---


<a name="b-27"></a>
## 2.4 · B-27 · 🔴 客户发票**晚于**供应商账单 → COGS 仍锁死在旧成本
### Customer invoice *after* the bill — COGS is still frozen at the old cost

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ **实机验证（四变体：AVCO / FIFO × 涨价 / 降价，全程回滚）** + 📖 源码确证 |

### 为什么单开一条 / Why this is separate from B-14

[B-14](#b-14) 的原始实测是「**客户发票先，供应商账单后**」—— COGS 早已过账冻结，
所以差额滞留是**平凡**的。

**本条测的是反过来的顺序**：供应商账单**先**过账（成本已经变成 12 了），
**然后**才给那 50 台开客户发票。**这时 COGS 会用新成本 12 吗？**

### 判别性测试 / The discriminating test

**在库单价在两种假设下都是 12 —— 没有区分度。必须看 COGS 那个数。**

| 假设 | COGS | 110100 滞留 |
|---|---|---|
| 出库 move 被账单回头改写 | 600 (@12) | **0** |
| 出库 move 冻结不动 | **500 (@10)** | **100** |

### 实测结果 / Observed —— 四变体

| 变体 | bill 单价 | 第 1 批 50 的 COGS | 全部卖完后总 COGS | 供应商实收 | **110100 滞留** |
|---|---|---|---|---|---|
| **AVCO 涨价** | 12 | **500 (@10)** | 1,100 | 1,200 | **+100** |
| **AVCO 降价** | 8 | **500 (@10)** | 900 | 800 | **−100** |
| **FIFO 涨价** | 12 | **500 (@10)** | 1,100 | 1,200 | **+100** |
| **FIFO 降价** | 8 | **500 (@10)** | 900 | 800 | **−100** |

> **COGS = 500 (@10)。出库 move 的 `value` 在 `_action_done` 那一刻钉死，
> 供应商账单不会回头改写它。**
>
> **顺序无关。** 无论客户发票在账单之前还是之后，已发出的那部分**永远拿不到新成本**。

### 三个附带结论 / Three by-products

**① AVCO 与 FIFO 表现完全一致。** 单批到货只有一层，FIFO 退化成同一层价。
→ [B-14](#b-14) 无需按成本法分条。

**② 在库的那部分被正确重估。** `std/avg → 12（或 8）`，`remaining_value → 600（或 400）`，
**下一批发货的 COGS 用的是新价。** 在库部分没问题。

**③ 🔴 `quant.value` 的「三方打架」是假象。**
一轮测试中曾观察到「报表 500 / AVCO 600 / GL 700」三个数打架 ——
**那个 500 是脚本单事务里的过期计算缓存**（发货后读过一次 `quant.value`，之后只
`invalidate` 了 product、没 `invalidate` quant）。**刷新后 `quant.value = 600`，与 AVCO 一致。**

> **真正的差异只有一个：GL(700) ≠ 实际库存价值(600)。**
> 写诊断脚本时，跨事务读估值字段**必须 `invalidate_all()`**，否则会造出不存在的 bug。

### 源码 / Source 📖

`purchase_stock/models/account_invoice.py:44` —— 生成价差修正分录的方法开头就写死：

```python
if not line._eligible_for_stock_account() or line.product_id.cost_method != 'standard':
    continue
```

**这一行同时解释了 [B-14](#b-14)、[B-16](#b-16) 和本条 —— 三者是一枚硬币的三个面。**

- **Standard**：bill 过账生成 `Dr/Cr 价差科目` 的 COGS 修正行，已售部分的差价进价差科目 → **干净**
- **AVCO / FIFO**：直接 `continue`，不生成任何价差；差价只靠「重估在库库存」来消化 →
  **已发出的部分没有库存可重估 → 卡在 110100 → 等期末关账扫**（[B-29](#b-29)）

### 📌 2026-07-19 补 · 「出库 value 铉死」从归纳升为源码事实 📖

`stock_account/models/account_move.py:42` —— 账单过账后重估的【唯一】触发点，带着一个显式过滤器：

```python
# AccountMove._post()
self.line_ids._get_stock_moves().filtered(lambda m: m.is_in or m.is_dropship)._set_value()
```

> **`filtered(is_in or is_dropship)` —— OUT move 在源码层面就被排除在重估之外。**
> 本条的四变体实测不再是孤证：**不是“恰好没重估”，是“写死了不重估”。**
>
> 同一方法 `:33` 还有一条早退：`if self.env.context.get('move_reverse_cancel'): return super()._post(soft)`
> → **用“红冲并作废”方式冲销账单，`_set_value` 同样不跑**（见 [B-58](#b-58)）。

---

<a name="b-58"></a>
## 2.5 · B-58 · 🔴 重估过的供应商账单转草稿/取消 → 成本层粘住、GL 回滚
### Resetting or cancelling a re-posted vendor bill: the cost layer sticks, the GL rolls back

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 实机验证（官方估值基类 110100/610000/600000，real_time + AVCO）+ 📖 源码确证 |

### 为什么单开一条 / Why this is separate from B-02

[B-02](#b-02) 测的是【删除】一张已过账账单 —— GL 掍了、库存不回落，缺口静默。

**本条撒销的是一张【已经重估过】的账单**（改价 → 重过账 → 在库部分已被抬到新成本）。
两个不同点：**成本层停在被抬高的中间态（不是回到起点）**；且客户发票的 COGS 行仍在，
**于是存货科目出现【贷方余额】—— 一个极醒目、可直接扫出来的信号。**

### 实测结果 / Observed

采购 100 @10，卖 50 并开客户发票；基准步① 三张凭证完美对平（对平是后面差额有意义的前提）：

```
供应商账单：   Dr 110100 存货 1000
客户发票：     Dr 600000 COGS 500  /  Cr 110100 存货 500
→ 110100 = 1000 − 500 = 500 = 在库价值 ✓   COGS = 500 ✓
```

| 步骤 | std | 已售 COGS(600000) | Odoo 在库价值 | 存货 GL(110100) | 差额 |
|---|---|---|---|---|---|
| **① 采购100@10 + 卖50开票** | 10 | 500 | 500 | **500** | **0** ✓ |
| **② 改采购账单 10→12 重过账** | 12 | 500（不变） | 600 | **700** | **+100** ← [B-27](#b-27) |
| **③ 取消采购账单** | **12（不回滚）** | 500 | **600** | **−500** | **−1100** 🔴 |

> ③ 那个 **−500 = 客户发票那条 `Cr 110100 500` 孤悬在外**。
> 存货类科目出现贷方余额在会计上是荒谬的 —— **这就是本条的诊断信号。**

### 机制 / Mechanism 📖

`stock_account/models/account_move.py`：

| 行 | 代码 | 含义 |
|---|---|---|
| **:42** | `..._get_stock_moves().filtered(lambda m: m.is_in or m.is_dropship)._set_value()` | 重估的**唯一**触发点，在 `_post()` 内 |
| **:46-52** | `button_draft()` → `filtered(display_type == 'cogs').unlink()` | **只删 COGS 行**，不重算 |
| **:54-62** | `button_cancel()` → 同上 | **只删 COGS 行**，不重算 |
| **:33** | `if context.get('move_reverse_cancel'): return super()._post(soft)` | 红冲并作废 **也不跑** `_set_value` |

> **重估只有【正向】触发点，没有【反向】触发点。**
> 过账会重算成本层；转草稿 / 取消 / 红冲作废全都不会。
> 这与 [B-02](#b-02) 、[B-03](#b-03) 是同一个开关的三个面：
> **L1 只在【有单据过账或手工重估】时重算，撤销动作从不反向重算。**

### 🔴 后果 / Consequence

1. **成本层背着一个没有任何有效单据支持的虚高成本**（std=12），而那张账单已不在了。
2. 存货 GL 贷方余额：报表一眼能看出来，但没人会去看库存科目的方向。
3. **后续发货的 COGS 按 12 结转，且按 [B-27](#b-27) 铉死不可逆。**

### 对策 / Mitigation

> ## 🔴 **撤销动作本身不是错误，【停留在撤销状态】才是。**
>
> **这与 [B-03](#b-03) 是同一句话：缺口可自愈，但没有任何机制提醒你去做。**

- ✅ **撤销 → 改正 → 重新过账 = 正常修正路径。** `_post` 会再跑一次 `_set_value`，
  成本层按新账单**重算并覆盖**旧值（不叠加），GL 按新价重建分录 —— 两本账重新对齐。
  这正是本条实测表步骤②所走的路（`std` 10→12），也是 [B-03](#b-03) 的自愈机制。
- 🔴 **危险的是停在 draft / cancel 状态**，或**红冲后不补新账单**：
  GL 已撤销，成本层粘在旧值，无任何告警。
- ⚠️ 红冲并作废（`move_reverse_cancel` 早退）保住了 GL 的可审计性，
  但**同样不重算成本层** —— 除非随后有一张正确账单过账，否则需一次**手工库存重估**
  （Inventory → Valuation → Revaluation）。
  这是对 [B-02](#b-02) 对策「一律用贷记单冲销」的**必要补丁**。
- **诊断探针（便宜、可周扫）：① 存货类科目出现贷方余额；② 长期停留在 draft / cancel
  的采购账单。两者都指向同一个状态。**

---

<a name="b-59"></a>
## 2.6 · B-59 · 🔴🔴 开票早于物理发货 → COGS 与出库价值取两套成本，永久发散
### Invoicing ahead of the delivery: COGS and the outgoing move are priced by two different rules

| | |
|---|---|
| **等级** | 🔴🔴（**无人犯错**、静默、不自愈；同时污染存货资产与毛利） |
| **状态** | ✅ 实机验证（AVCO / FIFO 两臂 + 一轮判别测试）+ 📖 源码确证 |
| **前提** | 销项开票原则 = **订单数量（Ordered quantities）** —— 它允许先开票、后发货 |

### 🔴 为什么这条最值得记

前面几条都需要有人做了一个可指认的动作。**这一条不需要。**
收货、开票、发货，三步全部按标准做，发散照样产生，而且**事后不可修复**。

### 核心公式

按 [B-13](#b-13)：**物理发货本身不产生任何 GL 分录**，
`Dr COGS / Cr 存货` 这一整笔在**开票时点**就走完了；物理出库只动成本层（L1）。

```
发散 = 物理出库价值(L1) − 开票时结转的 COGS(L2)
```

两个时点各取各的成本 —— 中间只要成本变过，差多少就永久卡多少。

### 取值：两套逻辑 📖

**① 开票时的 COGS** —— `stock_account/models/account_move_line.py:67-73`

```python
if moves := self._get_stock_moves().filtered(lambda m: m.state == 'done'):
    price_unit = moves._get_cogs_price_unit(cogs_qty)   # 已发货 → 用实际出库成本
else:                                                   # 未发货 → 落到这里
    if self.product_id.cost_method in ['standard', 'average']:
        price_unit = self.product_id.standard_price      # AVCO/标准：开票当刻均价
    else:
        price_unit = self.product_id._run_fifo(cogs_qty) / cogs_qty   # FIFO：队头层价格
```

**② 物理出库时的 move value** —— `stock_account/models/stock_move.py:343`

| 成本法 | 出库价值取自 |
|---|---|
| **AVCO** | `product.standard_price × qty` —— **出库当刻**的移动均价（会被开票之后的收货重估） |
| **FIFO** | 消耗历史层 —— **队头层**的价格 |

### 实测 · AVCO 臂

场景：收 100@10 → **开票 50（不发货）** → 收 100@14 → 发货 50

| 步骤 | std | 存货 GL | 观测 |
|---|---|---|---|
| 收 100@10 | 10 | 1000 | |
| **开票 50** | 10 | 500 | **Cr 存货 = 500**（开票时 std=10） |
| 收 100@14 | **12** | 1900 | 均价被重估 |
| 发货 50 | 12 | 1900 | 物理 OUT value = **600**（std 12 × 50） |
| **对账** | | **1900** | 在库 **1800**，**GL 多 100** 🔴 |

**发散 = 600 − 500 = +100，永久卡在存货科目。**

### 实测 · FIFO 臂

同一场景：

| 步骤 | 存货 GL | 队头层 `remaining_qty` | 观测 |
|---|---|---|---|
| 收 100@10 | 1000 | 层#311 = 100 | |
| **开票 50** | 500 | **仍 100** | Cr 存货 = 500，**FIFO 层未被消耗** |
| 收 100@14 | 1900 | +层#313 = 100 | 新层接在**队尾** |
| 发货 50 | 1900 | 层#311 → 50 | 物理 OUT value = **500**（层 @10） |
| **对账** | **1900** | Σremaining = 1900 | **GL = 在库，发散 0** ✅ |

**发散 = 500 − 500 = 0。**

### 🔬 判别测试：开票时的 FIFO 到底走哪一支

上一场景中开票时 `std = 10`、最早层也 `= @10`，两支给出同一个 500，**不具判别性**。
故补一轮把两支分开：

场景：收 100@10 → 收 100@14（此时 `std = 12`，队头仍 @10）→ **开票 50**

| 假设 | 预测 Cr 存货 |
|---|---|
| **A** 走 `standard_price` | 600（12 × 50） |
| **B** 走 `_run_fifo()` 队头 | **500**（10 × 50） |

**实测 = 500 → 假设 B 成立。`account_move_line.py:70-73` 的 `else` 支在 v19 确实生效。**

同时确认第二个观测：**`_run_fifo` 在开票取值时是「只看不吃」** —— 队头层 `remaining_qty` 开票后仍是 100。
源码印证 `stock_account/models/product.py:553` 的 docstring：

```python
def _run_fifo(self, quantity, lot=None, at_date=None, location=None):
    """ Returns the value for the next outgoing product base on the qty give as argument."""
```

> **它是纯读函数**：从 `qty_available` 建队列、走一遍、返回金额，全程不写库、不动 `remaining_qty`。
> 名字里的 `run` 有误导性，**真正的层消耗发生在 `_action_done`**。
> 所以 COGS 只是给队头当时的成本**拍了一张快照**，不预留、不排队。

### ⚠️ 修正记录 / Correction Log

| | |
|---|---|
| **原预测** | FIFO 在这个场景下会比 AVCO **更脏**（因为 `_run_fifo` 会在开票时直接消耗 FIFO 层） |
| **本次修订** | 🔴 **方向完全反了，已撤回。** 实测 FIFO 发散 **0**、AVCO 发散 **+100** —— **脏的是 AVCO** |
| **依据** | `_run_fifo` 为纯读（`product.py:553`）；FIFO 出库价值钉死在历史层，对后续收货免疫；而 AVCO 出库价值随移动均价浮动，**会被开票之后的收货重估** |

### 🔑 机制统一表述

> ## **发散触发条件 = 开票之后、物理发货之前，发生了任何改变【本单实际出库成本】的事件。**

| | 出库成本取自 | 会改变它的事件（窗口内） |
|---|---|---|
| **AVCO** | **当刻移动均价** | 收货、**到岸成本**（[B-17](#b-17)）、**账单晚到重估**（[B-27](#b-27)）、手工库存重估、带成本的盘盈 |
| **FIFO** | **队头层的价格** | 队头被别单先消耗（队序被改）、**队头那批被贴到岸成本**、**队头那批的账单晚到重估** |

### ⚠️ FIFO 的「干净」是巧合，不是保证

上面 FIFO 臂发散为 0，是因为**发货时消耗的正是开票时拍快照的那个 @10 层**。

**它不是机制保证：**

- 若开票 → 发货之间，队头那 50 个 @10 被**别的订单先吃掉**，本单发货落到 @14 层（=700），
  而 COGS 已锁死 500 → **错 200**；
- 若队头那批货被贴了 landed cost 或其账单晚到重估，**队头层价格本身就变了**（[B-17](#b-17) [B-27](#b-27)）。

> **FIFO 对「后续收货」天然免疫，但对「针对队头的成本修正」和「队序变化」不免疫。
> 没有一种成本法是安全的 —— 安全的只有窗口足够短。**

### 🔴 后果 / Consequence

- **存货虚高、COGS 少结、利润虚高**（AVCO 场景）—— 三者同时发生
- **不自愈**：物理发货在本配置下不再补过 GL（COGS 已在开票走完），残值永久卡在存货科目
- 老板感觉"毛利看着还行"、财务感觉"库存对不平"，**是同一件事的两个面**

### 对策 / Mitigation

- 🔴 **SOP（与成本法无关）：开票原则为「订单数量」的产品，
  开票与物理发货之间不得发生任何改变该产品成本的事件。**
  AVCO 触发面宽（任何收货即触发）；FIFO 触发面窄但非零。
- **根治路径**：高流转实物商品的开票原则改为**已交付数量（Delivered quantities）**，
  使 `_get_stock_moves()` 恒有已完成出库 move，走 `if` 支而非 `else` 支，两套逻辑合一。
- **若业务必须先开票**（预收、订单即开票）：缩短窗口，并把这批产品单独圈出来监控。

### 🔬 检测手段 / Detection —— 可逐单据分解

```
对每条销售订单行：
  COGS_posted = 该行产生的 display_type = 'cogs' 分录金额合计
  OUT_value   = 该行关联的已完成出库 move 的 value 合计
  发散        = OUT_value − COGS_posted        # 应为 0
```

> **这个探针不依赖客户科目表**，差额直接归到具体订单行，
> 与 F-13 / F-18 的分解口径一致，可直接进诊断脚本。
> 圈定范围：**开票原则 = 订单数量** 且 **成本法 = AVCO** 的产品是高发区。

---


# 第三章 · 成本法与按 Lot 估值：成本到底从哪里来
## Chapter 3 · Cost method and lot valuation — where the cost actually comes from

> 本章回答两个问题：**`cost_method` 到底还管什么？** 打开 **Valuation by Lot** 之后世界变成什么样？

简短版：打开 lot 估值后，`cost_method` 从「产品维度的成本流假设」退化为「同一颗 lot 多次入库时怎么合并」的边缘规则。
**GL 从此按实际发出的那颗 lot 的真实成本结算。**

Short version: enabling lot valuation demotes `cost_method` from a product-wide cost-flow
assumption to a within-lot merge rule. The GL now costs the lot that physically shipped.

---

<a name="b-16"></a>
## 3.1 · B-16 · 价差科目是 Standard 专属；同一条 move 上住着两个成本
### The price difference account is Standard-only; two costs live on one stock move


| | |
|---|---|
| **等级** | 🟡（🔴 对自建模块） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### 背景 / Why this was tested

前一版文档（基于 v18 心智模型）声称：AVCO/FIFO 下账单价 ≠ 收货估值时，
差额"回冲库存估值 / 进价差科目"。**这整段是 v18 残留，已作废。**

### 实测 / Test

```
产品 B：Goods + Track by Serials + Valuation by Lot
类别：Costing Method = Standard，Cost = 100，Price Difference Account = 999999
PO：10 台 @ 120，收货 → lot-B1，然后过账账单 10 @ 120
```

### 实测结果 / Observed

**① 未开票时（收货后）：**

| 字段 | 值 |
|---|---|
| `lot.standard_price` | **100**（标准成本） |
| `remaining_value` | **1,000**（标准成本） |
| **`move.value`** | **1,200**（**PO 金额**） |
| GL | **零分录** |

**200 的差异在收货那一刻就已经埋在 move 里等着，开票时释放。**

**② 账单过账后的真实 Journal Items：**

```
科目                          借        贷      display_type
110100 Stock Valuation      1,200.00           product      ← 账单行先按账单金额全额进存货
999999 Price Difference       200.00           cogs         ← 差异修正
110100 Stock Valuation                200.00   cogs         ← 同时把 200 从存货冲回
211000 Account Payable              1,200.00   payment_term ← 应付 = 实际账单

净额：存货 +1,000（钉死在标准成本）· 价差 +200 借方（进 P&L）· 应付 −1,200
```

**③ 开票后成本变了吗？** **没有。** `lot.standard_price` 和产品 `standard_price` 仍是 100。
**账单价 120 没有覆盖标准成本 —— 差异全部被价差科目吸收。**

### 机制 / Mechanism 📖

`purchase_stock/account_invoice.py` 的价差逻辑起手就是：

```python
if cost_method != 'standard':
    continue
```

→ **AVCO/FIFO 根本不进这段代码。**

### 核心结论 / Key Takeaway

> **v19 里有两套完全不同的估值架构：**
>
> | | **AVCO / FIFO** | **Standard** |
> |---|---|---|
> | 估值源 | **账单价就是成本** | **标准成本钉死** |
> | 涨价去向 | 全额重估进存货 | 只有标准成本进存货，差异进价差科目 |
> | 价差科目 | ❌ **不用**（"差异"概念不存在） | ✅ **必用**（唯一兜底） |
> | lot / 产品成本 | 被账单价更新 | **永远 = 标准成本** |
>
> **"Standard 在 v19 名存实亡"不成立 —— 恰恰相反，它是唯一会真正用到
> `property_price_difference_account` 的成本法。**

### 🔴 对自建模块的直接影响

**Standard 下，`stock.move.value` 存的是 PO 金额，不是标准成本。**
任何直接读 `move.value` 当成本的代码，在 Standard 下会读到错的数。
**要成本 → 读 `lot.standard_price` 或 `remaining_value`。**

---

<a name="b-05"></a>
## 3.2 · B-05 · Lot 估值**确实**进会计链路 ⚠️ 结论已修正
### Lot valuation DOES drive the accounting chain — earlier conclusion reversed


| | |
|---|---|
| **等级** | 🟡（机制本身正确；危险的是 B-06 的报表） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |
| **前提** | v19 · `lot_valuated = True` · Track Inventory By Lots/Serials |

### 测试 / Test
```
产品：AVCO + Track by Lots + Valuation by Lot
收货 lot1-po100 : 10 台 @ 100  → 1,000
收货 lot2-po200 : 10 台 @ 200  → 2,000
产品级 AVCO = 150

只发货 + 开票 lot1 的 10 台。
```

### 实测结果 / Observed
```
INV/2026/00001
    Cr 500001 Sales                3,000.00
    Cr 131100 Inventory            1,000.00   ← lot1 的真实成本
    Dr 400001 COGS                 1,000.00   ← 不是 10 × 150 = 1,500
    Dr 102011 Accounts Receivable  3,000.00
```

**COGS = 1,000 = lot1 的真实成本。不是产品级平均价 1,500。**

COGS equals the **actual cost of the lot shipped**, not the product-level average.

### 机制 / Mechanism 📖

`stock_move.py::_set_value` — 出库估值：

```python
if move.product_id.lot_valuated:
    value = 0.0
    for move_line in move.move_line_ids:
        if move_line.lot_id:
            value += move_line.lot_id.standard_price * move_line.quantity_product_uom
    move.value = value
    continue          # ← 直接 continue，根本不进下面 fifo / average 的分支

if move.product_id.cost_method == 'fifo':
    ...
else:  # average / standard
    move.value = move.product_id.standard_price * ...
```

那 lot 自己的成本从哪来？`stock_lot.py::_update_standard_price` —— **cost_method 依然生效，但作用域缩小到单个 lot 内部**：

| `cost_method` | lot 的 `standard_price` 怎么算 |
|---|---|
| `standard` | 用产品的 `standard_price`（**所有 lot 同一个成本**） |
| `average` (AVCO) | 对**这个 lot 自己的入库**求加权平均 |
| `fifo` | **同上 —— 结果与 AVCO 完全一致** |

> ⚠️ **本表的 `fifo` 行于 2026-07-12 修正。** 原写作"`_run_fifo_batch(lot=lot)` — 只在这个
> lot 内部先进先出"，暗示 lot 内部保留成本层供出库挑选。**实测证伪**：同一 lot 二次收货
> 5 @ 100 + 5 @ 200 后 `standard_price = 150`，出库 5 件 `move.value = 750`，
> **不是 FIFO 最老层的 500**。**一颗 lot 只有一个标量成本，lot 内部没有层。**
> 完整证据见 [B-20](#b-20)。

### 核心结论 / Key Takeaway

> **开启按 lot 估值 = 成本核算从「产品维度的假设成本流」退回到「每批货的真实成本」。**
> **cost_method 从此只决定"同一个 lot 多次入库时怎么合并"这个边缘情况。**
>
> **Enabling lot valuation demotes the cost method from a product-wide cost-flow assumption
> to a within-lot merge rule. The GL now uses the real cost of the goods that actually shipped.**

**推论（2026-07-12 强化）**：不只是单次入库的 lot ——
**在 lot 估值下，AVCO 与 FIFO 对任何 lot 都产出完全相同的成本。**
因为一颗 lot 永远只承载**一个标量成本**（`lot.standard_price`），
多次入库时两种模式都把它揉成该 lot 自身的加权平均（[B-20](#b-20) 实测）。

**`cost_method` 在 lot 内部只剩一个残余作用：`standard` 取产品成本。**
FIFO 的"先进先出"只发生在 **lot 与 lot 之间**，从不发生在一颗 lot 内部。

Corollary (strengthened): under lot valuation, AVCO and FIFO produce **identical** costs for
*any* lot, not merely single-receipt ones. A lot carries exactly **one scalar cost**; a second
receipt blends it to that lot's own weighted average under both methods. FIFO layering exists
only *between* lots — never inside one.

### 修正记录 / Correction Log
| 日期 | 曾经的结论 | 为什么错 |
|---|---|---|
| 初次 | "lot 只是标签，会计不按此结算" | 被 B-06 的报表显示误导 |
| 修正 | "lot 估值进会计链路，且是真实成本" | 实机 COGS = 1,000 + 源码 `continue` 分支 |
| **2026-07-12** | 机制表："`fifo` → 在这个 lot 内部先进先出" | **实测证伪。** 同 lot 收 5 @ 100 + 5 @ 200 → `std = 150`；出库 5 件 → `move.value = 750`，而非最老层的 500。**lot 内部无层。** → [B-20](#b-20) |

---

<a name="b-20"></a>
## 3.3 · B-20 · 同一 lot 多次收货 → 成本坍缩为加权平均；GL 与 quant 在部分出库期间分裂
### Re-receiving one lot blends its cost to a weighted average — and splits the GL from the quant report


| | |
|---|---|
| **等级** | 🟡（🔴 **对月结勾稽**：110100 总账余额与库存估值报表会对不上，且无任何提示） |
| **状态** | ✅ 实机验证 |
| **前提** | v19 · `lot_valuated = True` · Costing Method = FIFO |

### 场景 / Scenario

同一个 lot 号 `SAME` 分两次收货：先 **5 @ 100**，再 **5 @ 200**。

### 实测结果 ① · lot 可以被重复收货 / A lot may be received more than once

两次都用同名 lot，Odoo **复用同一条 `stock.lot` 记录**（`id` 不变），数量累加 5 → 10。

**lot 不是唯一性约束** —— 那是序列号（serial）的规矩。**lot 允许反复入库。**

### 实测结果 ② · 成本坍缩为该 lot 自身的加权平均 / The lot's cost collapses to its own weighted average

| 步骤 | lot qty | `avg_cost` | `total_value` | **`standard_price`** |
|---|---|---|---|---|
| 收 5 @ 100 | 5 | 100 | 500 | **100** |
| 再收 5 @ 200（同 lot） | 10 | 150 | 1,500 | **150** ← 两笔并成一个池子 |

> **一颗 lot 只有一个成本。**
> 一旦把两笔不同成本的货收进同一颗 lot，它们被揉成这颗 lot 的加权平均（150）。
> **lot 内部不再保留 100 / 200 两层给出库挑。**

### 实测结果 ③ · 出库按混价，不按 FIFO 最老层 / Issues at the blended cost, not the oldest layer

```
发 5 件  →  move.value = standard_price(150) × 5 = 750
            COGS = 750   ← 不是 FIFO 最老层的 500
```

**这直接推翻了 [B-05](#b-05) 机制表原来的 `fifo` 行。**
**同 lot 多次收货时，这颗 lot 的出库成本退化成 AVCO（按该 lot 均价），而不是 FIFO。**

### 实测结果 ④ · 🔴 三方勾稽：部分出库期间 GL 与库存报表错位

| 步骤 | lot qty | `quant` / 库存报表价值 | GL 110100 | 勾稽 |
|---|---|---|---|---|
| 收 5 @ 100 | 5 | 500 | 500 | ✅ |
| 再收 5 @ 200（同 lot） | 10 | 1,500 | 1,500 | ✅ |
| **发 5 件（COGS = 750）** | 5 | **1,000** | **750** | ❌ **差 250** |
| 再发 5 件（COGS = 750） | 0 | 0 | 0 | ✅ **耗尽后自愈** |

### 机制 / Mechanism

**两个口径用了不同的成本基准：**

| 口径 | 出库时怎么减 |
|---|---|
| **GL / `move.value`** | 按 lot 的**标量**成本 150 → 减 **750**（存货科目 1,500 → 750） |
| **`quant` / 库存估值报表** | 按 lot **内部的 FIFO 层**先消耗最老层（先吃掉 5 @ 100 = 500）→ 报表 1,500 → **1,000**（剩余 5 件按 @200 计，报表 avg 变 200） |

> **FIFO 的层确实存在 —— 但只存在于 `quant` 侧，不存在于 GL 侧。**
> GL 读 `lot.standard_price`（一个标量）；`quant` 按层消耗。
>
> **FIFO layering is real — but it lives in the quant, not in the GL.**
> The GL reads a single scalar (`lot.standard_price`); the quant consumes internal layers.

**同 lot 单价一致时两者恒等**（层的成本 = 标量成本，减多少都一样）。
**单价不一致时**，在部分出库期间分裂，lot 耗尽时归零、重新勾稽。

### 后果 / Consequence

**若月结时这颗混价 lot 还有一部分没发完，`110100` 总账余额与库存估值报表就不会平。**
差额既不是 GRNI、也不是价差、也不是 [B-14](#b-14) —— 是这个。**没有任何机制会提示。**

### 对策 / Mitigation

> **🔴 每笔到货用独立 lot 号（Lot-A、Lot-B …）。**
>
> 这样每颗 lot 一个干净成本，FIFO 在 **lot 之间**正常先进先出，
> **GL 与 quant 报表始终勾稽** —— 正是 [B-05](#b-05) / [B-06](#b-06) 测出来的那套一致行为。

- **序列号追踪天然满足**（每台一个 serial，只入库一次），本条不触发。
- **操作层封堵**：收货作业类型（Operation Type）→ *Lots/Serial Numbers* →
  **`Use Existing ones` 关闭**，则界面上选不到旧 lot；手打重名会撞
  `stock.lot` 的 `(name, product_id, company_id)` 唯一约束。
- ⚠️ **退货链路绕过该设置**（退货向导直接复制 `lot_id`，不走 lot 创建逻辑）。
  该设置不是全路径生效的。

### 修正记录 / Correction Log

| 日期 | 曾经的结论 | 为什么错 |
|---|---|---|
| B-05 初版 | \"`fifo` → `_run_fifo_batch(lot=lot)`，只在这个 lot 内部先进先出\" | 暗示 lot 内保留成本层供出库挑选。**实测证伪**：出库 `move.value = 750`（混价），不是 500（最老层） |

---

<a name="b-21"></a>
## 3.4 · B-21 · 🔴 `lot.avg_cost` 是在库均价，不是成本 —— lot 发空即归零
### `lot.avg_cost` is the on-hand average, not the cost — it drops to zero when the lot empties


| | |
|---|---|
| **等级** | 🔴 **高危**（任何以 `avg_cost` 为成本的读取都会静默取到 0，无告警） |
| **状态** | ✅ **生产库实证** |
| **前提** | v19 · `lot_valuated = True` |

### 事实 / The fact

`stock.lot` 上有两个看起来都像"成本"的字段：

| 字段 | 表单标签 | 语义 | lot 发空后 |
|---|---|---|---|
| **`lot.avg_cost`** | *Average Cost* | **在库价值 ÷ 在库数量** —— 一个**报表字段** | **归零** |
| **`lot.standard_price`** | ***Cost*** | **该 lot 的成本** —— 估值引擎读的就是它（[B-05](#b-05)） | **不变** |

**两个字段名都会误导。**
**`avg_cost` 不是成本；`standard_price` 也不是"产品级标准成本"。恰恰相反。**

（同一个陷阱在 [B-10](#b-10) 已出现过一次：`sale.order.line.purchase_price` 也不是采购价，
而是 Cost。**这套模型里的字段名系统性地不可信，必须回到源码确认语义。**）

### 生产库实证 / Observed on a live production database

一个**已售罄**的序列号：

```
Lot/Serial Number:  P00019-10
INVENTORY
    On Hand Quantity      0.00
    Location              Customers
    Total Value           0.00 AED
    Average Cost          0.00 AED      ← avg_cost
    Cost              2,009.68 AED      ← standard_price
```

**`avg_cost = 0`，`standard_price = 2,009.68`。**

### 机制 / Mechanism

`avg_cost = total_value / qty`。lot 发空 → `qty = 0` → 分子分母同时归零。

> **售罄不是边界情况 —— 它是每一颗 lot 的必然终态。**
> 因此 `avg_cost` 对**任何一颗已完成生命周期的 lot** 都读不到成本。
> 出库过账**之后**读取，同样读不到（库存此时已扣减）。
>
> Selling out is not an edge case — it is the normal end state of every lot. `avg_cost`
> therefore returns nothing useful for any lot that has completed its life, and returns
> nothing useful when read *after* an outgoing move has been validated.

### 🔴 后果 / Consequence

任何把 `avg_cost` 当成本读取的地方 —— 报表、导出、SQL 查询、二次开发 ——
**在 lot 售罄的那一刻起必然读到 0**，且**没有任何报错**。
而售罄是每颗 lot 的正常归宿，所以这不是小概率事件。

> **要成本 → 读 `lot.standard_price`。**
>
> 与 [B-16](#b-16) 的结论并列：`move.value` 在 Standard 下存的是 PO 金额、不可信；
> **`lot.standard_price` 在 Standard / AVCO / FIFO 三种成本法下都是 GL 实际使用的那个数**
> （[B-05](#b-05) 源码：`value += move_line.lot_id.standard_price * quantity`）。

### 判别方法 / How to check in one line

```python
lot = env['stock.lot'].browse(ID)      # 任取一颗已售罄的 lot
lot.avg_cost                            # → 0.0
lot.with_company(lot.company_id).standard_price   # → 该批真实成本
```

**两个数字不同 = 本条成立。** 生产库里随便找一颗卖完的 lot 即可。

### ⚠️ `standard_price` 会被事后改写 / It is rewritten after the fact

`lot.standard_price` **不是不变量**。三个事件会在出库**之后**改写它：

| 事件 | 条目 |
|---|---|
| 同一 lot 二次收货 | [B-20](#b-20) |
| 账单晚于发货且价格变动 | [B-14](#b-14) |
| 落地成本晚于发货 | [B-17](#b-17) |

**而 GL 分录一旦过账就冻结不动。**
因此在这三种情况下，**当前的 `lot.standard_price` ≠ 当初计入 GL 的金额** ——
差额正是 [B-14](#b-14) / [B-17](#b-17) 描述的那笔"滞留在存货科目、永不进损益"的钱。

**读当前值 = 读经济真实；读 GL = 读账面。这三种情况下两者不是同一个数。**

---


# 第四章 · 落地成本（Landed Cost）：分摊到哪一层
## Chapter 4 · Landed Cost — what it can and cannot reach

> LC 的分摊粒度是**整张收发货单**，不是行、不是 lot、不是产品。
**是否开启 Valuation by Lot，决定了 LC 落在一颗 lot 上还是摊到全部在库。**
本章两条一正一反，合起来就是 LC 的全部行为。

LC allocates per *picking*. Whether Valuation by Lot is on decides whether the cost lands on one
batch or smears across all stock on hand.

---

<a name="b-17"></a>
## 4.1 · B-17 · LC 按整张收发货单分摊；已发货部分的追加成本进差异科目
### Landed Cost allocates per picking; top-ups on delivered goods bypass COGS


| | |
|---|---|
| **等级** | 🟡（🔴 对按单台/按批次核算利润的业务） |
| **状态** | ✅ 实机验证 |

### 🔴 2026-07-14 · T-08 修正 —— **分摊粒度是【move 级】，不是【picking 级】**

**而且：原「LC 不落 lot」的存疑观察【已撤销】—— 那是测试脚手架缺陷。**

```
两张真实 PO：5 @ 100 → LOT-A，5 @ 200 → LOT-B（lot 成本来自【实际采购计价】）
LC 前： lotA.sp=100  lotB.sp=200  |  quant A=500  B=1000  |  total_value=1500
LC 运费 100

--- split = by_quantity（按数量）---
    valuation_adjustment_lines = 2        ← 🔑 每 move 一行 = 每 lot 一行
    lotA former=500 +LC=50    lotB former=1000 +LC=50
    → lotA.sp=110  quant.value=550  (unit 110)      ← +10 / 件
    → lotB.sp=210  quant.value=1050 (unit 210)      ← +10 / 件
    → product.total_value = 1600                     ← 1500 + 100 全额吸收

--- split = by_current_cost_price（按价值）---
    lotA +33.33   lotB +66.67                        ← 按原值比例 500 : 1000
    → lotA.sp=106.67   lotB.sp=213.33
    → product.total_value = 1600
```

### 定论 / Verdict

| # | 结论 |
|---|---|
| **1** | **LC 按 `picking.move_ids`（move 级）分摊。**<br>**不同成本的 lot 天然来自不同的 PO 收货（= 不同 move）→ 所以【实际上就是按 lot 分】。** |
| **2** | **真实计价下，LC 完整传导到 `lot.standard_price` + `quant.value` + `product.total_value`。**<br>**GL / 在手 / 报表 三方对平，零差异。Lot 估值与 LC 【完全兼容】。** ✅ |
| **3** | ⚠️ **原「LC 只进 move/GL、不落 lot」的观察 = 测试脚手架缺陷，已撤销。**<br>用 `lot.standard_price = 100/200` **手工种成本**，把 lot 单价**钉死**了，<br>**阻断了 LC 的成本重算传导路径**。换成**真实 PO 收货计价**后，现象消失。 |

> ## 🔴 **方法论：手工 `write` 到一个【本该由系统算出来】的字段上，**
> ## **就会切断那条链路的重算 —— 然后你观察到的是【自己造的假象】。**
>
> **与 B-34 的「料件缺席」是【同一个错】。**
> **测试必须走真实业务路径：真 PO、真收货、真计价。**

---

### 实测结果 / Observed —— 分摊粒度（原文，仍成立）

```
LC 单据  →  Transfers 字段选中一张或多张【收发货单】
              ↓  Split Method（Equal / By Quantity / By Current Cost / By Weight / By Volume）
            在【该单内的多个产品行】之间分摊
```

| 层级 | 可否人工选择 |
|---|---|
| **哪张收发货单** | ✅ 人工选。**粒度到此为止** |
| **单内多产品之间** | ✅ Split Method |
| **选 lot** | ❌ **不能** |
| **选数量** | ❌ **不能** |
| **选产品**（单内挑一个） | ❌ **不能** —— 整单都摊 |

### 🔴 发货单也能被选中 —— 但结果不一样

| 货的状态 | 追加成本去向 | 后果 |
|---|---|---|
| **仍在库** | ✅ `Dr 存货` —— 重估进该 lot | 成本正确 |
| **已发出** | ⚠️ **进差异科目**（P&L）<br>**不进存货，也不进 COGS** | 期间损益总额对了，但**那台机器的 lot 成本里永远缺这笔运费** |

> **总额正确 ≠ 归集正确。**
> 差异科目是一个"对得上账、但说不清是谁的"的桶。
> 对按 IMEI / 按批次 / 按项目算利润的业务，**这就是错的**。
>
> **The period P&L still balances, but the unit's cost is permanently short.
> Correct in total, wrong in attribution.**

### 🔴 2026-07-19 修订 · 「差异科目」措辞作废 —— 落点定论 📖

**原文写「已发出 → 进差异科目(P&L)」—— 这个词会被读成品类上的 `account_stock_variation_id`（[B-08](#b-08) 那条链）。错。**

| 问题 | 定论 |
|---|---|
| **残值落到哪个科目？** | **100% 由 LC 成本行的 `account_id` 决定**，兼底才是运费（服务）产品的费用科目 |
| **品类的差异科目会接吗？** | ❌ **不会，实测为 0。** `account_stock_variation_id` 在 v19 只有两个调用点：**期末关账 closing move** + **估值报表**。`stock_landed_cost.py` 全程不引用它 |
| **LC 产品要不要自己的估值科目？** | ❌ 不能有，也不需要。运费是 `service`，没有估值层 |

```python
# stock_landed_costs/models/stock_landed_cost.py:353
credit_account_id = self.cost_line_id.account_id.id or cost_product._get_product_accounts()['expense'].id
# :377
diff = self.additional_landed_cost * (remaining_qty / self.quantity)
```

### 🔴 而且这是【设计意图】，不是缺陷

`_create_account_move_line` 的 docstring 原文就写着：LC 供应商账单只平费用科目，
**只把「还在库的那部分」贷记出来、转入存货估值科目**。

> **所以本条的措辞改为：【只有在库份额被资本化，其余按设计留在费用科目】。**
> 不是“漏”，是可预期机制。**风险仍在归集口径，不在总额**（下文原结论不变）。

**干净基类重测（官方 110100/610000/600000，全程对平）：**

| | std | 已售50 COGS | 在库价值 | 存货 110100 | 运费清算 600100 | 差异科目 610000 |
|---|---|---|---|---|---|---|
| **A) LC 前** | 10 | 500 | 500 | **500** ✓ | 0 | 0 |
| **B) 补 LC 1000 后** | 20 | 500（不变） | 1000 | **1000** ✓ | **500** | **0** |

```
$1000 运费一分为二（比例 = remaining_qty / quantity = 50/100）
  $500（在库 50） → 资本化进存货 110100，单价 10→20，GL 与在库价值对平 ✓
  $500（已售 50） → 满在 LC 成本行科目（此例 600100）= 当期损益
                        不进存货、不进 COGS（恒 500）、不进任何差异科目
```

### 🔑 配置杆杆 / The only lever

`account_id` 在**每一张 LC 单据的成本行上可改** —— 所以想让“没落到在库数量上的那半运费”
有个干净可识别的归宿，做法是把它指到一个专户（例：**Landed Cost 未分摊**），
而不是混在普通运费里。**去配品类的 `account_stock_variation_id` 一分钱也不会进去。**

### ⚠️ 边界

`remaining_qty = 0`（LC 前已全部出库）是另一回事 —— **GL 零分录，但成本层仍被抬高**。
那是缺陷类，不是本条的设计行为 → **见 [B-57](#b-57)。**

### 对策 / Mitigation

- **硬纪律：LC 必须在货发出之前分摊完毕**（这条给了[机制文档 §2.2](./odoo19_accounting_mechanisms.md#topic-2) 一个精确的机制解释）
- 月结检查项：**是否存在"已发货后才补做"的 LC 单据**
- 补做历史 LC **只对当前仍在库的商品有效**

---

<a name="b-18"></a>
## 4.2 · B-18 · 不开 lot 估值，后到的运费会污染早批次的成本基础
### Without lot valuation, later freight contaminates the cost basis of earlier batches


| | |
|---|---|
| **等级** | 🔴（对多批次、价差大的商品） |
| **状态** | ✅ 实机验证（判别性测试） |
| **前提** | v19 · AVCO |

### 判别性测试 / The discriminating test

**关键在于构造一个"两个假设会给出不同数字"的局面：**

```
产品 A（AVCO + 序列号 + Valuation by Lot），清空库存
① PO-1 收 10 @ 100 → lot-1，【不做 LC】
② PO-2 收 10 @ 100 → lot-2，对 PO-2 的收货单做 LC 运费 200
③ 回头看 lot-1
```

### 实测结果 / Observed

| 步骤 | lot-1 cost | lot-2 cost |
|---|---|---|
| ① PO-1 收 10@100（无 LC） | **100** | — |
| ② PO-2 收 10@100（LC 前） | 100 | 100 |
| ③ 对 PO-2 收货单做 LC 运费 200 | | |
| ④ **回看** | **100（纹丝不动）** ✅ | **120** |

```
LC 估值调整明细（实测打印）：
move = WH/IN/00035 (PO-2 的收货单)
former_cost = 1000.00   additional = 200.00   final = 1200.00
→ by_quantity 分摊：200 / 10 台 = +20/台 → lot-2 成本 100 → 120
```

**LC 严格锁定在被贴单的那一批。lot-1 完全不受影响。**

### 关键对照 / The comparison that matters

| | **开 Valuation by Lot** | **关（产品级 AVCO）** |
|---|---|---|
| **LC 200 的落点** | 只进 lot-2 → lot-2 = **120**，lot-1 = **100** | 摊进产品移动平均：<br>(1,000 + 200 + 1,000) / 20 = **110**<br>**在库全部 20 台（含 lot-1）统统变 110** |
| **lot-1 成本** | **保持 100** ✅ | **被稀释成 110** ❌ |

> **不开 lot 估值，后到某一批货的运费会污染早批次的成本基础（移动平均一锅烩）。**
> **开了 lot 估值，运费严格归属到对应批次，早批次成本免疫。**
>
> **Without lot valuation, freight landing on a later batch silently rewrites the cost basis of
> batches already sitting in stock. With it, each batch keeps its own true landed cost.**

### 后果 / Consequence

对**同一产品、多个采购价、到货时点分散**的业务（二手手机、按项目采购的物料），
不开 lot 估值 = **每一次运费都在系统性地扭曲历史批次的成本**，且不可逆。

### 修正记录 / Correction Log

| 曾经的结论 | 为什么不成立 |
|---|---|
| "LC 落 lot 已由生产库数据确证（算术闭合）" | 那组数据取自**只采购过一次**的产品 —— lot 成本与产品级平均**天然相等**。<br>**该数据在两个假设下会给出相同数字，不含区分度 —— 不能用来区分两个假设。** |

---

<a name="b-57"></a>
## 4.3 · B-57 · 🔴🔴 LC 对 `remaining_qty = 0` 的收货 move 仍触发估值重算 → 零库存幽灵单价
### Landed cost still revalues a fully-consumed in-move — a phantom unit cost with zero stock

| | |
|---|---|
| **等级** | 🔴🔴（静默、无分录、无告警；窗口内出库则不可逆） |
| **状态** | ✅ 实机验证（AVCO / FIFO 两臂 + 负库存出库变体）+ 📖 源码确证 |

### 为什么单开一条 / Why this is separate from B-17

| | [B-17](#b-17) | **本条 B-57** |
|---|---|---|
| **讲什么** | **钱怎么拆**：只资本化在库份额，其余留 LC 成本行科目 | **成本层被抬高**：整笔金额写进一条**已全部消耗**的 in-move |
| **性质** | ✅ **按设计**，可预期，总额正确 | 🔴 **缺陷类**，L1 单侧 |
| **GL 痕迹** | 有（部分资本化分录） | ❌ **零分录** —— 现有的 GL↔库存对账探针**抓不到** |

> **一句话：B-17 讲 GL 侧怎么分；B-57 讲成本层侧【不该动却动了】。**

### 判别性测试 / The discriminating test

场景：收 100 @10 → **全部卖光**（`remaining_qty = 0`）→ 再补 LC 1000。

| 假设 | std | `total_value` | 存货 GL |
|---|---|---|---|
| **A** 成本层不动，整笔干净留费用，无劈叉 | **10** | 0 | 0 |
| **B** 成本层仍被抬高，GL 零分录，静默劈叉 | **20** | 0 | 0 |

**三个数里只有 `std` 有区分度 —— 这就是判别点。**

### 实测结果 / Observed —— AVCO

| 观测点 | LC 前 | LC 后 | 判定 |
|---|---|---|---|
| **`std`（移动均价）** | 10 | **20** ⚠️ | **成本层被抬高** |
| `product.total_value` | 0 | 0 | 无在库，不动 |
| **存货 GL 110100** | 0 | **0** | **LC 零分录** |
| `in_move.value`（成本层） | 1000 | **2000** | 成本层吞了整笔 LC |
| COGS 600000 | 1000 | 1000 | 已售不重算 |
| 运费清算 600100 | 0 | **1000** | 整笔 LC 留费用 |
| LC 的 `account_move` | — | **无** | `diff = 0` |

**→ 假设 A 否定，假设 B 成立。**

### 实测结果 / Observed —— FIFO：殊途同归

| 成本法 | 结果 | 机制 |
|---|---|---|
| **AVCO** | `std = 20` | `_run_average_batch(force_recompute=True)` 从历史重算，历史里那条 in-move 刚被抬成 2000/100 |
| **FIFO** | `std = 20` | 零库存走回退分支：`elif last_in := product._get_last_in(): standard_price = last_in._get_price_unit()` —— 回退到最后一次进货单价，**而那条 in-move 刚被 LC 抬过** |

> **两条完全不同的代码路径，落到同一个幽灵单价。**
> 记录这一点是因为：**换成本法救不了这条**。

### 🔴 实测结果 / Observed —— 窗口内出库：真正的钱

```
补 LC 后：      std = 20   qty = 0   total_value = 0
负库存出 100：  OUT move.value = 2000       ← 按幽灵 std 结转，正确应是 1000
再收 50 @10：   std 被覆盖回 10             ← 成本层自愈
                但那笔 OUT.value 仍 = 2000  ← 🔴 永久钉死
```

> **凭空 1000 的 COGS 进了利润表，零单据支撑。**
> 出库 `value` 在 `_action_done` 那一刻钉死（[B-27](#b-27) 铁律），
> **后面再收货、std 回落，那笔 COGS 永远改不回来。**

### 机制 / Mechanism 📖 —— 根因是【两套判据】

| 文件:行 | 代码 | 作用 |
|---|---|---|
| `stock_landed_cost.py:372` | `if not remaining_qty: return AccountMoveLine` | **GL 侧有门控** → 零分录 |
| `stock_landed_cost.py:377` | `diff = additional_landed_cost * (remaining_qty / quantity)` | 分摊比例硬编码，无配置项 |
| **`stock_landed_cost.py:152`** | **`cost.valuation_adjustment_lines.move_id._set_value()`** | 🔴 **成本层侧无条件** —— 不看 `remaining_qty`、不看 `valuation` |
| `product.py:676-683` | 增量重算：`previous_qty = qty_available - added_qty` | 零前量时**直接取新进货单价**，不加权 |
| `product.py:692-696` | FIFO 零库存回退 `_get_last_in()._get_price_unit()` | 幽灵单价的 FIFO 来路 |
| `product.py:699` | `_run_average_batch(force_recompute=True)` | 幽灵单价的 AVCO 来路 |
| `stock_move.py:343` | `move.value = product.standard_price * _get_valued_qty()` | 🔴 窗口内出库按幽灵 std 结转 |

> ## 🔴 **根因：L1 与 L2 用了【两套判据】。**
> **GL 侧用 `remaining_qty` 门控（"这批货已卖完，1000 该进费用"）；
> 成本层侧无条件全额写入（"这条收货的总成本就是 2000"）。
> 两边各自都自洽 —— 所以谁都不报错。静默的根因就是【判据不对称】。**

### ⚠️ Odoo 自己原本是有防呆的

`stock_landed_cost.py:130-136` —— 旧版更新 `standard_price` 的代码块**仍以注释形式留在文件里**，
注释里带着这个守卫：

```python
#     if not product.uom_id.is_zero(product.quantity_svl):
#         product.sudo()...standard_price += cost_to_add_byproduct[product] / product.quantity_svl
```

「**库存为零就不动 `standard_price`**」—— v19 把这段整体注释掉，改走 `:152` 的 `_set_value()`，
下游的 `_update_standard_price` 里没有等价守卫。

> **⚠️ 定性口径（重要）：不要说"下游丢了守卫"。**
> FIFO 的 `_get_last_in()` 回退本身是合理的（零库存也要给个最后进货价），
> AVCO 的 `_run_average_batch` 也只是忠实地把输入传下去。
> **准确的说法是：`LC 不该对 remaining_qty = 0 的 in-move 计估值 / 触发 std 重算`。**
> 指着下游说"丢守卫"会让修补点找错地方。

### 传播边界 / Blast radius —— 下一次收货整个覆盖

```python
# product.py:676-683
previous_qty = product.qty_available - added_qty      # = 0
if compare(previous_qty, 0) > 0 and compare(qty_available, 0) > 0:
    new_avg_cost = (previous_qty * standard_price + added_value) / qty_available
elif not is_zero(added_qty):
    new_avg_cost = added_value / added_qty            # ← 走这支：直接取新进货单价
```

> **`previous_qty = 0` 时不做加权混算，幽灵单价被整个覆盖，不外传。**

### ⚠️ 修正记录 / Correction Log

| | |
|---|---|
| **原结论** | 幽灵 `std` 会在"下一次收货做移动平均混算"里悄悄带毒，往后传染 |
| **本次修订** | 🔴 **不成立，已撤回。** 实测：再收 50@10 后 `std` 直接回到 10 |
| **依据** | `product.py:676-683` 增量路径 `previous_qty ≤ 0` 时不加权，直接取新进货单价 |

**→ 真实风险窗口 = 【LC 验证日 D】到【下一次收货日 D2】之间，不是无限期。**

### 🔴 危害两级 / Two levels of harm

| 级别 | 内容 | 可逆性 |
|---|---|---|
| **一级（读）** | 窗口内所有读 `standard_price` 的地方全带毒：销售毛利报表 / BoM·MO 成本 / 产品成本显示 | ✅ 下次收货即自愈 |
| **二级（写）** | 🔴 窗口内**一旦出库**（负库存 / 超发 / backorder 先发后到），那笔 COGS 按幽灵 `std` 结转并 `_action_done` 钉死 | ❌ **不可逆，需人工核账** |

### 🔬 检测手段 / Detection —— 两段，可直接落地

**Stage 1 · 单据落差法（锁定 `no_move = true` 那一档）**

```sql
SELECT lc.id, lc.amount_total,
       COALESCE((SELECT SUM(l.debit) FROM account_move_line l
                  WHERE l.move_id = lc.account_move_id), 0) AS gl_debit,
       (lc.account_move_id IS NULL) AS no_move
FROM stock_landed_cost lc
WHERE lc.state = 'done' AND lc.company_id = %(cid)s
  AND lc.amount_total > COALESCE(
      (SELECT SUM(l.debit) FROM account_move_line l WHERE l.move_id = lc.account_move_id), 0);
```

| 落差性质 | 判定 | 处理 |
|---|---|---|
| **`gl_debit > 0`（部分命中）** | ✅ **[B-17](#b-17) 的设计行为** —— 已售份额按设计费用化 | **只做台账留痕，不报警** |
| **`account_move_id IS NULL`（`gl_debit = 0`）** | 🔴 **唯一的 `std` 污染硬信号**，100% 确定（源码保证：`line_ids` 为空才不建 move，`:372`） | 进 Stage 2 |

> 🔴 **落差 > 0 混了两种性质，不能一律当缺陷 —— 否则会把正常的半售场景当事故报上来。**

**Stage 2 · 锁定不可逆 COGS**

```
对每条 no_move = true 的命中，取其验证日 D，查该产品：
  D2 = 该产品在 D 之后的第一笔 IN move 日期（无则取 now）
  IF 存在 OUT move，其 date ∈ [D, D2)
      → 🔴 已产生按幽灵 std 结转、且已钉死的不可逆虚高 COGS，需人工核账
  ELSE
      → 🟡 仅窗口内报表带毒，下次收货即自愈，无需改账
```

### 对策 / Mitigation

- 🔴 **硬纪律：LC 必须在货发出之前分摊完毕。**
  这条纪律在 [B-17](#b-17) 已经有了 —— **本条给出它的机制根因，以及破纪律之后的确切损害。**
- **已经破了纪律的补救：**
  - 窗口内**无** OUT move → 等下一次收货自动覆盖，或手工库存重估（Inventory → Valuation → Revaluation）
  - 窗口内**有** OUT move → 🔴 那笔 COGS **永久不可逆**（[B-27](#b-27)），只能人工核账
- **月结检查项**：跑一次 Stage 1，`no_move = true` 的条数应为 **0**。

---


# 第五章 · 绕开采购—销售链的估值事件：报废、重估、寄售
## Chapter 5 · Valuation events outside the purchase-to-sale chain

> 货物不总是「买进来、卖出去」。本章四条覆盖绕开常规链路的情形。
>
> **⚠️ 本章的 B-15 / B-19 在 2026-07-14 被推翻重写。** 两条旧结论（「Scrap 无条件出分录」、
> 「Adjust Valuation 已死」）都错了，而且错的方向相反 —— 前者把**有条件**当成了无条件，
> 后者把**搬家**当成了移除。**统一的真相见 [B-13](#b-13)。**

---

<a name="b-15"></a>
## 5.1 · B-15 · 🔴 报废/盘亏出不出分录，取决于库位有没有配科目（默认不配）
### Whether scrap and shrinkage post at all depends entirely on the location's account

| | |
|---|---|
| **等级** | 🔴（**机制已推翻重写**；配与不配是两个完全不同的世界） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |
| **修订** | **2026-07-14 — 原版的机制解释「取决于有没有发票对手方」是事后合理化，已作废。** |

### 🔴 真正的闸门 / The real gate 📖

**`stock.location.valuation_account_id`。就这一个字段。**

```python
# stock_account/models/stock_move.py:651
def _should_create_account_move(self):
    return self.product_id.is_storable and self.is_valued \
        and (self.location_dest_id.valuation_account_id
             or self.location_id.valuation_account_id) \      # ← 闸门
        and not float_is_zero(self.quantity, ...) \
        and self.product_id.valuation == 'real_time'
```

**Odoo 默认【不】给任何虚拟库位配这个字段。**（这是 v19 的变化 —— v18 的
`property_stock_account_input/output` 那套暂估科目没了。）

### 两个世界 / Two worlds

| | **库位【没配】科目**（Odoo 默认） | **库位【配了】科目** |
|---|---|---|
| 盘亏 / 报废时 | **零分录** | **立刻**：`Dr Loss / Cr 110100`，当场 `_post()` |
| L1（子账） | 减 | 减 |
| L2（GL） | **不动** | 减 |
| **对期末差额** | 🔴 **单边操作 → 制造差额** | ✅ **同额同向 → 零贡献** |
| 期末 Stock Variation 里装着 | 时点差 **＋ 盘亏 ＋ 报废 ＋ 改成本** → **垃圾桶** | 只有时点差 + [B-14](#b-14) 价差 → **可诊断** |

> **配上库位科目，Stock Variation 才有诊断价值。**
> 它的余额从此是一个**健康指标**：干净的公司它应该很小；**它很大 = 有结构性问题。**

### 实测结果 / Observed —— 配了科目之后

```
STJ/2026/07/0003        SP/00001 - Galaxy S22 Ultra
    Dr 400098 Inventory Adjustment    863.98
       Cr 131100 Inventory                     863.98
```

日记账 = `company.account_stock_journal_id`（设置页里的 *Inventory Valuation*）。
金额 = 该 lot 的**真实成本**（`move.value`）。

**盘盈方向相反**：`Dr 110100 / Cr Loss`（冲减费用）—— 见 [B-13](#b-13) 的源码。

### 🔴 配了之后，盘点调整就变成一个【会计事件】了

| | 配之前 | 配之后 |
|---|---|---|
| 仓库员做一笔盘点调整 | 只污染报表，期末混进 Stock Variation | **直接、立刻、`sudo()` 写进损益表** |

> **「盘点/报废走权限层 —— 菜单只给仓库管理员」这条纪律的重要性，因此提高了一个量级。**
> 之前那是「防数据脏」；现在那是**「防未授权的人直接改损益表」**。

⚠️ 分录会走锁期检查（`_post()` → `_check_fiscal_lock_dates`），
**但它用的是「今天」的日期**（[B-32](#b-32)）—— 锁了上月拦不住上月的盘点。

### `account_type` 的选择 —— 和 [B-08](#b-08) 一样的坑

| 类型 | 落在 | 含义 |
|---|---|---|
| `expense_direct_cost` | **毛利之内**（COGS 段） | 损耗是销货成本的一部分 |
| `expense` | 毛利之下（营业费用） | 损耗是经营开支，不脏毛利 |

**这是政策判断，不是技术判断。必须自觉地做一次，不能保持默认。**

### 对策 / Mitigation

```
Inventory → Configuration → Locations  →  把 usage = 'inventory' 的【每一个】都查一遍
    · Inventory adjustment  (stock.location_inventory)
    · Scrap                 (若存在)
    · Production            (usage = 'production'，MRP 启用时存在)
→ 逐个配 Stock Valuation Account，并明确各自的 account_type
```

**没配的那些，move 依然零分录，依然靠期末关账扫。** → [B-33](#b-33)

### 修正记录 / Correction Log

| 日期 | 曾经的结论 | 为什么错 |
|---|---|---|
| **2026-07-14** | 「出不出分录取决于有没有发票对手方」 | **事后合理化。** 真正的闸门是 `_should_create_account_move` 里的 `valuation_account_id` |
| **2026-07-14** | 「Scrap 即时出分录」（无条件） | **默认库位不配科目 → 默认零分录。** 原版实测的库是**已经配过**科目的生产库 |

---

<a name="b-19"></a>
## 5.2 · B-19 · 🔴 Adjust Valuation 没有被移除 —— 它搬家了，而且它 ⊥ GL
### Adjust Valuation was not removed — it moved. And it never touches the GL

| | |
|---|---|
| **等级** | 🔴（**结论已彻底推翻**） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |
| **修订** | **2026-07-14 — 原版结论「Adjust Valuation 已死」是【去老地方找没找到】。** |

### ⚠️ 原版错在哪 / What the old entry got wrong

老入口（`Stock Valuation` 报表的齿轮菜单）确实没了 —— **因为那张报表本身被删了。**
但功能**还在**，只是搬到了 `stock.move` 上。

### 现在从哪进 / Where it lives now 📖

**没有独立菜单，两个入口：**

```
① 产品表单 → 智能按钮/动作 "Valuation"（stock_move_valuation_action）
              → 列出该产品所有 is_in / is_out 的 move
② 选中任意 stock.move → ⚙️ 动作菜单 → "Adjust Valuation"
              （ir.actions.server: stock_move_action_adjust_valuation）
```

源码 `stock_account/models/stock_move.py`：

```python
value_manual = fields.Monetary("Manual Value", compute="_compute_value_manual",
                               inverse="_inverse_value_manual")      # :32
                               # 注释原文: "Useful for testing and custom valuation"

def action_adjust_valuation(self):                                    # :155
    action = self.env['ir.actions.act_window']._for_xml_id("stock_account.product_value_action")
    ...
```

弹出的是 **`product.value` 向导**：显示 Current Value，填 New Value + 描述。

### 🔴 但是 —— **它不产生任何 GL 分录**

**实测**（就是 [B-14](#b-14) 那个 GL=700 / 子账=600 的库）：

```
出库 move 是 Stock → Customers，两端库位都无 valuation_account_id
    → _should_create_account_move = False（B-13）
    → move.account_move_id 为空（当初的 COGS 挂在客户发票上）

Adjust Valuation 把 move.value 500 → 600
    → 只写了 1 条 product.value
    → 没有任何 account.move
    → GL 110100 仍是 700，一分未动
```

> **它只改「计算用的估值数字」（影响 FIFO 层、影响报表），对方科目根本不存在 —— 因为没生成分录。**

### 🔴 后果 / Consequence

**任何「用 Adjust Valuation 修 GL 差异」的想法都是错的。**
在 [B-14](#b-14) 的场景里，子账（600）本来就是对的，错的是 GL（700）。
**改子账 = 把对的那一边也弄错。**

### 货转固资：**必须用「库位科目法」** / Goods → Fixed Asset

| 方案 | 结果 |
|---|---|
| **库位科目法**（库位设 `valuation_account_id` = 固资科目，把成品移入） | ✅ **自动分录** `Dr 160000 固资 30 / Cr 110100 存货 30`（走库存估值日记账），**货值真正资本化** |
| Adjust Valuation 替代它 | ❌ 普通 move 上不产生 GL，**搬不动价值到固资科目** |
| 自动 Create Asset | ❌ **不触发** —— `_auto_create_asset` 只对**发票类** move 生效，库存估值分录是普通日记账分录，被跳过 |
| **手动 Create Asset** | ✅ 选中固资那条 journal item → ⚙️ 动作 → **Create Asset**（`turn_as_asset`）→ 打开预填好的 `account.asset` 草稿表单，保存即成资产 |

> **库位科目法不是 hack —— 它是官方机制。**
> `stock.location.valuation_account_id` 的 help 原文：
> *"Expense account used to **re-qualify** products removed from stock and sent to this location"*
> —— **「re-qualify」= 重新定性。这个字段就是为「货物离开库存、变成别的东西」设计的。**
>
> 设置页底部那句 *"Other accounts can be defined on **Inventory Loss** and **Production** on
> dedicated **locations**"* 也是在提示同一件事。

**⚠️ 若复用 `Inventory adjustment` 库位做这件事**，Loss Account 是**报废 + 盘亏 + 本操作**
三者共用（[B-15](#b-15)、[B-33](#b-33)）—— 窗口期内别人的任何盘点或报废都会串进固定资产。
**正解是新建一个专用库位**，而不是临时改再改回来。

### 修正记录 / Correction Log

| 日期 | 曾经的结论 | 为什么错 |
|---|---|---|
| **2026-07-14** | 「Adjust Valuation 已死 / 已随 SVL 一并移除」 | **只是搬家。** 现在挂在 `stock.move` 上（`action_adjust_valuation`，`stock_account/models/stock_move.py:155`）。老报表没了，功能还在 |
| **2026-07-14** | 「库位科目法是 🔬 推论」 | **✅ 实测通过**，且是官方设计的 "re-qualify" 机制 |

---

<a name="b-28"></a>
## 5.3 · B-28 · 🔴 `product.value` / `value_manual` / 改 lot cost —— 全部只动报表侧
### Manual valuation writes never reach the GL

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### `product.value` 是什么 / What it is 📖

`stock_account/models/product_value.py`：

```python
""" This model represents the history of manual update of a value.
    - Modification of the product standard price
    - Modification of the lot standard price        ← lot 级手工估值，v19 原生支持
    - Modification of the move value
"""
product_id = Many2one('product.product')
lot_id     = Many2one('stock.lot')
move_id    = Many2one('stock.move')
value, date, user_id, description
```

而 `_get_value_data(ignore_manual_update=...)` 的取值优先级：

```
manual (product.value)  >  bill / invoice  >  PO / SO  >  standard price
```

**手工值是最高优先级 —— 覆盖账单、覆盖 PO、覆盖标准成本。**

### 🔴 实测：三条手工路径，全部 ⊥ GL

| 操作 | L1（报表 / 子账） | **L2（GL）** |
|---|---|---|
| **Adjust Valuation**（改 `move.value`） | ✅ 变 | ❌ **零分录** |
| **改 `lot.standard_price`** | ✅ 变 | ❌ **零分录** |
| **改 `product.standard_price`** | ✅ 变 | ❌ **零分录** |

**源码定性证据**：`product.py::_change_standard_price` —— **它根本不生成任何 `account.move`**，
只写 `product.value` 历史记录 + 更新显示字段。

### 改 lot cost 的两个实测细节

| lot 状态 | 改 cost 后 |
|---|---|
| **售罄**（qty = 0） | `total_value` 仍是 0 —— **纯装饰，零影响，不追溯已结转的 COGS** |
| **在库**（qty = 10，10 → 15） | `total_value` 更新到 150，但 **GL 仍是 100** → 报表与 GL 背离 50 |

> **改 lot cost 只动「报表侧估值」，既不落 GL，也不追溯已发出的成本。**

### 🔴 后果 / Consequence

这一条把 [B-13](#b-13) 的总定理钉死了：**L1 上的任何写入都不会溢出到 L2。**

**所以：**
- ❌ 不能用手工估值修 GL 差异
- ❌ 不能用手工估值做货转固资（[B-19](#b-19)）
- ✅ 手工估值的**唯一正当用途**：修正**报表侧**的成本数字（例如 [B-20](#b-20) 的混价 lot）
- ⚠️ 而这样做会**制造**一个新的 L1/L2 差额 → 最终被期末关账扫进 Stock Variation（[B-31](#b-31)）

> **`value_manual` 的源码注释是 "Useful for testing and custom valuation"。**
> **Odoo 知道 [B-14](#b-14) 这类缺口存在，它的兜底方案就是「让你手工调 + 记一本 log」，
> 而不是自动路由到某个科目。这是「no replay of past data」设计哲学的必然结果。**

---

<a name="b-09"></a>
## 5.4 · B-09 · 寄售：仓库侧干净，异常发生在开票那一刻
### Consignment: the warehouse side is clean — the anomaly happens at invoicing


| | |
|---|---|
| **等级** | 🔴 **高危** |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### 场景 / Scenario
一张 SO 里**混卖**自持库存和寄售库存，直接 Create Invoice。

### ✅ 2026-07-14 · T-07 补全 —— **收货与退回，两个方向都零 GL**

```
                        move value   account_move   owner
寄售收货（owner=寄售商）      0          False       Gemini Furniture
寄售退回（owner=寄售商）      0          False       Gemini Furniture     ← 退回路径

[对照] 自有货收货            250         False*       None
[对照] 自有货退供应商         250         False*       None
```

- **寄售货 `value = 0`：`owner` 挂在寄售商名下的库存，【根本不进公司估值体系】。**
  **收、退都 `value = 0`、零分录。寄售退回【不产生任何仓库侧 GL 异常】。**
- **自有货 `value = 250`（报表侧有值），`account_move = False`\* 是因为本测试没配库位科目、也没开票**
  —— **自有货的 GL 来自【账单/发票过账】（门①），不来自库存移动。**
- **判别点：寄售 `value = 0` vs 自有 `value = 250`** —— **寄售库存完全在公司估值体系之外，收退对称，均不碰 GL。**

**→ 印证并补全本条：仓库侧干净，异常【只在开票端】。**

---

### ① 仓库 / 估值侧 —— **完全干净，没有问题**

**货权判定** —— `stock_move_line.py:45`：

```python
def _should_exclude_for_valuation(self):
    return self.owner_id and self.owner_id != self.company_id.partner_id
```

只要 `owner_id` 不是本公司，这条 move line 就被**排除在存货估值之外**。

| | 自持库存 | **寄售库存** |
|---|---|---|
| 入库 | 生成估值 | **不生成估值 —— 货本来就不在你账上** |
| 该批货的成本 | 有 | **无** |
| 发货 | 估值层减少，存货科目变动 | **不动你的存货，也不该动** |

> **寄售的货没有估值、没有成本。发货后仓库侧的数据是正确的 —— 这一侧不需要任何补救。**
>
> **Consigned goods carry no valuation and no cost. After delivery the warehouse side is
> correct. Nothing needs fixing here.**

### ② 开票侧 —— 🔴 **异常在这里**

**SO 的开票由 `qty_delivered` / `qty_to_invoice` 驱动，从不关心发出去的货是谁的。**

- 发货时可能同时从「自持」和「寄售」两种 quant 上扣数
  （一个 `stock.move` 拆成多条 `move_line`，`owner_id` 不同）
- 但回到 SO，`delivered` 数量是**合并统计**的
- → **一张发票、一条发票行、开总数量**

**于是开票时 Odoo 给寄售的那部分也算了一笔 COGS** ——
`_get_cogs_price_unit()` (`stock_move.py:257`) 把 `valued_consigned_qty` 也算进了分母。

### 实测结果 / Observed

> **混卖 + Create Invoice → 开票成本 = 销售行产品的 `cost` × 全部数量，不区分货权。**
>
> **Mixed sale + Create Invoice → the invoiced cost is the product's `cost` × the FULL quantity,
> with no distinction between owned and consigned units.**

**那部分货明明没有成本（见 ①），开票时却被按产品 `cost` 估了一个。**

### 后果 / Consequence

| | |
|---|---|
| **金额错配** | 产品 `cost` 未必等于寄售结算价 |
| **时点错配** | 寄售的真实成本要等寄售商事后开来的那张采购账单 |
| **维度缺失** | 想知道"这单里哪些是寄售卖的" → **销售单和发票上都没有这个维度**，只能查 `stock.move.line.owner_id` |

### 闭环怎么走 / How the loop closes

1. **卖给客户**：一张客户发票，自持 + 寄售合并，不分货权
2. **自持部分**：发货产生估值层，开票确认 COGS，存货减少
3. **寄售部分**：不动你的存货；你欠寄售商的钱由**一张独立的供应商账单**体现
   （通常按实际卖出量结算）—— 那张账单才是寄售成本的真实来源

### 对策 / Mitigation

- 货权维度**只存在于 `stock.move.line.owner_id`** —— 任何按货权拆分的分析必须从这里取数
- 寄售的真实成本以**寄售商的采购账单**为准，不以开票时的 COGS 为准
- 原生功能**不提供**在 SO / 发票层区分货权的能力

---


# 第六章 · 报表与毛利：数据是对的，你看到的未必
## Chapter 6 · Reports and margins — the data is right; what you see may not be

> **本章的核心命题：v19 的会计链路算对了成本，缺的是把成本和收入连起来的那个报表维度。**
前两条讲报表口径的陷阱，后两条讲原生毛利功能的两个时序前提。

v19's accounting chain computes the right cost. What is missing is the reporting dimension that
would join that cost to revenue.

---

<a name="b-06"></a>
## 6.1 · B-06 · Stock Valuation 报表的 Unit Cost 是产品级口径，与 GL 不同源
### The Stock Valuation report's Unit Cost is product-level — a different basis from the GL


| | |
|---|---|
| **等级** | 🟡（口径差异，不是报表 bug） |
| **状态** | ✅ **已实机验证（2026-07-14 · T-05 重验闭合）** —— 🔬 降级已解除 |
| **前提** | v19 · `lot_valuated = True` |

### 事实 / The fact

| 数据 | 口径 |
|---|---|
| `Stock Valuation` 报表的 **Unit Cost / Remaining Value** 列 | **产品级** `standard_price` |
| `stock.move.value` / **总账 COGS 分录** | **lot 级** `lot_id.standard_price`（[B-05](#b-05)） |
| `Locations` 视图（需 Storage Locations） | **lot 级** Value |

**两个数不同源，因此在多批次产品上必然不相等。**

**报表没有错 —— 它显示的就是它标注的那个东西（产品级单位成本）。**
**出错的是把这一列当作「这批货的成本」来读。**

**The report is not wrong. It shows exactly what its column header says: the product's unit cost.
The error is in reading it as the cost of a specific batch.**

### 为什么难察觉 / Why it slips past

**总额永远对得上，只有拆分不同。** 全部卖完时账完全正确；只有**部分发货**时才看得出差异。
因此任何对账程序都发现不了它。

### ✅ 重验结果 / Re-verification — 本条成立（2026-07-14）

```
开 lot_valuated。收两颗成本不同的 lot：LOT-A 5 @ 100，LOT-B 5 @ 200

product.standard_price（产品级）  = 150.0        ← 🔴 加权平均（100 + 200 混）
product.total_value               = 1500.0

lotA.standard_price = 100.0   |   lotB.standard_price = 200.0     ← 底层是 lot 级
LOT-A:  quant qty=5  value=500    →  Unit Cost = 150.0            ← 🔴 判别点
LOT-B:  quant qty=5  value=1000   →  Unit Cost = 200.0
```

| 侧 | 口径 |
|---|---|
| **价值侧** | ✅ **lot 级** —— 每颗 lot 的 quant 各记各的成本（500 / 1000），**互不混** |
| **Unit Cost 列** | 🔴 **产品级加权平均（150）** —— 这正是报表按科目 / 产品聚合时显示的口径 |

**根因：v19 的 Stock Valuation 报表是【按科目聚合】的（总值 1500，无 per-lot 明细行）。**
**所以报表层面的单价是产品级 150，不暴露 lot 的 100 / 200。**

> ## 🔑 **顺带得到一个更大的模式：**
> ## **【估值科目】是 v19 的【唯一聚合轴】。**
>
> **Stock Valuation 报表按它聚合。关账凭证也按它聚合（[B-35](#b-35)）。**
> **→ 这不是两个巧合，是一个设计。**
> **→ 推论：想要【任何维度】的颗粒度，唯一的杠杆都是【给它配一个独立的估值科目】。**
> **→ 这是上线期决策，补做代价极高。**

### 原重验方法（已执行）/ Re-verification method (executed)

```
同一产品，两个成本不同的 lot（lot1 = 10 @ 100，lot2 = 10 @ 200）
不发货，直接打开 Stock Valuation 报表
```

**只看一件事：两行的 Unit Cost 列，是 150 / 150，还是 100 / 200？**

| 结果 | 结论 |
|---|---|
| 150 / 150 | 该列确为产品级口径，本条成立，恢复 ✅ |
| 100 / 200 | 该列已是 lot 级，本条作废 |

### 📌 2026-07-12 · 范围收窄 / Scope narrowed（保留作为演进记录）

重验测试**尚未跑**（Unit Cost 列仍待确认）。但**价值侧**已有实测，本条的适用范围因此收窄：

**① 单次收货的 lot：`quant` 的 Value 是 lot 级，且与 GL 勾稽。**

```
Q-A 收 5 @ 100、Q-B 收 5 @ 200（两颗独立 lot），只发 5 件 Q-B
发货后：quant  Q-A qty=5 value=500 · Q-B qty=0 value=0 · 合计 500
        GL 110100 = 500 · COGS = 1,000
→ 数量口径（减 Q-B）与价值口径（减 1,000、留 500）一分不差
```

**减的是实际挑走的 lot，不是 FIFO 最老的那颗。** 仓库 quant 报表与库位报表读同一张
`stock.quant`，结论相同。

**② 因此**：本条若成立，**只对 `Unit Cost` 列成立，不对 `Value` 列成立**。

**③ 但价值侧确有一个已证实的分裂 —— 与本条无关，别混淆：**
**同一 lot 多次以不同单价收货**时，`quant` 按 lot 内部的 FIFO 层消耗，而 GL 按 lot 的标量
混价结算，两者在**部分出库期间**分裂（实测差 250），lot 耗尽自愈。→ **[B-20](#b-20)**

Only the **Unit Cost** column remains in question. The **Value** column tracks the lot actually
picked and ties to the GL — except in the re-received-lot case, which is a different and now
proven divergence ([B-20](#b-20)).

### 对策（无论重验结果如何都成立）/ Mitigation

- **lot 级单位成本 → 看 `Locations` 视图或 lot 表单**（必须先启用 Storage Locations）
- **真实成本 → 以总账 COGS 分录为准**
- **`lot.avg_cost` 不是成本，不可用于任何口径**（[B-21](#b-21)）

---

<a name="b-07"></a>
## 6.2 · B-07 · Lot 维度无任何标准报表支持
### No standard report carries a lot dimension


| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 实机验证 |

### 实测结果 / Observed

`Inventory → Reporting → Stock` 的可选列（Optional Columns）**全集**：

```
Product Category · Cost Method · Unit Cost · Total Value
Incoming · Outgoing · Forecasted
```

**没有 Lot / Serial 维度。**

lot 级价值**只在两处可见**：`Locations` 视图、lot 表单。
而 `Locations` 视图**必须先启用 Storage Locations** 才存在。

No lot dimension is available in any standard report. Lot-level value is visible **only** in the
Locations view and on the lot form — and that view requires Storage Locations to be enabled.

### 边界 / Scope

**lot 成本在总账里是正确的（[B-05](#b-05)）—— 缺的是报表维度，不是数据。**

标准报表**无法按 lot / serial 聚合**，因此下列问题在原生功能内无解：
单个 lot 的成本、单个 lot 的售出金额、按 lot 的盈亏。

### 对策 / Mitigation

- 单个 lot 的成本 → 逐条查看 lot 表单或 `Locations` 视图
- 需要 lot 维度的聚合报表 → 原生无此能力

---

<a name="b-10"></a>
## 6.3 · B-10 · Margins 功能晚启用 → 历史订单毛利永久错误
### Enabling Margins after the fact permanently corrupts historical margins


| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 实机验证 |
| **前提** | v19 · `lot_valuated = True` · Sales → Margins |

### 实测结果 / Observed

**S00003**（卖 lot1，真实成本 100/台，售价 300/台）—— **发货并开票之后**才启用 Margins：

```
S00003   Qty 10   Unit Price 300.00   Cost 500.00   Margin -2,000.00 (-66.67%)
```

| | 数字 |
|---|---|
| SO 显示的毛利 | **−2,000（−66.67%）** ← 巨亏 |
| 总账里的真实毛利 | 3,000 − 1,000（lot1 真实 COGS）= **+2,000** ← 翻倍 |

**符号是反的。**

### ⚠️ 先澄清一个命名陷阱 / A naming trap, first

**`purchase_price` 是 `sale_margin` 模块里那个字段的技术名。它不是"采购价"。**

| | |
|---|---|
| **技术字段名** | `sale.order.line.purchase_price` |
| **UI 标签** | **Cost** |
| **实际取值** | 产品的 `standard_price`（**AVCO 下 = 移动加权平均成本**） |

**实测反证**（取自 [B-11](#b-11) 的时间线）：库存 lot2 (10 @ 500)，PO3 收 10 @ 1,000
→ 产品 avg = 750 → **SO Cost 显示 750**。

**750 不是任何一张 PO 的价格**（那两张是 500 和 1,000）。**它只可能是移动平均。**
若该字段真取采购价，此处应显示 1,000 或 500。

> **字段名会误导任何读源码或写自建模块的人。看到 `purchase_price` 别读成采购价 —— 读成 Cost。**
>
> **The field is named `purchase_price` but holds the product's `standard_price`.
> Under AVCO that is the moving average cost, not any purchase order's price.**

### 机制 / Mechanism

正常情况下（Margins 从一开始就开着），`sale_stock_margin` 会在**发货完成时**把
`purchase_price` 改写为**实发货物的真实成本**（见 [B-11](#b-11)）。

但如果 Margins 是**在发货之后**才启用的：
- 那个"发货时改写"的钩子早已错过
- `purchase_price` 只能回退到 **产品当前的 `standard_price`**（当时是 500）
- **且此后不再更新** —— 错误被永久冻结

If Margins is switched on *after* the delivery, the delivery-time hook that would have written
the real cost has already passed. The field falls back to the product's *current* standard price
and is then frozen. The error is permanent.

### 后果 / Consequence
- 启用 Margins 之前的**所有历史订单**，毛利永久错误且不可修复
- 错误方向随产品成本的漂移而定，**可能符号相反**
- 历史业绩、提成、客户盈利分析全部受污染

### 对策 / Mitigation
> **Margins 必须在系统上线第一天就启用。**
> **一旦漏开，历史订单的毛利只能视为无效数据 —— 唯一可信的是总账 COGS。**
>
> **Enable Margins on day one. If it was missed, treat all pre-existing margins as
> invalid — the GL's COGS is the only trustworthy figure.**

---

<a name="b-11"></a>
## 6.4 · B-11 · 发货前的毛利是估计值，发货后才锁定为真实成本
### Pre-delivery margin is an estimate; delivery replaces it with the real cost


| | |
|---|---|
| **等级** | 🟢（机制正确，但需知道时点） |
| **状态** | ✅ 实机验证 |

### 测试时间线 / Test timeline

```
库存：lot2 (10 @ 500)
① PO3 收 10 @ 1,000              → 产品 avg cost = 750
② 新建 S00004，加产品行           → SO Cost 显示 750       ← 估计值（产品级 avg）
③ 发货，拣选 lot2（真实成本 500）  → SO Cost 变成 500       ← ✅ 改写为实发批次的真实成本
④ PO4 收 10 @ 50                  → 产品 avg cost = 525
                                  → SO Cost 仍是 500       ← ✅ 已冻结，不再漂移
```

**实测截图**：`S00004  Qty 10  Delivered 10  Unit Price 1,000  Cost 500.00  Margin 5,000 (50%)`
库存报表同时显示 `Unit Cost 525.00 / Total Value 10,500 / On Hand 20`（lot3 + lot4）。

### 机制 / Mechanism

`sale_stock_margin` 模块（`sale_margin` + `sale_stock` 同时存在时自动装）在**发货完成**时，
把 `sale.order.line.purchase_price` 从"产品当前 avg cost"改写为 **`stock.move` 的实际估值**。

| 时点 Stage | `purchase_price` 取自 | 准确性 |
|---|---|---|
| 加产品行 → 发货前 | 产品当前 `standard_price`（avg / std / fifo） | ⚠️ **估计值**，对多批次产品可能差很远 |
| **发货完成后** | **实发 `stock.move` 的真实价值**（lot 估值下 = lot 成本） | ✅ **正确** |
| 之后的任何采购账单 | **不再改变** | ✅ 已冻结 |

### 后果 / Consequence
- **报价阶段的毛利不可信** —— 它用的是产品级平均，而实际发哪批货还没定
- 对二手手机这类"同一产品、几十个收购价"的生意，报价毛利的偏差是**系统性的**（750 vs 500 = 50%）
- 发货后的毛利是**准的**，可以用

### 对策 / Mitigation
- 报价/议价阶段**不要依赖 Margin 字段**做定价决策
- 若必须在报价阶段看真实毛利 → 需要在下单时就锁定批次（自建）
- 已发货订单的 Margin 可信 —— 但前提是 Margins 功能**上线即启用**（[B-10](#b-10)）

### 修正记录 / Correction Log
| 曾经的结论 | 为什么错 |
|---|---|
| "产品 cost 是移动靶，供应商账单会追溯改写已关闭订单的毛利" | 只在 [B-10](#b-10) 的"晚启用"场景下成立。正常情况下发货即冻结。PO4 测试证伪。 |

---


# 第七章 · 期末关账：那台橡皮擦
## Chapter 7 · Period close — the eraser

> **期末关账是 [B-13](#b-13) 三条入口里的第 ③ 条 —— 也是唯一一条 catch-all 的。**
> 它把 L1（报表）与 L2（GL）之间的**一切**背离，不加区分地扫进同一个科目。
>
> **本章的核心命题（[B-31](#b-31)）：它是一块橡皮擦，不是一台校正器。它不认对错。**
> 时点差、[B-14](#b-14) 价差、未配科目的盘亏、手工改成本、**以及结构性错误** ——
> 全部一起被抹平。**按下按钮的那一刻，证据就没了。**

---

<a name="b-08"></a>
## 7.1 · B-08 · Stock Variation 的对方科目取值链；配错则机制静默失效
### The Stock Variation counterpart chain — misconfigure it and closing silently no-ops


| | |
|---|---|
| **等级** | 🔴 **高危**（若配错，整个结转机制静默失效） |
| **状态** | ✅ 实机验证（干净的 v19 测试库，未经人工改动） |

### 实测结果 / Observed —— 干净库的默认行为
```
Accounting → Review → Inventory Valuation

Initial Balance                                   2,000.00
Stock Variation                                   1,000.00
    Cr 400001 Cost of Goods Sold in Trading                1,000.00   ← 损益类科目
    Dr 131100 Inventory - Raw Materials           1,000.00
Ending Stock                                      3,000.00
```

`400001` 的 `account_type = expense_direct_cost` —— **一个损益科目**。

### 反例 / Counter-example（真实生产库的配置错误）
若把 Stock Variation 指向一个 `asset_current` 科目：

```
Dr 131100 Inventory   (asset_current)     92,223.36
   Cr 400097 Variation (asset_current)              92,223.36
```

| | 过账前 | 过账后 |
|---|---|---|
| 131100 存货 | 2,782,016.63 | 2,874,239.99 ✓ |
| 400097 变动 | 0 | **−92,223.36**（资产科目挂贷方） |
| **总资产** | 2,782,016.63 | **2,782,016.63 — 一分没变** |
| **损益** | — | **零影响** |

**资产 ↔ 资产的对倒。存货低估的问题一分钱都没解决 —— 只是把差额挪到了一个幽灵资产行。**

An asset-to-asset entry. Total assets unchanged, P&L impact nil, and the understatement
is not corrected at all — it is simply parked in a phantom asset line.

### 后果 / Consequence
- **结转机制完全失效，且系统不报错。**
- 若同时把 Periodic Valuation 设为 Monthly → 每月自动生成一张**无效凭证**，
  资产负债表上累积一个越来越大的负数科目。

### 对策 / Mitigation
> **上线检查项：Stock Variation 科目的 `account_type` 必须是损益类（`expense` 或 `expense_direct_cost`）。**
> **Go-live check: the Stock Variation account's `account_type` MUST be a P&L type.**

改动前须由会计确认其在损益表中的列示位置（建议置于 Cost of Revenue 之下作为存货变动调节项）。

### 📌 2026-07-14 补 · 对方科目的完整取值链 📖

关账凭证的对方科目**不是**硬编码的，源码 `_get_stock_valuation_account_vals` 的取值顺序：

```
① 估值科目（如 110100）上挂的  account_stock_variation_id     ← 首选
② 退回  company.expense_account_id                            ← 兜底
③ 两者都为空  →  【静默跳过，不生成分录，不报错】              ← 🔴
```

**→ 上线检查必须确认 ① 或 ② 至少有一个配了。** 否则 Generate Entry 点了没反应，
而且**不会有任何提示**。

### 🔴 `account_type` 决定了 [B-14](#b-14) 的伤害有多大

[B-14](#b-14) 的价差、[B-15](#b-15) 未配科目时的盘亏、[B-28](#b-28) 的手工改成本 ——
**全部**在期末被扫进这个科目（[B-31](#b-31)）。所以：

| Stock Variation 的 `account_type` | 后果 |
|---|---|
| `expense_direct_cost` | ✅ 落在 **COGS 段内** → **聚合毛利率正确** |
| `expense` | ⚠️ 落在毛利之下 → **毛利率虚高**（成本被挪出了毛利） |
| `asset_*` | 🔴 **机制静默失效**（见上方反例） |

**⚠️ 但无论配哪个，按 SKU / lot / 单台的成本分解都救不回来** —— 那笔钱进了一个不带
产品维度的桶。→ [B-14](#b-14)、[B-31](#b-31)

---

<a name="b-12"></a>
## 7.2 · B-12 · Stock Variation 是净额，会掩盖大额对冲错误
### Stock Variation is a NET figure that masks large offsetting errors


| | |
|---|---|
| **等级** | 🔴 **高危**（认知陷阱） |
| **状态** | ✅ 实机验证 |

### 实测数据 / Observed

测试库状态：PO1 收 10 @ 100 但**开票 20 @ 100**；PO2 收 10 @ 200 但**从未开票**。

```
Accounting → Review → Inventory Valuation

Initial Balance   131100 = 2,000      ← 总账侧（只有 PO1 的超额账单）
Stock Variation           1,000       ← 差额
Ending Stock              3,000       ← 库存侧 = lot1 (1,000) + lot2 (2,000)
```

### 那个 1,000 是怎么来的 / What the 1,000 actually contains

| 成因 Cause | 方向 | 金额 |
|---|---|---|
| PO2 已收货未开票（GRNI）→ 总账少记 | **+2,000** | |
| PO1 超额开票（收 10 开 20）→ 总账多记 | **−1,000** | |
| **净额 = 报表显示的 Stock Variation** | | **1,000** |

> **两个方向相反的错误，一个 +2,000、一个 −1,000，被压缩成了一个看起来无害的 1,000。**
>
> **Two errors in opposite directions — one of +2,000 and one of −1,000 — collapse into a
> single, innocuous-looking 1,000.**

### 后果 / Consequence

**Stock Variation 的绝对值大小，与底层问题的严重程度没有必然关系。**

一个 92,223 的差异，底下可能藏着一个 +50 万的 GRNI 和一个 −40 万的超额开票。
**小数字不代表小问题。**

The magnitude of Stock Variation says nothing about the severity of the underlying problems.
A gap of 92,223 could be hiding a +500k GRNI netted against a −400k over-billing.
**A small number does not mean a small problem.**

### 对策 / Mitigation
> **永远不要只看 Stock Variation 的净额。必须拆解到成因：**
> 1. GRNI（已收货未开票）—— 逐 PO 算 `qty_received − qty_invoiced`
> 2. 已发货未开票 —— 逐 SO 算 `qty_delivered − qty_invoiced`
> 3. 超额开票（[B-04](#b-04)）
> 4. 被删除的已过账账单（[B-02](#b-02)）
>
> 四项的**代数和**才应该等于 Stock Variation。对不上 = 还有第五个成因没找到。


---

<a name="b-29"></a>
## 7.3 · B-29 · 关账凭证是永久增量分录，无红冲
### The closing entry is a permanent, incremental posting — never reversed

| | |
|---|---|
| **等级** | 🟡（机制正确；但必须知道它**不是预提**） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### 入口 / Where

```
Accounting → Review → Inventory Valuation → 【Generate Entry】
    → res.company.action_close_stock_valuation()
```

### 实测 / Observed —— 就是 [B-14](#b-14) 那个 GL=100 / 报表=0 的库

```
关账报表读数：
    stock.value (报表侧, total_value)     =   0.0
    stock.accounting_value (GL 110100)    = 100.0
    DIFF                                  = -100.0      ← 看得见滞留

点 Generate Entry：
    Dr 610000 Stock Variation   100
       Cr 110100 Stock Valuation        100      ← 把滞留抹回 0
```

### 🔴 关键：**永久分录，没有任何自动红冲 / 预提**

```
reversed_entry_id  = （空）
reversal_move_ids  = （空）
```

**机制是【增量】：**
- `_get_last_closing_date()` 记住上次已过账的关账日
- `_save_closing_id()` 存最近 10 张关账凭证
- 下期只结算「**上次关账之后新产生的变动**」

> **每期一张永久增量分录 —— 不是「本期预提、下期冲回」。**
>
> 这一点很重要：如果它是预提+红冲，[B-14](#b-14) 的滞留会**每期复活**，永远抹不掉。
> **它不是。滞留被扫掉一次就没了。**

### 对方科目

见 [B-08](#b-08) 的取值链：估值科目上的 `account_stock_variation_id` → 退回
`company.expense_account_id` → **两者都空则静默跳过**。

---

<a name="b-30"></a>
## 7.4 · B-30 · 🔴 `real_time` 公司的自动关账 cron 永远不跑
### The auto-closing cron never fires for real_time companies

| | |
|---|---|
| **等级** | 🔴 **高危**（背离照样累积，而且**没人自动扫**） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### 两个正交的设置，别混 / Two independent settings

| 设置 | 取值 | 含义 |
|---|---|---|
| **`inventory_valuation`**（公司 / 品类 `property_valuation`） | `periodic` (at closing) / **`real_time`** (at invoicing) | 决定 **GL 从哪来**：期末关账 or 开票即入账 |
| **`inventory_period`** | `manual` / `daily` / `monthly` | 决定关账凭证**谁来点** |

- **Manual**：人去报表页点 Generate Entry
- **Daily**：cron `_cron_post_stock_valuation` **每天跑**
- **Monthly**：🔴 **只在【月末最后一天】跑**。源码 `periods = ['daily']`，
  只有 `today == 本月最后一天`（`relativedelta(day=31)` 自动取当月最后一天）才追加 `'monthly'`。
  **→ 月中手动触发 cron 也不动它。**

### 🔴 cron 的域 / The cron's domain

```
inventory_period in ('daily','monthly')   AND   inventory_valuation != 'real_time'
                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

> **→ 自动关账只对 `periodic` 公司生效。**
> **`real_time` 公司即便把 `inventory_period` 设成 monthly，cron 也不会跑** ——
> 只能手动点 Generate Entry（按钮本身照常可用）。

### 后果 / Consequence

Odoo 隐含假设了「`real_time` 公司天然没有背离」。**而本库已经证明它有**：
[B-14](#b-14) 价差滞留、已收未开票、已发未开票、[B-15](#b-15) 未配科目的盘亏、
[B-28](#b-28) 的手工改成本。

**→ `real_time` 公司拿到的是两头最差：背离照样累积，而且没有任何自动机制去扫。**

### 对策 / Mitigation

> **SOP 必须写死：每月末人工点一次 `Accounting → Review → Inventory Valuation → Generate Entry`。**
> **忘了 = 静默累积。**
>
> 但**点之前**必须先跑 [B-31](#b-31) 的清账顺序。

---

<a name="b-31"></a>
## 7.5 · B-31 · 🔴🔴 关账是一块橡皮擦，不是一台校正器
### Closing is an eraser, not a corrector

| | |
|---|---|
| **等级** | 🔴🔴 **最高危**（认知陷阱 + 不可逆的证据销毁） |
| **状态** | ✅ 实机验证 |

### 事实 / The fact

**Generate Entry 不问「这个差是怎么来的」。它只把数字抹平。**

它把**一切** L1（报表） vs L2（GL）的背离，**不加区分地**扫进同一个 Stock Variation 科目：

| 差的性质 | 例子 | 该不该被扫 |
|---|---|---|
| **正常时点差** | 已收未开票、已发未开票 | ✅ 本来就是它的职责 |
| **[B-14](#b-14) 价差滞留** | 账单晚于发货 + 涨价 | ⚠️ 该扫，但进的是 Stock Variation **不是 COGS** → **按 lot/按台的成本分解永久失真** |
| **盘亏 / 报废**（库位未配科目，[B-15](#b-15)） | 少了 10 台 | ⚠️ 本该单独进 Inventory Loss，现在混进来了 |
| **手工改成本**（[B-28](#b-28)） | Adjust Valuation / 改 lot cost | ⚠️ 混进来了 |
| 🔴 **结构性错误** | **退货未开贷记单**<br>**开票数量 ≠ 实物数量**<br>**删除已过账账单**（[B-02](#b-02)）<br>**超额开票**（[B-04](#b-04)） | ❌ **一旦扫进去，错误被「合法化」成一笔费用，永久失去线索** |

> **按下 Generate Entry 的那一刻，GL 和报表对上了 —— 但错误没有消失。**
> **它只是变成了一笔 Stock Variation。**

### 🔴 后果 / Consequence

**关账之后，所有成因的证据被压进同一个科目，再也分不开。**
[B-12](#b-12) 说的是「净额掩盖」；**本条说的是「关账销毁」—— 后者更彻底、且不可逆。**

### 对策 / Mitigation —— **顺序不能反**

```
1. 【关账之前】用数量勾稽把结构性错误逐条挑出来、补齐单据
       PO: 已过账开票数量 − 已收数量
       SO: 已过账开票数量 − 已发数量
   （⚠️ 必须用【已过账】口径 —— 原生的 qty_invoiced 含草稿账单，见 B-22）

2. 剩下的残差才是【真正该扫】的：
       时点差（会自愈）+ B-14 价差 + 已配科目的盘亏

3. 然后才按 Generate Entry
```

**反过来做就是毁灭证据。**

### 📌 Stock Variation 的余额是一个健康指标

配齐库位科目（[B-15](#b-15)）之后，盘亏/报废对期末差额**零贡献**。
于是 Stock Variation 里只剩时点差 + [B-14](#b-14) 价差。

> **一家干净的公司，Stock Variation 应该很小。**
> **它很大 = 有结构性问题 —— 而不是「盘点做多了」。**

---

<a name="b-32"></a>
## 7.6 · B-32 · 盘点的会计日期：`Accounting Date` 填了才倒填得动
### The inventory adjustment's Accounting Date is the only lever on the JE's period

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ **实机验证**（2026-07-14 修正） |
| **修订** | **原版说「锁期拦不住上月盘点」—— 不成立。防线是存在的，就是那个 `Accounting Date` 字段。** |

### 源码 / Source 📖

`stock_account/models/stock_move.py:205`：

```python
'date': self.env.context.get('force_period_date') or fields.Date.context_today(self),
```

**`force_period_date` 就是盘点单上的 `Accounting Date` 字段 —— 它有 UI 入口。**

### 实测 / Observed

| 盘点 | `account.move`（JE）日期 | `stock.move.date` |
|---|---|---|
| **填** `Accounting Date = 2026-05-15`（跨月） | **2026-05-15** ← **倒填生效** | **今天**（恒为 `now`） |
| **不填** | **今天**（`context_today`） | 今天 |

> **填了会计日期，跨月盘点能正确落到目标月，锁期也照常拦。**
> **真正的坑是【不填】—— JE 硬进当月。**

### 🔴 但 `stock.move.date` 不跟会计日期走

**`stock.move.date` 恒为 `now`，与 JE 的日期无关。**
→ 任何按 `stock.move.date` 做的时点分析（「5 月底的库存价值是多少」），
**会和 GL 差出一整个月**。两个日期字段不是同一个东西。

### ⚠️ 前提：库位必须配了科目

**只有库位配了 `valuation_account_id` 才有 move 级 JE**（[B-13](#b-13) [B-15](#b-15)）。
未配时，盘点根本不出 move 层分录，差异只在**期末关账**体现 ——
**那张凭证的日期 = 关账的 `at_date`（默认今天），`Accounting Date` 对它无效。**

### 修正记录 / Correction Log

| 日期 | 曾经的结论 | 为什么错 |
|---|---|---|
| **2026-07-14** | 「倒填日期的盘点必然记进本月；锁期拦不住」 | **`Accounting Date` 字段就是 `force_period_date` 的 UI 入口，倒填是生效的** |

---

<a name="b-33"></a>
## 7.7 · B-33 · 三个虚拟库位；报废库位靠 `min(id)` 抽签
### Three virtual locations — and the scrap location is picked by `min(id)`

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### 三个独立库位 / Three separate locations

```
stock.location_inventory        "Inventory adjustment"   usage = 'inventory'
stock.stock_location_scrapped   "Scrap"（若存在）         usage = 'inventory'
stock.location_production       "Production"             usage = 'production'   ← MRP 启用时存在
```

**配了一个 ≠ 配了其他。** 每一个都要单独设 `valuation_account_id`（[B-15](#b-15)）。
**Production 库位没配 → MRP 的消耗/产出 move 零分录，全靠期末关账扫。**

### 🔴 报废库位是「ID 抽签」，不是语义默认 📖

`stock/models/stock_scrap.py`：

```python
@api.depends('company_id')
def _compute_scrap_location_id(self):
    groups = self.env['stock.location']._read_group(
        [('company_id','in', self.company_id.ids), ('usage','=','inventory')],
        ['company_id'], ['id:min'])          # ← min(id)，不是按名字
```

> **报废库位 = 该公司 `usage='inventory'` 里 **ID 最小**的那个。**
> 新库里 `Inventory adjustment` 建得最早 → 中签。
> **→ 默认情况下，报废损失和盘亏损失落在【同一个科目】里。**

### 后果 / Consequence

**「报废率」这个管理指标，在默认配置下算不出来。** 且审计时无法解释科目余额的构成。

### 对策 / Mitigation

```
① 新建库位 "Scrap"，usage = 'inventory'（Location Type = Inventory Loss）
② 配独立的报废损失科目（如 400099 Scrap Loss）
③ 🔴 每次报废时【手动】改 scrap_location_id
      —— compute 只 depends('company_id')，且是 min(id)，没有任何配置钩子可挂
```

**这是配置决策，不是 bug。但必须有意识地做，而不是默认接受合流。**

---


---

## 7.8 · B-34 · ➡️ 见【场景 ② · 制造成本】

> **B-34(生产库位不配估值科目 → 整段 MO 零 GL)完整条目在本文件的 [场景 ② · 第一章](#b-34)。**
> **它与 [B-15](#b-15) 的报废/盘亏库位是【同一个开关】(库位 `valuation_account_id`)** —— 报废在本场景、制造在场景 ②,机制同源。

---

<a name="b-35"></a>
## 7.9 · B-35 · 🔴 关账凭证按【估值科目】聚合 —— 这是唯一的颗粒度杠杆
### The closing entry aggregates by *valuation account* — the only lever on granularity

| | |
|---|---|
| **等级** | 🔴（**决定了 [B-31](#b-31) 的橡皮擦能不能切细**） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### 实测 / Observed

**布局**：A1（值 30）、A2（值 20）挂估值科目 `110100`；B1（值 16）挂 `101000`。

```
Dr 110100                 50        ← A1 + A2 合并成【一对】，不是两行
   Cr 610000 Stock Variation   50
Dr 101000                 16        ← B1 单独一对
   Cr 610000 Stock Variation   16

凭证行名："Stock Variation Global for company"
```

**另一组（periodic 全库关账）：**

```
Dr 191000  (catA)                  50      ← 每个估值科目各占一行借方
Dr 101000  (catB)                  24
Dr 110100  (全库其余存货)     627,063
   Cr 610000 Stock Variation             627,137     ← 对方【一行汇总】
                                                       (= 50 + 24 + 627,063)

关账后：每个科目 GL == 报表实物估值，逐科目对平
```

### 规则 / The rule

| | |
|---|---|
| **借方** | **按估值科目拆行。** 把共用该科目的**所有产品**汇总成一个总数 —— **不是 per product，也不是 per 品类** |
| **贷方** | **一行汇总**（除非给不同估值科目配不同的 `account_stock_variation_id` —— 它是挂在**估值科目**上的） |
| **作用域** | **永远是全公司。** 报表页的品类/仓库筛选**只影响显示**（`_get_report_data` 的展示参数）；Generate Entry 按钮（`controller.js`）只把 `[公司, 日期]` 传给 `action_close_stock_valuation` |

> **→ 不能按产品/品类单独出凭证。**

### 🔴 杠杆 / The lever

> **想要「按品类」的颗粒度，唯一的办法是：给每个品类分派【不同的估值科目】。**
> 因为聚合是按科目分组的，那样每个品类自然各占一对借贷行。
> **想连变动科目也拆开 → 给每个估值科目配不同的 `account_stock_variation_id`。**

**这不能阻止 [B-31](#b-31) 销毁证据，但能把橡皮擦的【作用域切细】** ——
至少能知道 Ⅲ 类结构性错误集中在哪个品类。

**⚠️ 这是上线期的配置决策。补做代价很高**（要迁移历史科目余额）。

---


# 第八章 · 数量口径：哪些「已开票数量」不能信
## Chapter 8 · Quantity semantics — which "invoiced quantity" you cannot trust

> [B-13](#b-13) 证明了：**L1 与 L2 之间唯一的自由度是数量。**
> 于是「已开票数量」这个字段的口径，就成了整个数据完整性体系的地基。
> **本章两条说明：原生的那两个字段，一个都不能用。**

---

<a name="b-22"></a>
## 8.1 · B-22 · 🔴 `qty_invoiced` 包含草稿账单
### `qty_invoiced` counts draft bills

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | 📖 **源码确证**（Odoo 自己的注释即证据） |

### 事实 / The fact

`sale` 与 `purchase` 两侧的原生 `_prepare_qty_invoiced` 过滤条件都是：

```python
if inv_line.move_id.state not in ['cancel'] or inv_line.move_id.payment_state == 'invoicing_legacy':
```

**`state not in ['cancel']` → 草稿账单照单全收。**

而 v19 的 GL 分录**只在过账时产生**（[B-13](#b-13)）。

> **→ 一张躺在草稿里的账单，会把「已开票数量」刷满，而 GL 里一分存货都没有。**

**Odoo 自己的源码注释就是证据** —— `sale/models/sale_order_line.py::_compute_qty_invoiced_posted`：
*"for accounting purposes, we only want the quantities of the posted invoices"*

### 两侧不对称 / The asymmetry

| | 原生有没有「已过账」口径的字段 |
|---|---|
| **`sale.order.line`** | ✅ **`qty_invoiced_posted`**（`store=False`，`digits='Product Unit'`） |
| **`purchase.order.line`** | ❌ **没有任何 posted-only 字段 —— 必须自建** |

### 后果 / Consequence

- 任何用 `qty_invoiced` 做的数据完整性核对，**都会被草稿账单欺骗**
- 「货已发出、账单躺在草稿里三周」的 [B-14](#b-14) **酝酿态**，用 `qty_invoiced` 看不见

### 对策 / Mitigation

> **任何「已开票数量」的核对，口径必须是【已过账】。**
> SO 用原生 `qty_invoiced_posted`；**PO 必须自建**（镜像 `_prepare_qty_invoiced`，
> 把 `state not in ['cancel']` 换成 `state == 'posted'`，保留 UoM 转换和 in_refund 减号）。

---

<a name="b-23"></a>
## 8.2 · B-23 · 🔴 PO 的 `invoice_status` 公式里根本没有收货量
### The PO's `invoice_status` formula does not contain the received quantity at all

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | 📖 源码确证 |

### 事实 / The fact 📖

`purchase/models/purchase_order_line.py`：

```python
if line.product_id.purchase_method == 'purchase':
    line.qty_to_invoice = line.product_qty - line.qty_invoiced     # ← 订单量！
else:
    line.qty_to_invoice = line.qty_received - line.qty_invoiced
```

**`purchase_method == 'purchase'`（按订购数量开票）是很多产品的默认值。**
这一支里 **`qty_received` 根本不在公式中。**

### 🔴 判别性场景 / The killer case

```
订 100  /  实收 80  /  账单开 100
    qty_to_invoice = 100 − 100 = 0
    → invoice_status = 'invoiced'  →  界面显示绿色 "Fully Billed"
```

**而实际是【多开了 20】。** `invoice_status` 不是漏报 —— **它报反了。**

### 另外三个失效点 / Three more failure modes

| # | 问题 |
|---|---|
| ② | **含草稿账单**（[B-22](#b-22)）→ 绿色 "Fully Billed" 可以对应**零 GL** |
| ③ | **没有方向、没有「多开」状态**：多开 → `qty_to_invoice` 变负 → 非零 → `'to invoice'` = **"Waiting Bills"（叫你再开一张）**。退货未开贷记单也落在同一个标签上。**一个标签，三种相反含义** |
| ④ | **单头级，且 `'to invoice'` 就是正常在途态** —— 生产库里 95% 的活跃 PO 都是它，**零信号量** |

### SO 侧同理 / Same on the sales side

v19 只把 `_compute_amount_to_invoice`（金额 KPI）升级到了 `qty_invoiced_posted` 口径；
**驱动 `invoice_status` 的 `_compute_qty_to_invoice` 仍然用裸的 `qty_invoiced`** → 同样含草稿。

### 对策 / Mitigation

> **`invoice_status` 是一个采购管控字段，不是数据完整性字段。**
> **不要用它做任何 GL / 库存的一致性判断。**

---


# 第九章 · ORM 与模块开发陷阱（非会计）
## Chapter 9 · ORM and module-development pitfalls

---

<a name="b-24"></a>
## 9.1 · B-24 · 🔴 删除已对账的银行对账行 → 付款变孤儿
### Deleting a reconciled bank statement line orphans the payment

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | 📖 源码确证 |

### 事实 / The fact

`account.bank.statement.line.unlink()`（:430）走的是一条**残缺路径**：
**只删自己的 move、不撤 partial reconcile、不清 `payment_ids`。**

干净路径是 `action_undo_reconciliation()`（:460）—— **但原生不强制「先撤后删」。**

### 场景 / Scenario（先登记 payment、再用对账行匹配）

删除对账行后：只拆 partial B → Payment 被打回 `in_process`、partial A 原封不动
→ **发票仍显示已付款、付款凭证 JE 消失** —— 三者对不上，**永久无告警**。

### 原生唯一的护栏（不够用）

`_check_allow_unlink`（:478）只拦「从 valid + complete 的对账单里删行」。
**裸的已对账行放行。**

### 对策 / Mitigation

> **守卫的锚点必须是【对账状态】**（`payment_ids` 或 `matched_debit_ids` / `matched_credit_ids`），
> **与锁期无关。**

📌 相关：`account.bank.statement` 在 v19 **无 state 字段、无 `action_draft()`**
（v16 起降级为纯分组容器）。

---

<a name="b-25"></a>
## 9.2 · B-25 · `to_refund` 决定退货扣不扣 `qty_received` / `qty_delivered`
### `to_refund` decides whether a return reduces the received/delivered quantity

| | |
|---|---|
| **等级** | 🟡（暴露面很小，但一旦命中是全盲） |
| **状态** | 📖 源码确证 |

### 事实 / The fact

`to_refund`（UI 标签 *"Update quantities on SO/PO"*）定义在 **`stock_account`**，`default=True`。

`purchase_stock::_prepare_qty_received`：

```python
if not move.origin_returned_move_id or move.to_refund:
    total -= ...
```

> **`to_refund = False` 时：货退了，`qty_received` 不减 → 任何「开票量 vs 实物量」的
> 勾稽恒为 0 → 全盲。**

### ⚠️ 但实际暴露面很小

**源码核实：v19 的 `stock_account` 视图里 `to_refund` 出现 0 次，退货向导也没有这个字段
→ 正常 UI 里用户根本没有取消勾选的入口。**

实际暴露面只剩：**API / 数据导入 / Studio / 第三方模块塞 `default_to_refund=False`**。

### 对策 / Mitigation

ORM 级守卫（成本近零）值得加，**但别当卖点。**

---

<a name="b-26"></a>
## 9.3 · B-26 · 🔴 `parse_version` 剥尾零 → 补零升位 = 没升级 → migrations 静默不跑
### `parse_version` strips trailing zeros — a `.0` bump silently skips all migrations

| | |
|---|---|
| **等级** | 🔴（非会计，但会让整个数据迁移**静默失效**） |
| **状态** | ✅ 实机验证 + 📖 源码确证 |

### 事实 / The fact

```python
parse_version("19.0.6.0") == parse_version("19.0.6.0.0")   # → True（完全相同的 tuple，实测）
```

而 `MigrationManager.migrate_module` 的闸门是：

```python
parsed_installed_version < parse_version(full_version) <= current_version
#                        ^ 严格小于
```

### 🔴 后果 / Consequence

> **「补零升位」（`x.y.z.0` → `x.y.z.0.0`）在 Odoo 眼里等于【没升级】。**
> **`migrations/` 目录下的脚本静默不执行 —— 而模块本身、新增列、上架 Apps 全都不受影响。**
>
> 你会看到：模块升级成功、新字段出现了、**但迁移脚本一行没跑，老数据没被重算。**

### 核心结论 / Key takeaway

> **版本号在 Odoo 里唯一的功能性作用，就是决定 migrations 跑不跑。**
>
> **铁律：尾部补零不算升版本。要升就动非零位。**

---


# 附录 · Appendix

## A. GL 与库存报表分裂：**两类背离**
## A. GL-vs-stock divergence: two classes

> **2026-07-14 重构。** 原版的「五大成因 / 永久 vs 自愈」二分法**已作废** ——
> 它建立在「[B-14](#b-14) 是死账」这个错误认知上。
> **真相是：所有背离最终都会被期末关账扫平（[B-29](#b-29)）。区别不在【能不能扫】，
> 而在【扫掉之后，损失被归到哪个科目、还找不找得回来】。**

### 分类维度 = **扫进 Stock Variation 之后，还剩什么问题**

| 类 | 成因 | 条目 | 关账后 GL 总额 | 关账后**剩下的问题** |
|---|---|---|---|---|
| **Ⅰ · 时点差**<br>（设计特性） | 已收未开票（GRNI） | — | ✅ 正确 | **无** —— 下期账单一到就自愈 |
| | 已发货未开票 | — | ✅ 正确 | **无** |
| **Ⅱ · 分类错**<br>（总额对，归集错） | **账单晚于发货 + 价格变动** | [B-14](#b-14) [B-27](#b-27) | ✅ 正确 | 🔴 **按 lot / 按台的成本永久偏低**<br>（钱进了 Stock Variation，不带产品维度） |
| | 手工改成本 / Adjust Valuation | [B-28](#b-28) | ✅ 正确 | ⚠️ 同上 |
| | 盘亏 / 报废（**库位未配科目**） | [B-15](#b-15) | ✅ 正确 | ⚠️ **报废率算不出来** —— 混进 Stock Variation |
| | 混价 lot 部分出库 | [B-20](#b-20) | ✅ 正确 | **lot 耗尽即自愈** |
| **Ⅲ · 🔴 结构性错误**<br>（**关账 = 销毁证据**） | **删除已过账账单** | [B-02](#b-02) | ⚠️ 被"抹平" | 🔴🔴 **错误被合法化成一笔费用，线索永久消失** |
| | **超额开票（收 10 开 20）** | [B-04](#b-04) | ⚠️ 被"抹平" | 🔴🔴 同上 |
| | **退货未开贷记单** | — | ⚠️ 被"抹平" | 🔴🔴 同上 |
| | **开票数量 ≠ 实物数量** | [B-22](#b-22) [B-23](#b-23) | ⚠️ 被"抹平" | 🔴🔴 同上 |

### 🔴 唯一真正重要的那条线

> **Ⅰ / Ⅱ 类可以放心让关账去扫。**
> **Ⅲ 类【必须在关账之前】用【已过账口径】的数量勾稽逐条清掉。**
>
> **关账不会帮你区分它们。按下 Generate Entry 的那一刻，Ⅲ 类就变成了一笔
> 「库存变动费用」—— 你再也不知道那 50 万里有多少是真的损耗、多少是没开的贷记单。**
>
> → **[B-31](#b-31)**

### 数量勾稽的公式（Ⅲ 类的唯一探针）

```
PO 行：  已过账开票数量  −  qty_received
SO 行：  已过账开票数量  −  qty_delivered
                ↑
        ⚠️ 必须是【已过账】口径 —— 原生 qty_invoiced 含草稿账单（B-22）
        ⚠️ 不能用 invoice_status —— 它的公式里根本没有收货量（B-23）
```

**减号两边都是【数量】，其中一边直接来自 `stock.move`。**
**这不是「发票 vs 订单」的核对（那是采购管控），是「开票数量 vs 实物数量」的核对
（这是估值保护）。** 依据见 [B-13](#b-13) 的推论 ①：**数量是两本账之间唯一的自由度。**

### ⚠️ 净额会掩盖一切

**两个方向相反的错误会互相抵消**（[B-12](#b-12)、[B-14](#b-14) 双向）。
**生产库实证**：入库少记 575,126.32 vs 退货少减 536,767.65 → **净额仅 38,358.67，掩盖了 93%。**

> **gap 必须存【裸的带符号数】，永不 `abs()`、永不跨行相加。**

### 少开票（收 20 开 10）呢？

**普通 GRNI（Ⅰ 类），可自愈。** 实测（收 20 完全不开票）：`GL = {}` 完全无分录，
库存子账 = 2,000。**补开票即对齐。**

**⚠️ 与 [B-04](#b-04)（多开票）不对称**：多开票**直接虚增存货资产**且落进 Ⅲ 类；少开票只是滞后。

---

## B. 利润分析的四条路，没有一条能回答"这台机器赚了多少"
## B. Four native paths to margin — none answers "did this unit make money?"

| 路径 Path | 成本取自 Cost basis | 与总账勾稽 Ties to GL | 致命缺陷 Fatal flaw |
|---|---|---|---|
| **Sales → Margins**<br>(`sale_margin` + `sale_stock_margin`) | 发货前：产品 avg cost（估计）<br>发货后：**实发批次真实成本** ✅ | ⚠️ 数字对，但**无 lot / PO 维度** | 报价阶段不可信（[B-11](#b-11)）；<br>**晚启用则历史永久错**（[B-10](#b-10)）；<br>**无法按 lot / PO 归集** |
| **Accounting → Margin Analysis**<br>(`product_margin`) | 供应商账单价 × 数量 | ❌ | 算的是**采购额**，不是 COGS |
| **Analytic Accounts** | 人工打的标签 | ✅ | 要逐行打标签；不天然跟随 lot / PO |
| **Lot Valuation** | lot 真实成本 | ✅ | **无任何标准报表带 lot 维度**（[B-07](#b-07)） |

> **结论**：v19 的会计链路能算对每个 lot 的成本（[B-05](#b-05)），
> 但**没有任何标准报表把 lot 成本与收入放在同一张表上**。
> **成本数据是对的；缺的是把它和收入连起来的那个维度。**

**补充（2026-07-12）** —— 第 1 行 `Sales → Margins` 的一个属性值得单独记下：

**它覆盖销售订单上的全部货物**，不区分是否 lot 追踪、不区分库存来源。
配合 [B-11](#b-11)（发货后改写为实发批次真实成本），
**发货完成后的 SO 毛利，在 lot 估值下既 lot 精确、又覆盖完整。**

前提仍是 [B-10](#b-10)：**Margins 必须上线第一天启用。**

The native margin covers *every* line on the order, tracked or not. Post-delivery, under lot
valuation, it is both lot-accurate and complete — provided Margins was enabled from day one.
>
> **Conclusion**: v19's accounting chain computes the correct cost per lot. No standard report
> joins that cost to revenue. The data is right; the reporting dimension does not exist.

---

## C. 上线检查清单（从本库导出）
## C. Go-live checklist derived from this library

### 🔴 一级 · 配错了整个机制静默失效

| ✅ | 检查项 Check | 关联条目 |
|---|---|---|
| ☐ | **架构确认**：收一次货，确认 Journal Items **零分录** | [B-13](#b-13) |
| ☐ | 🔴 **Stock Variation 的对方科目已配**（估值科目上的 `account_stock_variation_id` **或** `company.expense_account_id`）—— **两者都空则 Generate Entry 静默无反应** | [B-08](#b-08) |
| ☐ | 🔴 Stock Variation 科目的 `account_type` 是**损益类**；建议 **`expense_direct_cost`**（落在 COGS 段内 → 聚合毛利正确） | [B-08](#b-08) [B-14](#b-14) |
| ☐ | 🔴 **虚拟库位的估值科目**：`Inventory adjustment` / `Scrap` / `Production` **逐个**配 `valuation_account_id`（Odoo **默认不配** → 盘亏/报废/制造全部零分录，混进 Stock Variation） | [B-15](#b-15) [B-33](#b-33) |
| ☐ | 🔴 **`real_time` 公司：自动关账 cron 永远不跑** → SOP 写死「每月末人工点 Generate Entry」 | [B-30](#b-30) |
| ☐ | 🔴 **关账之前必须先清 Ⅲ 类结构性错误** —— 按下 Generate Entry 就销毁证据 | [B-31](#b-31) [附录 A](#a-gl-与库存报表分裂两类背离) |
| ☐ | 🔴 **上线期决定估值科目的颗粒度** —— 关账凭证**按估值科目聚合**。想要按品类拆，唯一的办法是给每个品类配**不同的估值科目**（+ 不同的 `account_stock_variation_id`）。**补做代价极高** | [B-35](#b-35) |
| ☐ | 🔴 **若做制造**：整个制造成本域已拆出为独立文件 → **`odoo19_manufacturing_cost.md`（B-34、B-36 ~ B-45）**。<br>一句话预告：**生产库位不配估值科目 → 制造过程对总账完全静默；一配上，又冒出一个关账【不会】自动清掉的 WIP 差异。** | [B-34](#b-34) |

### 🔴 二级 · 操作纪律（配置救不了，只能靠 SOP）

| ✅ | 检查项 Check | 关联条目 |
|---|---|---|
| ☐ | 🔴 **开票顺序纪律**：供应商账单在**发货之前**过账 | [B-14](#b-14) [B-27](#b-27) |
| ☐ | 🔴 开票原则为**订单数量**的产品：开票与物理发货之间**不得发生任何改变该产品成本的事件**（收货 / LC / 账单重估 / 重估 / 盘盈） | [B-59](#b-59) |
| ☐ | 🔴 **每笔到货用独立 lot / serial 号**；收货作业类型的 `Use Existing ones` 关闭 | [B-20](#b-20) |
| ☐ | 🔴 **LC 必须在发货前分摊完毕**；月结检查有无事后补做的 LC | [B-17](#b-17) [B-57](#b-57) |
| ☐ | 🔴 月结跑一次 **LC 单据落差查询**：`account_move_id IS NULL` 的已验证 LC 条数 = 0 | [B-57](#b-57) |
| ☐ | 🔴 月结巡检 **存货类科目有无贷方余额**（撤销已重估账单的硬信号） | [B-58](#b-58) |
| ☐ | 🔴 修正已重估过的账单：**重开正确账单过账**，禁止转草稿/取消；红冲后仍须手工重估一次 | [B-58](#b-58) [B-03](#b-03) |
| ☐ | 🔴 已过账账单用**贷记单**冲销，**禁止 Reset to Draft 后删除** | [B-02](#b-02) |
| ☐ | 🔴 **盘点/报废菜单只给仓库管理员** —— 配了库位科目之后，一笔盘点调整会**直接、立刻写进损益表** | [B-15](#b-15) |
| ☐ | **Sales → Margins 必须上线第一天启用**（晚启用则历史永久错） | [B-10](#b-10) |
| ☐ | 按批次/单台核算成本 → **Valuation by Lot 已开启** | [B-18](#b-18) |
| ☐ | Bill Control = **Received quantities**（实物商品） | [B-04](#b-04) |
| ☐ | 已启用 **Storage Locations**（否则看不到 lot 级成本） | [B-06](#b-06) [B-07](#b-07) |
| ☐ | Standard 成本法：**价差科目已配**（AVCO/FIFO 无需配） | [B-16](#b-16) |
| ☐ | 期初库存用**清算科目法**，不用虚拟供应商 PO | — |

### 🟡 三级 · 团队认知（不知道就会误判）

| ✅ | 检查项 Check | 关联条目 |
|---|---|---|
| ☐ | 🔴 **`invoice_status` / `qty_invoiced` 不能用于任何数据完整性判断**（含草稿账单；PO 侧公式里根本没有收货量） | [B-22](#b-22) [B-23](#b-23) |
| ☐ | 🔴 **`lot.avg_cost` 不是成本**（lot 售罄即归零）；成本看 lot 表单的 **Cost**（`standard_price`） | [B-21](#b-21) |
| ☐ | 🔴 **Adjust Valuation / 改 lot cost / 改 standard price 全部 ⊥ GL** —— 不能用它们修 GL 差异 | [B-19](#b-19) [B-28](#b-28) |
| ☐ | **货转固资只能用「库位科目法」**；资产对象需**手动** Create Asset | [B-19](#b-19) |
| ☐ | **Stock Valuation 报表的 Unit Cost 是产品级口径**，不是 lot 成本 | [B-06](#b-06) |
| ☐ | 月结若某颗 lot 混价且未发完 → 110100 与库存报表**本来就不平**，别当成账错 | [B-20](#b-20) |
| ☐ | 月结时**拆解** Stock Variation 到 **Ⅰ / Ⅱ / Ⅲ 三类**，不只看净额 | [B-12](#b-12) [附录 A](#a-gl-与库存报表分裂两类背离) |
| ☐ | 若有寄售业务：已确认**异常在开票端**（仓库侧干净） | [B-09](#b-09) |
| ☐ | 盘点/报废**必须填 `Accounting Date`**，否则 JE 硬进当月；且 **`stock.move.date` 恒为今天，不跟会计日期走** | [B-32](#b-32) |
| ☐ | **`monthly` cron 只在月末最后一天跑**；`real_time` 公司**一律跳过** | [B-30](#b-30) |
| ☐ | 模块开发：**尾部补零不算升版本** → migrations 静默不跑 | [B-26](#b-26) |

---

---
---

# 场景 ② · 制造成本
## Scenario ② · Manufacturing cost

# 第一章 · 制造过程什么时候进 GL
## Chapter 1 · When manufacturing actually books

> 制造在 v19 的 GL 里,走的是 **B-13 的门② —— 库位科目**。
> 而 Odoo **默认一个虚拟库位都不配科目**。
>
> ## **所以默认情况下,制造过程在总账上不存在。这不是 bug,是没配。**
>
> Manufacturing reaches the GL through **door ② — the location account**. Odoo configures none of
> the virtual locations by default. **So by default, manufacturing does not exist in the GL.**

---

<a name="b-34"></a>
## 1.1 · B-34 · 🔴 生产库位不配估值科目 → 整段 MO 零 GL

### Without a production location account, the entire MO posts nothing

| | |
|---|---|
| **等级** | 🔴(对制造业:**整个生产过程在总账上不存在**) |
| **状态** | ✅ 已实机验证(2026-07-14 重测)· 📖 已源码确证 |
| **来源** | 从 `odoo19_verified_behaviours.md` 迁入,**ID 不变** |

### 实测 / Observed —— 生产库位**不配**科目,`real_time` 成品

```
RAW  移动:   state = done   |  qty = 2   |  value = 100  |  account_move?  False
成品 移动:                                 |  value = 125  |  account_move?  False
人工 JE:     0 条
110100 库存科目 GL:  0        191000 生产库位 GL:  0
```

**两点确认:**

1. **料件这次是【真的】被消耗了**(qty 2,value 100)——「料件缺席」是旧测试脚本的漏洞,已修正(见下方修正记录)
2. **生产库位不配估值科目 → 整段 MO 零 GL**:**料件消耗、成品完工、人工,全部 `account_move = False`,一分钱不进总账。**

### 🔴 而且这是 Odoo 的【默认状态】

**生产库位默认不配估值科目。**

> ## **开箱即用时,制造过程对总账【完全静默】。**
> ## **`real_time` 产品也一样不出 GL** —— 上面的测试里,成品完工后 110100 **仍然是 0**。

**价值只活在报表 / 估值侧:** 成品的 `standard_price` / move `value` 全都算对了,**但总账上什么都没发生。**

### 机制 / Mechanism 📖

生产库位默认 `valuation_account_id = None` → **B-13 的门② 关闭** → 两条 move 都不出分录。

> **raw → finished 的成本换算,只发生在【估值层 L1】。GL(L2)一分不动。**

**🔑 这与 B-15(报废/盘亏)是【同一个开关】。** 三个虚拟库位,一条规则,不用分开记。

### 后果 / Consequence

一家上了 Odoo Manufacturing 的公司,可能以为自己有了完整的制造成本核算。
**实际上他们的总账里,生产车间是个黑洞** —— 存货科目的余额从原料**直接跳到**成品,**WIP 从来没有存在过。**

**而月末关账会把这个缺口扫掉,没有任何人会发现。**

### 对策 / Mitigation

- 要让制造进 GL → **必须显式给生产库位配 `valuation_account_id`**(UI 标签 = **Cost of Production**)
- ⚠️ **一旦配了,又会冒出一个【关账不会帮你清掉】的 WIP 差异** → [B-44](#b-44) [B-45](#b-45)
- **这是一个「配也不是、不配也不是」的局面。两边都需要人管。**

### ⚠️ 修正记录 / Correction Log

> **2026-07-14 · 原实测证据作废,结论重测确认。**
>
> **原证据**(「制造 5 个成品、耗 10 个 RAW @ 7 → GL 零分录」)**是【非判别性】的:**
> 那一轮测试里 **RAW move 状态 = `cancel`,qty = 0 —— 料件根本没有被消耗。**
> 测试脚本只设了 `qty_producing` 就 `mark_done`,**漏了 `action_assign()` 预留 + 设消耗数量。**
>
> **料件根本没动 → 「零分录」是【必然的】,不管配没配科目。**
> **这组数据在两个假设下会给出【相同结果】→ 不能用来验证任何假设。**
>
> **本次已用【料件真的被消耗】的 MO 重测(`action_assign()` + `move_raw.quantity=2, picked=True`)→ 结论成立,证据现在是干净的。**

> **2026-07-14 · 表述修正。**
>
> ~~原文:「唯一的例外是 `account_production_wip_account_id`」~~
>
> **实测确证的开关是【生产库位的 `valuation_account_id`】。**
> 本文件所有实测(B-34 / B-36 / B-38 / B-44)用的都是这个字段。

> **2026-07-14 · T-04 闭合 —— `account_production_wip_account_id` 【是】一条独立机制,但性质完全不同。**
>
> | | 生产库位 `valuation_account_id` | `account_production_wip_account_id` |
> |---|---|---|
> | **性质** | **自动开关** —— 配了,MO 的料工费移动就实时出分录 | 🔴 **手工向导** —— 「**预提 + 次日红冲**」 |
> | **触发** | `_should_create_account_move`(门②) | **人去点** |
> | **产出** | 永久分录,跟着 move 走 | **预提凭证 + 自动红冲**(与库存移动无关) |
>
> **→ 两条【互不相干】的机制。**
> **→ 想在总账上看到【真的在制品】,只能靠这个手工向导** —— 因为库位科目**根本抓不到跨期 WIP**([B-46](#b-46))。
> **→ 原 B-34 的表述引用它不算错,但把它讲成了「开关」,性质讲错了。**

---

<a name="b-36"></a>
## 1.2 · B-36 · 🔴 工时成本进 GL 的三个必要条件

### Three necessary conditions for labour cost to reach the GL

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证 · 📖 已源码确证 |
| **源码** | `mrp_account` → `_post_labour` |

### 🎯 三个条件 / The three conditions

**三个必须【同时】满足。缺任何一条 → 一条分录都不出,静默无告警。**

| # | 条件 | 在哪配 |
|---|---|---|
| **1** | **成品的品类估值 = `real_time`**(实时 / 自动) | 产品类别 → Inventory Valuation |
| **2** | **生产库位配了 `valuation_account_id`** | Inventory → Configuration → Locations → **Virtual/Production** → **Cost of Production** |
| **3** | **工时成本 ≠ 0**(`costs_hour` × `duration`) | 工作中心 → Cost per hour |

### 实测结果 / Observed —— 三场景对照

| 场景 | 生产库位配估值科目? | 人工 GL 凭证 | 分析行 |
|---|---|---|---|
| **A** | ❌ 无 | **0 条** | 0 |
| **B** | ✅ 有(191000) | **1 条,已过账** | 0 |
| **C** | ❌ 无(但工作中心配了分析分摊) | **0 条** | **1 条,−30** |

**B 场景实际过账的凭证:**

```
JE MISC/2026/07/0001    ref "WH/MO/xxxx - Labour"    posted
    Dr  191000  生产库位估值科目      30
    Cr  600000  人工 / 费用科目             30
```

**含义:把人工从费用科目(600000,工资原本记这里)【资本化】进生产 / WIP 资产。**
再叠加完工入库那一笔(`Dr 库存 110100 / Cr 生产 191000`,含人工)——

> **净效果 = 人工从 P&L 挪进了成品存货资产。**

### 🔴 关键:三个场景里,**报表侧的估值都一样**

```
成品 standard_price  /  完工移动 value   ← 三个场景全都吃进了人工 30
```

> ## **报表估值侧【无条件】包含工时成本。差别只在 GL 和分析账。**

**所以场景 A 里,成品在库存估值报表里值 130,在总账里值 0**([B-34](#b-34))。

### 对方科目 / The counterpart

```
工作中心.expense_account_id
    ↓ 没配则回落到
成品品类的费用科目
```

---

<a name="b-37"></a>
## 1.3 · B-37 · GL 路径 ⊥ 分析路径

### The GL path and the analytic path are orthogonal

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 已实机验证 |

### 事实 / The fact

| 路径 | 触发条件 | 产出 | 性质 |
|---|---|---|---|
| **GL(总账)路径** | [B-36](#b-36) 的**三个条件全部**满足 | `account.move`(Labour 凭证) | **财务账** |
| **分析(analytic)路径** | 工作中心配了 `analytic_distribution` | `account.analytic.line` | **管理会计 / 成本分析** |

> ## **分析路径【不进总账】,而且【与生产库位科目完全无关】。**
> ## **即使 GL 一条分录都不出,分析行照跑。**
>
> (场景 C 实证:GL = **0 条**,分析行 = **1 条 −30**)

### ⚠️ 企业版 HR 模块的陷阱

`mrp_workorder_hr_account` 按**员工**记工时成本。

> **它只生成分析账(`account.analytic.line`),不进总账。**
> **想让员工人工成本进 GL,还是得走工作中心 `costs_hour` 这条路。**

### 对策 / Mitigation

| 你想要什么 | 配什么 |
|---|---|
| 人工/机器工时**进总账**做 WIP 资本化 | 品类 `real_time` + **生产库位估值科目** + 工作中心 `costs_hour`(及 `expense_account_id`) |
| 只做**成本分析**、不动总账 | 只配工作中心的**分析分摊** |
| **两个都要** | 两套都配 —— 它们互不干扰 |

---
---

# 第二章 · 成本法在 MRP 里的行为
## Chapter 2 · How the cost method behaves inside MRP

---

<a name="b-38"></a>
## 2.1 · B-38 · 🔴 Standard 在 MRP 里是硬约束;差额滞留 WIP 估值科目

### Standard cost is a hard constraint in MRP; the variance strands in the WIP account

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证(隔离生产库位) |

### 测试 / Test

```
成品:      cost_method = standard,standard_price = 125
BoM:       2 × RAW(standard 50)                    → 标准料件 100
工作中心:   costs_hour = 30,duration = 1h            → 标准工时  30
                                                    ─────────────
实际投入 = 130                          标准成品价 = 125       差 +5
```

### 实测结果 / Observed —— 生产库位估值科目的完整三笔

| 事件 | 分录 | 说明 |
|---|---|---|
| **料件消耗** | `Dr 生产库位 100` | 2 × standard 50,**按标准出库** |
| **人工资本化** | `Dr 生产库位 30` | 1h × 30 |
| **成品完工** | `Cr 生产库位 125` | 成品按 **standard 125** 入库,**不是实际 130** |
| | **净额 = 100 + 30 − 125 = `+5` 借方** | 🔴 **不归零** |

**对照证据 / Corroborating:**

| 检查项 | 值 | 说明 |
|---|---|---|
| 完工 move 的 `value` | **125** | 标准,不是实际 130 |
| 成品 `standard_price`(MO 之后) | **125** | **没有被改写** |
| 料件 consumed 的 `value` | **100** | 料件按标准出库 |

### 🎯 根因 / Root cause 📖 —— `mrp_account` · `_cal_price`

```
AVCO / FIFO  →  成品价 = 料 + 工 + 额外 = 【实际】
                → 料工费【全额】转进成品 → 生产库位进出相等 → 归零

Standard     →  price_unit = standard_price  之后【提前 return】
                → 料工费实际与标准的差额【没人接】→ 只能滞留 WIP
```

> ## **不是 Odoo 忘了处理差异。是那条代码路径【根本没走到】处理差异的地方。**

### 实测结果 ② / Observed —— 多单累积:**线性滚大,永不自清**

```
prod-loc 151000 起点:  0
    MO #1  →   5
    MO #2  →  10
    MO #3  →  15
    MO #4  →  20
    MO #5  →  25
                        5 单后 = 25 = 5 × 5      ← 一单一单线性累积
```

> ## 🔴 **每张 MO 的 `+5` 一单不落地全堆在 WIP 科目。**
> ## **关账不扫它([B-44](#b-44)) → 这个数【只增不减】。**
>
> **一个月几百单就是几千的【虚增 WIP 资产】。**
> **不做期末差异结转 → 资产负债表上的在制品科目会挂着一堆【幽灵价值】。**

### 核心结论 / Key takeaway

> ## **Standard 在 v19 MRP 里【完全生效】:成品恒等于标准价。**
>
> **实际投入(料 100 + 工 30 = 130)与标准(125)之间的 `+5`,滞留在【生产库位估值科目】上。**
>
> **这就是教科书里的【制造成本差异 / manufacturing cost variance】** ——
> **WIP 科目上的「标准 vs 实际」差额。**

### 🔴 这个 `+5` 的性质与清理

- **不会在完工时自动归零**,也**不进成品**(成品永远是标准价)
- **🔴 月末关账【也不会】清掉它** → [B-44](#b-44)
- **必须【人工】期末结转**到差异科目或 COGS

> **跟 [B-43](#b-43) 里机器折旧那个残差是【同一类东西】:**
> **Odoo 只负责按标准 / 按率记账。差异挂在中转科目上,要你自己认损益或结转。**

### ⚠️ 修正记录 / Correction Log

> **2026-07-14** — 本条最初几轮 MRP 测试的**结果作废**(料件根本没被消耗,`action_assign()` 缺失)。
> 详见 [B-34 的修正记录](#b-34)。**人工/机器的结论不受影响**(它们不依赖料件),
> **但「料件进不进、进多少」这条,以本条为准。**

---

<a name="b-39"></a>
## 2.2 · B-39 · 🔴 生产库位科目 = 【纯差异科目】；余额行为随成本法变

### The production location account is a pure variance account

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ **三种成本法全部实测**（AVCO / FIFO / Standard）· 📖 已源码确证 |
| **源码** | `mrp_account` → `_cal_price` |

### 🎯 一句话 / In one line

> ## **AVCO / FIFO 是「完工即平」。Standard 是「完工留差」。**

### 实测 ① / Observed —— AVCO 与 FIFO：**每张 MO 完工即归零**

```
RAW 收货 100 @ 50（FIFO 层，value 5000）
    MO #1  |  料消耗 100  |  成品 value = 130（实际）  |  prod-loc = 0
    MO #2  |  料消耗 100  |  成品 value = 130          |  prod-loc = 0
    MO #3  |  料消耗 100  |  成品 value = 130          |  prod-loc = 0
                                                    3 单后 = 0
```

**每张 MO 在该科目上的三笔：**

```
    Dr  <prod-loc>   100      (料件消耗)
    Cr  <prod-loc>   130      (成品按【实际】130 入库，不是标准)
    Dr  <prod-loc>    30      (人工资本化)
    ─────────────────
    净 = 100 − 130 + 30 = 0          ← 自动归零，零残差
```

**FIFO 走的是和 AVCO 完全相同的分支**（`_cal_price` 里 `cost_method in ('fifo','average')`）。

### 实测 ② / Observed —— Standard：**`+5` / 单，线性累积**（见 [B-38](#b-38)）

### 🎯 根因 / Root cause 📖 —— `_cal_price`

```
AVCO / FIFO  →  成品价 = 料 + 工 + 额外 = 【实际】
                → 料工费全额转进成品 → 生产库位进出相等 → 归零

Standard     →  price_unit = standard_price 之后【提前 return】
                → 料工费实际与标准的差额【没人接】→ 只能滞留 WIP
```

> ## **只有 Standard 会留差异。不是 Odoo 忘了处理 —— 是那条代码路径【根本没走到】处理差异的地方。**

### 🔴 关键事实：这个科目里【只有差异，没有真 WIP】

**[T-01 实测](#b-46)：单步制造下，料件消耗与完工是【原子】的。**
**`button_mark_done` 之前，`move_raw` 一直停在 `assigned`（预留），`value = 0`，零分录。**

> ## **「已领料未完工」这个会计状态，在 Odoo 里【根本不存在】。**
>
> **两步制造也一样：预生产库位 `usage = internal` → 库存→预生产是【内部调拨】
> （既非 `is_out` 也非 `is_in`）→ 不计价 → 即使挂了估值科目也【零分录】。**

**→ 所以这个科目是一个【纯差异容器】。它不需要承载资产。**

### 对照 / Side by side

| 成本法 | 成品估值 | 生产库位净额 | **期末要不要人管** |
|---|---|---|---|
| **AVCO** | **实际 130** | **每单归零** | ❌ **不用** |
| **FIFO** | **实际 130** | **每单归零** | ❌ **不用** |
| **Standard** | **标准 125** | **`+5` / 单，累积** | ✅ **必须处理** |

### 🎯 `account_type` —— **配 `expense_direct_cost`，并把它【当成差异科目命名】**

| 成本法 | 余额 | 配 `expense_direct_cost` 的效果 |
|---|---|---|
| **AVCO / FIFO** | 恒 0 | **损益表上是 0 → 无害** |
| **Standard** | 累积差异 | ✅ **差异【天然落在 COGS 段内】的一个专门命名的科目里** |

> ## **建议：把生产库位科目【本身】命名为 `Manufacturing Cost Variance`，类型 `expense_direct_cost`。**
>
> **→ 差异自动可见、可分析、落在毛利线之内。**
> **→ 【零手工分录】。月结 SOP 里那一步直接消失。**
>
> **不需要「一个 WIP 资产科目 + 一个差异损益科目」两个 —— 因为这个科目里【没有真 WIP】。**

### 备选：配 `asset_current` + 月结手工结转

**如果出于会计政策必须让它留在资产负债表上：**

```
月末：  Dr  制造成本差异 (P&L)      Cr  生产库位科目 (WIP)     ← 不利差异（实际 > 标准）
        Dr  生产库位科目            Cr  制造成本差异           ← 有利差异（反向）
金额 =  生产库位科目【当前余额】（因为它【全部】是差异）
```

**实测：3 张 Standard MO 后 WIP = 15 → 结转 `Dr COGS 15 / Cr WIP 15` → WIP 归零 ✅，差异进损益 ✅。**

**但这条路要多一步人工分录，而它买到的东西是零。**

### ⚠️ 修正记录 / Correction Log

> **2026-07-14（下午）· 原建议恢复。中间那次「修正」是【倒退】。**
>
> 曾一度改成「一律 `asset_current` + 手工结转」，理由是「这个科目同时装着真 WIP 和差异」。
>
> 🔴 **那个理由是【凭空发明的】。** T-01 实测证明：**跨期 WIP 根本进不了这个科目**
> （单步原子；两步是内部调拨，不计价）。
>
> **失败模式：用一个【未验证的推论】，去作废一个【已验证的结论】。**
> **这比推理不足更糟 —— 它是纯粹的倒退。**

---

<a name="b-40"></a>
## 2.3 · B-40 · `periodic`:MO 时零 GL,价值流月末才被扫进 GL

### Under periodic, the MO posts nothing; value flows only at close

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 已实机验证 |

### 实测 / Observed —— MO 完成时

```
人工 JE          = 0 条        ← real_time 的 _post_labour 不触发(B-36 条件 1 不满足)
库存科目 GL       = 0          ← periodic 全程不出 GL
```

### 实测 / Observed —— 月末关账(`action_close_stock_valuation`)之后

**关账凭证包含【两个不同的组件】,别混:**

| 组件 | 分录 | 说明 |
|---|---|---|
| **① Stock Variation 扫平** | `Dr 库存科目 / Cr Stock Variation` | 报表 vs GL 的**存货科目**背离(B-31 那台橡皮擦) |
| **② 库位重分类**<br>*"Closing: Location Reclassification"* | `Cr 生产库位科目` | 🔴 **只处理 `periodic` 产品** → [B-45](#b-45) |

### 核心结论 / Key takeaway

> **`periodic` 模式下,制造成本在 MO 时【只进报表估值】(不碰总账)。**
> **月末关账时才被搬进 GL。**

**这与料件、盘亏的结论一致 —— periodic 平时 GL 全静默,全靠期末一次性扫平。**

### 后果 / Consequence

**总额对,分类错。** 属于附录 A 的 **Ⅱ 类(分类错)**:

> **人工成本和料件成本、和盘亏、和一切别的东西,全部混在同一个 Stock Variation 里。**
> **你永远拆不出「这个月的人工成本是多少」。**

**而且 —— periodic 的库位重分类【并不完整】,它抓不到人工。** → [B-45](#b-45)

---
---

# 第三章 · 人工与机器:制造费用吸收
## Chapter 3 · Labour and machine — overhead absorption

---

<a name="b-41"></a>
## 3.1 · B-41 · 拆科目 = 拆工作中心

### To split accounts, split work centers

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 已实机验证 |

### 事实 / The fact

**社区版的工作中心只有:单一 `costs_hour` + 单一 `expense_account_id`。**

> **所以要把人工和机器记到不同科目,唯一的办法是【建两个工作中心】,各配各的费用科目,BoM 上各挂一道工序。**

### 实测 / Observed(`real_time` + 生产库位配了科目)

```
人工 JE:
    Cr  600000  Expenses            30      ← WC-LABOUR    0.5h × 60
    Cr  620000  折旧费用(机器)       90      ← WC-MACHINE   1.0h × 90
    Dr  191000  生产库位估值        120      ← 汇总资本化进 WIP / 成品
```

**两个工作中心 → 两条独立的贷方行。**
`_post_labour` 按 `workcenter_id.expense_account_id` **分组**,机器和人工干净落到不同科目。

### 多台机器 / Multiple machines —— GL 按工作中心自动拆

```
机器 JE:
    Cr  620001  折旧费用(机器 A)     90     ← 1h × 90
    Cr  620000  折旧费用(机器 B)    100     ← 2h × 50
    Dr  191000  生产库位估值(汇总)  190
```

**贷方一台一行,借方汇总进 WIP。**

### 配方 / The recipe

> ## **一台设备 = 一个工作中心 = 一个费用科目。**

---

<a name="b-42"></a>
## 3.2 · B-42 · 🔴 `costs_hour` 是一个【预定制造费用吸收率】

### `costs_hour` is a predetermined overhead absorption rate

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证 |

### 🎯 事实:机器折旧进成本,是【两套系统靠科目对接】,没有自动联动

| 系统 | 分录 |
|---|---|
| **`account_asset`(资产折旧)** | 机器作为固定资产,每月自动过账<br>`Dr 折旧费用(620000) / Cr 累计折旧` ← **折旧先进 P&L** |
| **工作中心 `costs_hour`(工时资本化)** | 把 WC-MACHINE 的 `expense_account_id` **指向同一个折旧费用科目 620000**<br>做 MO 时:`Dr 生产库位/WIP(191000) / Cr 折旧费用(620000)` |

> ## **正好把折旧费用从 P&L 冲出来、资本化进成品存货。**
>
> **净效果:实际用于生产的机器工时对应的那部分折旧,被摊进成品成本(存货);闲置产能的折旧,留在 P&L。**
>
> **这正是【制造费用吸收 / overhead absorption】那套会计。**

### 🔴 最坑的一点 / The trap

> ## **Odoo 【不会】从 `account_asset` 的折旧额自动倒算 `costs_hour`。**
> ## **这个率纯手工填。**

**要自己算:**

```
机器 costs_hour  =  月折旧额  ÷  该机器月预计有效生产工时
```

### 后果 / Consequence

**填错 = 长期、系统性地把存货成本记高或记低。**

**失败签名与 B-14 完全一致:**

- **配低了** → 存货成本偏低 → **按台毛利虚高** → **你以为赚了**
- **没有报错、没有告警**
- **月度损益的总额永远是对的**(少吸收的部分留在 P&L)
- **只有【按台成本】是错的,而且没有对手方会来抱怨**

### 对策 / Mitigation

- 🔴 **`costs_hour` 需要一个【定期复核的 SOP】**(建议每季度:设备月折旧 ÷ 预计有效工时,重算)
- **不做这件事,这个率就会一直是上线那天拍脑袋填的那个数。**

---

<a name="b-43"></a>
## 3.3 · B-43 · 🔴 吸收差异 ⊥ 库存关账

### The absorption variance is untouched by the inventory close

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证 |

### 场景 / Scenario

```
实际月折旧  = 100
MO 按 costs_hour 只吸收 = 90  (1h × 90)          → 少吸收 10
```

### 实测 / Observed —— 三步

**① `account_asset` 月折旧:**
```
    Dr  620001  折旧费用     100
    Cr          累计折旧            100
→ 620001 余额 = 100 借方  (费用在 P&L)
```

**② MO 机器工时资本化:**
```
    Dr  191000  生产库位估值  90
    Cr  620001  折旧费用            90
→ 620001 余额 = 100 − 90 = 10 借方     ← 少吸收 10
→ 110100 成品存货 GL = 90              ← 机器成本进了存货
```

**③ 跑月末库存关账:**
```
关账凭证涉及科目  =  ['110100', '191000', '610000']
620001 在关账里吗?  =  False              ← 🔴 关账根本不碰它
620001 最终余额    =  10                  ← 残差原封不动留在 P&L
```

### 🎯 核心结论 / Key takeaway

> ## **库存关账只对平【存货类科目】。**
> ## **对折旧费用 / 制造费用科目,一概不碰。**

**`costs_hour` 就是一个预定制造费用吸收率。费用科目(620001)同时扮演两个角色:**

| 角色 | 方向 |
|---|---|
| **费用归集** | 实际折旧 → **借方累加**(100) |
| **已吸收** | MO 吸收 → **贷方冲减**(90) |
| **残差** | **= 少吸收 / 多吸收的制造费用差异(under/over-applied overhead)**<br>🔴 **永远留在这个费用科目上** |

### 三种情形 / Three cases

| 情形 | `costs_hour` 设置 | 620001 残差 | 含义 |
|---|---|---|---|
| **吸收不足** | 率偏低(90 < 100) | **借方 +10** | 存货成本偏低,10 留 P&L 当期费用 |
| **吸收过度** | 率偏高(120 > 100) | **贷方 −20** | 存货成本偏高,**P&L 出现负费用(虚减成本)** |
| **刚好** | 率 = 实际 ÷ 有效工时 | **0** | 折旧全额资本化进存货 |

### 怎么调平 / How to clear it —— 三选一,**都要人管**

| # | 做法 | 适用 |
|---|---|---|
| **1** | **当期认了** —— 把它当制造费用差异,留在 P&L | **最省事,金额小就这么办** |
| **2** | **调率** —— 下月修 `costs_hour` = 月折旧 ÷ 预计有效机器工时 | 长期正解 |
| **3** | **手工结转** —— 期末做一笔 JE,把残差从 620001 转到 COGS | 要求差异全进当期销货成本时 |

### ⚠️ 修正记录 / Correction Log

> **2026-07-14 · 原推论作废。**
>
> ~~「配高了 → 多提的部分月末关账时又被 Stock Variation 调回」~~
>
> **错。** 本条实测证明:**关账凭证根本不碰费用科目**(`620001 在关账里吗 = False`)。
> **吸收过度的部分,也【原封不动】留在 P&L(作为贷方余额 / 负费用)。**
>
> **根因:关账的作用域是【估值科目】(B-35)。费用科目不是估值科目,不在作用域内。**

---
---

# 第四章 · 🔴🔴 关账与 WIP:那台橡皮擦【够不着】这里
## Chapter 4 · The close cannot reach the WIP account

> **B-31 说:关账是一块橡皮擦,它不认对错,把一切背离扫进 Stock Variation。**
>
> ## **本章的发现是:【那台橡皮擦够不着 WIP】。**
>
> **这不是好消息。它意味着 WIP 科目上的差异【永远不会消失,也永远不会被人注意到】——**
> **它只会静静地逐月累积,直到某天有人问「这个科目里的 80 万是什么」。**

---

<a name="b-44"></a>
## 4.1 · B-44 · 🔴🔴 关账【不扫】`real_time` 的 WIP 标准差异

### The close never touches the real_time WIP variance — excluded by design

| | |
|---|---|
| **等级** | 🔴🔴 |
| **状态** | ✅ 已实机验证(**全新隔离生产库位**)· 📖 已源码确证 |
| **源码** | `res_company.py:184-186` → `_get_location_valuation_vals` |

### 实测 / Observed

```
real_time  Standard  MO 后:    151000 = +5
点 Generate Entry(关账):      关账凭证碰 151000 的行数 = 0
关账后:                        151000 = +5        ← 🔴 纹丝不动
```

### 🎯 根因 / Root cause 📖

```python
# res_company.py:184-186   _get_location_valuation_vals
('product_id.valuation', '=', 'periodic')
```

> ## **关账的「库位重分类」组件,只处理 `periodic` 产品。**
>
> **`real_time`(永续)产品的料工费,在【移动发生时】就已经实时进了 GL。**
> **所以关账【定义上】就把它排除在外 —— 不是漏了,是设计。**

### 🔴 结论 / Consequence

> ## **`real_time` + Standard 成本法的 `+5` 标准差异,【永久滞留】在生产库位(WIP)估值科目上。**
> ## **关账不管、不会自清。**

**必须【人工】做期末差异结转分录。**

### ⚠️ 修正记录 —— 我预测错了 / I got this wrong

> **原预测(2026-07-14 上午):「关账会把 `+5` 扫进 Stock Variation」。**
>
> **推理链:** 191000 是估值科目 → B-35 说关账按估值科目聚合 → **而且 191000 出现在
> [B-43](#b-43) 测试的关账凭证科目列表里** → 所以它在作用域内。
>
> **🔴 错在第三环:** 那个科目列表来自**被 62 万存货污染的共享 dev 库**。
> **191000 出现在那里,完全可以是【别的 periodic 产品】带进来的。**
>
> **这正是「非判别性证据」的又一次现形** —— 而且是在**同一个测试者已经明确声明
> 「这个库隔离不出来,我不瞎报」之后**,把他拒绝采信的输出捡起来当证据用。
>
> **教训:被污染的输出,不能拿来当【任何】假设的支持证据 —— 哪怕只是当一条旁证。**

---

<a name="b-45"></a>
## 4.2 · B-45 · 🔴 `periodic` 的「库位重分类」只抓【料件价值流】

### Periodic's location reclassification only captures the material flow

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证 |

### 实测 / Observed

```
periodic  Standard  MO 后:     151000 GL = 0          ← periodic 移动时不出 GL

关账后:    Cr 151000    25      ← 凭证行标签 "Closing: Location Reclassification"
           151000 = −25
```

### 机制 / Mechanism

**`periodic` 产品【确实】被关账的库位重分类抓到了。但它只反映【料件价值流】:**

```
    料件进  100
    成品出  125
    ─────────────
    净额    −25        ← 这是【生产增值】
```

> ## 🔴 **而人工那 30,【根本没进】。**
>
> **人工 JE 只对 `real_time` 触发**([B-36](#b-36) 条件 1)。
> **`periodic` 下,人工成本从头到尾没有任何一条 GL 分录 —— 关账也不管它。**

**结果:生产库位又留下一个 `−25` 残差。**

### 🎯 两种模式,殊途同归 / Both roads lead to the same place

> ## **生产库位 / WIP 科目,在【两种模式下】都不会自清。**

| 模式 | 残留 | 性质 |
|---|---|---|
| **`real_time`** | **`+5`** | **标准差异**(实际 130 vs 标准 125) |
| **`periodic`** | **`−25`** | **增值残差**(料件流被抓,人工缺席) |
| | **两者都必须【人工】结转到差异科目 / COGS** | |

### 🔴 后果 / Consequence

**这个科目会【逐月累积】,而且:**

- **不会有任何告警**
- **月度损益的总额看起来永远是对的**
- **没有任何对手方会来抱怨**
- **报表侧(库存估值)永远是干净的** —— 只有 GL 这一侧在漏

> **它的失败签名,和 F-18、和 [B-42](#b-42) 的 `costs_hour`、和 B-14 —— 完全一致。**
> **结构性、静默、无对手方。**

---

<a name="b-46"></a>
## 4.3 · B-46 · 🗑️ **已作废** —— 「一个科目两种东西」不成立

### RETRACTED — the account holds only the variance, not WIP

| | |
|---|---|
| **状态** | 🗑️ **作废（2026-07-14 · T-01 实测证伪）。保留编号作为负结果记录，不再重用。** |

### 原主张 / The retracted claim

~~「生产库位估值科目里同时装着【真 WIP（资产）】和【标准差异（损益）】，
而 `account_type` 只能选一个 → 两条路都有洞。」~~

### 🔴 为什么它是错的 / Why it died

**T-01 实测（单步制造）：**

```
已领料未完工时：
    mo.state                  = confirmed
    move_raw.state            = assigned        ← 只是【预留】，不是 done
    move_raw.quantity         = 2.0
    move_raw.value            = 0.0             ← 🔴 价值没有流动
    move_raw.account_move_id  = False           ← 零分录
    生产库位科目余额            = 0.0             ← 判别点

完工后（mark_done）：
    move_raw.state = done  |  value = 100.0  |  生产库位科目余额 = 5.0   （只有 +5 差异）
```

> ## **单步制造下，料件消耗与完工是【原子】的。**
> ## **「已领料未完工」这个会计状态，根本不存在。**

**两步制造（`manufacture_steps = pbm`）补测：**

```
预生产库位 usage = internal，配估值科目 Q
「领料到预生产」调拨完成后（MO 仍 confirmed）：
    pick move state = done  |  pick move value = 0.0     ← 内部调拨【不计价】
    Q（预生产）余额 = 0.0                                  ← 真 WIP 还是抓不到
```

**根因：库存 → 预生产是【内部调拨】（既非 `is_out` 也非 `is_in`）→ 不计价 → 即使挂了估值科目也零分录。**

### 结论 / Verdict

> ## **生产库位科目是一个【纯差异容器】。**
> ## **`expense_direct_cost` 是对的。→ [B-39](#b-39)**

**⚠️ 副产物：原生【没有任何字段/报表】能给出「未完工 MO 已领料的价值」。**
**真要在总账上看到 WIP，只能靠 `account_production_wip_account_id` → [B-34](#b-34) 的补注。**

---
---
---

# 附录 · Appendix

## A. 制造成本的完整配置清单
## A. Full configuration checklist

### 🔴 一级 · 配错了整个机制静默失效

| ✅ | 检查项 | 关联条目 |
|---|---|---|
| ☐ | 🔴 **架构确认**:做一张 MO(料件**真的**被消耗),确认 Journal Items **不是空的**。<br>**Odoo 默认是空的。** | [B-34](#b-34) |
| ☐ | 🔴 **生产库位配了 `valuation_account_id`**(UI = **Cost of Production**)—— 不配则**整个制造过程在总账上不存在** | [B-34](#b-34) [B-36](#b-36) |
| ☐ | 🔴 **该科目 `account_type` = `expense_direct_cost`,命名为 `Manufacturing Cost Variance`**<br>**它是一个【纯差异科目】,里面没有真 WIP([B-46](#b-46) 已证伪)。AVCO/FIFO 下余额恒 0 → 无害;Standard 下差异自动落 COGS 段 → 零手工分录** | [B-39](#b-39) [B-46](#b-46) |
| ☐ | 🔴 **成本法决定月结工作量**:**AVCO = 完工即平,期末无需管 WIP**;**Standard = 完工留差,月结必须加一步人工清理** | [B-39](#b-39) |
| ☐ | 🔴 **成品品类 = `real_time`**(否则人工永远不进 GL) | [B-36](#b-36) [B-45](#b-45) |
| ☐ | **每个工作中心的 `expense_account_id` 已配**(没配则回落到成品品类的费用科目) | [B-36](#b-36) |
| ☐ | 人工与机器要**分开记科目** → **拆成两个工作中心**,BoM 上各挂一道工序 | [B-41](#b-41) |
| ☐ | **每台关键设备:一个资产 + 一个工作中心 + 一个折旧费用科目** | [B-41](#b-41) [B-42](#b-42) |

### 🔴 二级 · 操作纪律(配置救不了,只能靠 SOP)

| ✅ | 检查项 | 关联条目 |
|---|---|---|
| ☐ | 🔴 **Standard + 科目配成 `asset_current`(备选路线)→ 月末必须【人工】结转差异**<br>`Dr 制造成本差异(P&L)   Cr 生产库位科目`,金额 = **该科目当前余额**(它【全部】是差异)<br>✅ **若按推荐配成 `expense_direct_cost` → 这一步不需要** | [B-39](#b-39) [B-44](#b-44) |
| ☐ | 🔴 **`periodic`:月末同样留残差**(库位重分类只抓料件流,人工缺席) | [B-45](#b-45) |
| ☐ | ✅ **AVCO / FIFO:这一步永远不需要**(每单自清,零残差) | [B-39](#b-39) |
| ☐ | 🔴 **`costs_hour` 定期复核**(季度:设备月折旧 ÷ 预计有效工时,重算) | [B-42](#b-42) |
| ☐ | 🔴 **制造费用吸收差异**(费用科目上的残差)每月认损益或结转 COGS —— **关账不碰它** | [B-43](#b-43) |
| ☐ | **Standard 成本法上线前问一个问题:「谁,每个月,会打开差异科目看一眼?」**<br>**答不上来 → 不要上 Standard。**(没人看的差异 ≡ 没有差异,此时 Standard **严格劣于** AVCO) | [B-38](#b-38) [B-39](#b-39) |

### 🟡 三级 · 团队认知

| ✅ | 检查项 | 关联条目 |
|---|---|---|
| ☐ | **分析账 ⊥ 总账** —— 分析行照跑,不代表总账有分录 | [B-37](#b-37) |
| ☐ | **企业版 HR 工时成本只进分析账,永不进 GL** | [B-37](#b-37) |
| ☐ | **报表估值侧【无条件】包含工时成本** —— 报表对 ≠ 总账对 | [B-36](#b-36) |
| ☐ | **想在总账上看到【真的在制品】→ 只能用 `account_production_wip_account_id` 的【手工预提 + 次日红冲】向导**。<br>**库位科目抓不到跨期 WIP** | [B-34](#b-34) [B-46](#b-46) |
| ☐ | 🔴 **原料和成品必须【一起】用 Standard**(T-03 实测:原料非 Standard → 采购价差涌进 WIP,与制造差异**不可分**) | [B-38](#b-38) |

---

## B. 三种成本的去向 · 一张表
## B. Where the three cost types go

| 成本 | 配置 | **实时进 GL 的条件** | **`periodic` 时** |
|---|---|---|---|
| **人工** | 工作中心 A + 费用科目 | `real_time` + **生产库位估值科目** | 🔴 **永远不进 GL**([B-45](#b-45)) |
| **机器** | 工作中心 B + 折旧费用科目 | 同上 | 同上 |
| **料件** | — | **生产库位估值科目** | 关账的**库位重分类**抓到 |
| **标准差异**<br>(Standard 专属) | — | 🔴 **滞留 WIP 科目,线性累积**<br>**关账不碰,必须人工结转** | 同左 |
| **员工(HR 模块)** | 员工工时率 | ❌ **只进分析账,永不进 GL** | — |

---

## C. Odoo MRP 的模型边界
## C. The boundaries of Odoo's MRP model

**事实,不是意见:**

| Odoo MRP **有** | Odoo MRP **没有** |
|---|---|
| BoM(物料清单) | **得率 / Yield**(投 100kg 出 92kg,那 8kg 的处理) |
| MO(「生产 N 个」) | **配方版本管理**(Recipe versioning) |
| 工序 / 工作中心 | 成熟的**联产品 / 副产品**成本分摊 |
| 差异【产生】的机制 | 🔴 **差异【分析】的报表** —— 采购价差 / 用量差 / 效率差<br>**全挤在一个科目里,一个数** |

> ## **整套模型假设产品是【可数的个体】—— 即【离散制造】。**

**流程制造(化工、食品、制药、涂料)上 Odoo,得率与联产品成本是【原生缺口】。**

⚠️ **别把「离散 vs 流程」和「MTO vs MTS」搞混 —— 那是两条正交的轴。**
一家给苹果做外壳的代工厂 = **离散 + MTS**。
---
---

# 增补 · 2026-07-15 · `periodic` 完整机制闭合
## Addendum · The complete periodic mechanism

> **来源:T-10 / T-11 / T-13 三轮实测(脚手架校验全部通过 → 数据可信)。**
> **本轮把「`periodic` 到底怎么记账」从三个盲点变成一条完整链路,并推翻了两条旧结论的适用范围。**
> **一句话:`periodic` 不是「延迟入账的 real_time」,它是【真·定期盘存制】—— 采购即费用化,期末反向资本化。**

---

<a name="b-47"></a>
## B-47 · 🔴🔴 `periodic` = 真·定期盘存制:账单进 P&L,卖出无 COGS 行

### Under periodic, the bill hits P&L and the sale posts no COGS line

| | |
|---|---|
| **等级** | 🔴🔴(**颠覆"periodic 是延迟版 real_time"的直觉**) |
| **状态** | ✅ 已实机验证(T-10 / 补测 2 / **T-16 确认与成本法无关**:AVCO 臂同样零 COGS 行) |
| **前置** | [B-13](#b-13) 门② 分叉 |

### 🎯 核心 / The core

**`periodic` 品类下,整条采购—制造—销售链的会计,和 `real_time` 是【两套完全不同的机制】,不是"晚一点入账"。**

### 实测 ① / Observed —— 供应商账单过账

```
periodic 品类,采购原料 → 收货 → 供应商账单【过账】:
    Dr  600000 Expenses      ← 🔴 原料成本进【P&L 费用】,不是存货科目
    Cr  211000 Payable
```

> **门① 也带 `real_time` 条件。`periodic` 下账单【绕过存货科目】,直接费用化。**
> **收货 move `account_move_id = False`(和 real_time 一样),但账单去向完全不同。**

### 实测 ② / Observed —— 卖出制成品(FG),COGS 科目零触发

```
发货时:  move value=125  account_move? False   ← periodic 发货零 GL
开票时:  Cr Income 200 / Cr Tax 30 / Dr Receivable 230   ← 发票上【没有 COGS 行】
关账时:  关账凭证里【没有任何一行碰 COGS 科目】
                                              ─────────────
COGS 科目自始至终 = 0
```

### 机制 / Mechanism —— COGS 是【隐式】的

```
本期成本  =  原料采购全额费用化 (600000, Dr 1000)
           − 关账把未售存货资本化回资产 (Stock Variation, Dr 存货 / Cr StockVar)
           ────────────────────────────────────────────────
           = 已售部分的成本               ← 这就是"隐式 COGS"
```

**实测(卖 1 台 FG,原料买 20@50=1000,耗 2 件):**
```
600000 Expenses          +1000  (Dr)   ← 采购全额费用化
StockVariation            −875  (Cr)   ← 关账资本化未售的 18 件
生产库位                   −25  (Cr)
本期 P&L 成本 = 1000 − 875 − 25 = 100   ← 只有已耗 2 件原料的钱
```

### 🔴 后果 / Consequence

> ## **`periodic` 下【没有按单 / 按台 COGS】。**
> ## **任何按单毛利的报表或模块(含 `suite_po_profit`),在 periodic 客户库上【无源可读】—— 不是不准,是数据根本不存在。**

- 上例:账面毛利 = 200 − 100 = **100**;但 FG 真实成本 = 料 100 + **工 30** = 130 → 真实毛利应是 **70**
- **虚高的 30 = 那笔从未入账的人工**([B-45](#b-45))
- **没有告警、没有对手方、月度损益总额永远对。**

### 对策 / Mitigation

- **要按单毛利 → 品类必须 `real_time`。** 见决策速查 Q2。
- periodic 只适合:存货非主要资产、不做制造、不看按单毛利(耗材/包材/办公品)。

---

<a name="b-48"></a>
## B-48 · 🔴 `periodic` 的生产库位科目 = 转换成本吸收科目,不是差异容器

### Under periodic, the production-location account is an absorption account, not a variance container

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证(T-10:A/B 双臂 + 逐月关账) |
| **⚠️ 修订** | **[B-46](#b-46) 的「纯差异容器」结论,只对 `real_time` 成立。periodic 下本科目性质完全不同。** |

### 🎯 判别实测 / The discriminating test

**判别力全在两个成本法的差值上:**

| 臂 | 生产库位(3 单后) | 每单 | 分解 |
|---|---|---|---|
| **A · periodic + AVCO** | **−90** | **−30** | **纯人工资本化,零标准差异** |
| **B · periodic + Standard** | **−75** | **−25** | **= −30(人工) + 5(标准差异)** |

> **那 5 的差,把「人工资本化」和「标准差异」两个成分干净地分离出来。**
> **若 A 跑出 0 或 +30,或 A = B,H1 当场死 —— 它没有,H1 活。**

### 机制 / Mechanism —— 吸收贷方落在哪,决定科目里剩什么

关账的「库位重分类」post 的是净额 `料件进 − 成品出`:
```
AVCO:      100 − 130(实际) = −30     ← 纯人工
Standard:  100 − 125(标准) = −25     ← 人工 + 标准差异
```

**根子在:`periodic` 下 `_post_labour` 不触发([B-36](#b-36) 条件 1)→ 人工的 30 从来没以"费用"身份进过 GL → 关账把成品全值(含人工)搬进存货时,其贷方对手只能落在生产库位科目上。**

| 模式 | 生产库位科目装的是 | 吸收贷方落点 |
|---|---|---|
| **`real_time`** | **只有标准差异**(+5/单) | `workcenter.expense_account_id`(和工资同科目 → 自然对冲) |
| **`periodic`** | 🔴 **−人工 + 标准差异**(−30 或 −25/单) | **生产库位 `valuation_account_id`**(和工资不同科目 → 永不对冲) |

### 🔴 逐月累积,永不自清

```
月1 关账:  −25    月2:  −50    月3:  −75     ← 线性滚大
人工科目全程 = 0,关账每月只 ADD 一笔,无任何自动对冲
```

### 对策 / Mitigation —— 见 [B-51](#b-51)

**直接把生产库位科目配成 `expense_direct_cost` 会在 COGS 段挂一个逐月增长的贷方(负成本)→ 毛利虚高。**

**正解:新建一个隔离的 overhead 科目,把生产人员 payroll 归集进它、关账吸收贷方也落它 → 自然对冲。** 详见 [B-51](#b-51)。

---

<a name="b-49"></a>
## B-49 · `action_close_stock_valuation` 对未来期不过账,凭证卡 draft

### The close does not post to a future period — the entry stays draft

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 已实机验证(T-13 过程中踩到并修正) |

### 实测 / Observed

```
关账日 at_date = 未来日期(今天 07-15,关账日填 07-31)
    → 生成的关账凭证卡在 draft、不过账
    → 科目余额【假性停滞】,看上去像"没变化"
改用过去/当前月份 → 凭证全部 posted,余额正常变动
```

### 🔴 后果 / Consequence

**这是一个真实行为,不只是测试陷阱:** 若在月中用未来的月末日期跑关账,凭证不 post → 你看到的余额是**过期快照**,会误判"关账没起作用"。

**测试纪律的姊妹条见 [B-52](#b-52)(回填月份时,单据链上所有 move 必须同期回填)。**

---

<a name="b-50"></a>
## B-50 · `expense` 型科目可挂 `location.valuation_account_id`,Odoo 无约束

### An expense-type account can serve as a location valuation account — no constraint

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 已实机验证(T-13,四臂皆然) |

### 事实 / The fact

```
expense 型科目挂进 location.valuation_account_id  →  ok = True, err = None
四臂全部无任何约束 / 报错 / 警告
```

> **这是 [B-48](#b-48) 那个解的机制前提:** 既然 `expense` 科目能当估值科目,就能让 payroll 的借方(费用科目)和关账吸收的贷方(库位估值科目)落进同一个 `expense_direct_cost` 科目,实现自然对冲。

### ⚠️ 但别照字面配「指向工资科目本身」

**副作用(未评估,但确定存在):** 工资科目一旦兼任存货流中转,它的余额就不再是"本期工资总额",而是「工资 − 已吸收」→ **payroll 对账和审计会读错**;非生产人员工资若也记这个科目,会和吸收永久混。

**正确配法是隔一层(见 [B-51](#b-51)):新建专用 overhead 科目,工资【转拨】进去,而不是让工资科目本身兼任。**

---

<a name="b-51"></a>
## B-51 · 🔴 `costs_hour` 是两模式共用的吸收率;通则:归集科目 = 吸收贷方科目

### `costs_hour` is one absorption rate across both modes; the general rule

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证(T-13:E/F/G 三臂 + real_time 对照) |
| **前置** | [B-42](#b-42) [B-48](#b-48) —— **本条把 B-42 从"折旧特例"升成通则** |
| **⚠️ 适用边界** | **本条的 payroll 对冲 SOP 只在 `periodic` 严格成立。** `real_time` 跨期生产的人工错期结构性、关账不可修 → **见 [B-55](#b-55)**。隐含前提 = 同一关账区间内看净额 → [B-56](#b-56) |

### 🎯 通则 / The general rule

> ## **`costs_hour` 在【两种模式下】都是【预定制造费用吸收率】。**
> ## **变的只是【吸收贷方落在哪个科目】。**
> ## **要让转换成本(人工/机器)自然对冲 —— 【归集借方的科目】必须 = 【吸收贷方的科目】。**

| | 吸收贷方落点 | 归集借方要记到 |
|---|---|---|
| **`real_time`** | `workcenter.expense_account_id`(`_post_labour` 触发) | **同一个科目** |
| **`periodic`** | **生产库位 `valuation_account_id`**(关账重分类触发) | **同一个科目** |

> 🔴 **`periodic` 下 `workcenter.expense_account_id` 压根不被使用** —— 唯一的杠杆是生产库位科目。
> **B-42 的「机器折旧指向同一个 620000」不是折旧的特例,它就是这条通则的一个实例。**

### 实测 / Observed —— T-13 三臂,H3 活

| 臂 | 配置 | payroll 借 | 关账吸收 贷 | **关账后余额** | 性质 |
|---|---|---|---|---|---|
| **E** | periodic+AVCO,实发 30 | +90 | Cr 90 | **0** | 完全对冲 |
| **F** | periodic+Std,实发 30 | +90 | Cr 75 | **+15** | 纯标准差异(3×5) |
| **G** | periodic+AVCO,实发 **40**(率 30) | +120 | Cr 90 | **+30** | **吸收不足差异,与 [B-43](#b-43) 同构** |

**关键旁证:三臂 `Stock Variation Global` 全部 = −500,与「独立科目 + 无 payroll」对照臂完全相同 → payroll 落在【库位重分类】链上对冲,不进【Stock Variation】链,存货科目对账 gap = 0。**

### 🎯 推荐配法 / Recommended setup

```
新建   T_OVH  "Manufacturing Overhead — Absorbed"   account_type = expense_direct_cost
       ↑ 生产库位 valuation_account_id 指向它(periodic 下)

生产人员 payroll  →  Dr T_OVH        ← 归集(转拨,不是让工资科目本身兼任)
机器折旧          →  Dr T_OVH        ← 归集(或按 B-41 拆多个)
关账重分类        →  Cr T_OVH        ← 吸收
                     ─────────────────
                     余额 = 吸收差异 + 标准差异     ← 每月看一眼,与 B-42/B-43 同套 SOP
```

- **工资科目留干净**(全额工资),生产工资**转拨**进 T_OVH
- **`expense_direct_cost`** → 差异落毛利线内,可见
- **AVCO + 率准 → 恒 0**,无害
- `costs_hour` 季度复核、残差三选一(当期认/调率/转 COGS)—— **与 [B-42](#b-42) [B-43](#b-43) 原样适用**

### 🔬 未测 / Not yet tested

- **工资/生产跨期错配**(工资月结、生产跨月):payroll 在 M 月、吸收在 M+1 月 → 科目余额月度摆动、年度净平。会影响"每月看一眼"的可读性。**建议跑一次确认。**
- **配置在报表科目性质上的副作用**(`expense` 科目出现在库位估值链路)对财务报表分类/审计的影响 —— 超出 GL 机制范围,未评估。

---

<a name="b-52"></a>
## B-52 · 🔴 (测试纪律)回填月份关账,单据链上所有 move 必须同期回填

### (Test discipline) When back-dating a close, back-date every move on the chain

| | |
|---|---|
| **等级** | 🔴(测试纪律,非会计机制) |
| **状态** | ✅ 已实机验证(T-13 过程中踩到) |
| **归属** | 属于测试方法论;正式规格见 `odoo19_test_specs.md` 第 0 节。此处留一条指针 |

### 陷阱 / The trap

```
模拟过去月份关账时,只回填了 MO 的 move(06-15),没回填 PO 收货(留在今天 07-14)
关账在 06-30  →  关账快照看不到原料入库  →  存货少算 200
             →  Stock Variation 行消失  →  制造出 INV_GL−report = −200/−500 的伪证
```

### 🎯 判别 / How it was caught

**同库 side-by-side 拆穿:** 独立科目无 payroll 的对照臂(S)和共用 payroll 臂(P)**缺口一模一样都是 −200** → 证明缺口与配置无关,是【日期 bug】。回填收货日期后两臂归零(590→590),H3 结论不变。

> **这是 [B-49](#b-49)「未来期关账 draft」的姊妹条:回填月份时,一张单据链上的【所有】move(收货/消耗/完工)必须同期回填,漏一个就会让关账快照失真。**

---
---

# 增补 · 2026-07-15 (二) · `real_time` 回填 & 跨期人工错期
## Addendum · Back-dating and cross-period labour under real_time

> **来源:T-14 / T-15 / T-16 + 补测 A/B/C + T-18(脚手架全过 → 数据可信)。**
> **本轮把「`real_time` 回填过去期"看起来对不上"」追到源码,并划死了 [B-51](#b-51) 那套 payroll 对冲的适用边界。**
> **核心认知:`real_time` 解决了「人工进不进 GL」,但没解决「人工进对期」—— labour GL 硬编码今天,跨期无解。**

---

<a name="b-53"></a>
## B-53 · 🔴 `real_time` 存货 GL 入账日 = `force_period_date or today`,与 `stock.move.date` 解耦

### The real_time inventory GL date follows force_period_date, not stock.move.date

| | |
|---|---|
| **等级** | 🔴 |
| **状态** | ✅ 已实机验证(T-15 三臂)· 📖 已源码确证 |
| **源码** | `stock_move._create_account_move()` 第 205 行 |

### 🎯 事实 / The fact

```python
# stock_move._create_account_move() : 205
'date': self.env.context.get('force_period_date') or fields.Date.context_today(self)
```

> **`real_time` 的每笔存货 GL 分录,入账日取 `force_period_date`(context)或【今天】—— 【不跟】 `stock.move.date` 走。**

### 实测 / Observed —— 这解释了 T-13 的 75 缺口

| 手法 | 生产 move.date | 生产 GL.date | 缺口 |
|---|---|---|---|
| **CLEAN**(validate 时传 `force_period_date=6月`) | 2026-06-15 | **2026-06-15**(一致) | **0** ✅ |
| **MOVEONLY**(validate 在今天,事后 `write({'date':6月})`) | 2026-06-15 | **2026-07-15**(锁今天,错位) | **+25/单** 🔴 |

**T-13 的 75 = 3 MO × 25 = 那批"今天的"生产 GL 事后仍留在账上,关账按差额补 25/单 → 净多算。**

> **→ T-15 结案:75 是 [B-52](#b-52) 的一个实例(回填不完整),【不是关账引擎的 bug】。**

### 🔴 铁律 / The rule

> **`real_time` 下「回填一笔交易」不能只改 `stock.move.date`。** 它的 GL 分录日期在 validate 那一刻就锁死了。
> **正确回填 = 在 validate 时传 `force_period_date`**(或事后同时改 `account.move.line.date`)。

---

<a name="b-54"></a>
## B-54 · 🔴🔴 `_post_labour` 的 GL 日期硬编码 `context_today` —— 人工成本无法回填到过去期

### Labour GL date is hardcoded to today — it cannot be back-dated even with force_period_date

| | |
|---|---|
| **等级** | 🔴🔴 |
| **状态** | ✅ 已实机验证(T-15 / 补测 C)· 📖 已源码确证 |
| **源码** | `mrp_account._post_labour()` 第 119 行 |

### 🎯 事实 / The fact

```
labour 分录 date = context_today  —— 连 force_period_date 都【不认】
```

**比 [B-53](#b-53) 更硬:** 存货 GL 至少还认 `force_period_date`;labour GL **谁都不认,永远落今天。**

### 实测 / Observed —— 补测 C(real_time + AVCO,生产回填 6 月)

```
OVH 上的三条 GL:
    raw       date = 2026-06-15   Dr 100    ← force_period_date 生效,回到 6 月 ✓
    finished  date = 2026-06-15   Cr 130    ← force_period_date 生效,回到 6 月 ✓
    labour    date = 2026-07-15   Dr  30    ← 🔴 锁今天,回填不了
```

### 🔴 后果 / Consequence

> **`real_time` 的人工成本 GL【无法回填到过去期】。**
> **补跨月生产、或工资跨期时,这条会【持续制造】labour 科目的时点错位。** → 见 [B-55](#b-55)

---

<a name="b-55"></a>
## B-55 · 🔴🔴 [B-51](#b-51) 的 payroll 对冲只在 `periodic` 成立;`real_time` 跨期人工错期结构性、关账不可修

### B-51's payroll offset holds only under periodic

| | |
|---|---|
| **等级** | 🔴🔴 |
| **状态** | ✅ 已实机验证(补测 B/C 对照 + T-18) |
| **⚠️ 修订** | **[B-51](#b-51) 的对冲 SOP 加 `real_time` 跨期免责** |

### 🎯 两种模式的分野 / The divide

| | `periodic`(补测 B) | `real_time`(补测 C) |
|---|---|---|
| 吸收贷方落地 | 关账 **Location Reclassification** `Cr OVH`,**永远随生产在同一关账期** | 🔴 **生产库位科目不参与 Location Reclassification**(那是 periodic 专属,[B-45](#b-45)) |
| 人工 GL 日期 | (无独立 labour JE,人工靠库位重分类聚合) | 🔴 **labour 锁今天**([B-54](#b-54)) |
| 跨期结果 | ✅ payroll 借方对冲干净,两月净平([B-56](#b-56)) | 🔴 **6 月生产的人工(30)缺席 → OVH 挂 −30,要等 7 月人工入账才归零** |

> ## **`periodic` 有补偿机制(库位重分类把吸收随生产落在同期);`real_time` 没有。**
> ## **`real_time` + 需回填过去期生产 → 人工时点错位是【结构性的、关账不可修复】。**

### 🎯 对策 / Mitigation —— T-18 实测

**✅ 手工可逆预提【有效】(C2b,五行台账为证):**

```
6-30  Dr OVH 30 / Cr 应计工资 30      ← 期末预提本期已完工但人工未落地的部分
7-01  Cr OVH 30 / Dr 应计工资 30      ← 次日自动冲回
7-15  Dr OVH 30                        ← 真实人工(_post_labour)落地,补上冲回的缺口
────────────────────────────────────
每个期末快照 OVH 都干净 = 0;应计工资负债只在 6 月存在,7-1 清零
```

**这就是标准的月末权责发生制切分,手工做完全可行。**

### 🔴 但标准 mrp WIP 向导【补不了】这个场景 —— 两个独立死因(C2a)

| # | 死因 | 源码 |
|---|---|---|
| **1** | **状态过滤:向导 `default_get` 只认在制 MO**(`state in ['progress','to_close','confirmed']`)。**已完工 MO 被直接剔除** → `mo_ids=[]`,三条 line 全 0 空分录 | 向导第 47 行 |
| **2** | **科目解耦:向导记的是公司级 WIP 资产 + WIP 间接费科目**(`110100 fallback / TDWIP / TDWOVH`),**跟生产库位的 OVH 科目完全无关。** 就算跑起来也是另起一套 WIP 分录,**根本不碰那 −30** | 向导第 86/96/101 行 |

> ## **向导是给「在制品月末切分」用的(已投料工的在制品快照进 WIP、次日冲回),不是修「已完工品的人工晚记」的。两者是不同问题。**
> **别指望 mrp 的 WIP 向导 —— 名字叫 "Manufacturing WIP" 但它管的不是这个。**

### 🔬 未测(降级为模块/开发待办,非机制)

> **C2b 的预提金额(30)在测试里是手填的。真实场景要回答「本期已完工、但人工未落地的待提金额是多少」—— Odoo 没有现成报表给这个数。**
> **这已经不是会计机制的坑,是一个【取数缺口】:需要一个查询,捞出"本期 `done`、但其 workorder 的 labour move 尚未过账"的 MO。属开发任务,见附录 Z。**

---

<a name="b-56"></a>
## B-56 · `periodic` 跨期 OVH 摆动是对称的;SOP 双向警告

### Periodic's cross-period OVH swing is symmetric

| | |
|---|---|
| **等级** | 🟡 |
| **状态** | ✅ 已实机验证(T-14 + 补测 B,正反双向) |

### 实测 / Observed —— 正反两向是精确镜像

| 方向 | M 月末 OVH | M+1 月末 | 两月净 |
|---|---|---|---|
| **工资早、生产晚**(T-14) | **+90**(像欠吸收) | 0 | 0 |
| **生产早、工资晚**(补测 B) | **−90**(像超吸收) | 0 | 0 |

**根因:吸收贷方随生产落地、payroll 借方随工资落地 —— 两者错期,单月看到净差;同一关账区间内看则净平。**

### 🎯 SOP —— 双向警告

> ## **「每月末打开 OVH 看一眼」会把【时点错配】误读成【吸收差异】。**
> **单月 OVH 无论正负大额,都可能只是工资/生产没对齐。**
> ## **必须看累计 / 季度,不看单月。**
>
> **[B-51](#b-51) 的 payroll 对冲成立,但隐含前提 = 「在同一关账区间内看净额」。**

---
---
---

# 旧条目修订 · Amendments to existing entries (2026-07-15 / 2026-07-19)

> **本库用「保留原文 + 追加修订」的方式留审计痕迹 —— 你能看见当初信了什么、为什么改。**
> **以下条目的原文【不动】,适用范围以本表为准。**

| 条目 | 原结论 | 本轮修订 | 依据 |
|---|---|---|---|
| **[B-13](#b-13)** | 门②(库位科目)只对 `real_time` 生效,`periodic` 塌缩进门③ | ✅ **不变,但补一层:`periodic` 下账单本身也绕过存货科目直接进 P&L(600000 Expenses)。periodic = 真·定期盘存制,不是"延迟版 real_time"** | [B-47](#b-47) / T-10 |
| **[B-35](#b-35)** | 关账凭证按【估值科目】聚合;按品类拆科目 = 唯一颗粒度杠杆 | 🔴 **收窄:共用科目时能按【组件】拆(库位重分类 vs Stock Variation,各带 label),但【不能按品类拆】—— `Stock Variation Global` 是全公司聚合行。→ 混用 periodic/real_time 仍必须拆估值科目** | [B-48](#b-48) / T-11 |
| **[B-39](#b-39)** | 生产库位科目 = 纯差异科目,配 `expense_direct_cost` | ⚠️ **限 `real_time`。** `periodic` 下它是**吸收科目**(装 −人工+差异),类型仍用 `expense_direct_cost` 但**必须隔一层引入 payroll 归集**,否则挂负成本贷方 → 毛利虚高 | [B-48](#b-48) [B-51](#b-51) / T-10·T-13 |
| **[B-45](#b-45)** | `periodic` 库位重分类只抓料件流,人工缺席,留 −25 残差 | ✅ **不变,机制补全:那 −25 是「吸收贷方落在生产库位科目」的结果。配好隔离 overhead 科目 + payroll 归集后可自然对冲(E 臂实测归零)** | [B-48](#b-48) [B-51](#b-51) / T-13 |
| **[B-46](#b-46)** | 生产库位科目是纯差异容器,里面没有真 WIP | ⚠️ **限 `real_time`。** 「纯差异容器」只对 real_time 成立;`periodic` 下它是**转换成本吸收科目**(见 [B-48](#b-48))。两步制造下"库存→预生产是内部调拨不计价"的结论**两模式都成立**(真 WIP 都抓不到) | [B-48](#b-48) / T-10 |
| **[B-17](#b-17)** | 已发货部分的追加成本「进差异科目(P&L)」 | 🔴 **措辞作废。** 落点 = **LC 成本行 `account_id`**(兜底 = 运费产品费用科目);品类 `account_stock_variation_id` **全程不被引用,配了实测为 0**。且这是**设计意图**(docstring 明写),措辞改为「只资本化在库份额,其余按设计留费用科目」。配置杠杆 = 每张 LC 单据的成本行科目 | `stock_landed_cost.py:353/377`;干净基类对平重测 |
| **[B-27](#b-27)** | 出库 move 的 value 在 `_action_done` 钉死(四变体实测归纳) | ✅ **不变,证据升级为源码事实。** `account_move.py:42` 的 `filtered(lambda m: m.is_in or m.is_dropship)` —— **OUT move 被显式排除在重估之外**。同方法 `:33` 的 `move_reverse_cancel` 早退 → 红冲作废也不重算 | `account_move.py:33/42` |
| **[B-13](#b-13)** | 门②(库位科目)只对 `real_time` 生效 | ✅ **不变,补 LC 落点:** `stock_landed_cost.py:124` 令 periodic 产品做 LC **零 GL 分录**、估值层照调;但同方法 `:152` 的 `_set_value()` **无条件** —— 这个不对称正是 [B-57](#b-57) 的根 | `stock_landed_cost.py:124/152` |
| **[B-47](#b-47)** | `periodic` 卖出无 COGS 行(Standard 臂验) | ✅ **确认与成本法无关。** AVCO 臂(T-16)COGS posted 行数=1、唯一那行=采购账单,发货/开票/关账三处全 0 行 | T-16 |
| **[B-51](#b-51)** | payroll 对冲成立(同期实测归零) | 🔴 **收窄:只在 `periodic` 严格成立。** `real_time` 生产库位不参与关账重分类 + labour 锁今天 → 跨期人工错期结构性、关账不可修 → **新增 [B-55](#b-55)**。对冲的隐含前提 = 同一关账区间内看净额([B-56](#b-56)) | [B-55](#b-55) [B-56](#b-56) / 补测B·C / T-18 |

---
---

# 附录 Z · 合并待验证队列 · Combined Verification Queue

> **跨全库汇总,替代原三文件各自的队列。按重要性排序。**

### 🔬 仍未闭合 · Open(GL 机制)

| # | 待验证 | 出处 | 优先级 |
|---|---|---|---|
| **1** | `real_time` + Standard **跨期**残差(应是 −5 标准差异侧叠加在人工错期上) | [B-55](#b-55) | 🟢 低,机制同构可预测 |
| **2** | 手工可逆预提在**多月连续 / 多 MO 叠加**下是否仍逐月净零 | [B-55](#b-55) | 🟡 中,权责月末切分理论上净零,值得一个确认 |
| **3** | 关账后 `suite_po_profit` 的按台毛利在 [B-14](#b-14) 下是否失真 | [B-14](#b-14) | **模块域**,另起 suite 环境 |
| **5** | 开启 **Valuation by Lot** 时,零库存 lot 的 `lot.standard_price` 在 LC 后是否同样被抬高 | [B-57](#b-57) | 🟡 中。[B-21](#b-21) 已知 `lot.avg_cost` 发空归零,lot 侧行为可能另有分支 |
| **6** | LC 验证**之后**发生采购退货 / 盘盈,使 `remaining_qty` 回升 —— 已成型的分摊比例是否重算 | [B-57](#b-57) | 🟡 中。影响 Stage 1 探针的口径稳定性 |
| **8** | FIFO 下,开票→发货窗口内**队头那批被贴 landed cost 或账单晚到重估** —— 发散是否等于队头层价差 | [B-59](#b-59) [B-17](#b-17) | 🟡 中。机制可预测,但 FIFO「安全」的边界需要实测钉死 |
| **9** | FIFO 下,开票→发货窗口内**队头被别单先消耗** —— 实测发散是否 = 队头层与实际消耗层的价差 | [B-59](#b-59) | 🟡 中。多单并发是真实环境常态 |
| **7** | `periodic` 产品在 [B-57](#b-57) 场景下的表现(GL 本就零分录,成本层是否同样被抬高) | [B-57](#b-57) [B-13](#b-13) | 🟢 低,机制同构可预测 |
| **4** | `expense` 科目出现在库位估值链路,对**财务报表分类 / 审计**的影响 | [B-50](#b-50) | 超出 GL 机制范围,靠会计政策判断 |

### 🛠️ 开发待办(非机制,取数缺口)

| # | 任务 | 出处 | 说明 |
|---|---|---|---|
| **D-1** | 查询「本期已完工、但 workorder 的 labour move 尚未过账」的 MO,给出待提金额 | [B-55](#b-55) / C2b | `real_time` 跨期人工预提的输入。**Odoo 无现成报表**,须自建查询。这是机制探索的下游,属模块/开发域 |

### ✅ 已闭合(2026-07-15 · T-10 ~ T-18)

| 原问题 | 结论 |
|---|---|
| ~~`periodic` + 制造的完整 GL 路径(料件/人工/差异分别落哪)~~ | ✅ **闭合。** 账单→P&L([B-47](#b-47));料件流→关账库位重分类;人工→**永不进 GL**,以"吸收贷方"落生产库位科目([B-48](#b-48)) |
| ~~`periodic` 下卖出制成品有没有 COGS 行~~ | 🔴 **零 COGS 行。** 发货/开票/关账全不碰。COGS 是隐式的;AVCO 臂(T-16)确认与成本法无关 → [B-47](#b-47) |
| ~~`expense_direct_cost` 的推荐在 periodic 下成不成立~~ | ⚠️ **不能照搬。** periodic 下是吸收科目,须隔离 overhead 科目 + payroll 归集 → [B-48](#b-48) [B-51](#b-51) |
| ~~混用 periodic/real_time 估值科目能不能共用~~ | 🔴 **不能。** 能按组件拆、不能按品类拆 → [B-35](#b-35) 修订 |
| ~~payroll 借方能不能与关账吸收贷方自然对冲~~ | ✅ **能(同期 H3 活)。** 归集科目 = 吸收贷方科目 → E 臂归零、G 臂 +30 与 [B-43](#b-43) 同构 → [B-51](#b-51) |
| ~~`expense` 型科目能不能当库位估值科目~~ | ✅ **能,Odoo 无任何约束/报错/警告** → [B-50](#b-50) |
| ~~未来期关账为什么"没反应"~~ | ✅ **凭证卡 draft、不过账** → [B-49](#b-49) |
| ~~T-13 的 75 缺口:真 bug 还是脚手架残留~~ | ✅ **脚手架残留(B-52 实例)。** `real_time` 存货 GL 日期取 `force_period_date`,只改 move.date 不带动 GL → [B-53](#b-53) |
| ~~`real_time` 人工能不能回填到过去期~~ | 🔴 **不能。** `_post_labour` 硬编码 today,连 fpd 都不认 → [B-54](#b-54) |
| ~~payroll 对冲 SOP 在 `real_time` 跨期成不成立~~ | 🔴 **不成立,只在 periodic。** real_time 生产库位不参与关账重分类 + labour 锁今天 → 跨期人工错期结构性、关账不可修 → [B-55](#b-55) |
| ~~`real_time` 跨期人工错期能不能补~~ | ✅ **手工可逆预提能补**(五行台账);🔴 **标准 mrp WIP 向导补不了**(状态过滤剔除已完工 MO + 科目与 OVH 解耦,两个死因)→ [B-55](#b-55) |
| ~~LC 残值到底进品类差异科目还是别处~~ | ✅ **进 LC 成本行 `account_id`。** 品类 `account_stock_variation_id` 只在期末关账 + 估值报表被调用,`stock_landed_cost.py` 全程不引用 → [B-17](#b-17) 修订 |
| ~~零库存补 LC,坏在哪一层~~ | 🔴 **L1 成本层,且完全静默。** GL 零分录、`total_value` 不动,只有 `std` 被抬成幽灵值;AVCO / FIFO 两条路径殊途同归 → [B-57](#b-57) |
| ~~幽灵 `std` 会不会往后传染~~ | ✅ **不会。** 下一次收货的增量路径 `previous_qty ≤ 0` 时直接取新进货单价,不加权 → 窗口 = [D, D2) → [B-57](#b-57) 修正记录 |
| ~~开票早于发货时,COGS 与出库价值会不会对不上~~ | 🔴 **会,且不自愈。** 开票按当刻成本结转(AVCO 用 `standard_price`、FIFO 用队头层),物理出库另取一套;窗口内任何改变出库成本的事件都变成永久发散。**AVCO +100 / FIFO 0** —— 与原预测方向相反 → [B-59](#b-59) |
| ~~FIFO 开票时会不会直接消耗 FIFO 层~~ | ✅ **不会。** `_run_fifo` 是纯读函数(`product.py:553` docstring),开票只对队头成本拍快照,层消耗仍在 `_action_done` → [B-59](#b-59) |
| ~~取消/转草稿一张已重估的账单,估值会不会回滚~~ | 🔴 **撤销时不会**(成本层粘在中间态,GL 掉回去,存货科目现 **−500 贷方余额**,劈叉 1100);**但重新过账会**,`_post` 重算并覆盖([B-03](#b-03) 自愈)。风险在【停留在撤销状态】→ [B-58](#b-58) |
| ~~periodic 跨期 OVH 摆动是不是对称~~ | ✅ **对称。** 工资早 +90 / 生产早 −90,两月净平。SOP 双向警告、看累计 → [B-56](#b-56) |

*(场景 ① / ② 各自 2026-07-14 之前闭合的队列,保留在各章内的原始「本轮闭合」小节,未上移,避免重复。)*

---
---

*本库仅收录已在 Odoo 19 实机或源码上验证的行为。任何条目在升级到新的大版本后必须重新验证。*
*This library contains only behaviours verified on a live Odoo 19 instance or against its source.
Every entry must be re-verified after a major version upgrade.*
