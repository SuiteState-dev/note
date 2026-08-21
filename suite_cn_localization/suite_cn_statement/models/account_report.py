# -*- coding: utf-8 -*-
import io
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# 表内勾稽 (cross-footing) rules per reporting form, keyed by the official report's
# xmlid. Each rule: subtotal row == Σ(add rows) − Σ(sub rows), where the row keys
# are the 报送 line numbers (BS: 行次 1–72; PL: 附录B 顺序 1–43, since the tax-bureau
# P&L has no 行次). The tax-bureau importer validates these — R24 review surfaced
# that our subtotals bind to the OFFICIAL aggregation lines, which still include the
# 官方有·报送无 lines we drop from the form: BS 流动资产合计 includes 买入返售
# (cn_faur), PL 净利润 includes 以前年度损益调整 (cn_pyia). For the target segment
# (general enterprise on the new standard) both are 0 so every rule holds; a non-zero
# break equals exactly that dropped line's balance and signals data that does not fit
# this template (a financial enterprise, or prior-year P&L adjustments run through
# current profit) — which the tax bureau would reject on upload. Verified live R24.
_CN_CROSSFOOT = {
    'l10n_cn_reports.l10n_cn_asbe_bs': [
        ('14 = Σ(1..13) 流动资产合计', 14, list(range(1, 14)), []),
        ('33 = Σ(15..32) 非流动资产合计', 33, list(range(15, 33)), []),
        ('34 = 14+33 资产总计', 34, [14, 33], []),
        ('48 = Σ(35..47) 流动负债合计', 48, list(range(35, 48)), []),
        ('59 = Σ(49..58) 非流动负债合计', 59, list(range(49, 59)), []),
        ('60 = 48+59 负债合计', 60, [48, 59], []),
        ('71 = 61+62+65-66+67+68+69+70 所有者权益合计', 71,
         [61, 62, 65, 67, 68, 69, 70], [66]),
        ('72 = 60+71 负债和所有者权益总计', 72, [60, 71], []),
        ('34 = 72 资产总计=负债权益总计', 34, [72], []),
        # R37-T2 (B-69): 行9 存货 ≥ 0 —— 🔴 自推断言, 无原文背书 (编制说明无「存货不得为负」
        # 字样), 与本表其余自推勾稽同族。B-69 那个错精确抵消资产 −6000 与权益 −6000, 30=53
        # 自洽, 现有平衡类勾稽一条不响 —— 只有【语义】断言能抓: 存货是资产, 净额为负在任何口径
        # 下都是数据问题。op='nonneg' → target≥0 (add/sub=[] ⇒ expect=0, 破当 存货<0)。
        # 告警非拦截 (不阻止导出/记账); T1 阶段B 修好 5001 口径后该场景不再响属正确, 本断言
        # 留作【兜住未来其它成因造成的负存货】, 勿撤。
        ('9 ≥ 0 存货不得为负 (自推·无原文)', 9, [], [], 'structural', 'nonneg'),
    ],
    'l10n_cn_reports.l10n_cn_asbe_pl': [
        ('19 = 1-2-3-4-5-6-7+10+11+13+14+15+16+17+18 营业利润', 19,
         [1, 10, 11, 13, 14, 15, 16, 17, 18], [2, 3, 4, 5, 6, 7]),
        ('22 = 19+20-21 利润总额', 22, [19, 20], [21]),
        ('24 = 22-23 净利润', 24, [22], [23]),
        ('24 = 25+26 净利润=持续经营+终止经营', 24, [25, 26], []),
        ('27 = 28+33 其他综合收益', 27, [28, 33], []),
        ('40 = 24+27 综合收益总额', 40, [24, 27], []),
    ],
    # ASSBE (小企业会计准则) — 报送 row layout differs from ASBE (BS 53 / PL 32).
    # R30-P2: the nine rules below are now the VERBATIM 勾稽 relations of 财会〔2011〕17号
    #   附录「（二）小企业资产负债表格式及编制说明」第 4 点「本表中各项目之间的勾稽关系」
    #   (`verified` 原文). R30-P2 复核结论: our earlier SELF-DERIVED equalities matched the
    #   原文 eight equalities BYTE-FOR-BYTE — 零差异 (no strike-through needed; the derivation
    #   was correct). TWO things the 原文 pass added / reconciled:
    #   (a) NEW 行9 ≥ 行10+11+12+13 — an INEQUALITY (存货 ≥ 其中项之和); the 其中 items
    #       (原材料/在产品/库存商品/周转材料) are NON-EXHAUSTIVE (半成品/产成品/消耗性生物资产
    #       may exist unlisted), so equality would over-constrain. op='gte'. Was ABSENT before.
    #   (b) 行20 = 行18 − 行19 (原文 编制说明 (13)): 累计折旧 (行19) is filled as a POSITIVE
    #       magnitude on the 报送 form (贷方余额 = 累计折旧额). R30-P3 ① 订正 (was R30-P2's
    #       18+19neg): the FIX is to present 行19 POSITIVE (_CN_NEGATE flips Odoo's −3000 to
    #       +3000) and subtract — this matches the 原文 verbatim AND makes the printed 行19
    #       cell correct (it travels to the 税局). 行18/19 feed NO subtotal (行29 uses 行20),
    #       so the sign flip has no cascade. The earlier 18+19neg only made 行20 right while
    #       leaving 行19 printed as −3000 — a wrong outbound cell.
    #   其中 rows (存货 sub-items, 税金及附加 sub-taxes, …) remain memo lines NOT summed into
    #   their subtotal (verified live R24). Source: 财会〔2011〕17号 附录（二）小企业资产负债表
    #   编制说明 第4点「本表中各项目之间的勾稽关系」(NOT a single "3.4" — PL 勾稽 is 附录（三）
    #   第4点, CF 附录（四）第4点; three tables, three separate 第4点 — R30-P3 Safi).
    'l10n_cn_reports.l10n_cn_assbe_bs': [
        ('15 = Σ(1..9,14) 流动资产合计', 15, [1, 2, 3, 4, 5, 6, 7, 8, 9, 14], []),
        # 行9 ≥ 行10+11+12+13 存货 ≥ 其中项之和 (原材料/在产品/库存商品/周转材料，非穷尽) — 不等式
        # kind='structural' is filler (a 'gte' break carries its own message); op='gte'.
        ('9 ≥ 10+11+12+13 存货 ≥ 其中项之和', 9, [10, 11, 12, 13], [],
         'structural', 'gte'),
        # 行20 = 行18 − 行19 (原文 编制说明 (13)). 累计折旧 (行19) is filled POSITIVE on the
        # 报送 form (_CN_NEGATE presents Odoo's −3000 as +3000), so this is a plain subtract
        # matching the 原文 verbatim (R30-P3 ① 订正: was 18+19neg while 行19 rendered negative).
        ('20 = 18-19 固定资产账面价值', 20, [18], [19]),
        ('29 = 16+17+20+21+22+23+24+25+26+27+28 非流动资产合计', 29,
         [16, 17, 20, 21, 22, 23, 24, 25, 26, 27, 28], []),
        ('30 = 15+29 资产总计', 30, [15, 29], []),
        ('41 = Σ(31..40) 流动负债合计', 41, [31, 32, 33, 34, 35, 36, 37, 38, 39, 40], []),
        ('46 = Σ(42..45) 非流动负债合计', 46, [42, 43, 44, 45], []),
        ('47 = 41+46 负债合计', 47, [41, 46], []),
        ('52 = 48+49+50+51 所有者权益合计', 52, [48, 49, 50, 51], []),
        ('53 = 47+52 负债和所有者权益总计', 53, [47, 52], []),
        ('30 = 53 资产总计=负债权益总计', 30, [53], []),
        # R37-T2: 行9 存货 ≥ 0 —— 同 ASBE, 自推·无原文。负存货在 ASSBE 下同样不正常 (断言通用,
        # 虽然 B-69 的成因机制是 ASBE 特有的 5\(53) 吞成本)。已有 gte「存货≥其中项之和」是不同
        # 检查 (比对内含项和), 两条独立并存。op='nonneg' → expect=0, 破当 存货<0。
        ('9 ≥ 0 存货不得为负 (自推·无原文)', 9, [], [], 'structural', 'nonneg'),
    ],
    # R30-P3: verbatim from 财会〔2011〕17号 附录（三）小企业利润表编制说明 第4点
    # 「本表中各项目之间的勾稽关系」(`verified` 原文). Nine relations: THREE equalities
    # (行21/行30/行32 — our earlier self-derived rules matched 原文 byte-for-byte, 零差异)
    # + SIX inequalities (each 费用/收支 total ≥ Σ其中项, the 其中 items being NON-exhaustive
    # → op='gte'), previously absent. PL has NO direction split, so these are pure guards.
    'l10n_cn_reports.l10n_cn_assbe_pl': [
        ('21 = 1-2-3-11-14-18+20 营业利润', 21, [1, 20], [2, 3, 11, 14, 18]),
        ('3 ≥ Σ(4..10) 税金及附加 ≥ 其中项之和', 3, [4, 5, 6, 7, 8, 9, 10], [],
         'structural', 'gte'),
        ('11 ≥ 12+13 销售费用 ≥ 其中项之和', 11, [12, 13], [], 'structural', 'gte'),
        ('14 ≥ 15+16+17 管理费用 ≥ 其中项之和', 14, [15, 16, 17], [], 'structural', 'gte'),
        ('18 ≥ 19 财务费用 ≥ 其中利息费用', 18, [19], [], 'structural', 'gte'),
        ('30 = 21+22-24 利润总额', 30, [21, 22], [24]),
        ('22 ≥ 23 营业外收入 ≥ 其中政府补助', 22, [23], [], 'structural', 'gte'),
        ('24 ≥ Σ(25..29) 营业外支出 ≥ 其中项之和', 24, [25, 26, 27, 28, 29], [],
         'structural', 'gte'),
        ('32 = 30-31 净利润', 32, [30], [31]),
    ],
    # Cash-flow bridge form. Rules mirror the official report formulas exactly
    # (cn_cf_s_7 = Σ 1..6, s_13 = Σ 8..12, s_19 = Σ 14..18, s_20 = 7+13+19 (+UNC),
    # s_22 = 20+21) — outflow rows are stored negative, so every net is a plain sum.
    # Row 20 binds cn_cf_s_20 which also includes 未分类现金流量 (cn_cf_s_unc, dropped
    # from the reporting form). A non-zero UNC breaks 20 = 7+13+19 — but this is NOT
    # the 买入返售/以前年度损益调整 case (R25 复核): those are rare structural "wrong
    # statutory form" signals that travel to the tax bureau; UNC is a DAY-TO-DAY,
    # FIXABLE data-quality gap (N 元现金流未打标记) that only the internal accountant
    # sees (CF 不报送, §4.5.2), and R5 deliberately shows it as a visible line (行19).
    # So it carries kind='unclassified' → a DIFFERENT message ("去补标", not "换报表").
    'suite_cn_cashflow.cn_cash_flow_s': [
        ('7 = Σ(1..6) 经营活动现金流量净额', 7, [1, 2, 3, 4, 5, 6], []),
        ('13 = Σ(8..12) 投资活动现金流量净额', 13, [8, 9, 10, 11, 12], []),
        ('19 = Σ(14..18) 筹资活动现金流量净额', 19, [14, 15, 16, 17, 18], []),
        ('20 = 7+13+19 现金净增加额', 20, [7, 13, 19], [], 'unclassified'),
        ('22 = 20+21 期末现金余额', 22, [20, 21], []),
    ],
}

# Cross-foot break kinds — drive DIFFERENT user guidance (R25):
#   'structural'   — a dropped 官方有·报送无 row (买入返售 / 以前年度损益调整) carries a
#                    balance → the data belongs on a DIFFERENT statutory form. Rare,
#                    travels to the tax bureau. Guidance: 本表可能不适用，换报表。
#   'unclassified' — CF 未分类现金流量 (cn_cf_s_unc) ≠ 0 → N 元现金流没打标记. Common,
#                    fixable, internal-only (CF 不报送). Guidance: 去补标后重新导出。
_CROSSFOOT_KIND_DEFAULT = 'structural'

# Cross-foot assertion OPERATOR (R30-P2) — orthogonal to `kind` (which drives the
# message). A rule declares how its target relates to Σ(add)−Σ(sub):
#   'eq'  — target == expect            (equality; the default, all pre-R30 rules)
#   'gte' — target >= expect            (inequality; breaks ONLY when target < expect,
#           e.g. 行9 存货 ≥ 内含项之和 where the 内含 items are non-exhaustive). A 'gte'
#           break carries its OWN message regardless of `kind`.
# §15.3 category name for a 'gte' break = 「内含项超出」(inclusion). NOTE: this third
# category is DERIVED FROM op=='gte', it is NOT a third value of `kind` — grepping
# kind=='inclusion' finds nothing on purpose (R30-P2 审稿 Q2 §9.3). op ⟂ kind.
_CROSSFOOT_OP_DEFAULT = 'eq'

# 往来行方向分流 (R30-T2a / B-58) — keyed by official report xmlid. Under 财会〔2011〕17号
# 附录（二）小企业资产负债表编制说明 的【项目说明】条 (4)/(5)/(25)/(26) (NOT the 第4点勾稽;
# 项目说明 and 勾稽关系 are different parts of the same 附录（二）), the four ASSBE 往来 rows
# are a CLOSED 2×2 cross:
# each row = 按科目期末余额方向填列, credit spilling into the opposite row. We render them
# as sum_if_pos / -sum_if_neg PER ACCOUNT, two single-source terms summed — NOT a merged
# domain (each term judges its OWN account's net, so B-55 第三条边界 is not touched).
#
# Each recipe: 行次 → [(src_行次, sign, take), ...]:
#   net_src = sign * 官方值(src_行次)   ('official 行4=1122, 行5=1123, 行33=-2202, 行34=-2203',
#                                        so 2202/2203 nets need sign=-1 to undo the report's '-')
#   term    = max(0, net_src)  if take=='pos'  (= sum_if_pos(该科目))
#           = max(0, -net_src) if take=='neg'  (= -sum_if_neg(该科目), 贷方净额以正数列示)
# The split is balance-NEUTRAL (Σpos − Σ|neg| = Σnet); the asset/liability subtotals that
# contain these rows are cascaded by DELTA in _cn_dir_overrides so 53=30 holds and the
# _CN_CROSSFOOT guard stays a real check (not self-fulfilling). Official records untouched
# (P-01): the split is computed at render time from the official per-column nets, which
# makes it inherently correct per-column (期末/年初/上期 each judged on its own net).
_CN_DIR = {
    'l10n_cn_reports.l10n_cn_assbe_bs': {
        4:  [(4, 1, 'pos'), (34, -1, 'pos')],   # 应收账款 = sum_if_pos(1122) + sum_if_pos(2203)
        34: [(34, -1, 'neg'), (4, 1, 'neg')],   # 预收账款 = -sum_if_neg(2203) + -sum_if_neg(1122)
        5:  [(5, 1, 'pos'), (33, -1, 'pos')],   # 预付账款 = sum_if_pos(1123) + sum_if_pos(2202)
        33: [(33, -1, 'neg'), (5, 1, 'neg')],   # 应付账款 = -sum_if_neg(2202) + -sum_if_neg(1123)
    },
}


# 报送-form rows the official report renders NEGATIVE (contra-asset convention) that the
# 报送 layout shows as a POSITIVE magnitude in a 「减：」 row (R30-P3 ①). 财会〔2011〕17号
# 编制说明 (13) fills 「累计折旧」 from the 累计折旧 科目 期末余额 (a CREDIT balance = 累计
# 折旧额, i.e. filled POSITIVE); 行20 账面价值 = 行18 − 行19. Odoo renders the contra-asset
# 累计折旧 as −3000, so we present |value| here and the crossfoot rule subtracts (18−19).
# Only standalone 「减：」 rows belong here (无形资产 uses a single net 账面价值 line, no row).
_CN_NEGATE = {
    'l10n_cn_reports.l10n_cn_assbe_bs': {19},   # 减：累计折旧
}

# 往来成对预置守卫 (R33-A §4.5) — keyed by report xmlid. R30-T2a 的方向分流把往来对
# 【跨科目成套】拆(应收/预收 取 1122×2203、预付/应付 取 1123×2202)。若客户【只删对里的
# 一条】(如小规模不设 1123 预付账款、统一挂 2202 应付账款),该方向的净额【无处可去,只能以
# 负数挂在对侧行】—— 二姐 2026-08-11 实测:某客户行33 应付账款 −37,948 且进了行41 合计。
# 这是【科目表缺失导致的填列缺陷,不是报表引擎缺陷】,故走 dc_notice 通道(a',R33-A):提示出现
# 在会计【看/导报表那一刻】(他会问"为什么这里是负数"),而非删科目那一刻(他觉得自己有理由)。
# 每对 ((码,名),(码,名)):恰好一侧存在时,告警缺失的那侧 + 说清后果(§4.5 守卫的全部价值在后果)。
_CN_DIR_PAIRS = {
    'l10n_cn_reports.l10n_cn_assbe_bs': [
        (('1122', '应收账款'), ('2203', '预收账款')),
        (('1123', '预付账款'), ('2202', '应付账款')),
    ],
}

# 往来行 明细级 D/C 方向分流 (R30-T2b) — keyed by official report xmlid.
# ASBE 已执行版 (附件2 第16条 ≡ 附件1 第9条; §6.7 第十八条: 两版往来行公式相同): 应付账款 /
# 预付款项 按往来科目所属【明细科目】的期末借/贷方向合计列报. 机制: 逐 column_group 实跑
# account_codes 引擎的 D/C 公式 (T2-a 的净额还原法拆不出方向 —— D/C 逐 account_id 判符号,
# B-55 第一条边界). 客户未把 2202/1123 编成子账户时 D/C 退化为科目级 → go/no-go 告警+仍产出.
#
# Each recipe: 行次 → (account_codes formula, negate):
#   'C' = 该前缀下【各账户】净贷(负)才计; 'D' = 净借(正)才计 (逐 account_id, GROUP BY account_id).
#   negate=True: 引擎返回带符号值 (贷方为负); 负债行须取负显正 —— 同 _CN_NEGATE 行19 累计折旧
#                坑, 本轮第二次 (Safi 拦). negate=False: 借方本为正; 1231.03 坏账准备贷方余额
#                为负 = 自然净额扣减, 【绝不加 D/C 否则会被判负债侧丢出】, 不取负.
_CN_DC = {
    'l10n_cn_reports.l10n_cn_asbe_bs': {
        # 应付账款 = 「应付账款」(2202) 和「预付账款」(1123) 科目所属相关明细科目的期末【贷方】
        #          余额合计数 (附件2 第16条原文, observed). 引擎 2202C+1123C 返负 → 取负显正.
        39: ('2202C + 1123C', True),
        # 预付款项 = 明细【借方】合计 (2202D + 1123D) + 1231.03 坏账准备(原样净额扣减, 不参与
        #          方向分流). 预付款项【原文无条目】(附件1 15/附件2 29 均无), 明细借方合计 =
        #          §4.5.12 三唯一平衡解, 【推演非原文】. 借方本为正, 不取负.
        7:  ('2202D + 1123D + 1231.03', False),
    },
}


class AccountReport(models.Model):
    """Non-invasive extension: adds a "中式版式" export button to reports that
    have a suite.cn.statement.form, and renders that form to XLSX / PDF.

    Nothing is written onto the official report records — the button is added in
    memory during ``get_options`` and gated on the existence of a form record, so
    ``-u l10n_cn_reports`` never resets anything (R21-B2).
    """
    _inherit = 'account.report'

    # ------------------------------------------------------------------ buttons
    def _cn_statement_form(self, period_scope=None):
        """The reporting-form to render for this report at ``period_scope``.

        R26-T2 — a report may now carry several forms (月季报 / 年报). Resolution:

        * ``period_scope=None`` (button-gate check): return ANY form for the report.
        * exact ``period_scope`` match wins;
        * else a ``period_scope='any'`` form (月季=年报 cell-identical, ASSBE BS) wins;
        * else EMPTY — the caller must signal 该准则的<期间>版式尚未支持 and NOT fall
          back to another cadence. A silent monthly→annual fallback would ship the
          季报 column 口径 under a 年报 filing (the exact silent-口径-swap failure the
          ASBE 年报 has no material to avoid — 🔴 R26-T2).
        """
        self.ensure_one()
        Form = self.env['suite.cn.statement.form']
        base = [('report_id', '=', self.id)]
        if period_scope is None:
            return Form.search(base, limit=1)
        exact = Form.search(base + [('period_scope', '=', period_scope)], limit=1)
        if exact:
            return exact
        return Form.search(base + [('period_scope', '=', 'any')], limit=1)

    def _cn_has_any_form(self):
        self.ensure_one()
        return bool(self.env['suite.cn.statement.form'].search_count(
            [('report_id', '=', self.id)]))

    def _init_options_buttons(self, options, previous_options):
        super()._init_options_buttons(options, previous_options)
        # Short-circuit before the form search (R22-T3): this is a global
        # account.report override, so it runs for every report's get_options —
        # most of them not Chinese. A statement form only ever exists for a
        # Chinese report, so skip the search for non-CN reports. Gate on the
        # REPORT's own country, not env.company (R23-T4-2): env.company is the
        # first allowed company, which may be non-CN (e.g. a Chicago default with
        # chart_template=False) even while the user opens a CN report with a CN
        # company in the selector — the old chart_template gate hid the button in
        # that combination. self.country_id is a property of the report itself,
        # so it is correct under every default-company / selector combination.
        if self.country_id.code != 'CN':
            return
        # R47-T1: 科目余额表走【自己一条】中式版式路径（无 form；按 _get_lines 层级直接
        # 迭代，六/八栏 单选）。与 BS/PL 的 form 驱动路径并列，共用表头/告警/签章机件。
        if self._cn_is_trial_balance():
            options['buttons'].append({
                'name': _('中式版式 XLSX'), 'sequence': 5,
                'action': 'action_open_cn_tb_export_wizard', 'always_show': True,
            })
            return
        # R49-T1: 中式总分类账走【自己一条】中式版式路径（月汇总，无 form、无六/八栏子选项
        # ⇒ 按钮直接下载，不经向导，同「取数口径说明」按钮先例）。账簿受众=会计/审计，非报送
        # 件，表内提示允许（惯例29 受众先定）。
        if self._cn_is_general_ledger():
            options['buttons'].append({
                'name': _('中式版式 XLSX'), 'sequence': 5,
                'action': 'action_export_cn_general_ledger', 'always_show': True,
            })
            return
        # R51-T1: 中式三栏式明细分类账走【自己一条】中式版式路径（逐笔，无 form、无子选项 ⇒
        # 按钮直接下载，同总账先例）。账簿受众=会计/审计，非报送件，表内提示允许（惯例29）。
        if self._cn_is_subsidiary_ledger():
            options['buttons'].append({
                'name': _('中式版式 XLSX'), 'sequence': 5,
                'action': 'action_export_cn_subsidiary_ledger', 'always_show': True,
            })
            return
        # R53-T1: 数量金额式明细账走【自己一条】中式版式路径（换源 stock.move、无 form、无
        # 子选项 ⇒ 按钮直接下载，同三栏式先例）。账簿受众=会计/审计。
        if self._cn_is_quantity_ledger():
            options['buttons'].append({
                'name': _('中式版式 XLSX'), 'sequence': 5,
                'action': 'action_export_cn_quantity_ledger', 'always_show': True,
            })
            return
        if self._cn_has_any_form():
            # always_show=True keeps it in the main button bar (buttons without
            # it are collapsed into the cog/overflow menu — buttons_bar.js only
            # shows always_show buttons); sequence 5 puts it before the official
            # PDF(10) / XLSX(20), since the Chinese-form XLSX is the only export
            # Chinese clients use (R23-T3). The form gate keeps this off every
            # non-Chinese report, so ordering never affects them.
            #
            # R26-T2: the button now OPENS A WIZARD (报送期间 单选, default 月季报)
            # instead of downloading directly — the accountant must pick 月季报/年报
            # (isomorphic to the tax-bureau 报送期间 单选; +1 click, 5×/yr, buys
            # upgrade-safety over an account_reports options-template selector which
            # is the layer that breaks on official upgrade — background §7). No
            # file_export_type → the framework EXECUTES the returned act_window.
            options['buttons'].append({
                'name': _('中式版式 XLSX'), 'sequence': 5,
                'action': 'action_open_cn_export_wizard', 'always_show': True,
            })
            # PDF button lands with export_to_cn_pdf (design §D2); _cn_prepare
            # already drives it — added next once the QWeb template is in.
        # R48-T3：口径说明【独立说明件】——仅在带「取数口径披露行」的报表(ASBE BS)上出。
        # 受众=客户自己的会计(主动索取一份说明文档,二姐原话),与中式版式(税局/审计)分家。
        if self._cn_disclosure_note():
            options['buttons'].append({
                'name': _('取数口径说明'), 'sequence': 6,
                'action': 'action_export_cn_disclosure_note', 'always_show': False,
            })

    def action_open_cn_export_wizard(self, options):
        """Open the 中式版式 export wizard, carrying the current report options so
        the wizard can render the chosen form without re-deriving the period."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('中式版式导出'),
            'res_model': 'suite.cn.statement.export',
            'view_mode': 'form',
            # R27: account_reports 的按钮栏经 dispatch_report_action 直接把本 dict
            # 交给 client 的 actionService.doAction —— 不走 web call_button/clean_action,
            # 故 view_mode→views 的服务端补全不会发生。_preprocessAction 在
            # act_window 分支硬取 action.views.map(...)，缺 views 即 undefined.map
            # TypeError（"打开导出向导"整个挂掉）。此处显式给出 views，堵住这条路。
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_report_id': self.id,
                'cn_export_options': options,
            },
        }

    # ------------------------------------------------------- 取数口径说明件 (R48-T3)
    def _cn_disclosure_note(self):
        """独立说明件的【唯一文案源】= 本报表尾部通用披露行 account.report.line 的 name。
        导出件从它直取 ⇒ 与通用披露行【一字一致】、不会漂移(判据4 钉住)。报表不匹配则空
        ⇒ 按钮不出(仅 ASBE BS 挂了这条披露行)。"""
        self.ensure_one()
        line = self.env.ref('suite_cn_statement.cn_asbe_bs_prefix_disclosure',
                            raise_if_not_found=False)
        if line and line.report_id.id == self.id:
            return line.name or ''
        return ''

    def action_export_cn_disclosure_note(self, options):
        """工具栏「取数口径说明」→ 独立文本说明件。内容一字取自通用披露行(见 _cn_disclosure_note)。
        受众=客户会计(主动索取),载体独立于报送数据,故对外报送件里不再夹带(R48-T3)。"""
        self.ensure_one()
        note = self._cn_disclosure_note()
        content = ('%s\n取数口径说明\n%s\n\n%s\n' % (
            self.display_name, '=' * 20, note)).encode('utf-8')
        attachment = self.env['ir.attachment'].create({
            'name': '取数口径说明_%s.txt' % (self.name or self.id),
            'raw': content,
            'mimetype': 'text/plain',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    # ----------------------------------------------------------- 科目余额表 (R47-T1)
    def _cn_is_trial_balance(self):
        self.ensure_one()
        tb = self.env.ref('suite_cn_statement.cn_trial_balance', raise_if_not_found=False)
        return bool(tb) and self.id == tb.id

    def action_open_cn_tb_export_wizard(self, options):
        """打开科目余额表中式版式导出向导（六/八栏 单选）。与 BS/PL 的月季报/年报向导
        同构：控件是列集单选而非期间单选（六栏八栏都要毛额，与列集无关）。"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('科目余额表 中式版式导出'),
            'res_model': 'suite.cn.tb.export',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_report_id': self.id,
                'cn_export_options': options,
            },
        }

    def export_to_cn_tb_xlsx(self, options, columns_mode='eight'):
        """科目余额表中式版式 XLSX。数据源=_get_lines（含 handler 后处理器合成的一级行），
        非 form 行模型（惯例29 第二条路径）。六/八栏经 cn_tb_columns 塞进 options 再取数，
        故两条路径【列集一致】。

        🔴 强制 lang='zh_CN' 渲染（R47 复核③）：中式版式是法定打印/装订件，科目名按
        env.lang 渲染时若 zh_CN 未激活会落 en_US（B-68 同族，运行时用户数据不随语言回填）
        —— 法定件上出现英文科目名不可接受。与 R44 页脚 translate=False 同类问题、同解：
        本渲染器整链（get_options→_get_lines→handler 后处理取 account.name）走 zh_CN 语境；
        账套若有 zh_CN 键取中文，无则回落 en（不劣于现状）。"""
        self.ensure_one()
        report = self.with_context(lang='zh_CN')
        opts = report.get_options({**options, 'cn_tb_columns': columns_mode})
        data = report._cn_tb_prepare(opts)

        import xlsxwriter  # noqa: PLC0415
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})
        ws = wb.add_worksheet(data['sheet_name'][:31])
        F = {
            'title': wb.add_format({'bold': True, 'font_size': 15, 'align': 'center', 'valign': 'vcenter'}),
            'meta': wb.add_format({'font_size': 10}),
            'meta_r': wb.add_format({'font_size': 10, 'align': 'right'}),
            'hdr': wb.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#F2F2F2'}),
            'no': wb.add_format({'border': 1, 'align': 'center'}),
            'name': wb.add_format({'border': 1}),
            'name_b': wb.add_format({'border': 1, 'bold': True}),
            'num': wb.add_format({'border': 1, 'num_format': '#,##0.00'}),
            'num_b': wb.add_format({'border': 1, 'bold': True, 'num_format': '#,##0.00'}),
            'empty': wb.add_format({'border': 1}),
            'sign': wb.add_format({'font_size': 10, 'align': 'center', 'top': 1}),
            'warn': wb.add_format({'font_size': 10, 'bold': True, 'font_color': '#C00000',
                                   'text_wrap': True, 'valign': 'vcenter'}),
            'note': wb.add_format({'font_size': 10, 'text_wrap': True, 'valign': 'vcenter'}),
        }
        self._cn_xlsx_tb(ws, F, data)
        wb.close()
        buf.seek(0)
        return {
            'file_name': '%s_%s.xlsx' % (data['title'], data['period']),
            'file_content': buf.read(),
            'file_type': 'xlsx',
        }

    def _cn_tb_prepare(self, options):
        """把 _get_lines 的层级输出（一级父行 / 明细叶子 / 合计）摊成中式版式行序列。"""
        self.ensure_one()
        lines = self._get_lines(options)
        cols = options.get('columns', [])
        company = self._cn_report_company(options)
        dates = options.get('date') or {}
        rows = []
        dir_warnings = []            # 余额方向推导告警（判据5）→ 走警示带，不进数据行
        for line in lines:
            if line.get('cn_is_dir_warning'):
                dir_warnings.append(line.get('name') or '')
                continue
            acc_id = self._get_res_id_from_line_id(line['id'], 'account.account')
            is_parent = bool(line.get('cn_is_parent'))
            is_total = bool(line.get('cn_is_total'))
            if not (acc_id or is_parent or is_total):
                continue
            rows.append({
                'code': line.get('cn_code') or '',
                'name': line.get('cn_name') or line.get('name') or '',
                'is_parent': is_parent,
                'is_total': is_total,
                'values': [c.get('no_format') for c in line['columns']],
            })
        d = fields.Date.to_date(dates.get('date_to')) if dates.get('date_to') else fields.Date.context_today(self)
        return {
            'title': '科目余额表',
            'title_suffix': '',
            'form_no': '',                       # 科目余额表非税局报送表，无表号
            'sheet_name': '科目余额表',
            'company': company.name,
            'taxpayer_id': company.vat or company.company_registry or '',
            'taxpayer_name': company.name,
            'date_from': dates.get('date_from') or '',
            'date_to': dates.get('date_to') or '',
            'period': '%d年%d期' % (d.year, d.month),
            'unit': self._cn_unit_label(company),
            'col_headers': [c.get('name') for c in cols],
            'rows': rows,
            # TB 无表内勾稽/往来口径/页脚披露；dc_notice 承载余额方向推导告警（判据5，
            # 条件红字，账簿对内件放表内无 T3 受众问题）。footer_note 恒空（T3 已撤）。
            'crossfoot_breaks': [], 'dc_notice': dir_warnings, 'footer_note': '',
        }

    def _cn_xlsx_tb(self, ws, F, data):
        """科目余额表版式：A 空 | B 科目编码 | C 科目名称 | D.. 值列。表头带单位/所属期间/
        金额单位（§4.5.9 / 会计基础工作规范 §58）；打印页脚连续编号（§58 电算化专条）；
        末尾签章栏（单位负责人/会计负责人/制表人）。本轮只留栏位，不做签章流程（M3b 冻结）。"""
        ncol = len(data['col_headers'])
        code_c = self._CN_DATA_COL0          # 1 (B)
        name_c = code_c + 1                  # 2 (C)
        val0 = name_c + 1                    # 3 (D)
        last = val0 + ncol - 1
        self._cn_xlsx_meta(ws, F, data, code_c, last, last + 1)
        hr = self._CN_HEADER_ROW
        ws.write(hr, code_c, '科目编码', F['hdr'])
        ws.write(hr, name_c, '科目名称', F['hdr'])
        for i, h in enumerate(data['col_headers']):
            ws.write(hr, val0 + i, h, F['hdr'])
        ws.set_column(0, 0, 2)
        ws.set_column(code_c, code_c, 16)
        ws.set_column(name_c, name_c, 30)
        ws.set_column(val0, last, 16)
        # 连续编号（§58 电算化）——打印时每页页脚自动编号，可装订成册。
        ws.set_footer('&C第 &P 页 / 共 &N 页')
        r = hr + 1
        for row in data['rows']:
            bold = row['is_parent'] or row['is_total']
            ws.write(r, code_c, row['code'], F['name_b'] if bold else F['no'])
            ws.write(r, name_c, row['name'], F['name_b'] if bold else F['name'])
            for i, v in enumerate(row['values']):
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    ws.write_number(r, val0 + i, v, F['num_b'] if bold else F['num'])
                else:
                    ws.write_blank(r, val0 + i, None, F['empty'])
            r += 1
        rr = self._cn_xlsx_warning(ws, F, data, r + 1, last)
        self._cn_xlsx_signatures(ws, F, rr, last)

    # --------------------------------------------------------- 总分类账 (R49-T1)
    def _cn_is_general_ledger(self):
        self.ensure_one()
        gl = self.env.ref('suite_cn_statement.cn_general_ledger', raise_if_not_found=False)
        return bool(gl) and self.id == gl.id

    def action_export_cn_general_ledger(self, options):
        """中式总分类账 XLSX → 独立下载件（无子选项，直接 act_url，同「取数口径说明」）。"""
        self.ensure_one()
        result = self.export_to_cn_gl_xlsx(options)
        attachment = self.env['ir.attachment'].create({
            'name': result['file_name'],
            'raw': result['file_content'],
            'mimetype': ('application/vnd.openxmlformats-officedocument.'
                         'spreadsheetml.sheet'),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def export_to_cn_gl_xlsx(self, options):
        """总分类账中式版式 XLSX。数据源=handler `_cn_gl_compute`（与屏幕 _dynamic_lines_
        generator 同源单点）。🔴 强制 lang='zh_CN'（法定账簿件，同 R47 复核③：运行时科目名
        不随语言回填，法定件不可出英文名）。"""
        self.ensure_one()
        report = self.with_context(lang='zh_CN')
        opts = report.get_options(options)
        data = report._cn_gl_prepare(opts)

        import xlsxwriter  # noqa: PLC0415
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})
        ws = wb.add_worksheet(data['sheet_name'][:31])
        F = {
            'title': wb.add_format({'bold': True, 'font_size': 15, 'align': 'center', 'valign': 'vcenter'}),
            'meta': wb.add_format({'font_size': 10}),
            'meta_r': wb.add_format({'font_size': 10, 'align': 'right'}),
            'hdr': wb.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#F2F2F2'}),
            'acct': wb.add_format({'bold': True, 'border': 1, 'bg_color': '#FBFBEA'}),
            'no': wb.add_format({'border': 1, 'align': 'center'}),
            'name': wb.add_format({'border': 1}),
            'name_b': wb.add_format({'border': 1, 'bold': True}),
            'num': wb.add_format({'border': 1, 'num_format': '#,##0.00'}),
            'num_b': wb.add_format({'border': 1, 'bold': True, 'num_format': '#,##0.00'}),
            'empty': wb.add_format({'border': 1}),
            'sign': wb.add_format({'font_size': 10, 'align': 'center', 'top': 1}),
            'note': wb.add_format({'font_size': 10, 'text_wrap': True, 'valign': 'vcenter'}),
        }
        self._cn_xlsx_gl(ws, F, data)
        wb.close()
        buf.seek(0)
        return {
            'file_name': '%s_%s.xlsx' % (data['title'], data['period']),
            'file_content': buf.read(),
            'file_type': 'xlsx',
        }

    def _cn_gl_prepare(self, options):
        """把 handler 结构化计算摊成中式版式段序列。列 = 科目编码 | 科目名称 | 期间 | 摘要 |
        借方发生额 | 贷方发生额 | 方向 | 余额（R50-D：编码/名称各一列、跨该科目诸行合并）。
        每段：期初余额行 + 每有发生额期(本期合计 + 本年累计) + 只期初科目补一本年累计(0)行。"""
        self.ensure_one()
        handler = self.env['suite.cn.general.ledger.report.handler']
        computed = handler._cn_gl_compute(self, options)
        company = self._cn_report_company(options)
        dates = options.get('date') or {}
        sections = []
        for sec in computed['sections']:
            op = sec['open_period']
            o = sec['opening']
            rows = [{'period': op, 'summary': '期初余额', 'debit': None, 'credit': None,
                     'direction': o['direction'], 'balance': o['balance'], 'is_total': False}]
            for pr in sec['periods']:
                cu, yt = pr['current'], pr['ytd']
                rows.append({'period': pr['label'], 'summary': '本期合计',
                             'debit': cu['debit'], 'credit': cu['credit'],
                             'direction': cu['direction'], 'balance': cu['balance'],
                             'is_total': False})
                rows.append({'period': pr['label'], 'summary': '本年累计',
                             'debit': yt['debit'], 'credit': yt['credit'],
                             'direction': yt['direction'], 'balance': yt['balance'],
                             'is_total': True})
            if not sec['periods']:
                t = sec['total']
                rows.append({'period': op, 'summary': '本年累计', 'debit': t['debit'],
                             'credit': t['credit'], 'direction': t['direction'],
                             'balance': t['balance'], 'is_total': True})
            sections.append({'code': sec['code'], 'name': sec['name'], 'rows': rows})
        d = fields.Date.to_date(dates.get('date_to')) if dates.get('date_to') else fields.Date.context_today(self)
        return {
            'title': '总分类账',
            'title_suffix': '',
            'sheet_name': '总分类账',
            'form_no': '',
            'company': company.name,
            'taxpayer_id': company.vat or company.company_registry or '',
            'taxpayer_name': company.name,
            'date_from': dates.get('date_from') or '',
            'date_to': dates.get('date_to') or '',
            'period': '%d年%d期' % (d.year, d.month),
            'unit': self._cn_unit_label(company),
            'col_headers': ['科目编码', '科目名称', '期间', '摘要',
                            '借方发生额', '贷方发生额', '方向', '余额'],
            'sections': sections,
            'only_opening_count': computed['only_opening_count'],
            'derived_count': computed.get('derived_count', 0),
        }

    def _cn_xlsx_gl(self, ws, F, data):
        """总分类账版式：A 空 | B 科目编码 | C 科目名称 | D 期间 | E 摘要 | F 借方发生额 |
        G 贷方发生额 | H 方向 | I 余额。一级科目一段：编码/名称跨该科目诸行【纵向合并】(R50-D，
        对位导出件的表内两列)。零值金额栏留空不显 0.00(R50-E)；余额带符号(实际方向与属性相反
        为负)、平时留空。表头单位/期间；打印页脚连续编号(§58)；末尾签章栏(只留栏位，M3b 冻结)。
        账簿受众=会计/审计，口径说明放表内(惯例29 受众先定)。"""
        headers = data['col_headers']
        ncol = len(headers)
        base = self._CN_DATA_COL0            # 1 (B)
        last = base + ncol - 1               # I
        self._cn_xlsx_meta(ws, F, data, base, last, last)
        hr = self._CN_HEADER_ROW
        for i, h in enumerate(headers):
            ws.write(hr, base + i, h, F['hdr'])
        ws.set_column(0, 0, 2)
        ws.set_column(base, base, 10)          # 科目编码
        ws.set_column(base + 1, base + 1, 18)  # 科目名称
        ws.set_column(base + 2, base + 2, 8)   # 期间
        ws.set_column(base + 3, base + 3, 12)  # 摘要
        ws.set_column(base + 4, last, 15)
        ws.set_footer('&C第 &P 页 / 共 &N 页')

        def _num_or_blank(r, col, v, bold):
            # 零值/None 留空（R50-E）；非零(含负数)写数。
            if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) > 1e-9:
                ws.write_number(r, col, v, F['num_b'] if bold else F['num'])
            else:
                ws.write_blank(r, col, None, F['empty'])

        r = hr + 1
        for sec in data['sections']:
            rows = sec['rows']
            n = len(rows)
            r0 = r
            for row in rows:
                bold = row['is_total']
                nf = F['name_b'] if bold else F['name']
                ws.write(r, base + 2, row['period'], nf)
                ws.write(r, base + 3, row['summary'], nf)
                _num_or_blank(r, base + 4, row['debit'], bold)
                _num_or_blank(r, base + 5, row['credit'], bold)
                ws.write(r, base + 6, row['direction'], F['no'])         # H 方向
                bal = row['balance']
                if bal is None:                 # 平：余额栏留空（R50-E）
                    ws.write_blank(r, base + 7, None, F['empty'])
                else:
                    ws.write_number(r, base + 7, bal, F['num_b'] if bold else F['num'])
                r += 1
            # 科目编码 / 名称：跨该科目诸行纵向合并（单行时不能 merge，改 write）。
            if n > 1:
                ws.merge_range(r0, base, r0 + n - 1, base, sec['code'], F['acct'])
                ws.merge_range(r0, base + 1, r0 + n - 1, base + 1, sec['name'], F['acct'])
            else:
                ws.write(r0, base, sec['code'], F['acct'])
                ws.write(r0, base + 1, sec['name'], F['acct'])
        # 口径提示（表内，中性；账簿受众允许）——与科目余额表【口径一致】(§4.5.22 二，R50 订正)。
        note = ('说明：「方向」栏按科目余额方向属性列示（借/贷；无余额为「平」），'
                '「余额」栏为带符号余额（实际方向与属性相反时列负数）——与科目余额表'
                '【口径一致、方向与数字一致】。')
        ws.merge_range(r + 1, 0, r + 1, last, note, F['note'])
        self._cn_xlsx_signatures(ws, F, r + 3, last)

    # ==================================================== 三栏式明细分类账 (R51-T1)
    def _cn_is_subsidiary_ledger(self):
        self.ensure_one()
        sl = self.env.ref('suite_cn_statement.cn_subsidiary_ledger',
                          raise_if_not_found=False)
        return bool(sl) and self.id == sl.id

    def action_export_cn_subsidiary_ledger(self, options):
        """中式三栏式明细账 XLSX → 独立下载件（无子选项，直接 act_url，同总账）。"""
        self.ensure_one()
        result = self.export_to_cn_sl_xlsx(options)
        attachment = self.env['ir.attachment'].create({
            'name': result['file_name'],
            'raw': result['file_content'],
            'mimetype': ('application/vnd.openxmlformats-officedocument.'
                         'spreadsheetml.sheet'),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def export_to_cn_sl_xlsx(self, options):
        """三栏式明细账中式版式 XLSX。数据源 = handler `_cn_sl_compute`（与屏幕
        _dynamic_lines_generator 同源单点）。🔴 强制 lang='zh_CN'（法定账簿件，同总账）。"""
        self.ensure_one()
        report = self.with_context(lang='zh_CN')
        opts = report.get_options(options)
        data = report._cn_sl_prepare(opts)

        import xlsxwriter  # noqa: PLC0415
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})
        ws = wb.add_worksheet(data['sheet_name'][:31])
        F = {
            'title': wb.add_format({'bold': True, 'font_size': 15, 'align': 'center', 'valign': 'vcenter'}),
            'meta': wb.add_format({'font_size': 10}),
            'meta_r': wb.add_format({'font_size': 10, 'align': 'right'}),
            'hdr': wb.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#F2F2F2'}),
            'acct': wb.add_format({'bold': True, 'border': 1, 'bg_color': '#FBFBEA'}),
            'no': wb.add_format({'border': 1, 'align': 'center'}),
            'name': wb.add_format({'border': 1}),
            'name_b': wb.add_format({'border': 1, 'bold': True}),
            'num': wb.add_format({'border': 1, 'num_format': '#,##0.00'}),
            'num_b': wb.add_format({'border': 1, 'bold': True, 'num_format': '#,##0.00'}),
            'empty': wb.add_format({'border': 1}),
            'sign': wb.add_format({'font_size': 10, 'align': 'center', 'top': 1}),
            'note': wb.add_format({'font_size': 10, 'text_wrap': True, 'valign': 'vcenter'}),
        }
        self._cn_xlsx_sl(ws, F, data)
        wb.close()
        buf.seek(0)
        return {
            'file_name': '%s_%s.xlsx' % (data['title'], data['period']),
            'file_content': buf.read(),
            'file_type': 'xlsx',
        }

    def _cn_sl_prepare(self, options):
        """把 handler 结构化计算摊成中式版式段序列。列 = 日期 | 凭证字号 | 摘要 | 借方发生额 |
        贷方发生额 | 方向 | 余额（导出件锚，7 列）。每段：期初余额行 + 每有发生额期(逐笔明细行 +
        本期合计 + 本年累计) + 只期初科目补一本年累计(0)行。逐笔行余额【逐笔滚动】。"""
        self.ensure_one()
        handler = self.env['suite.cn.subsidiary.ledger.report.handler']
        computed = handler._cn_sl_compute(self, options)
        company = self._cn_report_company(options)
        dates = options.get('date') or {}
        sections = []
        for sec in computed['sections']:
            op = sec['open_date']
            o = sec['opening']
            rows = [{'date': op, 'voucher': '', 'summary': '期初余额', 'debit': None,
                     'credit': None, 'direction': o['direction'], 'balance': o['balance'],
                     'is_total': False}]
            for pr in sec['periods']:
                for ln in pr['lines']:
                    rows.append({'date': ln['date'], 'voucher': ln['voucher'],
                                 'summary': ln['summary'], 'debit': ln['debit'],
                                 'credit': ln['credit'], 'direction': ln['direction'],
                                 'balance': ln['balance'], 'is_total': False})
                cu, yt = pr['current'], pr['ytd']
                rows.append({'date': '', 'voucher': '', 'summary': '本期合计',
                             'debit': cu['debit'], 'credit': cu['credit'],
                             'direction': cu['direction'], 'balance': cu['balance'],
                             'is_total': True})
                rows.append({'date': '', 'voucher': '', 'summary': '本年累计',
                             'debit': yt['debit'], 'credit': yt['credit'],
                             'direction': yt['direction'], 'balance': yt['balance'],
                             'is_total': True})
            if not sec['periods']:
                t = sec['total']
                rows.append({'date': op, 'voucher': '', 'summary': '本年累计',
                             'debit': t['debit'], 'credit': t['credit'],
                             'direction': t['direction'], 'balance': t['balance'],
                             'is_total': True})
            sections.append({'code': sec['code'], 'name': sec['name'], 'rows': rows})
        d = fields.Date.to_date(dates.get('date_to')) if dates.get('date_to') else fields.Date.context_today(self)
        return {
            'title': '三栏式明细分类账',
            'title_suffix': '',
            'sheet_name': '三栏式明细分类账',
            'form_no': '',
            'company': company.name,
            'taxpayer_id': company.vat or company.company_registry or '',
            # 🔴 R53-T2：明细账【表头】不出公司名——载体落点已闭合（kingdee v6 §3.6b：
            # 明细账公司名在【页脚】、表头只有科目与期间；总账才在表头每页重复）。故 taxpayer_name
            # 置空、公司名只经 set_footer 落每页页脚（R52-T2 保留不动）。订正 R52「两处并存」的
            # 安全态（当时总账页脚有无未知；v6 总账第 2 页到手 ⇒ 不确定性消除）。
            'taxpayer_name': '',
            'date_from': dates.get('date_from') or '',
            'date_to': dates.get('date_to') or '',
            'period': '%d年%d期' % (d.year, d.month),
            'unit': self._cn_unit_label(company),
            'col_headers': ['日期', '凭证字号', '摘要', '借方发生额',
                            '贷方发生额', '方向', '余额'],
            'sections': sections,
            'only_opening_count': computed['only_opening_count'],
            'derived_count': computed.get('derived_count', 0),
        }

    def _cn_xlsx_sl(self, ws, F, data):
        """三栏式明细账版式：A 空 | B 日期 | C 凭证字号 | D 摘要 | E 借方发生额 | F 贷方发生额 |
        G 方向 | H 余额。科目落【段头 banner 行】(导出件里科目在表头、非表内列)；逐笔行日期取
        分录【实际日期】(§4.5.22 四陷阱：不压成期末日)。零值金额栏留空不显 0.00；余额带符号、
        逐笔滚动、平时留空。表头单位/期间；打印页脚连续编号(§58)；末尾签章栏(只留栏位，M3b)。"""
        headers = data['col_headers']
        ncol = len(headers)
        base = self._CN_DATA_COL0            # 1 (B)
        last = base + ncol - 1               # H
        self._cn_xlsx_meta(ws, F, data, base, last, last)
        hr = self._CN_HEADER_ROW
        for i, h in enumerate(headers):
            ws.write(hr, base + i, h, F['hdr'])
        ws.set_column(0, 0, 2)
        ws.set_column(base, base, 12)          # 日期
        ws.set_column(base + 1, base + 1, 10)  # 凭证字号
        ws.set_column(base + 2, base + 2, 28)  # 摘要
        ws.set_column(base + 3, last, 15)
        # 🔴 每页页脚：公司名（导出件锚 kingdee_subledger_3col_export_wanjia_1002.png，公司名在
        # 【页脚】非表头，页级要素、与 §58 连续页码同族）+ 连续页码，两者并存（R52-T2）。
        ws.set_footer('&L公司名称：%s&C第 &P 页 / 共 &N 页' % (data.get('company') or ''))

        def _num_or_blank(r, col, v, bold):
            # 零值/None 留空（R50-E 同款）；非零(含负数)写数。
            if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) > 1e-9:
                ws.write_number(r, col, v, F['num_b'] if bold else F['num'])
            else:
                ws.write_blank(r, col, None, F['empty'])

        r = hr + 1
        for sec in data['sections']:
            # 科目 banner 行：整段横跨（导出件里科目在表头一科目一段）。
            ws.merge_range(r, base, r, last,
                           '科目：%s %s' % (sec['code'], sec['name']), F['acct'])
            r += 1
            for row in sec['rows']:
                bold = row['is_total']
                nf = F['name_b'] if bold else F['name']
                ws.write(r, base, row['date'], nf)                 # B 日期
                ws.write(r, base + 1, row['voucher'], nf)          # C 凭证字号
                ws.write(r, base + 2, row['summary'], nf)          # D 摘要
                _num_or_blank(r, base + 3, row['debit'], bold)     # E 借方
                _num_or_blank(r, base + 4, row['credit'], bold)    # F 贷方
                ws.write(r, base + 5, row['direction'], F['no'])   # G 方向
                bal = row['balance']
                if bal is None:                 # 平：余额栏留空
                    ws.write_blank(r, base + 6, None, F['empty'])
                else:
                    ws.write_number(r, base + 6, bal, F['num_b'] if bold else F['num'])
                r += 1
        # 口径提示（表内，中性；账簿受众允许）——与科目余额表/总账【口径一致】(§4.5.22 二)。
        note = ('说明：「方向」栏按科目余额方向属性列示（借/贷；无余额为「平」），'
                '「余额」栏为逐笔滚动的带符号余额（实际方向与属性相反时列负数）；「日期」栏为'
                '分录实际入账日期——与科目余额表、总账【口径一致】。')
        ws.merge_range(r + 1, 0, r + 1, last, note, F['note'])
        self._cn_xlsx_signatures(ws, F, r + 3, last)

    # ================================================= 数量金额式明细账 (R53-T1)
    def _cn_is_quantity_ledger(self):
        self.ensure_one()
        ql = self.env.ref('suite_cn_statement.cn_quantity_ledger',
                          raise_if_not_found=False)
        return bool(ql) and self.id == ql.id

    def action_export_cn_quantity_ledger(self, options):
        """数量金额式明细账 XLSX → 独立下载件（无子选项，直接 act_url，同总账/三栏式）。"""
        self.ensure_one()
        result = self.export_to_cn_ql_xlsx(options)
        attachment = self.env['ir.attachment'].create({
            'name': result['file_name'],
            'raw': result['file_content'],
            'mimetype': ('application/vnd.openxmlformats-officedocument.'
                         'spreadsheetml.sheet'),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def export_to_cn_ql_xlsx(self, options):
        """数量金额式明细账中式版式 XLSX。数据源 = handler `_cn_ql_compute`（换源 stock.move，
        与屏幕 _dynamic_lines_generator 同源单点）。🔴 强制 lang='zh_CN'（法定账簿件）。"""
        self.ensure_one()
        report = self.with_context(lang='zh_CN')
        opts = report.get_options(options)
        data = report._cn_ql_prepare(opts)

        import xlsxwriter  # noqa: PLC0415
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})
        ws = wb.add_worksheet(data['sheet_name'][:31])
        F = {
            'title': wb.add_format({'bold': True, 'font_size': 15, 'align': 'center', 'valign': 'vcenter'}),
            'meta': wb.add_format({'font_size': 10}),
            'meta_r': wb.add_format({'font_size': 10, 'align': 'right'}),
            'hdr': wb.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#F2F2F2'}),
            'acct': wb.add_format({'bold': True, 'border': 1, 'bg_color': '#FBFBEA'}),
            'no': wb.add_format({'border': 1, 'align': 'center'}),
            'name': wb.add_format({'border': 1}),
            'name_b': wb.add_format({'border': 1, 'bold': True}),
            'num': wb.add_format({'border': 1, 'num_format': '#,##0.00'}),
            'num_b': wb.add_format({'border': 1, 'bold': True, 'num_format': '#,##0.00'}),
            'empty': wb.add_format({'border': 1}),
            'sign': wb.add_format({'font_size': 10, 'align': 'center', 'top': 1}),
            'note': wb.add_format({'font_size': 10, 'text_wrap': True, 'valign': 'vcenter'}),
        }
        self._cn_xlsx_ql(ws, F, data)
        wb.close()
        buf.seek(0)
        return {
            'file_name': '%s_%s.xlsx' % (data['title'], data['period']),
            'file_content': buf.read(),
            'file_type': 'xlsx',
        }

    def _cn_ql_prepare(self, options):
        """把 handler 结构化计算摊成中式版式段序列（13 列 + 摘要）。每段：期初余额行 + 每期
        (逐笔明细行 + 本期合计 + 本年累计) + 跨年补一条【合计】行（H1）。数量/金额【逐笔滚动】。"""
        self.ensure_one()
        handler = self.env['suite.cn.quantity.ledger.report.handler']
        computed = handler._cn_ql_compute(self, options)
        company = self._cn_report_company(options)
        dates = options.get('date') or {}

        def block_row(summary, blk, is_total):
            return {'date': '', 'voucher': '', 'summary': summary, 'unit': '',
                    'd_qty': blk['d_qty'], 'd_price': blk['d_price'], 'd_amt': blk['d_amt'],
                    'c_qty': blk['c_qty'], 'c_price': blk['c_price'], 'c_amt': blk['c_amt'],
                    'direction': blk['direction'], 'bal_qty': blk['bal_qty'],
                    'bal_price': blk['bal_price'], 'bal_amt': blk['bal_value'] or None,
                    'is_total': is_total}

        sections = []
        for sec in computed['sections']:
            op = sec['open_date']
            o = sec['opening']
            rows = [{'date': op, 'voucher': '', 'summary': '期初余额', 'unit': sec['unit'],
                     'd_qty': None, 'd_price': None, 'd_amt': None,
                     'c_qty': None, 'c_price': None, 'c_amt': None,
                     'direction': o['direction'], 'bal_qty': o['qty'] or None,
                     'bal_price': o['bal_price'], 'bal_amt': o['value'] or None,
                     'is_total': False}]
            for pr in sec['periods']:
                for ln in pr['lines']:
                    rows.append({'date': ln['date'], 'voucher': ln['voucher'],
                                 'summary': ln['summary'], 'unit': sec['unit'],
                                 'd_qty': ln['d_qty'], 'd_price': ln['d_price'], 'd_amt': ln['d_amt'],
                                 'c_qty': ln['c_qty'], 'c_price': ln['c_price'], 'c_amt': ln['c_amt'],
                                 'direction': ln['direction'], 'bal_qty': ln['bal_qty'],
                                 'bal_price': ln['bal_price'], 'bal_amt': ln['bal_value'] or None,
                                 'is_total': False})
                rows.append(block_row('本期合计', pr['current'], True))
                rows.append(block_row('本年累计', pr['ytd'], True))
            if sec['total_row']:
                rows.append(block_row('合计', sec['total_row'], True))
            sections.append({'acct_code': sec['acct_code'], 'acct_name': sec['acct_name'],
                             'product_name': sec['product_name'], 'rows': rows})
        d = fields.Date.to_date(dates.get('date_to')) if dates.get('date_to') else fields.Date.context_today(self)
        return {
            'title': '数量金额式明细分类账',
            'title_suffix': '',
            'sheet_name': '数量金额式明细分类账',
            'form_no': '',
            'company': company.name,
            'taxpayer_id': company.vat or company.company_registry or '',
            # 🔴 R53-T2 同款：明细账表头不出公司名（页脚承载）。
            'taxpayer_name': '',
            'date_from': dates.get('date_from') or '',
            'date_to': dates.get('date_to') or '',
            'period': '%d年%d期' % (d.year, d.month),
            'unit': self._cn_unit_label(company),
            'sections': sections,
            'is_cross_year': computed['is_cross_year'],
            'only_opening_count': computed['only_opening_count'],
        }

    _CN_QL_GROUPS = ['借方发生额', '贷方发生额', '余额']
    _CN_QL_SUBS = ['数量', '单价', '金额']

    def _cn_xlsx_ql(self, ws, F, data):
        """数量金额式版式：A 空 | B 日期 | C 凭证字号 | D 摘要 | E 单位 | F-H 借(数量/单价/金额) |
        I-K 贷(数量/单价/金额) | L 方向 | M-O 余额(数量/单价/金额)。三级表头（借/贷/余额 各横跨
        3 子列）。段头 banner = 科目 + 产品（导出件里一科目一材料一段）。🔴 三条独有规则：
        方向由金额定、双单价口径（发生额均价 vs 结存均价）、单价留空不除零。表头单位/期间；
        每页页脚 = 公司名（R52 同款）+ §58 连续页码；末尾签章栏（M3b 冻结、只留栏位）。"""
        base = self._CN_DATA_COL0                       # 1 (B)
        # 单列字段（跨两行合并）：日期/凭证字号/摘要/单位/方向
        c_date, c_vch, c_sum, c_unit = base, base + 1, base + 2, base + 3
        c_d0 = base + 4                                 # 借方三列 F,G,H
        c_c0 = base + 7                                 # 贷方三列 I,J,K
        c_dir = base + 10                               # 方向 L
        c_b0 = base + 11                                # 余额三列 M,N,O
        last = base + 13                                # O
        self._cn_xlsx_meta(ws, F, data, base, last, last)
        hr = self._CN_HEADER_ROW                        # 4
        hr2 = hr + 1
        for c, h in [(c_date, '日期'), (c_vch, '凭证字号'), (c_sum, '摘要'),
                     (c_unit, '单位'), (c_dir, '方向')]:
            ws.merge_range(hr, c, hr2, c, h, F['hdr'])
        for c0, g in [(c_d0, '借方发生额'), (c_c0, '贷方发生额'), (c_b0, '余额')]:
            ws.merge_range(hr, c0, hr, c0 + 2, g, F['hdr'])
            for i, s in enumerate(self._CN_QL_SUBS):
                ws.write(hr2, c0 + i, s, F['hdr'])
        ws.set_column(0, 0, 2)
        ws.set_column(c_date, c_date, 11)
        ws.set_column(c_vch, c_vch, 11)
        ws.set_column(c_sum, c_sum, 22)
        ws.set_column(c_unit, c_unit, 6)
        ws.set_column(c_d0, last, 11)
        # 🔴 每页页脚：公司名 + §58 连续页码（与三栏式明细账同族，R52-T2 同款）。
        ws.set_footer('&L公司名称：%s&C第 &P 页 / 共 &N 页' % (data.get('company') or ''))

        def num_or_blank(r, col, v, bold):
            # 🔴 独有规则3：None（金额/单价留空）与零值一律留空、不出 0.00；非零写数。
            if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) > 1e-9:
                ws.write_number(r, col, v, F['num_b'] if bold else F['num'])
            else:
                ws.write_blank(r, col, None, F['empty'])

        r = hr2 + 1
        for sec in data['sections']:
            ws.merge_range(r, base, r, last,
                           '科目：%s %s — %s' % (sec['acct_code'], sec['acct_name'],
                                                sec['product_name']), F['acct'])
            r += 1
            for row in sec['rows']:
                bold = row['is_total']
                nf = F['name_b'] if bold else F['name']
                ws.write(r, c_date, row['date'], nf)
                ws.write(r, c_vch, row['voucher'], nf)
                ws.write(r, c_sum, row['summary'], nf)
                ws.write(r, c_unit, row['unit'], nf)
                num_or_blank(r, c_d0, row['d_qty'], bold)
                num_or_blank(r, c_d0 + 1, row['d_price'], bold)
                num_or_blank(r, c_d0 + 2, row['d_amt'], bold)
                num_or_blank(r, c_c0, row['c_qty'], bold)
                num_or_blank(r, c_c0 + 1, row['c_price'], bold)
                num_or_blank(r, c_c0 + 2, row['c_amt'], bold)
                ws.write(r, c_dir, row['direction'], F['no'])
                num_or_blank(r, c_b0, row['bal_qty'], bold)
                num_or_blank(r, c_b0 + 1, row['bal_price'], bold)
                num_or_blank(r, c_b0 + 2, row['bal_amt'], bold)
                r += 1
        note = ('说明：「方向」栏由【金额】余额定（借/贷；金额为零/空为「平」，与数量无关）；'
                '「发生额单价」为本期均价、「余额单价」为结存均价（两个口径不同）；单价/金额分子'
                '为空时整格留空（不显 0.00）；数量+金额取自存货核算（stock.move），日期为实际'
                '出入库日期。')
        ws.merge_range(r + 1, 0, r + 1, last, note, F['note'])
        self._cn_xlsx_signatures(ws, F, r + 3, last)

    # ------------------------------------------------------------------ prepare
    def _cn_collect_values(self, options):
        """``{account.report.line id: {(group_role, expression_label): value}}``.

        ``group_role`` is ``'primary'`` for the report's own current-period column
        group and ``'comparison'`` for the prior comparable period (上期金额). The
        two are keyed by ``(role, label)`` — not by ``label`` alone — because the
        ASBE P&L reads label ``balance`` from BOTH groups (本期金额 / 上期金额), so
        the label is no longer unique (R24-T1). The role is derived from the ORDER
        of ``options['column_groups']`` (first = primary, second = comparison), the
        same order the engine lays the columns out in — verified: ``_get_lines``
        returns ``line['columns']`` 1-1 aligned with ``options['columns']``.
        """
        self.ensure_one()
        lines = self._get_lines(options)
        cols = options.get('columns', [])
        group_keys = list(options.get('column_groups') or {})
        role_of = {}
        if group_keys:
            role_of[group_keys[0]] = 'primary'
        if len(group_keys) > 1:
            role_of[group_keys[1]] = 'comparison'
        out = {}
        for line in lines:
            model, res_id = self._get_model_info_from_id(line['id'])
            if model != 'account.report.line':
                continue
            row = {}
            for col_opt, cell in zip(cols, line.get('columns', [])):
                role = role_of.get(col_opt.get('column_group_key'))
                label = col_opt.get('expression_label')
                if role and label:
                    row[(role, label)] = cell.get('no_format')
            out[res_id] = row
        return out

    def _cn_options_for(self, form, options):
        """Options to render ``form`` with. If any column reads the 上期 group,
        force a ``same_last_year`` comparison so that second group EXISTS — the
        export button is often clicked with no comparison enabled, and without it
        the 上期金额 column would silently render blank (§4.5.6 / R24-T1). One path
        serves both statutory cadences: ``same_last_year`` lands on the prior
        fiscal year for an annual filing and the same quarter last year for a
        quarterly filing (verified R24-T1)."""
        self.ensure_one()
        if not any(c.column_group == 'comparison' for c in form.column_ids):
            return options
        if (options.get('comparison') or {}).get('filter') == 'same_last_year':
            return options
        return self.get_options({
            **options,
            'comparison': {'filter': 'same_last_year', 'number_period': 1},
        })

    def _cn_period_label(self, form, options):
        date_to = (options.get('date') or {}).get('date_to')
        d = fields.Date.to_date(date_to) if date_to else fields.Date.context_today(self)
        if form.period_mode == 'point':
            return d.strftime('%Y-%m-%d')
        return '%d年%d期' % (d.year, d.month)

    def _cn_unit_label(self, company=None):
        # 铁律2: derive the currency from the report's company (options), not
        # env.company which may be a non-CN default.
        cur = (company or self.env.company).currency_id
        return '元' if (cur.name or '') in ('CNY', 'RMB') else (cur.name or '元')

    def _cn_report_company(self, options):
        """The company the report is RUN FOR (options['companies'][0]) — NOT
        env.company, which is only the first allowed company and may be a non-CN
        default (铁律2 / R23-T4-2). Falls back to env.company if options carry none."""
        comp_ids = [c['id'] for c in (options.get('companies') or []) if c.get('id')]
        return (self.env['res.company'].browse(comp_ids[0])
                if comp_ids else self.env.company)

    def _cn_assert_annual_period(self, form, options):
        """🔴 R26 review: a 年报 form is only an 年报 if its period IS a full fiscal
        year. Selecting 年报 with the report's date filter stopped at, say, Jan–Jun
        yields 本年累计半年 | 上年同期半年 — two self-consistent columns that are NOT
        an annual filing, exported under the 年报 表名/表号. That is the SAME silent-
        wrong-口径 accident the no-silent-fallback rule guards against, on the period
        axis instead of the form axis. Hard-stop rather than ship a mislabeled file."""
        if form.period_scope != 'annual':
            return
        dates = options.get('date') or {}
        df = fields.Date.to_date(dates.get('date_from'))
        dt = fields.Date.to_date(dates.get('date_to'))
        company = self._cn_report_company(options)
        fy = company.compute_fiscalyear_dates(dt) if dt else None
        if not (df and dt and fy and df == fy['date_from'] and dt == fy['date_to']):
            fy_txt = ('%s ~ %s' % (fy['date_from'], fy['date_to'])) if fy else '整个会计年度'
            raise UserError(_(
                '选择了「年报」，但报表期间（%(dfrom)s ~ %(dto)s）不是完整会计年度'
                '（%(fy)s）。\n年报的两列口径是本年累计/上年金额，非整年会导出成'
                '「半年报」却顶着年报的表名和表号——请把报表日期改为整个会计年度，'
                '或改选「月季报」。',
                dfrom=df or '（空）', dto=dt or '（空）', fy=fy_txt))

    def _cn_prepare(self, form, options):
        """Format-agnostic structure driving both XLSX and PDF."""
        self.ensure_one()
        options = self._cn_options_for(form, options)
        values = self._cn_collect_values(options)
        cols = form.column_ids.sorted('sequence')
        dir_over = self._cn_dir_overrides(form, values)
        dc_over, dc_notice = self._cn_dc_overrides(form, options, values)
        negate = self._cn_negate_rows(form)

        def cells(row):
            if row.is_header or not row.report_line_id:
                return [None] * len(cols)
            v = values.get(row.report_line_id.id, {})
            rn = int(row.row_no) if (row.row_no or '').strip().isdigit() else None
            # a report carries EITHER the ASSBE net-split (_CN_DIR) OR the ASBE D/C
            # split (_CN_DC), never both — so one of these is always empty for it.
            ov = dir_over.get(rn) or dc_over.get(rn)
            neg = rn in negate
            out = []
            for c in cols:
                ck = (c.column_group, c.expression_label)
                val = ov[ck] if (ov is not None and ck in ov) else v.get(ck)
                if neg and isinstance(val, (int, float)) and not isinstance(val, bool):
                    val = -val
                out.append(val)
            return out

        def prep(row):
            return {
                'row_no': row.row_no or '', 'name': row.name,
                'is_header': row.is_header, 'values': cells(row),
            }

        rows = form._effective_rows().sorted('sequence')
        # 铁律2 / R23-T4-2: taxpayer identity = the company the report is RUN FOR.
        company = self._cn_report_company(options)
        dates = options.get('date') or {}
        data = {
            'title': form.title,
            'title_suffix': form.title_suffix or '',
            'form_no': form.form_no or '',
            'sheet_name': (form.sheet_name or form.title),
            'company': company.name,
            # 纳税人识别号 (R26-T1): base Tax-ID field; for a CN company this is the
            # 18-digit 统一社会信用代码. company_registry is the documented fallback.
            # Whether a given customer fills vat vs company_registry is graded
            # `unknown` (design §7.1) — not verifiable headlessly.
            'taxpayer_id': company.vat or company.company_registry or '',
            'taxpayer_name': company.name,
            'date_from': dates.get('date_from') or '',
            'date_to': dates.get('date_to') or '',
            'period': self._cn_period_label(form, options),
            'unit': self._cn_unit_label(company),
            'col_headers': [c.header for c in cols],
            'layout': form.layout,
            'ncols': len(cols),
            'has_row_no': form.has_row_no,
        }
        if form.layout == 'two_column':
            data['left'] = [prep(r) for r in rows if r.section == 'left']
            data['right'] = [prep(r) for r in rows if r.section == 'right']
        else:
            data['rows'] = [prep(r) for r in rows]
        data['crossfoot_breaks'] = self._cn_crossfoot_breaks(form, data)
        # 往来明细级口径声明 (R30-T2b go/no-go) — SEPARATE from crossfoot breaks: it is a
        # 取数口径 notice (往来科目未编子账户 → 科目级), NOT an arithmetic break, so it does
        # not enter _cn_crossfoot_breaks nor carry a `kind` (would pollute §15.3's table).
        # R33-A §4.5: 往来成对预置缺失,并进同一 dc_notice 通道(不改其既有语义,只加一类消息)。
        data['dc_notice'] = dc_notice + self._cn_dir_pair_gap(form, options)
        # R44-T2: 页脚取数口径静态披露 (中式版式导出路径的载体;中性格式,见 _cn_xlsx_warning)。
        data['footer_note'] = form.footer_note or ''
        return data

    def _cn_dir_pair_gap(self, form, options):
        """往来对缺一时的告警文案 (R33-A §4.5)。恰好一侧存在 → 告警缺失侧 + 后果。

        为什么是"恰好一侧":两侧都在 → 分流正常;两侧都无 → 该客户不用这对往来,无 spill,
        不告警(免噪)。asymmetric 才是二姐追出的缺陷(有 2202 无 1123 → 借方净额挂负数)。"""
        pairs = None
        for xmlid, p in _CN_DIR_PAIRS.items():
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            if rec and rec.id == form.report_id.id:
                pairs = p
                break
        if not pairs:
            return []
        company = self._cn_report_company(options)
        Account = self.env['account.account'].with_company(company).with_context(
            active_test=False)

        def present(prefix):
            return bool(Account.search(
                [('company_ids', 'in', company.id),
                 ('code', '=like', prefix + '%')], limit=1))

        notices = []
        for (ca, na), (cb, nb) in pairs:
            a, b = present(ca), present(cb)
            if a == b:
                continue
            code, name = (ca, na) if not a else (cb, nb)
            notices.append(
                '⚠ 缺往来科目「%s %s」：应收/应付/预收/预付 方向分流(R30-T2a)将失效，'
                '该方向余额会以负数挂到对侧行——实测:缺 1123 预付账款 → 借方净额 −37,948 '
                '挂在行33 应付账款并计入行41 合计。请补建该科目后重新导出。' % (code, name))
        return notices

    def _cn_negate_rows(self, form):
        """行次 set to present as a positive magnitude (see _CN_NEGATE), or empty."""
        for xmlid, rows in _CN_NEGATE.items():
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            if rec and rec.id == form.report_id.id:
                return rows
        return set()

    # ------------------------------------------ 往来行明细级 D/C 方向分流 (R30-T2b)
    def _cn_dc_rules(self, form):
        """The D/C direction-split recipe map {行次: (formula, negate)}, or {}."""
        for xmlid, rules in _CN_DC.items():
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            if rec and rec.id == form.report_id.id:
                return rules
        return {}

    def _cn_dc_subaccount_gap(self, options, rules):
        """The set of D/C 往来 prefixes that have NO 明细子账户 in the report's
        companies. For these, `account_codes` D/C degrades from 明细级 to 科目级
        (go/no-go): each prefix has a single account, so `2202C` = the whole 2202
        net, not a per-明细 credit sum. Non-empty → 科目级口径 notice (惯例9: 标明
        口径 + 仍产出, not 拒绝产出)."""
        import re  # noqa: PLC0415
        prefixes = set()
        for formula, _neg in rules.values():
            prefixes |= set(re.findall(r'(\d+)[CD](?![\w.])', formula))
        if not prefixes:
            return set()
        companies = self.get_report_company_ids(options)
        Acc = self.env['account.account'].with_context(active_test=False)
        gap = set()
        for p in prefixes:
            matches = Acc.search([('code', '=like', p + '%'),
                                  ('company_ids', 'in', companies)])
            # a 子账户 = a matching account whose code extends the prefix (2202.01 / 220201)
            has_sub = any(a.code != p and len(a.code) > len(p) for a in matches)
            if not has_sub:
                gap.add(p)
        return gap

    def _cn_dc_overrides(self, form, options, values):
        """R30-T2b: 明细级 D/C 方向分流 of the ASBE 往来 rows + subtotal cascade.

        Runs the `account_codes` engine with a D/C formula PER (column_group, label)
        — T2-a's net-recovery CANNOT split direction (D/C judges each account_id's
        sign, not derivable from the line net; B-55 第一条边界). Each column uses ITS
        OWN official expression's date_scope, so 期末/年初/上期 each judge direction
        independently (double-column). negate flips the 引擎's signed value to a
        positive 报送 magnitude on liability rows (同 行19 累计折旧). Subtotals are
        cascaded by DELTA (same as _cn_dir_overrides). Returns (overrides, notice)."""
        rules = self._cn_dc_rules(form)
        if not rules:
            return {}, []

        def num(v):
            return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0

        group_keys = list(options.get('column_groups') or {})
        role_of = {}
        if group_keys:
            role_of[group_keys[0]] = 'primary'
        if len(group_keys) > 1:
            role_of[group_keys[1]] = 'comparison'
        cgs = self._split_options_per_column_group(options)

        rows = form._effective_rows()
        off = {}
        for r in rows:
            if r.report_line_id and (r.row_no or '').strip().isdigit():
                off[int(r.row_no)] = values.get(r.report_line_id.id, {})
        colkeys = set()
        for d in off.values():
            colkeys |= set(d.keys())
        render_labels = {lbl for _role, lbl in colkeys}
        row_by_no = {int(r.row_no): r for r in rows
                     if (r.row_no or '').strip().isdigit() and r.report_line_id}

        overrides, delta = {}, {}
        for rn, (formula, neg) in rules.items():
            r = row_by_no.get(rn)
            if not r:
                continue
            ov, dl = {}, {}
            for expr in r.report_line_id.expression_ids:
                if expr.label not in render_labels:
                    continue
                for cg_key, cgo in cgs.items():
                    role = role_of.get(cg_key)
                    if not role:
                        continue
                    fr = self._compute_formula_batch_with_engine_account_codes(
                        cgo, expr.date_scope, {formula: expr}, None, None)
                    val = 0.0
                    for _k, res in fr.items():
                        val = res.get('result', 0.0) if isinstance(res, dict) else num(res)
                    if neg:
                        val = -val
                    ck = (role, expr.label)
                    ov[ck] = val
                    dl[ck] = val - num(off.get(rn, {}).get(ck))
            overrides[rn], delta[rn] = ov, dl

        # cascade subtotals containing a reassembled 往来 row (delta, not full recompute)
        for rule in self._cn_crossfoot_rules(form):
            target, add, sub = rule[1], rule[2], rule[3]
            op = rule[5] if len(rule) > 5 else _CROSSFOOT_OP_DEFAULT
            if op == 'gte' or target in overrides:
                continue
            ov, dl, touched = {}, {}, False
            for ck in colkeys:
                d = (sum(delta.get(a, {}).get(ck, 0.0) for a in add)
                     - sum(delta.get(s, {}).get(ck, 0.0) for s in sub))
                if abs(d) > 1e-6:
                    touched = True
                ov[ck] = num(off.get(target, {}).get(ck)) + d
                dl[ck] = d
            if touched:
                overrides[target], delta[target] = ov, dl

        # go/no-go: 无子账户 → 科目级口径声明 (NOT a crossfoot break; 惯例9 标明+产出)
        gap = self._cn_dc_subaccount_gap(options, rules)
        notice = []
        if gap:
            notice.append('⚠ 本表「应付账款/预付款项」按往来科目明细方向列报，但这两个'
                          '科目下未设明细子账户，本行取的是科目级口径（非明细级）。')
        return overrides, notice

    # ------------------------------------------------------ 往来行方向分流 (B-58)
    def _cn_dir_rules(self, form):
        """The direction-split recipe map for this form, or {} if none."""
        for xmlid, recipes in _CN_DIR.items():
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            if rec and rec.id == form.report_id.id:
                return recipes
        return {}

    def _cn_dir_overrides(self, form, values):
        """R30-T2a (B-58): directional split of the ASSBE 往来 rows + subtotal cascade.

        Returns ``{行次: {(column_group, label): value}}`` for every row whose rendered
        value differs from its official line — the four 往来 details reassembled as
        ``sum_if_pos``/``-sum_if_neg`` per account (per _CN_DIR), plus the asset/liability
        subtotals that contain them, shifted by the reassembly DELTA so ``53 = 30`` holds.
        Empty for forms without a _CN_DIR recipe. Official records are never touched: the
        split reads the official per-column nets, so each column (期末/年初/上期) is judged
        on its OWN net — the double-column direction requirement is satisfied by design."""
        recipes = self._cn_dir_rules(form)
        if not recipes:
            return {}

        def num(v):
            return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0

        # 行次 → official {(column_group, label): value}
        off = {}
        for r in form._effective_rows():
            if r.report_line_id and (r.row_no or '').strip().isdigit():
                off[int(r.row_no)] = values.get(r.report_line_id.id, {})
        colkeys = set()
        for d in off.values():
            colkeys |= set(d.keys())

        overrides, delta = {}, {}
        # (1) reassemble the four 往来 details from the official per-column nets.
        for target, terms in recipes.items():
            ov, dl = {}, {}
            for ck in colkeys:
                tot = 0.0
                for src, sign, take in terms:
                    net = sign * num(off.get(src, {}).get(ck))
                    tot += max(0.0, net) if take == 'pos' else max(0.0, -net)
                ov[ck] = tot
                dl[ck] = tot - num(off.get(target, {}).get(ck))
            overrides[target], delta[target] = ov, dl

        # (2) cascade the subtotals that transitively contain a reassembled detail,
        # reusing the _CN_CROSSFOOT structure. Adjust each by its DELTA (not a full
        # recompute-from-details) so a genuine dropped-row discrepancy in an official
        # subtotal is still surfaced by the crossfoot guard. Rules are ordered bottom-up
        # (15→30, 41→47→53); the first rule targeting a row defines it (the 30=53
        # identity rule then just checks equality, so skip re-defining an existing target).
        for rule in self._cn_crossfoot_rules(form):
            target, add, sub = rule[1], rule[2], rule[3]
            op = rule[5] if len(rule) > 5 else _CROSSFOOT_OP_DEFAULT
            if op == 'gte' or target in overrides:
                continue
            ov, dl, touched = {}, {}, False
            for ck in colkeys:
                d = (sum(delta.get(a, {}).get(ck, 0.0) for a in add)
                     - sum(delta.get(s, {}).get(ck, 0.0) for s in sub))
                if abs(d) > 1e-6:
                    touched = True
                ov[ck] = num(off.get(target, {}).get(ck)) + d
                dl[ck] = d
            if touched:
                overrides[target], delta[target] = ov, dl
        return overrides

    # --------------------------------------------------------------- crossfoot
    def _cn_crossfoot_rules(self, form):
        """The 表内勾稽 rule set for this form, or [] if none is registered."""
        for xmlid, rules in _CN_CROSSFOOT.items():
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            if rec and rec.id == form.report_id.id:
                return rules
        return []

    def _cn_crossfoot_breaks(self, form, data):
        """Check the reporting form's internal arithmetic (合计行 = Σ 明细行) on the
        rendered values and return the breaks. R24 review: our subtotals bind to the
        official aggregation lines, which still include the 官方有·报送无 rows we drop
        — so a non-zero balance on such a row makes a subtotal exceed the sum of its
        shown detail by exactly that amount. The delta pins the offending row. Runs
        as an export-time / pre-upload self-check (the tax-bureau importer validates
        the same relationships). Returns ``[(label, col, actual, expect, delta)]``."""
        rules = self._cn_crossfoot_rules(form)
        if not rules:
            return []

        def num(v):
            return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0

        ncols = data['ncols']
        # value_by_col[c] = {报送行号: value} for value column c
        value_by_col = [{} for _ in range(ncols)]
        if data['layout'] == 'two_column':
            src = [(int(r['row_no']), r) for r in (data['left'] + data['right'])
                   if not r['is_header'] and (r['row_no'] or '').strip().isdigit()]
        else:
            # single (P&L has no 行次): key by 1-based position = 附录B 顺序
            src = [(i, r) for i, r in enumerate(data['rows'], start=1)]
        for key, r in src:
            for c in range(ncols):
                value_by_col[c][key] = num(r['values'][c] if c < len(r['values']) else None)

        breaks = []
        for c in range(ncols):
            vals = value_by_col[c]
            for rule in rules:
                # A rule is (label, target, add, sub[, kind[, op]]). `kind` drives the
                # user message (structural vs unclassified); `op` the assertion type
                # (eq vs gte) — see _CROSSFOOT_KIND_* / _CROSSFOOT_OP_*.
                label, target, add, sub = rule[0], rule[1], rule[2], rule[3]
                kind = rule[4] if len(rule) > 4 else _CROSSFOOT_KIND_DEFAULT
                op = rule[5] if len(rule) > 5 else _CROSSFOOT_OP_DEFAULT
                expect = sum(vals.get(i, 0.0) for i in add) - sum(vals.get(i, 0.0) for i in sub)
                actual = vals.get(target, 0.0)
                delta = round(actual - expect, 2)
                if op in ('gte', 'nonneg'):
                    # inequality: a break is ONLY a shortfall (target below expect).
                    # 'gte'  expect=Σ其中项 (excess legal, non-exhaustive 其中项).
                    # 'nonneg' expect=0 (add/sub=[]): a break is target<0 (R37-T2/B-69).
                    broke = delta < -0.01
                else:
                    broke = abs(delta) > 0.01
                if broke:
                    breaks.append((label, c, actual, expect, delta, kind, op))
        return breaks

    def _cn_log_crossfoot(self, form, breaks):
        """Log a WARNING per cross-foot break so it is caught before the file is
        uploaded to the tax bureau (the delta points at the dropped row)."""
        for b in breaks:
            label, col, actual, expect, delta, kind = b[0], b[1], b[2], b[3], b[4], b[5]
            op = b[6] if len(b) > 6 else _CROSSFOOT_OP_DEFAULT
            if op == 'nonneg':
                # 存货为负 (R37-T2 / B-69). Accountant-facing FIX guidance lives HERE (the
                # outbound 税局 line states only the observed number — never volunteer a
                # 数据错误 admission to the tax bureau, R30-P2 审稿 ②).
                hint = ("存货净额为负 (%.2f) — 资产项不应为负; 常见成因: 生产成本/在产品(5xxx)"
                        "未计入存货取数口径(B-69, T1 阶段B 修), 或红冲/结转方向错误。核对"
                        "存货相关科目余额后重新导出。") % actual
            elif op == 'gte':
                # 「内含项超出」(inclusion, op='gte'). The full "this is a DATA error, go
                # fix it and re-export" guidance lives HERE (log reader = the accountant),
                # NOT in the outbound file line (R30-P2 审稿 ②).
                hint = ("内含项超出 (inclusion) break: the 内含项 sum (%.2f) EXCEEDS its "
                        "parent total (%.2f) by %.2f — a DATA ERROR (内含项 录多 or 总额 录少), "
                        "not a wrong-form signal; fix the 内含项 mapping/data and re-export.") \
                    % (expect, actual, -delta)
            elif kind == 'unclassified':
                hint = ("%.2f of cash flow is UNCLASSIFIED (cn_cf_s_unc) — a fixable "
                        "data-quality gap, NOT a wrong-form signal; classify it and "
                        "re-export (CF is internal, not filed).") % abs(delta)
            else:
                hint = ("A dropped 官方有·报送无 line carries this balance; this data "
                        "may not fit this statutory template and could be rejected on "
                        "财报导入 (design §15.3).")
            rel = '≥' if op in ('gte', 'nonneg') else '='
            _logger.warning(
                "suite_cn_statement 表内勾稽 break on %s [%s] col%d (%s/%s): %s — "
                "合计=%.2f Σ明细%s%.2f 差=%.2f. %s",
                form.title, form.report_id.name, col, kind, op, label, actual, rel,
                expect, delta, hint)

    def _cn_crossfoot_messages(self, data):
        """Human-readable 表内勾稽 warning lines for the export file itself (§7.0
        铁律1: the accountant clicking Export never sees the server log). Returns []
        when the form cross-foots. R25: split by KIND so a 未分类现金流量 gap (fixable,
        'go classify it') is NOT worded like a 买入返售/以前年度损益调整 structural break
        ('this form may not apply') — sharing the wording would make the accountant
        think the report is broken when the fix is just tagging a line (§15.3)."""
        breaks = data.get('crossfoot_breaks') or []
        if not breaks:
            return []
        headers = data.get('col_headers') or []

        def op_of(b):
            return b[6] if len(b) > 6 else _CROSSFOOT_OP_DEFAULT

        def kind_of(b):
            return b[5] if len(b) > 5 else 'structural'

        def detail(b):
            label, col, actual, expect, delta = b[0], b[1], b[2], b[3], b[4]
            hdr = headers[col] if col < len(headers) else ''
            if op_of(b) == 'nonneg':
                # R37-T2: 税局-facing line — only the observed number, no 数据错误 admission
                # (fix guidance is in the server log for the accountant). 行次 + 金额。
                rowno = (label.split() or [label])[0]
                return ('　行 %s ［%s］ 存货为负数 %.2f 元，请核对存货相关科目'
                        % (rowno, hdr, actual))
            if op_of(b) == 'gte':
                # Q4: accountant reads an ABSOLUTE amount + direction word, not a
                # signed delta (−20 confuses). Tuple keeps the signed delta.
                # R30-P2 审稿 ①③: outbound text (goes to the 税局 with the file) states
                # only the observed numbers — no normative "子项不应大于总额" claim (that
                # premise 待核 Q2b) and no per-rule example. Just the 行次 + figures.
                rowno = (label.split() or [label])[0]  # leading 行次, e.g. '9'
                return ('　行 %s ［%s］ 总额 %.2f，内含项之和 %.2f，超出 %.2f 元'
                        % (rowno, hdr, actual, expect, abs(delta)))
            return ('　行 %s ［%s］ 合计 %.2f ≠ Σ明细 %.2f，差 %+.2f'
                    % (label, hdr, actual, expect, delta))

        # 'gte' (inequality / 「内含项超出」) and 'nonneg' (存货为负, R37-T2) breaks are each
        # their own class — worded independently of structural/unclassified.
        inequality = [b for b in breaks if op_of(b) == 'gte']
        nonneg = [b for b in breaks if op_of(b) == 'nonneg']
        eq_breaks = [b for b in breaks if op_of(b) not in ('gte', 'nonneg')]
        structural = [b for b in eq_breaks if kind_of(b) != 'unclassified']
        unclassified = [b for b in eq_breaks if kind_of(b) == 'unclassified']
        lines = []
        if structural:
            lines.append('⚠ 本表存在 %d 处表内勾稽差异，本表可能不适用于该主体，请核对是否'
                         '选错报送主体/报表（如买入返售属金融企业、以前年度损益调整不入当期'
                         '损益）：' % len(structural))
            lines += [detail(b) for b in structural]
        if unclassified:
            total = sum(abs(b[4]) for b in unclassified)
            lines.append('⚠ 有 %.2f 元现金流未分类，请到「现金流量项目 / 分录」补标后重新'
                         '导出（本表不报送，此为数据质量提示，非报表错误）：' % total)
            lines += [detail(b) for b in unclassified]
        if inequality:
            # R30-P2 审稿 ①②③: the outbound (税局-facing) line drops the absolute
            # "子项不应大于总额" claim (待核 Q2b), the self-incriminating "此为数据错误"
            # (never volunteer "our data is wrong" to the tax bureau), and the per-rule
            # example. The "go fix the data" guidance moves to the server log
            # (_cn_log_crossfoot) whose reader is the accountant, not the tax bureau.
            lines.append('⚠ 本表有 %d 处内含项之和超过其所属总额，请核对内含项的科目归属与'
                         '数据后重新导出。' % len(inequality))
            lines += [detail(b) for b in inequality]
        if nonneg:
            # R37-T2 (B-69): 存货为负 —— 独立文案。税局-facing: 只述观察事实, 修复口径见服务器日志。
            lines.append('⚠ 本表有 %d 处存货项为负数，存货为资产项不应为负，请核对存货相关'
                         '科目余额后重新导出。' % len(nonneg))
            lines += [detail(b) for b in nonneg]
        return lines

    _PERIOD_LABEL = {'monthly_quarterly': '月季报', 'annual': '年报'}

    def _cn_resolve_form_or_raise(self, period_scope):
        """The form for ``period_scope`` — or an explicit UserError when the report
        has forms but none for this cadence (🔴 R26-T2: never a silent fallback).
        Returns None only for a report with NO form at all (non-CN caller path)."""
        self.ensure_one()
        form = self._cn_statement_form(period_scope)
        if form:
            return form
        if self._cn_has_any_form():
            raise UserError(_(
                '“%(report)s” 的%(period)s版式尚未支持。\n'
                '（该准则此报送期间的列口径无官方材料，不能用其它期间的版式代替——'
                '否则会以错误口径生成报送件。）',
                report=self.name,
                period=self._PERIOD_LABEL.get(period_scope, period_scope or '')))
        return None

    # -------------------------------------------------------------------- XLSX
    def export_to_cn_xlsx(self, options, period_scope='monthly_quarterly'):
        self.ensure_one()
        form = self._cn_resolve_form_or_raise(period_scope)
        if not form:
            return super().export_to_xlsx(options)
        # 🔴 an 年报 form must be over a FULL fiscal year, else it is a mislabeled
        # 半年报 (same silent-wrong-口径 class as the no-fallback rule, period axis).
        self._cn_assert_annual_period(form, options)
        data = self._cn_prepare(form, options)
        # Pre-upload self-check: 数值对 + 行次对 ≠ 表内勾稽对 (R24 review). A break
        # equals the balance of a dropped 官方有·报送无 row and would be rejected by
        # the tax-bureau importer. Surface it BOTH in the log AND in the file itself
        # (§7.0 铁律1: the accountant clicking Export never reads the server log — the
        # warning must travel with the xlsx). The in-file line is rendered above the
        # signature boxes by _cn_xlsx_signatures.
        self._cn_log_crossfoot(form, data['crossfoot_breaks'])
        # 往来明细级口径声明 → WARNING (not raise; the reader here is the accountant, so
        # the log carries the FIX guidance the outbound file omits, R30-T2b 审稿).
        if data.get('dc_notice'):
            _logger.warning(
                "suite_cn_statement 往来明细级口径 on %s [%s]: 应付账款/预付款项 科目下未设"
                "明细子账户 → 本表取【科目级】口径（非明细级）。如需明细级列报，请按供应商/"
                "客户为「应付账款」「预付账款」科目建明细子账户后重新导出（账套结构调整，"
                "非导出前临时修改）。",
                form.title, form.report_id.name)

        import xlsxwriter  # noqa: PLC0415  (Odoo-standard late import)
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})
        ws = wb.add_worksheet(data['sheet_name'][:31])
        F = {
            'title': wb.add_format({'bold': True, 'font_size': 15, 'align': 'center', 'valign': 'vcenter'}),
            'meta': wb.add_format({'font_size': 10}),
            'meta_r': wb.add_format({'font_size': 10, 'align': 'right'}),
            'hdr': wb.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#F2F2F2'}),
            'no': wb.add_format({'border': 1, 'align': 'center'}),
            'name': wb.add_format({'border': 1}),
            'name_b': wb.add_format({'border': 1, 'bold': True}),
            'num': wb.add_format({'border': 1, 'num_format': '#,##0.00'}),
            'empty': wb.add_format({'border': 1}),
            'sign': wb.add_format({'font_size': 10, 'align': 'center', 'top': 1}),
            'warn': wb.add_format({'font_size': 10, 'bold': True, 'font_color': '#C00000',
                                   'text_wrap': True, 'valign': 'vcenter'}),
            # R44-T2 取数口径静态披露：口径声明 ≠ 勾稽告警 → 【中性格式】(非 warn 的红字/粗体)。
            # 红字会在法定报送件上凭空出现一条像异常的行,而它恒真、什么异常都不表示。
            'note': wb.add_format({'font_size': 10, 'text_wrap': True, 'valign': 'vcenter'}),
        }
        if data['layout'] == 'two_column':
            self._cn_xlsx_two_column(ws, F, data)
        else:
            self._cn_xlsx_single(ws, F, data)
        wb.close()
        buf.seek(0)
        return {
            'file_name': '%s_%s.xlsx' % (data['title'], data['period']),
            'file_content': buf.read(),
            'file_type': 'xlsx',
        }

    def _cn_write_value(self, ws, r, c, val, F):
        if isinstance(val, bool) or val is None:
            ws.write_blank(r, c, None, F['empty'])
        elif isinstance(val, (int, float)):
            ws.write_number(r, c, val, F['num'])
        else:
            ws.write_blank(r, c, None, F['empty'])

    # R26-T1: the tax-bureau template geometry (verified against the corrected
    # structure spec; the exact metadata-cell columns are fixture-pinned by
    # test_template_alignment once the official .xls lands):
    #   * a BLANK column A (index 0) — the whole data block sits one column right;
    #   * 项目 BEFORE 行次 (was 行次|项目);
    #   * BS two-column has NO gap column between the two sides (8 data cols B..I);
    #   * rows 0 表名+适用说明 / 1 表号+单位 / 2 纳税人识别号+名称 / 3 所属期起+止 /
    #     4 列头 / 5+ 数据.
    # 资产 / 负债和所有者权益 are BS layout invariants (identical on ASSBE & ASBE), so
    # they live here as two_column constants — not per-form statutory text.
    # Official 税局报送采集 template uses the compact 2-char header (NOT the spaced
    # 资　产) — verified cell-for-cell against the .xls fixture (R27).
    _CN_BS_LEFT_HEADER = '资产'
    _CN_BS_RIGHT_HEADER = '负债和所有者权益'
    _CN_HEADER_ROW = 4          # 列头行 (0-indexed); data starts at _CN_HEADER_ROW+1
    _CN_DATA_COL0 = 1           # blank column A → data starts at column B

    def _cn_xlsx_meta(self, ws, F, data, meta_left, meta_right, end_col):
        """Rows 0–3: 表名+适用说明 / 表号+单位 / 纳税人识别号·名称 / 所属期起·止.
        Cell-aligned to the OFFICIAL 税局报送采集 template (R27, fixture-pinned by
        test_template_alignment — the prose spec was wrong twice: it missed both the
        blank column A on the title row and the bare metadata labels):
          * 表名 merges from column B (blank column A stays empty, NOT from column A)
            and carries the per-form 表名 INCLUDING its _月季报/_年 discriminator —
            i.e. ``sheet_name`` (利润表_月季报 vs 利润表_年 differ only here), never the
            bare ``title``;
          * ``end_col`` = the sheet's rightmost column, which holds 表号+单位 (a single
            form reserves ONE trailing column past its last value column; the
            two-column BS puts 表号 on the last value column — both fixture-pinned);
          * 表号 与 单位 are separated by THREE ASCII spaces (official), never 全角 空格;
          * 识别号/名称 · 起/止 are BARE labels — the collection template puts the label
            in one cell and leaves the value cell for the taxpayer; we pre-fill the
            value in ``label_col+1`` (empty on demo companies → the customer fills it).
        meta_left / meta_right = the two label columns (识别号 left · 名称 right; 起
        left · 止 right)."""
        ws.merge_range(0, self._CN_DATA_COL0, 0, end_col,
                       (data['sheet_name'] + (data['title_suffix'] or '')), F['title'])
        ws.set_row(0, 26)
        ws.write(1, end_col, '%s   单位：%s' % (data['form_no'], data['unit']),
                 F['meta_r'])
        ws.write(2, meta_left, '纳税人识别号', F['meta'])
        ws.write(2, meta_left + 1, data['taxpayer_id'], F['meta'])
        ws.write(2, meta_right, '纳税人名称', F['meta'])
        ws.write(2, meta_right + 1, data['taxpayer_name'], F['meta'])
        ws.write(3, meta_left, '所属期起', F['meta'])
        ws.write(3, meta_left + 1, data['date_from'], F['meta'])
        ws.write(3, meta_right, '所属期止', F['meta'])
        ws.write(3, meta_right + 1, data['date_to'], F['meta'])

    def _cn_xlsx_single(self, ws, F, data):
        ncol = data['ncols']
        # A(0) blank | B 项目 | C 行次 | D.. values  (项目 BEFORE 行次, R26-T1).
        # has_row_no=False (tax-bureau ASBE P&L) drops the 行次 column entirely.
        show_no = data['has_row_no']
        proj_c = self._CN_DATA_COL0            # 1 (B)
        no_c = proj_c + 1 if show_no else None
        val0 = (no_c + 1) if show_no else (proj_c + 1)
        last = val0 + ncol - 1
        # single forms reserve ONE trailing column past the last value column for
        # 表号+单位 (official geometry — R27, fixture-pinned).
        self._cn_xlsx_meta(ws, F, data, proj_c, last, last + 1)
        hr = self._CN_HEADER_ROW
        ws.write(hr, proj_c, '项目', F['hdr'])
        if show_no:
            ws.write(hr, no_c, '行次', F['hdr'])
            ws.set_column(no_c, no_c, 6)
        for i, h in enumerate(data['col_headers']):
            ws.write(hr, val0 + i, h, F['hdr'])
        ws.set_column(0, 0, 2)                 # blank column A
        ws.set_column(proj_c, proj_c, 46)
        ws.set_column(val0, last, 16)
        r = hr + 1
        for row in data['rows']:
            ws.write(r, proj_c, row['name'], F['name_b'] if row['is_header'] else F['name'])
            if show_no:
                ws.write(r, no_c, row['row_no'], F['no'])
            for i, v in enumerate(row['values']):
                self._cn_write_value(ws, r, val0 + i, v, F)
            r += 1
        rr = self._cn_xlsx_warning(ws, F, data, r + 1, last)
        self._cn_xlsx_signatures(ws, F, rr, last)

    def _cn_xlsx_two_column(self, ws, F, data):
        ncol = data['ncols']
        # A(0) blank | left block [项目 行次 vals] | right block [项目 行次 vals].
        # NO gap column between the two sides (R26-T1). block = 2 + ncol columns.
        block_w = 2 + ncol
        left_base = self._CN_DATA_COL0         # 1 (B)
        right_base = left_base + block_w       # 3+ncol (F when ncol=2)
        last = right_base + block_w - 1        # 4+2*ncol (I when ncol=2)
        self._cn_xlsx_meta(ws, F, data, left_base, right_base, last)
        hr = self._CN_HEADER_ROW

        def header_block(base, proj_header):
            ws.write(hr, base, proj_header, F['hdr'])       # 项目 (资产 / 负债权益)
            ws.write(hr, base + 1, '行次', F['hdr'])         # 行次 AFTER 项目
            for i, h in enumerate(data['col_headers']):
                ws.write(hr, base + 2 + i, h, F['hdr'])
        header_block(left_base, self._CN_BS_LEFT_HEADER)
        header_block(right_base, self._CN_BS_RIGHT_HEADER)
        ws.set_column(0, 0, 2)                 # blank column A
        ws.set_column(left_base, left_base, 30)
        ws.set_column(left_base + 1, left_base + 1, 6)
        ws.set_column(left_base + 2, left_base + 1 + ncol, 15)
        ws.set_column(right_base, right_base, 30)
        ws.set_column(right_base + 1, right_base + 1, 6)
        ws.set_column(right_base + 2, last, 15)

        left, right = data['left'], data['right']
        n = max(len(left), len(right))
        for i in range(n):
            r = hr + 1 + i
            if i < len(left):
                row = left[i]
                ws.write(r, left_base, row['name'], F['name_b'] if row['is_header'] else F['name'])
                ws.write(r, left_base + 1, row['row_no'], F['no'])
                for j, v in enumerate(row['values']):
                    self._cn_write_value(ws, r, left_base + 2 + j, v, F)
            else:
                for j in range(block_w):
                    ws.write_blank(r, left_base + j, None, F['empty'])
            if i < len(right):
                row = right[i]
                ws.write(r, right_base, row['name'], F['name_b'] if row['is_header'] else F['name'])
                ws.write(r, right_base + 1, row['row_no'], F['no'])
                for j, v in enumerate(row['values']):
                    self._cn_write_value(ws, r, right_base + 2 + j, v, F)
            else:
                for j in range(block_w):
                    ws.write_blank(r, right_base + j, None, F['empty'])
        rr = self._cn_xlsx_warning(ws, F, data, hr + 1 + n + 1, last)
        self._cn_xlsx_signatures(ws, F, rr, last)

    def _cn_xlsx_warning(self, ws, F, data, r, last):
        """Render the 表内勾稽 warning lines (if any) as merged red rows and return
        the next free row. Makes the self-check visible to the accountant in the
        file itself, not just the server log (R24 review / §7.0 铁律1)."""
        # crossfoot 差异 + 往来明细级口径声明 (both red, both travel with the file). The
        # dc_notice states only the 口径 FACT (审稿: no fix-how-to on the outbound file —
        # that lives in the log / wizard, R30-T2b, same as P2 第三类).
        msgs = self._cn_crossfoot_messages(data) + list(data.get('dc_notice') or [])
        for m in msgs:
            if last > 0:
                ws.merge_range(r, 0, r, last, m, F['warn'])
            else:
                ws.write(r, 0, m, F['warn'])
            r += 1
        if msgs:
            r += 1
        # 🔴 R48-T3：中式版式【不再渲染 footer_note】。二姐口径——取数口径说明对内审计可、
        # 【对外报送件(中式版式)撤下】,受众是税局/审计而非客户会计(惯例29 载体覆盖过头，
        # 与 R44 覆盖不足反向同源:没分清受众)。字段 statement_form.footer_note 保留(供他处),
        # 但本渲染路径不写它。改由 ASBE BS 工具栏「取数口径说明」独立导出件承载(受众=客户
        # 会计,主动索取),文案从通用披露行 account.report.line 直取、一字一致(判据4 钉住)。
        return r

    def _cn_xlsx_signatures(self, ws, F, r, last):
        ws.write(r, 0, '单位负责人：', F['sign'])
        ws.write(r, max(1, last // 2), '会计负责人：', F['sign'])
        ws.write(r, last, '制表人：', F['sign'])
