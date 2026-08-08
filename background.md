## 0. 快速导航

1. 商业与品牌架构
2. 基础设施与开发工作流
3. SuiteState项目简要
4. 已发布apps.odoo  / 内部模块清单（**⚠️ 截止2026 JUL**）
5. Apps Store 发布规则
6. WhatsApp 架构
7. Odoo 19 技术约束（踩坑合集）
8. 交付验收惯例（跨项目）
9. 中国财务与税务市场事实（跨项目）


---

## 1. 商业与品牌架构
- **ElectroState FZCO**: UAE自贸区法律实体，主业 B2B 二手手机批发,已完成odoo.sh部署; 并作为 SuiteState 的挂靠法律实体(在营业执照上增加 IT 类目).
- **SuiteState**: 作为商号（trade name）运行，主打 Odoo 咨询与模块开发。以公司”深圳市和界鸿源科技有限公司“主体注册为odoo中国区合作伙伴；
- **其他业务**：加拿大分公司主要负责采购；计划承接B2B业务的零售流量搭建odoo2的B2C业务系统。

---


## 2.基础设施与开发工作流
- **VPS**：Vultr Tokyo(24$/月 2 vCPU/4GB RAM + 100GB）；Reserved IP。用作 Claude Code 工作站 + 在中国时的网络出口。部署了odoo19社区版作为SuiteState的业务系统。
2026-07-25 VPS Odoo Community 已 systemctl disable（主动停用，非故障）
恢复：sudo systemctl enable --now odoo
Nginx 反代配置保留，停用期间访问 erp.suitestate.com 返回 502 属正常

- **开发工作流**：本地VS code → git push → odoo.sh生产分支。

- **DB1（主库）**：ElectroState B2B 主业务 odoo.sh19.
- **DB2**：B2C website零售为主(未完成) odoo.sh19.


---

## 3. SuiteState项目简要
- **定位——填平 IT 与客户之间的双重信息差**：IT 方常不懂客户实际业务；客户不懂技术、无法判断方案是否最优；而两边通常都缺乏对 Odoo 的深度理解。SuiteState 的差异化正在于对 Odoo 产品本身的深挖——做模块时多次发现自己的方案思路整个 apps.odoo 上都没有、经多方评估仍更优，反证了多数开发者并未真正吃透 Odoo。核心价值：懂业务、懂技术、更懂 Odoo，公平定价、方案以客户最优为准。
- **商标**：在UAE以 Safi 个人名义申请，中国以"和界鸿源科技有限公司"为主体注册。
- **品牌视觉**：Mint Logo `#10A08C`、Deep `#088071`。
- **基础设施**：GitHub org `github.com/SuiteState`（monorepo，含 community 分支）；开发者账号 `suitestate-dev`；网站 `suitestate.com`（GitHub Pages + Cloudflare）；邮箱 `Hello@suitestate.com`。

---


## 4. 已发布apps.odoo  / 内部模块清单（**⚠️ 截止2026 JUL**）
### 已发布开源模块
- `suite_ai_translate`：Bidirectional AI Translate
- `suite_ai_provider_pool`
- `suite_inventory_access`：sales用户查看库存数量额外权限
- `suite_landed_cost_access`accounting用户额外权限
- `suite_contact_guard` 

### 已发布闭源模块
- `suite_po_profit`
- `suite_data_guard`
- `suite_cost_guard`
- `suite_whatsapp_ai`
- `suite_serial_trace`
- `suite_consignment`


### ElectroState自用模块
- `es_wa_retail`（Odoo2 零售号）
- `es_sale_price_guard`
- `es_wa_ai`不依赖odoo AI的claude接口+whatsapp ai,为减少维护成本会换为suite_whatsapp_ai。

### SuiteState 内部模块（不上架、不外售，按标品工程标准做）
- `suite_cn_localization/`（容器目录，非模块）下五件套：`suite_cn`（伞）/ `suite_cn_coa` / `suite_cn_statement` / `suite_cn_cashflow` / `suite_cn_cashflow_statement`（桥，auto_install）。
  中国本地化**内账地基层**，做「账」不做「证」。详见 note 仓库 `l10n_cn_localization_project.md`；设计权威在开发分支仓库的 `l10n_cn_design.md`（改动频繁，不入 note）。



---

## 5. Apps Store 发布规则（硬性经验）
- **index.html 和 manifest description 必须纯 ASCII**（Unicode 标点会破坏渲染，Odoo issue #37364）。
- **截图必须 16:9（1920×1080）**，否则顶部被裁。
- `images[0]` 同时用作产品卡图 + 详情页 hero；`_screenshot` 后缀图作为搜索缩略图。
- **避免 legacy `oe_*` grid 类**——用普通流式 HTML（`h1/h2/h3/p/ul/img/hr`）+ `style="width:100%; max-width:1920px; height:auto"`。
- 新模块搜索索引需 **24–48h**。
- 卸载模块会删对应库记录；有依赖会级联；扩展了核心模型的模块，卸载会 DROP 字段列**连带丢数据**——生产库卸载前必备份、先 staging 演练。


---

## 6. WhatsApp 架构
- **Meta BSUID 变更（2026+）**：账号功能启用后，webhook 里的 `wa_id` 可能消失，被 `user_id`（BSUID 格式）替代。


---

## 7.Odoo 19 技术约束（踩坑合集）
> 这些是真金白银踩出来的、必须精确复查的约束。

### 权限 / 组
- `res.groups`：**无 `category_id`**；用 `privilege_id` + `res.groups.privilege`；成员用 `user_ids`（不是 `users`）；`implied_ids` 用 `Command.link()`。
- `ir.actions.act_window`：用 `group_ids`（不是 `groups_id`）；优先 `view_id` 直接绑定（而非 `views` 字段）；**无 `target='inline'`**（用 `'current'`）。
- `ir.ui.menu`：record 上**无 `groups_id`**。
- `ir.ui.view`：继承视图 record 上**不能用 `group_ids`**——改用 arch 层 `groups` 属性或计算布尔。
- `ir.cron`：**无 `numbercall`**。

### 模型 / 字段
- `res.partner`：**无 `mobile` 字段**（17+ 移除，只有 `phone`）。
- `stock.valuation.layer`：已废弃；估值并入 `stock.move`。
- `stock_landed_costs` 模型：`stock.landed.cost`、`stock.landed.cost.lines`、`stock.valuation.adjustment.lines`。
- `product.product`：**`attribute_value_ids` 已移除**；用 `product_template_attribute_value_ids`；属性名/值在 `product.template.attribute.value` 上通过 `attribute_id`。
- `account.account` 的 name 是**翻译 JSON**——必须用 ORM `write()`，**不能 SQL UPDATE**。

### API / 调用
- `pricelist._get_products_price(products_recordset, quantity)`——必须传 **recordset**，不是 list。
- `from odoo.modules.registry import Registry`（**不是** `from odoo import registry`）。
- PostgreSQL：事务出错后，**必须先 rollback 再 commit**。
- Cash journal：inbound/outbound 的 Manual 支付方式必须显式添加。

### 部署 / 迁移（Odoo.sh）
- **改容器目录名或 addons_path 结构后，必须先 rebuild 再做任何验收。** Odoo.sh 的 `ADDONS_PATH` env 在 **build 时冻结**；未 rebuild 的容器上模块会全部 `not installable, skipped`——此状态下模块「装着但没加载」、DB 仍留旧记录，**症状伪装成功能 bug**（R20 改名后据此误判过三处）。rebuild 会重扫仓库自愈。
- Odoo.sh 把 repo 根**与「直接含模块的子目录」都**加入 addons_path → 容器目录名本身就是一个 addons_path 段，**不可与官方模块技术名同名**。
- migration 脚本里 **`odoo.upgrade.util` 不一定可用**（非 upgrade 场景未装）；删列/删字段等操作须退回 raw SQL。
- deprecated 字段的「留一轮再删」可以压缩到同轮，前提是：`-u` 会**按版本序**先跑旧版本的 post-migration（拷值保全）再跑新版本的 pre-migration（删列），且确认无外部库停留在更早版本。压缩时须把这个理由写进文档，否则日后会被读成违规。

### 报表 / account_reports（Enterprise）
- `_init_options_buttons` 等**全局 override 不要依赖 `env.company`** 做门控——「默认公司非目标国 + 公司选择器勾了目标国公司」这个组合下 `env.company` 取的是默认公司，会误伤。改依赖对象自身属性（如报表的 `country_id`），company-independent。
- **按钮进主区靠 `always_show:True`，不是 `sequence`**。`buttons_bar.js` 的 `barButtons` 只收 `always_show:true`，其余一律折进齿轮溢出菜单；`sequence` 只管主区内排序。
- 自定义 `account.report` 想要**菜单可达**，设 `root_report_id` 挂成官方报表的变体即可（照抄官方同国变体形态）。若我方 `custom_handler_model_name=False`，变体渲染走自身 `report_id/line_ids`，**官方根报表的 custom handler 不会介入取数**。
- 官方模块 `-u` 后，我方给官方报表**追加的列/表达式存活**；但官方删行/改公式未验。
- 聚合（aggregation）表达式引用的 label 必须真实存在，否则打开报表即 `Could not expand term`。批量生成表达式时守卫要用**不动点迭代**（子行被跳过须向上传播到父行），单趟单层扫描会漏。
- **比较期（comparison）产出的是第二个 `column_group`，不是同组内的额外列。**开启后 `options['columns']` 由 2 变 4（首组=本期、次组=上期），`options['column_groups']` 有序。`_get_lines` 返回的 `line['columns']` 与 `options['columns']` **按位严格 1-1 对齐**（`zip` 安全）。→ 取上期值必须认**列组顺序**，不能按 `expression_label` 匹配（两组共享同名 label 如 `balance`）。**任何「只取 primary column group」的渲染器会静默丢弃全部比较列**——症状是导出件某列整片为空、报不出错。
- **`comparison.filter` 选 `same_last_year` 还是 `previous_period`，年报等价、季报不同。**实测 Q2 2026 下 `previous_period` 取 Q1 2026（上一季度）、`same_last_year` 取 Q2 2025（上年同期）；期间为整年时两者都落上一会计年度。→ 凡「上期/去年同期」语义的场景统一注入 `same_last_year`，一条路径通吃，无需按期间类型分支。`date_scope` 那套（`to_beginning_of_period` / `to_beginning_of_fiscalyear` 等）**没有**「上一个等长期间」的枚举值，此类需求只能走 comparison，离线生成 label 的路子不成立。
- **官方报表里「减：xxx」这类扣减行存的是负值**，所以合计关系是**加不是减**（实测：`减：累计折旧` 行为负 → `账面价值 = 原价 + 累计折旧`）。凡给官方报表做勾稽校验、二次聚合、导出映射，先造数确认每行的存储符号，别照人眼读到的「减」字写减法。同类：某些「其中：」明细行是**备注行、不计入上级合计**，聚合时要排除。

### 会计模型语义
- `_reverse_moves`（红冲/反过账）= 先 `move.copy(default_values)`（`reversed_entry_id` 在 default 里）→ 再 `write({'line_ids': [Command.update(..., {'balance': -balance})]})` 翻符号。**两步**，不是一次性建好。
- 因此：`store=True` + `readonly=False` 的 compute 字段 **`copy` 默认为 True、会带原值**，值被改掉是**后面那个 write 触发重算**导致的，不是 copy 丢值。要保留原值，守卫加在 `write()`/`_compute` 上判 `move_id.reversed_entry_id` 即可，无需行级匹配（Odoo **无 `reversed_line_id`**，行序不是承诺 API）。
- `account.move.line` 的 `debit`/`credit` **非负**：「借方红字」会被自动存成「贷方蓝字」→ 中式红冲的第二常见形态在 Odoo 里无法原样表达，属框架层限制。
- `account.group.parent_id` 是 **`ondelete='cascade'`**——删一个组会级联删掉挂在它下面的组（含用户自建的）。卸载 hook 里删自建组前必须先把幸存组从待删父上摘开。
- `account.partial.reconcile`（核销）**不生成分录**，只建勾稽关系。
- **`account.move.name` 不走 `ir.sequence`，走 `sequence.mixin`**：从上一条记录的名字正则反解格式再推下一条。两个后果：① `_get_last_sequence_domain` **按 journal 过滤**（`WHERE journal_id=…`），Odoo **从不跨 journal 统一编号**；② `_deduce_sequence_number_reset` 的匹配顺序是 monthly → yearly → year_range → fixed，**名字里不含年月就只能中 `fixed`，即 `reset='never'`、永不归零**。要按月归零，年月必须内嵌在名字里。
- 需要「跨 journal 统一 + 按期间归零」的第二套编号（如中式凭证号 `记-1`），**别去改 `move.name`**。`ir.sequence` 自带 `use_date_range` + `ir.sequence.date_range`，可做 (公司 × 类别 × 期间) 三键取号，完全不碰 `move.name`，卸载即删自有列、原生编号不受影响。
- ⚠️ 若该编号会被打印归档，**呈现层动态重排不安全**：回插一条日期靠前的记录会让所有后续号往后挪一位，而已归档的号不可变。这类编号必须落存储字段、取号即定。

### 视图 / 前端
- WhatsApp Discuss channels：是 OWL 组件，**不能 XML field 注入**；用独立自定义 list view。
- `list` view + `editable=bottom`：`decoration-*` 引用的字段必须先声明且带 `column_invisible=1`。
- `_get_whatsapp_channel()`：新 channel 才用 `Command.clear()` + `Command.create()`；responsible user 优先级：`user_id/user_ids` → 关联消息作者 → `create_uid` → `write_uid` → `notify_user_ids`；过滤掉 OdooBot/Superuser/inactive。

---

## 8. 交付验收惯例（跨项目）
> 来源：l10n_cn 线 R23–R25 的界面端到端走查与逐轮复盘。贯穿教训——**程序化验收与界面使用从未对齐**。全部是「历轮验收都通过过、但问题真实存在」的类型。

1. **界面可达性**：凡交付物带界面入口者（报表 / 菜单 / 按钮 / 向导），验收必须包含一次**不用开发者模式、不手敲 URL** 的走查，记录「从登录到看见该功能」的**点击路径与步数**。
   **数值正确 ≠ 用户找得到。**
2. **多公司组合**：凡逻辑读 `env.company` 或依公司属性门控者，须实测「**默认公司非目标公司 + 选择器勾目标公司**」这个组合，不能只测单公司切换。
   **单公司通过 ≠ 多公司通过。**
3. **有序性独立于完整性**：导出件除断言「无缺无重」外，须**单独断言有序**（逐个转 int、单调递增无缺号；两栏对开表左右各自单调）。
   **行次完整 ≠ 行次有序。**
4. **改目录结构后先 rebuild 再验收**（见 §7 部署/迁移）——否则会在「模块没加载」的环境上验收，把环境问题误判成功能 bug。
5. **正确的自检若只写日志，等于没做**：自检发现的问题必须出现在**需要看到它的人**面前。跑在服务端的 WARNING，对着界面点按钮、拿着导出件的人是看不到的——链路上多一道自检、少一道呈现，价值全漏在中间。
   **检查跑了 ≠ 有人看见。**
6. **结构化输出要按三个正交维度分别验**：**① 条目完整且有序**、**② 每个值等于权威来源**、**③ 内部算术自洽**（合计=Σ明细、上下游对平）。三者互不蕴含——尤其当输出是权威来源的**子集**时（有意丢弃了某些条目），②过而③破是常态，且**在测试数据里那些条目恰好为 0 时会静默通过**。
   **值算 0 会掩盖结构问题。**
7. **批量写回操作，「目标端有·来源文件无」的遗留项必须报出让人决定**。静默保留与静默删除同罪——前者让人以为已对齐、后者悄悄毁数据。导入/同步/迁移类动作，结果里要列出未被覆盖的条目清单。
8. **测试环境的「零异常」断言不是对生产环境的承诺**。当某类异常在真实数据里是常态（如「未分类」「未匹配」这种依赖人工打标的桶），要在文档里写死它的作用域，否则将来有人在客户库看到告警会当缺陷去查代码。**fixture 通过 ≠ 生产应当为零。**

---

## 9. 中国财务与税务市场事实（跨项目）
> 取材 2026-08-07：电子税务局界面一手截图 + 多年代账实操口述 + 金蝶星云/星辰导出件。任何面向中国客户的项目都用得上，不限于 l10n_cn 模块线。细节展开见 note 仓库 `l10n_cn_localization_project.md` §4.5。

### 报税的三条数据链，只有两条走账
- **增值税申报** —— 数据来自**发票**（金税 / 全电 / 进项勾选），**不从账簿取数**。用金蝶用友一样不从账取。任何 ERP 都不该把「对接增值税申报」当成本地化功能。
- **企业所得税季度预缴** —— 取利润表的营业收入 / 营业成本 / 利润总额。
- **财务报表报送** —— 报 BS + PL。

### 财务报表报送的实际路径（`verified`，2026-08-08 实测更正）
路径 = 电子税务局 → 我要办税 → 税费申报及缴纳 → **财务报表报送及更正**。三种模式：

| 模式 | 触发条件 | 代价 |
|---|---|---|
| **财报导入** | 🔴 **文件必须是税局官方标准模板的格式**（同 sheet 名、同表头、同列序，填数即可） | 零人工，一键 |
| **财报转换** | 不是模板格式的任何财务软件导出件 | 逐项人工映射（「调整项目」改项目名与月份），数据错了也能改 |
| 在线填写 | 手工 | 全人工 |

🔴 **早前记的「导入器不认厂商、按项目名称匹配、不要求逐格对齐」是错的**。「不认厂商」对——导入器不挑软件；但**认模板格式**，不是模板格式就落到转换、要人工映射。

**对做导出的含义**：目标不是「像官方模板」，而是**就是官方模板格式**。标准模板可从报送流程内下载（不在公开表单下载区，那里放的是纳税申报类表单）。

**模板的结构契约**（税局系统生成，各准则同构）：行0 表名含适用说明 / 行1 末列表号+单位 / **行2 纳税人识别号·纳税人名称** / **行3 所属期起·所属期止** / 行4 列头（**项目在前、行次在后**；双栏对开表两栏之间**无空隔列**）/ 行5+ 数据行，节标题行行次留空。**那四个元数据格是导入器定位纳税人与所属期的依据，最容易被外部软件的导出件漏掉。**

### 报送期间是列口径维度，不只是选期间（`verified`）
标准模板分**月季报**与**年报**两个文件，**资产负债表两版相同，利润表与现金流量表的列不同**：月季报 = 本期金额 \| 本年累计金额；年报 = **本年累计金额 \| 上年金额**。sheet 名也带期间（`利润表_月季报` / `利润表_年`）。
→ 做报送版式时，form 的枚举维度至少三维：**会计准则/企业类型 × 准则版本开关 × 报送期间**。只做月季报会漏掉每年必报的年报版。

### 应报哪几张表由「备案报告」决定（`verified`，界面原文）
报送页的报表列表**由《财务会计制度及核算软件备案报告》带出**，界面原文：「以上财报列表通过备案报告数据带出，如想修改本属期备案报告，需先联系主管税务机关**作废已填报的财报报表**」。

**《财务会计制度及核算软件备案报告》是什么**（`observed`，各省电子税务局界面组织略有差异）：企业设立或会计制度/核算软件变更时向主管税务机关报送的备案事项，路径通常在 **我要办税 → 综合信息报告 → 制度信息报告** 下。内容含所采用的会计制度类型、记账本位币、主要会计政策（折旧方法、存货计价、成本核算办法等），以及**是否使用计算机记账、财务核算软件名称/版本/开发单位**。税局据此判定该纳税人应报哪套财务报表与哪几张表。

两个后果：
- **「某张表要不要报」是客户属性，不是产品属性**。同一准则下，A 公司报三张、B 公司报两张，取决于各自备案。别把某张表判成「行业普遍不报」就降优先级。
- 🔴 **非国内备案软件如何填「核算软件」栏 = 未解，且比版式更前置**。备案填不了，版式再对也没用。接中国客户前必须确认。

⚠️ **提交有代价**：改本属期备案须先作废已填报的财报报表。→ 测试类操作**走到导入预览为止，不点「提交申报」**。
### 表样是枚举的，不是一张（`verified`）
维度 = **报送期间（月季报 / 年报）× 报送小类（会计制度 + 企业类型）× 准则版本开关（部分准则有）**。三维都影响表样：期间影响**列口径**（见上），小类与版本影响**行集合与行名**。做本地化报送功能时按三维枚举 form，别按「一个准则一套表」设计。

部分准则的报送小类还带**准则版本开关**（如企业会计准则一般企业分「已执行/未执行新金融·新收入·新租赁准则」），同一套报表项目库靠标签过滤切换名称，不是多套模板。

### 账是主、业务是从（形态根因，`observed`）
从业者原话：**「账必须做对，业务可以迁就」**。这一条解释了中国企业软件为什么普遍重财税——不是功能取舍，是入口方向的差别：

| | 起点 | 结果 |
|---|---|---|
| Odoo 系 | 业务单据驱动，会计是业务的副产品 | 业务顺、账要迁就 |
| 用友 / 金蝶系 | 账驱动，业务模块服务于出账 | 账严密、业务要迁就 |

注意：中国**不缺**全流程 ERP（用友 U9/YonSuite、金蝶云星空、浪潮都带制造供应链）。差别不在覆盖度，在设计哲学。做中国市场时，「业务做得好」不足以说服财务部门。

### 增值税不是账的切片，是另一个事实源（`observed`）
凭证 / 账簿 / 报表 = 同一套数据的三个切片（事件 → 按科目重排 → 按报送口径聚合）。**增值税不在这套里。**
- 中国以票控税：应缴增值税以**发票**为准 —— 销项 = 金税系统实际开具的发票，进项 = 在发票综合服务平台**勾选认证过**的发票。
- 开票时点 ≠ 收入确认时点；未开票收入要单独申报，已开票未确认收入也要申报；进项能不能抵取决于勾没勾选，与账上记没记无关。
- 结果：账上「应交税费—应交增值税」与申报表**经常不等**，差异要专门做台账对账。**该科目是对账点，不是申报的数据来源。**

### 税务发票 ≠ 商业单据（`observed`）
ERP 里的 customer invoice / vendor bill 是**商业单据**；中国的「发票」是**税务发票**，有税局赋的发票代码与号码，必须经金税或电子发票服务平台开具。一张商业单据可能对应 0 张、1 张或多张税务发票；ERP 自己生成的 PDF 不是发票。
→ 要让 ERP 对增值税有用，缺的是一层**税务发票登记与勾稽**（代码/号码/认证状态字段 + 与平台的导入导出 + 账票差异台账）。这是中国 ERP 里与业务耦合最紧的一块。

### 报税上传没有对第三方 ERP 开放的接口（`observed`）
税局、社保的申报接口不对一般 ERP 开放（仅特定服务商）。**任何 ERP 在中国都只能做到「出数据 + 人工/半自动上传」**，用友金蝶的客户同样如此。分界线是数据在谁手里：

| 层 | 在哪 | ERP 能否包 |
|---|---|---|
| 账 + 凭证 + 账簿 + 报表 | ERP | ✅ |
| 薪酬计算 | ERP（需本地化） | ✅ |
| 发票开具与进项认证 | 税局平台 | ❌ 只能对接 |
| 报税上传 | 电子税务局 | ❌ 只能导出 |
| 社保申报 | 社保网厅 | ❌ 只能导出 |

### 记账凭证字实务（`observed`，待一手确认）
中国企业现在**绝大多数只用「记」一种通用记账凭证字**；「收 / 付 / 转」是手工账时代分开装订的老做法，电算化后基本不用。
→ 做凭证字功能时，「按单据类型自动推导凭证字」多半是过度设计；更贴实际的是**给一个可配字段、默认全填「记」**，客户要分才分。

### 公开的完整中国本地化方案基本不存在（`observed`）
Odoo 侧：OCA 的 l10n-china 很薄；真正做过完整本地化的中国伙伴，方案都是自家资产、不发布。**本地化本身就是护城河，所以没人开源。**找不到参照不代表没人做过，代表做过的人不给看。

### ~~现金流量表不参与报送~~ —— 已改写（2026-08-08）
原记「季报年报都不传」。**实测更正**：官方标准模板**含现金流量表**（月季报/年报各一张 sheet）；某企业的报送列表里没有它，是因为**其备案报告没带出这张表**，不是税局一律不收。
→ 正确表述：**现金流量表是否报送取决于客户备案。**多年代账观察到的「从没传过」成立，但原因是备案，不是税种规则。**别据此判定 CF 功能对报税非必需。**

### 存量账套至少三套科目编码并存
| 体系 | 指纹 |
|---|---|
| 《企业会计制度》/《小企业会计制度》（旧） | 1131 应收账款 / 3131 本年利润 / 5101 主营业务收入 |
| ASSBE 小企业会计准则 | 3001 实收资本 / 4001 生产成本 / 5001 主营业务收入 |
| ASBE 企业会计准则 | 4001 实收资本 / 5001 生产成本 / 6001 主营业务收入 |

接存量客户**必须先验编码体系**，不能默认准则编码。代账实操中报送是**按项目名称手填**（同一编号在不同行业名称不同）——**报表行名必须与税局表样逐字一致，科目编码反而是可各家不同的中介**。

---

