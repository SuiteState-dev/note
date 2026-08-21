## 0. 快速导航

> **本档版本：2026-08-21 v34**（R54 中途）：§8 五处 —— **惯例 12 落法扩写**（🔴 **凡用「包含」代替「相等」的判定，其计数一律不作数**；`join` 未排序静默丢行 / `expected in xml_text` 子串假匹配，**两例同族，且后者工具全程不吭声**）；**惯例 26 补对版双锚**（🔴 **其中一条必须不依赖任何文档**）；**惯例 27 补跨窗口轮次须留【中途状态】**（判据：新窗口只读 `status` 能否接着跑）；**惯例 33 补第四例 —— 据【名字】推实现**（`_cn_direction_by_code` 查表却像在推导）；**惯例 13 补一例 —— 工单未指向已有登记处，导致重推三条**。
>
> **以下为 v33 原记：**
> **本档版本：2026-08-20 v33**（R53 结项）：§8 **惯例 30 新增子形态 (c)** —— 🔴 **跨源/跨路径核对的注入，必须注在【真实模型侧】并各自重算两源；注在读出来之后的中间变量上是【假检出】** —— 绿灯是真绿的，只是绿错了地方，它只证明「断言会响」，不证明「那条链是通的」。**本条不是本项目特有，任何两条路径对账的测试都可能这么错。**§7 **B-80 补一条时点差**：改 `stock.move.value` **不回溯已过账 `aml`** ⇒ 两源之间存在**时点差**，不只是路径差。
>
> **以下为 v32 原记：**
> **本档版本：2026-08-20 v32**（R52 结项）：§7 新增 **B-80** —— 🔴 **Odoo 19 已移除 `stock.valuation.layer`**（→ `stock.move.quantity`/`value` + `product.value`），且 `perpetual` 下 `_action_done()` 后 `account_move_id = None` ⇒ **移动完成那一刻会计分录尚不存在**；另 `account.move.line.quantity` 在 `display_type='product'` 下**恒占位 `1.0`** —— **占位比为空更危险**。§8 **惯例 25 补一例**（问句措辞决定答句适用面：「都是一样的呀」）；**惯例 29 ⑥ 由悬项转已闭**（总账第 2 页到手，落点关系完整）。
>
> **以下为 v31 原记：**
> **本档版本：2026-08-19 v31 —— 第二次推送，覆盖同版本号。** 🔴 **首推版有一处结论错误，已订正**：「明细账公司名入表头」系 note 侧由总账类推得出，实为**每页页脚**（依据 `kingdee_materials/kingdee_subledger_3col_export_wanjia_1002.png`）。本次另补三处：**惯例 27** 加 raw CDN 陈旧副本的判别落法（看 `x-cache` / `source-age` 响应头，并列出三种无效的绕缓存做法）；**惯例 29** 补**第六形态**（同一载体内的**表间差**：总账公司名在表头、明细账在页脚）；**惯例 33** 补**两例 note 侧自犯**，三例共同形状 = **有直接观测在手却选了推理**。Safi 判定本版本号未被下游工单消费，故覆盖同号、不烧新号。
>
> **以下为 v31 首推原记：**
> **本档版本：2026-08-18 v31**（§8 **惯例 17 补第四条 —— 几格参与数相同有三种成因，必须答是哪一种**：R51 判据 2/3/5/6 同为 7 是**同一批 period-row 被四条判据各验一遍**（合法，正是覆盖面的证据），而同轮判据 4 的 7 却是**两个强弱不等的口径被加号合并**（真实跨期转移 3 + 首期基线 4）。⇒ 三选一落法入表；并收一格：**判据表的参与格应直接贴断言输出那一行，手写转录这个动作本身就是缺陷面**。附**正面实例**：本次三格非数字被指出后，执行方当场以 in-tx 探针重取真值、自陈根因、同轮回写 design 注明纠错 —— **判据只有在被指出后能当场重取真值时，才算可执行**。）
> **本档版本：2026-08-18 v30**（§8 **惯例 17 第三条补第二例 —— 立条者同日自犯**：note 侧在 R50 施工单里写「原件 9 个科目」，实为**凭印象估的**；回数原件为 **≥10 且共 2 页、第 2 页未见**。该错被执行方原样引用、又被 note 侧写进 `status` 待办。⇒ 补一条落法：**凡「原件上有 N 个 X」这类计数，必须在同一句里写明是【数过】还是【估的】，估的一律写「约」并标未数。**）
> **本档版本：2026-08-18 v29**（吸收 l10n_cn R50 返工轮：§7 **B-78 补第二实例**（直连 raw SQL 前缺 `flush_all` —— 与币表同一形态，**同一条一般化在两轮内被撞了两次**，故把「要补什么」列成清单）；§8 **惯例 14 补第三实例并订正措辞**（R49 定的「同源一致性检验」**用词过窄** —— 该判据实际抓到了真 bug，因为两条路径**并非全同源**，改称「**跨路径差量检验**」；附执行方给出的信任校准句）；**惯例 17 补第三条**（🔴 **回报摘要里的实数必须从断言的实际输出誊抄，不得凭印象填** —— 假数比没数更坏）；**惯例 27 补一条落法**（施工单声明所依赖的**文档版本**，回报**回显**版本号，首次使用即见效）；**新增惯例 34**（🔴 **向执行方提封闭选项题时，必须留「以上皆非」那一格** —— 选项集本身是下单方的推断）。）
> **本档版本：2026-08-18 v28**（§8 **惯例 12 补第四变体**：**他方的演示 / 试用账套，数据与配置都被改过** —— 不只金额不可信，**报表公式、行项目增删也被改过**，据其推行集 / 行次 / 列序会系统性偏移。实例：金蝶「通用行业（旗舰版）」ASSBE 资产负债表导出件，表不平 869,459.00、「短期借款」被配进「货币资金」、负债侧缺「短期借款」行致行次整体 +1、列序与准则相反。）
> **本档版本：2026-08-18 v27**（吸收 l10n_cn R49 证伪轮：§8 新增 **惯例 33**（🔴 **从法源 / 原文推出的那句「因此……」是我方的推断，不是原文本身，不得用它压过原件观测** —— 实例：从「无余额的写『平』」推出「方向必是余额的函数」，据此否掉了与原件一致的方案，错裁决进了两份档）；**惯例 29 补第五条实例**（**他方原件也分载体** —— 同一张表的打印模板与导出件列集不同，一轮里拿到三个实例；29 前四条管我方输出的载体，本条管我方读入的载体）。）
> **本档版本：2026-08-17 v26**（吸收 l10n_cn R49 中式总分类账轮：§7 新增 **B-78**（`_init_currency_table` 显式幂等、多入口自建安全）与 **B-79**（`totals_below_sections` 会在**有子行的 section 下自动插一条合计行** ⇒ 账簿类报表须用扁平行规避）；§8 新增 **惯例 32**（**「我方没有 X」与「我方有 X」同为断言，同样要举证** —— 与惯例 28 互为镜像：28 管「说有其实没有」，32 管「说没有其实有」）；**惯例 14 补一条实例**（**同源、构造必等的两表比对不是互证**，写成「互证」会把弱证据当强证据往上堆）；**惯例 17 补一句**（正向哨兵 `>0` **不能代替**实数计数，两条惯例不可互相顶替）。）
> **本档版本：2026-08-17 v25**（§8 **惯例 29 补第四条实例**：**载体覆盖过头** —— 与第三条「覆盖不足」成对，同一个病根：**没分清「谁拿去用」和「谁要看」**。自查四问 → **五问**，新增一问：这个载体**还会被谁看到**？）
> **本档版本：2026-08-16 v24**（§8 新增 **惯例 31**：**禁令要写清对象，不要写成禁手段。**「不改写官方逻辑」≠「不使用官方提供的扩展点」——手段是中性的，官方自己也在用。与惯例 29 是同一堵墙的两个面。）
> **本档版本：2026-08-16 v23**（§8 **惯例 30 补子形态 (b)**：**检测器 / 哨兵类测试必须自带「注入 → 检出」那半**，只验「没抓到」等于什么都没验。第三次撞同一堵墙——R43 撞号哨兵做到了，R44 悬空检测没做到，R46 补上。）
> **本档版本：2026-08-15 v22**（§8 新增 **惯例 30**：**测试通过 ≠ 被测路径执行过** —— 断言类测试须先断言被测路径确实跑到了，否则前置条件一变就静默空绿。实例：`TestCoaPublish` 8 条用例因 `zh_CN` 未激活被语言门整批拒绝，长期显示通过而从未发行过一条科目。）
> **本档版本：2026-08-15 v21**（§7 新增 **B-77**：我方记录挂官方共享表 —— 子记录归我方 module，官方 `-u` 的 stale-cleanup 按 `ir_model_data.module` 键、**不删不改**；唯一耦合是 FK 指向那条官方记录。§8 **惯例 29 补第三条实例**：同一份数据有两条渲染/导出路径时，只加在其中一条上等于没送到，且**测试全绿**。）
> **本档版本：2026-08-14 v20**（§8 新增 **惯例 29**：告警/提示类交付，交付前须确认「载体的可见人群」与「问题的相关人群」相交。）
> **本档版本：2026-08-14 v19**（§8 新增 **惯例 28**：档里写「材料已制备/已到位」必须同时给仓库路径 + raw 链接，给不出路径的一律写「尚未制备」。）
> **本档版本：2026-08-14 v18**（吸收 l10n_cn R43 交付：§7 **B-73 表格标签订正**（驱动变量是纳税人档、非 chart）、**B-76** 落定（推了代码 ≠ 跑着新代码）、**新增 88 撞号陷阱**（`cn_common` 88 与我方通用发行件 88 数字相同、毫不相干）；§8 新增 **惯例 26**（取证须带被测库实际模块版本号）。）
> **本档版本：2026-08-14 v17**（吸收 l10n_cn R42 后二姐两批反馈 + 两库全量科目表实测：§7 新增 **B-72**（Odoo `account_type` 中文标签非中国会计要素术语，且已造成一次实际误判）、**B-73**（认领按 `code` 匹配 ⇒ 明细层编码形态不一致时认领**结构性失效**，实证同义重复 15/25 条）、**B-74**（官方 chart 含已废止/已被取代的历史科目）、**B-75**（归档动作的样本边界）；§7 会计模型语义段 **「借方红字存成贷方蓝字」降为「不适用」**（实务口径：电算化下无红字）。§8 补编 **惯例 23**（事后推断的成因须标 `observed`）、新增 **惯例 24**（验收判据下发前须自查可达性）与 **惯例 25**（向领域专家提问时凡含平台技术字段名须写明该字段作用，**本轮已兑现一次完整闭环**）。）
> **本档版本：2026-08-13 v16**（吸收 l10n_cn R41 存量库活体轮：§7 🔴 **B-68 补活体实测段** —— 我方发行的**两条路径落库不同**（`post_init` 落**单键**、wizard 落**双键**），差别在 `env.lang` 有无 UI 语境，**源码读不出来**；官方 chart 在**正序**（先语言后科目表）下双键正常（`verified`），**反序仍未复现**；**B-67 全链升 `verified`**（2.1.0 → 2.4.0 跨三个 migration 真实升级路径实测，八条公式同步到位、无半应用）；新增 **B-71**（Odoo.sh staging 推 commit = **保留数据库、重建容器** —— 与官方文档「每次推送创建生产库新副本」不符，`/tmp` 类产物会丢）。§8 新增 **惯例 21**（`observed` 的采纳门槛随结论方向不对称）与 **惯例 22**（待办条目必须自带可执行内容，只有指针没有内容的条目不得进待办档）。）
> **本档版本：2026-08-13 v15**（吸收 l10n_cn R37 测量轮：§7 🔴 **B-68 整条改写** —— 原设问「落 `zh_CN` 还是回落 `en_US`」有**第三种真相**：未激活语言的 context **直接硬报错**，既不落也不回落；真正的暴露面是**以默认 context 建记录 ⇒ 只有 `en_US` 单键**，而若该串是中文则界面回落显示正常、**肉眼查不出**；**B-69 补两个吸收口**（`5\(53)` 营业成本 + **裸前缀 `-5`** 往年未分配），受害科目实为**六个**不是一个。§8 新增 **惯例 19**（验收判据必须写绝对终态、不得写"改善量"）与 **惯例 20**（顺序依赖类问题必须复现顺序，查"当前状态"答不了）。）
> **本档版本：2026-08-13 v14**（吸收 l10n_cn R36 缺陷 #2 修复轮：§7 **B-67 升 `verified`** 并补出**两条加载路径的分野**（XML `data`+`noupdate="0"` **随 `-u` 重载** vs `post_init_hook` **不随 `-u` 重跑**）；新增 **B-69**（ASBE 报表 `5\(53)` 把 `5001 生产成本` 立即费用化 ⇒ **存货变负数 + 成本高估、`30=53` 不破、守卫抓不到**，与 B-60 的「漏计」是**两种机制**）；新增 **B-70**（报表 variant 可达性两条规则：**root 通用版恒可达**、**兄弟 variant 受 `availability_condition` 相互隔离**）；§8 新增 **惯例 18**（一组数据被拆到两条加载路径时，先问它们是否必须同步 —— **部分重放比完全不重放更坏**）。）
> **本档版本：2026-08-13 v13**（吸收 l10n_cn R35 staging 首次真装走查：§7 新增 **B-68**（**翻译型字段在 create 时冻结，后装语言不回溯** —— 同一根因下有三个症状：官方 chart 先装后加中文则永久英文、我方 `post_init` 把中文写进 `en_US`、同一份数据经两条路径落库不一致）；§8 **惯例 17 补一句**（平铺之后要追问「异质列是否意味着机制该分叉」）。**一条改变判断的 nuance**：「外显程度高」在本体系里是**减分项不是加分项** —— 看得见的错会被投诉，看不见的错会进报表，修复排序应按 `概率 × 严重度 × 静默度`，不按显眼程度。）
> **本档版本：2026-08-11 v12**（吸收 l10n_cn R34 脱钩前置探查 + 原值哨兵轮：§7 **B-65 补第二次事故**（同一条表达式被两种机制各漏一次 —— 检索方法是一层，**计数表述本身是独立的另一层**）、新增 **B-66**（`_register` 为框架保留布尔属性，自定义方法撞名即 `TypeError`）、新增 **B-67**（`post_init_hook` 不随 `-u` 重跑 ⇒ 对官方记录的外科覆盖在升级路径上**不重放**，`observed` 待受控实测）；§8 新增**惯例 17**（计数表述必须平铺、禁乘法式）。**一条改变判断的 nuance**：官方按 `account_type` 的通用报表在 CN 公司上**仍可达**（variant 下拉可切）⇒「客户默认看不到按型版」成立、但「客户看不到」**不成立**；一个库里两张表两个答案**今天就存在**，不是脱钩才引入的。）
> **本档版本：2026-08-11 v11**（吸收 R33-A 自发 ASSBE 科目表交付 + 电子税务局外部验证轮：§7 新增 **B-65**（核报表公式覆盖面须逐条 ORM 遍历、不得依赖文本检索）、**B-60 就地收窄**（ASSBE 侧已修、ASBE 侧仍在，且作废 `R30-P3 ②`）；§9 新增「财务报表报送的校验与差异」六条实测。**一条改变判断的 nuance**：电子税务局对财报做**跨表**校验（利润表 ↔ 所得税预缴 ↔ 增值税申报），但差异**可以是准则性必然差异**（固定资产处置），处置 = 上传情况说明，不是把账改成一致。）
> **v9**（吸收 l10n_cn R31 v20 源码定位轮 + R32 dev 库实测轮：§7 新增 **B-63**（多公司共享账户 + 本公司 code 缺失时 `account_codes` 引擎跨公司兜底 → 前缀吃入 → **静默错报**，`verified`）；**B-54/55/58/59 各补 v20 版本锚**（`sum_if_pos`/`sum_if_neg`/`count_rows` 在 v20 已删、`account.group` 已删、D/C 与前缀匹配保留、报表引擎方法全改名）；§8 新增 **惯例 15**（grep 前先确认工作树完整）、**惯例 16**（官方先例证明「当下认可」不证明「稳定」），**惯例 12 补第三变体**（渲染语言造成的假 0）；🔴 **B-54 前提订正**：`code` 非公司无关单值，按 root 公司存于 `code_store`）
> **本档版本：2026-08-10 v8**（🔴 **B-60 收窄**：缺陷不是「编码体系错配」而是「在产品 vs 生产成本的 WIP 建模错配」——Odoo 的 ASBE 模板 `cn_large_bis` 与财政部 ASBE 码是对齐的；§7 新增 **B-62**（2017 后新增科目无权威码 + 前缀匹配的碰撞面大于逐码对照））
> v7（§7 新增 **B-60**（`l10n_cn` chart 的 1406/4001 双轨 = 西式 WIP 模型与中国成本模型错配）、**B-61**（同事务新建 `account.account` 未 flush 引擎取不到）；**B-55 补第四条锚**（D/C 与 `sum_if_pos` 两套机制不可互推）；§8 新增**第 14 条**（弱证据组必须自带标签）。🔴 **编号事故留痕**：design draft-36 §17.4 曾把 R30-T2b 交付挂到 **B-59**，与本档 v6 已占用的 B-59（subformula 引擎归属）**撞号**；且 T2-b 的报表公式属中国口径、home 在项目档 §4.5.12，不入本档。T2-b **不占新号**，其跨项目部分并入 B-55 第四条锚）
> v6（§7 新增 **B-53 ~ B-59**：lock date 留痕 / `account.account` 19.0 扁平+v20 版本锚 / `account_codes` D-C 三条边界 / `ir.sequence` 三键取号 / `account_type` 静默继承 / `sum_if_pos`-`-sum_if_neg` 符号分流 / subformula 引擎归属）
> v5（命名规矩：「和界鸿源」只用于真实实体在电子税务局侧的实测；开发库事实一律称「dev 库」—— 详见项目档 §0.2）
> v4（§7 B-47~B-52 补「R17-C1 旧结论不完整」的溯源；§8 第 12 条「查到 0 ≠ 真为 0」+ 第 13 条「实测事实必须落主题索引，流水账不是索引」）
> v2（§8 加第 11 条「入口可见 ≠ 入口可用」；§9 「报税上传」节升级为「申报侧不存在直连」并拆开三条通道、备案节补法条与产品结论、新增「中国会计软件的法定功能规范」、凭证字实务升 `verified`）

1. 商业与品牌架构
2. 基础设施与开发工作流
3. SuiteState项目简要
4. 已发布apps.odoo  / 内部模块清单（**⚠️ 截止2026 JUL**）
5. Apps Store 发布规则
6. WhatsApp 架构
7. Odoo 19 技术约束（踩坑合集）—— 含 **B-47 ~ B-62**
8. 交付验收惯例（跨项目）
9. 中国财务与税务市场事实（跨项目）


---

## 1. 商业与品牌架构
- **ElectroState FZCO**: UAE自贸区法律实体，主业 B2B 二手手机批发,已完成odoo.sh部署; 并作为 SuiteState 的挂靠法律实体(在营业执照上增加 IT 类目).
- **SuiteState**: 作为商号（trade name）运行，主打 Odoo 咨询与模块开发。以公司”深圳市和界鸿源科技有限公司“主体注册为odoo中国区合作伙伴；
- **其他业务**：加拿大分公司主要负责采购；计划承接B2B业务的零售流量搭建odoo2的B2C业务系统。

---


## 2.基础设施与开发工作流
- **VPS**：Vultr Tokyo(24$/月 2 vCPU/4GB RAM + 100GB）；Reserved IP。用作 Claude Code 工作站 + 在中国时的网络出口。部署了odoo19社区版作为B2C的业务系统。
2026-07-25 VPS Odoo Community 已 systemctl disable（主动停用，非故障）
恢复：sudo systemctl enable --now odoo
Nginx 反代配置保留，停用期间访问 erp.suitestate.com 返回 502 属正常

- **开发工作流**：本地VS code → git push → odoo.sh生产分支。

- **DB1（主库）**：ElectroState B2B 主业务 odoo.sh19.
- **DB2（VPS）**：B2C 零售为主(未完成) odoo.19社区版.


---

## 3. SuiteState项目简要
- **定位——填平 IT 与客户之间的双重信息差**：IT 方常不懂客户实际业务；客户不懂技术、无法判断方案是否最优；而两边通常都缺乏对 Odoo 的深度理解。SuiteState 的差异化正在于对 Odoo 产品本身的深挖——做模块时多次发现自己的方案思路整个 apps.odoo 上都没有、经多方评估仍更优，反证了多数开发者并未真正吃透 Odoo。核心价值：懂业务、懂技术、更懂 Odoo，公平定价、方案以客户最优为准。
- **商标**：在UAE以 Safi 个人名义申请，中国以"和界鸿源科技有限公司"为主体注册。
- **品牌视觉**：Mint Logo `#10A08C`、Deep `#088071`。
- **基础设施**：GitHub org `github.com/SuiteState`（monorepo，含 community 分支）；开发者账号 `suitestate-dev`；网站 `suitestate.com`（GitHub Pages + Cloudflare）；邮箱 `Hello@suitestate.com`；Lark邮箱服务。

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

🔴 **v20 锚（`observed`，`odoo/enterprise@d2368c8b6fe`，2026-08-10；本组随 20.0 发布须重核）**：
- **line / column 由 dict 改为 `@dataclass(slots=True)` 对象**（`account_reports/utils/report_data_objects.py`，19.0 无此目录）；`column_group_key`(str) → `column_group_index`(int)，`options['column_groups']` 由 dict 改为**按整数下标访问的 list**。1-1 对齐**保留**，但 `line['columns']` / `column['no_format']` 这类**按 dict 读写的代码会直接抛异常**（引入 `odoo/enterprise@db5cef786049`，2026-05-22）。
- **官方 XLSX 按钮的 `always_show` 由 `True` 翻为 `False`**（默认收进齿轮菜单），按钮名 `PDF` → `Print`；`always_show` **机制本身未变** ⇒ 我方按钮显式带 `always_show: True` 仍在主区。
- `_init_options_buttons` / `dispatch_report_action` / `export_file` / `export_to_xlsx` / `xlsxwriter` / `root_report_id` / custom_handler 回落 —— **签名与语义均未变**。
- 二进制字段赋值 `base64.b64encode(...)` → `BinaryBytes(...)`（全局改动，官方给了 `odoo/upgrade_code/19.3-00-base64-in-xml.py`）。
- 报表引擎方法全部改名 + 掉 3 参、`sum_if_pos`/`sum_if_neg`/`count_rows` 删除，见 B-58 / B-59。

### 会计模型语义
- `_reverse_moves`（红冲/反过账）= 先 `move.copy(default_values)`（`reversed_entry_id` 在 default 里）→ 再 `write({'line_ids': [Command.update(..., {'balance': -balance})]})` 翻符号。**两步**，不是一次性建好。
- 因此：`store=True` + `readonly=False` 的 compute 字段 **`copy` 默认为 True、会带原值**，值被改掉是**后面那个 write 触发重算**导致的，不是 copy 丢值。要保留原值，守卫加在 `write()`/`_compute` 上判 `move_id.reversed_entry_id` 即可，无需行级匹配（Odoo **无 `reversed_line_id`**，行序不是承诺 API）。
- `account.move.line` 的 `debit`/`credit` **非负**：「借方红字」会被自动存成「贷方蓝字」→ 中式红冲的第二常见形态在 Odoo 里无法原样表达，属框架层限制。🟢 **R42 后降为「不适用」，不再作为待补缺口挂着**：从业者口径（`observed`，单人样本）「红字是手工登记账的标识」「现在没有手工帐啦」「没红字」⇒ 红字是**纸质账时代的方向标识手段**，电算化下本就不需要还原。⇒ 连带 `缺陷 #5` 中文大写形态定案：**取绝对值、方向由借贷栏承载、不做红字**（与 R36 已交付实现一致，零代码改动）。
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

### Odoo 19 合规机制边界（`verified`，源码 + live 复证，2026-08-08）
> 来源：l10n_cn R27-T2-A 只读实测（源码 + live 复证）。任何中国/欧盟合规项目会重复问同一批问题，故进 background。
>
> ⚠️ **溯源**：本组事实中的「哈希挡改删」「`hard_lock_date` 不可逆」，**R17（三个窗口前）的 C1/C3 已实测过**，但只落在开发分支变更记录里、无主题索引，导致 R27 重推。**重推纠正了一条错**：C1 的「删除 BLOCKED」是全称表述，实际删除靠 `restrictive_audit_trail` 且中国可关（B-49）；C1 也没给字段全集，漏了 B-47 的币种/汇率缺口。→ **一条只覆盖部分字段的实测，不要写成全称结论。**

- **B-47 哈希链的确切保护面**：机制 = `account.journal.restrict_mode_hash_table`（Boolean，**默认关**，Journal→Advanced Settings，`account.group_account_readonly` 可见，不需开发者模式）。保护字段 = move 级 `name/date/journal_id/company_id` + line 级 `name/debit/credit/account_id/partner_id`，改则 `UserError`。🔴 **`currency_id` / `amount_currency` 不在保护面**（多币种主体的事后篡改哈希不拦；同币种行受 "entry not balanced" 平衡约束挡，非哈希挡）。
- **B-48 哈希开启不可逆（安全方向）**：journal 一旦有任一哈希分录，`restrict_mode_hash_table` 改不回 False（`UserError: You cannot modify the field … of a journal that already has accounting entries`）。→ 可对外声明「启用后不可关闭」，**没有"可逆无留痕"漏洞**。
- **B-49 「不可删除」不靠哈希，靠审计追踪，且中国可逆**：判据 = `move.posted_before AND company.restrictive_audit_trail`。而 `force_restrictive_audit_trail` 只有 DE 无条件 / IN 有条件强制，**CN = False** → CN 公司开启后能关回 False。关闭有 `tracking=True` 留痕（写 mail.message）。**改=哈希挡、删=审计追踪挡，两套机制、两种可逆性，别混为一谈。**
- **B-50 硬锁定日期只进不退**：`res.company.hard_lock_date`（v19 新增）live 实测只能前移，回退被挡（"A new Hard Lock Date must be posterior (or equal) to the previous one"）= **不可逆**。它挡整期间任何写入（**含 `currency_id`/`amount_currency`）且挡删除**。
  → **合规声明的正确形态 = 哈希链（字段级）+ 硬锁定日期（期间级）双层**，而非「哈希 + 一个缺口」。**月结上锁 = 实施必做项**，缺此步则"不可篡改/不可删除"仅对开哈希的开放期成立。
  ⚠️ **不可逆意味着不能在唯一的验证载体上试手**：设错日期退不回来，先在 dev 库验行为、生产库按流程设。
- **B-51 编号与断号**：哈希链按 `sequence_prefix` 分链；`report_hash_integrity` 检出断号（"A gap has been detected in the sequence"），报首尾哈希 + 状态（verified/corrupted/no_data）。
- **B-52 `account.move` 不走 `ir.sequence`**：继承 `sequence.mixin`，用 `_get_last_sequence` 正则那套。→ 自建 (公司×凭证字×期间) `ir.sequence.use_date_range` 三键取号与 `account.move.name` **两套独立机制、零污染**，卸载删列原生编号不受影响。配套：过账才分配号（草稿 name=`/`）；作废（cancel/draft）号永久保留跳号，删除（unlink）号释放可复用；反过账取新号不复用（`name` `copy=False`）。

### B-53 ~ B-62（l10n_cn 线 R28–R30 回流，2026-08-10）
> 承接上节 B-47~B-52 的编号。来源：l10n_cn R28（只读探查）、R29（M3a 交付 + T2 证伪）、R30-P1（原生机制探查）。

**B-53 五个 lock date 全带 `tracking`，软锁可自由回退（19.0，`verified live`）**

`account.move` 相关的五个 lock date（soft / hard / tax / sale / purchase）**全部 `tracking=True`**，chatter 留「谁 / 何时 / 旧值→新值」。
`_validate_locks` **只挡 `hard_lock_date`** → **软锁可以自由往回调**。
⚠️ **必须与 B-50 对读**：`hard_lock_date` 不可逆是**特例**，别只见 B-50 就以为 Odoo 的锁都不可逆。
**含义**：中式「结账」不需要自建对象 —— 向导写 lock date，留痕由原生承担（项目档 §6.10 决策 D）。

---

**B-54 `account.account` 在 19.0 是扁平的（🔴 版本敏感，v20 已变）**

🔴 **本条结论仅对 Odoo 19.0 成立。v20 已把 `parent_id` / `parent_path` / `code_path` 加回 `account.account`、并删除 `account.group`；转录 / 引用务必带版本锚。**

**19.0（`verified live`）**：
- `account.account` **无** `parent_id` / `is_group` / `deprecated`，**扁平**；
- **父科目可直接记账，无原生守卫** → 前缀汇总同时吃父与子，**父子混用即重复计数**；
- `code` = `Char(64)`，同公司唯一强制，`.` 合法；
  🔴 **但 `code` 不是公司无关的单值**（19.0 即如此，**非 v20 变更**，R31/R32 两侧亲核）：实际存储在 `code_store`（`company_dependent=True`），`code` 是其 `depends_context('company')` 的 compute/inverse 门面，**按 `env.company.root_id`（公司族）解析** —— 跨 root 才不同。另有 `account.code.mapping` 承载跨公司映射。源码 19.0 `addons/account/models/account_account.py:39-40/97/100/334-336`；master 同构。
  🔴 **对前缀取数的直接后果**：`account_codes` 引擎取 code 时**带跨公司兜底** —— 当前公司/root 的 `code` 为空时，遍历 `account.company_ids` 取**其它公司的 code** 参与前缀匹配（19.0 `account_reports/models/account_report.py:4231-4242`，`verified`；master `:4688-4694`，同机制）。**详见 B-63。**
  ⚠️ **note 侧订正**：若 `code = Char(64) 同公司唯一` 被读成「公司无关的单值」，前提就错了。销号 `status §8 第4项子问题③`——答案是「**从来就不是**」。
- 删有分录的账户被挡；停用父不级联子；**无 parent FK，故 `account.group` 的 `ondelete='cascade'` 坑不适用**。

**v20 补充（`observed`，未亲验）**：「父科目可记账」在 v20 是**官方明示的设计意图**（commit message），纯分组父级靠 `active=False` 表达 → 守卫应取「告警」而非「硬约束」，硬约束是在跟框架方向对着干。

---

**B-55 `account_codes` 的 `D`/`C` 方向后缀 —— 三条边界（19.0）**

> 🟢 **v20 锚（`observed`，`odoo/enterprise@d2368c8b6fe`，2026-08-10）**：`D`/`C` 后缀**保留、语义等价**，仍按 `account_id` 整户余额判方向、`0` 仍归 D 侧（`account_report.py:4574-4582`；`GROUP BY account_id` 仍在 `:4632`）。前缀匹配（Python 侧 `bisect`+`startswith`，非 SQL LIKE）与正则**逐字符未变**。实现层一处改写：master 按 `account_id` 跨该公式所有 prefix_key 求和（19.0 按 `(prefix_key, account_id)` 分桶），倍数为正、不改符号，D/C 判定结果相同。🔴 **但第四条锚（下）在 v20 失去一半对象** —— `sum_if_pos` 侧已被官方删除，见 B-58。

**能力（`verified`，源码 `account_reports/models/account_report.py:4211-4223 / 4272 / 4362-4370`）**：引擎**有** `D` / `C` 方向后缀（`2202C` = 该前缀下各账户净额为**贷**才计、否则 0；`2202D` 反之）。**推翻「`account_codes` 表达不了借贷方向」的绝对表述。**

- **第一条边界（粒度）**：D/C 在**每个 `account.account` 上判方向**（`GROUP BY account_id` 后逐账户比较），**不是明细 / 往来伙伴粒度**。→ 只有客户**把往来明细编成子账户**时才等于财政部的「明细贷方余额」；单一科目 + `partner_id` 的账套，账户级 D/C 拆不了伙伴。
- **第二条边界（算符性质，R29-T2 实测证伪）**：**`D`/`C` 是拆分算符不是列报算符。** 单改一行往来（如 `1122D`）= 半个变换 —— 被丢弃的贷额**有归宿**（负债侧预收款项），不是消失。**必破表内勾稽**：夹具 `1122.001 借500 / 1122.002 贷200` + `1122D` → `_cn_crossfoot_breaks` 报「流动资产合计差 **−200 structural**」。**正确用法 = 成套同改，被分出的部分必须有落点。**
- **第三条边界（单一来源，R30-P1）**：`sum_if_pos` / `-sum_if_neg`（见 B-58）只对**单一来源**成立。多来源合并域时「先合并再判方向」≠「分别判方向再相加」—— 属**公式构造 + 原文口径**问题，不属机制能力问题。**当前无适用场景**，记录备查。

🔴 **第四条锚：两套机制不可互推（R30-T2b，`verified` 19.0）。** `sum_if_pos` 可以**从官方行的净额还原**（净额本身含方向信息，呈现层分流即可，官方记录零改）；`D`/`C` **不能** —— 它逐 `account_id` 判方向，而账户级净额还原不出「哪些明细是贷方」，**必须实跑 `account_codes` 引擎**（逐 `column_group`、按日期域）。实测：官方 `行39 = −200` 只给合计，取不出 `2202C = −300 / 2202D = +100` 的明细拆分。
→ **推论**：任何在 B-58 上验证过的做法，不能因为「都是方向」就套到 D/C 上；反之亦然。选机制前先问一句「这个值能不能从官方净额还原」。

⚠️ **第二条与 B-58 的表内中性证明必须对读**：同样是「方向」，一个破勾稽、一个中性，**差别在是否给被分出的部分安排了落点**。

---

**B-56 `ir.sequence` + `use_date_range` 可做三键取号，完全不碰 `move.name`（19.0，`verified`）**

需要「跨 journal 统一 + 按期间归零」的第二套编号（如中式凭证号 `记-1`），**别去改 `account.move.name`**（它走 `sequence.mixin`，按 journal 过滤且名字不含年月就只能 `reset='never'`，见 §7 会计模型语义）。
`ir.sequence` 自带 `use_date_range` + `ir.sequence.date_range`，可做 **(公司 × 类别 × 期间) 三键**取号。
**R29-T1 实测坐实**：`implementation='standard'` 允许断号；过账（`_post`）时分配；作废草稿不释放、删除随记录消失（**跳号不释放 = 接受 gap**）；反过账另编新号；**零 `move.name` 副作用**。
⚠️ 若该编号会被打印归档，**呈现层动态重排不安全** —— 回插一条日期靠前的记录会让后续号整体挪位，而已归档的号不可变。**这类编号必须落存储字段、取号即定。**

---

**B-57 建科目不填 `account_type` 会按 code 字典序静默继承（19.0 `verified`，v20 未亲验）**

建 `account.account` **不填 `account_type`** 时，`_compute_account_type`（`@api.depends('code')`）按 **code 字典序邻近**静默继承：`bisect_left(codes_list, code) - 1` 取**字典序前一个**账户的 `account_type`（`tag_ids` 同法，`_compute_account_tags`）；**仅当为全库首个 code 才落 `default_value='asset_current'`**。
源码：`odoo/addons/account/models/account_account.py:604-606, 613-636`。

**后果**：批量建中式科目若漏填 `account_type`，**科目能建、报表照跑、不报错，只在报表上少一块**。
例：`1601 固定资产`（应为 `asset_fixed`）若不填，字典序前一个是 `15xx` 长期投资类（`asset_non_current`）→ 静默继承 `asset_non_current`，固定资产从 BS 的固定资产行掉出去。

🔴 **建科目务必显式给 `account_type`，勿依赖继承。** 比 B-54 更容易在批量建科目时坑人。
**Safi 述 19.0 / v20 两分支共有，v20 未亲验。**

---

**B-58 `domain` 引擎的 `sum_if_pos` / `-sum_if_neg` = 单一来源按符号分流、双侧正数列示（19.0）**

> 🔴 **v20 锚（`observed`）：本条机制已被官方删除。** `sum_if_pos` / `sum_if_neg` / `count_rows` 三个 subformula 在 `odoo/enterprise@e7439ee932ab`（2026-07-14，`[IMP] account_reports: make domain engine snapshotable`）删除，官方原因 = 它们破坏 domain 引擎的可组合性（快照需要）。前后逐字核：`e7439ee932ab~1` 命中 18 / `e7439ee932ab` 命中 0。
> **官方迁移范式**：拆两个表达式 —— 原表达式 `subformula` 改 `sum`，新增一个 `aggregation` 表达式挂 `if_above(CUR(0))` / `if_below(CUR(0))`，并把上游引用改指新 label。样板 = 同 commit 的 `l10n_vn_reports/data/balance_sheet.xml`（改 630 行）。
> 🔴 **`0` 的归属反转，不可机械替换**：旧 `sum_if_pos` 判据 `>= 0`（**0 归正侧**），新 `if_above(CUR(0))` 判据 = **严格大于 0**。本条四夹具（尤其 F4「无余额 → 0/0」与边界为 0 的场景）迁移后须**逐条重判**。
> ⚠️ **本条 19.0 结论仍成立**（`verified live`，四夹具全对），**保质期到 v20 为止**。见惯例 16。

**语义（`observed`，源码）**：
- `sum_if_pos` / `sum_if_neg` 判**整行聚合净额**（`total_sum`，`:4181`，注释明写**不可逐 `query_res` 判**）；
- `-` 前缀经 `safe_eval` 处理（`:3510 / :3531`），把负净额**取正**；
- `0` 归入正号侧（`>=`，`:4182`，「0 视为正」）；
- 阈值不满足时返回 **`0`**（非 `None`、非塌行）。

**装配式（一段式，两行同源同 formula、分挂两个 subformula）**：
```
R_recv: engine=domain  formula=[('account_id.code','=like','1122%')]  subformula=sum_if_pos
R_prep: engine=domain  formula=[('account_id.code','=like','1122%')]  subformula=-sum_if_neg
```

**四夹具实测（`verified`，temp report + dev 库，全 rollback）**：

| 夹具 | 造数 | 实测 R_recv / R_prep | 正确口径 |
|---|---|---|---|
| F1 | `1122` 借 500 | 500 / 0 | ✅ |
| F2 | `1122` 贷 200 | 0 / **200（正数）** | ✅ |
| F3 | `1122.001` 借 500 / `1122.002` 贷 200 | **300 / 0** | ✅ 科目级净额，非逐账户 |
| F4 | `1122` 无余额 | 0 / 0 | ✅ 不塌行、不报错 |

🔴 **F3 是区分性夹具**：`D`/`C` 后缀在同一夹具下给出 500 / 200 —— **本机制与 D/C 后缀在子账户场景下结果不同，二者不可互换。**

**表内中性证明**：恒等式 `R_recv − R_prep = 科目净额` 逐夹具成立（500 / −200 / 300 / 0）⇒ 该分流把单行净额拆成资产侧正 + 负债侧正，**合计不变**。与 **B-55 第二条边界对读**。

**官方先例（`observed`，逐字）**：越南 TT200 资产负债表 `l10n_vn_reports/data/balance_sheet.xml` —— 短期应收账款 `1311%` 挂 `sum_if_pos`（`:264`）、预付供应商 `3311%` 挂 `sum_if_pos`（`:283`）、负债侧以正数列示贷方净额挂 `-sum_if_neg`（`:1689 / 1708 / 1727 / 1756`）。旁证：西班牙 `l10n_es_reports/data/full_balance_sheet_report_data.xml`。法国 `l10n_fr_reports` 用 `aggregation` + `if_above` / `if_below` 分两行，但那是**净额对冲不是正数列示**。

---

**B-59 条件类 subformula 分挂两套引擎，`account_codes` 不能直接挂（19.0，`observed`）**

> 🟢 **v20 锚（`observed`）**：`if_above` / `if_below` / `if_between` / `if_other_expr_above|below` / `round` / `ignore_zero_division` / `cross_report` **全部保留**（`aggregation` 侧）；`sum` / `-sum` 保留（`domain` 侧）；🔴 `sum_if_pos` / `sum_if_neg` / `count_rows` **删除**（见 B-58）。两处增量：① `cross_report` 新增可选第二参 `force_date_scope`，正则收紧为**报表 id 不得含逗号/空白**；② `aggregation` 在 groupby 时不施加 bound。
> 🔴 **引擎方法全部改名**：`_compute_formula_batch_with_engine_<x>` → **`_report_engine_<x>`**，并**去掉 `next_groupby` / `offset` / `limit` 三参**（`odoo/enterprise@839c055caf11`，2026-05-07）。引擎的**技术标识符** `'account_codes'` / `'domain'` 等**未变** ⇒ 纯声明式表达式不受影响，**只有 override 过引擎方法的代码会碎**。

源码 `account_reports/models/account_report.py`：

| 关键字 | 适用 engine | 拼写 / 参数 | 行号 |
|---|---|---|---|
| `sum` | `domain` | 裸词 | :4048 |
| `sum_if_pos` / `sum_if_neg` | `domain` | 裸词，可带 `-` 前缀 | :4169–4193 |
| `count_rows` | `domain` | 裸词 | :4071 |
| `if_above(CUR(x))` | `aggregation` | 带货币前缀，如 `if_above(CNY(0))` | :3899 |
| `if_below(CUR(x))` | `aggregation` | 同上 | :3896 |
| `if_between(CUR(x),CUR(y))` | `aggregation` | 双参 | :3902 |
| `if_other_expr_above/below(code.label,CUR(x))` | `aggregation` | 判**另一表达式**的值 | :3772–3800 |
| `round(precision[,method])` | `aggregation` | 如 `round(-2,HALF-UP)` | :3845 |
| `cross_report(report_xmlid)` | `aggregation` | markup，非计算 | :3859 / :3596 |
| `ignore_zero_division` | `aggregation` | 裸词 | :3761 |
| `editable` / `rounding=` | `external` | —— | :3172 / :3178 |

- **`sum*` 系只在 `domain` 引擎解析；`if_*` 系只在 `aggregation` 引擎解析。**
- 🔴 **`account_codes` 引擎不能直接挂条件类 subformula。** 要用其前缀汇总 + 方向分流，须**两段式**（`account_codes` 算中间行 → `aggregation` 引用并挂 `if_above` / `if_below`）。
- 但 `domain` 引擎的 `sum_if_pos` / `-sum_if_neg` **一段式即可**（`domain` 用 `=like` 自行汇总）→ **优先走一段式**。
- `if_above` / `if_below` 判整个 `formula` 求值后的净额（`:3758 → :3802`），**不能取正数**（保留原符号）；要正数须另起一表达式 `-line.label` 二段负负得正。

---

**B-60 `l10n_cn` 的「在产品(资产户) vs 生产成本(损益户)」= 西式 WIP 模型与中国成本模型错配（19.0，`observed` 源码）**

> 🔴 **v18 补一条计数陷阱（踩过一次，记牢）**：`71` 与 `202` 是**子模板自身的科目数**，不是装完之后库里的科目数。实装还要叠父模板 **`cn_common`（88 条，不可单独装）** ⇒ **官方原生实装 `cn` = 159、`cn_large_bis` = 290**（`verified`，R43 实测）。
> ⚠️ **而我方 `post_init` 的通用发行件"恰好"也是 88 条** —— 两个毫不相干的东西数字相同。`159 − 71 = 88`、`290 − 202 = 88` 会"减出"一个看起来完美自洽的机制（"基线里已含我方 88"），**这是错的**。note 侧 R43 就这么错过一次，被「发行台账 0 行」当场证伪（台账只记新建，0 行 ⇒ `post_init` 一条没新建）。
> ⇒ **凡引用科目条数，必须写明"哪一层"**：子模板数 / 实装数 / 我方新建数 / 我方认领数。归族惯例 17（计数表述必须平铺）与惯例 12。
>
> 🔴 **v8 收窄**：本条初稿把缺陷写成「编码体系错配」，**不对**。Odoo 有两套模板 —— `cn`（ASSBE 式，71 科目）与 `cn_large_bis`（**ASBE 式**，202 科目），**后者与财政部 ASBE 码是对齐的**（`4001` 实收资本 / `5001` 生产成本 / `6001` 主营业务收入 / `1406` 发出商品），官方 ASBE 报表对 ASBE 客户在**编码轴**上没坏。
> **真缺陷与编码无关，只与 `account_type` 有关**：生产成本户（ASSBE `4001` / ASBE `5001`）**两套模板下都 typed `expense_direct_cost`**，而 Odoo 另设一个资产户装 WIP。**双轨的常量是「WIP 被拆成两个户」，不是某个码。**

官方 `l10n_cn` chart（`addons/l10n_cn/data/template/account.account-cn.csv`，19.0 共 **71 科目**）同时存在：

| 编码 | 名称 | `account_type` |
|---|---|---|
| `1406` | Work In Progress / 在产品 | `asset_current` |
| `1406.01` | Work In Progress Overhead / 在产品费用 | `asset_current` |
| `4001` | Production Costs / 生产成本 | **`expense_direct_cost`** |
| `4101` | Manufacturing Expenses / 制造费用 | `expense_direct_cost` |

**这是 Odoo 把西式模型原样搬进来的结果**：WIP 是资产科目，生产成本是**成本归集池**（走损益）。中国准则下这两者是**同一个东西** —— 生产成本期末借方余额**就是**在产品，是资产，不结转损益。

**三条后果（`verified` live，dev 库 `CN ASBE Company`）**：

1. 中国会计按肌肉记忆往 `4001` 记在产品 → BS「在产品」行取 `1406`，**值为 0**；
2. 存货行漏计在产品（财会〔2011〕17号 编制说明 (9) 明列「生产成本」为存货源科目）；
3. 🔴 **期末在产品成本被计入当期损益** —— 虚减利润、虚减资产，而 `资产总计 = 负债和所有者权益总计` **照样自平**，表内勾稽守卫**抓不到**。这是一个**静默错报**。

**若强行把 `4001` 纳入存货取数** → 该余额已经由损益进了未分配利润（权益侧），再计一次即**双重计**，实测 `53 ≠ 30`。所以「当前排除 `4001` 是对的」与「取数完整」是两回事：**缺陷在科目类型层，不在报表取数层。**

🔴 **`4001` 的 `expense_direct_cost` 是官方 chart 自带**（CSV 显式给出），**不是 B-57 那种静默继承** —— 是上游缺陷，不是建库事故。

**`1406` 的语义（`observed`，v8 结案，不再挂待核）**：金蝶星云科目表 263 行与《企业会计准则实务应用精解（2025年版）》**两源互印**：ASBE `1406 = 发出商品`。
- `cn_large_bis`（ASBE 模板）中文名**就是「发出商品」** → **与财政部一致，无冲突**。
- `cn`（ASSBE 模板）把 `1406` 用作「在产品」，而 **ASSBE 财政部科目表根本没有 `1406`**（`1405` 直接跳 `1407`）→ 性质是**在财政部未分配的号段上自造了一个户**，不是占用已有语义。严重度低于冲突。

**跨项目适用面**：任何中国制造业客户装 `l10n_cn` 都会碰上，与是否用中国本地化报表无关。

---

**B-61 同事务内新建 `account.account` 未 `flush()` 时，`account_codes` 引擎取不到（19.0，`verified`）**

只读探针在同一事务里造 `account.account` 后直接调 `account_codes` 引擎，会得空或抛异常（新账户尚未落库、引擎的账户搜索看不到），须先 `invalidate_all()` / `flush()`。

🔴 **与惯例 12「回滚事务里的 0 尤其骗人」同族，但骗人的形态不同：这次骗人的不是 0，是异常。** 异常比 0 更危险 —— 0 至少会让人怀疑数据，异常则极易被直接误判成「**机制不支持**」而收工，从而把一条可用能力错误地记成不可用。

**判据**：探针报「机制不支持」之前，先答一句「我造的数据 flush 了吗」。

---

**B-62 2017 年后新增的中国会计科目没有权威编码；前缀匹配的碰撞面大于逐码对照（`observed`，2026-08）**

**事实**：财政部 2006 年后**没有再发布过完整会计科目表**。收入准则（财会〔2017〕22号）、租赁准则（财会〔2018〕35号）、金融工具准则（财会〔2017〕7号）新增的科目，**编码由各软件厂商自行分配**，彼此不同。

**实测对照（Odoo `l10n_cn_reports` ASBE 报表绑定码 vs 金蝶星云科目表 263 行）**：ASBE BS/PL 里属这一批的共 **14 行**，**一致仅 3 行**（交易性金融资产 1101 / 交易性金融负债 2101 / 合同负债 2204），其余为碰撞或错位。例：

| 科目 | Odoo | 金蝶 |
|---|---|---|
| 合同资产 | 1481 | **1462**（金蝶 1481 = 持有待售资产） |
| 债权投资 | 1504 | **1501**（金蝶 1504 = 其他权益工具投资） |
| 租赁负债 | 251 前缀 | **2601** |
| 使用权资产 | 1704(+1705+1706) | **1641** |

**两类后果，严重度不同**：
- 🟥 **碰撞** —— 该码在别家是**另一个科目** ⇒ 报表取到的**不是 0、是错的数**，且静默；
- 🔴 **错位** —— 取一个别家不用的码 ⇒ 取到 0/空，是**可见的漏**。

🔴 **判据（本条的真正价值）**：不是「我的码在别家叫什么」，而是「**这个码/前缀在客户账上有没有余额**」。**前缀匹配的碰撞面大于逐码对照** —— `1704` 在金蝶表里根本没定义，但 `17xx` 前缀会吃掉客户的 `1701 无形资产`。逐码对照会漏判这一类。

**推论（跨项目）**：任何按编码前缀取数的报表，**新增科目的绑定不能只靠硬编码前缀**，要么可配置，要么按科目名/类型兜底。中国 CAS 30 修订（财会〔2026〕11号）的五类别新增项目**必然重演一轮**。

**但也不要过度反应**：2006 体系的老码（1001–1602 / 2201–2241 / 4·5·6xxx 大类）四方一致，前缀匹配够用。**要分开处置的只有这一小撮。**

**B-63 多公司共享账户 + 本公司 code 缺失 → `account_codes` 引擎跨公司兜底 → 前缀吃入 → 静默错报（19.0，`verified` dev 库）**

**机制（`observed` 源码，19.0 亲核）**：`account_codes` 引擎在遍历账户取 code 时，若**当前公司/root 的 `code` 为空**，会遍历 `account.company_ids` 取**其它公司的 code** 参与前缀匹配。
`account_reports/models/account_report.py:4231-4242`（`_compute_formula_batch_with_engine_account_codes` 内）：
```
4231 for account in all_accounts:
4232     account_code = account.code
4233     if not account_code:                 # ← 仅当本公司/root code 空才触发
4234         for company in account.company_ids:
4235             account_code = account.with_company(company).code
4236             if account_code: break
```

**这个危险状态普通 ORM 造不出来（`verified`，R32-T1-0-d）**：`account.account.create` **无条件**调 `_ensure_code_is_unique`，要求账户所属**每家公司都有 code**，否则 `ValidationError`；只有 `write` 认 `defer_account_code_checks=True` 才放行。实测：`create(company_ids=[A,B], 只给 A code)` → 报错；A 单公司带码 create + defer-write 把 B 加进 `company_ids` 且不给码 → 成功且持久。**⇒ 该状态仅经导入 / 建表模板 / load（defer 路径）产生。**

**四夹具实测（`verified`，dev 库两家 CN 公司，全 rollback）**：

| 夹具 | 造数 | 实测 | 判定 |
|---|---|---|---|
| F1 基线 | 单公司 A，code `1122.001`，Dr 7777 | 落应收账款及各级合计 | ✅ **预期结果非证据**（惯例 14） |
| **F3 🔴唯一证据组** | 账户 A code=`1122.001`；defer 把 B 加入 `company_ids` 且 **B 侧留空 code**；在 **B** 上 Dr 8888 | 引擎 `source=fallback:comp4`、`resolved_code=1122.001`；8888 落进 B 报表的**应收账款（1122 前缀）** | ✅ **被吃到** |
| **F4 勾稽面** | F3 命中下跑 `_CN_CROSSFOOT` | `breaks=[]`；资产总计 `[8888,0]` = 负债权益总计 `[8888,0]` | 🔴 **静默** |
| F5 双列 | F3 场景开双列 | 应收账款 `[8888, 0]`，仅期末列受影响 | ✅ 逐列独立 |
| F2 无泄漏对照 | A code=`1122.001` / B code=`2202.001`，各有余额 | on A `source=own` 落应收；on B `source=own` 落应付 | ✅ 两公司都有码 → 各用自身码，兜底门控 `if not account_code` 挡住 |

🔴 **F4 静默的机理**：被错放的账户**同时**进入 ① 它错落的明细行（1122 前缀）② 「流动资产合计」子表（同为 1122 前缀 Σ），**同源同吸 → 子表恒等式不破**；且双分录对手方带码正常入表 → 资产=负债权益也守恒。**两个守恒同时成立，所以守卫看不见。** 属「静默错报」，**严重度与 `4001`（B-60）同级**。

🔴 **跨项目适用面**：任何按 `account_codes` 前缀取数的报表都受此约束，不限于 l10n_cn。**判据**：客户账套是否会经**导入路径**产生「跨公司共享 + 本公司缺码」的账户 —— 若会，静默错报真实存在。处置见 `status §8 第 10 项`（Safi 拍）。

⚠️ **与 B-54 对读**：本条是 B-54「`code` 按 root 公司多值」那一前提的**实测后果**。B-54 讲事实，本条讲这个事实怎么变成一个抓不到的错报。


**B-60 补记（R33-A，2026-08-11）**：B-60 的三后果中「② 行9 存货漏在产品 / ③ 期末在产品成本静默进损益」在 **ASSBE 侧已修** —— 对官方 ASSBE 报表做 5 处 formula 外科覆盖（BS 行11 `1406→4001`、BS 行12 补 `1406`、PL 行2 `40→40\(4001)`、BS 往年未分配利润 `-4→-4\(4001)`、BS 行26 `hide_if_zero`），先存原值、`uninstall_hook` 写回。🔴 **ASBE 侧（`5001`）未动，B-60 仍成立。**
🔴 **同时作废 `R30-P3 ②`**（原判「存货 4001 报表正确排除」，`verified`）—— 那是**不完整变换**的结论（只试塞进存货、未同时摘权益侧），且与它自己引用的原文（编制说明(9)：存货源科目**含**生产成本）直接冲突。详见 `项目档 v24 §6.7 第二十二条`。

---

**B-64 两条取数路径分野：`account_codes`(编码) vs `account_type`(类型)，冲突时各不相让（19.0，`verified` dev 库）**

**同一笔「编码与类型冲突」的分录，在两类报表里落到完全不同的地方，两边都不看对方那个维度。**

| 路径 | 报表 | 取数依据 | 源码 |
|---|---|---|---|
| **A** | 我方 CN BS/PL 四张 form | 🟢 **纯按编码前缀** | `account_codes` 引擎选账户只靠 `code.startswith(prefix)`+`tag_ids`、**全函数无 `account_type`**（`observed` `account_report.py:4283/4318-4342`）；`suite_cn_statement/models/` 取数与勾稽 grep `account_type` **零命中**（T0-5） |
| **B** | 官方**通用** BS/PL | 🔴 **按 `account_type`** | 每条 `domain` 公式按 `account_id.account_type` 归类（Receivables=asset_receivable、Revenue=income…，`observed` T0-0-c） |

**Live 铁证（`verified`，dev 库 company 4 ASSBE，全 rollback）**：
- `code=1122999`（应收号段）+ `account_type=expense` Dr 8888 → 我方 ASSBE BS 落**应收账款**（按码）；官方通用 BS 落**未分配利润 −8888** / 官方通用 P&L 落 **Less Operating Expenses**（按型）。
- 对称 `code=6999`（损益段）+ `account_type=asset_current` Dr 7777 → 我方 BS **资产行取不到**（可见漏）；官方通用 BS 落 **Current Assets**（按型）。

🔴 **⇒ 客户改错 `account_type`：我方中式报表不受影响（按码），官方通用报表会错（按型）。这是 B-60（`4001`）的一般化** —— `4001` 只是「编码对·类型错」这个普遍分野的一个实例。

🔴 **两个关键 nuance（改变了此前的判断）**：
1. **我方 CN 报表本身就是 Odoo 官方通用 BS(id4) 的 `variant`（27/28）** —— CN 公司上打开「官方 Balance Sheet」**默认渲染的就是这个 `account_codes` 的 CN 变体**，不是按类型的通用版；只有强制切 `selected_variant_id=通用id` 才走 `account_type`。⇒ **「客户会打开按型的官方报表因此 account_type 必须建对」这个前提要重估** —— CN 公司的会计默认看到的就是按编码的我方版。
2. **现金流量表是唯一例外** —— `suite_cn_cashflow` 走 `domain` 引擎，**用 `account_type='asset_cash'` 判「哪笔分录触及现金」**（现金流定义只能按货币资金类型认、编码不固定，`observed`）。⇒ **「我方 form 纯按编码」这个断言限 BS/PL 四张成立，CF 不成立**。货币资金类科目（1001/1002/1012）的 `account_type` **必须** typed `asset_cash`，否则 CF 判不出现金。

**TB/GL 按编码分组**（T0-4）：`1122999`（type=expense）在 TB 里落「1 资产类」段紧跟 1122，GL 按 code 排 ⇒ 类型建错的科目在日常 TB/GL 上**混在应收区、更隐蔽**。

🔴 **对自发科目表的直接含义（跨项目）**：既然我方 BS/PL 按编码、且 CN 公司默认看的就是我方版，则自发科目表时 **`account_type` 只有货币资金类必须钉死（=asset_cash，为 CF）**，其余科目类型建错不影响我方报表。**编码号段才是取数键，必须对；类型除现金外是次要的。** 这把 B-60 那种「类型建错=静默错报」的恐慌**收窄到只剩现金类**。

⚠️ **与 B-60 对读**：B-60 说「4001 类型错致在产品静默进损益」—— 那是**官方通用报表/`account_type` 路径**下的现象；在我方按编码的 CN 报表里，只要 `4001` 编码落在成本号段、报表按 `4001` 前缀取，就对。两条一起读才不误判。

---

---

**B-65 核报表公式覆盖面，须逐条 ORM 遍历，不得依赖文本检索（19.0，`verified`，2026-08-11）**

`account.report.expression` 的同一公式在 XML 里有**两种写法**：`account_codes_formula` 短标签、与 `<field name="formula">` 长字段。**文本检索（grep）必漏其一。**

**实例（R33-A）**：覆盖官方 ASSBE 报表口径时，`BS 往年未分配利润` 的 `-4` 前缀写在**长字段**里，纯文本 grep 扫不到 → 首版 override 清单漏了这一处 → `4001` 被移进 BS 存货当资产、权益侧仍靠 `-4` 把它当损益扣除 → **`资产 ≠ 负债+权益`**，实测破 6000。改用 ORM 全扫 `engine=account_codes` 的表达式才逼出来。

**做法**：
1. 按 `account.report.expression` **记录**逐条遍历，不按文本。
2. **扫全部取数引擎**，不能只扫 `account_codes`。（本例已确认 ASSBE BS/PL 仅 `account_codes` 87/58 + `aggregation` 27/18、**零 `domain`**；`aggregation` 只引别的表达式、不独立选账户，叶子对了即随之正确。）
3. 🔴 **每行往往有两条表达式**：`balance` + `bal_begin`/`ytd`（年初/本年累计列复用同一公式）。**按 line 覆盖其全部表达式，不分 label** —— 只改一条会让期末列与年初列读不同的码，**同表两列打架且不报错**。

**跨项目适用**：任何**覆盖上游 Odoo 报表公式**的场景。

🔴 **同一条表达式第二次被漏（R34-T1，`verified`）**：`BS 往年未分配利润` 的 `balance_domain` 覆盖，在 R33-A **实现时**被 grep 漏（长字段，V6 测试抓出，即上文实例）；又在 **文档计数时**被漏 —— `项目档 §4.5.12-E7` 用「3 行 × 2 表达式 + 1 条 `hide_if_zero` = 7 条」的**乘法式**表述，把这条**单表达式异质项**结构性排除在计数之外，实际台账为 **8 条**，由 R34-T1 数实条数抓出。

**推论（跨项目，比上文的做法更前置）**：**同一个异质项会被不同机制反复漏。** 逐条 ORM 遍历解决的是「**检索方法**」这一层；「**计数表述**」是独立的另一层，两层都要平铺 —— 见 §8 **惯例 17**。

**B-66 `_register` 是 Odoo 模型保留布尔属性，不可用作自定义方法名（19.0，`verified`，2026-08-11）**

在 `models.Model` 子类上定义名为 `_register` 的方法 → **`TypeError`**。Odoo 元类把 `_register` 当布尔属性消费，方法对象无法参与布尔语义。R34-T1 改名 `_register_drift` 后正常。

**做法**：自定义方法名避开单下划线前缀的框架保留名族（`_register` / `_auto` / `_abstract` / `_transient` / `_inherit` 一类）。**加业务后缀是最省事的规避**，且顺带把方法的作用域写进名字。

---

**B-67 两条加载路径的分野：`post_init_hook` 不随 `-u` 重跑，XML `data` 随 `-u` 重载（19.0，`verified`，2026-08-11 提出 / 2026-08-13 升级）**

R34 在 dev 库观察：`suite_cn_coa` 经 `-u` 升级后，E-7 的官方公式覆盖**仍为原值**（`1406` 未换成 `4001`）—— `post_init_hook` 只在**首次安装**执行，`-u` 不触发。

🔴 **对「覆盖上游记录」这类设计的直接含义**：凡把外科覆盖放在 `post_init` 的，**升级路径上不会重新施加**。若某客户库在覆盖功能上线**之前**已装该模块、其后仅 `-u` 升级，则**永远拿不到覆盖，且无任何提示** —— 与 B-63、B-60 同族：**静默**。

**归族**：这不是「覆盖写错了」，是「覆盖没被执行过」。排查覆盖类缺陷时，**先答「这个库上覆盖到底跑没跑过」，再答「跑出来对不对」**。

🟢 **2026-08-13 升 `verified`（R36-T5b 活体首装 → `-u` 观测）**，并补出对照的另一条路径：

| 承载方式 | 纯 `-u`（无 migration） | `-u` + migration | 证据 |
|---|---|---|---|
| **XML `data` + `noupdate="0"`** | 🟢 **重放 → 新值** | 同（新值） | 两次 `-u` 后 DB 均为新值 |
| **`post_init_hook`** | 🔴 **不重放 → 留原值** | 重放 → 新值 | 首次 `-u` 后仍为原值；强制重跑 migration 后变新值 |

⇒ **想让改动随升级到达存量库，就把它放进 XML `data`；放在 `post_init_hook` 里的，每个触及它的版本都必须自带一次 migration。**

🔴 **后者是个靠记性守不住的模式**：将来某版改了同一批记录却忘了带 migration，就会再次不重放，且**静默**。⇒ 应当有一条能在**任意既有库**上跑的自检（不能只做成单测 —— 单测在 fresh install 上恒绿，抓不到「升级路径漏放」）。

**归族**：这不是「覆盖写错了」，是「覆盖没被执行过」。排查覆盖类缺陷时，**先答「这个库上覆盖到底跑过没有」，再答「跑出来对不对」**。

---

**B-68 翻译型字段的语言键：未激活语言硬报错，默认 context 建记录只落单键（19.0，`verified`，2026-08-13 提出 / 同日改写）**

🔴 **本条 R37 整条改写。** 原设问是「目标语言未激活时，`with_context(lang=…)` 落目标键还是回落 `en_US`」—— **两个答案都不对，有第三种真相。**

| # | 场景 | 实测 | 等级 |
|---|---|---|---|
| 代理 | context 用**未激活**语言（`sq_AL`）访问翻译字段 | 🔴 **`UserError: Invalid language code` 硬报错** —— 既不落目标键，**也不静默回落 `en_US`** | `verified` |
| 1/2 | `zh_CN` 已激活，`create`/`write` 带 `lang='zh_CN'` | `{'en_US': X, 'zh_CN': X}` **双键同值** | `verified` |
| 3 | 以**默认 / `en_US`** context `create` | 🔴 **`{'en_US': X}` 单键，无 `zh_CN`** | `verified` |
| 4 | 场景 3 之后**再激活**语言 | 老记录 jsonb **未变** —— 激活**不回填用户数据** | `verified` |
| 5 | 官方 chart 账户当前状态 | 双键正常（`en_US`=英文 / `zh_CN`=中文，**来自模块 i18n**） | `verified` |

## 真正的缺陷暴露面是场景 3

**不是「写不进目标键」，是「压根没往目标键写」。** 以默认 context 建记录 ⇒ 只有 `en_US` 单键；**若那个串本身是中文**（`l10n_cn` 官方数据即如此），则：

- `zh_CN` 界面**回落显示 `en_US`** ⇒ 看起来完全正常，**肉眼查不出**；
- 只有**显式取 `zh_CN`** 的地方（导出模板、打印模板）才会空。

⇒ **验收必须查 jsonb 原值，看界面等于没查。**

## 对修法的约束

🔴 **「直接写双键」这个方案不成立** —— 未激活语言硬报错，写双键**也得先激活**。

⇒ **实际修法只能是前置**：建记录前确保目标语言**已激活且在 context 中**；未激活则**拒绝并给出可读原因**（同 T4-a 门控的形状），**不得静默继续**。

## 🆕 R41 活体实测（`verified`，全新 staging 库，2.1.0 现场）

🔴 **我方发行的两条路径落库结果不同 —— 这条只有活体能得，源码读不出来。**

| 路径 | 落库 | 成因 |
|---|---|---|
| **`post_init_hook` 自动发行** | 🔴 **单键**：中文写进 `en_US`、`zh_CN` **空** | hook 跑在**无 UI 语境**下，`env.lang` 取不到 `zh_CN` |
| **wizard 手动发行**（中文界面下） | 🟢 **双键**：`en_US` 与 `zh_CN` **两键都是中文** | wizard 跑在用户会话里，`env.lang` = `zh_CN` |
| **官方 chart 账户**（先装中文 → 后装科目表，**正序**） | 🟢 **双键正常**：`en_US`=英文 / `zh_CN`=中文 | 模块 i18n |

**同一个库、同一份代码、相隔 16 分钟建的两批科目，jsonb 形态相反。**

⇒ **B-68 的准确表述不是「我方发行账户不落 `zh_CN`」，而是「`post_init` 路径落单键、wizard 路径落双键」。** 笼统表述会让人以为改一处即可，实际要看的是**每条建记录路径各自的 `env.lang` 语境**。

⇒ **验收判据同步收紧**：不能只抽查"我方发的科目"，必须**按发行路径分别抽查**。

## ⚠️ 一条仍未闭合

**「先装科目表、后加语言 ⇒ 中文环境永久英文」这个顺序性症状，尚未被复现或推翻**（`observed`）。

🆕 **R41 只验到了正序**（先装中文 → 后装科目表 → 官方账户双键正常）。**反序（先科目表、后中文）仍未按序活体复现** —— 按惯例 20，正序结果**不能**用来推反序。

场景 5 报的是**当前状态**，来自一个语言一直激活的库 —— 按 §8 **惯例 20**，查当前状态答不了顺序性问题。

**存在一个可能的分野尚待实测**：官方 chart 账户的译名**走模块 i18n**，而模块 i18n 在**语言激活时会加载**；我方发行的账户是**运行时创建的用户数据**，场景 4 已证实激活不回填。**若该分野成立，则官方 chart 可能并不中招，而我方独中** —— 这与原先「官方同样中招、非我方独有」的判断**方向相反**，直接影响对客户的说法。

**复现法**：全新库、**不装目标语言** → 选本地化装 chart → 再激活语言 → 查官方账户 jsonb。

**B-69 ASBE 报表把 `5001 生产成本` 立即费用化 ⇒ 存货变负数、`30=53` 不破、守卫抓不到（19.0，`verified`，2026-08-13）**

`l10n_cn_reports` 的 ASBE 侧：

| 行 | 公式 | 后果 |
|---|---|---|
| BS `CN_INV` 存货 | `140+142+145+147+1411` —— 🔴 **不含任何 5xxx，这是病根** | 在产品不进存货 |
| PL `CN_OC` 营业成本 | `64\(6403) + 5\(53)` —— `5\(53)` = 5xxx 除 53xx | **吸收口一**：当期费用化 |
| BS 往年未分配 `CN_PREV_YEAR_EARNINGS` | `balance_domain` = **裸前缀 `-5`** `-60-61…-69` | 🔴 **吸收口二**：把**全部 5xxx** 扫进未分配利润 |

🔴 **两个吸收口，不是一个。** 第二个是**裸前缀 `-5`**（比 ASSBE 侧的 `-4\(4001)` 更粗，不带任何排除），R36-T4 观察到的权益 −6000 正由它而来（`CN_OE`/`CN_PC` 均为 0，因它们只含 4xxx）。⇒ **修复必须三处成对摘**（存货 + 营业成本 + 权益），缺任一处则破 `30=53` 或 P&L 错。

🔴 **受害科目是六个不是一个。** ASBE 的 5xxx 只有 7 个一级码，`\(53)` 只排除了 `5301 研发支出`（它有专用行 `cn_rde`、`account_type` = 费用，排除是对的）：

| 被吃入 | `5001` 生产成本 · `5101` 制造费用 · `5201` 劳务成本 · `5401` 工程施工 · `5402` 工程结算 · `5403` 机械作业 |
|---|---|

**而 v20 官方只补了三个**（`5001+5101+5201`）—— **照抄上游不等于修完。**

**实测**（`Dr 5001 / Cr 1403 6000`，造数后 rollback）：存货 **−6000**（原材料流出、在产品不入存货 ⇒ **转负**）· 营业成本 +6000 · `CN_OE`/`CN_PC` 均 0 · **`30=53` 不破，差 0** · 勾稽守卫**无破口**。对照组 `Dr 1403 / Cr 2202` 基线正常。

🔴 **与 B-60 是两种机制，措辞不可混**：

| | 机制 | 症状 |
|---|---|---|
| **ASSBE**（B-60） | 报表行读 `1406`，取不到 | 存货**漏计** |
| **ASBE**（本条） | `5\(53)` 吃入营业成本 | 存货**变负数** + 成本高估 |

**为什么最阴**：资产 −6000 与「费用 → 权益 −6000」精确抵消，**平衡式自洽**，所以任何基于 `30=53` 的守卫都抓不到。⇒ **一个静默错报可以完全躲开平衡类断言；要抓它，得靠「存货不应为负」这类语义断言。**

🟢 **上游已承认并修**：v20 官方自己在 ASBE 存货口径上加了 `5001+5101+5201`。

---

**B-70 报表 variant 可达性的两条规则（19.0，`verified`，2026-08-13）**

| 层 | 可达性 | 证据 |
|---|---|---|
| **root 通用版**（如 BS `id4` / PL `id7`） | 🔴 **恒可达** —— 始终在 variant 下拉里 | R34-T3 |
| **兄弟 variant 之间**（如 ASSBE 28 ↔ ASBE 27） | 🟢 **受 `availability_condition` 相互隔离**，正常 UI 切不过去 | R36-T3：ASBE 公司下拉仅 `[(4,…),(27,…)]`，28 不在列；PL 侧 25 同样不在列 |

⇒ **「客户看不看得到另一张表」要分两问**：看得到 root 通用版（永远），看不到隔壁准则的 variant（受条件挡住）。**两条实测不矛盾，合起来才是完整规则。**

⚠️ **残余风险**：`availability_condition` 挡的是 UI，**程序化强制渲染仍可绕过**。若被绕过，读到的是另一套准则的科目语义（实例：ASSBE 行11 在产品公式 `4001`，在 ASBE 库里 `4001` = 实收资本）。**属结构性风险，非当前故障。**

**B-71 Odoo.sh staging 推 commit ＝ 保留数据库、重建容器（`verified`，2026-08-13 实测）**

官方文档写的是「staging 分支每次推送创建一份生产构建的**新副本**」。**实测行为不是这样**：

| 对象 | 推 commit 后 |
|---|---|
| **数据库** | 🟢 **保留** —— 公司、语言、科目、已装模块全部原样在（实测：三家公司 `ae`/`cn`/`cn_large_bis` 与科目数一条不差、`zh_CN` 仍激活） |
| **容器文件系统** | 🔴 **重建** —— `/tmp` 下的产物**全部丢失** |

**两条落法**：

1. 🟢 **升级路径实验可以放心做** —— 推新代码不会顶掉现场，这是造「存量库 → `-u`」场景的唯一途径（R41 据此把 B-67 跑通）。
2. 🔴 **任何取证产物不得只落在容器文件系统**（`/tmp`、`~`）。基线快照、导出件一律**打到屏幕并带出库外留存**。R41 第一次落 `/tmp` 的 205 行基线在推 commit 后即丢失，靠库外副本才没白跑。

归族：与惯例 12「查到 0 ≠ 真为 0」同源 —— **文档说的行为与实际跑出来的行为不是一回事**，凡以平台文档为前提的实验设计，先用一次廉价动作验证该前提。

---

### 🆕 B-72 Odoo `account_type` 中文标签不是中国会计要素术语（`verified(artifact)` + `observed`）

**形态事实**（`verified(artifact)`，两库科目表导出件 + 界面截图）：`equity` → 「股本」、`expense_direct_cost` → 「收入成本」，另有「信用卡」「应收账款」直接作为**类型名**出现。而中国会计要素分类是 资产 / 负债 / 所有者权益 / 成本 / 损益。

**从业者判读**（`observed`，单人样本）：「股本是一个会计科目，股份有限公司使用」（即「股本」是**科目名**不是类别名）；「类别属于成本，收入成本方便内部，**不是财政部规范**」。

🔴 **严重度定准（别按正确性读）**：R33-T0 已证我方 BS/PL 四张 form **纯按 `account_codes` 编码取数、不读 `account_type`**，唯一例外是 CF 用 `asset_cash` 判现金。⇒ **标签错不影响任何一个数**，这是**识别度问题（指标 2）**，不是正确性问题。

🔴 **本条已造成一次实际误判并被纠正（完整闭环见 §8 惯例 25）**：按字段名问「`1012` 的 `account_type` 对不对」→ 答「流动资产是对的」（读起来像「别改」）；绕开字段名重问「`1012` 余额在编现金流量表时算不算现金及现金等价物」→ 答「**不要剔除**」（等于「要改成 `asset_cash`」）。**两次方向相反，且第一次更像结论。** 若按第一次结案，会把一条**正确的告警**当成错的删掉。

归族：与惯例 12「查到 0 ≠ 真为 0」同源 —— 都是「**我拿到的这个东西，是不是我以为的那个东西**」。

---

### 🆕 B-73 认领按 `code` 匹配 ⇒ 明细层编码形态不一致时，认领**结构性失效**（`verified(artifact)`）

**机制**：发行件的「认领优先 / 幂等」以 `code` 为判据。一级科目两边同为 4 位、同码 ⇒ 认领成功；**二级及以下**一边点分（官方 `2221.02`）、一边连号（我方 `2221002`）⇒ **判据永不命中，全部走新建分支**，同一父级下产出两套同义明细。**这不是漏写了一个分支，是判据与数据形态不匹配。**

**实证**（两库全量科目表导出件）：

| 发行档 | 官方点分 | 我方连号 | **同义重复** | 我方独有 | 官方独有 |
|---|---|---|---|---|---|
| **小规模纳税人档** | 27 | 21 | **15** | 6 | 12 |
| **一般纳税人档** | 27 | 31 | **25**（二级 15 + 三级 10） | 6 | 2 |

🔴 **驱动变量是「纳税人档」，不是「chart / 准则」**（R43-T1-b 逐条映射核清）。一般纳税人档比小规模档多发 10 条增值税三级明细，故多 10 条重复；**两档的「我方独有」均为 6 条**。
⚠️ **note 侧曾把这张表按库（`cn` / `cn_large_bis`）分行，写成「ASSBE 15 / ASBE 25」——错了。** 样本里两个变量恰好共变（小企业库用小规模档、大企业库用一般纳税人档），因果被挂到了 chart 上。归族惯例 12：**我拿到的这个东西，是不是我以为的那个东西。**

- **我方独有 6 条**（两库相同）：应交个人所得税 / 应交资源税 / 应交土地增值税 / 应交房产税 / 应交土地使用税 / 应交车船使用税 —— 官方 `2221` 下确无这些地方税种的**负债侧**明细（官方只在 `5403.xx` 建了**费用侧**）。⇒ 这 6 条是真实补缺，**不与重复的那 15/25 条同罪**。
- **官方独有**：`2221.08` 代扣代交增值税、`2221.01.09` 进项税加计抵减 —— 后者我方一般纳税人档**缺失**。
- **名称近似但不等**：我方「销项税额的抵减」vs 官方「销项税额抵减」；我方「应交所得税」vs 官方「应交企业所得税」。
- **官方数据自带毛刺**：`2221.02` 名称尾部带一个空格。⇒ **任何按名称做的同义匹配都更脆**，「判据不写同义」在此再次成立。

🟢 **处置 = 统一编码格式**（R42 后定案：我方统一改点分）。改点分后 `code` 判据自然命中，15/25 条同义重复走认领分支、不再新建 —— **格式统一与重复消除是同一个动作**；反之只修重复，则修完仍不统一。

归族：与惯例 17「计数表述必须平铺」同族，但更前一层 —— **17 管我们怎么数，本条管系统按什么判。判据选错，平铺得再干净也数不出重复。**

---

### 🆕 B-74 官方 chart 含已废止 / 已被取代的历史科目（`verified(artifact)`）

- `5403.02 营业税` —— 2016 年营改增全面完成后已废止，官方仍发。
- `5401 工程施工` / `5402 工程结算` —— 新收入准则下已由**合同履约成本 / 合同结算**取代（`observed`：老制度入存货；新准则借方合同资产、贷方合同负债）。
- `cn_large_bis` 中 **`4401` 与 `5401` 两个「工程施工」并存**（ASSBE 码与 ASBE 码同时躺在一张表上）。
- 而**新准则真正要用的**「合同履约成本」「合同结算」，官方 chart **一条都没有**（`1481 合同资产` / `2204 合同负债` 有）——正面印证「可选自设科目、财政部未给编码」。

⇒ **「官方 chart 里有这个科目」≠「现行准则下还在用这个科目」，反过来「官方 chart 没有」≠「现行准则不需要」。** 差异表比对、归档判据、以及任何以官方 chart 为基线的推论都要多带这一层。

归族：与惯例 16「官方先例证明当下认可、不证明稳定」同族但方向相反 —— **16 管它将来会不会被删，本条管它过去是不是早该删。**

---

### 🆕 B-75 归档动作的样本边界（`verified(artifact)`）

小企业库 181 条中 **49 条被真实从业者归档（27%）**；大企业库 333 条**全部 `有效=True`，一条未归档**。增删判断只在 ASSBE 侧做过。

归档构成：官方点分明细 26 条（`1601`·`1602`·`1606` **各 6**、`1012`×2、`1402`×2、`1122.01`、`1221.02`、`1406.01`、`5403.02`）+ 我方连号 20 条（全为 `2221` 税费档）+ Odoo 技术户 3 条（`1003` 信用卡、`1006` 未结清收据、`1007` 未结清付款）。**一条行业垂直科目都没有 —— 归档的全是通用件。**

⇒ 🔴 **归档结论不得推到 ASBE 侧。** 记此条是为防下个窗口把「27% 被判为不需要」当成跨准则事实引用。

⇒ 🟢 另一面：**27% 这个数本身是指标 1（装机人工步骤数）与销售叙事的可用锚** —— 通用科目表按国家切、中国实务按行业切，切分维度不同 ⇒ 通用件必然**既不垂直、又有多余**，这不是实现质量问题。

---

### 🆕 B-76 推了代码 ≠ 跑着新代码（Odoo.sh staging；`observed`）

**现象**：staging 分支推送新版本后**未执行 upgrade apps**，则数据库中运行的仍是**旧版本代码**。此时一切基于"该库已是新版本"的取证，取的都是旧代码的行为。

**实例**：一份「大企业库 333 条含 31 条我方形态」的导出件，被当成「新版门控失效」的疑似证据下发查证。实测真因是**推了代码但没 upgrade**，门控代码根本没加载；升级后重跑，`cn_large_bis` 一条不加（290 → 290，REJECTED）。

⚠️ **开发侧当时对该 artifact 的推断成因是「R35 pre-gate 时期的历史污染残留」，标了 `observed`（惯例 23），事后证明该推断是错的** —— 两个成因都落在「门控无恙」，但机制不同：前者是已封存的旧账，后者是**随时可重复的操作模式**。

⇒ 与 **B-67**（`-u` 升级不 re-run hooks）同族但更前一层：**B-67 管"升级了但 hook 没跑"，本条管"根本没升级"。** 归族惯例 12。

**落法**：任何以「该库是版本 X」为前提的取证，**回报里必须带该库的实际模块版本号**（`ir_module_module.latest_version`），不得以"我推过代码"代替。

---

### 🆕 B-77 我方记录挂官方共享表：官方 `-u` 不删不改（`verified`）

**形态**：我方模块在**官方拥有的父记录**下插入**我方拥有的子记录** —— `account.report.line`（`suite_cn_statement.cn_asbe_bs_prefix_disclosure`，id 303）通过 `report_id` FK 挂到官方 `l10n_cn_reports.l10n_cn_asbe_bs`（`account.report` id 27）。**表是共享的，记录的归属不是。**

**为什么安全**：官方模块 `-u` 的 stale-cleanup 按 `ir_model_data.module` 键遍历，**只清理它自己 module 名下的记录**。我方行 `module = suite_cn_statement`，不在官方清理范围内 ⇒ **官方 `-u` 不删不改**。且我方**没有改写官方那条 `account.report` 记录的任何字段** —— 与 E-7 那种**外科覆盖**（改写官方记录字段，须先存原值 + `uninstall_hook` 写回 + 原值哨兵）**不是同一类动作**，不要混判。

**先例**：我方 `bal_begin` 列 / 表达式是同一模式（FK 挂官方报表 27），**R15/R16 已验证 survive 官方 `-u`**。

🔴 **唯一耦合 = FK 指向那条官方记录**。官方若删除或重构该报表，我方这些子记录会与既有 `bal_begin` 列**一起**受影响 —— 这是**既有的模块级依赖，不是新增风险面**。⇒ 判「往官方报表加一行」是不是新开 territory 时，问的是**有没有新增耦合**，不是**有没有碰官方的表**。

**与 B-70 的分工**：B-70 管报表 variant 的**可达性**，本条管挂上去的记录在**升级路径上的存活**。

### 🆕 B-78 `_init_currency_table` 是显式幂等的，多入口可各自自建（`observed` 源码 + `verified` 实跑，R49）

`account_reports` 的币种折算临时表 `account_currency_table` 由框架在 `_get_lines` 路径上建好。但**绕过 `_get_lines` 的入口**（自写 XLSX 渲染器直接调取数方法、单元测试直接调 handler 内部方法）进来时**该表不存在**，SQL 直接报错。

**解法**：在取数入口自行调 `report._init_currency_table(options)`。该方法源码是 `DROP TABLE IF EXISTS` + `CREATE ... ON COMMIT DROP`，**显式设计为可重复调用**，多入口各自调一次安全、不会互相踩。

🔴 **一般化**：凡框架「在某条主路径上替你准备好了什么」的机制，**一旦我方开了第二条入口，准备工作就要自己补一遍**。判据 = 数一数「这个方法有几个调用入口」，不是「主路径跑通了没有」。与惯例 29 ③「同一份数据有两条渲染路径」同族 —— **29 管输出漏一条路径，本条管输入漏一条路径。**

🆕 🔴 **第二实例：ORM 尚未落库的写入（`flush_all`）——R50，`verified`。**
自写的直连 raw SQL 取数方法**在执行前不 flush**，读到的是**数据库当前状态**，而 ORM 缓存里尚未落库的写入**读不到**。症状是「与走 `_get_lines` 的另一张表对账少一笔」。

⚠️ **同一条一般化在两轮内被撞了两次**（R49 币表、R50 flush）⇒ 它不是偶发，是**开第二条入口的固定代价**。故把清单显式写出来：

| 绕过 `_get_lines` 直连 SQL 时，必须自己补 | 症状 |
|---|---|
| `report._init_currency_table(options)` | SQL 直接报错（表不存在） |
| `self.env.flush_all()`（或相关 model 的 flush） | **静默少数据**，无报错 |
| 框架在主路径上做的其它准备（options 归一、期间解析等） | 视缺什么而定 |

🔴 **两者的危险度不同**：币表缺失**当场报错**，flush 缺失**静默少一笔且测试可能全绿**。⇒ **越是不报错的那种，越要靠清单而不是靠跑通来防。**

🔴 **绿灯不代表没缺陷 —— R50 的实证**：该缺陷 R49 就已在交付代码里（`git show` 确认），但 R49 夹具的末笔**在 compute 前已可见**，没触发；R50 夹具加了第二条同日 move 才撞上。⇒ **R49 的「63 tests 0 failed」是真绿，不是假绿**。「代码有缺陷」与「绿灯是假的」是**两件事，要分开回答**（惯例 34 的实例）。

🟢 **反向的一条便宜验法**：要证明**另一条**路径 flush 正确，最强的证据往往就是**这次不一致本身** —— R50 判据 9 挂掉，正是因为走 `_get_lines` 的那张表**看到了**漏掉的末笔。**一次跨路径不一致，同时证伪一条、证实另一条。**

### 🆕 B-79 `totals_below_sections` 会在有子行的 section 下自动插合计行（`observed`，R49）

官方 `account_reports` 的 `totals_below_sections` 选项：**任何带子行（`parent_id` 指向它）的 section 行，框架会在其子行下方自动插一条「Total ⟨section 名⟩」**。做**报表**时这是想要的；做**账簿**时不是 —— 中式账簿里一个科目段的末行是「本年累计」，多出一条 Total 行，会计看见必问。

**规避**：账簿类输出用**扁平行序列**（段头行不带子行 ⇒ 不触发），段内顺序即装订顺序，另加一条测试钉住「不出现 Total 噪声行」。

⚠️ **这不是缺陷，是形态错配**：官方那个行为对报表是对的。⇒ 凡把 `account.report` 拿来当**账簿**载体，先盘一遍「框架为报表加的东西，在账簿上是不是噪声」。

---

### 🆕 B-80 Odoo 19 存货数量的取数面：`stock.valuation.layer` 已移除 + `aml` 侧恒占位（R52-T3，`verified` 除标注外）

🔴 **三条一起构成「存货数量不能从会计分录取」这个结论**，缺一条都不足以定案。

| # | 事实 | 级别 |
|---|---|---|
| 1 | **`stock.valuation.layer` 在 v19 已移除** → 数量与价值改由 `stock.move.quantity` / `stock.move.value` + `product.value` 承载；`stock.move` **无 `name` 字段** | `verified` |
| 2 | 🔴 **`perpetual`（=「at invoicing」）下，`stock.move._action_done()` 之后 `account_move_id = None`** —— 存货科目的会计分录在**开票 / 期末结转**时才生成 ⇒ **移动完成的那一刻 `aml` 尚不存在** | `verified` |
| 3 | 🔴 **`account.move.line.quantity` 在 `display_type='product'` 下恒占位 `1.0`**（非真实数量），`uom=False` | `verified`（**确认为占位、非空**） |

🔴 **第 2 条是决定性的**：断掉「从分录问数量」这条路的**不是覆盖面高低，是时序上不存在**。
🔴 **第 3 条的危险性高于「为空」** —— 为空会被发现；**恒 `1.0` 会渲染出一张看起来正常、数量全是 1 的表**，且所有「相等 / 非空」形态的断言仍然全绿（惯例 30 那个形态）。
**桥的方向**：`account.move.line` 上**无任何** `stock`/`valuation` 字段；唯一桥是 `stock.move.account_move_id`（**`stock→account` 单向**，且 move-done 时未接）⇒ **不存在「总是可用」的正向 `aml→数量` 路径。**
**官方现状**：无官方报表按聚合 `aml.quantity`；存货侧另有 `stock_avco_audit_report` / `stock_valuation_report`；`l10n_cn_reports` 仅 BS/PL。

🆕 🔴 **补一条时点差（R53 实测，`verified`）**：**修改 `stock.move.value` 不回溯已过账的 `aml`** —— 存货估值改动**不会自动传导到已过账分录**。
⇒ 两源之间**不只是路径差，还有时点差**：同一笔业务在 `stock` 侧与 `account` 侧可能**各自停在不同的值上**，且这是正常行为、不是数据损坏。
⚠️ **对账判据的含义因此要收窄**：金额维「对得上」意味着**两源在当前时点一致**，不等于「两源永远同步」。

**落法**：凡「按会计科目出带数量的账簿 / 报表」，**取数源走存货移动侧、按 `product → 估值科目` 归集**，并**显式声明「非存货科目的手工凭证数量不可得」**（**产品边界，不是缺陷**）。
⚠️ **换源的连带效应**：换源之后，该报表与走 `aml` 的总账 / 三栏式**不再共用上游** ⇒ **金额维仍可对，数量维没有第二条路径可对**。这反而是**真互证**的雏形（两条独立取数路径），**不是**共模的「跨路径差量检验」—— 对账判据须重新设计，**不可照抄**（`项目档 §4.5.22 七` / `§4.5.23 六-bis`）。


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
9. **「哪个变体」的选择器必须查两条轴**：变体**存在** AND **上下文与该变体匹配**。只封一条轴等于没封——封住「变体缺失时不回退」，却放任「变体对了但期间/范围不对」，产出的仍是贴着正确标签的错口径文件。**拒绝产出错标签的文件，好过静默换口径。**
10. **跨仓库/跨文档引用要带被引方的版本号**。回写是单向动作，防不住被引用那一侧后来变了；引用时标注依据版本（如「依据 design draft-26」），下个窗口看到版本号对不上就知道要复核，不必逐条比对。同理，**从新节引用旧节时必须同时改旧节** —— 读旧节的人不会跳到新节，单向引用会攒矛盾。
11. **凡改动了「点击后发生什么」的入口，走查必须跑到终态**（向导弹出、文件落地、数据可见），不是跑到按钮可见为止。
   依据：R26 的 `_preprocessAction` 崩溃 —— Python 方法手工返回的 `ir.actions.act_window` 字典缺 `views` 键，客户端 `action.views.map()` 直接炸。三维齐验全过、11/11 live 过、按钮可见，**一点就崩**。这是惯例 1「数值正确 ≠ 用户找得到」的一个未被覆盖的子面：**入口可见 ≠ 入口可用**。
   修法：用 `ir.actions.act_window._for_xml_id(...)` 取动作（`views` 由服务端算，顺框架），或手工 dict 里显式给 `'views': [(False, 'form')]` —— 只写 `view_mode` 不够。
12. **只读探针要先确认查的是正确载体：查到 0 ≠ 真为 0。**空结果有两种成因——真的没有，或者查错了对象（错公司 / 错库 / 未装数据 / 过滤条件不同）。回滚事务里的 0 尤其骗人，因为它看起来像一次干净的实测。
   依据：R27-T2-B 在 dev 库的 `CN ASSBE Company`（chart 未装、0 账户）上查 `account.group`，得 0，误报「本库 0 组」；实际装了 chart 的是同库另一家 CN 公司。
   这是惯例 2「单公司通过 ≠ 多公司通过」的同族：**惯例 2 管"通过"，本条管"没有"。**任何以"某某为 0 / 不存在"为前提的结论，先回答「我查的是哪个主体、过滤条件是什么」。
   **配套**：还要回答「**我查的这个库是什么性质**」—— demo/测试数据上得出的结论，不能用来推真实客户的行为。R27 曾据 dev demo 库的科目表推出"客户不建二级科目"，无效。
   🆕 🔴 **第四变体（他方演示账套，2026-08-18）**：上面那句配套讲的是**我方**的 demo 库；**他方厂商的演示 / 试用账套同样适用，而且更险** —— 因为它看起来像「厂商官方出品」。**被改的不只是数据，还有配置**：报表公式可被用户自由编辑、行项目可被增删。
   **实例**：金蝶「通用行业（旗舰版）」的 ASSBE 资产负债表导出件 —— ① 表**不平**（资产总计 − 负债和所有者权益总计 = 869,459.00，年初与期末同一差额）；② BS 公式里「**短期借款**」被配进「**货币资金**」项目；③ 导出件负债侧**没有「短期借款」行**，致**行次整体较准则 +1**（货币资金显示为行次 2，官方是 1）；④ **列序与准则相反**（年初在前，官方是期末在前）。
   ⇒ **判读分层**：**形态**（有哪些列、怎么排版）与**产品行为**（不平照出、不拦截）**可以引**；**行集 / 行次 / 列序 / 金额不可引**，那些的锚只能是**发布方原文**。
   **自查**：引用他方材料下任何「这张表就长这样」的结论前，问一句「**这份是产品出厂态，还是有人在上面建过账**」。
   🆕 **第三变体（渲染语言造成的假 0，R32）**：报表行名会**按 UI 语言渲染**。dev 库 UI = en_US 时，按中文名「应收账款」过滤命中 ∅，是**语言假象不是没取到**。R32 全程改按**金额锚定**（carriers）定位命中。⇒ 惯例 12 现有三个变体：**查错载体**（R27，本条正文）、**载体没 flush**（B-61）、**渲染语言假 0**（R32）。三条同族，"命中 0"之前都要先答一句「我这个 0 是真的没有，还是查错了 / 没落库 / 语言渲染成了别的字」。
   🆕 🔴 **落法扩写（R54，两例同族）：凡用【包含】代替【相等】做出的判定，其计数一律不作数。**
   **形态**：工具在前提不满足时**不报错、给出一个外观可信的错误结果** —— 这不是「没查到」，也不是「确认为 0」，是**第三种成因：工具静默降级**。原条管前两种，管不住这一种。
   **实例（同一轮内两次）**：① `join` 对未排序输入**静默丢行**，只在 stderr 抱怨一句 `input is not in sorted order`，得到假「0 不一致」；重名键还会笛卡尔交叉出假对（两个同名科目 join 出 6 条换号，实数 4）。② `expected in xml_text` 判覆盖是否仍匹配，因 `1406` 是 `1406 + 1408 + 4001 + 4101` 的子串、`140 + 142 + …` 是新值的前缀，得到两条假「仍匹配」（真数 5，报了 3）。🔴 **第二例工具全程不吭声**，比第一例更隐蔽。
   **落法**：报「N / M 条」时**同时声明前提已满足** —— 输入已按 `LC_ALL=C` 排序、连接键**唯一**（无重名笛卡尔）、判定用的是**全等而非包含**（结构化数据请按 id/label 定位后比值，不要拿文本裹）。**未声明前提的计数视为未验证，即使它是 0、尤其当它是 0。**
   **正面做法（同轮）**：用共有 id 数 65/88/195 逐份对总账，对得上才作数；改用 `ElementTree` 按 record id + label 定位再比全等；字典条目数改用 `exec` 求值而非 `grep` 字面量（那个字典是推导式，`grep` 只匹配到 4 行无关字面量，真值 99）。
13. **实测得出的事实必须落主题索引，不能只落变更流水。**按时间追加的变更记录（design changelog、commit message、轮次回写）是**流水账不是索引**：下个窗口按主题找不到，只能重推一遍。
   规矩：任何"某系统实际怎么表现"的实测结论，除了写进本轮回写，**必须同时落到一个按主题组织的位置**（本档 §7 的 B-xx，或项目档的对应节）。
   依据：l10n_cn R17-C 组的合规机制实测，三个窗口后被 R27 完整重做。代价不只是重复劳动——**旧结论中那条不完整的表述在这三个窗口里一直被当成已结案引用。**
14. **一次验收里若有强弱两组证据，弱的那组必须自带标签。**当某组测试**按设计必然通过**（改动在该场景下不产生差异、或该维度的值恰好为 0），它的「全绿」不构成任何正确性证据；而回报里两组并列时，读者默认它们等权。
   规矩：回报中把弱证据组**显式标成「预期结果，非证据」**，并指明**唯一构成证据的那一组**是哪个。
   依据：R30-T2b。dev 库无子账户（`2202C = 净额`、`2202D = 0`），明细级 D/C 改动后逐格值**与改前完全相同**，回归双跑必然零差异；唯一能证明正确性的是**有子账户夹具**（`2202.01 贷500 / 2202.02 借100`）。若不标注，下个窗口看到「双跑全绿」四个字就会认为改动已被验证。
   这是惯例 6「值算 0 会掩盖结构问题」的**回报文本侧**：惯例 6 管**怎么测**，本条管**怎么写测出来的东西**。
   🆕 🔴 **第二实例（R49）：同源、构造必等的两表比对，不是「互证」。** 我方总分类账与科目余额表**共用同一套取数**（同一 roll-up 键、同一 `_get_report_query` 窗口，总分类账只多「按月分组」一层），交付方自己也写了「**构造必等**」。⇒ 这条比对能抓的只有**月层聚合新引入的错**，**抓不到两表共用的那段上游错**（共模失效，两张表会一起错、一起绿）。
   **它仍有价值，但价值不是「互证」。** 真互证需要**一条完全独立的取数路径**（如另写一段直接从 `account.move.line` 聚合的对照）。
   **落法**：措辞里出现「互证 / 交叉验证 / 两个来源对上了」之前，先答一句「**这两个来源共用了哪一段代码**」。共用了，就把措辞降下来。**下单方尤其要防** —— 这条错的措辞是写在施工单里由下单方带进来的，执行方照着抄了一遍。
   🆕 🔴 **第三实例（R50）：降级的方向对了，词却用窄了 —— 「同源一致性检验」应为「跨路径差量检验」。**
   R49 降级时说「两表共用取数、构造必等」，据此判它抓不到东西。**R50 它抓到了一个真 bug**（直连 SQL 缺 `flush`，少读一笔）。原因是**两条路径并非全同源**：其中一张表有一段**自己独有的直连 SQL**，另一张没有。⇒ 这条判据覆盖的**恰恰是两条路径的差量**，而差量正是新缺陷的产地。
   **「同源」二字把它说小了**，会让下个窗口以为该判据没价值而不再维护。**正确命名 = 跨路径差量检验。**
   🔴 **同时附上它的有效边界**（执行方 R50 原话，逐字保留，本档第一次为一条已通过的判据写明适用条件）：
   > **cross-check 测试通过 ≠ 证明 flush 路径普遍正确 —— 只在「末笔已可见」的夹具下才成立。**
   ⇒ **一条判据的价值 = 它覆盖的差量面，不是它是否绿。** 降级要降到**正确的名字**上：降过头与不降，两种错都会让后人误判它的强度。
15. **grep 之前先确认工作树是完整的。** sparse-checkout / shallow clone / worktree 会把「全树 grep」悄悄变成「部分目录 grep」，而**命中 0 的输出与"确实不存在"长得一模一样**。
   **判据**：任何形如「全树命中 0」的结论，先答一句「**我这棵树是完整的吗**」——`git sparse-checkout list`、`git rev-parse --is-shallow-repository`、顶层目录数 vs `git ls-tree` 项数。
   依据：R31。社区 master 工作树启用了 sparse-checkout（仅 7 个目录），两次"全树 grep"（`account.group`、`code_path`）实际只覆盖了这 7 个目录；执行方自查发现后展开全树重做。**该失误由执行方自陈，判据因此被证明可执行。**
   归族：与惯例 12「查到 0 ≠ 真为 0」、B-61「未 flush 引擎取不到」同族——惯例 12 管**查错了载体**、B-61 管**载体没落库**、本条管**载体被截断**。引用时一起读。
16. **「官方先例」证明的是"这个写法当下是官方认可的"，不证明"这个写法稳定"。**
   先例能挡住「我们是不是用错了」，挡不住「它会不会被删」。凡以"某官方本地化模块也这么写"作为设计依据的，**必须同时记下先例的版本锚**，并在版本迁移时**把先例本身也当成待核对象**。
   依据：B-58 当初以越南 TT200（`l10n_vn_reports`）为官方先例给 `sum_if_pos` / `-sum_if_neg` 背书；官方在 `odoo/enterprise@e7439ee932ab` 删除该机制时，**在同一个 commit 里把越南那份也改了 630 行**。
   归族：与项目档 §9.1「结论有保质期」同源，只是对象从**我方结论**换成了**他方先例**。
17. **计数表述必须平铺，不得用乘法式。**
   「N 行 × M 表达式 + K」这类写法隐含「集合内每处同构」。一旦集合里存在**异质项**（单表达式、不同 label、不同 xmlid 归属、不同引擎），异质项会被**结构性排除在计数之外**；更糟的是，复核的人会跟着做同一次乘法，**复现同一处漏**——所以它不是一次笔误，是一个会自我复制的表述缺陷。
   **落法**：凡须逐条比对的集合（覆盖清单、原值基线、差集表、迁移面），一律**一行一条平表**，并显式给出每条的**归属列 / 类型列**，让异质性在表面上可见。
   依据：`项目档 §4.5.12-E7` 的「3 行 × 2 + 1 = 7」把 `prev_year_earnings`（`balance_domain` 单表达式）排除，致同一条表达式被两种机制各漏一次（详见 §7 B-65）。
   这是惯例 13「实测事实必须落主题索引」的**表述形状**侧：惯例 13 管**落在哪**，本条管**落成什么形状**。
   🔴 **补一句（R35）：平铺只是第一步，平铺之后必须追问「异质列是否意味着机制该分叉」。** 实例：8 条台账平表的 `xmlid 归属` 列已把「我方 3 + 官方 5」显示出来，注 1 也据此推出「脱钩时前者重建、后者只需重覆盖」—— 但**只应用到了未来的脱钩任务，没有回头应用到当下的覆盖机制**，而那 3 条本就是我方自己的静态数据、根本不该绕道用另一模块的 hook 覆盖自己。**把异质性显示出来而不追问它，等于白平铺。**
   🆕 🔴 **再补一句（R49）：正向哨兵 `>0` 不能代替实数计数。** 惯例 30 要求断言前加「参与数 > 0」的哨兵，惯例 17 要求回报给出**两个实数**（参与数 / 不成立数）。两者是**两条不同的惯例**：哨兵管「有没有跑到」，计数管「跑到了多大面上」。R49 回报把四条判据全写成「参与 > 0 / 不成立 0」，**哨兵满足了、计数没有** —— 读者无从判断那条交叉对账覆盖的是 3 个科目还是 100 个科目，而**覆盖面正是该判据的全部价值**。同一批人在 R47 是给了实数的（参与 5 行 / 不成立 0 行），⇒ 这是**表述退化不是能力问题**，只能靠回报格式来防。
   **落法**：判据表里「参与」那一格**必须是数字**，不得是 `>0`。
   🆕 🔴 **第三条（R50）：填了数字也可能是假的 —— 实数必须从断言的实际输出誊抄，不得凭印象填。**
   R50 的回报摘要里，六条判据的「参与」格**全填了 5**。实测真值是 **4 / 8 / 8 / 8 / 5 / 13** —— 六个口径各不相同（期初非零段 / 期次转移 / 期次对 / ytd 转移 / 科目 / 栏位），**是同一个 5 被填进了六格**。**测试代码本身一直是对的**（断言消息里 `%d` 取的是 live 计数），错只在人写的摘要。
   🔴 **假数比没数更坏**：没数时读者知道自己不知道；假数会让人以为夹具是「5 科目 × 5 期的整齐结构」，从而**对判据强度做出错误估计**——而覆盖面正是这些判据的全部价值（本条第一句）。
   **落法**：断言消息里已有 `%d` 的，**直接贴那行输出**，不要复述；一组判据的参与数**若恰好相同，须显式说明它们是不是同一个口径**。
   **序列**：R49 给哨兵不给实数 → R50 给了编造的实数。**同一条惯例的第三次失守，形态一次比一次隐蔽。**
   🆕 🔴 **第二例：立条者同日自犯（2026-08-18）。** 本条刚写进档的同一天，note 侧在 R50 施工单里写下「**原件 9 个科目里 4 个是平**」—— 那个 9 **是凭印象估的，没数**。回数原件：`1002`/`1122`/`2202`/`2211`/`2221`/`2241`/`3103`/`3104`/`4401`/`5001` 已 **10 个**，`5301` 起头被截断，且页眉写「**第1页 共2页**」，第 2 页从未见过。**真值是「≥10，未知上限」。**
   该错**被执行方原样引用**（回报里「原件那张金蝶总账是 9 科目」），又被 note 侧写进 `status` 待办「铺到 9 科目」—— **一个估数在两份文件里变成了目标值。**
   ⇒ **补一条落法**：凡「原件上有 N 个 X」这类**对材料的计数**，必须在同一句里写明是**数过**还是**估的**；估的一律写「**约 N，未数**」。
   ⚠️ **附带教训（比计数本身重要）**：「铺到 9 科目」这个待办**目标就设错了** —— 夹具该按**形态清单**核覆盖（反向 / 零余额「平」/ 只有期初 / 损益结转 / 有子目的父科目 / 跨年期初），**科目个数是结果不是目标**。凑数到 N 可能只是把同类形态重复一遍，不产生新覆盖。
   🆕 🔴 **第四条（R51）：几格参与数相同，有三种成因，处置各不相同 —— 必须答是哪一种。**
   第三条的落法（「实数须从断言输出誊抄」）只防得住「一个数被填进多格」这一种。R51 出现了**第三种形态**：
   判据 2/3/5/6 的参与数**同为 7**，是**同一批 7 个「科目-期段」被四条判据各验了一遍**（余额连续 / 发生额==Σ明细 / 累计==本期合计 / 跨路径差量）—— **同口径、合法，且这正是覆盖面的证据**；
   而**同一张表里**判据 4 的 **7** 却是**另一个口径**（转移数），且是 `真实跨期转移 3 + 首期基线 4` **两个强弱不等的口径被加号合并** —— 「与 0 比」和「与上一期真值比」验的强度不是一回事，合并之后读者会把 **3 当成 7**。
   **落法（几格同数时，必须三选一作答，不得沉默）**：
   - **① 同口径、多条判据复验**（判别：参与对象是同一批）⇒ **合法**，写明「同口径 N 个 X，被 k 条判据各验一遍」。
   - **② 一个数被填进多格**（判别：口径本不同、数却相同）⇒ **假数**，重取（第三条）。
   - 🆕 **③ 口径不同而碰巧相等**（判别：拆开后两半不等）⇒ **必须拆开分列**，并把弱的那半显式标「弱」（惯例 14）。

   **序列**：R49 给哨兵不给实数 → R50 编造实数 → note 侧同日自犯 → **R51 口径合并**。
   🔴 **四次失守，形态一次比一次隐蔽，但四次都发生在【回报摘要】这一层 —— 测试代码里的 `%d` 始终是对的。**
   ⇒ 落法再收一格：**判据表的「参与」格应直接贴断言输出那一行；「手写转录」这个动作本身就是缺陷面**，不是靠细心能防的。
   🟢 **附一条正面实例（同轮，R51）**：三格非数字（判据 6 填了「参与」二字、判据 8/10 只给了不成立数）被指出后，执行方**当场以 in-tx 探针重取真值**（10 行 / 7 期 / 7 对 / 2 行 / 22 栏位）、**自陈根因**（`1001` 的单段期数 3 被填进多格）、**同轮回写 design 并注明「纠前次误填」**。
   与惯例 15 那次「执行方自陈 sparse-checkout」同族 —— **一条判据的可执行性，不看它被写得多严，看它被指出后能不能当场重取真值。**

18. 🔴 **一组数据被拆到两条加载路径时，先问它们是否必须同步 —— 部分重放比完全不重放更坏。**
   完全不重放，至少一组数据整体停在旧态、内部自洽（都错，但一致）；**部分重放会造出一个自相矛盾的中间态**，而中间态往往没人测过。
   **实例**：把一组表达式中的 3 条改由 XML `data` 承载（随 `-u` 重载）、另 5 条仍由 `post_init_hook` 承载（不随 `-u` 重跑），升级后**同一张表的两列来自两个年代** —— 年初列已是新值、期末列还是旧值，实测破 `30=53` 差 500。
   **落法**：凡改动使一组数据分走两条加载/执行路径，**必须同时回答「它们是否必须同步」**；答案为是，则同一次改动里就要把慢的那条补上（migration / hook / 显式重放），不能留到下轮。
   与惯例 17 相连：17 让异质性**可见**，本条要求对可见的异质性**追问后果**。
19. 🔴 **验收判据必须写成绝对终态，不得写成"改善量"。**
   "修好后应当 **+6000**" 这类写法混淆了「相对于破损态的改善」与「正确的绝对值」。**修复方要照着判据验收，写错了就会验到一个错的目标。**
   **实例**：`Dr 5001 / Cr 1403` 是**存货内部结转**（`5001` +6000 与 `1403` −6000 **都在存货口径内**），正确终态是**净 0**；施工单误写"存货 +6000"，把"相对 −6000 的改善量"当成了绝对值。同一形状在另一准则侧（`Dr 4001 / Cr 1403` → 存货 0）曾经写对过，**说明这是笔误而非认知错误 —— 也正因如此，它只能靠判据格式来防，防不住靠细心。**
   **落法**：判据一律写「X 应等于 N」，不写「X 应增加 N」「X 应回到正常」。
20. 🔴 **顺序依赖类问题必须复现顺序 —— 查"当前状态"答不了"按某顺序产生的状态"。**
   一个库现在是好的，不能证明"按另一种顺序装出来也是好的"。**尤其当现有库的那个条件根本停不掉时**（如已被用户使用的语言无法停用），"在本库测"这条路是走不通的，须**另开全新库按目标顺序重来**。
   **实例**：验"先装科目表、后加语言会不会永久英文"，在一个语言一直激活的库上查当前 jsonb —— 结果是双键正常，但**这不是那个问题的答案**。
   **落法**：凡问题里含"先…后…""在…之前/之后"，回报中必须写明**是否真的按该顺序复现过**；没复现就标 `unknown`，不得用当前状态代答。
21. 🔴 **`observed` 的采纳门槛随结论方向不对称。**
   同样是 `observed` 级证据，**指向我方缺陷、或指向更保守说法的，可以先行采纳**（改文档、改对客户的说法）；**指向我方免责、或指向更有利说法的，必须等 `verified`**。
   **理由**：两类错的代价不对称。保守方向若日后被推翻，损失是"我们过度谨慎了一阵"；有利方向若日后被推翻，损失是"我们对客户说过一句错话"，而话已经说出去了。
   **实例**：R38-T2 从源码读通「官方 chart 会被回填 ⇒ 官方不中招、**我方独中**」，仅 `observed`。这条对我方不利（等于承认永久缺 `zh_CN` 键的是我方发行的科目），故**按 `observed` 就改对客户的说法**；反之若源码读出的是「官方同样中招、非我方独有」，则必须等活体 `verified` 才准写进对外材料。
   与惯例 16「官方先例证明不了稳定性」同族：都是**证据强度与使用方式的匹配问题**，不是证据本身的问题。
22. 🔴 **待办条目必须自带可执行内容 —— 只有指针没有内容的条目不得进待办档。**
   一个条目若无法回答"做完是什么样"，它会永远挂着：接手的人看不懂要做什么，只能原样再传一轮，而每传一轮它看起来都更像"已知问题"。
   **判据**：写进待办前先自问「**换一个人来，照这条能不能动手**」。不能，就要么当场补齐内容，要么不写。
   **实例**：`status` 里「design draft-36 四处落档缺陷」挂了**六轮**。四项具体内容在项目档、status、background、design 与历轮对话中**从未枚举**；开发侧两次回报"全文搜不到此列表"，是正确回答而非失职。第六轮由 note 侧销号，依据之一是 `§17.4` 的落点建议（B-53…B-65）**早已在本档 §7 全部有 home**——即便那四处曾存在，承载内容也已被后续轮覆盖。
   与惯例 13「实测事实必须落主题索引」互补：13 管**结论**要落到能查的地方，本条管**待办**要落到能做的程度。
23. 🔴 **事后推断的「成因」必须显式标 `observed`；`verified` 只能来自按原路径重跑。**
   若某次事故的成因来自**事后据下游证据反推**、而非当场取证，须显式标 `observed` 并写明「未按原路径重跑」。
   **实例**：l10n_cn R35「`post_init` 误发到别公司」这条成因**被引用了六轮**，一直撑着「缺陷 #1 必须修」的判断，直到 R41 在真实版本上按原路径重跑一次才发现是 wizard 路径。原始记录**自己标了「来源非第一手」**——**标了来源还不够**：来源分级管的是「这段话哪来的」，而**推断出的因果本身是一个独立的断言，也要各自挂级**。
   **落法**：凡「因为 X 所以出了 Y」的结论，问一句「X 这一步我看着它发生了吗」。没有，就是 `observed`。
   与惯例 21 同族（证据强度与使用方式的匹配），与惯例 12 / 20 同族（我查的到底是不是那个东西）。
24. 🔴 **验收判据下发前须自查可达性 —— 尤其当本方近期交付的门控/校验可能把待观测状态变成不可构造。**
   下发前问一句：**这个状态，在当前版本上还造得出来吗？**
   **实例**：R42 施工单 T1 同时要求「验证 R38-T3 门控挡得住激活前发行」与「观测我方账户在激活前的 jsonb」——**后者正是被前者封死的状态**。开发侧当场拦下并换可达对照组，处置正确；但判据本身自相矛盾，是下单方的错。
   **推论（同样重要）**：当一个状态因**本方修复**而不可构造时，正确处置是记为「**构造性关闭**」，**不是**永远挂 `observed` 待验 —— 否则下个窗口会反复尝试去验一个已经不存在的东西，而且每验一次失败都更像「这里有问题没查清」。
25. 🔴 **向领域专家提问时，凡问题里含平台的技术字段名，必须把该字段的作用写进问题 —— 不要出现字段名。**
   领域专家会按**本领域的同名概念**作答，而平台字段与领域概念往往**同词不同义**。拿到的答案语法正确、方向明确、**且看起来像是答了**，因此**比「没回答」更危险**。
   **判据**：提问前自查「这个词在他那里和在系统里，是不是同一个意思」。不是，就改问**这个字段在系统里实际决定什么**。
   **实例（同轮完整闭环）**：
   - 含字段名：「`1012` 的 `account_type` 是不是该改」→「流动资产是对的」⇒ 读作「别改」
   - 绕开字段名：「`1012` 余额在编现金流量表时算不算现金及现金等价物？受限的保证金要不要剔除」→「**不要剔除**」⇒ 读作「要改成 `asset_cash`」
   **两次方向相反，而第一次更像结论。** 若按第一次结案，会把一条**正确的告警**当错的删掉。
   🆕 🔴 **第二例（R52，2026-08-20，反向形态：问句太粗，答句失真）** —— 本例**不含字段名**，仍然出错，说明本条管的不只是「字段名」，是**问句的适用面**。
   note 侧想确认「明细账**最后一页最后一行**是不是有一行『合计』」，问出去的却是「**剩下那几页**（能不能给）」⇒ 二姐答「**都是一样的呀**」「选择的月份多就每个月显示完」。
   **她答得没错**：在**版式**层面（列集、行型规则）后面几页确实一样。**但我要问的恰好是只在末页出现的那一行** —— 原件到手后证实：末页**比其他页多一行且只多这一行**。
   ⇒ **答句在自己的适用面内为真，在提问者的适用面内为假。** 这比「答错」更难发现，因为它读起来像已经答了。
   **落法（补）**：问「有没有 / 在哪 / 是什么」时，**把定位词写到最细的那一级**（哪一页、哪一行、哪一格），**不要问「一样不一样」「还有没有别的」**这类需要对方猜适用面的问法。
   **改写示范**：❌「剩下的页能给我吗」→ ✅「**最后一页最下面，有没有一行摘要写着『合计』的？如果有，它的日期栏是空的吗、余额栏有数吗？**」
   与 §7 **B-72** 互为表里：**B-72 管这个坑存在，本条管怎么不掉进去。**
26. 🔴 **凡以「该库是版本 X」为前提的取证，回报必须带被测库的实际模块版本号**（`ir_module_module.latest_version`），**不得以「我推过代码」「我装的是新版」代替**。
   **实例**：一份「大企业库 333 条含 31 条我方形态」的导出件被当作「门控失效」疑证下发查证，耗掉一整个阻断项。真因是**推了代码但没执行 upgrade apps，跑的仍是旧代码、门控未加载**（§7 **B-76**）；升级后重跑，`cn_large_bis` 两档纳税人身份均 REJECTED、290 → 290 一条不加。
   **同轮次生教训**：开发侧对该 artifact 的推断成因（「R35 pre-gate 历史污染残留」）**事后证明是错的** —— 因按惯例 23 标了 `observed`，一次重跑即翻掉、成本为零。对照 R35 那次错成因撑了六轮才塌，**惯例 23 在此回本**。
   **落法**：取证脚本第一条查 `latest_version`，与回报表第一行并列。**版本号是取证的坐标，不是背景信息。**
   🆕 🔴 **补落法 (a)（R54）：对版至少两条锚，其中一条【不依赖任何文档】。**
   档会漏记、会写错、会指向另一份档。**代码自身的属性才是不会漂的锚。**
   **实例**：R54 要确认「拿到的代码 = R53 交付版」。第一条锚是 design `draft-52` 记的 `19.0.1.26.0 → 19.0.1.27.0`，与 `__manifest__.py` 对上；第二条锚是 `grep -c "^\s*def test_"` 逐文件求和 = **122**，且 `test_quantity_ledger.py` 恰为 **26** —— 与 `status §2` 记的 `122 = 94+26+2` 一致。**第二条不依赖任何档。**
   🆕 🔴 **补落法 (b)（R54）：声明源码基线时，必须写清读的是哪一类 ref** —— 工作树 HEAD / 本地分支 / **远程跟踪分支**。
   `git show origin/X:` 与 `git show X:` 在同一台机器上可相差数百个 commit（实例：`origin/19.0` 在 `fecc29dd`、本地 `19.0` 在 `40d84d17`，**相差 387 个 commit**），而两者写进回报**都长得像「我读的是 X」**。
27. 🔴 **施工单开头须声明「本轮需要什么起始状态」；库的某些初始状态是一次性耗材。**
   语言激活、未激活态、某个特定版本的存量现场 —— 这类状态**用掉就没了**，事务 rollback 救不回来（激活是单向门），只能靠重建环境重新制备。
   **实例（两次）**：① R42-T1 用掉 `develop-6` 的「`zh_CN` 未激活」起点；② R43 把 `develop-6` `-u` 升到 3.0.0，它既不再是干净起点、也不再是 R42 那个库。
   **落法**：施工单第一段写明所需起始状态与制备方式；**回报时写明该状态是否已被本轮消耗**，供下轮排期。
   🆕 🟢 **补一条同形态的落法（R50 首用即见效）：起始状态不止是「库的状态」，还包括「执行方读到的文档版本」。**
   跨窗口协作里，执行方是**自己去仓库拉档**的；下单方引用了 `§4.5.22`，而执行方拉到的是**尚未推送的上一版**，那一节根本不存在 —— 于是他要么停下问，要么照着旧规则做，**后者不会报错**。
   **落法（两半，缺一不可）**：① 施工单「起始状态」段**逐份列出所依赖的文档版本号**，并写明「对不上就停下问，不要凭空推」；② **回报里回显实际读到的版本号**。
   ⚠️ 注意 GitHub raw CDN 有几分钟缓存 —— 「拉不到」要等一会儿再判。（原文此处引「惯例 4」，**是个错引**：§8 惯例 4 讲的是改目录结构后先 rebuild；raw 负缓存那条实际在 `index.md §取用规矩 第 4 条`。**引用已就地订正**。）
   🆕 🔴 **补一条（R54，2026-08-21）：一轮若【跨窗口】，note 侧须在 `status` 留【中途状态】。**
   此前每一轮都在单个对话窗口里从下发跑到结项，故从不需要这个位置；`status §3` 记的是**事项**，不是**某一轮跑到哪了**。窗口会丢，仓库不会 —— **中途状态不落档，等于整轮进度只活在一个会话里。**
   **必须含**：锚（双仓 SHA + 抓取日期 + 基线口径）· 已闭清单及其落点 · **未闭清单及卡在哪、下一步怎么查** · 被测物在哪台机 / 哪个 ref / 怎么对的版 · 本轮登记但不动的项。
   🔴 **判据（写的时候自问）**：**新窗口只读 `status`，能不能接着往下跑而不重问一遍？** 答不出的就是缺的。**轮次结项后本节清空**，结论并入常设各节。
   **实例**：R54（v20 影响面评估）跨窗口，`status s-35 §11` 即按此建。
   🆕 🔴 **补两条落法（2026-08-19，note 侧连撞两次）**：
   **(a) 「档已推 / 未推」是一个断言，发令方与执行方同样要举证（归族惯例 32）。** 口头确认不算证据 —— 双方都可能记错自己有没有点那个按钮。**核验方法 = 拉 raw 比对版本号与字节数**，一条命令的成本。⚠️ **本条的正面用法**：note 侧据「已推」在错基线上写档，产出会整批作废；先核对再动手，是惯例 27 第一次用在 note 侧自己身上。
   **(b) 🔴 判断 raw 拿到的是不是【陈旧副本】，看响应头，不要靠推理。**
   看两个字段：**`x-cache`**（`HIT` = 命中缓存副本）与 **`source-age`**（该副本的秒龄）。**若 `source-age` 大于「推送距今的时长」，拿到的必然是推送前的旧内容** —— 等它过期重拉即可，**不得据此推断「推送失败」**。
   ⚠️ **三种看起来像绕过缓存、实际都没用的做法**（实测无效）：① URL 加随机查询串 `?cb=xxx`（**缓存键忽略查询串**）；② 请求头带 `Cache-Control: no-cache` / `Pragma: no-cache`（**不强制回源**）；③ 换 `refs/heads/main/` 与 `main/` 两种路径形式（**同一缓存对象**）。
   ⚠️ **一条特别容易骗过自己的反证**：「同一时刻新上传的**图片**拉得到，所以不是缓存问题」—— **不成立**。新文件是**全新路径、无既存缓存对象**，首次请求必然回源；被更新的旧文件命中的是**既存副本**。**两者不可比。**
   **实例（2026-08-19，note 侧）**：Safi 推送三份档后，note 侧连拉四次均得旧版，据上述①②③与图片反证断言「不是 CDN 的问题、多半没推成」，让 Safi 两次回去查仓库 —— 而 `x-cache: HIT` + `source-age: 278` 就在响应头里，比推送时间还老 4 分钟，**一眼可判**。等约 5 分钟后重拉即得新版，逐字节 sha256 一致。⇒ **不是「查得不够」，是「有直接观测却用了推理」**（惯例 33 第三例）。
28. 🔴 **凡档里写「材料已制备 / 已到位」，必须同时给出仓库路径 + raw 链接；给不出路径的，一律写「尚未制备」。**
   **失败形态**：把「我已经分析出来了」写成了「材料已制备」。**分析活在对话里，产物应当活在仓库里** —— 对话窗口一关，分析就没了，档里只剩那句「已到位」，而下游据此排期、下施工单、列随单材料，一路到开发侧才发现拉不到。
   **实例**：`l10n_cn_ASBE_unexecuted_rowset.md` 被 `status §5` 记为「材料已到位（v29 重判）」并两次列入施工单随单材料，实际**从未作为文件存在过**（仓库 404、索引无此条）。其中的统计数（BS 26/31、PL 37、说明 15/8 条）经回核原件**全部准确** ⇒ 分析确实做过，只是从未落地。开发侧「材料我还没拉」不是懈怠，是**拉不到**。
   **与惯例 22 的分工**：22 管**待办**要写到可执行；本条管**材料**要写到可取用。两者都是「档里那句话，接手的人能不能照着动手」。
   **自查**：写下「已到位」三个字之前，把那个 raw 链接粘出来。粘不出来就改写措辞。
29. 🔴 **告警 / 提示 / 披露类交付，动手前必须确认「载体的可见人群」与「问题的相关人群」相交。**
   这类交付的价值**全部**在于送达。载体选错，代码写得再对也等于没做，而且**测试会全绿** —— 因为它确实按设计工作了，只是没人看得见。
   **实例（同期两次）**：
   - **① 人群互斥**：十三项取 0 提示原拟挂**发行回执**（照 `legacy_lianhao`/`cash_warn` 的成功先例类推）。但那两条挂在**小企业发行路径**上，而这 13 项在**大企业报表**上 —— `l10n_cn_asbe_bs` 的 `chart_template = cn_large_bis`，而发行 wizard 的 `_supported_companies` 只对 `chart_template='cn'` 跑、明确拒绝 `cn_large_bis`。**两拨公司互斥，提示结构上永远送不到看这张表的人手里。**
   - **② 载体不可见**：6 条地方税种以 `active=False` 发出，而归档科目界面默认不显示 ⇒ **发了等于没发**，客户照样自建。补救＝发行报告加 `archived` 清单 + 回执明写编码与取消归档路径。
   - **③ 载体只覆盖一条路径**（R44-T2 落地时抓到，`verified`）：同一张 ASBE 资产负债表有**两条渲染路径** —— 通用路径（屏幕 / 通用 XLSX / 通用 PDF）走 `_get_lines` → `account.report.line`；**中式版式 XLSX（法定主力导出件）走 form 行、不含 `account.report.line`**。披露若只加报表行，在**客户真正拿去用的那份文件上直接消失**，而屏幕上看着一切正常、**测试全绿**。补救＝双载体（报表行 + form 页脚），**两处文案一字一致**。
   - 🆕 **④ 载体覆盖过头**（R48-T3 撤回，`observed`：执业会计口径）：R44 为解决「③ 覆盖不足」，把口径披露补到**中式版式 XLSX 页脚**上 —— 而中式版式是**对外报送件**。二姐原话：**「对内审计没问题；对外报送不要放页脚，单独附说明文档。」**
     🔴 **病根与 ③ 完全相同**：R44 那轮的推理链是「客户拿去用的那份文件上会消失 ⇒ 补上去」，**把「客户拿去用」和「客户自己看」当成了一件事**。实际上**中式版式的受众是税局与审计，口径说明的受众是客户自己的会计 —— 两个受众从来不重合**。⇒ 撤下页脚渲染（字段保留）、通用路径披露行**保留不动**（对内那半判断是对的）、另出独立说明件（报表工具栏「取数口径说明」导出按钮）。
     ⚠️ **这不是缺陷，是受众判断修正** —— 不进 §6.7 作废清单，进沿革。
     🔴 **顺带查出**：R44 声称的「两载体文案一字一致」**在测试库里根本没有用例钉着**（构造性关闭）——**那是「验过但没钉住」**。⇒ 新载体上线时**同轮补一致性钉**（说明件文案 `==` 通用披露行 `name`），从源头堵漂移。
   🆕 🔴 **⑥ 载体差存在于「同一载体内的不同表之间」（R51 后续，2026-08-19；🟢 **v32 已闭**，`observed`，两账套 2/2）** —— ⑤ 管的是**同一张表的两个载体**（打印模板 vs 导出件）；本条管**同一个载体（都是导出件）里，甲表与乙表的同一要素落点不同**。
   **实例**：金蝶**导出件**上，**总账**把公司名放在**表头**（`万佳设计集团有限公司深圳分公司` 与期间并列），而**明细账**把公司名放在**页脚**（`公司名称: …`），表头只有 `科目: 1002-银行存款` + 期间范围。**三栏式（万佳）与数量金额式（佳兴加固）两个不同账套、两张明细账，2/2 都在页脚。**
   🟢 **v32 闭合（总账第 2 页到手）**：总账第 2 页表头**仍是**公司名 + 期间 ⇒ **总账公司名在表头且【每页重复】**；该页表末**未见页脚公司名**。落点关系至此完整：**总账 = 表头有 / 页脚无；明细账 = 表头无 / 页脚有。**
   ⚠️ 边界：总账第 2 页是**照片**、下缘可能被裁 ⇒「总账页脚无」落 `observed`、**不落 `verified`**；但**即便总账页脚也有，也不改变明细账表头该空着**（明细账那张是清晰导出件）。
   **失败形态**：从甲表的落点**类推**乙表（「三件同套，都跟总账走」），而乙表恰好有原件可查、且答案相反。⇒ note 侧据此把一条**原件支持的正确工单要求**改成了错的（详见惯例 33 第二例）。
   **落法**：**新增一张表时，该表的原件要单独看一眼**；「与已交付的甲表同套」是**推断**，不是观测，**有原件就不许用推断代替**。
   **自查五问**：这条提示**给谁看**？他**从哪个界面**会看到？那个界面**他这类公司打得开吗**？那个界面**只有一条渲染 / 导出路径吗**？🆕 **这个载体还会被谁看到** —— 有没有一拨人会看到它、而这句话根本不是说给他们听的？
   🔴 **③ 与 ④ 是同一句话的两个方向**：**先定受众，再选载体。** 从「客户会打开哪个文件」出发去选载体，两个方向都会踩。
   🆕 🔴 **⑤ 载体差存在于「他方原件」这一侧（R49 证伪轮，`verified(artifact)`）** —— 前四条管的都是**我方输出**挂在哪个载体上；本条管**我方读入**的那份原件说的是哪个载体。
   **失败形态**：把一份原件的列集当成「这张表就长这样」，而同一张表在**另一个载体**上列集不同。两边都是真的，引用时不写载体就会**拿甲的列集去验乙的实现**。
   **实例（一轮里三个）**：金蝶同一套报表，**打印模板与导出件列集不同** —— 总账（打印模板科目在表头、`month`+`day` 两列；导出件科目占表内两列、期间合成一列 `202607`）、数量金额明细账（打印模板余额组无方向列、导出件有）、科目余额表（打印模板六栏、导出件八栏）。
   **落法**：**引用任何一手原件的列集 / 行集，必须在同一句话里写明是哪个载体**（打印模板 / 导出件 / 界面截图）；**我方选哪个当锚也要写明**，并说明理由。
30. 🔴 **测试通过 ≠ 被测路径执行过。断言类测试必须先断言「它确实跑到了」。**
   **失败形态**：用例的前置条件悄悄不成立 —— 被测方法在入口处就整批拒绝 / 早退 / 返回空集 —— 于是后续断言**在空数据上全部成立**，测试显示通过，而**被测逻辑一行都没执行**。这比测试失败坏得多：失败会被修，空绿会被当作证据往上堆。
   **实例（`verified`，R45-T1 顺带发现）**：`TestCoaPublish` **8 条**用例长期全绿。真因是 `develop-6` 的 `zh_CN` **从未激活**，R38-T3 语言门在 `_publish` 入口把整批发行拒掉 ⇒ **一条科目都没发过**，8 条断言全部落在空结果上。补法＝`setUpClass` 自备 `_activate_lang('zh_CN')`、`tearDownClass` 回滚。
   **落法**：每个断言块前加一条**正向哨兵** —— 产出条数 > 0 / 被测方法被调用过 / 返回值非空。哨兵失败即前置条件失效，**不允许用"结果符合预期"掩盖"根本没发生"**。
   **与惯例 14 的分工**：**14 管结果弱**（预期结果不构成证据），**本条管事件根本没发生**（连弱结果都不是）。14 之下至少跑过，本条之下什么都没跑。
   **自查**：这条用例如果把被测方法整个删掉，它会不会**照样绿**？会，就是空绿。
   🆕 **子形态 (a)：断言「不存在 / 为 0 / 无残留」的用例是重灾区。** R46 全量打桩排查 77 条用例、查出 **4 条空绿**（`confirmed 4`，非「没查到」），**全部落在这一类**——因为「什么都没发生」时这类断言天然成立。⇒ 写这类断言时，**必须先让它有东西可查**。
   🆕 🔴 **子形态 (b)：检测器 / 哨兵类测试必须自带「注入 → 检出」那半。**
   只跑「正常数据下它不报警」，验的是**不误报**；而**「构造一个真问题、它确实抓到」才是检测器存在的理由**。缺后半的哨兵测试与一句 `pass` 无异——它在检测器被删空后**照样绿**。
   **实例（三次撞同一堵墙）**：① R43 撞号哨兵**两半都跑**（合成撞号能触发）✅；② R44 `test_no_dangling_expressions` **只跑了不误报那半**，检测器正确性从未正向验证，R46 打桩即证空绿 ❌ → 改为注入 `ZZ_NO_SUCH_CODE.balance` 悬空表达式、断言检测器抓到（证有牙）+ 真数据无悬空（证无害）；③ R44-T1 存量告警亦是只验「不误报」，R45 才补上「能响」那半。
   ⇒ **凡交付一个「会报警的东西」，验收判据恒为两条：该静时静、该响时响。** 少任何一条都不算交付。
   🆕 🔴 **子形态 (c)：跨源 / 跨路径核对的注入，必须注在【真实模型侧】，并各自重算两源。**（R53，`verified`）
   **失败形态**：注入造在**我方读出来之后的中间变量**上（拷贝一份结果字典、改里面的数）。断言确实会响 ⇒ **绿灯是真绿的，只是绿错了地方** —— 它证明的是「断言可用」，**不是「那条跨源链是通的」**。检出的是自己刚改的那个数，两个数据源一次都没被牵动。
   **实例（R53 判据 11，`stock.move.value` ↔ 总账 `aml.balance`）**：原注入 = `copy.deepcopy(self.data)` 后改 `[...]['current']['d_amt'] += 123` ⇒ 属本形态，**已订正**为两条真实模型侧注入：

   | 注入点（模型.字段） | 重算范围 | 验的链 |
   |---|---|---|
   | `account.move.line.balance`（补一笔非 stock 手工分录） | **重算总账（含它）+ 重算报表（读 `stock.move`、不含它）** | account 变 → 报表不跟 → 拉开差 |
   | `stock.move.value`（改入库计价） | **重算报表（读改后 value）+ 总账（`aml` 已按旧值入账、不变）** | stock 变 → 报表跟着变 → 与总账拉开差 |

   🔴 **判别式**：**一侧动、另一侧按各自的源重算后【不动】** —— 这才叫两源独立。若两侧重算后都跟着变，说明仍是共模，注入没验到独立性。
   ⚠️ **共用上游时本条弱化**：R51 判据 6 两条路径共用上游取数，注哪侧差别不大；**两侧是真正独立的两个模型时，注错地方就等于没验。** ⇒ **换源轮尤其要查这一条。**
   **副产物（净增事实，非本条主旨）**：订正过程中掉出来一条 —— **改 `stock.move.value` 不回溯已过账 `aml`**（见 §7 B-80）。
31. 🔴 **禁令要写清对象，不要写成禁手段。**
   **失败形态**：一条针对**对象**的禁令（「不覆盖**官方的**报表 / 不改写**官方的**引擎」），在转述、压缩、写进下游工单时丢掉限定词，变成针对**手段**的禁令（「不加 `custom_handler`」）。下游据此把一条本来完全可走的路判死，**并且判得有理有据** —— 因为工单上白纸黑字就是这么写的。
   **实例（`verified`，R47-T1）**：R44 否掉的备选原文是「为一句恒真的口径声明去**覆盖官方 generic 引擎报表**」，禁的是**官方报表**；R47 工单压缩成「不加 custom handler」，禁成了**手段**。而中式六 / 八栏余额表的「本期发生额·借 / 贷」是**毛额**，`account_codes` 与 `domain` 两个引擎都只出 `SUM(balance)` 净额，**数学上从余额推不出借贷两个毛额**（一个方程两个未知数）⇒ 全 Odoo 里唯一能分借贷毛额的就是 `custom_handler`，而官方自己的试算平衡表正是这么实现的。**禁令若成立，这张表根本做不出来。** 开发侧照门槛条款停下回报，未擅自绕行 —— 裁决＝**在我方新建报表上自带 handler 允许，碰官方机件禁止**。
   🔴 **自查**：**这条禁令如果官方自己也在做同样的事，那禁的多半不是这件事本身，而是它的作用对象。**
   **落法**：写禁令时把对象写进句子 —— 「不给**官方报表**挂 handler」而不是「不加 handler」；「不改写**官方** `account_report.py`」而不是「不碰引擎」。**验收时要求正面陈述**：让下游明说「官方的 X / Y / Z 三个都没碰」，而不是只说「我加了自己的 handler」。
   **与惯例 29 的分工**：**29 管「先例可复用的是规范，不是那段代码所在的位置」；本条管「不是那段代码用的手段」。** 同一堵墙的两个面 —— 都是把「为什么」丢了、只留下「怎么做的」。
   **与惯例 1 的分工**：**1 管用户找不找得到入口，本条管这个入口下有没有他要的人。** 先例可复用的是**规范**（非拦截、只述事实、不自证），**不是那段代码所在的位置**。
32. 🔴 **「我方没有 X」与「我方有 X」同为断言，同样要举证。**
   「诚实边界」「材料缺口」「无原件对位」这类**否定式声明**读起来像谦虚，实际上是**一个未经检索就下的全称否定**。它比乐观声明更难被发现是错的 —— 没有人会去查证一句「我们没有」，而它会**直接改变下游动作**：据它向外部索要已经在手的东西、据它把已有原件级证据的结论降级成「按惯例推演」。
   **判据**：写下「我方没有 / 尚无 / 无原件对位 / 是缺口」之前，**先在 `index.md` 列出的材料里检索一遍，并把检索的落点写进句子**（「已查 `X.md` §Y，无此项」），检索不了就写「**未检索**」，不写「没有」。
   **实例（R49，一轮里两份档同时写错）**：施工单与 design draft-48 都写「**总分类账无实务版式锚**」，并据此把 Q1 方向栏的裁决降级为「按中式惯例、非对原件」、还挂了一条「下次向二姐要一份总分类账样本」的待办。而 `l10n_cn_kingdee_material.md` **§3.6 早已记着金蝶总分类账打印模板 `KZ-J101` 的逐字段绑定**（`month`/`day`/`acctname`/`explanation`/`debitamount`/`creditamount`/`balancedc`/`balanceamount`），**§7.1 还专门写了「方向栏是计算列、中式账簿余额侧恒有借/贷/平」** —— 那正是该轮争议最大那条裁决的原件级支撑。**材料在库里躺了十天，两侧都没查。**
   **归族**：与**惯例 28** 互为镜像（28 管「档里写『材料已到位』其实没有」，本条管「档里写『没有材料』其实有」）；与**惯例 12**「查到 0 ≠ 真为 0」同族，但更前一层 —— **惯例 12 管查了但查错了载体，本条管根本没查。**
   **对下单方的额外要求**：施工单里的「诚实边界」段**是下单方的断言，不是执行方的**。执行方通常没有独立渠道去证伪它，会原样抄进 design ⇒ **写错一次会被复制到两份档。**
33. 🔴 **从法源 / 原文推出的那句「因此……」是我方的推断，不是原文本身 —— 不得用它压过原件观测。**
   引用原文时，句子里往往同时装着两样东西：**原文说了什么**（权威）与**我方由此推出了什么**（推断）。写下来之后两者长得一样，读者（包括下一个窗口的自己）会把整句都当成原文的权威。而**当推断与一手原件观测冲突时，正确的默认是「推断错了」，不是「原件是厂商的做法、不算数」。**
   **判据**：任何「原文说 X ⇒ 因此 Y」的句子，把 Y 单独拎出来问一句「**原文有没有排除掉 not-Y**」。没排除，Y 就只是**一个与原文相容的解**，不是唯一解，**不得用来否掉另一个同样相容、且有原件支持的解**。
   **实例（R49，`verified` 由次日原件证伪）**：《会计基础工作规范》§60(七)「结出余额后须在『借或贷』栏写明借或贷；**无余额的写『平』**」。note 侧推出「**因此**方向栏必然是余额的函数、不可能是科目固有属性」，据此否掉「方向 = 科目余额方向属性」这条**与金蝶实务一致**的方案，并写进 `项目档 v39 §4.5.22` 与 `design draft-48`，交付件按错规则实现。
   **错在哪**：「平」的存在只证明**零值要单独处理**，**并未排除**「非零时取属性」——真实规则正是这个二段式（`余额==0 → 平`；`≠0 → 取属性`）。**原文没错，推断错了，而错的那半被写得像原文在说话。**
   🆕 🔴 **第二例（2026-08-19，note 侧自犯，形态与首例完全相同）**：R51 工单 §八原写「**页脚：公司名称**」，依据是**明细账导出件**。回报阶段执行方提出金蝶 `getCompanyName` 是**表头**绑定，note 侧遂推「**三件同套**（余额表/总账/明细账都跟总账走）⇒ 公司名入表头、页脚只留页码」，并裁为「**改工单不改代码**」。
   **错在哪**：「三件同套」是**类推**，而**明细账导出件就在手边**（`kingdee_subledger_3col_export_wanjia_1002.png`），图上公司名清清楚楚在**页脚**。⇒ **推断压过了可直接观测的原件**，且这次被压掉的是**我方自己先前写对了的那一条**。
   🆕 🔴 **第三例（同日，note 侧）**：据「查询串已绕过缓存」「图片拉得到」两条**推断**断言 raw 拉到旧档「不是 CDN 的问题」，而 `x-cache` / `source-age` 响应头是**直接观测**、就在同一次请求里（详见惯例 27 (b)）。
   🆕 🔴 **第四例（R54，note 侧）：据【名字】推实现。**
   note 侧看见回落路径调用 `_cn_direction_by_code()`，据函数名判定它是「按编码推导方向」，并据此预言 `1602 累计折旧` 会被判成「借」、§4.5.22 那条「父行方向 = 父科目属性」的结论会在 v20 上**静默翻转**。
   **实际**：该函数**查的是我方发行件的方向表**（`ASSBE_DIRECTION_BY_CODE`，R48 裁决的唯一权威值），**不是推导**；真正会翻车的推导层是另一个函数 `_cn_derive_direction(account_type)`，而回落路径**不走它**。⇒ 预言的机制**不存在**，`1602` 在发行件里明确是 `credit`，7 个一级键 **7/7** 命中。
   🔴 **新的触发物**：前三例推的是「另一件事的规律」，本例推的是**一个名字**。
   **落法**：**函数名 / 字段名 / 变量名是【作者的意图表达】，不是实现。** 凡据名字判断行为，**打开看一眼** —— 名字与实现不一致时，名字往往是历史遗留，而**读名字的人不会知道自己读的是历史**。
   ⚠️ 🔴 **四例连起来看，共同形状不是「查得不够」，是【有直接观测在手却选了推理】。** 首例的观测是原件截图，第二例是同一张截图，第三例是响应头 —— **三次的观测成本都低于推理成本**。
   **落法**：写下「因此 / 所以 / 同套 / 必然」这类词时，问一句「**这件事有没有一个可以直接看的东西**」；有就去看，**看完再写**。
   **加重情节**：该推断是用来**推翻一条已有原件支持的结论**的。⇒ **推断的证据强度天然低于观测**；用低强度证据推翻高强度证据，须先解释「原件为什么会那样」，解释不了就是推断错。
   **归族**：与**惯例 23** 同源（事后推断的成因须标 `observed`）—— 23 管**因果推断**要挂级，本条管**从原文的推断**要挂级，且多一条：**它不得越级压过观测**。与**惯例 21**（`observed` 采纳门槛按方向不对称）互补：21 管采纳，本条管**推翻**。
34. 🔴 **向执行方提封闭选项题时，必须显式留「以上皆非，请说明」那一格 —— 选项集本身是下单方的一个推断。**
   问「是 A 还是 B」，表面在提问，实际在**断言「答案必属 A、B 之一」**。执行方处在「回答下单方的问题」这个框里，倾向于**在给定选项里挑一个最近的**，于是真实答案被挤进错误的格子，而**双方都不会察觉**——因为回答形式上是合规的。
   **实例（R50）**：note 侧问「这个缺陷是 **R49 就潜伏**，还是 **R50 新引入**？」并写明「这两种情况处理完全不同，别混过去」。真实答案是**第三类**：**代码缺陷 R49 就在**（`git show` 确认），但 **R49 的绿灯是真的**（当时夹具的末笔在 compute 前已可见，没触发这条路径），R50 夹具加了第二条同日 move 才撞上。
   ⇒ 我预设的二选一里，隐含了「代码有缺陷 ⇒ 当时的绿灯是假的」这个**并不成立**的蕴含。**执行方明确回答「落第三类，不是你给的两选一」，是对的做法。**
   **落法**：① 封闭选项题**末尾固定加一格**「以上皆非 —— 请说明实际形态」；② 在题面上写明「**选项集是我方推断，不是穷举**」；③ 若某条追问带着「这两种情况处理完全不同」这类**压力话术**，更要留那一格——压力越大，被挤进错格的概率越高。
   **归族**：与**惯例 33** 同族但作用点不同 —— **33 管从原文推出的「结论」要挂级，本条管提问时给出的「框架」要挂级。** 两条都是「我方的推断被当成了事实」，一条发生在答，一条发生在问。

---

## 9. 中国财务与税务市场事实（跨项目）
> 取材 2026-08-07：电子税务局界面一手截图 + 多年代账实操口述 + 金蝶星云/星辰导出件。任何面向中国客户的项目都用得上，不限于 l10n_cn 模块线。细节展开见 note 仓库 `l10n_cn_localization_project.md` §4.5。

### 财务报表报送的校验与差异（`observed`，2026-08-11 电子税务局实测 + 二姐实务）

1. **税局对财报做两类校验**：**跨期连续性**（`本年累计 = 本期 + 本年上期累计`，税局自带上期数据）与**跨表一致性**（利润表营业收入 ↔ 企业所得税预缴申报表 ↔ 增值税申报）。
2. **不一致是软提示、不阻拦提交**（有「继续申报」按钮），**但异常会进「我的提醒」，与信用失分同一个池**。⇒ 在真实公司账号上造数测试**不是零成本**。
3. 🔴 **跨表差异可以是准则性必然差异，账做对了也对不上。** 典型：固定资产处置——**增值税**按销售货物申报销售额，**会计**走固定资产清理、净额入营业外收入，**不进营业收入**。实务处置 = **上传情况说明**。同类：视同销售、包装物押金逾期、部分价外费用。
4. **小企业按季报**，属期 = **季初~季末**（如 `2026-04-01 ~ 2026-06-30`）；**一般纳税人才月报**。
5. **税局在线填报会自动算合计行** —— 收入、成本、费用一填，营业利润/利润总额/净利润自动出数。⇒ 想验证某条勾稽的方向（如「账面价值 = 原价 − 累计折旧」还是「+」），可直接在网页试算后点「重置」，不留报送数据。
6. **应报哪几张表由《财务会计制度及核算软件备案报告》带出**；改本属期备案报告须先联系主管税务机关**作废已填报的财报**。⇒ 测试一律走到数据落位为止，**不点「提交申报」**。
7. **纸质印刷账本的利润表列序 = `本年累计金额｜本月金额`**，与官方报送模板（`本期金额｜本年累计金额`）**相反**。中国会计的手感来自账本，review 报送件时会据此提「列序不对」——**那是惯例与官方模板的差异，不是错误**。
8. **科目表缺明细会造成填列缺陷**：某小规模客户未设「预付账款」明细，借方净额无处可去 → 以 **−37,948** 负数挂在资产负债表「应付账款」行并计入流动负债合计。实务共识：按方向分流填列**更专业**。⇒ 预置成对科目（应收/预收、预付/应付）+ 删除告警，是能让会计一眼看懂的产品价值点。

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

#### 备案是法定义务，但不是审批（`verified`，2026-08-08 新增）

- 《税收征管法》§20：从事生产、经营的纳税人的财务、会计制度或者财务、会计处理办法**和会计核算软件**，应当报送税务机关备案。
- 《税收征管法实施细则》§24：自领取税务登记证件之日起 15 日内报送财务、会计制度或处理办法；**纳税人使用计算机记账的，应当在使用前将会计电算化系统的会计核算软件、使用说明书及有关资料报送主管税务机关备案**；建立的会计电算化系统应当符合国家有关规定，**并能正确、完整核算其收入或者所得**。
- 浙江省税务局把它列为纳税人十项义务之一；有省份曾发文全面清理，对不按要求或虚假申报备案的批评教育限期改正，拒不改正按征管法 §60 处罚。

🔴 **但税务机关的审核是形式审核** —— 查资料是否齐全、是否符合法定形式、填写内容是否完整，不齐全的一次性告知补正。**没有任何环节审查软件的资质、国别或认证。**唯一的实体要求是「能正确、完整核算其收入或者所得」——**这是对核算结果的要求，不是对软件品牌的要求**。

→ **「Odoo 能不能通过备案」是个问错的问题**：备案是**报备不是审批**，不存在「通过」这回事。**备案不构成 Odoo 的准入门槛。**真问题只是「填了之后税局会不会来问、问什么」。

#### 🔴 产品结论：备案说明书是法条明文要求的报送材料

法条原文是「会计核算软件、**使用说明书**及有关资料」；北京、上海等地政务服务页均列明「使用计算机记账的，应提供财务会计核算软件、**使用说明书复印件**」。

→ **「Odoo 中式核算方法说明书（备案用）」不是猜的产品线索，是客户上 Odoo 就必须交的东西**，而中国没有任何一家 Odoo 实施商会写。从「产品线索」升为**实施服务的确定组成部分**。

**说明书素材已有**：会计档案保管期限（永久 / 10 年 / 30 年）、防篡改措施、审签程序、多种核算方法可选、科目分类编码、报表自定义 —— 见下节。

#### 实操侧的对照说法（`observed`，二姐，单点样本，2026-08-08）

- 备案里实际填的是**折旧摊销方法、申报期（月报/季报）**这类会计政策项。
- 问「备案是用小企业会计准则还是企业会计准则」→ 答**「没有特定」** → 备案**不锁定准则口径**。对报送表样设计是好消息：表样由报送小类决定，不由备案锁死。
- 问「软件备案是必填吗、是下拉还是手填」→ 答**「没有说要备案软件」**。

🔴 **与上文法条部分冲突，冲突本身要记，不要抹平。**两种可能：① 该栏因省份/电局界面版本而异；② 执行层面已弱化（新办套餐式服务）。**结论仍待和界鸿源（真实实体）登录电子税务局看备案报告界面确认。**二姐的话把风险**降级**了，没有**关闭**它。

**归纳**：法条层面要交，实务层面不难交、也不会被卡。

### 🔴 中国会计软件的法定功能规范（`verified`，2026-08-08 新增）
> 任何中国客户的 Odoo 实施都受它约束，不限于 l10n_cn 线。条款级清单与 Odoo 对照见 note 仓库 `l10n_cn_localization_project.md` **v12 §4.5.13**。

| 文件 | 管谁 | 施行 | 废止 |
|---|---|---|---|
| 财会〔2024〕**11号**《会计信息化工作规范》 | **用软件的单位** | 2025-01-01 | 财会字〔1996〕17号、财会〔2013〕20号 |
| 财会〔2024〕**12号**《会计软件基本功能和服务规范》 | **软件本身 + 服务商** | 2025-01-01 | 财会字〔1994〕27号 |
| 《会计档案管理办法》财政部·国家档案局令第79号 | 归档 | 2016-01-01 | — |
| 财会〔2025〕**9号**推广应用电子凭证会计数据标准 | 电子凭证全流程 | 2025-05 起全国 | — |

🔴 **12号 §2 把实施方框进来了**：适用对象含「会计软件服务商（**含相关咨询服务机构**）」。**做 Odoo 实施，法律上就是会计软件服务商。**

🔴 **三年过渡期**：施行前已投入使用但不符合的会计软件，自施行之日起 3 年内升级完善 → **2027-12-31**。

**服务商的持续义务（12号 §39）**：新制度/新数据标准施行时应及时评估升级并通知用户；已施行的若影响用户合规核算，**应当为用户免费提供更正程序**。→ **写进实施合同。**

**几条对 Odoo 直接有影响的**：
- 🔴 **§21(三) 不可逆记账**：不得删除/插入已记账凭证、不得修改其日期/币种/汇率/金额/科目/操作人、同类已记账凭证连续编号。Odoo 有安全锁/hash 机制但**默认关闭** → **实施必做项，非开发项**，且是备案说明书的核心章节。
- 🔴 **§36 / 11号 §42 跨境数据境内备份**：数据服务器在境外的，须在境内保存备份、**频率不得低于每月一次**，且境内备份须能在境外服务器不能正常工作时**独立**满足会计工作与财会监督需要。→ **对上 odoo.sh / Odoo Online 的中国客户是硬约束，同时是可卖的服务。**
- **§25 报表自定义**（格式/项目/数据来源/计算逻辑）：`account_reports` 引擎直接命中，**是 Odoo 的强项**。
- **§41 数据归用户所有、不得以任何理由拒绝导出**：这是 P-05 可移交性的外部依据。

🆕 **电子凭证会计数据标准适配 = 集成而非从零开发**：财政部提供**免费基础工具包**，可直接集成至现有信息系统，提供解析与入账信息结构化数据文件生成功能。发布于财政部会计司门户网站 > 会计信息化建设专栏。详见项目档 §4.5.14。

🔴 **别激活 GB/T 24589**：12号 §29/§41 的「国家统一标准的数据接口」，锚点是**电子凭证会计数据标准 + 电子档案格式**（GB/T 44554.1、GB/T 42965.1/.2、DA/T 94），不是 GB/T 24589 —— 后者消费方是审计/检查，而一般企业不强制审计。
### 法定报表的权威源分层（`verified`）
做任何国家的法定报表本地化，取材权威等级要分层，混用会出错：

| 要什么 | 权威源 |
|---|---|
| **行集合与顺序** | 会计准则制定机构的报表格式原文（中国=财政部《一般企业财务报表格式》附件） |
| **行名字面**（全半角、标点、括号） | **税务机关的报送表样** —— 因为报送匹配是税局导入器在做，不是准则在做 |
| **行次号** | 税务机关表样 —— 准则原文通常**不编行次**，行次是税局加的 |
| 取数表达式 | 准则原文的「有关项目说明」；商业财务软件的配置只能作交叉参照 |
| **列口径与列名**（本期/本年累计/上年…） | **税务机关的标准模板** —— 列是税局的采集设计，准则原文只给「本期/上期」的抽象口径 |

🔴 **行验对了不等于列验对了。**逆推表样时，「行集合」这一维靠准则原文可以推得很准，「列口径」这一维**推不得** —— 两者权威源不同。实例：某套报表的行集合逐张验证通过、被当作「逆推方法可靠」的证据，但同一批表的月季报列序是反的（把「本年累计」放在了「本期」前面），且列名标成「本月金额」而取数实际是整个季度 —— **名字错到会让使用者按字面误读数字**，属 bug 不属措辞。根因是当初照一份非官方样表定的列序，官方采集模板到手后才推翻。

实例：中国财政部原文用全角「1．」，税局表样用半角「1.」；准则原文在小节末留「……」占位符，商业软件实现成「其他」可取数行，税局表样直接删掉——**同一个位置三方三种处理**。

⚠️ **准则原文的「项目说明」里藏着引擎能力边界**。例如中国「应付账款」项目要求取「应付账款」和**「预付账款」科目所属明细的期末<u>贷方</u>余额合计**——按科目取净余额的取数引擎（如 Odoo 的 `account_codes`）**表达不了按借贷方向拆**。又如要求「分析填列」的项目（下钻到明细科目 + 人工判断），任何自动取数引擎都做不到，**留空是准则约束的结果，不是软件缺陷**。做本地化时先把这两类行挑出来，别当成待补的缺口。
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

### 申报侧不存在企业软件↔政府系统的直连（`verified`，2026-08-08 升级）
税局、社保的申报接口不对一般 ERP 开放。**任何 ERP 在中国都只能做到「出数据 + 人工/半自动上传」**，用友金蝶的客户同样如此。分界线是数据在谁手里：

| 层 | 在哪 | ERP 能否包 |
|---|---|---|
| 账 + 凭证 + 账簿 + 报表 | ERP | ✅ |
| 薪酬计算 | ERP（需本地化） | ✅ |
| 发票开具与进项认证 | 税局平台 | ❌ 只能对接 |
| 报税上传 | 电子税务局 | ❌ 只能导出 |
| 社保申报 | 社保网厅 | ❌ 只能导出 |

🔴 **本土软件的「一键报税」是 RPA，不是接口**（`verified`，厂商官方产品手册）：金蝶云星空「报税机器人-广东」自动填报增值税申报表、附加税报表及财务报表，**只支持广东（不含深圳）地区的一般纳税人、通过网页端**；同系列「网银机器人-建设银行」自动登录网银下载明细，**不同银行是不同的机器人方案**。
→ **有接口就不会去写网页机器人，更不会一省一个、一家银行一个。**这是判断「某条通道是不是真直连」的硬指标。

**销售话术**：客户问「金蝶能一键报税，Odoo 行吗」，正确答案不是"我们做不到"，而是「那不是接口是网页机器人、只覆盖部分省份；申报这一段所有软件都只能导出，包括金蝶用友」。

#### 🔴 三条通道的性质必须分开，不能打包成「外部接口层」（`verified`）

| 通道 | 对方是谁 | 真直连？ | 谁用得上 | 与合规的关系 |
|---|---|---|---|---|
| **银企直联** | **银行**，不是政府 | ✅ 最成熟的一条 | 企业与银行签约 | **无关**，纯效率 |
| **数电票开具（乐企直连）** | 税务总局电子发票服务平台 | ✅ 税务侧**唯一**官方接口 | 有准入门槛：纳税信用等级、营业收入规模、发票吞吐量、无税收违法记录、系统能力 | 有关，中小企业够不着 |
| **进项取票 / 勾选认证** | 增值税发票综合服务平台 | ❌ 服务商通道或 RPA | 普遍 | 无关，是**录入工作量**门槛 |
| **纳税申报** | 电子税务局 | ❌ RPA / 模板导入 | 分省、分场景 | 有关 |
| **社保 / 公积金** | 社保网厅 | ❌ 不存在 | — | 无关 |

🔴 **乐企的申报能力至今未上线**（`verified`）：乐企规划三种能力 —— 开票、用票、**申报**；开票用票已有大量企业上线，**申报能力仍在规划中**。
→ **申报侧的官方直连今天不存在**，「财报导入 xlsx」不是低配替代方案，它就是今天所有人在走的那条路，而且是软件中立的那条。

**对产品的含义**：本土软件的真实优势**不在申报，在发票**（销项开具 + 进项取票勾选）以及银企直联。这三项**都不是合规门槛** —— 客户不会因为缺它们而报不了税，只会多花录入工时。**排优先级按「工时」排，不要按「合规」排。**

#### 实务侧的对照（`observed`，二姐，单点样本，2026-08-08）

- 社保网站增减人员约半小时后同步至税务系统 —— 这是**政府内部**同步，企业软件不参与。
- 社保跟企业软件没有直连。
- **税务系统自己生成税费数据**：一般纳税人进销项多少、要交多少税，是税务网站生成的。因为增值税的数据源是发票，而发票本来就在税务系统里 → **企业软件在这条链上没有位置**。
- 「申报的数据跟做账的数据要相对应」= **对账义务**，不是集成关系。方向是税务系统生成数字 → 账要跟它对得上。
  🆕 **产品线索**（`unknown`，仅记录）：增值税台账 vs 申报表的比对现在是人工做的，与 `suite_data_guard` 思路同构。

### 记账凭证字实务（`verified` 法条 + `observed` 实务，2026-08-08 升级）
**法条**（《会计基础工作规范》财政部令第98号 §50）：记帐凭证可以分为收款凭证、付款凭证和转帐凭证，**也可以使用通用记帐凭证**。→ **单一「记」字有明确法律依据**，不是将就。

**实务**（`observed`）：中国企业现在**绝大多数只用「记」一种**；「收 / 付 / 转」是手工账时代分开装订的老做法，电算化后基本不用。
→ 做凭证字功能时，「按单据类型自动推导凭证字」多半是过度设计；更贴实际的是**给一个可配字段、默认全填「记」**，客户要分才分。

⚠️ **但「记」不是唯一形态**：电子凭证会计数据标准的官方示例里，「记账凭证编号」填的是 **`付款凭证868`**（凭证字+号）。→ **凭证字段本身必须存在且可配**，不能硬编码成「记」。

**记账凭证的法定要素**（§51(一)）：填制凭证的日期；凭证编号；经济业务摘要；会计科目；金额；**所附原始凭证张数**；填制凭证人员、稽核人员、记帐人员、会计机构负责人、会计主管人员签名或盖章；收付款凭证还须出纳签章。

**电算化的签章方式**（§53）：机制记帐凭证**打印出来后**加盖印章或签字 → **系统不需要电子签名工作流，只需在打印件上印出签章位。**

🔴 **边界，别用错法条**：§97 规定「填制会计凭证、登记会计账簿」两节**一般适用于手工记帐**，电算化按财政部会计电算化规定（即财会〔2024〕12号）。具体地：**§52（阿拉伯数字逐个写、大写金额壹贰叁、角分位补零）不能拿来要求 Odoo。**

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

