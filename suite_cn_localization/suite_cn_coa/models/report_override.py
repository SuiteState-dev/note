# -*- coding: utf-8 -*-
r"""官方 ASSBE 报表 formula 外科覆盖 + 卸载恢复台账 —— R33-A §4.10 / §4.9.2.

E-7 判定(Safi 拍): 星辰 chart 走国标编号 → 二选一(取数口径以我方 101 为准) →
把 l10n_cn 官方 ASSBE 报表里【照 Odoo 非国标编号建】的几条 account_codes 改成国标口径。

🔴 为什么是【Python 改字段 + 台账存原值】而不是 XML data 覆盖:
  Odoo 卸载【不回滚字段值】。被改的 account.report.expression / line 属 l10n_cn_reports,
  卸载器不碰 → 若走 XML data,我方写入的 '4001' 会【永久残留】,客户卸载后官方报表仍读
  我方口径且【看起来一切正常】,比科目被删更隐蔽(§4.9.2)。故:apply 时【先把原值存台账】,
  uninstall_hook 逐条写回。

五处覆盖(§4.10.3 定稿 + V6 逼出的第 5 处,verified live: 缺任一"摘 4001"处会破 30=53
差 6000,见 tests V6):
  1. BS 行11 在产品          1406 → 4001       (国标: 在产品=生产成本期末借方=存货, R30-P3/B-60)
  2. BS 行12 库存商品        +1406             (1406 发出商品仍属存货,行11 腾出后落这里)
  3. PL 行2 营业成本         40 → 40\(4001)    (把 4001 从营业成本摘掉,否则计入净利润)
  4. BS 往年未分配利润        - 4 → - 4\(4001)  (balance_domain;equity 的 -4 也扫 4001,不摘则
     (prev_year_earnings)                       资产移走但权益仍扣 → 破 30=53。V6 逼出,早先 grep 漏)
  5. BS 行26 研发费用        hide_if_zero=True (国标 ASSBE BS 无此行;1802 官方 cn 独有、星辰无)
     ⚠️ account.report.line 无 active 字段(19.0 实测),用 hide_if_zero;星辰无 1802 恒 0 → 恒隐藏。
  🔴 3+4 成对: 4001 从【损益(营业成本)】和【权益(往年未分配)】两处一起摘,才是"只当存货"的完整闭合。

🔴 R36-T1 缺陷#2 修复(拍板 status s-09 §8 第13项):本覆盖【只打官方 balance 一列】。
  前 3 条(行11/行12/PL营业成本)的年初列/本年累计列(bal_begin/ytd)是 suite_cn_statement
  自有 XML 记录(exp_253/254/129),不该由本模块跨模块覆盖 —— 它们在本覆盖执行后 1.148s 才
  由 statement 的 data 创建,_apply_all 遍历时尚不存在 ⇒ 【每次装机必漏且静默】(期末列读 4001、
  年初列仍读 1406,同表两列打架)。修法:statement 源头 XML 直接产出国标值(改产物即改源头,无
  独立生成器),本模块 labels 收到 ('balance',) 只覆盖官方那一列。故台账从 8 缩到 5(见下平表)。

🔴 R38-T1 阶段B 扩展(status s-11 拍板):ASBE(企业会计准则, cn_large_bis)侧同类存货口径
  backport。ASBE 原生把 生产成本 5001/制造费用 5101/劳务成本 5201 漏出存货口径(存货
  =140+142+145+147+1411 不含 5xxx)、却被营业成本 `5\(53)` 与往年未分配 裸前缀 `- 5` 双吃 →
  存货变负(B-69,R36-T4 实测 −6000)。同 ASSBE【三处成对摘】:存货加、营业成本摘、权益
  balance_domain 摘;官方原生 3 条进本表(#6/#7/#8),我方 bal_begin/ytd 2 条走 statement 源头
  XML。缺权益那处 → 资产0/权益−6000 破 30=53(阶段A逐组验证)。🔴 5401-5403 不做(建造合同
  净额列报,登记为已知偏离,解冻=建筑业客户+二姐判断);nonneg 断言(R37-T2)兜住其负存货。

🔴 刻意【不动】的两处(留字防下轮误判为漏改):
  * 行14 其他流动资产 排除表已含 1406 —— 新理由: 1406 现为发出商品、仍属存货、仍应从
    "其他流动资产"排除(结论同、理由变,防 §6.9 漂移)。
  * 行28 其他非流动资产 排除表留 1802 —— 1802 非国标 ASSBE 概念,星辰客户账上不会有,
    排不排都零影响;不动 = 少一处 override、少一条卸载要恢复的字段。
  * PL 41(制造费用)/44(工程施工) 仍在营业成本 —— 既有 B-60-lite,非本轮引入:4101 期末应
    结零、4401 在 ASSBE BS 无落点,刻意不动(§4.10 B-60-lite 留字)。

每条 formula 覆盖【钉住已知原值】:current==原值→套新值;current==新值→已套(幂等);
两者都不是→上游公式变了,【告警跳过不硬改】(自报警,防静默改坏)。
"""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# (line_xmlid, kind, expected_original, new_value, labels)
#   kind='formula' : 覆盖该 line 下 account_codes 表达式的 formula。
#       labels=('balance',) → 只覆盖官方原生的 balance 那一列(R36-T1 起,前 3 条都用此)。
#                     🔴 勿用 labels=None(=覆盖全部 account_codes,会连同 statement 自有的
#                     bal_begin/ytd 一起改)——那正是缺陷#2:那些列 statement 后创建、覆盖时不存在,
#                     静默漏。现由 statement 源头 XML 自产国标值,本模块不越界碰它们。
#       labels=(...) → 只覆盖指定 label 的表达式(用于一行有多条 account_codes、公式各异时)。
#   kind='hide_if_zero' : 置 line.hide_if_zero=True(expected/new/labels 忽略)
#
# 🔴 4001 双计连带(V6 实测钉死):要把 4001 生产成本【只当存货、不当损益/权益】,必须把它从
# 【全部会吃到它的 account_codes】里摘掉。ORM 全扫结果 = 两处:
#   (a) PL 行2 营业成本 balance/ytd 前缀 40 → 40\(4001)
#   (b) BS Previous Years Unallocated Earnings balance_domain 前缀 4 → 4\(4001)
# 只改 (a) 漏 (b) → V6 破 30=53 差 6000(equity 仍被 -4 扫入 4001)。(b) 是早先 grep 漏的
# (它是 <field name="formula"> 非 account_codes_formula 短标签),V6 测试把它逼出来。
_OV_BS = 'l10n_cn_reports.l10n_cn_assbe_bs_'
_OV_PL = 'l10n_cn_reports.l10n_cn_assbe_pl_'
# R38-T1 阶段B:ASBE(企业会计准则, cn_large_bis)侧存货口径 backport。行 xmlid 前缀是
# `asbe_`(单 s)、明细用 `cn_`,与 ASSBE 的 `assbe_`/`cns_` 不同(勿混)。
_OVB_BS = 'l10n_cn_reports.l10n_cn_asbe_bs_'
_OVB_PL = 'l10n_cn_reports.l10n_cn_asbe_pl_'
REPORT_OVERRIDES = [
    (_OV_BS + 'cns_wip', 'formula', '1406', '4001', ('balance',)),
    (_OV_BS + 'cns_inv', 'formula',
     '1401 + 1402 + 1404 + 1405 + 1407 + 1408 + 1421',
     '1401 + 1402 + 1404 + 1405 + 1406 + 1407 + 1408 + 1421', ('balance',)),
    (_OV_PL + 'cns_oc', 'formula',
     r'54\(5403) + 55 + 56\(5601, 5602, 5603) + 40 + 41 + 42 + 44',
     r'54\(5403) + 55 + 56\(5601, 5602, 5603) + 40\(4001) + 41 + 42 + 44', ('balance',)),
    (_OV_BS + 'cns_prev_year_earnings', 'formula',
     '- 4 - 50 - 51 - 52 - 53 - 54 - 55 - 56 - 57 - 58',
     r'- 4\(4001) - 50 - 51 - 52 - 53 - 54 - 55 - 56 - 57 - 58',
     ('balance_domain',)),
    (_OV_BS + 'cns_rdc', 'hide_if_zero', None, None, None),
    # —— R38-T1 阶段B:ASBE 侧【三处成对摘】(存货 + 营业成本 + 权益)。只做 5001/5101/5201
    #    (生产成本/制造费用/劳务成本);🔴 5401-5403 本轮不做(建造合同净额列报,登记为已知偏离)。
    #    缺任一处:只加存货不摘权益 balance_domain → 资产0/权益−6000 破 30=53(阶段A逐组验证)。
    (_OVB_BS + 'cn_inv', 'formula',
     '140 + 142 + 145 + 147 + 1411',
     '140 + 142 + 145 + 147 + 1411 + 5001 + 5101 + 5201', ('balance',)),
    (_OVB_PL + 'cn_oc', 'formula',
     r'64\(6403) + 5\(53)',
     r'64\(6403) + 5\(53, 5001, 5101, 5201)', ('balance',)),
    (_OVB_BS + 'cn_prev_year_earnings', 'formula',
     '- 5 - 60 - 61 - 62 - 63 - 64 - 65 - 66 - 67 - 68 - 69',
     r'- 5\(5001, 5101, 5201) - 60 - 61 - 62 - 63 - 64 - 65 - 66 - 67 - 68 - 69',
     ('balance_domain',)),
]

# 🔴 权威平表(R38-T1 阶段B 后 = 8 条:ASSBE 5 + ASBE 3;本模块只覆盖官方原生记录;我方
# bal_begin/ytd 共 4 条已回归 statement 源头 XML)。勿用乘法式计数——它隐含"每处成对"、把单
# 表达式排除在外,历史上已致两次漏(实现时 grep 漏→V6 抓;文档计数漏→R34-T1 抓)。数平表:
#   #  准则  表·行                       label          xmlid归属       原→新                本模块覆盖?
#   1  ASSBE BS行11 在产品 cns_wip        balance        无(官方原生)    1406→4001            ✅
#   2  ASSBE BS行12 库存 cns_inv          balance        无(官方原生)    +1406                ✅
#   3  ASSBE PL行2 营业成本 cns_oc        balance        无(官方原生)    40→40\(4001)         ✅
#   4  ASSBE BS往年未分配 cns_prev_year_earnings balance_domain 官方原生 -4→-4\(4001)         ✅
#   5  ASSBE BS行26 研发 cns_rdc          (line.hide_if_zero) 官方 line  False→True           ✅(hide)
#   6  ASBE  BS存货 cn_inv                balance        无(官方原生)    +5001+5101+5201      ✅ R38
#   7  ASBE  PL营业成本 cn_oc             balance        无(官方原生)    5\(53)→5\(53,5001..) ✅ R38
#   8  ASBE  BS往年未分配 cn_prev_year_earnings balance_domain 官方原生 -5→-5\(5001,5101,5201)✅ R38
#   ── 以下【不再由本模块覆盖】,已在 suite_cn_statement 源头 XML 写国标值(R36-T1 / R38-T1)──
#   -  ASSBE BS行11 cns_wip bal_begin      我方 exp_253_bal_begin        =4001               ❌ 源头自产
#   -  ASSBE BS行12 cns_inv bal_begin      我方 exp_254_bal_begin        含1406              ❌ 源头自产
#   -  ASSBE PL行2  cns_oc  ytd            我方 exp_129_ytd              =40\(4001)          ❌ 源头自产
#   -  ASBE  BS存货 cn_inv  bal_begin      我方 exp_177_bal_begin        +5001+5101+5201     ❌ 源头自产(R38)
#   -  ASBE  PL营业成本 cn_oc ytd          我方 exp_100_ytd              5\(53,5001..)       ❌ 源头自产(R38)
# #4/#8 年初列走官方原生 aggregation(bal_begin→balance→balance_domain,按列 date_scope 各自
# 重算),故单条 balance_domain 覆盖两列(V6b/V7b 坐实)。
# 卸载:本模块台账含官方 8 条 → _restore_all 只写回官方记录;我方 5 条是 statement 自有 XML,
# 随其模块卸载而消失,不存在"还原官方原值"的问题(R36-T1 改动5 / R38-T1)。


class CoaReportOverride(models.Model):
    _name = 'suite.cn.coa.report.override'
    _description = 'China COA — 官方报表 formula 覆盖恢复台账 (R33-A §4.9.2)'

    line_xmlid = fields.Char(string='报表行 xmlid', required=True, index=True)
    expr_label = fields.Char(
        string='表达式 label',
        help="formula 类覆盖按 label 定位(balance/bal_begin/ytd);hide_if_zero 类为空。")
    kind = fields.Selection(
        [('formula', 'formula'), ('hide_if_zero', 'hide_if_zero')],
        string='类型', required=True)
    original_value = fields.Char(
        string='原值',
        help="覆盖前的原始 formula 字符串,或 hide_if_zero 的原布尔('1'/'0')。"
             "uninstall_hook 逐条写回,还原官方报表。")

    _target_uniq = models.Constraint(
        'unique(line_xmlid, expr_label, kind)',
        '同一目标只登记一条原值。')

    # ------------------------------------------------------------------ apply
    @api.model
    def _apply_all(self):
        """套上覆盖。先存原值再改;幂等;上游变更则告警跳过。"""
        for line_xmlid, kind, expected, new, labels in REPORT_OVERRIDES:
            line = self.env.ref(line_xmlid, raise_if_not_found=False)
            if not line:
                _logger.warning('suite_cn_coa: 报表行 %s 不存在,跳过覆盖', line_xmlid)
                continue
            if kind == 'formula':
                exprs = line.expression_ids.filtered(
                    lambda e: e.engine == 'account_codes'
                    and (labels is None or e.label in labels))
                for expr in exprs:
                    self._apply_formula(line_xmlid, expr, expected, new)
            elif kind == 'hide_if_zero':
                self._apply_hide_if_zero(line_xmlid, line)
        # R37-T3 (b):装/升末尾自查覆盖是否真的生效 —— 刚 apply 完,正常恒空;非空 = apply 本身
        # 没套上(编码bug/意外),立刻 ERROR 不静默。fresh install 与带 migration 的 -u 都经此,
        # 故【不误报】。抓不到「-u 无 migration」漏放(那条路径本模块无代码运行)—— 那条靠 (a)
        # 只读方法随时手查 / server action,见 _check_overrides_effective 头注。
        self._assert_overrides_effective(origin='apply')

    def _apply_formula(self, line_xmlid, expr, expected, new):
        cur = expr.formula or ''
        if cur == new:
            return  # 已套(幂等)
        if cur != expected:
            # 🔴 T1 原值哨兵(R34):现公式既非基线(expected)、又非我方新值(new) → 官方在
            # patch/20.0 改了这条公式,基线常量已成历史文物。【不得覆盖该条】(否则套上后
            # uninstall 会把客户库写回一个官方已废弃的公式、且不报错=静默,与 F3/B-60 同类);
            # 改为 ERROR 级 + 登记「基线漂移」台账。是否整体中止安装留 Safi(本轮:跳过不中止)。
            _logger.error(
                'suite_cn_coa E7 基线漂移: %s[%s] 官方现公式 %r 既非基线 %r 亦非我方新值,'
                '【跳过该条不覆盖】。官方可能在 19.x patch / 20.0 改了此公式,基线常量待人工'
                '复核更新(V-1 自动化)。', line_xmlid, expr.label, cur, expected)
            self.env['suite.cn.coa.baseline.drift']._register_drift(
                line_xmlid, expr.label, expected, cur)
            return
        self._remember(line_xmlid, expr.label, 'formula', cur)
        expr.formula = new

    def _apply_hide_if_zero(self, line_xmlid, line):
        if line.hide_if_zero:
            return
        self._remember(line_xmlid, False, 'hide_if_zero',
                       '1' if line.hide_if_zero else '0')
        line.hide_if_zero = True

    def _remember(self, line_xmlid, label, kind, original):
        """只在首次存原值(re-run/官方 -u 后本值可能变,但台账保留【真原值】)。"""
        exists = self.search([
            ('line_xmlid', '=', line_xmlid),
            ('expr_label', '=', label or False),
            ('kind', '=', kind)], limit=1)
        if not exists:
            self.create({
                'line_xmlid': line_xmlid, 'expr_label': label or False,
                'kind': kind, 'original_value': original})

    # ---------------------------------------------------------------- restore
    @api.model
    def _restore_all(self):
        """卸载时逐条写回原值,还原官方报表(§4.9.2)。"""
        for rec in self.search([]):
            line = self.env.ref(rec.line_xmlid, raise_if_not_found=False)
            if not line:
                continue
            if rec.kind == 'formula':
                expr = line.expression_ids.filtered(
                    lambda e: e.engine == 'account_codes'
                    and e.label == rec.expr_label)[:1]
                if expr and rec.original_value is not False:
                    expr.formula = rec.original_value
            elif rec.kind == 'hide_if_zero':
                line.hide_if_zero = (rec.original_value == '1')
        self.search([]).unlink()

    # -------------------------------------------------- R37-T3 覆盖漏放自检
    @api.model
    def _check_overrides_effective(self):
        """(a) 只读自检,任意库可调(shell / server action *检查官方报表覆盖是否生效*)。

        逐条核 REPORT_OVERRIDES 是否【已生效】(current==new)。返回【未生效且非漂移】的
        清单 —— current 仍等于 expected(原值)即【漏放】签名:覆盖本该套上却没套(如某版改了
        这几条却忘带 migration → B-67 不重放)。current 既非 new 亦非 expected = 官方改了公式
        (漂移),归 E7 哨兵(_register_drift)管,不算漏放,排除。hide_if_zero 类:未生效 =
        line.hide_if_zero 仍为 False。

        🔴 这是 test_e7_baseline_drift(「官方原值没被改过」)缺的反向那半(「官方几条当前
        已是覆盖后的新值」),两条合起来才闭环。单测在 fresh install 上恒绿 —— 升级路径漏放
        只在【既有库】显形,故本方法【只读、任意库可调】是关键(不能只做成单测)。
        当前无存量库可验 ⇒ fresh 库上只能验【不误报】;真正抓漏放要等第一个客户装过、且我们
        发过第二个版本之后。"""
        missing = []
        for line_xmlid, kind, expected, new, labels in REPORT_OVERRIDES:
            line = self.env.ref(line_xmlid, raise_if_not_found=False)
            if not line:
                missing.append({'line_xmlid': line_xmlid, 'label': None,
                                'reason': 'line 不存在', 'current': None, 'want': new})
                continue
            if kind == 'formula':
                exprs = line.expression_ids.filtered(
                    lambda e: e.engine == 'account_codes'
                    and (labels is None or e.label in labels))
                for expr in exprs:
                    cur = expr.formula or ''
                    if cur == new:
                        continue                       # 已生效
                    if cur == expected:
                        missing.append({
                            'line_xmlid': line_xmlid, 'label': expr.label,
                            'reason': '漏放(仍为原值)', 'current': cur, 'want': new})
                    # else: 官方改了公式(漂移)→ E7 哨兵管,不计漏放
            elif kind == 'hide_if_zero':
                if not line.hide_if_zero:
                    missing.append({
                        'line_xmlid': line_xmlid, 'label': False,
                        'reason': 'hide_if_zero 漏放', 'current': 'False', 'want': 'True'})
        return missing

    @api.model
    def _assert_overrides_effective(self, origin='check'):
        """(b) 把 (a) 的清单转成【会自己叫的信号】:非空 → ERROR 日志 + 登记漂移台账
        (baseline='R37-T3 漏放:应为<new>', actual=<current 陈旧值>,与 E7 漂移同表,用户
        本就在看那张表)。返回清单(空=健康)。"""
        missing = self._check_overrides_effective()
        if missing:
            _logger.error(
                'suite_cn_coa R37-T3 覆盖漏放自检[%s]:%d 条官方报表覆盖【未生效】—— '
                '某版改了这几条却没重放(B-67),报表口径已错且静默。清单:%s',
                origin, len(missing), missing)
            Drift = self.env['suite.cn.coa.baseline.drift']
            for m in missing:
                Drift._register_drift(
                    m['line_xmlid'], m.get('label'),
                    'R37-T3 漏放:应为 %s' % m.get('want'),
                    '%s(%s)' % (m.get('current'), m['reason']))
        return missing


class CoaBaselineDrift(models.Model):
    _name = 'suite.cn.coa.baseline.drift'
    _description = 'China COA — E7 基线漂移登记 (R34 T1 原值哨兵)'

    line_xmlid = fields.Char(string='报表行 xmlid', required=True, index=True)
    expr_label = fields.Char(string='表达式 label')
    baseline = fields.Char(
        string='基线常量值', help="模块固化的已知官方原值(REPORT_OVERRIDES.expected)。")
    actual = fields.Char(
        string='官方实测值', help="安装/覆盖时读到的官方 account.report.expression.formula。"
                                  "与 baseline 不等 = 官方改了公式,基线常量成历史文物。")

    @api.model
    def _register_drift(self, line_xmlid, expr_label, baseline, actual):
        """登记一条基线漂移(幂等:同目标只留最新一条)。
        🔴 方法名勿用 `_register`——Odoo `models.Model._register` 是保留布尔属性(控制注册),
        撞名会 TypeError: 'bool' object is not callable。"""
        rec = self.search([
            ('line_xmlid', '=', line_xmlid),
            ('expr_label', '=', expr_label or False)], limit=1)
        vals = {'line_xmlid': line_xmlid, 'expr_label': expr_label or False,
                'baseline': baseline, 'actual': actual}
        if rec:
            rec.write(vals)
        else:
            self.create(vals)
        return True
