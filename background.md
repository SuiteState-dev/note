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

### 会计模型语义
- `_reverse_moves`（红冲/反过账）= 先 `move.copy(default_values)`（`reversed_entry_id` 在 default 里）→ 再 `write({'line_ids': [Command.update(..., {'balance': -balance})]})` 翻符号。**两步**，不是一次性建好。
- 因此：`store=True` + `readonly=False` 的 compute 字段 **`copy` 默认为 True、会带原值**，值被改掉是**后面那个 write 触发重算**导致的，不是 copy 丢值。要保留原值，守卫加在 `write()`/`_compute` 上判 `move_id.reversed_entry_id` 即可，无需行级匹配（Odoo **无 `reversed_line_id`**，行序不是承诺 API）。
- `account.move.line` 的 `debit`/`credit` **非负**：「借方红字」会被自动存成「贷方蓝字」→ 中式红冲的第二常见形态在 Odoo 里无法原样表达，属框架层限制。
- `account.group.parent_id` 是 **`ondelete='cascade'`**——删一个组会级联删掉挂在它下面的组（含用户自建的）。卸载 hook 里删自建组前必须先把幸存组从待删父上摘开。
- `account.partial.reconcile`（核销）**不生成分录**，只建勾稽关系。

### 视图 / 前端
- WhatsApp Discuss channels：是 OWL 组件，**不能 XML field 注入**；用独立自定义 list view。
- `list` view + `editable=bottom`：`decoration-*` 引用的字段必须先声明且带 `column_invisible=1`。
- `_get_whatsapp_channel()`：新 channel 才用 `Command.clear()` + `Command.create()`；responsible user 优先级：`user_id/user_ids` → 关联消息作者 → `create_uid` → `write_uid` → `notify_user_ids`；过滤掉 OdooBot/Superuser/inactive。

---

## 8. 交付验收惯例（跨项目）
> 来源：l10n_cn 线 R23 的界面端到端走查。贯穿教训——**程序化验收与界面使用从未对齐**。三条都是「历轮验收都通过过、但问题真实存在」的类型。

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

---

## 9. 中国财务与税务市场事实（跨项目）
> 取材 2026-08-07：电子税务局界面一手截图 + 多年代账实操口述 + 金蝶星云/星辰导出件。任何面向中国客户的项目都用得上，不限于 l10n_cn 模块线。细节展开见 note 仓库 `l10n_cn_localization_project.md` §4.5。

### 报税的三条数据链，只有两条走账
- **增值税申报** —— 数据来自**发票**（金税 / 全电 / 进项勾选），**不从账簿取数**。用金蝶用友一样不从账取。任何 ERP 都不该把「对接增值税申报」当成本地化功能。
- **企业所得税季度预缴** —— 取利润表的营业收入 / 营业成本 / 利润总额。
- **财务报表报送** —— 报 BS + PL。

### 财务报表报送的实际路径
路径 = 电子税务局 → 我要办税 → 税费申报及缴纳 → **财务报表报送及更正**。三种模式：
- **财报导入**：导入**标准模板表单**。**软件中立** —— 导入器不认厂商，按表样结构/项目名称匹配。**这是非国产财务软件唯一能走的路，而且它走得通**（实操：财务软件导出的 xlsx 直接上传即可）。
- **财报转换**：转换特定财务软件导出的报表。认厂商格式。
- **在线填写**：手工填。

**结论：中国企业用非国产 ERP 做账并自行报税，在报送环节没有技术门槛** —— 只要能导出符合表样的 xlsx。

### 表样是枚举的，不是一张
维度 = **报送期间（季报 / 年报）× 报送小类（会计制度 + 企业类型，如「企业会计准则一般企业」）× 是否已执行新金融·新收入·新租赁准则**。同一套报表项目库靠标签过滤切换，不是多套模板。

另需先完成**「财务会计制度及核算软件备案」**，系统据此自动带出应报的表种。非国内备案软件如何填这一栏 = **未解，接中国客户前须确认**。

### 现金流量表不参与报送（`observed`，多年代账实操）
季报年报都不传。与部分省级操作指引的文字表述不符，以实操为准。
→ 现金流量表功能对「客户能不能报税」不构成门槛，其价值在内部管理与稽查备查。

### 存量账套至少三套科目编码并存
| 体系 | 指纹 |
|---|---|
| 《企业会计制度》/《小企业会计制度》（旧） | 1131 应收账款 / 3131 本年利润 / 5101 主营业务收入 |
| ASSBE 小企业会计准则 | 3001 实收资本 / 4001 生产成本 / 5001 主营业务收入 |
| ASBE 企业会计准则 | 4001 实收资本 / 5001 生产成本 / 6001 主营业务收入 |

接存量客户**必须先验编码体系**，不能默认准则编码。代账实操中报送是**按项目名称手填**（同一编号在不同行业名称不同）——**报表行名必须与税局表样逐字一致，科目编码反而是可各家不同的中介**。

---

