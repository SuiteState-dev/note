# -*- coding: utf-8 -*-
from datetime import date

from odoo import Command
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestCnVoucher(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data_2 = cls.setup_other_company()
        cls.company = cls.company_data['company']
        cls.journal = cls.company_data['default_journal_misc']
        cls.acc_a = cls.company_data['default_account_revenue']
        cls.acc_b = cls.company_data['default_account_expense']

    def _mk_move(self, on_date, word='general', amount=100.0, company=None, journal=None,
                 acc_a=None, acc_b=None):
        return self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': (journal or self.journal).id,
            'date': on_date,
            'company_id': (company or self.company).id,
            'l10n_cn_voucher_word': word,
            'line_ids': [
                Command.create({'account_id': (acc_a or self.acc_a).id, 'balance': amount, 'name': 't'}),
                Command.create({'account_id': (acc_b or self.acc_b).id, 'balance': -amount, 'name': 't'}),
            ],
        })

    # —— T1-2 取号四态 ——
    def test_number_assigned_on_post_only(self):
        move = self._mk_move(date(2026, 6, 1))
        self.assertFalse(move.l10n_cn_voucher_number, "草稿不给号")
        move.action_post()
        self.assertEqual(move.l10n_cn_voucher_number, 1, "过账才给号，首号=1")
        self.assertEqual(move.l10n_cn_voucher_display, '记-1')

    def test_sequential_same_month(self):
        m1 = self._mk_move(date(2026, 6, 1)); m1.action_post()
        m2 = self._mk_move(date(2026, 6, 20)); m2.action_post()
        self.assertEqual([m1.l10n_cn_voucher_number, m2.l10n_cn_voucher_number], [1, 2])

    def test_reset_per_month(self):
        m_jun = self._mk_move(date(2026, 6, 15)); m_jun.action_post()
        m_jul = self._mk_move(date(2026, 7, 1)); m_jul.action_post()
        self.assertEqual(m_jun.l10n_cn_voucher_number, 1)
        self.assertEqual(m_jul.l10n_cn_voucher_number, 1, "跨会计期间（月）归零")

    def test_word_separates_sequence(self):
        m_gen = self._mk_move(date(2026, 6, 1), word='general'); m_gen.action_post()
        m_trf = self._mk_move(date(2026, 6, 1), word='transfer'); m_trf.action_post()
        self.assertEqual(m_gen.l10n_cn_voucher_number, 1)
        self.assertEqual(m_trf.l10n_cn_voucher_number, 1, "凭证字各自独立取号")
        self.assertEqual(m_trf.l10n_cn_voucher_display, '转账-1')

    def test_draft_keeps_number(self):
        move = self._mk_move(date(2026, 6, 1)); move.action_post()
        self.assertEqual(move.l10n_cn_voucher_number, 1)
        move.button_draft()
        self.assertEqual(move.l10n_cn_voucher_number, 1, "作废/草稿号永久保留、跳号不释放")

    def test_reverse_gets_new_number(self):
        move = self._mk_move(date(2026, 6, 1)); move.action_post()
        self.assertEqual(move.l10n_cn_voucher_number, 1)
        rev = move._reverse_moves([{'date': date(2026, 6, 2)}])
        rev.action_post()
        self.assertEqual(rev.l10n_cn_voucher_number, 2, "红冲另编新号、不复用原号")

    def test_delete_leaves_gap_not_reused(self):
        m1 = self._mk_move(date(2026, 6, 1)); m1.action_post()   # 1
        m2 = self._mk_move(date(2026, 6, 2)); m2.action_post()   # 2
        m1.button_draft(); m1.unlink()                           # 删除 1 → 断号
        m3 = self._mk_move(date(2026, 6, 3)); m3.action_post()   # 3（不复用 1）
        self.assertEqual([m2.l10n_cn_voucher_number, m3.l10n_cn_voucher_number], [2, 3])

    # —— T1-3 一级—明细科目串 ——
    def test_account_path_dotted_and_fallback(self):
        parent = self.env['account.account'].create({
            'code': '2221', 'name': '应交税费', 'account_type': 'liability_current',
            'company_ids': [Command.link(self.company.id)]})
        child = self.env['account.account'].create({
            'code': '2221.01', 'name': '应交增值税', 'account_type': 'liability_current',
            'company_ids': [Command.link(self.company.id)]})
        move = self._mk_move(date(2026, 6, 1), acc_a=child)
        move.action_post()
        child_line = move.line_ids.filtered(lambda l: l.account_id == child)
        self.assertEqual(move._l10n_cn_account_path(child_line), '应交税费 / 应交增值税',
                         "点分编码截首点取一级、拼明细")
        flat_line = move.line_ids.filtered(lambda l: l.account_id == self.acc_b)
        # 扁平账户无点分 → 回退打全名，不报错不猜
        self.assertEqual(move._l10n_cn_account_path(flat_line), self.acc_b.display_name)

    def test_account_path_serial_tiers(self):
        """R34 三档:连号编码取前4位一级(档2),前4位须真实存在(边界),否则落全名(档3)。"""
        A = self.env['account.account']
        # 一级 4 位(R33-A 我方发行件结构)
        lv1 = A.create({'code': '2221', 'name': '应交税费',
                        'account_type': 'liability_current',
                        'company_ids': [Command.link(self.company.id)]})
        # 三级 10 位连号(无点), code[:4]='2221' 真实存在 → 档2 截一级
        lv3 = A.create({'code': '2221001001', 'name': '进项税额',
                        'account_type': 'liability_current',
                        'company_ids': [Command.link(self.company.id)]})
        m1 = self._mk_move(date(2026, 6, 1), acc_a=lv3)
        m1.action_post()
        line3 = m1.line_ids.filtered(lambda l: l.account_id == lv3)
        self.assertEqual(m1._l10n_cn_account_path(line3), '应交税费 / 进项税额',
                         "档2:连号三级 code[:4]=2221 存在 → 一级/明细")
        # 边界:连号明细但 code[:4] 无对应一级科目 → 落档3 全名(不猜)
        orphan = A.create({'code': '9988001', 'name': '孤儿明细',
                           'account_type': 'liability_current',
                           'company_ids': [Command.link(self.company.id)]})
        m2 = self._mk_move(date(2026, 6, 1), acc_a=orphan)
        m2.action_post()
        lo = m2.line_ids.filtered(lambda l: l.account_id == orphan)
        self.assertEqual(m2._l10n_cn_account_path(lo), orphan.display_name,
                         "档2边界:code[:4]=9988 不存在 → 落档3 全名,不违 R28-T2-7")
        # 档3:一级科目自身(len=4)不截,打全名
        m3 = self._mk_move(date(2026, 6, 1), acc_a=lv1)
        m3.action_post()
        l1 = m3.line_ids.filtered(lambda l: l.account_id == lv1)
        self.assertEqual(m3._l10n_cn_account_path(l1), lv1.display_name,
                         "档3:一级 4 位不满足 len>4 → 全名")

    # —— T2-c 缺陷#8 官方明细名自带父名前缀 → 剥除(防重复 + 防误剥)——
    def test_t2c_account_path_strip_parent_prefix(self):
        """官方明细名「应交税费 - 应交增值税（销项税额）」拼「一级/明细」会重复成
        「应交税费 / 应交税费 - …」→ 剥除父名+分隔符前缀。仅官方点分科目触发(带前缀);
        我方短名不触发。防误剥:父名恰为明细名前缀但【无分隔符】⇒ 不剥(语义不同)。"""
        A = self.env['account.account']
        A.create({'code': '2221', 'name': '应交税费',
                  'account_type': 'liability_current',
                  'company_ids': [Command.link(self.company.id)]})
        # (1) 官方带前缀 → 剥
        official = A.create({
            'code': '2221.01.01', 'name': '应交税费 - 应交增值税（销项税额）',
            'account_type': 'liability_current',
            'company_ids': [Command.link(self.company.id)]})
        m1 = self._mk_move(date(2026, 6, 1), acc_a=official); m1.action_post()
        l1 = m1.line_ids.filtered(lambda l: l.account_id == official)
        self.assertEqual(m1._l10n_cn_account_path(l1), '应交税费 / 应交增值税（销项税额）',
                         'T2-c:官方带父名前缀 → 剥除,不重复')
        # (2) 我方短名(无前缀) → 不剥(原样)
        ours = A.create({
            'code': '2221.02', 'name': '未交增值税',
            'account_type': 'liability_current',
            'company_ids': [Command.link(self.company.id)]})
        m2 = self._mk_move(date(2026, 6, 1), acc_a=ours); m2.action_post()
        l2 = m2.line_ids.filtered(lambda l: l.account_id == ours)
        self.assertEqual(m2._l10n_cn_account_path(l2), '应交税费 / 未交增值税',
                         'T2-c:我方短名不带前缀 → 不误剥')
        # (3) 防误剥:父名恰为明细名前缀但【无分隔符】(应交税费 vs 应交税费xxx 连写)
        no_sep = A.create({
            'code': '2221.03', 'name': '应交税费返还',   # 「应交税费」+「返还」无分隔符
            'account_type': 'liability_current',
            'company_ids': [Command.link(self.company.id)]})
        m3 = self._mk_move(date(2026, 6, 1), acc_a=no_sep); m3.action_post()
        l3 = m3.line_ids.filtered(lambda l: l.account_id == no_sep)
        self.assertEqual(m3._l10n_cn_account_path(l3), '应交税费 / 应交税费返还',
                         'T2-c:无分隔符 ⇒ 不剥(防误剥,语义不同)')

    def test_t2c_strip_helper_separators(self):
        """剥除助手按【父名+分隔符】枚举,不用贪婪正则;有分隔符才剥、无则不剥。"""
        A = self.env['account.move']
        self.assertEqual(A._l10n_cn_strip_parent_prefix('应交税费', '应交税费 - 增值税'), '增值税')
        self.assertEqual(A._l10n_cn_strip_parent_prefix('应交税费', '应交税费-增值税'), '增值税')
        self.assertEqual(A._l10n_cn_strip_parent_prefix('应交税费', '应交税费/增值税'), '增值税')
        self.assertEqual(A._l10n_cn_strip_parent_prefix('应交税费', '应交税费增值税'),
                         '应交税费增值税', '无分隔符 → 不剥')
        self.assertEqual(A._l10n_cn_strip_parent_prefix('应收', '应收账款'),
                         '应收账款', '前缀无分隔符 → 不剥')

    # —— T3-3 批量打印 docs 正序(不依赖默认 _order 倒序)——
    def test_t3_batch_print_docs_ordered(self):
        """造 5 张同月同凭证字凭证(号 1..5),以【乱序 docids】喂打印取值 → docs 必须按
        (公司×凭证字×凭证号)正序返回 1..5。account.move._order 默认倒序,不重排会打出倒序。"""
        moves = []
        for i in range(5):
            m = self._mk_move(date(2026, 6, i + 1), word='general')
            m.action_post()
            moves.append(m)
        self.assertEqual(sorted(m.l10n_cn_voucher_number for m in moves), [1, 2, 3, 4, 5])
        shuffled = [moves[4].id, moves[0].id, moves[2].id, moves[1].id, moves[3].id]
        vals = self.env['report.l10n_cn.report_voucher']._get_report_values(shuffled)
        self.assertEqual([m.l10n_cn_voucher_number for m in vals['docs']],
                         [1, 2, 3, 4, 5], 'T3-3:打印 docs 须按凭证号正序')

    def test_t3_batch_print_render_order_end_to_end(self):
        """惯例11 走查到终态:乱序输入 → 真渲染出的 PDF 里 记-1..记-5 位置必须递增。"""
        moves = self.env['account.move']
        for i in range(5):
            m = self._mk_move(date(2026, 6, i + 1), word='general')
            m.action_post()
            moves |= m
        html, _ttype = self.env['ir.actions.report']._render_qweb_html(
            'l10n_cn.account_voucher_cn', list(reversed(moves.ids)))
        body = html.decode() if isinstance(html, bytes) else html
        positions = [body.index('记-%d' % n) for n in range(1, 6)]
        self.assertEqual(positions, sorted(positions),
                         '🔴 T3-3:渲染出的凭证须按 记-1..记-5 正序,不受输入(倒序)影响')

    def test_t3_single_print_still_works(self):
        """T3-5 回归:单张打印不因批量重排改动而破。"""
        move = self._mk_move(date(2026, 6, 1)); move.action_post()
        html, _ttype = self.env['ir.actions.report']._render_qweb_html(
            'l10n_cn.account_voucher_cn', move.ids)
        body = html.decode() if isinstance(html, bytes) else html
        self.assertIn('记-1', body, '单张打印仍渲染凭证字号')

    def test_t3_report_binding_reaches_list(self):
        """T3-4:官方凭证报表打印绑定须含 list(列表打印菜单可达)。"""
        report = self.env.ref('l10n_cn.account_voucher_cn')
        self.assertIn('list', report.binding_view_types,
                      'T3-4:binding_view_types 须含 list(否则列表无打印入口)')

    # —— T2 缺陷#5 中文财务大写金额(人民币)——
    def test_amount_in_word_rmb(self):
        """PBOC《正确填写票据和结算凭证的基本规定》大写规则,10 用例 + 负数 + 三位小数取舍。"""
        A = self.env['account.move']
        cases = [
            (150.00, '壹佰伍拾元整'),          # 基础 + 「整」
            (0.00, '零元整'),                  # 零值
            (1409.50, '壹仟肆佰零玖元伍角'),    # 中间零 + 到角不写整
            (6007.14, '陆仟零柒元壹角肆分'),    # 连续零只写一个
            (1680.32, '壹仟陆佰捌拾元零叁角贰分'),  # 元位为 0
            (107000.53, '壹拾万柒仟元零伍角叁分'),  # 万位分级 + 连续零
            (100000000.00, '壹亿元整'),        # 亿分级
            (100000200.00, '壹亿零贰佰元整'),   # 亿位后连续零
            (0.05, '零元零伍分'),              # 无整数部分
        ]
        for amt, exp in cases:
            self.assertEqual(A._l10n_cn_rmb_upper(amt), exp, '金额 %.2f' % amt)
        # 🔴 负数:本轮取绝对值(中国凭证实务红字表负数,红字/负号形态待二姐确认)
        self.assertEqual(A._l10n_cn_rmb_upper(-150.00), '壹佰伍拾元整', '负数取绝对值')
        # 三位小数 → 四舍五入到分(HALF-UP);避开 .xx5 浮点边界,用无歧义值
        self.assertEqual(A._l10n_cn_rmb_upper(1.239), '壹元贰角肆分', '1.239→1.24')
        self.assertEqual(A._l10n_cn_rmb_upper(1.231), '壹元贰角叁分', '1.231→1.23')
        # 浮点误差(0.1+0.2=0.30000000000000004)不误判
        self.assertEqual(A._l10n_cn_rmb_upper(0.1 + 0.2), '零元叁角', '浮点 0.3→叁角')

    def test_amount_in_word_currency_guard(self):
        """币种守卫:仅 CNY 产中文大写;其他币种落回上游(cn2an 未装 → None/非中文)。"""
        cny = self.env.ref('base.CNY')
        usd = self.env.ref('base.USD')
        (cny + usd).write({'active': True})
        m = self._mk_move(date(2026, 6, 1))
        m.currency_id = cny
        self.assertEqual(m._convert_to_amount_in_word(150.0), '壹佰伍拾元整', 'CNY → 中文大写')
        m.currency_id = usd
        self.assertNotIn('元', m._convert_to_amount_in_word(150.0) or '',
                         '非 CNY → 落回上游行为,不产中文')

    # —— 惯例2 多公司 ——
    def test_multicompany_scoping(self):
        m_a = self._mk_move(date(2026, 6, 1)); m_a.action_post()
        c2 = self.company_data_2['company']
        m_b = self._mk_move(date(2026, 6, 1), company=c2,
                            journal=self.company_data_2['default_journal_misc'],
                            acc_a=self.company_data_2['default_account_revenue'],
                            acc_b=self.company_data_2['default_account_expense'])
        m_b.action_post()
        self.assertEqual(m_a.l10n_cn_voucher_number, 1)
        self.assertEqual(m_b.l10n_cn_voucher_number, 1, "各公司序列独立")

    # —— 惯例11 走查跑到终态：PDF 模板真的渲染出来 ——
    def test_report_renders_to_end(self):
        move = self._mk_move(date(2026, 6, 1)); move.action_post()
        html, ttype = self.env['ir.actions.report']._render_qweb_html(
            'l10n_cn.account_voucher_cn', move.ids)
        self.assertEqual(ttype, 'html')
        body = html.decode() if isinstance(html, bytes) else html
        self.assertIn('记账凭证', body, "中文版式真的渲染")
        self.assertIn('记-1', body, "凭证字号出现在 PDF")
        self.assertIn('摘要', body)

    # —— P-01：原生 name 不受我方取号影响（两套机制独立，B-52）——
    def test_native_name_untouched(self):
        move = self._mk_move(date(2026, 6, 1)); move.action_post()
        # 🔴 R46 正向哨兵(惯例30):我方取号【确实发生】(号=1)。否则本用例只验「name 无 记-」,
        # 打桩 _l10n_cn_assign_voucher_number→None(我方码全不写)时,原生 name 仍正常、当然无
        # 记- → 全绿=空绿(R46 实测)。哨兵挂钩我方产出后:取号空转 → 红。
        self.assertEqual(move.l10n_cn_voucher_number, 1, "哨兵:我方取号须真发生(号=1)")
        self.assertTrue(move.name and move.name != '/', "原生 name 由 sequence.mixin 正常分配")
        self.assertNotIn('记-', move.name, "凭证号不污染 account.move.name")
