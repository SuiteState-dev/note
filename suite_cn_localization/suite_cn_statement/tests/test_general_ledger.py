# -*- coding: utf-8 -*-
"""R50-T1 —— 中式总分类账返工 验收判据（绝对终态，惯例19；计数类两数分列，惯例17）。

🔴 本单判据比 R49 强一档：有金蝶原件能验算，判据 2/4/5 是可拿原件数复算的机械判据。
规则锚 = 项目档 v42 §4.5.22（属性制，唯一归宿），R49 的 Q1-A 纯符号方向已作废。

判据（全部机械可判定）：
  1 期初余额行形态：借方/贷方栏均空，方向/余额有值（参与科目 / 不符）。
  2 本期合计行余额 == 上一已印期期末 ± 本期发生（按方向；signed 连续）（参与期次 / 不成立）。
  3 同期本年累计行余额 == 本期合计行余额（参与对数 / 不相等）。
  4 本年累计逐期滚动：本期本年累计(借/贷各自) == 上一已印期本年累计 + 本期合计（参与转移 / 不成立）。
  5 年初勾稽：年初 + Σ本年累计借 − Σ本年累计贷（借为正）== 本年累计行余额（参与科目 / 不成立）。
  6 方向栏取值：非零取属性、零取平。必含 ① 反向(3103 属性贷/实际借 ⇒ 方向贷/余额负)；
    ② 平(余额栏同时留空)。
  7 零值留空：应为 0 的金额栏渲染为空、不出 0.00（参与栏位 / 出现 0.00 条数，期望 0）。
  8 只出一级科目：明细科目作独立段条数【确认为 0】。
  9 与八栏余额表对账（本年累计借/贷）：参与科目 / 不一致。⚠️ 证据级 = 同源一致性检验
    （两表共用取数、构造必等），不是互证（H 条；draft-49 起措辞下调）。

惯例30 两半：① 每条断言前置正向哨兵（参与数>0）——判据 1-5/7-9 皆「相等/为零」形态，空数据
恒真；② 判据 2/4/5/7/9 属校验类，自带「注入→检出」——在校验边界篡改已算好的一格（造滚动断裂
/年初勾稽不平/0.00 泄漏/两表不一致），断言校验确实报出来。
打桩自检（交付要求8 / R46）：核心方法体换 return，对应用例变红——见 stub 自检回报，不在本文件内。
"""
import copy

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGeneralLedger(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.country_id = cls.env.ref('base.cn').id
        cls.currency = cls.company.currency_id
        cls.report = cls.env.ref('suite_cn_statement.cn_general_ledger')
        cls.handler = cls.env['suite.cn.general.ledger.report.handler']
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', cls.company.id)], limit=1)

        A = cls.env['account.account']

        def acc(code, name, atype):
            return A.create({'name': name, 'code': code, 'account_type': atype})

        cls.a_cash = acc('1001', 'GL库存现金', 'asset_cash')          # 属性借
        cls.a_ar = acc('1122', 'GL应收账款', 'asset_current')          # 属性借，造【平】
        cls.a_va = acc('2221.01', 'GL应交增值税', 'liability_current')  # 明细，归 2221（属性贷）
        cls.a_vb = acc('2221.02', 'GL应交城建税', 'liability_current')  # 明细，归 2221
        cls.a_profit = acc('3103', 'GL本年利润', 'equity')             # 属性贷，造借方余额(反向)
        cls.a_onlyopen = acc('1601', 'GL固定资产原价', 'asset_non_current')  # 只期初无发生额
        # R51-T2 夹具形态覆盖核：补「损益类年末结转→平」形态（ytd借==贷≠0、余额归零 —— 与
        # 1122「期初+冲回归零」是【平的另一成因、另一路径】）。结转承接入 3104 本年利润结转。
        cls.a_income = acc('6001', 'GL主营业务收入', 'income')          # 损益类，属性贷
        cls.a_carry = acc('3104', 'GL本年利润结转', 'equity')           # 结转承接

        def post(date, pairs):
            move = cls.env['account.move'].create({
                'move_type': 'entry', 'journal_id': cls.journal.id, 'date': date,
                'line_ids': [(0, 0, {'account_id': a.id, 'debit': d, 'credit': c})
                             for (a, d, c) in pairs],
            })
            move.action_post()
            return move

        # 上年（打期初，经 to_beginning_of_fiscalyear 进 2026）
        post('2025-06-30', [(cls.a_va, 0.0, 300.0), (cls.a_cash, 300.0, 0.0)])
        post('2025-12-31', [(cls.a_onlyopen, 1000.0, 0.0), (cls.a_cash, 0.0, 1000.0)])
        post('2025-12-31', [(cls.a_ar, 500.0, 0.0), (cls.a_cash, 0.0, 500.0)])
        # 本年多月（2221 三个月 → 判据2/4 逐期连续 + 注入有料）
        post('2026-01-15', [(cls.a_cash, 100.0, 0.0), (cls.a_va, 0.0, 100.0)])
        post('2026-03-10', [(cls.a_cash, 200.0, 0.0), (cls.a_vb, 0.0, 200.0)])
        # 6 月：2221.01 借 250；3103 借 500（属性贷/实际借 ⇒ 方向贷/余额负）；1122 贷 500（平）
        post('2026-06-20', [(cls.a_va, 250.0, 0.0), (cls.a_profit, 500.0, 0.0),
                            (cls.a_cash, 0.0, 750.0)])
        post('2026-06-20', [(cls.a_cash, 500.0, 0.0), (cls.a_ar, 0.0, 500.0)])
        # R51-T2：损益类年末结转 → 6001 期末平（ytd借==贷==1000、余额归零，成因≠1122）。
        post('2026-11-30', [(cls.a_income, 0.0, 1000.0), (cls.a_cash, 1000.0, 0.0)])  # 收入确认
        post('2026-12-31', [(cls.a_income, 1000.0, 0.0), (cls.a_carry, 0.0, 1000.0)])  # 结转本年利润

        cls.options = cls.report.get_options({
            'selected_variant_id': cls.report.id, 'unfold_all': True,
            'date': {'mode': 'range', 'date_from': '2026-01-01', 'date_to': '2026-12-31'},
        })
        cls.data = cls.handler._cn_gl_compute(cls.report, cls.options)

    # ------------------------------------------------------------- helpers
    def _sec(self, code, data=None):
        data = data or self.data
        for s in data['sections']:
            if s['code'] == code:
                return s
        self.fail('段 %s 不在结果中' % code)

    def _rounding(self):
        return self.currency.rounding

    # 判据1：期初余额行形态（借/贷栏空、方向/余额有值）。参与=期初非零段。
    def _opening_form(self, data):
        n = bad = 0
        for s in data['sections']:
            o = s['opening']
            if o['balance'] is None:          # 期初为平（0）——不入本判据参与集
                continue
            n += 1
            # 期初无发生额（借/贷栏空 by construction：opening 无 debit/credit）；方向/余额有值
            if not o['direction'] or o['balance'] is None:
                bad += 1
        return n, bad

    # 判据2：本期合计行余额（signed）== 上一已印期期末 ± 本期发生。参与=期次转移数。
    def _continuity(self, data):
        trans = breaks = 0
        for s in data['sections']:
            prev = s['opening']['signed']
            for p in s['periods']:
                trans += 1
                cu = p['current']
                if abs(cu['signed'] - (prev + cu['debit'] - cu['credit'])) > 0.005:
                    breaks += 1
                prev = cu['signed']
        return trans, breaks

    # 判据3：同期 本年累计行余额 == 本期合计行余额。参与=期次对数。
    def _ytd_equals_current(self, data):
        n = bad = 0
        for s in data['sections']:
            for p in s['periods']:
                n += 1
                if (p['ytd']['signed'] != p['current']['signed']
                        or p['ytd']['balance'] != p['current']['balance']):
                    bad += 1
        return n, bad

    # 判据4：本年累计逐期滚动（借/贷各自）。参与=期次转移数。
    def _ytd_rolling(self, data):
        trans = bad = 0
        for s in data['sections']:
            pd = pc = 0.0
            for p in s['periods']:
                trans += 1
                yt, cu = p['ytd'], p['current']
                if abs(yt['debit'] - (pd + cu['debit'])) > 0.005 \
                        or abs(yt['credit'] - (pc + cu['credit'])) > 0.005:
                    bad += 1
                pd, pc = yt['debit'], yt['credit']
        return trans, bad

    # 判据5：年初勾稽 年初 + Σ累计借 − Σ累计贷 == 本年累计行余额(signed)。参与=科目数。
    def _year_reconcile(self, data):
        n = bad = 0
        for s in data['sections']:
            n += 1
            t = s['total']
            if abs(s['opening']['signed'] + t['debit'] - t['credit'] - t['signed']) > 0.005:
                bad += 1
        return n, bad

    def _tb_ytd(self, code):
        tb = self.env.ref('suite_cn_statement.cn_trial_balance')
        opts = tb.get_options({
            'selected_variant_id': tb.id, 'unfold_all': True, 'cn_tb_columns': 'eight',
            'date': {'mode': 'range', 'date_from': '2026-01-01', 'date_to': '2026-12-31'}})
        lines = tb._get_lines(opts)
        idx = {c.get('expression_label'): i for i, c in enumerate(opts['columns'])}
        for l in lines:
            if l.get('cn_code') == code and (l.get('cn_is_parent') or l.get('cn_collapsed')):
                cols = l['columns']
                return (cols[idx['ytd_d']].get('no_format') or 0.0,
                        cols[idx['ytd_c']].get('no_format') or 0.0)
        return None

    # 判据9：GL 本年累计借/贷（毛额）vs 八栏 TB。同源一致性检验（非互证）。
    def _cross_check(self, data):
        n = bad = 0
        for s in data['sections']:
            tb = self._tb_ytd(s['code'])
            if tb is None:
                continue
            n += 1
            if abs(s['total']['debit'] - tb[0]) > 0.005 or abs(s['total']['credit'] - tb[1]) > 0.005:
                bad += 1
        return n, bad

    # =============================================================== 判据1
    def test_j1_opening_row_form(self):
        n, bad = self._opening_form(self.data)
        self.assertGreater(n, 0, '哨兵：期初非零段数须>0，否则空绿')
        self.assertEqual(bad, 0, '判据1：期初行 借/贷栏空、方向/余额有值（参与 %d / 不符 %d）' % (n, bad))
        # 期初非零段 by construction 无 debit/credit 键（渲染时借/贷栏空）
        o = self._sec('2221')['opening']
        self.assertEqual(o['direction'], '贷')
        self.assertIsNotNone(o['balance'])

    # =============================================================== 判据2
    def test_j2_current_balance_continuity(self):
        trans, breaks = self._continuity(self.data)
        self.assertGreater(trans, 0, '哨兵：参与期次转移数须>0')
        self.assertEqual(breaks, 0, '判据2：本期合计余额逐期连续（参与 %d / 不成立 %d）' % (trans, breaks))
        self.assertGreaterEqual(len(self._sec('2221')['periods']), 3, '2221 应有≥3 个期')

    def test_j2_continuity_inject_detect(self):
        tampered = copy.deepcopy(self.data)
        sec = next(s for s in tampered['sections'] if s['code'] == '2221')
        sec['periods'][1]['current']['signed'] += 999.0
        trans, breaks = self._continuity(tampered)
        self.assertGreaterEqual(breaks, 1, '🔴 连续性校验未检出注入的断期')

    # =============================================================== 判据3
    def test_j3_ytd_equals_current_balance(self):
        n, bad = self._ytd_equals_current(self.data)
        self.assertGreater(n, 0, '哨兵：参与期次对数须>0')
        self.assertEqual(bad, 0, '判据3：本年累计行余额==本期合计行余额（参与 %d / 不相等 %d）' % (n, bad))

    # =============================================================== 判据4
    def test_j4_ytd_rolling(self):
        trans, bad = self._ytd_rolling(self.data)
        self.assertGreater(trans, 0, '哨兵：参与转移数须>0')
        self.assertEqual(bad, 0, '判据4：本年累计逐期滚动（参与 %d / 不成立 %d）' % (trans, bad))

    def test_j4_ytd_rolling_inject_detect(self):
        tampered = copy.deepcopy(self.data)
        sec = next(s for s in tampered['sections'] if s['code'] == '2221')
        sec['periods'][2]['ytd']['debit'] += 77.0
        trans, bad = self._ytd_rolling(tampered)
        self.assertGreaterEqual(bad, 1, '🔴 逐期滚动校验未检出注入的累计断裂')

    # =============================================================== 判据5
    def test_j5_year_reconcile(self):
        n, bad = self._year_reconcile(self.data)
        self.assertGreater(n, 0, '哨兵：参与科目数须>0')
        self.assertEqual(bad, 0, '判据5：年初勾稽（参与 %d / 不成立 %d）' % (n, bad))

    def test_j5_year_reconcile_inject_detect(self):
        tampered = copy.deepcopy(self.data)
        tampered['sections'][0]['total']['debit'] += 500.0
        n, bad = self._year_reconcile(tampered)
        self.assertGreaterEqual(bad, 1, '🔴 年初勾稽校验未检出注入的不平')

    # =============================================================== 判据6
    def test_j6_direction_attribute_incl_reversal_and_ping(self):
        """方向=属性（非零）/平（零）。① 反向：3103 属性贷、6月造借方余额 ⇒ 方向贷、余额【负】。"""
        profit = self._sec('3103')
        self.assertEqual(profit['total']['direction'], '贷',
                         '🔴 反向：属性贷科目实际借方余额，方向仍取属性「贷」（不随符号迁移）')
        self.assertLess(profit['total']['balance'], 0, '🔴 反向：余额须为负（实际方向与属性相反）')
        # 2221 贷方余额 ⇒ 方向贷、余额正
        self.assertEqual(self._sec('2221')['total']['direction'], '贷')
        self.assertGreater(self._sec('2221')['total']['balance'], 0)
        # ② 平：1122 期末归零 ⇒ 方向平、余额栏 None（留空）
        ar = self._sec('1122')
        self.assertEqual(ar['total']['direction'], '平', '🔴 平：期末零余额方向须为「平」')
        self.assertIsNone(ar['total']['balance'], '🔴 平：余额栏须留空（None）')

    def test_j6_dir_bal_unit(self):
        """_cn_gl_dir_bal 单测（打桩即红）：属性定向、余额带符号、0→平/None。"""
        f = self.handler._cn_gl_dir_bal
        cur = self.currency
        self.assertEqual(f(300.0, 'debit', cur), ('借', 300.0))
        self.assertEqual(f(-300.0, 'debit', cur), ('借', -300.0))   # 属性借/实际贷 ⇒ 余额负
        self.assertEqual(f(300.0, 'credit', cur), ('贷', -300.0))   # 属性贷/实际借 ⇒ 余额负
        self.assertEqual(f(-300.0, 'credit', cur), ('贷', 300.0))
        self.assertEqual(f(0.0, 'debit', cur), ('平', None))
        self.assertEqual(f(0.0, 'credit', cur), ('平', None))

    # =============================================================== 判据7
    def _zero_cells_in_data(self, data):
        """参与栏位数 = 数据里应为 0 的发生额栏位（本期/本年累计的 debit/credit == 0）。"""
        n = 0
        for s in data['sections']:
            for p in s['periods']:
                for blk in ('current', 'ytd'):
                    for k in ('debit', 'credit'):
                        if abs(p[blk][k]) < 1e-9:
                            n += 1
        return n

    def _render_and_capture(self, data_override=None):
        data = data_override or self.report._cn_gl_prepare(self.options)
        rec = _RecWS()
        keys = ['title', 'meta', 'meta_r', 'hdr', 'acct', 'no', 'name', 'name_b',
                'num', 'num_b', 'empty', 'sign', 'note']
        F = {k: object() for k in keys}
        self.report._cn_xlsx_gl(rec, F, data)
        return rec

    def test_j7_zero_blank_no_double_zero(self):
        participate = self._zero_cells_in_data(self.data)
        self.assertGreater(participate, 0, '哨兵：应为 0 的发生额栏位须>0（否则判据空测）')
        rec = self._render_and_capture()
        leaked = sum(1 for v in rec.numbers if abs(v) < 1e-9)
        self.assertEqual(leaked, 0,
                         '判据7：零值须渲染为空（参与 %d / 出现 0.00 条数 %d，期望 0）'
                         % (participate, leaked))

    def test_j7_zero_leak_inject_detect(self):
        """注入→检出：手动往数字流写一个 0.0，断言检测器报出泄漏。"""
        rec = _RecWS()
        rec.write_number(0, 0, 0.0, None)
        leaked = sum(1 for v in rec.numbers if abs(v) < 1e-9)
        self.assertGreaterEqual(leaked, 1, '🔴 0.00 泄漏检测器未检出注入的零值')

    # =============================================================== 判据8
    def test_j8_only_level1_accounts(self):
        self.assertEqual(self.data['detail_leak'], 0,
                         '判据8：明细科目作独立段的条数须【确认为 0】')
        codes = [s['code'] for s in self.data['sections']]
        self.assertIn('2221', codes, '一级键 2221 应成段')
        self.assertNotIn('2221.01', codes, '明细 2221.01 不应作独立段')
        self.assertNotIn('2221.02', codes, '明细 2221.02 不应作独立段')

    # =============================================================== 判据9
    def test_j9_cross_check_same_source(self):
        n, bad = self._cross_check(self.data)
        self.assertGreater(n, 0, '哨兵：交叉对账参与科目数须>0')
        self.assertEqual(bad, 0,
                         '🔴 判据9：GL 本年累计借/贷 与八栏余额表不一致（参与 %d / 不一致 %d）'
                         '——同源一致性检验，不一致即立即停下' % (n, bad))

    def test_j9_cross_check_inject_detect(self):
        tampered = copy.deepcopy(self.data)
        tampered['sections'][0]['total']['debit'] += 123.0
        n, bad = self._cross_check(tampered)
        self.assertGreaterEqual(bad, 1, '🔴 交叉对账未检出注入的两表不一致')

    # =============================================================== Q2 edge
    def test_q2_only_opening_account_emits_section(self):
        self.assertGreaterEqual(self.data['only_opening_count'], 1,
                                'Q2 edge：只期初无发生额科目数须≥1（1601）')
        sec = self._sec('1601')
        self.assertEqual(len(sec['periods']), 0, '1601 本年无发生额 ⇒ 无期行')
        self.assertIsNotNone(sec['opening']['balance'], '1601 应有期初余额')
        self.assertEqual(sec['total']['debit'], 0.0, '累计借应为 0')
        self.assertEqual(sec['total']['credit'], 0.0, '累计贷应为 0')

    def test_q2_all_empty_account_absent(self):
        empty = self.env['account.account'].create(
            {'name': 'GL纯空', 'code': '6999', 'account_type': 'expense'})
        data = self.handler._cn_gl_compute(self.report, self.options)
        self.assertNotIn('6999', [s['code'] for s in data['sections']],
                         '无期初无发生额科目不应出段')
        self.assertTrue(empty.exists())

    # =============================================================== 渲染两路径
    def test_screen_lines_structure(self):
        lines = self.report._get_lines(self.options)
        self.assertGreater(len(lines), 0, '哨兵：屏幕行须>0')
        names = [l.get('name') for l in lines]
        self.assertTrue(any(n and n.startswith('2221 ') for n in names), '应有 2221 段头')
        self.assertTrue(any('期初余额' in (n or '') for n in names))
        self.assertTrue(any('本期合计' in (n or '') for n in names), '应有本期合计行')
        self.assertTrue(any('本年累计' in (n or '') for n in names))
        self.assertFalse(any((n or '').startswith('Total ') for n in names),
                         '🔴 不应出现框架 totals_below_sections 噪声合计行')

    def test_cn_xlsx_gl_render(self):
        data = self.report._cn_gl_prepare(self.options)
        rec = self._render_and_capture(data)
        joined = '\n'.join(t for t in rec.texts if isinstance(t, str))
        self.assertIn('总分类账', joined, '表名须在')
        self.assertIn('2221', joined, '科目编码须在')
        self.assertIn('科目编码', joined, '编码列头须在（R50-D 两列）')
        self.assertIn('本期合计', joined, '本期合计行须在')
        self.assertIn('本年累计', joined, '本年累计行须在')
        self.assertIn('贷', rec.texts, '方向标签须写入（2221/3103 属性贷）')
        self.assertIn('口径一致', joined, '口径提示（与 TB 一致）须在表内（R50 订正措辞）')
        self.assertNotIn('表现不同', joined, '🔴 R49 旧口径「表现不同」措辞须撤下')

    # =============================================== R51-T2 夹具形态覆盖核
    def test_t2_form_coverage(self):
        """六类形态逐类【有】——科目个数是结果不是目标（惯例17，参与数从实际输出誊抄）。
          1 反向（属性≠实际余额方向）：1001（借属性/贷余额）+ 3103（贷属性/借余额），双向都有。
          2 平（零余额→方向平、余额空）：1122（期初+冲回归零）。
          3 只期初、全年无发生额：1601。
          4 损益类年末结转→平（ytd借==贷≠0、余额归零，成因≠2）：6001。
          5 有子目的父科目 roll-up 到一级：2221（子目 2221.01/.02）。
          6 跨年期初进来（走 to_beginning_of_fiscalyear）：1001/1122/1601/2221。"""
        secs = {s['code']: s for s in self.data['sections']}
        # 1 反向 双向
        rev = [c for c, s in secs.items()
               if (s['attr'] == 'credit' and s['total']['signed'] > 0.005)
               or (s['attr'] == 'debit' and s['total']['signed'] < -0.005)]
        self.assertIn('3103', rev, '形态1 反向(贷属性/借余额) 须有 3103')
        self.assertIn('1001', rev, '形态1 反向(借属性/贷余额) 须有 1001')
        # 2 平（零余额）
        self.assertIsNone(secs['1122']['total']['balance'], '形态2 平 须有 1122')
        # 3 只期初
        self.assertEqual(len(secs['1601']['periods']), 0, '形态3 只期初 须有 1601')
        # 4 损益结转→平
        t6001 = secs['6001']['total']
        self.assertIsNone(t6001['balance'], '形态4 损益结转→平 须有 6001（余额归零）')
        self.assertAlmostEqual(t6001['debit'], t6001['credit'], places=2,
                               msg='形态4：ytd 借==贷')
        self.assertGreater(t6001['debit'], 0, '形态4：ytd 借==贷≠0（与 1122 不同成因）')
        # 5 父科目 roll-up
        self.assertIn('2221', secs, '形态5 父科目 roll-up 须有 2221')
        self.assertNotIn('2221.01', secs, '形态5：子目不作独立段（已 roll-up）')
        # 6 跨年期初
        crossyear = [c for c, s in secs.items() if s['opening']['balance'] is not None]
        self.assertTrue({'1001', '1122', '1601', '2221'} <= set(crossyear),
                        '形态6 跨年期初 须含 1001/1122/1601/2221')


class _RecWS:
    """记录式假 worksheet：捕获文本与数字写入，供渲染/零值泄漏断言。"""
    def __init__(self):
        self.texts = []
        self.numbers = []

    def write(self, r, c, val, fmt=None):
        self.texts.append(val)

    def write_number(self, r, c, val, fmt=None):
        self.numbers.append(val)

    def write_blank(self, r, c, val, fmt=None):
        pass

    def merge_range(self, r0, c0, r1, c1, val, fmt=None):
        self.texts.append(val)

    def set_column(self, *a, **k):
        pass

    def set_row(self, *a, **k):
        pass

    def set_footer(self, *a, **k):
        pass
