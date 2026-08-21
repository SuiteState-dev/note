# -*- coding: utf-8 -*-
"""R53-T1 —— 数量金额式明细分类账 验收判据（绝对终态，惯例19；计数类两数分列，惯例17）。

🔴 换取数源：本件从 `stock.move`（数量+金额）取数，【不挂 account.move.line】。夹具用【真实
入库/出库单】（button_validate → 计价落账），非手写数字——这样判据11「金额跨源核对」才是两条
【真正独立】的库表路径（stock.move vs account.move.line），而非 present-by-copy（惯例24）。

对账设计（〇节）——
  金额维：判据11「金额跨源核对」。本报表读 stock.move.value、总账读 account.move.line.balance，
    两张【不同的库表】⇒ 真互证雏形（【不叫「互证」也不叫「跨路径差量检验」】——那是共模）。
    成立前提：估值科目 GL 分录确由 stock 计价路径生成（库位估值科目已配、该科目无手工旁路
    分录）；夹具保证估值科目只有 stock 分录。不一致即【立即停下回报】。
  数量维：【无对账路径】（惯例32：说「没有」也举证）——aml.quantity 恒占位 1.0（R53 探针
    verified）⇒ 会计侧无第二数量源。数量维只有报表内部自洽（判据1/3），无跨源对账。

判据（12 条，全部机械可判定；校验类 1/2/3/4/5/6/11 自带「注入→检出」）——
  1 数量逐笔滚动；2 金额逐笔滚动；3 结存单价==余额金额÷余额数量；
  4 发生额单价==本期金额÷本期数量 且 与结存单价【两个值】；5 方向由金额定；
  6 单价留空不除零；7 跨年本年累计归零留空；8 跨年余额数量不归零；
  9 零发生（单边）期仍出本期合计+本年累计两行；10 合计行(跨年出/单年不出)；
  11 金额跨源核对（vs 总账）；12 非存货科目边界（回报实际形态）。
"""
import copy
import datetime

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestQuantityLedger(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.country_id = cls.env.ref('base.cn').id
        cls.currency = cls.company.currency_id
        cls.report = cls.env.ref('suite_cn_statement.cn_quantity_ledger')
        cls.handler = cls.env['suite.cn.quantity.ledger.report.handler']
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', cls.company.id)], limit=1)
        if not cls.company.account_stock_journal_id:
            cls.company.account_stock_journal_id = cls.journal.id

        A = cls.env['account.account']

        def acc(code, name, atype):
            return A.create({'name': name, 'code': code, 'account_type': atype})

        cls.inv = acc('1405', 'QL库存商品', 'asset_current')      # 估值科目（借方）
        cls.inp = acc('1402', 'QL在途物资', 'asset_current')      # 供应商库位（入库对方）
        cls.cogs = acc('6401', 'QL主营成本', 'expense')           # 客户库位（出库对方）
        cls.ns1 = acc('1001', 'QL库存现金', 'asset_cash')         # 非存货（判据12）
        cls.ns2 = acc('2202', 'QL应付账款', 'liability_payable')  # 非存货对方

        # 品类 real_time + 标准成本，估值科目/存货日记账。
        cls.cat = cls.env['product.category'].create({'name': 'QLCat'})
        cls.cat.write({'property_valuation': 'real_time', 'property_cost_method': 'standard'})
        cls.cat.with_company(cls.company).property_stock_valuation_account_id = cls.inv.id
        cls.cat.with_company(cls.company).property_stock_journal = cls.journal.id

        # 🔴 v19 落账门槛：库位估值科目（供应商→入库对方、客户→出库对方）。
        cls.sup = cls.env.ref('stock.stock_location_suppliers')
        cls.stk = cls.env.ref('stock.stock_location_stock')
        cls.cust = cls.env.ref('stock.stock_location_customers')
        cls.sup.valuation_account_id = cls.inp.id
        cls.cust.valuation_account_id = cls.cogs.id
        cls.wh = cls.env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)

        def prod(name, cost):
            return cls.env['product.product'].create({
                'name': name, 'is_storable': True, 'categ_id': cls.cat.id,
                'standard_price': cost})

        cls.env.flush_all()
        cls.cat.invalidate_recordset()
        cls.p1 = prod('QL甲', 7.0)      # 主料：多期 + 出入库（判据1-4,9,11）
        cls.p2 = prod('QL乙', 0.0)      # 零成本：数量非零金额零（判据5,6）
        cls.p3 = prod('QL丙', 3.0)      # 跨年（判据7,8,10）
        # 🔴 fail-fast：确认三产品的估值科目【确】落在 1405（否则夹具无效、判据11 假绿）。
        assert cls.p1._get_product_accounts().get('stock_valuation') == cls.inv, \
            'QL甲 估值科目未落 1405，夹具无效：%s' % cls.p1._get_product_accounts().get('stock_valuation')

        # ── 造数（真实入库/出库单，button_validate 计价落账）──
        cls.p1_open = cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p1, 10.0, datetime.date(2025, 12, 15))
        cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p1, 20.0, datetime.date(2026, 1, 10))
        cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p1, 5.0, datetime.date(2026, 1, 20))
        cls._mv(cls.wh.out_type_id, cls.stk, cls.cust, cls.p1, 8.0, datetime.date(2026, 3, 15))
        # 零成本：qty>0、value=0
        cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p2, 100.0, datetime.date(2026, 2, 5))
        # 跨年：Dec2025 + Jan2026（标准成本 3.0）
        cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p3, 100.0, datetime.date(2025, 12, 10))
        cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p3, 20.0, datetime.date(2026, 1, 15))

        # 🔴 P4（FIFO，估值科目仍 1405）：两期不同单位成本 ⇒ 本期均价≠结存均价，判据4 的两口径
        # 【实证可分】（惯例17③口径不同就得拆；标准成本恒定时二者数值相等易被误判为「串」）。
        cls.cat_fifo = cls.env['product.category'].create({'name': 'QLCatFifo'})
        cls.cat_fifo.write({'property_valuation': 'real_time', 'property_cost_method': 'fifo'})
        cls.cat_fifo.with_company(cls.company).property_stock_valuation_account_id = cls.inv.id
        cls.cat_fifo.with_company(cls.company).property_stock_journal = cls.journal.id
        cls.env.flush_all()
        cls.cat_fifo.invalidate_recordset()
        cls.p4 = cls.env['product.product'].create({
            'name': 'QL丁', 'is_storable': True, 'categ_id': cls.cat_fifo.id, 'standard_price': 5.0})
        cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p4, 10.0, datetime.date(2026, 1, 10))  # 10@5=50
        cls.p4.standard_price = 9.0
        cls.env.flush_all()
        cls._mv(cls.wh.in_type_id, cls.sup, cls.stk, cls.p4, 10.0, datetime.date(2026, 2, 10))  # 10@9=90

        # 非存货科目：手工凭证（无 stock.move）——判据12。🔴 不碰估值科目 1405（保金额跨源核对成立）。
        mv = cls.env['account.move'].create({
            'move_type': 'entry', 'journal_id': cls.journal.id, 'date': '2026-04-01',
            'line_ids': [(0, 0, {'account_id': cls.ns1.id, 'debit': 500.0, 'credit': 0.0, 'name': '现金'}),
                         (0, 0, {'account_id': cls.ns2.id, 'debit': 0.0, 'credit': 500.0, 'name': '应付'})]})
        mv.action_post()

        cls.env.flush_all()

        # 🔴 pin 报表到【本公司】（多公司 DB：CN 报表默认可能选到别的 CN 公司 id，而夹具落在
        # env.company）——用 allowed_company_ids 固定，否则估值科目按错公司解析成默认 1403。
        cls._rep = cls.report.with_context(allowed_company_ids=[cls.company.id])
        cls.options = cls._rep.get_options({
            'selected_variant_id': cls.report.id, 'unfold_all': True,
            'date': {'mode': 'range', 'date_from': '2026-01-01', 'date_to': '2026-12-31'}})
        cls.data = cls.handler._cn_ql_compute(cls._rep, cls.options)

        cls.options_cy = cls._rep.get_options({
            'selected_variant_id': cls.report.id, 'unfold_all': True,
            'date': {'mode': 'range', 'date_from': '2025-12-01', 'date_to': '2026-01-31'}})
        cls.data_cy = cls.handler._cn_ql_compute(cls._rep, cls.options_cy)

    @classmethod
    def _mv(cls, ptype, src, dst, product, qty, date):
        """真实入库/出库：建单→确认→置数→validate（force_period_date 对齐会计分录日期）→
        回写 stock.move.date 到目标日（使 QL/GL 期间对齐）。返回 move。"""
        pick = cls.env['stock.picking'].create({
            'picking_type_id': ptype.id, 'location_id': src.id, 'location_dest_id': dst.id,
            'move_ids': [(0, 0, {'product_id': product.id, 'product_uom_qty': qty,
                                 'location_id': src.id, 'location_dest_id': dst.id})]})
        pick.action_confirm()
        m = pick.move_ids
        m.quantity = qty
        m.picked = True
        pick.with_context(force_period_date=date).button_validate()
        m = m.exists()
        m.write({'date': datetime.datetime(date.year, date.month, date.day, 12, 0)})
        return m

    # ------------------------------------------------------------- helpers
    def _sec(self, data, product_name):
        for s in data['sections']:
            if s['product_name'] == product_name or product_name in s['product_name']:
                return s
        self.fail('段 %s 不在结果中（现有 %s）'
                  % (product_name, [s['product_name'] for s in data['sections']]))

    # 判据1：数量逐笔滚动。参与=明细行数。
    def _qty_rolling(self, data):
        n = bad = 0
        for s in data['sections']:
            prev = s['opening']['qty']
            for p in s['periods']:
                for ln in p['lines']:
                    n += 1
                    step = (ln['d_qty'] or 0.0) - (ln['c_qty'] or 0.0)
                    if abs(ln['bal_qty'] - (prev + step)) > 0.005:
                        bad += 1
                    prev = ln['bal_qty']
        return n, bad

    # 判据2：金额逐笔滚动。参与=明细行数。
    def _val_rolling(self, data):
        n = bad = 0
        for s in data['sections']:
            prev = s['opening']['value']
            for p in s['periods']:
                for ln in p['lines']:
                    n += 1
                    step = (ln['d_amt'] or 0.0) - (ln['c_amt'] or 0.0)
                    if abs(ln['bal_value'] - (prev + step)) > 0.005:
                        bad += 1
                    prev = ln['bal_value']
        return n, bad

    # 判据3：结存单价==余额金额÷余额数量（2dp）。参与=有余额单价的行。
    def _bal_price_ok(self, data):
        n = bad = 0
        for s in data['sections']:
            for p in s['periods']:
                for ln in p['lines']:
                    if ln['bal_price'] is None:
                        continue
                    n += 1
                    want = round(ln['bal_value'] / ln['bal_qty'], 2)
                    if abs(round(ln['bal_price'], 2) - want) > 0.005:
                        bad += 1
        return n, bad

    # 判据4：发生额单价==本期金额÷本期数量；且与结存单价是两个值。参与=本期合计行；eq=两值相等的行。
    def _current_price_ok(self, data):
        n = bad = eq = 0
        for s in data['sections']:
            for p in s['periods']:
                cu = p['current']
                # 借方或贷方任一有发生额单价
                for qk, ak, pk in [('d_qty', 'd_amt', 'd_price'), ('c_qty', 'c_amt', 'c_price')]:
                    if cu[pk] is None:
                        continue
                    n += 1
                    want = round((cu[ak] or 0.0) / (cu[qk] or 1.0), 2)
                    if abs(round(cu[pk], 2) - want) > 0.005:
                        bad += 1
                    if cu['bal_price'] is not None \
                            and abs(round(cu[pk], 2) - round(cu['bal_price'], 2)) < 0.005:
                        eq += 1
        return n, bad, eq

    # 判据11：金额跨源核对（QL 按估值科目聚合 vs 总账本期合计）。参与=对数。
    # 🔴 只核【我方隔离科目 1405】——DB 既有存货数据（存货调整等）落在别的估值科目，不入本核。
    def _cross_source(self, data, gl_map, only_code='1405'):
        agg = {}   # (acct_code, label) -> [借金额, 贷金额]
        for s in data['sections']:
            if only_code and s['acct_code'] != only_code:
                continue
            for p in s['periods']:
                k = (s['acct_code'], p['label'])
                a = agg.setdefault(k, [0.0, 0.0])
                a[0] += p['current']['d_amt'] or 0.0
                a[1] += p['current']['c_amt'] or 0.0
        n = bad = 0
        for k, (d, c) in agg.items():
            if k not in gl_map:
                continue
            n += 1
            gd, gc = gl_map[k]
            if abs(d - gd) > 0.005 or abs(c - gc) > 0.005:
                bad += 1
        return n, bad

    def _gl_current_map(self, date_from, date_to):
        gl = self.env['suite.cn.general.ledger.report.handler']
        glr = self.env.ref('suite_cn_statement.cn_general_ledger').with_context(
            allowed_company_ids=[self.company.id])   # pin 同 QL，避免落到别的 CN 公司
        gopts = glr.get_options({
            'selected_variant_id': glr.id, 'unfold_all': True,
            'date': {'mode': 'range', 'date_from': date_from, 'date_to': date_to}})
        gdata = gl._cn_gl_compute(glr, gopts)
        m = {}
        for s in gdata['sections']:
            for p in s['periods']:
                m[(s['code'], p['label'])] = (p['current']['debit'], p['current']['credit'])
        return m

    # =============================================================== 判据1
    def test_j1_qty_rolling(self):
        n, bad = self._qty_rolling(self.data)
        self.assertGreater(n, 0, '哨兵：参与明细行数须>0')
        self.assertEqual(bad, 0, '判据1：数量逐笔滚动（参与 %d / 不成立 %d）' % (n, bad))

    def test_j1_qty_inject_detect(self):
        t = copy.deepcopy(self.data)
        self._sec(t, 'QL甲')['periods'][0]['lines'][1]['bal_qty'] += 99.0
        n, bad = self._qty_rolling(t)
        self.assertGreaterEqual(bad, 1, '🔴 数量滚动校验未检出注入')

    # =============================================================== 判据2
    def test_j2_val_rolling(self):
        n, bad = self._val_rolling(self.data)
        self.assertGreater(n, 0, '哨兵：参与明细行数须>0')
        self.assertEqual(bad, 0, '判据2：金额逐笔滚动（参与 %d / 不成立 %d）' % (n, bad))

    def test_j2_val_inject_detect(self):
        t = copy.deepcopy(self.data)
        self._sec(t, 'QL甲')['periods'][0]['lines'][0]['bal_value'] += 50.0
        n, bad = self._val_rolling(t)
        self.assertGreaterEqual(bad, 1, '🔴 金额滚动校验未检出注入')

    # =============================================================== 判据3
    def test_j3_bal_price(self):
        n, bad = self._bal_price_ok(self.data)
        self.assertGreater(n, 0, '哨兵：有余额单价的行须>0')
        self.assertEqual(bad, 0, '判据3：结存单价==余额金额÷余额数量（参与 %d / 不成立 %d）' % (n, bad))

    def test_j3_bal_price_inject_detect(self):
        t = copy.deepcopy(self.data)
        for p in self._sec(t, 'QL甲')['periods']:
            for ln in p['lines']:
                if ln['bal_price'] is not None:
                    ln['bal_price'] += 5.0
                    break
        n, bad = self._bal_price_ok(t)
        self.assertGreaterEqual(bad, 1, '🔴 结存单价校验未检出注入')

    # =============================================================== 判据4
    def test_j4_current_price_two_values(self):
        n, bad, eq = self._current_price_ok(self.data)
        self.assertGreater(n, 0, '哨兵：本期发生额单价行须>0')
        self.assertEqual(bad, 0, '判据4：发生额单价==本期金额÷本期数量（参与 %d / 不成立 %d）' % (n, bad))
        # 🔴 两口径【实证可分】：丁（FIFO）二月 本期均价 9.00（90/10）≠ 结存均价 7.00（140/20）。
        # ⇒ 发生额单价 与 结存单价 是【两个不同口径】，非串一个值（惯例17③已拆）。
        feb = self._sec(self.data, 'QL丁')['periods'][1]['current']
        self.assertAlmostEqual(feb['d_price'], 9.0, places=2, msg='丁二月本期均价 90/10=9')
        self.assertAlmostEqual(feb['bal_price'], 7.0, places=2, msg='丁二月结存均价 140/20=7')
        self.assertNotAlmostEqual(feb['d_price'], feb['bal_price'], places=2,
                                  msg='🔴 发生额单价≠结存单价 ⇒ 确是两个口径')
        self.assertLess(eq, n, '🔴 两值并非【恒相等】（存在不等期）⇒ 未串（惯例17③）')
        # 甲 一月：本期均价 175/25=7.00
        jan = self._sec(self.data, 'QL甲')['periods'][0]['current']
        self.assertAlmostEqual(jan['d_price'], 7.0, places=2, msg='甲一月本期均价 175/25')

    def test_j4_current_price_inject_detect(self):
        t = copy.deepcopy(self.data)
        self._sec(t, 'QL甲')['periods'][0]['current']['d_price'] += 3.0
        n, bad, eq = self._current_price_ok(t)
        self.assertGreaterEqual(bad, 1, '🔴 发生额单价校验未检出注入')

    # =============================================================== 判据5
    def _dir_by_amount(self, data):
        """方向须由【金额】定：value>0→借、<0→贷、==0→平（与数量无关）。
        🔴 参与口径 = 【方向判定格数】= 每段(期初余额行 + 各期本期合计行) 的方向格，与判据1/2
        的「明细行数」、判据3/4 的「有单价的格数」是【不同口径】（惯例17：不同数因不同口径，
        非几格同数）。本夹具 = Σ段(1 期初 + 期数) 里 value 非 None 的格。"""
        n = bad = 0
        for s in data['sections']:
            rows = [s['opening']] + [p['current'] for p in s['periods']]
            for blk in rows:
                v = blk.get('value', blk.get('bal_value'))
                if v is None:
                    continue
                n += 1
                want = '平' if abs(v) < 1e-9 else ('借' if v > 0 else '贷')
                if blk['direction'] != want:
                    bad += 1
        return n, bad

    def test_j5_direction_by_amount(self):
        n, bad = self._dir_by_amount(self.data)
        self.assertGreater(n, 0, '哨兵：参与余额格须>0')
        self.assertEqual(bad, 0, '判据5：方向由金额定（参与 %d / 判成非「平」等错向 %d，期望 0）' % (n, bad))
        # 乙：100 件、金额 0 ⇒ 余额数量非零、方向「平」（🔴 方向与数量无关）。
        yi = self._sec(self.data, 'QL乙')['periods'][0]['current']
        self.assertGreater(yi['bal_qty'], 0, '乙 结存数量须>0')
        self.assertEqual(yi['direction'], '平', '🔴 数量非零、金额零 ⇒ 方向「平」（由金额定）')

    def test_j5_direction_inject_detect(self):
        t = copy.deepcopy(self.data)
        self._sec(t, 'QL乙')['periods'][0]['current']['direction'] = '借'
        n, bad = self._dir_by_amount(t)
        self.assertGreaterEqual(bad, 1, '🔴 方向由金额定校验未检出注入（金额零却判「借」）')

    # =============================================================== 判据6
    def test_j6_price_blank_no_div_zero(self):
        """乙：余额数量非零、金额空 ⇒ 单价栏渲染为空字符串（不 0.00、不除零异常）。"""
        yi = self._sec(self.data, 'QL乙')['periods'][0]['current']
        self.assertGreater(yi['bal_qty'], 0, '乙 结存数量须>0')
        self.assertIsNone(yi['bal_price'], '🔴 余额金额空 ⇒ 结存单价须 None（不除零）')
        # 渲染层：单价格必须是空（write_blank），不得出现 0.00 数字
        rec = self._render()
        # 乙段结存单价那格应为 blank —— 检查渲染没有把 None 写成 0.0
        leaked = sum(1 for v in rec.numbers if abs(v) < 1e-9)
        self.assertEqual(leaked, 0, '判据6：单价/金额留空须不显 0.00（出现 0.00 条数 %d，期望 0）' % leaked)

    def test_j6_zero_leak_inject_detect(self):
        rec = _RecWS()
        rec.write_number(0, 0, 0.0, None)
        leaked = sum(1 for v in rec.numbers if abs(v) < 1e-9)
        self.assertGreaterEqual(leaked, 1, '🔴 0.00 泄漏检测器未检出注入')

    # =============================================================== 判据7
    def test_j7_ytd_reset_blank_cross_year(self):
        """跨年：丙 2026-01 本年累计【重置】（==Jan-only，非 Dec+Jan）；零列留空非 0.00。"""
        bing = self._sec(self.data_cy, 'QL丙')
        self.assertGreaterEqual(len(bing['periods']), 2, '丙 应有 2025-12 与 2026-01 两期')
        p_dec, p_jan = bing['periods'][0], bing['periods'][1]
        self.assertEqual(p_dec['label'], '202512')
        self.assertEqual(p_jan['label'], '202601')
        # 🔴 60 的来源：`ytd['d_amt']` = 本年累计【借方发生金额】。FY2026 首期(Jan) 重置后只含
        # Jan 入库（20 件 @ 标准 3.0 = 60）；因是本财年首期，本年累计借 == 本期借（60）。
        # 若错误累进上年 Dec(300) 则为 360 —— 反证。同期本期借方发生额亦 60（首期二者相等）。
        self.assertAlmostEqual(p_jan['current']['d_amt'], 60.0, places=2,
                               msg='Jan 本期借方发生金额 20×3=60（60 的来源=本期发生额）')
        # FY2025 累计 = Dec 100/300；FY2026 累计【重置】= Jan 20/60（非 120/360）
        self.assertAlmostEqual(p_dec['ytd']['d_amt'], 300.0, places=2, msg='FY2025 累计金额 300')
        self.assertAlmostEqual(p_jan['ytd']['d_amt'], 60.0, places=2,
                               msg='🔴 跨财年本年累计【重置】为 Jan-only 60（==本期发生额），非 360')
        self.assertAlmostEqual(p_jan['ytd']['d_qty'], 20.0, places=2, msg='🔴 累计数量亦重置为 20')
        # 贷方本年累计为 0 ⇒ 留空（None），非 0.00
        self.assertIsNone(p_jan['ytd']['c_amt'], '🔴 零本年累计列须留空 None（非 0.00）')

    def test_j7_ytd_reset_inject_detect(self):
        """注入→检出：模拟「跨年不重置」——把 Jan 累计写成 Dec+Jan。"""
        p_jan_ytd = self._sec(self.data_cy, 'QL丙')['periods'][1]['ytd']['d_amt']
        no_reset = 300.0 + 60.0
        # 检测器：断言真实值 != 不重置值
        self.assertNotAlmostEqual(p_jan_ytd, no_reset, places=2,
                                  msg='🔴 若累计=360 即未重置（本例应为 60）')

    # =============================================================== 判据8
    def test_j8_balance_qty_not_reset_cross_year(self):
        """跨年：丙 2026-01 余额数量【不重置】= Dec100 + Jan20 = 120。"""
        p_jan = self._sec(self.data_cy, 'QL丙')['periods'][1]['current']
        self.assertAlmostEqual(p_jan['bal_qty'], 120.0, places=2,
                               msg='🔴 跨年余额数量不归零：100+20=120')
        self.assertAlmostEqual(p_jan['bal_value'], 360.0, places=2, msg='余额金额 300+60=360')

    def test_j8_balance_inject_detect(self):
        p_jan_qty = self._sec(self.data_cy, 'QL丙')['periods'][1]['current']['bal_qty']
        self.assertNotAlmostEqual(p_jan_qty, 20.0, places=2,
                                  msg='🔴 若余额数量=20 即被错误重置（应 120）')

    # =============================================================== 判据9
    def test_j9_zero_side_period_two_summary_rows(self):
        """零发生（单边）期仍出【本期合计+本年累计】两行。参与=期次 / 缺行数（期望 0）。"""
        rows_by_sec = self._rep._cn_ql_prepare(self.options)['sections']
        n = missing = 0
        for sec_c, sec_p in zip(self.data['sections'], rows_by_sec):
            for p in sec_c['periods']:
                n += 1
                names = [r['summary'] for r in sec_p['rows']]
                if '本期合计' not in names or '本年累计' not in names:
                    missing += 1
        self.assertGreater(n, 0, '哨兵：参与期次须>0')
        self.assertEqual(missing, 0, '判据9：每期出本期合计+本年累计两行（参与 %d / 缺行 %d）' % (n, missing))
        # 甲一月只有借方发生（贷方为零）——正是「单边零发生」期，仍出两行
        jan = self._sec(self.data, 'QL甲')['periods'][0]['current']
        self.assertIsNone(jan['c_amt'], '甲一月贷方发生须为空（单边零发生）')

    # =============================================================== 判据10
    def test_j10_grand_total_cross_year_only(self):
        """合计行：跨年区间【出】且 == 各期本期之和；单年区间【不出】。"""
        # 跨年件：丙有合计行、值==Σ本期
        self.assertTrue(self.data_cy['is_cross_year'], '2025-12..2026-01 应判为跨年')
        bing = self._sec(self.data_cy, 'QL丙')
        self.assertIsNotNone(bing['total_row'], '🔴 跨年段须出【合计】行')
        want_d = sum(p['current']['d_amt'] or 0.0 for p in bing['periods'])
        self.assertAlmostEqual(bing['total_row']['d_amt'], want_d, places=2,
                               msg='合计借方金额==各期本期之和')
        # 单年件：无任何合计行
        cy_participate = sum(1 for s in self.data_cy['sections'] if s['total_row'])
        single_leak = sum(1 for s in self.data['sections'] if s['total_row'])
        self.assertGreater(cy_participate, 0, '哨兵：跨年件参与段须>0')
        self.assertEqual(single_leak, 0,
                         '判据10：单年区间出现「合计」行的条数须【确认为 0】（跨年件 %d / 单年泄漏 %d）'
                         % (cy_participate, single_leak))

    # =============================================================== 判据11
    def test_j11_cross_source_amount(self):
        gl_map = self._gl_current_map('2026-01-01', '2026-12-31')
        n, bad = self._cross_source(self.data, gl_map)
        self.assertGreater(n, 0, '哨兵：金额跨源对数须>0')
        self.assertEqual(bad, 0,
                         '🔴 判据11：数量金额式(stock.move) 与 总账(aml) 金额不一致'
                         '（参与 %d / 不一致 %d）——金额跨源核对，不一致即立即停下' % (n, bad))

    def test_j11_inject_account_side_detect(self):
        """🔴 注入落在【account 侧真实模型 account.move.line】——给估值科目 1405 补一笔【非 stock】
        手工分录（借 100，2026-03），【重算】总账（含新分录）与 QL（读 stock.move、不含它）⇒
        两库表分歧、跨源核对检出。证明的是【跨源这条链是通的】（account 变→QL 不跟→检出），不是
        「断言会响」。亦坐实诚实边界⑦：估值科目混入手工旁路分录会破坏核对（正确地报不一致）。"""
        before_map = self._gl_current_map('2026-01-01', '2026-12-31')
        n0, bad0 = self._cross_source(self.data, before_map)
        self.assertEqual(bad0, 0, '注入前须一致（%d/%d）' % (n0, bad0))
        extra = self.env['account.move'].create({
            'move_type': 'entry', 'journal_id': self.journal.id, 'date': '2026-03-20',
            'line_ids': [(0, 0, {'account_id': self.inv.id, 'debit': 100.0, 'credit': 0.0, 'name': '旁路'}),
                         (0, 0, {'account_id': self.ns2.id, 'debit': 0.0, 'credit': 100.0, 'name': '旁路对方'})]})
        extra.action_post()
        self.env.flush_all()
        after_map = self._gl_current_map('2026-01-01', '2026-12-31')          # 总账重算，含手工分录
        data = self.handler._cn_ql_compute(self._rep, self.options)           # QL 重算，读 stock.move（不含）
        n, bad = self._cross_source(data, after_map)
        self.assertGreater(n, 0, '哨兵：参与对数须>0')
        self.assertGreaterEqual(bad, 1,
                                '🔴 account 侧旁路分录未被跨源核对检出（注入 account.move.line.balance@1405）')

    def test_j11_inject_stock_side_detect(self):
        """🔴 注入落在【stock 侧真实模型 stock.move.value】——把 QL甲 一月一笔入库的 value 改大 500，
        【重算】QL（读改后的 stock.move）与总账（aml 已按旧值过账、不变）⇒ 分歧、检出。证明的是
        【stock 变→报表跟着变→与总账拉开差】（用户 ✅ 案一）。stock.move.value 是存储字段，改写
        不回溯已过账 aml ⇒ 两源真分叉。"""
        mv = self.env['stock.move'].search(
            [('product_id', '=', self.p1.id), ('state', '=', 'done'),
             ('date', '>=', '2026-01-01'), ('date', '<', '2026-02-01'),
             ('company_id', '=', self.company.id)], limit=1)
        self.assertTrue(mv, '应找到 QL甲 一月入库 move')
        mv.write({'value': mv.value + 500.0})   # 只改 stock 侧，不重过账 aml
        self.env.flush_all()
        gl_map = self._gl_current_map('2026-01-01', '2026-12-31')             # aml 仍旧值
        data = self.handler._cn_ql_compute(self._rep, self.options)          # QL 读改后 value
        n, bad = self._cross_source(data, gl_map)
        self.assertGreater(n, 0, '哨兵：参与对数须>0')
        self.assertGreaterEqual(bad, 1,
                                '🔴 stock 侧 value 改动未被跨源核对检出（注入 stock.move.value）')

    # =============================================================== 判据12
    def test_j12_nonstock_account_boundary(self):
        """🔴 非存货科目边界——回报【实际形态】：纯手工凭证科目在数量金额式里【根本不出现】
        （取数源=stock.move，非存货科目无 move ⇒ 不成段）。这是产品边界、非缺陷。"""
        codes = {s['acct_code'] for s in self.data['sections']}
        self.assertNotIn('1001', codes, '非存货 1001（现金）不应出现在数量金额式')
        self.assertNotIn('2202', codes, '非存货 2202（应付）不应出现在数量金额式')
        # 存货科目在（正向哨兵）
        self.assertIn('1405', codes, '估值科目 1405 应出现')
        # 该手工凭证确实入了账（证明「不出现」不是因为没造数）
        cash_amls = self.env['account.move.line'].search_count(
            [('account_id', '=', self.ns1.id), ('parent_state', '=', 'posted')])
        self.assertGreaterEqual(cash_amls, 1, '非存货手工凭证确已入账（边界非因缺数）')

    # =============================================================== 结构 / 渲染
    def test_sections_present(self):
        names = {s['product_name'] for s in self.data['sections']}
        for want in ('QL甲', 'QL乙', 'QL丙'):
            self.assertTrue(any(want in n for n in names), '段应含 %s（现 %s）' % (want, names))

    def test_screen_lines_structure(self):
        lines = self._rep._get_lines(self.options)
        self.assertGreater(len(lines), 0, '哨兵：屏幕行须>0')
        names = [l.get('name') for l in lines]
        self.assertTrue(any('1405' in (n or '') for n in names), '应有 1405 段头')
        self.assertTrue(any('期初余额' in (n or '') for n in names))
        self.assertTrue(any('本期合计' in (n or '') for n in names))
        self.assertTrue(any('本年累计' in (n or '') for n in names))
        self.assertFalse(any((n or '').startswith('Total ') for n in names),
                         '🔴 不应出现框架 totals_below_sections 噪声合计行')

    def _render(self, data_override=None):
        data = data_override or self._rep._cn_ql_prepare(self.options)
        rec = _RecWS()
        keys = ['title', 'meta', 'meta_r', 'hdr', 'acct', 'no', 'name', 'name_b',
                'num', 'num_b', 'empty', 'sign', 'note']
        F = {k: object() for k in keys}
        self._rep._cn_xlsx_ql(rec, F, data)
        return rec

    def test_cn_xlsx_ql_render(self):
        rec = self._render()
        joined = '\n'.join(t for t in rec.texts if isinstance(t, str))
        self.assertIn('数量金额式明细分类账', joined, '表名须在')
        self.assertIn('科目：1405', joined, '科目/产品 banner 须在')
        self.assertIn('借方发生额', joined, '三级表头借方组须在')
        self.assertIn('数量', joined)
        self.assertIn('单价', joined)
        self.assertIn('本期合计', joined)
        self.assertIn('本年累计', joined)

    def test_t2_ql_footer_company_header_blank(self):
        """T2 同款：数量金额式明细账公司名在【页脚】、表头不出（明细账载体落点）。"""
        data = self._rep._cn_ql_prepare(self.options)
        self.assertEqual(data['taxpayer_name'], '', '🔴 明细账表头不出公司名（taxpayer_name 空）')
        rec = self._render(data)
        self.assertIsNotNone(rec.footer, '页脚须被设置')
        self.assertIn('公司名称：', rec.footer, '页脚须含公司名')
        self.assertIn(data['company'], rec.footer, '页脚公司名须为本公司名')
        self.assertIn('&P', rec.footer)
        self.assertIn('&N', rec.footer)
        # 表头区（rec.texts）不得出现公司名
        header_texts = '\n'.join(t for t in rec.texts if isinstance(t, str))
        self.assertNotIn(data['company'], header_texts, '🔴 表头区不得出现公司名')


class _RecWS:
    """记录式假 worksheet：捕获文本与数字写入 + 页脚。"""
    def __init__(self):
        self.texts = []
        self.numbers = []
        self.footer = None

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

    def set_footer(self, s=None, *a, **k):
        self.footer = s
