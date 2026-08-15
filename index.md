# SuiteState 记忆仓库索引

> 读此文件即知本仓库有哪些资料、各自 covers 什么、raw 链接在哪。
> **新增任何文件时**（不限 md），在下方加一块：文件名 + 一句摘要 + raw 链接 + 可读性标记。

## 🔴 取用规矩（先读这三条）

1. **目录浏览页不可 `curl`** —— `https://github.com/.../tree/...` 返回的是 HTML 外壳，不是文件。**只有 `raw.githubusercontent.com/.../<单个文件名>` 才拿得到内容。**
2. **`raw` 按字节返回，不挑类型 —— PDF / xlsx 同样有 raw 链接。** 区别不在"有没有链接"，在**能不能直接读**：
   - 🟢 **TXT / MD / CSV** = 拉下来就是文字，直接可用
   - 🟡 **PDF** = 二进制，需 PDF 取文本工具
   - 🟡 **XLSX** = 二进制，需表格库
   ⇒ **凡 PDF 若已有转录 `.txt`，一律优先用 `.txt`**；本索引逐条标注。
3. **文件名含空格须编码为 `%20`**（`legal documents/` 目录必然涉及）。中文文件名亦须 URL 编码。

---

## 一、l10n_cn 项目主档（新窗口按此顺序读）

| 序 | 文件 | 讲什么 | raw |
|---|---|---|---|
| 1 | **`l10n_cn_status.md`** | 🔴 **现在在哪** —— 已交付 / 冻结 / 开工候选 / 收尾未清 / 材料缺口 / 开放项 / v20 迁移面。**只有这份讲当前状态** | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/l10n_cn_status.md |
| 2 | **`l10n_cn_localization_project.md`** | **设计权威** —— 模块结构、设计原则、口径与材料、版本沿革、作废清单 | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/l10n_cn_localization_project.md |
| 3 | **`background.md`** | **跨项目约束 + 惯例 1–27** —— 商业与品牌架构、基础设施与工作流、SuiteState 定位、模块清单、Apps Store 规则、Odoo 19 技术约束踩坑合集 | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/background.md |
| 4 | **`l10n_cn_kingdee_material.md`** | 金蝶材料档 —— 中式账簿/凭证/科目/报表的一手规格来源：两条产品线对照、科目主数据模型、版式解析、凭证规则引擎、报表取数公式、与 Odoo 的差集总表、已作废条目 | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/l10n_cn_kingdee_material.md |

🔴 **`l10n_cn_design.md` 不在本仓库** —— 它在**开发分支** `suite_cn_localization/l10n_cn_design.md`，由开发侧同轮回写。note 侧不写、也拉不到（本仓库该路径返回 404）。

---

## 二、其他主题档

### `odoo19_accounting_mechanics.md`
Odoo 19 实测笔记：估值架构基线、总账与库存分裂、成本法与按 Lot 估值、Landed Cost、绕开采购—销售链的估值事件、报表与毛利、期末关账等。
https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/odoo19_accounting_mechanics.md

### `vps_odoo_ops.md`
VPS 配置信息。
https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/vps_odoo_ops.md

---

## 三、数据件

| 文件 | 是什么 | 类型 | raw |
|---|---|---|---|
| `l10n_cn_assbe_chart_R33A.csv` | **我方 ASSBE 科目表发行件**（R33-A 基线） | 🟢 CSV | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/l10n_cn_assbe_chart_R33A.csv |
| `l10n_cn_asbe_chart_reference.csv` | ASBE 企业准则科目表（参考） | 🟢 CSV | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/l10n_cn_asbe_chart_reference.csv |
| `l10n_cn_assbe_chart_R33A旧版.csv` | R33-A 之前的旧版，**仅供追溯，勿作依据** | 🟢 CSV | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/l10n_cn_assbe_chart_R33A%E6%97%A7%E7%89%88.csv |
| `odoo+suite小企业科目 (account.account).xlsx` | **小企业库全量科目导出 181 条**（R43 证据件，含二姐归档的 49 条） | 🟡 XLSX | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/odoo%2Bsuite%E5%B0%8F%E4%BC%81%E4%B8%9A%E7%A7%91%E7%9B%AE%20%28account.account%29.xlsx |
| `odoo+suite大企业科目 (account.account).xlsx` | **大企业库全量科目导出 333 条**（R43 证据件）。🔴 该库当时**推了代码但未 upgrade**，跑的是旧代码 —— 属历史件，见 `background §7 B-76` | 🟡 XLSX | https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/odoo%2Bsuite%E5%A4%A7%E4%BC%81%E4%B8%9A%E7%A7%91%E7%9B%AE%20%28account.account%29.xlsx |

---

## 四、法规原文（`legal documents/`，**20 个**，截至 2026-08-14 收录）

🔴 **目录页不可 `curl`。逐个文件用下方 raw 链接。**

### 小企业会计准则（ASSBE）—— 财会〔2011〕17号
ASSBE 本体。正文 + 会计科目主要账务处理与财务报表格式。**我方 ASSBE 科目表与报表的准则依据**。
- 🟡 PDF，需取文本 — `小企业会计准则_财会2011_17号_正文.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E5%B0%8F%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99_%E8%B4%A2%E4%BC%9A2011_17%E5%8F%B7_%E6%AD%A3%E6%96%87.pdf
- 🟡 PDF，需取文本 — `小企业会计准则_财会2011_17号_会计科目主要账务处理和财务报表.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E5%B0%8F%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99_%E8%B4%A2%E4%BC%9A2011_17%E5%8F%B7_%E4%BC%9A%E8%AE%A1%E7%A7%91%E7%9B%AE%E4%B8%BB%E8%A6%81%E8%B4%A6%E5%8A%A1%E5%A4%84%E7%90%86%E5%92%8C%E8%B4%A2%E5%8A%A1%E6%8A%A5%E8%A1%A8.pdf

### 一般企业财务报表格式 —— 财会〔2019〕6号
ASBE 报表格式。**附件1 = 未执行新准则版、附件2 = 已执行新准则版**，两版分别对应我方 `standard_version` 维度。正文有转录。
- 🟢 **TXT，直接可读** — `财会[2019]6号.txt`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%5B2019%5D6%E5%8F%B7.txt
- 🟡 PDF，需取文本 — `财会2019-6号_附件1_一般企业财务报表格式_未执行新准则.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A2019-6%E5%8F%B7_%E9%99%84%E4%BB%B61_%E4%B8%80%E8%88%AC%E4%BC%81%E4%B8%9A%E8%B4%A2%E5%8A%A1%E6%8A%A5%E8%A1%A8%E6%A0%BC%E5%BC%8F_%E6%9C%AA%E6%89%A7%E8%A1%8C%E6%96%B0%E5%87%86%E5%88%99.pdf
- 🟡 PDF，需取文本 — `财会2019-6号_附件2_一般企业财务报表格式_已执行新准则.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A2019-6%E5%8F%B7_%E9%99%84%E4%BB%B62_%E4%B8%80%E8%88%AC%E4%BC%81%E4%B8%9A%E8%B4%A2%E5%8A%A1%E6%8A%A5%E8%A1%A8%E6%A0%BC%E5%BC%8F_%E5%B7%B2%E6%89%A7%E8%A1%8C%E6%96%B0%E5%87%86%E5%88%99.pdf

### 企业会计准则第30号 财务报表列报 —— 财会〔2026〕11号
报表列报总则（现行版）。
- 🟢 **TXT，直接可读** — `企业会计准则第30号_财务报表列报_财会2026_11号.txt`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99%E7%AC%AC30%E5%8F%B7_%E8%B4%A2%E5%8A%A1%E6%8A%A5%E8%A1%A8%E5%88%97%E6%8A%A5_%E8%B4%A2%E4%BC%9A2026_11%E5%8F%B7.txt

### 企业会计准则第31号 现金流量表 应用指南
现金流量表编制指南。**间接法附注的依据**；「现金」定义（库存现金 + 可随时支付的存款）出处。
- 🟡 PDF，需取文本 — `《企业会计准则第31号－现金流量表》应用指南.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E3%80%8A%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99%E7%AC%AC31%E5%8F%B7%EF%BC%8D%E7%8E%B0%E9%87%91%E6%B5%81%E9%87%8F%E8%A1%A8%E3%80%8B%E5%BA%94%E7%94%A8%E6%8C%87%E5%8D%97.pdf

### 财会〔2006〕18号
应用指南（含间接法现金流量）。
- 🟢 **TXT，直接可读** — `财会[2006]18号.txt`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%5B2006%5D18%E5%8F%B7.txt

### 会计基础工作规范 —— 财政部令98号
**记账凭证、账簿、装订的法定要求出处**。凭证字号、附件张数、金额大写等均源出此处。
- 🟢 **TXT，直接可读** — `财政部令98号_会计基础工作规范.txt`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E6%94%BF%E9%83%A8%E4%BB%A498%E5%8F%B7_%E4%BC%9A%E8%AE%A1%E5%9F%BA%E7%A1%80%E5%B7%A5%E4%BD%9C%E8%A7%84%E8%8C%83.txt
- 🟡 PDF，需取文本 — `财政部令98号_会计基础工作规范_2019修订.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E6%94%BF%E9%83%A8%E4%BB%A498%E5%8F%B7_%E4%BC%9A%E8%AE%A1%E5%9F%BA%E7%A1%80%E5%B7%A5%E4%BD%9C%E8%A7%84%E8%8C%83_2019%E4%BF%AE%E8%AE%A2.pdf

### 会计信息化工作规范 —— 财会〔2024〕11号
**电子凭证会计数据标准、国家统一标准数据接口的锚点**（§29/§41）。有转录。
- 🟢 **TXT，直接可读** — `财会[2024]11号_会计信息化工作规范(转录).txt`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%5B2024%5D11%E5%8F%B7_%E4%BC%9A%E8%AE%A1%E4%BF%A1%E6%81%AF%E5%8C%96%E5%B7%A5%E4%BD%9C%E8%A7%84%E8%8C%83%28%E8%BD%AC%E5%BD%95%29.txt
- 🟡 PDF，需取文本 — `财会[2024]11号_会计信息化工作规范.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%5B2024%5D11%E5%8F%B7_%E4%BC%9A%E8%AE%A1%E4%BF%A1%E6%81%AF%E5%8C%96%E5%B7%A5%E4%BD%9C%E8%A7%84%E8%8C%83.pdf

### 会计软件基本功能和服务规范 —— 财会〔2024〕12号
**会计软件的功能底线清单**，我方交付面对照用。有转录。
- 🟢 **TXT，直接可读** — `财会[2024]12号 会计软件基本功能和服务规范(转录).txt`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%5B2024%5D12%E5%8F%B7%20%E4%BC%9A%E8%AE%A1%E8%BD%AF%E4%BB%B6%E5%9F%BA%E6%9C%AC%E5%8A%9F%E8%83%BD%E5%92%8C%E6%9C%8D%E5%8A%A1%E8%A7%84%E8%8C%83%28%E8%BD%AC%E5%BD%95%29.txt
- 🟡 PDF，需取文本 — `财会[2024]12号 会计软件基本功能和服务规范.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%5B2024%5D12%E5%8F%B7%20%E4%BC%9A%E8%AE%A1%E8%BD%AF%E4%BB%B6%E5%9F%BA%E6%9C%AC%E5%8A%9F%E8%83%BD%E5%92%8C%E6%9C%8D%E5%8A%A1%E8%A7%84%E8%8C%83.pdf


### 三项新准则修订通知 —— 财会〔2017〕7号 / 22号 / 财会〔2018〕35号
🔴 **判断「某准则适用面」时取这三份，不是取附件** —— **施行日只在通知里**。三份均写明：**执行企业会计准则的非上市企业自 2021-01-01 起施行**。
🔴 财会〔2017〕22号 另明文废止《企业会计准则第15号——**建造合同**》⇒ `5401 工程施工`/`5402 工程结算` 是废止准则下的科目。
🟢 同时仅废止财会〔2006〕18号 中《〈第14号——收入〉应用指南》**一篇**，间接法现金流量部分完好。
- 🟢 **TXT，直接可读** — `财会〔2017〕7号修订通知.txt`（新金融准则 CAS 22）  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%E3%80%942017%E3%80%957%E5%8F%B7%E4%BF%AE%E8%AE%A2%E9%80%9A%E7%9F%A5.txt
- 🟢 **TXT，直接可读** — `财会〔2017〕22号修订通知.txt`（新收入准则 CAS 14）  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%E3%80%942017%E3%80%9522%E5%8F%B7%E4%BF%AE%E8%AE%A2%E9%80%9A%E7%9F%A5.txt
- 🟢 **TXT，直接可读** — `财会〔2018〕35号修订通知.txt`（新租赁准则 CAS 21）  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%E3%80%942018%E3%80%9535%E5%8F%B7%E4%BF%AE%E8%AE%A2%E9%80%9A%E7%9F%A5.txt
- 🟢 TXT — `财会〔2017〕22号《企业会计准则第14号--收入》.txt`（准则正文）  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%E3%80%942017%E3%80%9522%E5%8F%B7%E3%80%8A%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99%E7%AC%AC14%E5%8F%B7--%E6%94%B6%E5%85%A5%E3%80%8B.txt
- 🟢 TXT — `财会〔2018〕35号《企业会计准则第21号－租赁》.txt`（准则正文）  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%E3%80%942018%E3%80%9535%E5%8F%B7%E3%80%8A%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99%E7%AC%AC21%E5%8F%B7%EF%BC%8D%E7%A7%9F%E8%B5%81%E3%80%8B.txt
- 🟡 PDF — `财会〔2017〕7号附件《企业会计准则第22号——金融工具确认和计量》.pdf`  
  https://raw.githubusercontent.com/SuiteState-dev/note/refs/heads/main/legal%20documents/%E8%B4%A2%E4%BC%9A%E3%80%942017%E3%80%957%E5%8F%B7%E9%99%84%E4%BB%B6%E3%80%8A%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99%E7%AC%AC22%E5%8F%B7%E2%80%94%E2%80%94%E9%87%91%E8%9E%8D%E5%B7%A5%E5%85%B7%E7%A1%AE%E8%AE%A4%E5%92%8C%E8%AE%A1%E9%87%8F%E3%80%8B.pdf

---

## 五、已知缺口

- 🟢 ~~`l10n_cn_ASBE_unexecuted_rowset.md` 尚未制备~~ → **已判定不需要**（2026-08-14）：**ASBE 未执行版 form 判定不做**，论据＝适用面（三项新准则对非上市 ASBE 企业均自 2021-01-01 施行，附件1 适用面≈0），见 `项目档 v32 §4.5.21`。⚠️ 该文件此前被 `status §5` 记为「材料已到位」并两次列入施工单随单材料，实际**从未存在过** ⇒ `background v19` **惯例 28**：写「已到位」必须同时给得出 raw 链接。
- 🟡 财会〔2019〕6号**附件1 / 附件2 无转录 txt**，`小企业会计准则` 两份、`第31号应用指南` 亦为 PDF-only。若下游消费方无 PDF 取文本能力，需先补转录。
