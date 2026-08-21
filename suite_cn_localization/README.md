# Odoo 19 中国本地化（内账地基层）— `suite_cn_localization`

SuiteState 的 Odoo 19 Enterprise 中国本地化模块包。**做「账」不做「证」**：承担企业内部经营账
（科目分级 / 科目余额表 / 三栏式明细账 / 三张报表 / 现金流量表），法定账在外部持有（代账或双轨，
DATEV 模式）。定位、决策与验证记录见配套设计文档 **`l10n_cn_design.md`**。

> 本目录是**容器**（其子目录才是模块），R20 自 `l10n_cn` 改名为 `suite_cn_localization`，
> 避免与官方模块技术名同名。目录本身无 `__manifest__.py`，不是模块。

## 模块（R20 结构，5 个）

| 模块 | 内容 | depends | 许可 |
|---|---|---|---|
| `suite_cn` | **聚合伞**：一键装齐（纯 `depends`，永不放代码） | 下列子模块 | OPL-1 |
| `suite_cn_coa` | 科目分级树（`account.group`）→ 让原生 科目余额表 / 三栏式明细账 中式折叠 | `account`, `account_reports` | OPL-1 |
| `suite_cn_statement` | 官方 BS/PL 年初/累计列（R21 起：行次映射 / 中式表头表尾 / BS 两栏对开 / XLSX·PDF） | `account`, `account_reports`, `l10n_cn_reports` | OPL-1 |
| `suite_cn_cashflow` | 现金流量表（小企业会计准则，直接法 22 行）+ 现金流量项目维度 | `account`, `account_reports` | OPL-1 |
| `suite_cn_cashflow_statement` | 桥：现金流量 × 版式行次映射（`auto_install`，R21 起有内容） | 上二者 | OPL-1 |

**依赖方向**：除桥外，任何子模块不依赖兄弟、全部直挂官方；伞只做 `depends` 聚合。
每个叶子模块可独立安装。桥 `auto_install`：两侧皆装时自动装上、任一卸载即随之卸载。

## 安装

```bash
# 装齐全部（推荐）
odoo -d <dev_db> -i suite_cn --stop-after-init
# 或按需单装，例如只要科目分级：
odoo -d <dev_db> -i suite_cn_coa --stop-after-init
```

中文报表渲染需安装 **zh_CN 语言包**（任何中国部署的常规步骤；译文由 Odoo 提供，非本包）。

## 验收不变量（P-01）

卸载全部自有模块后，`account.move.line` 的 `debit` / `credit` / `account_id` 无变化、
试算平衡表与安装前逐账户一致。全部模块均为呈现层（只读既有会计数据），天然满足
（R16 起历轮实测，R20 再验：卸载全部后 251 行 / 借贷各 540347.09 / 46 账户逐账户 identical）。

> 已知：`suite_cn_cashflow` 卸载时，若有分录带 `cn_cash_flow_item_id`，删除现金流量项目会撞
> 外键（非洁净卸载；核心 debit/credit/account_id 不受影响）。见设计 §11.7，待后续修缮。

## 文档

- `l10n_cn_design.md` — 设计意图、否决方案、验证记录、变更历史（权威）。
- `l10n_cn_gb24589_data_matrix.md` — 国标 GB/T 24589 导出探查矩阵（**已归档**，待客群信号解冻）。
