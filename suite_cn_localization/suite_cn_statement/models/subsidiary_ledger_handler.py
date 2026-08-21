# -*- coding: utf-8 -*-
"""R51-T1 —— 中式三栏式明细分类账.

一张【新建】的 account.report（挂官方 General Ledger 变体），自带 custom_handler。
🔴 官方 General Ledger 记录 / 官方 account_report.py / 官方 handler 【三个都不碰】——
本 handler 只在【我方新建报表】上取数（惯例31：禁对象不禁手段；R47/R49 已立同款）。

与总账（R50，`suite.cn.general.ledger.report.handler`）的关系（项目档 v43 §4.5.22 五 / 六，
金蝶导出件锚，非「按中式惯例做」）——
    🟢 【取数同源、roll-up 同键】：期初经 to_beginning_of_fiscalyear、发生额经 from_fiscalyear，
      一级 roll-up 复用 R47 点分前缀键。总账把发生额【按月聚合】，明细账【保留逐笔】、只多
      「逐笔滚动余额」这一层。⇒ 复用总账的 `_cn_gl_dir_bal`（方向/余额属性制）、`_cn_gl_key_attr`
      （方向属性三层回落）、`_cn_gl_open_period`、`_cn_gl_company`，不另起一套（§三 复用四条）。
    🔴 与总账的三处【形态】不同（§4.5.22 五，别照抄）——
      1. 日期列 = 分录【实际日期】（YYYY-MM-DD），不是总账的期间号 YYYYMM。
         ⚠️ 陷阱（§4.5.22 四 / kingdee v4 §0.1）：金蝶导出件里「同月所有明细行日期相同」是
         那个账套【月末集中入账】的记账习惯（真实日期写进摘要），【不是】版式规则。⇒ 日期列
         必须取 account_move_line.date，【绝不】实现成期间末日（判据8 钉死）。
      2. 有【凭证字号】列（move.name，形如「记-3」），总账没有。
      3. 逐笔明细行 + 余额【逐笔滚动】（running balance），总账只有期汇总。

形态（导出件锚）——
    每个一级科目一段，段内：
      期初余额行（范围首月期间号；凭证字号/借贷栏空、方向/余额有值）；
      每有发生额期：逐笔明细行（逐笔滚动余额）+ 本期合计（本期毛额 + 期末方向/余额）+
        本年累计（截至该期 YTD 毛额 + 期末方向/余额，与本期合计同一期末余额）——逐期滚动；
      只有期初余额、全年无发生额的科目出段、只期初行 + 本年累计行(0)。
    零值金额栏【留空】不显 0.00。

🔴 直连 raw SQL 的自补清单（background v30 §7 B-78，R50 血泪同款）——
    `_cn_sl_query` 直连裸 SQL：进来前必须 `env.flush_all()`（否则最后一笔未落库分录被漏读、
    与总账/余额表对账差一笔，判据6）+ `_init_currency_table`（DROP IF EXISTS + ON COMMIT
    DROP，幂等）。经 _get_lines→_dynamic_lines_generator 进来时框架已 flush + 建币表；但
    XLSX 的 `_cn_sl_prepare` 与测试【直接】调 `_cn_sl_compute`，两者都必须自补。
"""
import datetime

from odoo import models
from odoo.tools import SQL, float_is_zero


class CnSubsidiaryLedgerReportHandler(models.AbstractModel):
    _name = 'suite.cn.subsidiary.ledger.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = '三栏式明细分类账 Custom Handler'

    # ------------------------------------------------------------- 取数（逐笔）
    def _cn_sl_query(self, report, options):
        """返回 (opening_by_acc, lines)，honoring 报表全部筛选。
            opening_by_acc: {account_id: signed 期初余额(本年度首日前累计)}
            lines: [{lid, aid, ld(date), mid, summary, d, c}, ...] 按 (date, id) 升序。
        与总账 `_cn_gl_query` 逐字同款范式（flush + _currency_table_* + _get_report_query），
        差别仅在【不按月聚合、保留逐笔】。"""
        # 🔴 B-78：直连 SQL 前 flush ORM（同 R50 总账；不 flush 会漏读最后一笔未落库分录）。
        self.env.flush_all()
        report._init_currency_table(options)

        q_open = report._get_report_query(options, 'to_beginning_of_fiscalyear')
        self.env.cr.execute(SQL(
            """
            SELECT account_move_line.account_id AS aid,
                   COALESCE(SUM(%(bal)s), 0.0) AS bal
            FROM %(tables)s
            %(cj)s
            WHERE %(where)s
            GROUP BY account_move_line.account_id
            """,
            bal=report._currency_table_apply_rate(SQL("account_move_line.balance")),
            tables=q_open.from_clause,
            cj=report._currency_table_aml_join(options),
            where=q_open.where_clause,
        ))
        opening = {r['aid']: r['bal'] for r in self.env.cr.dictfetchall()}

        # 逐笔（无 GROUP BY）：凭证字号走标量子查询取 account_move.name（避免 join 别名撞车）。
        q_mv = report._get_report_query(options, 'from_fiscalyear')
        self.env.cr.execute(SQL(
            """
            SELECT account_move_line.id AS lid,
                   account_move_line.account_id AS aid,
                   account_move_line.date AS ld,
                   account_move_line.move_id AS mid,
                   account_move_line.name AS summary,
                   (SELECT am.name FROM account_move am
                     WHERE am.id = account_move_line.move_id) AS vch,
                   %(d)s AS d,
                   %(c)s AS c
            FROM %(tables)s
            %(cj)s
            WHERE %(where)s
            ORDER BY account_move_line.date, account_move_line.id
            """,
            d=report._currency_table_apply_rate(SQL("account_move_line.debit")),
            c=report._currency_table_apply_rate(SQL("account_move_line.credit")),
            tables=q_mv.from_clause,
            cj=report._currency_table_aml_join(options),
            where=q_mv.where_clause,
        ))
        lines = []
        for r in self.env.cr.dictfetchall():
            ld = r['ld']
            lines.append({
                'lid': r['lid'], 'aid': r['aid'],
                'ld': ld.date() if isinstance(ld, datetime.datetime) else ld,
                'mid': r['mid'], 'summary': r['summary'] or '', 'vch': r['vch'] or '',
                'd': r['d'], 'c': r['c'],
            })
        return opening, lines

    # --------------------------------------------------------- 结构化计算（同源单点）
    def _cn_sl_compute(self, report, options):
        """算一次、渲染两次（屏幕 _dynamic_lines_generator + 中式版式 XLSX）+ 供测试直取。
        一级 roll-up 复用 R47 键；每段 = 期初行 / 每期(逐笔明细 + 本期合计 + 本年累计) /
        只期初科目补一本年累计(0)行。逐笔滚动余额在 line['signed']/['balance']。"""
        opening, lines = self._cn_sl_query(report, options)
        gl = self.env['suite.cn.general.ledger.report.handler']
        tb = self.env['suite.cn.trial.balance.report.handler']
        company = gl._cn_gl_company(report, options)
        currency = company.currency_id
        rnd = currency.rounding

        acc_ids = set(opening) | {ln['aid'] for ln in lines}
        accounts = self.env['account.account'].browse([a for a in acc_ids if a])
        code_of = {a.id: (a.code or '') for a in accounts}
        key_of = {aid: tb._cn_tb_rollup_key(code_of.get(aid, '')) for aid in acc_ids}
        leaf_types_by_key = {}
        for a in accounts:
            leaf_types_by_key.setdefault(key_of.get(a.id, ''), []).append(a.account_type)

        open_key = {}
        for aid, bal in opening.items():
            k = key_of.get(aid, '')
            open_key[k] = open_key.get(k, 0.0) + bal
        # 逐笔按一级键分组，保留 SQL 的全局 (date, id) 顺序。
        lines_key = {}
        for ln in lines:
            lines_key.setdefault(key_of.get(ln['aid'], ''), []).append(ln)

        keys = sorted(set(open_key) | set(lines_key))
        company_ids = report.get_report_company_ids(options)
        anchors = self.env['account.account'].search(
            [('code', 'in', keys), ('company_ids', 'in', company_ids)])
        anchor_name = {a.code: a.name for a in anchors}
        anchor_by_code = {a.code: a for a in anchors}
        national = tb._cn_tb_national_names()
        # 期初余额行日期 = 范围首日（完整 YYYY-MM-DD，导出件锚；判据7 钉）——非总账的期间号。
        open_date = self._cn_sl_open_date(options)

        sections = []
        only_opening_count = 0
        detail_leak = 0
        derived_count = 0
        line_count = 0
        for k in keys:
            opening_signed = open_key.get(k, 0.0)
            klines = lines_key.get(k, [])
            has_open = not float_is_zero(opening_signed, precision_rounding=rnd)
            if not klines and not has_open:
                continue
            if not klines and has_open:
                only_opening_count += 1
            if k and tb._cn_tb_rollup_key(k) != k:
                detail_leak += 1

            attr, src = gl._cn_gl_key_attr(tb, k, anchor_by_code, leaf_types_by_key)
            if src == 'derived':
                derived_count += 1

            odir, obal = gl._cn_gl_dir_bal(opening_signed, attr, currency)
            running = opening_signed
            ytd_d = ytd_c = 0.0
            periods = []
            cur = None
            cur_month = None
            for ln in klines:
                m = datetime.date(ln['ld'].year, ln['ld'].month, 1)
                if cur is None or m != cur_month:
                    if cur is not None:
                        periods.append(self._cn_sl_finalize(gl, cur, attr, currency))
                    cur = {'period': m, 'label': '%d%02d' % (m.year, m.month),
                           'lines': [], 'cd': 0.0, 'cc': 0.0,
                           'run': running, 'yd': ytd_d, 'yc': ytd_c}
                    cur_month = m
                d, c = ln['d'], ln['c']
                running += d - c
                ytd_d += d
                ytd_c += c
                ldir, lbal = gl._cn_gl_dir_bal(running, attr, currency)
                cur['lines'].append({
                    'date': ln['ld'].strftime('%Y-%m-%d'),
                    'voucher': ln['vch'],
                    'summary': ln['summary'],
                    'debit': d, 'credit': c, 'signed': running,
                    'direction': ldir, 'balance': lbal,
                })
                cur['cd'] += d
                cur['cc'] += c
                cur['run'] = running
                cur['yd'] = ytd_d
                cur['yc'] = ytd_c
                line_count += 1
            if cur is not None:
                periods.append(self._cn_sl_finalize(gl, cur, attr, currency))

            tdir, tbal = gl._cn_gl_dir_bal(running, attr, currency)
            sections.append({
                'code': k,
                'name': anchor_name.get(k) or national.get(k, ''),
                'attr': attr,
                'attr_source': src,
                'open_date': open_date,
                'opening': {'signed': opening_signed, 'direction': odir, 'balance': obal},
                'periods': periods,
                'total': {'debit': ytd_d, 'credit': ytd_c, 'signed': running,
                          'direction': tdir, 'balance': tbal},
            })
        return {
            'sections': sections,
            'currency': currency,
            'only_opening_count': only_opening_count,
            'detail_leak': detail_leak,
            'derived_count': derived_count,
            'line_count': line_count,
        }

    def _cn_sl_open_date(self, options):
        """期初余额行的日期 = 报表范围 date_from（YYYY-MM-DD，导出件里期初行取范围首日）。"""
        d = (options.get('date') or {}).get('date_from')
        return str(d)[:10] if d else ''

    def _cn_sl_finalize(self, gl, cur, attr, currency):
        """把累加中的一期收成 {period,label,lines,current(本期合计),ytd(本年累计)}。
        本期合计余额 == 本年累计余额 == 期末 signed（同一期末，与总账同规则）。"""
        cdir, cbal = gl._cn_gl_dir_bal(cur['run'], attr, currency)
        return {
            'period': cur['period'], 'label': cur['label'], 'lines': cur['lines'],
            'current': {'debit': cur['cd'], 'credit': cur['cc'], 'signed': cur['run'],
                        'direction': cdir, 'balance': cbal},
            'ytd': {'debit': cur['yd'], 'credit': cur['yc'], 'signed': cur['run'],
                    'direction': cdir, 'balance': cbal},
        }

    # ---------------------------------------------------------- 屏幕行（动态生成器）
    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals,
                                 warnings=None):
        """摊成 account.report 行序列：每段一条科目标题行(level 0) + 期初行 + 每期(逐笔明细 +
        本期合计 + 本年累计)行(level 2)。name = 摘要；列 = 日期/凭证字号/借方/贷方/方向/余额。
        🔴 扁平行（不用 parent_id 层级）：规避框架 totals_below_sections 在有子行段下插「Total」
        噪声合计行（账簿不该有，background §7 B-79），段头无子行即不触发。"""
        data = self._cn_sl_compute(report, options)
        currency = data['currency']
        cols = options.get('columns', [])
        out = []
        seq = 0
        for sec in data['sections']:
            seq += 1
            out.append((seq, {
                'id': report._get_generic_line_id(
                    None, None, markup={'cn_sl_acct': sec['code']}),
                'name': ('%s %s' % (sec['code'], sec['name'])).strip(),
                'level': 0,
                'unfoldable': False,
                'columns': [{} for _c in cols],
                'cn_sl_code': sec['code'],
                'cn_sl_name': sec['name'],
                'cn_sl_row_type': 'section',
            }))

            def row(summary, date_txt, voucher, debit, credit, direction, balance, rtype, i):
                nonlocal seq
                seq += 1
                return (seq, {
                    'id': report._get_generic_line_id(
                        None, None, markup={'cn_sl_row': '%s:%s' % (sec['code'], i)}),
                    'name': summary,
                    'level': 2,
                    'unfoldable': False,
                    'columns': self._cn_sl_cols(report, options, cols, currency,
                                                date_txt, voucher, debit, credit,
                                                direction, balance),
                    'cn_sl_date': date_txt,
                    'cn_sl_summary': summary,
                    'cn_sl_row_type': rtype,
                })

            o = sec['opening']
            out.append(row('期初余额', sec['open_date'], '', None, None, o['direction'],
                           o['balance'], 'opening', 'o'))
            for pi, pr in enumerate(sec['periods']):
                for li, ln in enumerate(pr['lines']):
                    out.append(row(ln['summary'], ln['date'], ln['voucher'],
                                   ln['debit'], ln['credit'], ln['direction'],
                                   ln['balance'], 'detail', '%s.l%s' % (pi, li)))
                cu, yt = pr['current'], pr['ytd']
                out.append(row('本期合计', '', '', cu['debit'], cu['credit'],
                               cu['direction'], cu['balance'], 'current', '%s.c' % pi))
                out.append(row('本年累计', '', '', yt['debit'], yt['credit'],
                               yt['direction'], yt['balance'], 'ytd', '%s.y' % pi))
            if not sec['periods']:
                t = sec['total']
                out.append(row('本年累计', sec['open_date'], '', t['debit'], t['credit'],
                               t['direction'], t['balance'], 'ytd', 't'))
        return out

    def _cn_sl_cols(self, report, options, cols, currency, date_txt, voucher,
                    debit, credit, direction, balance):
        """按 options['columns'] 顺序造列字典。debit/credit/balance 数值列（留空 name，None ⇒
        blank，含「平」余额与期初/合计空发生额）；date_txt/voucher/direction string 列预置 name。"""
        by_label = {'date_txt': date_txt, 'voucher': voucher, 'debit_amt': debit,
                    'credit_amt': credit, 'direction': direction, 'balance': balance}
        strcols = {'date_txt', 'voucher', 'direction'}
        out = []
        for c in cols:
            label = c.get('expression_label')
            val = by_label.get(label)
            d = report._build_column_dict(val, c, options=options, currency=currency)
            if label in strcols and val not in (None, ''):
                d['name'] = val
            out.append(d)
        return out
