# -*- coding: utf-8 -*-
"""R33-A 验收 —— ASSBE 科目表发行 + 官方报表国标口径覆盖 + 卸载可逆。

🔴 V6 平衡回归是本轮最强的一条实证的固化:手工实测「行11 改读 4001 而 PL 营业成本不摘
4001 会破 30=53 差 6000」，人走了就没了 → 变成一条会自己叫的测试(否则谁把 PL 那处
override 摘掉,没人会知道)。
"""
from odoo import Command
from odoo.tests import TransactionCase, tagged

from odoo.addons.suite_cn_coa.models.assbe_chart_data import (
    ASSBE_CHART, CASH_CODES,
)
from odoo.addons.suite_cn_coa.models.report_override import REPORT_OVERRIDES


@tagged('post_install', '-at_install')
class TestCoaPublish(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # R45-T1: 本类【全部发行路径用例】的前置 = zh_CN 已激活(R38-T3 语言门:未激活则
        # _publish 整批拒绝、不建一条科目 → 依赖发行的用例连锁失败)。test_t3_publish_lang_gate
        # 亦断言「本库 zh_CN 应已激活」并对未激活路径【打桩】验。develop-6 dev 库默认未激活
        # zh_CN(一次性起点,惯例27),这批用例遂在本 build 静默红。此处于 setUpClass【自备】
        # 该前置——TransactionCase 在 tearDownClass 整体回滚,真实库 zh_CN 仍保持未激活,
        # 【不消耗】那份「未激活」一次性起点(惯例27:本轮消耗=无)。
        lang = cls.env['res.lang'].with_context(active_test=False).search(
            [('code', '=', 'zh_CN')], limit=1)
        if lang and not lang.active:
            cls.env['res.lang']._activate_lang('zh_CN')
        cls.company = cls.env['res.company'].search(
            [('chart_template', '=', 'cn')], limit=1)
        cls.company_large = cls.env['res.company'].search(
            [('chart_template', '=', 'cn_large_bis')], limit=1)
        cls.publisher = cls.env['suite.cn.coa.publisher']
        cls.Ledger = cls.env['suite.cn.coa.published.account']
        cls.Account = cls.env['account.account']

    def _acc(self, code):
        return self.Account.with_company(self.company).with_context(
            active_test=False).search(
            [('code', '=', code), ('company_ids', 'in', self.company.id)], limit=1)

    # ------------------------------------------------------------ chart data
    def test_chart_data_integrity(self):
        """100 条;【每纳税人档内】无重复码(R43:2221.01 一般=应交增值税树父 / 小规模=flat
        增值税,同码但按 taxpayer 互斥,故整表看有一对同码是【合法】的);现金三码 asset_cash。"""
        self.assertEqual(len(ASSBE_CHART), 100)
        self.assertNotIn('2221023', [a['code'] for a in ASSBE_CHART], '应交关税=不预置')
        # 每个实际发行档(common / common+small / common+general)内不得有重复码
        Pub = self.env['suite.cn.coa.publisher']
        for tp in ('common', 'small', 'general'):
            codes = [a['code'] for a in Pub._accounts_for(tp)]
            self.assertEqual(len(codes), len(set(codes)),
                             'taxpayer=%s 档内编码不得重复' % tp)
        # 整表唯一允许的同码 = 2221.01(general vs small),其余全唯一
        all_codes = [a['code'] for a in ASSBE_CHART]
        dups = {c for c in all_codes if all_codes.count(c) > 1}
        self.assertEqual(dups, {'2221.01'},
                         '整表唯一允许同码=2221.01(一般/小规模互斥);got %s' % dups)
        for a in ASSBE_CHART:
            if a['cf_cash']:
                self.assertEqual(a['account_type'], 'asset_cash',
                                 '%s cf_cash → 必须 asset_cash' % a['code'])
        self.assertEqual(set(CASH_CODES), {'1001', '1002', '1012'})

    # --------------------------------------------------------------- publish
    def test_publish_idempotent_and_claim(self):
        """认领优先 + 幂等:重跑不重复建、不覆盖客户改动(§4.8.3)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        self.publisher._publish(self.company, taxpayer='small')
        # 🔴 R46 正向哨兵(惯例30):_publish 必须【真发行】(我方创建号段 .51–.56 落 created
        # 台账),否则下方「认领不覆盖客户改名」在【发行整体空转】时也天然成立=空绿。原用例仅
        # 用官方 1122(恒存在)+ 自设名验非覆盖,打桩 _publish→{} 仍全绿(R46 实测)。
        self.assertTrue(self.Ledger.search_count(
            [('company_id', '=', self.company.id), ('action', '=', 'created')]),
            '哨兵:_publish 须真发行(created 台账 > 0);为 0 说明发行空转,本用例本会空绿')
        acc = self._acc('1122')
        self.assertTrue(acc, '1122 应收账款 应已发行')
        # 客户改名 + 再发行 → 名字不被覆盖(认领不改名)
        acc.name = '客户改过的名字'
        self.publisher._publish(self.company, taxpayer='small')
        self.assertEqual(self._acc('1122').name, '客户改过的名字',
                         '认领优先:再发行不得覆盖客户改的名')
        # reconcile 往来标记
        self.assertTrue(self._acc('1122').reconcile)

    # ------------------------------------------------ R37-T4-a 门控:非 cn 拒绝
    def test_publish_rejects_non_cn_chart(self):
        """缺陷#1:判据 = 目标公司 chart_template。向 cn_large_bis(ASBE)发行必须【拒绝】,
        不建一条科目、不写一条台账,并回可读原因(点名公司+准则,不写「见日志」)。此前
        wizard 默认滤 supported 但 _publish 从不复核,手动加公司即绕过(R35 实污染)。"""
        if not self.company_large:
            self.skipTest('no cn_large_bis company')
        before = self.Ledger.search_count([('company_id', '=', self.company_large.id)])
        rep = self.publisher._publish(self.company_large, taxpayer='common')
        r = rep[self.company_large.id]
        self.assertTrue(r.get('rejected'), '向 cn_large_bis 发行必须被拒绝')
        self.assertIn('cn_large_bis', r['reason'], '拒绝原因须点名准则')
        self.assertIn(self.company_large.name, r['reason'], '拒绝原因须点名公司')
        self.assertNotIn('见日志', r['reason'], '惯例5:界面须自证,不得写「见日志」')
        self.assertEqual(
            self.Ledger.search_count([('company_id', '=', self.company_large.id)]),
            before, '被拒绝的公司不得新增任何发行台账行')

    def test_supported_companies_excludes_large(self):
        """_supported_companies 只含 cn 准则公司,天然不含 cn_large_bis。"""
        supported = self.publisher._supported_companies()
        self.assertNotIn(self.company_large, supported,
                         'cn_large_bis 不应在 supported 集合')
        if self.company:
            self.assertIn(self.company, supported)

    # -------------------------------------------------- R37-T4-b 认领写台账
    def test_claim_writes_ledger(self):
        """缺陷#3:认领分支必须写台账(action='claimed' + 认领前 name/type 快照),否则跨
        准则碰撞(4001 等)事后无迹可查。幂等:再发行不重复写、不翻转 created。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        # 1122 在官方 cn 表已存在 → 首次发行即【认领】→ 应落一条 claimed 台账
        self.publisher._publish(self.company, taxpayer='small')
        led = self.Ledger.search(
            [('company_id', '=', self.company.id), ('code', '=', '1122')], limit=1)
        self.assertTrue(led, '认领 1122 必须写台账(缺陷#3)')
        self.assertEqual(led.action, 'claimed', '既有科目=认领,非新建')
        self.assertTrue(led.claimed_type, '认领前 account_type 须快照')
        self.assertTrue(led.claimed_name, '认领前名称须快照')
        # 幂等:再发行不新增第二条、不翻转
        n1 = self.Ledger.search_count([('company_id', '=', self.company.id)])
        self.publisher._publish(self.company, taxpayer='small')
        self.assertEqual(
            self.Ledger.search_count([('company_id', '=', self.company.id)]), n1,
            '再发行不得重复写台账')
        self.assertEqual(led.action, 'claimed', '再发行不得翻转已有 action')

    # -------------------------------------------------- R37-T4-c 存量污染扫描
    def test_scan_foreign_publications(self):
        """只读扫描:台账行落在【非 cn 公司】上 → 列入 by_ledger(抓 R35 那批新建的 43 条)。
        cn 公司上的正常台账行不得混入。"""
        if not (self.company_large and self.company):
            self.skipTest('need both cn and cn_large_bis companies')
        # 模拟 R35 污染:在 cn_large_bis 上手工插一条我方发行台账(指向其 4001 科目)
        acc4001 = self.Account.with_company(self.company_large).with_context(
            active_test=False).search(
            [('code', '=', '4001'),
             ('company_ids', 'in', self.company_large.id)], limit=1)
        if not acc4001:
            self.skipTest('cn_large_bis has no 4001')
        self.Ledger.create({
            'company_id': self.company_large.id, 'code': '4001',
            'account_id': acc4001.id, 'taxpayer': 'common', 'action': 'created'})
        # cn 公司上放一条正常台账做对照(不应被扫出)
        acc_cn = self._acc('1001') or self.Account.with_company(self.company).search(
            [('company_ids', 'in', self.company.id)], limit=1)
        self.Ledger.create({
            'company_id': self.company.id, 'code': 'ZZTEST',
            'account_id': acc_cn.id, 'taxpayer': 'common', 'action': 'created'})
        res = self.publisher._scan_foreign_publications()
        codes = [(r['company_id'], r['code']) for r in res['by_ledger']]
        self.assertIn((self.company_large.id, '4001'), codes,
                      '非 cn 公司上的我方发行痕迹必须被扫出')
        self.assertNotIn((self.company.id, 'ZZTEST'), codes,
                         'cn 公司上的正常台账不得混入污染清单')
        self.assertIn('盲区', res['untracked_note'], '须诚实标注认领盲区(惯例12)')

    # -------------------------------------------------- R38-T3 语言前置校验
    def test_t3_publish_lang_gate(self):
        """R38-T3 (#4/#7 前置校验):zh_CN 未激活 → 发行【拒绝】+ 可读原因(缺什么语言/去哪装/
        为什么必须先装),不建一条科目。激活态(本库)→ _publish_lang_active True。
        🔴 dual-key create 路径(激活后以 lang=zh_CN 建 → en_US+zh_CN 双键)由 R37-T5 verified
        保证,本库 zh_CN 停不掉,故未激活分支用打桩验(honest 边界:未做全新库顺序实测)。"""
        from unittest.mock import patch  # noqa: PLC0415
        if not self.company:
            self.skipTest('no cn-chart company')
        self.assertTrue(self.publisher._publish_lang_active(), '本库 zh_CN 应已激活')
        AccC = self.Account.with_company(self.company).with_context(active_test=False)
        before = AccC.search_count([('company_ids', 'in', self.company.id)])
        with patch.object(type(self.publisher), '_publish_lang_active', return_value=False):
            rep = self.publisher._publish(self.company, taxpayer='common')
        r = rep[self.company.id]
        self.assertTrue(r.get('rejected'), 'zh_CN 未激活必须拒绝发行')
        self.assertIn('zh_CN', r['reason'], '原因须点名语言')
        self.assertIn('先装语言', r['reason'], '原因须给装机顺序指引')
        self.assertNotIn('见日志', r['reason'], '惯例5:界面须自证')
        after = AccC.search_count([('company_ids', 'in', self.company.id)])
        self.assertEqual(before, after, '拒绝时不得新建任何科目')

    def test_publish_taxpayer_filter(self):
        """R43 点分:一般纳税人得三级增值税树(2221.01 + 2221.01.0x);小规模得 flat 2221.01
        (无三级)。两档 2221.01 同码、按 taxpayer 互斥(§4.4)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        self.publisher._publish(self.company, taxpayer='general')
        self.assertTrue(self._acc('2221.01'), '一般纳税人应有 2221.01 应交增值税')
        self.assertTrue(self._acc('2221.01.02'), '应有增值税三级明细 2221.01.02 进项税额')
        rows_small = {a['code'] for a in self.publisher._accounts_for('small')}
        rows_general = {a['code'] for a in self.publisher._accounts_for('general')}
        # 两档都含 2221.01;三级明细只在一般档
        self.assertIn('2221.01', rows_small)
        self.assertIn('2221.01', rows_general)
        self.assertNotIn('2221.01.02', rows_small, '小规模不发三级增值税明细')
        self.assertIn('2221.01.02', rows_general)
        # 旧连号编码全不复存在
        self.assertNotIn('2221001', rows_general | rows_small, '连号编码已废')
        self.assertNotIn('2221010', rows_general | rows_small, '连号编码已废')

    # ============================== R43 点分迁移验收 (T1-e 绝对终态) ==============
    def _led(self, action, like):
        return self.Ledger.search([
            ('company_id', '=', self.company.id),
            ('action', '=', action), ('code', '=like', like)])

    def test_r43_small_acceptance(self):
        """R43-T1e 小规模档:2221 下【新建=6】(=我方 .51–.56)、【认领明细=15】、连号=0。
        (基线由装机 post_init 发过 common;本档补 small 2221.01 认领 → 认领 14→15。)"""
        if not self.company:
            self.skipTest('no cn-chart company')
        self.publisher._publish(self.company, taxpayer='small')
        created = self._led('created', '2221.%')
        self.assertEqual(len(created), 6, 'R43-T1e#1:小规模 2221 下新建=6')
        self.assertEqual(
            set(created.mapped('code')),
            {'2221.51', '2221.52', '2221.53', '2221.54', '2221.55', '2221.56'},
            '新建 6 条即我方号段 .51–.56')
        self.assertEqual(len(self._led('claimed', '2221.%')), 15,
                         'R43-T1e#2:小规模 2221 明细认领=15')
        self.assertEqual(self.publisher._detect_legacy_lianhao(self.company), [],
                         'R43-T1e#4:干净库无连号残留')

    def test_r43_general_acceptance(self):
        """R43-T1e 一般纳税人档:2221 下【新建=6】、【认领明细=25】(比小规模多 10 条增值税
        三级 + 2221.01 父,共 +11 − small 的 +1 折算… 直接断言绝对值 25)、连号=0。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        self.publisher._publish(self.company, taxpayer='general')
        self.assertEqual(len(self._led('created', '2221.%')), 6,
                         'R43-T1e#1:一般档 2221 下新建=6')
        self.assertEqual(len(self._led('claimed', '2221.%')), 25,
                         'R43-T1e#2:一般档 2221 明细认领=25')
        self.assertEqual(self.publisher._detect_legacy_lianhao(self.company), [],
                         'R43-T1e#4:干净库无连号残留')

    def test_r43_collision_sentinel(self):
        """R43-T1e#7 撞号哨兵【两半都跑】:①正常路径不误报(惯例14=预期结果,非证据);
        ②合成撞号【能触发】(唯一构成证据的那半)——我方号段码被非我方占用 → 跳过不覆盖 + 留痕。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        A = self.company
        # 半①:正常发行 collision=0(预期结果,非证据)
        rep = self.publisher._publish(A, taxpayer='common')
        self.assertEqual(rep[A.id]['collision'], 0, '正常路径不得误报撞号')
        # 半②(证据):把我方 2221.51 换成【非我方】占用者,再发行 → 撞号必触发
        self.Ledger.search(
            [('company_id', '=', A.id), ('code', '=', '2221.51')]).unlink()
        ours = self._acc('2221.51')
        if ours:
            ours.unlink()
        self.Account.create({
            'code': '2221.51', 'name': '外人占号科目',
            'account_type': 'liability_current',
            'company_ids': [Command.link(A.id)]})
        rep2 = self.publisher._publish(A, taxpayer='common')
        self.assertGreaterEqual(rep2[A.id]['collision'], 1,
                                '🔴 合成撞号必须触发(唯一构成证据的那半)')
        self.assertEqual(self._acc('2221.51').name, '外人占号科目',
                         '撞号不得覆盖占用者')
        self.assertTrue(self.Ledger.search(
            [('company_id', '=', A.id), ('code', '=', '2221.51'),
             ('action', '=', 'collision')]),
            '撞号须留台账(action=collision)')

    def test_r45_legacy_lianhao_narrowed(self):
        """R45-T1:连号检测【收窄为「且台账痕迹」】的两半(该静时静 / 该响时响)。

        起因(R45-T1):原判据 `2221`+纯数字【或】台账痕迹 —— 第一分支不要求台账,会把
        【从金蝶迁来的正常客户】的自有连号税费明细(2221001 应交增值税、2221011 应交
        所得税 … 星辰表 34 条)整批误报为「旧版连号残留」。产品上线前无客户装过 2.x ⇒
        「有我方残留」人群为空,「或」的现实唯一受众是被误报的连号客户。收窄为【且】后:
          * 误报半:连号科目【无我方台账痕迹】(=金蝶迁入客户) → 【不触发】(该静时静)。
          * 正报半:同一码【补我方发行台账痕迹】(=真·2.x 残留) → 【触发】(该响时响)。
        两半是本用例的全部价值:任一不成立即判未过,不得用「其余都对」抵(R45-T1 验收)。
        用例走 TransactionCase → 事务内 rollback 收尾(R45 无 T1 例外)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        A = self.company
        # 星辰表「保留」且 2221 开头那批的代表码(真实客户自有税费明细形态)。
        KINGDEE = ['2221001', '2221011', '2221001007']
        self.assertEqual(self.publisher._detect_legacy_lianhao(A), [],
                         'R45-T1#0:干净库无连号')
        accs = {}
        for code in KINGDEE:
            accs[code] = self.Account.create({
                'code': code, 'name': '金蝶迁入-%s' % code,
                'account_type': 'liability_current',
                'company_ids': [Command.link(A.id)]})
        # ── 误报半:2221 连号形态齐备,但【无我方发行台账】→ 收窄后【不触发】。
        self.assertEqual(
            self.publisher._detect_legacy_lianhao(A), [],
            '🔴 R45-T1#2(误报半):金蝶连号客户无我方台账痕迹 → 不得触发')
        # 旧行为对照(判据6):`2221`+纯数字【或】台账 —— 同夹具旧判据的命中数。
        old_hits = sorted(
            c for c in KINGDEE
            if (c.startswith('2221') and c[4:].isdigit()))  # 旧「或」左支即命中
        self.assertEqual(len(old_hits), 3,
                         'R45-T1#6(旧行为):旧「或」判据在同夹具会误报 3 条')
        # ── 正报半:补我方发行台账痕迹(=真·2.x 我方残留)→ 收窄后【触发】。
        for code in KINGDEE:
            self.Ledger.create({
                'company_id': A.id, 'code': code,
                'account_id': accs[code].id, 'taxpayer': 'common',
                'action': 'created'})
        detected = self.publisher._detect_legacy_lianhao(A)
        for code in KINGDEE:
            self.assertIn(code, detected,
                          '🔴 R45-T1#3(正报半):有我方台账痕迹的连号残留须触发')
        # ── 只报不动 + 回执原文:发行后连号科目仍在、名字未变,回执带清单。
        rep = self.publisher._publish(A, taxpayer='common')
        for code in KINGDEE:
            self.assertIn(code, rep[A.id].get('legacy_lianhao', []),
                          'R45-T1#4:回执须带连号残留清单')
            self.assertTrue(self._acc(code), '连号科目不得被删(科目留库)')
            self.assertEqual(self._acc(code).name, '金蝶迁入-%s' % code,
                             'R45-T1#5:连号科目不得被改')

    def test_r43_local_taxes_archived(self):
        """R43-T4:6 条地方税种默认归档 active=False;台账照记(记的是发过,非启用中)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        A = self.company
        self.publisher._publish(A, taxpayer='common')
        acc = self.Account.with_company(A).with_context(active_test=False).search(
            [('code', '=', '2221.51'), ('company_ids', 'in', A.id)], limit=1)
        self.assertTrue(acc, '2221.51 应交个人所得税 应已发行')
        self.assertFalse(acc.active, 'R43-T4:地方税默认 active=False')
        self.assertTrue(self.Ledger.search(
            [('company_id', '=', A.id), ('code', '=', '2221.51')]),
            '归档科目发行台账照记')
        vat = self.Account.with_company(A).with_context(active_test=False).search(
            [('code', '=', '2221.02'), ('company_ids', 'in', A.id)], limit=1)
        if vat:
            self.assertTrue(vat.active, '2221.02 未交增值税 应 active(非地方税)')

    def test_r43_archived_disclosed_in_report_and_receipt(self):
        """R43-T4 理由链闭合:默认归档的 6 条须在 _publish 报告 + wizard 回执【明列 + 给启用
        路径】。归档科目界面默认不显示,回执不说 = 等于没发(客户照样自建、指标3零省)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        A = self.company
        rep = self.publisher._publish(A, taxpayer='common')
        archived = rep[A.id].get('archived') or []
        self.assertEqual(len(archived), 6, 'R43-T4:6 条地方税须在报告 archived 列出')
        self.assertIn('应交个人所得税', [a['name'] for a in archived])
        # wizard 回执:明列 + 启用路径(过滤已归档 → 取消归档)
        wiz = self.env['suite.cn.coa.publish'].create({
            'company_ids': [Command.link(A.id)], 'taxpayer': 'small'})
        wiz.action_run()
        self.assertIn('默认已归档', wiz.result, '回执须声明这些科目已归档')
        self.assertIn('取消归档', wiz.result, '回执须给启用路径(否则客户找不到)')
        self.assertIn('应交房产税', wiz.result, '回执须点名具体科目')

    def test_cash_type_guard(self):
        """1001/1002/1012 已存在但非 asset_cash → 认领不改 + 告警计数(§4.2)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        self.publisher._publish(self.company, taxpayer='common')
        cash = self._acc('1001')
        self.assertEqual(cash.account_type, 'asset_cash')
        # 人为破坏 type, 再发行:不被改回, 但 cash_warn 计数
        cash.account_type = 'asset_current'
        rep = self.publisher._publish(self.company, taxpayer='common')
        self.assertEqual(self._acc('1001').account_type, 'asset_current',
                         '认领不改 type')
        self.assertGreaterEqual(rep[self.company.id]['cash_warn'], 1)

    def test_validate_codes_no_empty(self):
        """§4.7:发行后无【有记录无 code】科目(F3/B-63 静默错报形态防线)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        self.publisher._publish(self.company, taxpayer='common')
        self.assertTrue(self.publisher._validate_codes(self.company))

    # ------------------------------------------------- report override 可逆
    def test_report_override_roundtrip(self):
        """apply → 行11=4001 / 行12 含 1406 / PL营业成本 摘 4001 / 行26 hide_if_zero;
        restore → 全部写回原值(§4.9.2)。

        R36-T1:本模块只覆盖官方原生 balance 那一列,故只断言 balance;我方 bal_begin/ytd
        由 suite_cn_statement 源头 XML 恒产国标值,不参与本模块的 apply/restore(改动5)。"""
        Ov = self.env['suite.cn.coa.report.override']
        wip = self.env.ref('l10n_cn_reports.l10n_cn_assbe_bs_cns_wip')
        inv = self.env.ref('l10n_cn_reports.l10n_cn_assbe_bs_cns_inv')
        oc = self.env.ref('l10n_cn_reports.l10n_cn_assbe_pl_cns_oc')
        rdc = self.env.ref('l10n_cn_reports.l10n_cn_assbe_bs_cns_rdc')

        def ac(line):
            # R36-T1:只取官方原生 balance 列(本模块覆盖面);bal_begin/ytd 归 statement 源头。
            return line.expression_ids.filtered(
                lambda e: e.engine == 'account_codes' and e.label == 'balance')

        Ov._apply_all()
        for e in ac(wip):
            self.assertEqual(e.formula, '4001', '行11 在产品 → 4001')
        for e in ac(inv):
            self.assertIn('1406', e.formula, '行12 库存商品 → 含 1406')
        for e in ac(oc):
            self.assertIn(r'40\(4001)', e.formula, 'PL 营业成本 → 摘 4001')
        self.assertTrue(rdc.hide_if_zero, '行26 研发费用 → hide_if_zero')

        Ov._restore_all()
        for e in ac(wip):
            self.assertEqual(e.formula, '1406', '还原:行11 → 1406')
        for e in ac(oc):
            self.assertNotIn(r'40\(4001)', e.formula, '还原:PL 营业成本 → 原值')
        self.assertFalse(
            self.env['suite.cn.coa.report.override'].search([]),
            '还原后台账清空')

    # --------------------------------------------------- 🔴 V6 平衡回归
    def test_v6_balance_regression(self):
        """🔴 Dr 4001 / Cr 1403 6000 → 套 5 处覆盖 → 30=53、crossfoot 空、
        PL 营业成本【不含】该 6000。缺 PL 那处覆盖会破 30=53 差 6000(手工实测固化)。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        A = self.company
        self.publisher._publish(A, taxpayer='common')
        self.env['suite.cn.coa.report.override']._apply_all()
        self.env.invalidate_all()
        wip = self._acc('4001')
        rm = self._acc('1403')
        self.assertTrue(wip and rm, '4001/1403 应已发行')
        journal = self.env['account.journal'].with_company(A).search(
            [('company_id', '=', A.id), ('type', '=', 'general')], limit=1)
        move = self.env['account.move'].with_company(A).create({
            'move_type': 'entry', 'journal_id': journal.id,
            'date': '2026-06-30',
            'line_ids': [
                Command.create({'account_id': wip.id, 'debit': 6000, 'credit': 0, 'name': 'WIP'}),
                Command.create({'account_id': rm.id, 'debit': 0, 'credit': 6000, 'name': 'WIP'}),
            ]})
        move.action_post()
        self.env.invalidate_all()

        bs = self.env.ref('l10n_cn_reports.l10n_cn_assbe_bs')
        rep = bs.with_company(A).with_context(allowed_company_ids=[A.id])
        opts = rep.get_options({})
        vals = {}
        for line in rep._get_lines(opts):
            if rep._get_model_info_from_id(line['id'])[0] != 'account.report.line':
                continue
            cols = line.get('columns') or []
            vals[line['name']] = cols[0].get('no_format') if cols else None

        def by(*keys):
            return next((v for n, v in vals.items()
                         if v is not None and any(k in n for k in keys)), None)

        total_assets = by('资产总计', 'Total Assets')
        total_le = by('负债和所有', "Total liabilities")
        self.assertIsNotNone(total_assets)
        self.assertAlmostEqual(
            total_assets, total_le, 2,
            '🔴 30=53 必须成立:行11→4001 已配 PL 营业成本摘 4001,资产=负债权益。'
            '若破,说明 PL 那处 override 被摘/失效(V6 的全部意义)。')

        # crossfoot 空(若 suite_cn_statement 装了才验)
        form = self.env['suite.cn.statement.form'].search(
            [('report_id', '=', bs.id)], limit=1)
        if form:
            data = rep._cn_prepare(form, opts)
            breaks = rep._cn_crossfoot_breaks(form, data)
            self.assertFalse(
                [b for b in breaks if '30' in b[0] and '53' in b[0]],
                'crossfoot 不得有 30=53 破口')

    # --------------------------------------- 🔴 V6b 年初列(bal_begin)路径
    def test_v6b_balance_regression_bal_begin(self):
        """🔴 V6b:同一笔 6000 记在【上一年度】→ 验【年初列(bal_begin)】30=53 不破、
        年初列存货含 6000、年初列权益不被扣。

        为什么单列:每行有 balance + bal_begin/ytd 两条表达式,7 条原值里 3 条是 bal_begin
        的;V6 只走 balance 路,bal_begin 路(prev_year_earnings balance_domain 的年初评估
        + 行11/行12 的 bal_begin)此前是推演。R32-F5 已证逐列独立,故须单列验。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        form = self.env['suite.cn.statement.form'].search(
            [('report_id.id', '=', self.env.ref(
                'l10n_cn_reports.l10n_cn_assbe_bs').id)], limit=1)
        if not form:
            self.skipTest('suite_cn_statement 未装,无年初列')
        A = self.company
        self.publisher._publish(A, taxpayer='common')
        self.env['suite.cn.coa.report.override']._apply_all()
        self.env.invalidate_all()
        wip, rm = self._acc('4001'), self._acc('1403')
        journal = self.env['account.journal'].with_company(A).search(
            [('company_id', '=', A.id), ('type', '=', 'general')], limit=1)
        # 上一会计年度(中国 FY=历年):记 2025-06-30 → 2026 年初余额含它
        move = self.env['account.move'].with_company(A).create({
            'move_type': 'entry', 'journal_id': journal.id, 'date': '2025-06-30',
            'line_ids': [
                Command.create({'account_id': wip.id, 'debit': 6000, 'credit': 0, 'name': 'WIP'}),
                Command.create({'account_id': rm.id, 'debit': 0, 'credit': 6000, 'name': 'WIP'}),
            ]})
        move.action_post()
        self.env.invalidate_all()

        bs = self.env.ref('l10n_cn_reports.l10n_cn_assbe_bs')
        rep = bs.with_company(A).with_context(allowed_company_ids=[A.id])
        opts = rep.get_options({})
        data = rep._cn_prepare(form, opts)
        # crossfoot 覆盖【全部列】(含年初列):30=53 任一列破都会现
        breaks = rep._cn_crossfoot_breaks(form, data)
        self.assertFalse(
            [b for b in breaks if '30' in b[0] and '53' in b[0]],
            '🔴 年初列 30=53 破 → bal_begin 路的某条 override 失效(V6b 的全部意义)。'
            ' breaks=%s' % breaks)

        # 年初列(第 2 列, index 1)逐行取值,验存货含 6000、资产总计=负债权益总计
        rows = data.get('left', []) + data.get('right', [])
        by_no = {r['row_no']: r for r in rows if (r.get('row_no') or '').strip()}

        def col1(row_no):
            r = by_no.get(str(row_no))
            v = r['values'][1] if r and len(r['values']) > 1 else None
            return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

        stock_begin = col1(9)          # 行9 存货
        assets_begin = col1(30)        # 行30 资产总计
        le_begin = col1(53)            # 行53 负债和所有者权益总计
        self.assertIsNotNone(assets_begin, '年初列应有资产总计')
        self.assertAlmostEqual(assets_begin, le_begin, 2,
                               '🔴 年初列 资产总计=负债权益总计')
        # 存货年初 = 原材料(-6000) + 在产品(+6000) = 0(移动中性);关键是 4001 进了存货口径
        # 而非权益。用行11 在产品年初列直接验含 6000。
        self.assertAlmostEqual(col1(11), 6000.0, 2,
                               '🔴 年初列 行11 在产品 = 4001 余额 6000(bal_begin=4001 生效)')

    # --------------------------------- 🔴 R38-T1 阶段B ASBE 存货 backport 回归
    def test_v7_asbe_inventory_backport(self):
        """🔴 R38-T1:ASBE【三处成对摘】(存货+营业成本+权益)。Dr5001/Cr1403 6000 →
        存货Δ=0(在产品进存货、与原材料流出净抵)、营业成本Δ=0(摘出成本码)、30=53 不破、
        无 nonneg 破口。5101/5201 各同形态一笔、同判据。对照 Dr1403/Cr2202 → 存货Δ=+6000。

        缺权益 balance_domain 那处会破 30=53 差 6000(阶段A逐组验证固化为会自己叫的测试);
        并校 bal_begin/ytd 源头 XML 已含成本码(年初列/本年累计列口径)。"""
        A = self.company_large
        if not A:
            self.skipTest('no cn_large_bis company')
        Ov = self.env['suite.cn.coa.report.override']
        Ov._apply_all()
        self.env.invalidate_all()

        def acc(code):
            return self.Account.with_company(A).with_context(active_test=False).search(
                [('code', '=', code), ('company_ids', 'in', A.id)], limit=1)
        a1403, a2202 = acc('1403'), acc('2202')
        if not (a1403 and a2202 and acc('5001') and acc('5101') and acc('5201')):
            self.skipTest('5001/5101/5201/1403/2202 缺,cn_large_bis 科目不全')

        # 源头 XML(年初列/本年累计列)已含成本码
        inv_line = self.env.ref('l10n_cn_reports.l10n_cn_asbe_bs_cn_inv')
        begin = inv_line.expression_ids.filtered(
            lambda e: e.label == 'bal_begin' and e.engine == 'account_codes')[:1]
        self.assertTrue(begin and '5001' in (begin.formula or ''),
                        '🔴 cn_inv bal_begin 源头 XML 应含 5001(年初列口径)')
        oc_line = self.env.ref('l10n_cn_reports.l10n_cn_asbe_pl_cn_oc')
        ytd = oc_line.expression_ids.filtered(
            lambda e: e.label == 'ytd' and e.engine == 'account_codes')[:1]
        self.assertTrue(ytd and '5001' in (ytd.formula or ''),
                        '🔴 cn_oc ytd 源头 XML 应含 5001(本年累计列摘出)')

        journal = self.env['account.journal'].with_company(A).search(
            [('company_id', '=', A.id), ('type', '=', 'general')], limit=1)
        bs = self.env.ref('l10n_cn_reports.l10n_cn_asbe_bs')
        pl = self.env.ref('l10n_cn_reports.l10n_cn_asbe_pl')
        form = self.env['suite.cn.statement.form'].search(
            [('report_id', '=', bs.id)], limit=1)
        inv_id = inv_line.id
        assets_id = self.env.ref('l10n_cn_reports.l10n_cn_asbe_bs_cn_a').id
        tle_id = self.env.ref('l10n_cn_reports.l10n_cn_asbe_bs_cn_tle').id
        oc_id = oc_line.id

        def num(v):
            return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0

        def snapshot():
            m = {}
            for rep_rec, want in ((bs, (inv_id, assets_id, tle_id)), (pl, (oc_id,))):
                rep = rep_rec.with_company(A).with_context(allowed_company_ids=[A.id])
                for line in rep._get_lines(rep.get_options({})):
                    mi = rep._get_model_info_from_id(line['id'])
                    if mi and mi[0] == 'account.report.line' and mi[1] in want:
                        cols = line.get('columns') or []
                        m[mi[1]] = num(cols[0].get('no_format') if cols else None)
            return {'inv': m.get(inv_id, 0.0), 'assets': m.get(assets_id, 0.0),
                    'tle': m.get(tle_id, 0.0), 'oc': m.get(oc_id, 0.0)}

        def post(dr, cr_acc):
            mv = self.env['account.move'].with_company(A).create({
                'move_type': 'entry', 'journal_id': journal.id, 'date': '2026-06-30',
                'line_ids': [
                    Command.create({'account_id': dr.id, 'debit': 6000, 'credit': 0, 'name': 't'}),
                    Command.create({'account_id': cr_acc.id, 'debit': 0, 'credit': 6000, 'name': 't'})]})
            mv.action_post()
            self.env.invalidate_all()

        def nonneg():
            if not form:
                return []
            rep = bs.with_company(A).with_context(allowed_company_ids=[A.id])
            data = rep._cn_prepare(form, rep.get_options({}))
            return [b for b in rep._cn_crossfoot_breaks(form, data)
                    if len(b) > 6 and b[6] == 'nonneg']

        prev = snapshot()   # 基线
        # 病症-修复:三个成本码各一笔,每笔存货/营业成本增量必须为 0(在产品口径),30=53 不破
        for code in ('5001', '5101', '5201'):
            post(acc(code), a1403)
            s = snapshot()
            self.assertAlmostEqual(
                s['inv'], prev['inv'], 2,
                '🔴 Dr%s/Cr1403:存货增量必须=0(成本码进存货、与原材料流出净抵)' % code)
            self.assertAlmostEqual(
                s['oc'], prev['oc'], 2,
                '🔴 Dr%s/Cr1403:营业成本增量必须=0(摘出成本码,不当期费用化)' % code)
            self.assertAlmostEqual(s['assets'], s['tle'], 2,
                                   '🔴 Dr%s:30=53 必须成立(缺权益那处摘会破差6000)' % code)
            self.assertFalse(nonneg(), 'Dr%s:存货非负,不得有 nonneg 破口' % code)
            prev = s
        # 对照组:Dr1403/Cr2202 → 存货 +6000、30=53 不破
        post(a1403, a2202)
        s = snapshot()
        self.assertAlmostEqual(s['inv'] - prev['inv'], 6000.0, 2,
                               '对照:Dr1403/Cr2202 → 存货 +6000')
        self.assertAlmostEqual(s['assets'], s['tle'], 2, '对照:30=53 不破')

    def test_v7b_nonneg_guards_unfixed_5401(self):
        """🔴 R39-T1-a:nonneg 正向回归的【活体】加固。R38-T1 只 backport 了 5001/5101/5201;
        5401-5403(建造合同)仍【未修】(已知偏离)。Dr5401/Cr1403 6000 → 5401 未进存货口径、
        仍被 PL 5\\(53) 吃 → 存货变负 → nonneg 断言必须【响】。这是 T1 修法【覆盖不到】的负存货
        成因,守住兜底不被静默拆(synthetic 的 test_crossfoot_nonneg_inventory 验规则本身,此处
        验【真实未修成因下活体触发】)。"""
        A = self.company_large
        if not A:
            self.skipTest('no cn_large_bis company')
        self.env['suite.cn.coa.report.override']._apply_all()
        self.env.invalidate_all()

        def acc(code):
            return self.Account.with_company(A).with_context(active_test=False).search(
                [('code', '=', code), ('company_ids', 'in', A.id)], limit=1)
        a5401, a1403 = acc('5401'), acc('1403')
        if not (a5401 and a1403):
            self.skipTest('5401/1403 缺,cn_large_bis 科目不全')
        bs = self.env.ref('l10n_cn_reports.l10n_cn_asbe_bs')
        form = self.env['suite.cn.statement.form'].search(
            [('report_id', '=', bs.id)], limit=1)
        if not form:
            self.skipTest('no asbe bs form')
        journal = self.env['account.journal'].with_company(A).search(
            [('company_id', '=', A.id), ('type', '=', 'general')], limit=1)
        mv = self.env['account.move'].with_company(A).create({
            'move_type': 'entry', 'journal_id': journal.id, 'date': '2026-06-30',
            'line_ids': [
                Command.create({'account_id': a5401.id, 'debit': 6000, 'credit': 0, 'name': 't'}),
                Command.create({'account_id': a1403.id, 'debit': 0, 'credit': 6000, 'name': 't'})]})
        mv.action_post()
        self.env.invalidate_all()
        rep = bs.with_company(A).with_context(allowed_company_ids=[A.id])
        data = rep._cn_prepare(form, rep.get_options({}))
        nn = [b for b in rep._cn_crossfoot_breaks(form, data)
              if len(b) > 6 and b[6] == 'nonneg']
        self.assertTrue(
            nn, '🔴 5401(T1 未修)造负存货 → nonneg 必须响(兜底未被拆);got %s'
            % rep._cn_crossfoot_breaks(form, data))

    # ------------------------------------- 🔴 T1(R34) E7 基线漂移哨兵
    def test_e7_baseline_drift(self):
        """🔴 R34-T1:逐条断言官方当前公式 == 基线常量(未覆盖态)或 == 我方新值(已覆盖态);
        既非基线亦非新值 = 官方 patch/20.0 改了公式,基线成历史文物 → 红灯。

        副产品=项目档 §8 补查 V-1(ASSBE 两报表 v20 改了什么公式)自动化:官方一改,本测试
        直接报出是哪条 line/label。哨兵有效性(改一条官方值→变红)由 _apply_formula 的 ERROR+
        drift 登记路径守，此处守【基线常量抄写正确】= 当前库全绿。"""
        n_formula = 0
        for line_xmlid, kind, expected, new, labels in REPORT_OVERRIDES:
            line = self.env.ref(line_xmlid, raise_if_not_found=False)
            self.assertTrue(line, '基线目标 %s 应存在' % line_xmlid)
            if kind == 'formula':
                exprs = line.expression_ids.filtered(
                    lambda e: e.engine == 'account_codes'
                    and (labels is None or e.label in labels))
                self.assertTrue(exprs, '%s 应有 account_codes 表达式' % line_xmlid)
                for expr in exprs:
                    n_formula += 1
                    self.assertIn(
                        expr.formula or '', (expected, new),
                        '🔴 E7 基线漂移:%s[%s] 官方现公式 %r 既非基线 %r 亦非我方新值 %r'
                        '——官方改了此公式,基线常量待更新(V-1)。'
                        % (line_xmlid, expr.label, expr.formula, expected, new))
            elif kind == 'hide_if_zero':
                # 基线 = 存在且(未覆盖时)hide_if_zero 可为 False;已覆盖为 True。两态皆合法。
                self.assertIn(line.hide_if_zero, (False, True))
        # 台账条数固化(R38-T1 阶段B 后 = 8:ASSBE 5 + ASBE 3):
        #   formula 类 7 = ASSBE 4(行11/行12/PL balance + prev_year balance_domain)
        #                + ASBE 3(存货/营业成本 balance + prev_year balance_domain);
        #   hide_if_zero 类 1(行26)。合计 8。
        # 我方 bal_begin/ytd 5 条(ASSBE 3 + ASBE 2)已回归 statement 源头 XML,不在本模块覆盖面。
        self.assertEqual(n_formula, 7,
                         'formula 覆盖表达式应 7 条(ASSBE 4 + ASBE 3);我方 bal_begin/ytd 由 '
                         'statement 源头 XML 自产,不由本模块覆盖')

    def test_e7_drift_sentinel_fires(self):
        """哨兵有效性:人为把官方一条公式改成第三值 → _apply_all 登记 drift + 不覆盖。"""
        Ov = self.env['suite.cn.coa.report.override']
        Drift = self.env['suite.cn.coa.baseline.drift']
        wip = self.env.ref('l10n_cn_reports.l10n_cn_assbe_bs_cns_wip')
        expr = wip.expression_ids.filtered(
            lambda e: e.engine == 'account_codes' and e.label == 'balance')[:1]
        expr.formula = '9999'   # 冒充官方改了公式(既非基线 1406 亦非新值 4001)
        Ov._apply_all()
        self.assertEqual(expr.formula, '9999', '漂移条【不得被覆盖】')
        self.assertTrue(
            Drift.search([('line_xmlid', 'like', 'l10n_cn_assbe_bs_cns_wip'),
                          ('expr_label', '=', 'balance')]),
            '应登记一条 wip/balance 基线漂移')

    # ---------------------------------------- R37-T3 覆盖漏放自检 (b+a)
    def test_t3_override_health_check(self):
        """R37-T3:test_e7_baseline_drift 断言「官方原值没被改过」,本测试补反向那半——
        「官方几条当前已是覆盖后的新值」。fresh 库【不误报】(刚 apply 恒空);人为把一条官方
        覆盖回退原值(模拟某版改了这几条却忘带 migration → B-67 不重放)→ (a) 必抓, (b) 登记。

        🔴 本测试只能验【不误报 + 逻辑正确】;真正的「升级路径漏放」只在既有客户库、发过第二版
        之后才显形,fresh CI 无法复现那条路径(方法之所以【只读、任意库可调】而非纯单测)。"""
        Ov = self.env['suite.cn.coa.report.override']
        Drift = self.env['suite.cn.coa.baseline.drift']
        Ov._apply_all()   # 末尾已含自检 (b);此后覆盖全生效
        self.assertEqual(Ov._check_overrides_effective(), [],
                         '刚 apply 后覆盖全生效,自检必须为空(fresh 库不误报)')
        # 模拟漏放:把 wip/balance 回退原值 1406(绕过 _apply_all,冒充某版没重放)
        wip = self.env.ref('l10n_cn_reports.l10n_cn_assbe_bs_cns_wip')
        expr = wip.expression_ids.filtered(
            lambda e: e.engine == 'account_codes' and e.label == 'balance')[:1]
        expr.formula = '1406'
        missing = Ov._check_overrides_effective()
        hit = [m for m in missing
               if 'cns_wip' in m['line_xmlid'] and m['label'] == 'balance']
        self.assertTrue(hit, '回退到原值必须被判漏放;got %s' % missing)
        self.assertEqual(hit[0]['reason'], '漏放(仍为原值)')
        self.assertEqual((hit[0]['current'], hit[0]['want']), ('1406', '4001'))
        # (b) 登记漂移台账(与 E7 同表,用户本就在看)
        Ov._assert_overrides_effective(origin='test')
        self.assertTrue(
            Drift.search([('line_xmlid', 'like', 'cns_wip'),
                          ('expr_label', '=', 'balance'),
                          ('baseline', 'like', 'R37-T3')]),
            '漏放须登记漂移台账(baseline 带 R37-T3 标记)')

    # ----------------------------------------------- V1/V2 科目卸载不动
    def test_v1_v2_accounts_survive_restore(self):
        """V1/V2:发行(+记分录)后走 formula 还原,发行的科目【留库】(§4.9.1 无 xmlid)。

        🔴 R46:被测对象由官方 1122 改为【我方创建】科目 2221.51。原用例用 1122 测「发行
        科目留库」——但 1122 是【官方账户】、`_restore_all` 从不碰 account.account,三条断言
        (存在/无我方 xmlid/还原后仍在)【恒真】,打桩 _publish/_apply_all/_restore_all 全绿=
        空绿(R46 实测)。改用我方 created 科目 + 正向哨兵后:发行空转 → 哨兵红。"""
        if not self.company:
            self.skipTest('no cn-chart company')
        self.publisher._publish(self.company, taxpayer='common')
        # 正向哨兵(惯例30):2221.51 确由我方【发行创建】(created 台账),否则下方留库断言空转。
        self.assertTrue(self.Ledger.search_count(
            [('company_id', '=', self.company.id), ('code', '=', '2221.51'),
             ('action', '=', 'created')]),
            '哨兵:2221.51 须为我方发行创建(created 台账);为空说明发行空转,本用例本会空绿')
        acc = self._acc('2221.51')   # 我方号段、active=False → _acc 用 active_test=False 可取
        self.assertTrue(acc, '我方发行创建的科目应在库')
        # 发行的科目不带本模块 ir.model.data(卸载器看不见 → 留库)
        imd = self.env['ir.model.data'].search([
            ('model', '=', 'account.account'), ('res_id', '=', acc.id),
            ('module', '=', 'suite_cn_coa')])
        self.assertFalse(imd, '发行科目不得挂 suite_cn_coa xmlid(§4.8.3)')
        # 还原报表 formula 后科目仍在
        self.env['suite.cn.coa.report.override']._apply_all()
        self.env['suite.cn.coa.report.override']._restore_all()
        self.assertTrue(self._acc('2221.51'), '还原后我方发行科目仍在')
