# -*- coding: utf-8 -*-
"""R53-T1 —— 数量金额式明细分类账（换源实现）.

一张【新建】的 account.report（挂官方 General Ledger 变体），自带 custom_handler。
🔴 官方 General Ledger 记录 / 官方 account_report.py / 官方 handler 【三个都不碰】——
本 handler 只在【我方新建报表】上取数（惯例31：禁对象不禁手段；R47/R49/R51 已立同款）。

🔴 与前三件（余额表 R47/48、总账 R49/50、三栏式明细账 R51/52）的【根本不同：换取数源】。
    前三件都走 `account.move.line`（经 report._get_report_query）。数量金额式每行要给【数量】，
    R52-T3（background v32 B-80）实测：会计分录侧的数量不可用——
      · `account.move.line.quantity` 在 display_type='product' 下【恒占位 1.0】，非真实数量
        （本轮 R53 探针复核 verified：入库真实 10、出库真实 4，两腿 aml.quantity 均为 1.0）；
      · v19 已移除 `stock.valuation.layer`，估值挂 `stock.move.quantity`/`.value`。
    ⇒ 本件【不挂 account.move.line】，改从 `stock.move` 取【数量+金额】，按 product→估值科目 归集。

🔴 R53 探针对 B-80 的订正（verified，in-tx，交付要求12「与预期不符原样回报」）——
    B-80 曾断言「perpetual 下 move-done 时会计分录尚不存在」。本轮实证：这是【配置相关】、非绝对。
    v19 计价落账门槛 `stock.move._should_create_account_move()` 要求
    `location_dest_id.valuation_account_id or location_id.valuation_account_id`（估值科目 v19 挂在
    【库位】上）。默认库存/供应商/客户库位【未配】估值科目 ⇒ move-done 不落分录（B-80 原探针所见）；
    一旦按 perpetual 正式配置库位估值科目，`_action_done()` 即【同事务落账并过账】、
    `stock.move.account_move_id` 有值、估值科目 aml 金额 == `stock.move.value`（借入贷出、value 恒正）。
    ⇒ 金额维【确有第二取数源】；但那条 aml 的 quantity 仍是占位 1.0 ⇒ 数量维仍无会计侧源。

对账设计（〇节，写进 design §17.7）——
  · 金额维：`金额跨源核对`（判据11）。两条【真正独立】的库表路径：本报表读 `stock.move.value`，
    总账读 `account.move.line.balance`。⚠️ 命名【不叫「互证」也不叫「跨路径差量检验」】——R51 判据6
    那两条路径共用 aml 上游、是【共模】；本件 stock.move 与 account.move.line 是两张不同的库表
    ⇒ 是【真互证的雏形】。成立前提：估值科目的 GL 分录确由 stock 计价路径生成（库位估值科目已配、
    该科目无手工/发票旁路分录）；不成立即【立即停下回报】、不自判哪张表错。
  · 数量维：【无对账路径】（惯例32：说「没有」也须举证）。证据 = aml.quantity 恒占位 1.0（verified）
    ⇒ 会计侧无第二数量源。数量维只有【报表内部自洽】（判据1 逐笔滚动、判据3 结存单价=金额÷数量），
    【无跨源对账】——明说，不假装对上。

形态（导出件锚 佳兴 1403，observed，原件在 Safi 手上未入库）——
  每(估值科目, product)一段，段内五种行型（项目档 §4.5.23 一）：
    期初余额行（范围首日；发生额空、余额有值）；
    明细行（逐笔 stock.move，实际日期、逐笔滚动数量+金额+结存均价）；
    本期合计行（本期 借/贷 数量+金额+本期均价；余额=期末）；
    本年累计行（截至该期【本财年】累计——🔴 跨财年【重置】，余额不重置）；
    合计行（🔴 只在【跨年区间】出、单年不出，按假设 H1 实现，H2 未排除）。
  三条独有规则（三栏式上都不存在，§4.5.23 三）——
    1. 方向由【金额】定、与数量无关（余额金额 0/空 → 平，哪怕余额数量非零）；
    2. 同一行并列两个【不同口径】的单价：发生额单价=本期均价、余额单价=结存均价 —— 取数须显式分开；
    3. 单价【不做除法兜底】：分子(金额)为空或分母(数量)为零 → 整格【留空】，不出 0.00、不除零异常。
  跨年两条【独立】规则（§4.5.23 四，别合并）——
    本年累计发生额【按财年重置】（新财年首期起从 0 累加，零值留空非 0.00）；
    余额数量/金额【不重置】（连续结转）。
"""
import datetime

from odoo import models
from odoo.tools import float_is_zero


class CnQuantityLedgerReportHandler(models.AbstractModel):
    _name = 'suite.cn.quantity.ledger.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = '数量金额式明细分类账 Custom Handler'

    # ------------------------------------------------------------- 取数（换源：stock.move）
    def _cn_ql_query(self, report, options):
        """从 `stock.move` 取数（🔴 换源——非 account.move.line）。返回 (open_moves, period_moves)。
        honoring 报表 期间 + 多公司 筛选（stock 无 journal/过账 维度）。value 已是公司本位币、
        无需 _init_currency_table / flush_all 那套（B-78 是 aml 裸 SQL 专属，本件走 ORM）。"""
        companies = report.get_report_company_ids(options)
        dates = options.get('date') or {}
        date_from = dates.get('date_from')
        date_to = dates.get('date_to')
        Move = self.env['stock.move']
        base = [('state', '=', 'done'), ('company_id', 'in', companies)]
        period = Move.search(base + [('date', '>=', date_from), ('date', '<=', date_to)],
                             order='date, id')
        opening = Move.search(base + [('date', '<', date_from)]) if date_from else Move
        return opening, period

    def _cn_ql_val_account(self, product, company):
        """product 的估值科目 = `_get_product_accounts()['stock_valuation']`——🔴 与 stock 计价
        落账（`_get_account_move_line_vals`）【同一解析】，保证本报表归集科目 == GL 落账科目
        （判据11 金额跨源核对成立的前提）。无 → None（该 product 不入数量金额式，判据12 边界）。"""
        accts = product.with_company(company)._get_product_accounts()
        return accts.get('stock_valuation') or None

    def _cn_ql_price(self, amount, qty):
        """结存/本期/逐笔 单价 = 金额 ÷ 数量。🔴 独有规则3：分子为空(0)或分母为零 → 留空(None)，
        绝不 0.00、绝不除零异常。amount/qty 同号 ⇒ 单价恒正。"""
        if not amount or not qty or abs(qty) < 1e-9 or abs(amount) < 1e-9:
            return None
        return amount / qty

    def _cn_ql_dir(self, value_signed, currency):
        """🔴 独有规则1：方向由【金额】定、与数量无关。余额金额==0 → 平；>0 → 借；<0 → 贷。
        （存货为借方科目，正常结存 value>0 ⇒ 借；零值结存 ⇒ 平，哪怕数量非零。）"""
        if float_is_zero(value_signed, precision_rounding=currency.rounding):
            return '平'
        return '借' if value_signed > 0 else '贷'

    # --------------------------------------------------------- 结构化计算（同源单点）
    def _cn_ql_compute(self, report, options):
        """算一次、渲染两次（屏幕 _dynamic_lines_generator + 中式版式 XLSX）+ 供测试直取。
        每(估值科目, product)一段；数量+金额【逐笔滚动】；本年累计【按财年重置】、余额不重置；
        跨年区间补一条【合计】行（H1）。"""
        opening, period = self._cn_ql_query(report, options)
        company = self.env['suite.cn.general.ledger.report.handler']._cn_gl_company(report, options)
        currency = company.currency_id

        # 跨年判定：报表范围横跨 >1 个财年 → 出「合计」行（H1：跨年触发、与表种无关；H2 未排除）。
        dates = options.get('date') or {}
        df = self._to_date(dates.get('date_from'))
        dt = self._to_date(dates.get('date_to'))
        is_cross_year = False
        if df and dt:
            fy0 = company.compute_fiscalyear_dates(df)['date_from']
            fy1 = company.compute_fiscalyear_dates(dt)['date_from']
            is_cross_year = fy0 != fy1

        # 归集键 = (估值科目, product)。逐笔保留 SQL 的 (date, id) 顺序。
        # 🔴 估值科目按【每条 move 自己的 company】解析（property_stock_valuation_account_id
        # 是公司相关字段）——多公司下 move 的落账科目取决于 move.company_id，不能用报表首公司
        # 一刀切（否则跨公司 move 会被解析到错公司的默认估值科目）。
        def keyfn(m):
            acct = self._cn_ql_val_account(m.product_id, m.company_id or company)
            return (acct, m.product_id) if acct else None

        open_agg = {}          # key -> [qty, value]（signed：入+ 出-）
        for m in opening:
            k = keyfn(m)
            if not k:
                continue
            sign = 1.0 if m.is_in else -1.0
            agg = open_agg.setdefault(k, [0.0, 0.0])
            agg[0] += sign * m.quantity
            agg[1] += sign * m.value

        period_lines = {}      # key -> [move, ...]（已按 date,id 序）
        for m in period:
            k = keyfn(m)
            if not k:
                continue
            period_lines.setdefault(k, []).append(m)

        keys = sorted(set(open_agg) | set(period_lines),
                      key=lambda k: ((k[0].code or ''), (k[1].default_code or ''), k[1].id))

        sections = []
        only_opening_count = 0
        line_count = 0
        nonstock_line_seen = 0     # 判据12 交叉核：非存货 move 被键为 None 的条数（报数）
        for m in period:
            if keyfn(m) is None:
                nonstock_line_seen += 1

        for k in keys:
            acct, product = k
            oqty, oval = open_agg.get(k, [0.0, 0.0])
            klines = period_lines.get(k, [])
            has_open = not (float_is_zero(oqty, precision_rounding=0.000001)
                            and float_is_zero(oval, precision_rounding=currency.rounding))
            if not klines and not has_open:
                continue
            if not klines and has_open:
                only_opening_count += 1

            run_qty, run_val = oqty, oval
            odir = self._cn_ql_dir(oval, currency)
            opening_row = {
                'qty': oqty, 'value': oval, 'direction': odir,
                'bal_price': self._cn_ql_price(oval, oqty),
            }

            # 逐笔 → 分期（按 (year, month)），期内逐笔滚动，期末收本期合计 + 本年累计。
            periods = []
            cur = None
            cur_ym = None
            fy_d = fy_c = 0.0            # 本财年累计（借/贷 金额）
            fy_dq = fy_cq = 0.0          # 本财年累计（借/贷 数量）
            cur_fy = None
            for m in klines:
                md = m.date if isinstance(m.date, datetime.date) else self._to_date(m.date)
                ym = (md.year, md.month)
                fy = company.compute_fiscalyear_dates(md)['date_from']
                if cur_fy is None or fy != cur_fy:
                    # 🔴 跨财年：本年累计【重置】（余额不重置）。
                    fy_d = fy_c = fy_dq = fy_cq = 0.0
                    cur_fy = fy
                if cur is None or ym != cur_ym:
                    if cur is not None:
                        periods.append(self._cn_ql_finalize(cur, run_qty, run_val, currency))
                    cur = {'label': '%d%02d' % ym, 'ym': ym, 'lines': [],
                           'dq': 0.0, 'dv': 0.0, 'cq': 0.0, 'cv': 0.0}
                    cur_ym = ym
                sign = 1.0 if m.is_in else -1.0
                q = m.quantity
                v = m.value
                run_qty += sign * q
                run_val += sign * v
                if m.is_in:
                    dq, dv, cq, cv = q, v, 0.0, 0.0
                    fy_d += v
                    fy_dq += q
                else:
                    dq, dv, cq, cv = 0.0, 0.0, q, v
                    fy_c += v
                    fy_cq += q
                cur['lines'].append({
                    'date': md.strftime('%Y-%m-%d'),
                    'voucher': m.reference or '',
                    'summary': m.origin or m.reference or (m.product_id.display_name or ''),
                    'd_qty': dq or None, 'd_price': self._cn_ql_price(dv, dq), 'd_amt': dv or None,
                    'c_qty': cq or None, 'c_price': self._cn_ql_price(cv, cq), 'c_amt': cv or None,
                    'direction': self._cn_ql_dir(run_val, currency),
                    'bal_qty': run_qty, 'bal_price': self._cn_ql_price(run_val, run_qty),
                    'bal_value': run_val,
                })
                cur['dq'] += dq
                cur['dv'] += dv
                cur['cq'] += cq
                cur['cv'] += cv
                cur['fy_d'] = fy_d
                cur['fy_c'] = fy_c
                cur['fy_dq'] = fy_dq
                cur['fy_cq'] = fy_cq
                line_count += 1
            if cur is not None:
                periods.append(self._cn_ql_finalize(cur, run_qty, run_val, currency))

            total_row = None
            if is_cross_year:
                # 🔴 合计行（H1）：跨年区间出，= 各期本期发生之和（全区间总计），余额=末余额。
                td = sum(p['current']['d_amt'] or 0.0 for p in periods)
                tc = sum(p['current']['c_amt'] or 0.0 for p in periods)
                tdq = sum(p['current']['d_qty'] or 0.0 for p in periods)
                tcq = sum(p['current']['c_qty'] or 0.0 for p in periods)
                total_row = {
                    'd_qty': tdq or None, 'd_price': self._cn_ql_price(td, tdq), 'd_amt': td or None,
                    'c_qty': tcq or None, 'c_price': self._cn_ql_price(tc, tcq), 'c_amt': tc or None,
                    'direction': self._cn_ql_dir(run_val, currency),
                    'bal_qty': run_qty, 'bal_price': self._cn_ql_price(run_val, run_qty),
                    'bal_value': run_val,
                }

            sections.append({
                'acct_code': acct.code or '', 'acct_name': acct.name or '',
                'product_name': product.display_name or '',
                'unit': '',                      # 🟡 单位列内容形态 unknown（原件通栏空）：留空、不猜
                'open_date': self._cn_ql_open_date(options),
                'opening': opening_row,
                'periods': periods,
                'total_row': total_row,
            })
        return {
            'sections': sections,
            'currency': currency,
            'is_cross_year': is_cross_year,
            'only_opening_count': only_opening_count,
            'line_count': line_count,
            'nonstock_line_seen': nonstock_line_seen,
        }

    def _cn_ql_finalize(self, cur, run_qty, run_val, currency):
        """收一期：本期合计（本期均价 = 本期金额÷本期数量）+ 本年累计（本财年累计、余额=期末）。"""
        return {
            'label': cur['label'], 'ym': cur['ym'], 'lines': cur['lines'],
            'current': {
                'd_qty': cur['dq'] or None, 'd_price': self._cn_ql_price(cur['dv'], cur['dq']),
                'd_amt': cur['dv'] or None,
                'c_qty': cur['cq'] or None, 'c_price': self._cn_ql_price(cur['cv'], cur['cq']),
                'c_amt': cur['cv'] or None,
                'direction': self._cn_ql_dir(run_val, currency),
                'bal_qty': run_qty, 'bal_price': self._cn_ql_price(run_val, run_qty),
                'bal_value': run_val,
            },
            'ytd': {
                'd_qty': cur.get('fy_dq') or None,
                'd_price': self._cn_ql_price(cur.get('fy_d'), cur.get('fy_dq')),
                'd_amt': cur.get('fy_d') or None,
                'c_qty': cur.get('fy_cq') or None,
                'c_price': self._cn_ql_price(cur.get('fy_c'), cur.get('fy_cq')),
                'c_amt': cur.get('fy_c') or None,
                'direction': self._cn_ql_dir(run_val, currency),
                'bal_qty': run_qty, 'bal_price': self._cn_ql_price(run_val, run_qty),
                'bal_value': run_val,
            },
        }

    def _cn_ql_open_date(self, options):
        d = (options.get('date') or {}).get('date_from')
        return str(d)[:10] if d else ''

    def _to_date(self, v):
        if not v:
            return None
        if isinstance(v, datetime.datetime):
            return v.date()
        if isinstance(v, datetime.date):
            return v
        return datetime.date.fromisoformat(str(v)[:10])

    # ---------------------------------------------------------- 屏幕行（动态生成器）
    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals,
                                 warnings=None):
        """摊成 account.report 行序列：每段一条科目/产品标题行(level 0) + 期初行 + 每期(逐笔 +
        本期合计 + 本年累计) + 跨年合计行(level 2)。🔴 扁平行（不用 parent_id）：规避框架
        totals_below_sections 噪声合计行（B-79）。"""
        data = self._cn_ql_compute(report, options)
        cols = options.get('columns', [])
        out = []
        seq = 0
        for sec in data['sections']:
            seq += 1
            out.append((seq, {
                'id': report._get_generic_line_id(
                    None, None, markup={'cn_ql_sec': '%s:%s' % (sec['acct_code'], sec['product_name'])}),
                'name': ('%s %s — %s' % (sec['acct_code'], sec['acct_name'], sec['product_name'])).strip(),
                'level': 0,
                'unfoldable': False,
                'columns': [{} for _c in cols],
                'cn_ql_row_type': 'section',
            }))

            def row(summary, vals, rtype, i):
                nonlocal seq
                seq += 1
                return (seq, {
                    'id': report._get_generic_line_id(
                        None, None, markup={'cn_ql_row': '%s:%s' % (sec['acct_code'], i)}),
                    'name': summary,
                    'level': 2,
                    'unfoldable': False,
                    'columns': self._cn_ql_cols(report, options, cols, data['currency'], vals),
                    'cn_ql_row_type': rtype,
                })

            o = sec['opening']
            out.append(row('期初余额', {
                'date_txt': sec['open_date'], 'voucher': '', 'unit': sec['unit'],
                'd_qty': None, 'd_price': None, 'd_amt': None,
                'c_qty': None, 'c_price': None, 'c_amt': None,
                'direction': o['direction'], 'bal_qty': o['qty'] or None,
                'bal_price': o['bal_price'], 'bal_amt': o['value'] or None,
            }, 'opening', 'o'))
            for pi, pr in enumerate(sec['periods']):
                for li, ln in enumerate(pr['lines']):
                    out.append(row(ln['summary'], {
                        'date_txt': ln['date'], 'voucher': ln['voucher'], 'unit': sec['unit'],
                        'd_qty': ln['d_qty'], 'd_price': ln['d_price'], 'd_amt': ln['d_amt'],
                        'c_qty': ln['c_qty'], 'c_price': ln['c_price'], 'c_amt': ln['c_amt'],
                        'direction': ln['direction'], 'bal_qty': ln['bal_qty'],
                        'bal_price': ln['bal_price'], 'bal_amt': ln['bal_value'] or None,
                    }, 'detail', '%s.l%s' % (pi, li)))
                out.append(row('本期合计', self._cn_ql_block_vals(pr['current'], sec['unit']),
                               'current', '%s.c' % pi))
                out.append(row('本年累计', self._cn_ql_block_vals(pr['ytd'], sec['unit']),
                               'ytd', '%s.y' % pi))
            if sec['total_row']:
                out.append(row('合计', self._cn_ql_block_vals(sec['total_row'], sec['unit']),
                               'grand_total', 'g'))
        return out

    def _cn_ql_block_vals(self, blk, unit):
        return {
            'date_txt': '', 'voucher': '', 'unit': unit,
            'd_qty': blk['d_qty'], 'd_price': blk['d_price'], 'd_amt': blk['d_amt'],
            'c_qty': blk['c_qty'], 'c_price': blk['c_price'], 'c_amt': blk['c_amt'],
            'direction': blk['direction'], 'bal_qty': blk['bal_qty'],
            'bal_price': blk['bal_price'], 'bal_amt': blk['bal_value'] or None,
        }

    def _cn_ql_cols(self, report, options, cols, currency, vals):
        strcols = {'date_txt', 'voucher', 'unit', 'direction'}
        out = []
        for c in cols:
            label = c.get('expression_label')
            val = vals.get(label)
            d = report._build_column_dict(val, c, options=options, currency=currency)
            if label in strcols and val not in (None, ''):
                d['name'] = val
            out.append(d)
        return out
