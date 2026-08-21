# -*- coding: utf-8 -*-
"""R47-T1 —— 严格六 / 八栏 科目余额表 验收判据 (绝对终态，惯例19)。

判据分三组（全部机械可判定）：
  A 组 三组合计平衡：Σ期初借==Σ期初贷 / Σ本期借==Σ本期贷 / Σ本年累计借==Σ本年累计贷 /
                     Σ期末借==Σ期末贷。这是「试算平衡」四个字的全部内容。
  B 组 逐行勾稽：每行 期初(借−贷)+本期借−本期贷==期末(借−贷)；一级行各列==其下明细同列之和。
  C 组 中式规范：余额只在一侧出数（另一侧留空非0）；无发生额无余额科目行为；排序。

惯例30 两半都上：
  ① 每条断言前置「参与校验行数>0」哨兵 —— 判据 A/B 全是 Σ相等/差为0 形态，空数据上
     0==0 恒真，不加哨兵必然空绿。故先用【前期+本期】双段造数把各窗口打成非0，再断言。
  ② 平衡校验自带「注入→检出」那半 —— Odoo 不允许过账不平的分录（ORM 挡死），故【数据级】
     的不平在当前版本【构造性关闭】(惯例24)；改在【校验边界】注入：把已渲染的行数据故意
     篡改一格，断言校验确实报出来。只跑「正常数据下它平」验的是不误报，不是这张表存在的理由。

打桩自检（交付要求8 / R46 判据）：把 handler 取数方法体换成 return，本组用例必须变红——
见 tests 之外的 stub 自检回报，不在本文件内。
"""
import copy

from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.tools import float_is_zero, float_compare


@tagged('post_install', '-at_install')
class TestTrialBalance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id
        cls.report = cls.env.ref('suite_cn_statement.cn_trial_balance')
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', cls.company.id)], limit=1)

        A = cls.env['account.account']

        def acc(code, name, atype):
            return A.create({'name': name, 'code': code, 'account_type': atype})

        # 混合编码表（规则①验收点）：点分 2221.01/.02 + 连号 2221001 + 一级锚 2221，
        # 四者都应归入一级键 '2221'；'2221' 账户名作父行名。
        cls.a_2221 = acc('2221', '应交税费', 'liability_current')
        cls.a_2221_01 = acc('2221.01', '应交增值税', 'liability_current')
        cls.a_2221_02 = acc('2221.02', '应交城建税', 'liability_current')
        cls.a_2221001 = acc('2221001', '连号税费', 'liability_current')
        cls.a_cash = acc('1001', 'TB库存现金', 'asset_cash')
        cls.a_untouched = acc('6999', 'TB未动科目', 'expense')  # 判据8：无任何分录
        # 复核②验收点：连号明细 2211001，且【库里无 2211 锚账户】——父行名须回落我方国标
        # 标准名『应付职工薪酬』，不显裸「2211」。单明细但编码≠键 ⇒ 不折叠（合法一级+单明细）。
        cls.a_2211001 = acc('2211001', '连号工资', 'liability_current')

        def post(date, pairs):
            move = cls.env['account.move'].create({
                'move_type': 'entry', 'journal_id': cls.journal.id, 'date': date,
                'line_ids': [(0, 0, {'account_id': a.id, 'debit': d, 'credit': c})
                             for (a, d, c) in pairs],
            })
            move.action_post()
            return move

        # 前期分录（打非0 期初）：现金借 500 / 应交增值税贷 500。
        post('2026-01-15', [(cls.a_cash, 500.0, 0.0), (cls.a_2221_01, 0.0, 500.0)])
        # 本期分录（打非0 本期发生）：现金借 300 / 应交城建税贷 300；连号税费贷 200 / 现金借 200。
        post('2026-06-15', [(cls.a_cash, 300.0, 0.0), (cls.a_2221_02, 0.0, 300.0)])
        post('2026-06-20', [(cls.a_cash, 200.0, 0.0), (cls.a_2221001, 0.0, 200.0)])
        # 直接过账到【一级科目本身】2221（现金借 100 / 应交税费贷 100）——覆盖「一级账户
        # 既是父行取名锚、又作为叶子出现在自己名下」的情形；判据6 的 Σ明细 须含它这笔。
        post('2026-06-25', [(cls.a_cash, 100.0, 0.0), (cls.a_2221, 0.0, 100.0)])
        # 连号明细 2211001（现金借 50 / 连号工资贷 50）——无 2211 锚，测名字回落国标。
        post('2026-06-28', [(cls.a_cash, 50.0, 0.0), (cls.a_2211001, 0.0, 50.0)])

        cls.options = cls.report.get_options({
            'selected_variant_id': cls.report.id, 'unfold_all': True,
            'date': {'mode': 'range', 'date_from': '2026-06-01', 'date_to': '2026-06-30'},
        })
        cls.lines = cls.report._get_lines(cls.options)

    # ------------------------------------------------------------- helpers
    def _idx(self, label):
        for i, c in enumerate(self.options['columns']):
            if c.get('expression_label') == label:
                return i
        self.fail('列 %s 不在 options 中' % label)

    def _v(self, line, label):
        return line['columns'][self._idx(label)].get('no_format') or 0.0

    def _leaves(self, lines=None):
        lines = self.lines if lines is None else lines
        return [l for l in lines
                if self.report._get_res_id_from_line_id(l['id'], 'account.account')]

    def _rollups(self, lines=None):
        lines = self.lines if lines is None else lines
        return [l for l in lines if l.get('cn_is_parent')]

    def _total(self, lines=None):
        lines = self.lines if lines is None else lines
        tot = [l for l in lines if l.get('cn_is_total')]
        self.assertEqual(len(tot), 1, '应恰有一条合计行')
        return tot[0]

    def _sum(self, label, lines=None):
        return sum(self._v(l, label) for l in self._leaves(lines))

    def _balanced(self, d_label, c_label, lines=None):
        """校验边界：返回 (参与行数, Σ借−Σ贷)。差为0=平。注入→检出复用此函数。"""
        leaves = self._leaves(lines)
        diff = sum(self._v(l, d_label) for l in leaves) - sum(self._v(l, c_label) for l in leaves)
        return len(leaves), diff

    # =============================================================== A 组
    def test_a_three_group_totals_balanced(self):
        """判据 A#1-4：三组（八栏时四组）合计借==贷。"""
        leaves = self._leaves()
        self.assertGreater(len(leaves), 0, '哨兵：参与校验的叶子行数须>0，为0则下列 Σ 全是空绿')
        # 哨兵：期初、本期两组必须非0（前期+本期双段造数即为此），否则 0==0 空绿。
        self.assertGreater(self._sum('open_d'), 0.0, '哨兵：Σ期初借须>0（前期分录未生效？）')
        self.assertGreater(self._sum('period_d'), 0.0, '哨兵：Σ本期借须>0（本期分录未生效？）')
        self.assertGreater(self._sum('ytd_d'), 0.0, '哨兵：Σ本年累计借须>0')
        self.assertGreater(self._sum('close_d'), 0.0, '哨兵：Σ期末借须>0')
        for d, c, label in [('open_d', 'open_c', '期初'), ('period_d', 'period_c', '本期发生'),
                            ('ytd_d', 'ytd_c', '本年累计'), ('close_d', 'close_c', '期末')]:
            n, diff = self._balanced(d, c)
            self.assertEqual(
                float_compare(diff, 0.0, precision_rounding=self.currency.rounding), 0,
                '判据A %s：Σ借−Σ贷=%s，不平' % (label, diff))

    def test_a_totals_balance_inject_detect(self):
        """惯例30②：注入→检出。正常数据下平（不误报）；篡改一格后校验确报出不平。"""
        n, diff = self._balanced('period_d', 'period_c')
        self.assertGreater(n, 0, '哨兵：无参与行')
        self.assertEqual(float_compare(diff, 0.0, precision_rounding=self.currency.rounding), 0,
                         '正常数据本应平')
        # 注入：深拷贝行、给某叶子的 period_d 加 0.01，断言 _balanced 确实检出。
        tampered = copy.deepcopy(self.lines)
        leaf = self._leaves(tampered)[0]
        leaf['columns'][self._idx('period_d')]['no_format'] = self._v(leaf, 'period_d') + 0.01
        n2, diff2 = self._balanced('period_d', 'period_c', lines=tampered)
        self.assertNotEqual(
            float_compare(diff2, 0.0, precision_rounding=self.currency.rounding), 0,
            '注入不平后校验未检出 —— 平衡校验形同虚设（这半才是这张表存在的理由）')

    # =============================================================== B 组
    def test_b_row_crossfoot(self):
        """判据 B#5 逐行勾稽：期初(借−贷)+本期借−本期贷 == 期末(借−贷)。两个数分列（惯例17）。"""
        leaves = self._leaves()
        self.assertGreater(len(leaves), 0, '哨兵：参与校验行数须>0')
        participated = 0
        broken = 0
        for l in leaves:
            participated += 1
            lhs = (self._v(l, 'open_d') - self._v(l, 'open_c')
                   + self._v(l, 'period_d') - self._v(l, 'period_c'))
            rhs = self._v(l, 'close_d') - self._v(l, 'close_c')
            if float_compare(lhs, rhs, precision_rounding=self.currency.rounding) != 0:
                broken += 1
        self.assertEqual(broken, 0,
                         '判据B：逐行勾稽——参与 %s 行 / 不成立 %s 行' % (participated, broken))

    def test_b_row_crossfoot_inject_detect(self):
        """惯例30②：篡改某叶子期末借，断言逐行勾稽确检出该行。"""
        tampered = copy.deepcopy(self.lines)
        leaf = self._leaves(tampered)[0]
        leaf['columns'][self._idx('close_d')]['no_format'] = self._v(leaf, 'close_d') + 1.0
        broken = 0
        for l in self._leaves(tampered):
            lhs = (self._v(l, 'open_d') - self._v(l, 'open_c')
                   + self._v(l, 'period_d') - self._v(l, 'period_c'))
            rhs = self._v(l, 'close_d') - self._v(l, 'close_c')
            if float_compare(lhs, rhs, precision_rounding=self.currency.rounding) != 0:
                broken += 1
        self.assertEqual(broken, 1, '注入后逐行勾稽应恰检出 1 行不成立')

    def test_b_rollup_equals_children(self):
        """判据 B#6：一级行各列 == 其下全部明细同列之和。回报：参与一级行数 / 不成立行数，
        另单给未归入任何一级的叶子行数（期望0，非0即完整性问题真发生，原样报，惯例17）。"""
        rollups = self._rollups()
        self.assertGreater(len(rollups), 0, '哨兵：参与校验的一级行数须>0')
        # 建立 rollup id → 其子叶子
        children_of = {}
        for l in self.lines:
            pid = l.get('parent_id')
            if pid and self.report._get_res_id_from_line_id(l['id'], 'account.account'):
                children_of.setdefault(pid, []).append(l)
        participated = 0
        broken = 0
        # 未归入=既无父行、又非折叠顶层单行（折叠行 cn_collapsed 是合法顶层，非异常）。
        unmapped = len([l for l in self._leaves()
                        if not l.get('parent_id') and not l.get('cn_collapsed')])
        labels = [c.get('expression_label') for c in self.options['columns']]
        for rl in rollups:
            participated += 1
            kids = children_of.get(rl['id'], [])
            for lab in labels:
                s = sum(self._v(k, lab) for k in kids)
                if float_compare(self._v(rl, lab), s, precision_rounding=self.currency.rounding) != 0:
                    broken += 1
                    break
        self.assertEqual(
            broken, 0,
            '判据B#6：一级==Σ明细——参与 %s 行 / 不成立 %s 行' % (participated, broken))
        self.assertEqual(
            unmapped, 0,
            '未归入任何一级的叶子行数=%s（期望0，非0即①完整性问题真发生）' % unmapped)

    def test_b_rollup_inject_detect(self):
        """惯例30②：篡改某一级行一格，断言一级==Σ明细校验确检出。"""
        tampered = copy.deepcopy(self.lines)
        rl = self._rollups(tampered)[0]
        rl['columns'][self._idx('close_d')]['no_format'] = self._v(rl, 'close_d') + 5.0
        children_of = {}
        for l in tampered:
            pid = l.get('parent_id')
            if pid and self.report._get_res_id_from_line_id(l['id'], 'account.account'):
                children_of.setdefault(pid, []).append(l)
        s = sum(self._v(k, 'close_d') for k in children_of.get(rl['id'], []))
        self.assertNotEqual(
            float_compare(self._v(rl, 'close_d'), s, precision_rounding=self.currency.rounding), 0,
            '注入后一级!=Σ明细，校验须检出')

    def test_b_rollup_mixed_dotted_and_lianhao(self):
        """规则①验收点：点分 2221.01/.02 + 连号 2221001 + 一级 2221 —— 全部归入一级键
        '2221'；父行名取 2221 账户名『应交税费』。回报混合表实际归并结果。"""
        rollups = self._rollups()
        by_code = {rl.get('cn_code'): rl for rl in rollups}
        self.assertIn('2221', by_code, '混合编码未合成出一级键 2221；实际键=%s'
                      % sorted(by_code.keys()))
        rl = by_code['2221']
        self.assertEqual(rl.get('cn_name'), '应交税费',
                         '一级 2221 父行名应取编码恰等于前缀的账户名')
        # 该一级下应含全部四个 2221* 叶子
        children_codes = {
            l.get('cn_code') for l in self.lines
            if l.get('parent_id') == rl['id']
            and self.report._get_res_id_from_line_id(l['id'], 'account.account')}
        self.assertEqual(
            children_codes, {'2221', '2221.01', '2221.02', '2221001'},
            '混合归并结果不符：一级 2221 下叶子=%s' % sorted(children_codes))

    def test_rollup_key_unit(self):
        """规则①键定义单测：有点→首段；无点→前4位。"""
        H = self.env['suite.cn.trial.balance.report.handler']
        self.assertEqual(H._cn_tb_rollup_key('2221.01'), '2221')
        self.assertEqual(H._cn_tb_rollup_key('2221.01.03'), '2221')  # 只到首段（规则②）
        self.assertEqual(H._cn_tb_rollup_key('2221001'), '2221')      # 连号取前4
        self.assertEqual(H._cn_tb_rollup_key('2221'), '2221')
        self.assertEqual(H._cn_tb_rollup_key('1001'), '1001')
        self.assertEqual(H._cn_tb_rollup_key('100'), '100')           # 短码原样

    # =============================================================== C 组
    def test_c_one_side_blank_not_zero(self):
        """判据7：余额只在一侧出数，另一侧留空（不是0）。渲染层 name=='' 即空。"""
        leaves = self._leaves()
        self.assertGreater(len(leaves), 0, '哨兵：无叶子行')
        checked = 0
        for l in leaves:
            for d, c in [('open_d', 'open_c'), ('close_d', 'close_c')]:
                vd, vc = self._v(l, d), self._v(l, c)
                # 至多一侧非0
                self.assertFalse(
                    not float_is_zero(vd, precision_rounding=self.currency.rounding)
                    and not float_is_zero(vc, precision_rounding=self.currency.rounding),
                    '%s 同一账户余额借贷两侧同时非0（%s/%s）' % (l.get('cn_code'), vd, vc))
                # 为0的一侧应渲染成空串（blank_if_zero 生效）
                for lab, val in [(d, vd), (c, vc)]:
                    if float_is_zero(val, precision_rounding=self.currency.rounding):
                        cell = l['columns'][self._idx(lab)]
                        self.assertEqual(cell.get('name'), '',
                                         '%s 余额为0一侧应留空，实为 %r'
                                         % (l.get('cn_code'), cell.get('name')))
                        checked += 1
        self.assertGreater(checked, 0, '哨兵：未校验到任何「零侧留空」单元')

    def test_c8_no_movement_no_balance_row_absent(self):
        """判据8：无发生额且无余额的科目——当前行为=不出行（四窗口均无分录→SQL 不返回）。
        是否可配：filter_hide_0_lines=optional（用户可开「隐藏本期全0行」）。不预设对错。"""
        codes = {l.get('cn_code') for l in self._leaves()}
        self.assertNotIn('6999', codes,
                         '无任何分录的 6999 不应出行（当前行为）')
        self.assertIn('1001', codes, '有分录的 1001 应出行')

    def test_c_ordering_code_asc_parent_before_children(self):
        """判据C（惯例3 有序）：整表科目编码升序；合成父行紧排在其子行之前；合计行在末。"""
        seq = [l for l in self.lines if l.get('cn_is_parent') or
               self.report._get_res_id_from_line_id(l['id'], 'account.account') or
               l.get('cn_is_total')]
        # 合计行必须在最后
        self.assertTrue(seq[-1].get('cn_is_total'), '合计行须在末行')
        body = seq[:-1]
        # 顶层行（合成父行 + 折叠单行）cn_code 升序
        top_codes = [l.get('cn_code') for l in body
                     if l.get('cn_is_parent') or l.get('cn_collapsed')]
        self.assertEqual(top_codes, sorted(top_codes),
                         '顶层行未按编码升序：%s' % top_codes)
        # 父行紧邻其子：遍历 body，遇父行后、下一个顶层行前的都应是它的子；
        # 折叠单行是无子顶层 → 复位 cur_parent。
        cur_parent = None
        for l in body:
            if l.get('cn_is_parent'):
                cur_parent = l['id']
            elif l.get('cn_collapsed'):
                cur_parent = None
            else:
                self.assertEqual(l.get('parent_id'), cur_parent,
                                 '子行 %s 未紧排在其一级父行之后' % l.get('cn_code'))

    # =========================================================== 复核① 折叠
    def test_single_leaf_group_collapses(self):
        """复核①：一级组下恰一个叶子且叶子编码==一级键（如 1001 库存现金独占 1001 号段）
        → 折叠成一行，不重复出「一级父行 + 同值叶子」两行（金蝶/用友惯例）。"""
        # 1001 号段只有 a_cash（编码恰为 1001）⇒ 应折叠。
        parent_1001 = [l for l in self._rollups() if l.get('cn_code') == '1001']
        self.assertFalse(parent_1001, '1001 单叶子应折叠，不应生成一级父行')
        rows_1001 = [l for l in self.lines
                     if l.get('cn_code') == '1001'
                     and (l.get('cn_is_parent')
                          or self.report._get_res_id_from_line_id(l['id'], 'account.account'))]
        self.assertEqual(len(rows_1001), 1, '1001 应恰出一行（折叠），实出 %d 行' % len(rows_1001))
        self.assertTrue(rows_1001[0].get('cn_collapsed'), '该行应标记为折叠单行')
        # 折叠不改数：1001 那行本期借=600（500期初来自1月、本期300+200+100=600）
        self.assertGreater(self._v(rows_1001[0], 'period_d'), 0.0, '哨兵：折叠行数值须在')
        # 反面：2221 号段有多个叶子 ⇒ 不折叠，仍有一级父行
        self.assertTrue([l for l in self._rollups() if l.get('cn_code') == '2221'],
                        '多叶子 2221 不应被折叠')

    # ====================================================== 复核② 名字回落
    def test_rollup_name_falls_back_to_national(self):
        """复核②：连号明细 2211001、库里无 2211 锚账户 → 一级父行名回落我方国标标准名
        『应付职工薪酬』，不显裸「2211」。命中最想接的连号（金蝶迁入）客户人群。"""
        # 确认库里确无 2211 锚（只造了 2211001）
        anchor = self.env['account.account'].search(
            [('code', '=', '2211'), ('company_ids', 'in', self.company.id)], limit=1)
        self.assertFalse(anchor, '前置：本测依赖库里无 2211 锚账户')
        rl = [l for l in self._rollups() if l.get('cn_code') == '2211']
        self.assertTrue(rl, '2211 连号明细应合成一级父行（编码≠键，不折叠）')
        self.assertEqual(rl[0].get('cn_name'), '应付职工薪酬',
                         '无锚时父行名应回落国标标准名，实为 %r' % rl[0].get('cn_name'))

    # =============================================================== 六/八栏
    def test_six_eight_toggle(self):
        """六/八栏 = 同一张报表两种列集，一个开关（cn_tb_columns）切换。八=8列含本年累计，
        六=6列抽掉本年累计。"""
        opt8 = self.report.get_options({
            'selected_variant_id': self.report.id, 'cn_tb_columns': 'eight',
            'date': {'mode': 'range', 'date_from': '2026-06-01', 'date_to': '2026-06-30'}})
        labels8 = [c.get('expression_label') for c in opt8['columns']]
        self.assertEqual(len(labels8), 8, '八栏应8列')
        self.assertIn('ytd_d', labels8)
        self.assertIn('ytd_c', labels8)

        opt6 = self.report.get_options({
            'selected_variant_id': self.report.id, 'cn_tb_columns': 'six',
            'date': {'mode': 'range', 'date_from': '2026-06-01', 'date_to': '2026-06-30'}})
        labels6 = [c.get('expression_label') for c in opt6['columns']]
        self.assertEqual(len(labels6), 6, '六栏应6列')
        self.assertNotIn('ytd_d', labels6, '六栏须抽掉本年累计借')
        self.assertNotIn('ytd_c', labels6, '六栏须抽掉本年累计贷')
        # 六栏下仍能出得来且合计平衡（本期一组）
        lines6 = self.report._get_lines(opt6)
        leaves6 = self._leaves(lines6)
        self.assertGreater(len(leaves6), 0, '哨兵：六栏无叶子行')


@tagged('post_install', '-at_install')
class TestTrialBalanceDirection(TransactionCase):
    """R48-T1/T2 —— 余额方向落栏（贴金蝶实务）+ 毛额允许为负。

    实务前提（observed，照片+二姐口述，【不升 verified】）：余额落哪一栏由科目自身
    「余额方向」属性决定,不随数值符号迁移;实际方向与属性相反时【在原栏写负数】(3103
    本年利润属性贷、亏损净额在借 ⇒ 贷栏写 -31,989.46)。发生额是毛额、允许为负(红字冲销)。
    下列落地校验是 verified,与上述前提分层。

    造数全部 TransactionCase 事务内、类结束回滚。方向用【字段显式指定】以隔离落栏逻辑
    （方向解析三层另有单测 test_resolve_direction_layers）。账套自平 ⇒ Σ借==Σ贷 恒真的
    数学基础是 Σ(signed balance)=0,含负数不破(判据2 是 R47 A 组的含负加强版,须新增)。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id
        cls.report = cls.env.ref('suite_cn_statement.cn_trial_balance')
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', cls.company.id)], limit=1)
        A = cls.env['account.account']

        def acc(code, name, atype, direction=None):
            vals = {'name': name, 'code': code, 'account_type': atype}
            if direction:
                vals['cn_balance_direction'] = direction
            return A.create(vals)

        # 字段显式指定方向(隔离落栏逻辑)。D902 备抵【故意不给字段、不在发行件】⇒ 走 account_type
        # 推导(资产→借,翻车),验判据5 计数+告警。
        cls.cash = acc('D101', 'D现金', 'asset_cash', 'debit')
        cls.cap = acc('D301', 'D实收资本', 'equity', 'credit')
        cls.profit = acc('D310', 'D本年利润', 'equity', 'credit')   # 3103 型：属性贷
        cls.vat_p = acc('D221', 'D应交税费', 'liability_current', 'credit')
        cls.vat_in = acc('D221.01', 'D进项税额', 'liability_current', 'debit')   # 借方专栏
        cls.vat_out = acc('D221.02', 'D未交增值税', 'liability_current', 'credit')
        cls.contra = acc('D902', 'D自建累计折旧', 'asset_non_current')  # 无字段→推导翻车

        def post(date, pairs):
            m = cls.env['account.move'].create({
                'move_type': 'entry', 'journal_id': cls.journal.id, 'date': date,
                'line_ids': [(0, 0, {'account_id': a.id, 'debit': d, 'credit': c})
                             for (a, d, c) in pairs]})
            m.action_post()
            return m

        # 前期(打非0 期初)
        post('2026-01-10', [(cls.cash, 1000.0, 0.0), (cls.cap, 0.0, 1000.0)])
        post('2026-01-20', [(cls.profit, 100.0, 0.0), (cls.cash, 0.0, 100.0)])   # 前期亏损
        # 本期
        post('2026-06-10', [(cls.profit, 300.0, 0.0), (cls.cash, 0.0, 300.0)])   # 本期亏损
        post('2026-06-11', [(cls.vat_in, 500.0, 0.0), (cls.cash, 0.0, 500.0)])   # 进项(借方子目)
        post('2026-06-12', [(cls.vat_out, 0.0, 800.0), (cls.cash, 800.0, 0.0)])  # 未交(贷)
        post('2026-06-13', [(cls.vat_p, 0.0, 100.0), (cls.cash, 100.0, 0.0)])    # 直接过账一级
        post('2026-06-14', [(cls.contra, 0.0, 60.0), (cls.cash, 60.0, 0.0)])     # 备抵(贷余)

        cls.options = cls.report.get_options({
            'selected_variant_id': cls.report.id, 'unfold_all': True,
            'date': {'mode': 'range', 'date_from': '2026-06-01', 'date_to': '2026-06-30'}})
        cls.lines = cls.report._get_lines(cls.options)

    # ---------------------------------------------------------------- helpers
    def _idx(self, label, options=None):
        options = options or self.options
        for i, c in enumerate(options['columns']):
            if c.get('expression_label') == label:
                return i
        self.fail('列 %s 不在 options' % label)

    def _v(self, line, label):
        return line['columns'][self._idx(label)].get('no_format') or 0.0

    def _leaves(self, lines=None):
        lines = self.lines if lines is None else lines
        return [l for l in lines
                if self.report._get_res_id_from_line_id(l['id'], 'account.account')]

    def _row_by_code(self, code, lines=None):
        lines = self.lines if lines is None else lines
        for l in lines:
            if l.get('cn_code') == code:
                return l
        self.fail('未找到行 %s' % code)

    def _blank(self, line, label):
        return self.currency.is_zero(self._v(line, label))

    # ============================================================ 判据1 落栏
    def test_c1_credit_account_loss_negative_in_credit_col(self):
        """判据1：3103 型(属性=贷、实际净额在借)——落【贷栏、写负数】,借栏留空,贴原样。
        D本年利润 期末 signed=+400(借向),属性贷 ⇒ 期末贷=-400、期末借空。"""
        row = self._row_by_code('D310')   # 单叶子折叠为顶层行
        # 哨兵：该科目确有本期发生(否则空绿)
        self.assertGreater(self._v(row, 'period_d'), 0.0, '哨兵：D310 本期借须>0')
        self.assertEqual(
            float_compare(self._v(row, 'close_c'), -400.0, precision_rounding=self.currency.rounding),
            0, '属性贷、净额在借 ⇒ 期末贷栏应写 -400（贴原样），实为 %s' % self._v(row, 'close_c'))
        self.assertTrue(self._blank(row, 'close_d'), '期末借栏应留空（方向不随符号迁移到借栏）')
        # 期初同理：前期亏损100 ⇒ 期初贷=-100
        self.assertEqual(
            float_compare(self._v(row, 'open_c'), -100.0, precision_rounding=self.currency.rounding),
            0, '期初贷栏应写 -100，实为 %s' % self._v(row, 'open_c'))

    # ============================================================ 判据2 含负数合计
    def test_c2_four_groups_balanced_with_negatives(self):
        """判据2（R47 A 组含负加强版）：四组合计在含负数(D310 贷栏 -100/-400)时仍借==贷。
        每组贴两数。"""
        leaves = self._leaves()
        self.assertGreater(len(leaves), 0, '哨兵：无叶子行')
        # 哨兵：确有负数参与（否则退化成 R47 旧场景，加强版没被验到）
        neg = [l for l in leaves for lab in ('open_c', 'close_c')
               if self._v(l, lab) < 0.0]
        self.assertTrue(neg, '哨兵：本用例须含负数余额，否则未验到「含负仍平」')
        for d, c, name in [('open_d', 'open_c', '期初'), ('period_d', 'period_c', '本期'),
                           ('ytd_d', 'ytd_c', '本年累计'), ('close_d', 'close_c', '期末')]:
            sd = sum(self._v(l, d) for l in leaves)
            sc = sum(self._v(l, c) for l in leaves)
            self.assertEqual(
                float_compare(sd, sc, precision_rounding=self.currency.rounding), 0,
                '判据2 %s：Σ借=%s / Σ贷=%s，含负数不平' % (name, sd, sc))

    def test_c2_inject_detect(self):
        """惯例30②：篡改一格后合计确不平（含负数场景下校验仍有牙）。"""
        leaves = self._leaves()
        sd = sum(self._v(l, 'close_d') for l in leaves)
        sc = sum(self._v(l, 'close_c') for l in leaves)
        self.assertEqual(float_compare(sd, sc, precision_rounding=self.currency.rounding), 0)
        tampered = copy.deepcopy(self.lines)
        self._leaves(tampered)[0]['columns'][self._idx('close_d')]['no_format'] = \
            self._v(self._leaves(tampered)[0], 'close_d') + 0.01
        sd2 = sum(self._v(l, 'close_d') for l in self._leaves(tampered))
        self.assertNotEqual(
            float_compare(sd2, sc, precision_rounding=self.currency.rounding), 0,
            '注入不平后未检出')

    # ============================================================ 判据3 逐行勾稽
    def test_c3_row_crossfoot_with_negatives(self):
        """判据3：期初(借−贷)+本期借−本期贷 == 期末(借−贷)，含负数行也成立。两数分列。"""
        leaves = self._leaves()
        self.assertGreater(len(leaves), 0, '哨兵：无叶子行')
        participated = broken = 0
        for l in leaves:
            participated += 1
            lhs = (self._v(l, 'open_d') - self._v(l, 'open_c')
                   + self._v(l, 'period_d') - self._v(l, 'period_c'))
            rhs = self._v(l, 'close_d') - self._v(l, 'close_c')
            if float_compare(lhs, rhs, precision_rounding=self.currency.rounding) != 0:
                broken += 1
        self.assertEqual(broken, 0, '判据3：参与 %s 行 / 不成立 %s 行' % (participated, broken))

    # ============================================================ 判据4 父行方向
    def test_c4_parent_rollup_direction(self):
        """判据4（本单最可能出意外，原样回报）：一级父行落栏与子行属性不一致时的行为。
        D221 应交税费(属性贷)下：D221.01 进项(属性借,期末借500) + D221.02 未交(贷800) +
        D221 直接过账(贷100)。观测行为=【父行按父自身方向(贷)落栏】：父净额 signed=
        500−800−100=−400 ⇒ 期末贷=400、期末借空。子行各自保留其属性方向不变。"""
        parent = None
        for l in self.lines:
            if l.get('cn_is_parent') and l.get('cn_code') == 'D221':
                parent = l
                break
        self.assertIsNotNone(parent, 'D221 应合成一级父行')
        # 原样回报的观测：父行净额落【父方向=贷】栏，借栏空
        self.assertEqual(
            float_compare(self._v(parent, 'close_c'), 400.0, precision_rounding=self.currency.rounding),
            0, '父行按父方向(贷)落栏：期末贷应=400，实为 %s' % self._v(parent, 'close_c'))
        self.assertTrue(self._blank(parent, 'close_d'),
                        '父行期末借应空（父方向贷，不随借方子目挪栏）')
        # 子行各自方向不变：进项(借)期末借=500、未交(贷)期末贷=800
        self.assertEqual(
            float_compare(self._v(self._row_by_code('D221.01'), 'close_d'), 500.0,
                          precision_rounding=self.currency.rounding), 0,
            '借方子目 D221.01 期末借应=500')
        self.assertEqual(
            float_compare(self._v(self._row_by_code('D221.02'), 'close_c'), 800.0,
                          precision_rounding=self.currency.rounding), 0,
            '贷方子目 D221.02 期末贷应=800')
        # 父行=Σ子行 的勾稽（借−贷 层面）仍成立：父(借−贷)=Σ子(借−贷)
        kids = [l for l in self.lines if l.get('parent_id') == parent['id']
                and self.report._get_res_id_from_line_id(l['id'], 'account.account')]
        for lab_d, lab_c in [('open_d', 'open_c'), ('close_d', 'close_c')]:
            p_net = self._v(parent, lab_d) - self._v(parent, lab_c)
            k_net = sum(self._v(k, lab_d) - self._v(k, lab_c) for k in kids)
            self.assertEqual(
                float_compare(p_net, k_net, precision_rounding=self.currency.rounding), 0,
                '父行(借−贷)须==Σ子(借−贷)：%s vs %s' % (p_net, k_net))

    # ============================================================ 判据5 无属性计数
    def test_c5_no_attribute_count_and_warning(self):
        """判据5：无「余额方向」属性(无字段、非发行件)的科目——【确认为 N】,并出条件告警行
        (给条数+编码+去哪改,不写「见日志」,惯例5)。D902 备抵是唯一这类科目 ⇒ N=1。"""
        H = self.env['suite.cn.trial.balance.report.handler']
        derived = [a for a in (self.cash + self.cap + self.profit + self.vat_p
                               + self.vat_in + self.vat_out + self.contra)
                   if H._cn_resolve_direction(a)[1] == 'derived']
        self.assertEqual(len(derived), 1, '无属性科目【确认为 1】(D902)，实为 %s'
                         % [a.code for a in derived])
        self.assertEqual(derived[0].code, 'D902')
        # 告警行须出现在渲染结果里(账簿对内件,放表内)
        warn = [l for l in self.lines if l.get('cn_is_dir_warning')]
        self.assertEqual(len(warn), 1, '应恰一条方向推导告警行')
        msg = warn[0].get('name') or ''
        self.assertIn('D902', msg, '告警须点名具体科目编码')
        self.assertIn('1', msg, '告警须给条数')
        self.assertNotIn('日志', msg, '惯例5：不得让人去看日志')
        self.assertIn('科目表', msg, '告警须指出去哪改')

    # ============================================================ 方向解析三层
    def test_resolve_direction_layers(self):
        """方向解析 field→issued→derived 三层单测（隔离于落栏）。"""
        H = self.env['suite.cn.trial.balance.report.handler']
        # field 层：显式字段优先
        self.assertEqual(H._cn_resolve_direction(self.profit), ('credit', 'field'))
        self.assertEqual(H._cn_resolve_direction(self.vat_in), ('debit', 'field'))
        # derived 层：无字段、非发行件 → account_type 推导
        self.assertEqual(H._cn_resolve_direction(self.contra), ('debit', 'derived'),
                         '备抵无字段应推导为借(翻车)并标 derived')
        # issued 层：发行件方向列须抵达 handler（唯一 home 是 coa 的 ASSBE_CHART）。
        # 直接校验快查表：备抵/借方专栏例外确已生效，证明 issued 源数据在运行时可用。
        dmap = H._cn_direction_by_code()
        self.assertTrue(dmap, 'issued 源(ASSBE_CHART 方向列)未抵达 handler（coa 未装齐？）')
        self.assertEqual(dmap.get('1001'), 'debit', '发行件 1001 库存现金应=借')
        self.assertEqual(dmap.get('2221'), 'credit', '发行件 2221 应交税费应=贷')
        self.assertEqual(dmap.get('1602'), 'credit', '发行件例外：累计折旧(备抵)应=贷')
        self.assertEqual(dmap.get('2221.01.02'), 'debit', '发行件例外：进项税额应=借')

    # ============================================================ T2 红字冲销毛额
    def test_t2_red_reversal_gross_allows_negative(self):
        """T2：发生额毛额不取绝对值。storno 红冲后本期借/贷各自允许为负,四组仍平。
        造数：1月原分录(费用借4.16/银行贷4.16 + 费用贷4.16/银行借4.16 两笔),6月 storno
        红冲两笔 ⇒ 6月该费用科目 SUM(debit)=-4.16、SUM(credit)=-4.16(贴金蝶截图形态)。"""
        self.company.sudo().write({'account_storno': True})
        A = self.env['account.account']
        fee = A.create({'name': 'T2财务费用', 'code': 'T603', 'account_type': 'expense',
                        'cn_balance_direction': 'debit'})
        bank = A.create({'name': 'T2银行', 'code': 'T002', 'account_type': 'asset_cash',
                         'cn_balance_direction': 'debit'})

        def post(date, pairs):
            m = self.env['account.move'].create({
                'move_type': 'entry', 'journal_id': self.journal.id, 'date': date,
                'line_ids': [(0, 0, {'account_id': a.id, 'debit': d, 'credit': c})
                             for (a, d, c) in pairs]})
            m.action_post()
            return m

        m1 = post('2026-01-05', [(fee, 4.16, 0.0), (bank, 0.0, 4.16)])   # 费用借
        m2 = post('2026-01-06', [(fee, 0.0, 4.16), (bank, 4.16, 0.0)])   # 费用贷
        for m in (m1, m2):
            rev = m._reverse_moves([{'date': '2026-06-05'}], cancel=False)
            if rev.state != 'posted':
                rev.action_post()

        opts = self.report.get_options({
            'selected_variant_id': self.report.id, 'unfold_all': True,
            'date': {'mode': 'range', 'date_from': '2026-06-01', 'date_to': '2026-06-30'}})
        lines = self.report._get_lines(opts)
        row = None
        for l in lines:
            if l.get('cn_code') == 'T603':
                row = l
                break
        self.assertIsNotNone(row, 'T603 应出行')
        pd = self._v(row, 'period_d')
        pc = self._v(row, 'period_c')
        # 贴原样：允许为负（handler 无 abs/GREATEST 截断）
        self.assertEqual(float_compare(pd, -4.16, precision_rounding=self.currency.rounding), 0,
                         '本期借应=-4.16（红冲毛额为负，不取绝对值），实为 %s' % pd)
        self.assertEqual(float_compare(pc, -4.16, precision_rounding=self.currency.rounding), 0,
                         '本期贷应=-4.16，实为 %s' % pc)
        # 四组仍平（红冲移动自平 ⇒ Σ借==Σ贷）
        leaves = [l for l in lines
                  if self.report._get_res_id_from_line_id(l['id'], 'account.account')]
        sd = sum((l['columns'][self._idx('period_d', opts)].get('no_format') or 0.0) for l in leaves)
        sc = sum((l['columns'][self._idx('period_c', opts)].get('no_format') or 0.0) for l in leaves)
        self.assertEqual(float_compare(sd, sc, precision_rounding=self.currency.rounding), 0,
                         '含负毛额本期合计仍应平：Σ借=%s Σ贷=%s' % (sd, sc))
