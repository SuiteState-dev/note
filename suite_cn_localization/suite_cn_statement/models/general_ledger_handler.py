# -*- coding: utf-8 -*-
"""中式总分类账 (R49 交付 → R50 返工).

一张【新建】的 account.report（挂官方 General Ledger 变体），自带 custom_handler。
🔴 官方 General Ledger 记录 / 官方 account_report.py / 官方 handler 【三个都不碰】——
本 handler 只在【我方新建报表】上取数（惯例31：禁对象不禁手段；R47 已立同款）。

为什么用 _dynamic_lines_generator（而非 R47 的表达式引擎+后处理器）——
    总分类账【行=期间】、一个科目一段；R47 那套是「列式 date_scope + groupby=account_id」
    出【行=科目】。期间行不吃列式 date_scope，须由 handler 全权生成行序列 ⇒ 用官方 GL 同款
    的 _dynamic_lines_generator（基类/官方 GL handler 都有此钩，实测 hasattr 双 True）。

取数复用 R47/R48 地基，只多「按月分组」一层——
    期初  = _get_report_query(options, 'to_beginning_of_fiscalyear')  本年度首日前累计(signed)
    发生额 = _get_report_query(options, 'from_fiscalyear') + date_trunc('month')  逐月毛额
    两个 date_scope 与官方 bal_begin(年初)/ytd(本年累计) 同款，honoring 期间/日记账/过账/
    多公司 全部筛选。一级 roll-up 复用 R47 的点分前缀键（`_cn_tb_rollup_key`）与国标名回落。

🔴 R50 返工（R49 的 Q1-A「方向=余额实际符号」被金蝶总账+明细账导出件原件证伪，作废）——
    规则改回【属性制】（项目档 v42 §4.5.22，唯一归宿，双栏表/单栏表【共用一条】规则）：
      余额 == 0 → 方向「平」、余额栏【留空】；
      余额 != 0 → 方向 = 该科目【余额方向属性】(借/贷)，【不随数值符号迁移】；
      余额【带符号】：实际方向与属性一致为正、相反为负（3103 属性贷/实际借 ⇒ 方向贷/余额负）。
    符号【不】参与方向判定——方向只由「属性 + 是否为零」决定。复用 R48 的
    `_cn_resolve_direction` / `_cn_prefix_direction`（不另起一套）。
    ⇒ 与科目余额表【表现完全一致】、客户两表对账看不到差异（§4.5.22 二）；R49 那句
    「表现不同、语义一致」一并作废。

形态（项目档 §4.5.22 五 / 六，导出件锚，非「按中式惯例做」）——
    每个一级科目一段，段内：
      期初余额行（年初余额；借/贷发生额栏空、方向/余额有值）；
      每个【有发生额的期】两行：本期合计（本期毛额 + 期末方向/余额）+ 本年累计（截至该期
        YTD 毛额 + 期末方向/余额，与本期合计同一期末余额）——本年累计【逐期滚动】；
      只有期初余额、全年无发生额的科目【出段】（有余额就是账）、只期初行 + 本年累计行(0)。
    期间列 = YYYYMM 六位；零值金额栏【留空】不显 0.00。
"""
import datetime
from collections import Counter

from odoo import api, models, _
from odoo.tools import SQL, float_is_zero


class CnGeneralLedgerReportHandler(models.AbstractModel):
    _name = 'suite.cn.general.ledger.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = '总分类账 Custom Handler'

    # ------------------------------------------------------------- 取数（按月毛额）
    def _cn_gl_query(self, report, options):
        """返回 (opening_by_acc, monthly_by_acc)，honoring 报表全部筛选。
            opening_by_acc: {account_id: signed 期初余额(本年度首日前累计)}
            monthly_by_acc: {account_id: {month_date(当月1日): (debit, credit)}}
        SQL 与官方 TB / 我方 R47 逐字同款范式（_currency_table_* + _get_report_query）。"""
        # 🔴 直连 SQL 前必须 flush ORM：经 _get_lines 进来时框架已 flush；但 XLSX 的
        # _cn_gl_prepare 与测试【直接】调 _cn_gl_compute，最后一笔 ORM 写入(如刚过账的分录)
        # 仍在缓存未落库，裸 SQL 会漏读 ⇒ 与八栏余额表对账差一笔(判据9)。flush 后一致。
        self.env.flush_all()
        # 币表临时表：经 _get_lines→_dynamic_lines_generator 进来时框架已建；但直接调用须自建。
        # _init_currency_table 是 DROP IF EXISTS + ON COMMIT DROP，幂等、可重复调用。
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

        q_mv = report._get_report_query(options, 'from_fiscalyear')
        self.env.cr.execute(SQL(
            """
            SELECT account_move_line.account_id AS aid,
                   date_trunc('month', account_move_line.date) AS m,
                   COALESCE(SUM(%(d)s), 0.0) AS d,
                   COALESCE(SUM(%(c)s), 0.0) AS c
            FROM %(tables)s
            %(cj)s
            WHERE %(where)s
            GROUP BY account_move_line.account_id, m
            """,
            d=report._currency_table_apply_rate(SQL("account_move_line.debit")),
            c=report._currency_table_apply_rate(SQL("account_move_line.credit")),
            tables=q_mv.from_clause,
            cj=report._currency_table_aml_join(options),
            where=q_mv.where_clause,
        ))
        monthly = {}
        for r in self.env.cr.dictfetchall():
            m = r['m']
            mk = m.date() if isinstance(m, datetime.datetime) else m
            monthly.setdefault(r['aid'], {})[mk] = (r['d'], r['c'])
        return opening, monthly

    # -------------------------------------------------------- 方向 + 余额（属性制 R50）
    def _cn_gl_dir_bal(self, signed, attr, currency):
        """§4.5.22 唯一规则：余额==0 → 方向「平」、余额栏留空(None)；余额!=0 → 方向取科目
        【余额方向属性】(attr∈{'debit','credit'})、余额带符号(与属性一致为正、相反为负)。
        返回 (方向标签, 余额 或 None)。符号不参与方向判定。"""
        if float_is_zero(signed, precision_rounding=currency.rounding):
            return '平', None
        if attr == 'debit':
            return '借', signed          # 实际在借为正、在贷为负
        return '贷', -signed             # 属性贷：实际在贷为正、在借(signed>0)为负

    def _cn_gl_key_attr(self, tb, key, anchor_by_code, leaf_types_by_key):
        """一级键的余额方向属性，复用 R48 三层 + 键级回落，返回 (attr, source)：
            field/issued 走 R48 anchor 账户或我方发行件（`_cn_prefix_direction` 同源）；
            连号客户(无编码恰为 key 的账户、又非标准发行码) ⇒ 从该键下明细科目的 account_type
            多数派推导(source='derived'，与 R48 derived 同级、随件报数)。二姐口述：单科目只有
            一个方向属性、父不例外(§4.5.22 六)。"""
        anchor = anchor_by_code.get(key)
        if anchor is not None:
            return tb._cn_resolve_direction(anchor)          # (dir, source∈field/issued/derived)
        issued = tb._cn_direction_by_code().get(key)
        if issued:
            return issued, 'issued'
        types = leaf_types_by_key.get(key) or []
        if types:
            at = Counter(types).most_common(1)[0][0]
            return tb._cn_derive_direction(at), 'derived'
        return 'debit', 'derived'

    # --------------------------------------------------------- 结构化计算（同源单点）
    def _cn_gl_compute(self, report, options):
        """算一次、渲染两次（屏幕 _dynamic_lines_generator + 中式版式 XLSX）+ 供测试直取。
        一级 roll-up 复用 R47 键；每段 = 期初行 / 逐期(本期合计+本年累计) / 只期初科目累计0。"""
        opening, monthly = self._cn_gl_query(report, options)
        company = self._cn_gl_company(report, options)
        currency = company.currency_id
        rnd = currency.rounding
        tb = self.env['suite.cn.trial.balance.report.handler']

        acc_ids = set(opening) | set(monthly)
        accounts = self.env['account.account'].browse([a for a in acc_ids if a])
        code_of = {a.id: (a.code or '') for a in accounts}
        key_of = {aid: tb._cn_tb_rollup_key(code_of.get(aid, '')) for aid in acc_ids}
        leaf_types_by_key = {}
        for a in accounts:
            leaf_types_by_key.setdefault(key_of.get(a.id, ''), []).append(a.account_type)

        # 一级键聚合：期初 signed、逐月毛额。
        open_key = {}
        for aid, bal in opening.items():
            k = key_of.get(aid, '')
            open_key[k] = open_key.get(k, 0.0) + bal
        mv_key = {}
        for aid, mm in monthly.items():
            k = key_of.get(aid, '')
            dst = mv_key.setdefault(k, {})
            for m, (d, c) in mm.items():
                cur = dst.setdefault(m, [0.0, 0.0])
                cur[0] += d
                cur[1] += c

        # 一级名回落 + 锚账户（复用 R47：公司内锚账户 → 我方国标标准名 → 裸前缀）。
        keys = sorted(set(open_key) | set(mv_key))
        company_ids = report.get_report_company_ids(options)
        anchors = self.env['account.account'].search(
            [('code', 'in', keys), ('company_ids', 'in', company_ids)])
        anchor_name = {a.code: a.name for a in anchors}
        anchor_by_code = {a.code: a for a in anchors}
        national = tb._cn_tb_national_names()

        # 期初余额行的期间号 = 报表范围起始月 YYYYMM（多期视图下期初=年初；单期原件下即该期）。
        open_period = self._cn_gl_open_period(options)

        sections = []
        only_opening_count = 0    # 只期初余额、全年无发生额 出段的科目数（Q2 edge 回报）
        detail_leak = 0           # 段编码 != 其一级键 的条数（判据8 期望 0）
        derived_count = 0         # 方向属性走 account_type 推导兜底的段数（随件报数）
        for k in keys:
            opening_signed = open_key.get(k, 0.0)
            months = sorted(mv_key.get(k, {}).keys())
            has_open = not float_is_zero(opening_signed, precision_rounding=rnd)
            # 全年无发生额且无期初 → 不出段（同 TB 判据8）。
            if not months and not has_open:
                continue
            if not months and has_open:
                only_opening_count += 1
            if k and tb._cn_tb_rollup_key(k) != k:
                detail_leak += 1

            attr, src = self._cn_gl_key_attr(tb, k, anchor_by_code, leaf_types_by_key)
            if src == 'derived':
                derived_count += 1

            odir, obal = self._cn_gl_dir_bal(opening_signed, attr, currency)
            running = opening_signed
            ytd_d = ytd_c = 0.0
            periods = []
            for m in months:
                d, c = mv_key[k][m]
                running += d - c
                ytd_d += d
                ytd_c += c
                cdir, cbal = self._cn_gl_dir_bal(running, attr, currency)
                periods.append({
                    'period': m,
                    'label': '%d%02d' % (m.year, m.month),
                    'current': {'debit': d, 'credit': c, 'signed': running,
                                'direction': cdir, 'balance': cbal},
                    'ytd': {'debit': ytd_d, 'credit': ytd_c, 'signed': running,
                            'direction': cdir, 'balance': cbal},
                })
            tdir, tbal = self._cn_gl_dir_bal(running, attr, currency)
            sections.append({
                'code': k,
                'name': anchor_name.get(k) or national.get(k, ''),
                'attr': attr,
                'attr_source': src,
                'open_period': open_period,
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
        }

    def _cn_gl_open_period(self, options):
        """期初余额行的期间号 YYYYMM，取报表范围 date_from（年初）。"""
        d = (options.get('date') or {}).get('date_from')
        if not d:
            return ''
        s = str(d)
        return '%s%s' % (s[0:4], s[5:7]) if len(s) >= 7 else ''

    # ---------------------------------------------------------- 屏幕行（动态生成器）
    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals,
                                 warnings=None):
        """把结构化计算摊成 account.report 行序列：每段一条科目标题行(level 0) + 期初行 +
        逐期(本期合计/本年累计) 行(level 2)。数值列留空 name 交框架格式化；方向列 string 预置
        name 原样保留。"""
        data = self._cn_gl_compute(report, options)
        currency = data['currency']
        cols = options.get('columns', [])
        out = []
        seq = 0
        # 🔴 扁平行序列（不用 parent_id 层级）：段头 level 0、行 level 2 仅作缩进。用父子层级
        # 会触发框架 totals_below_sections 在每段下插一条「Total <科目>」噪声行（账簿不该有），
        # 扁平即规避（段头无子行 ⇒ 不触发合计）。段内顺序即装订顺序。
        for sec in data['sections']:
            seq += 1
            out.append((seq, {
                'id': report._get_generic_line_id(
                    None, None, markup={'cn_gl_acct': sec['code']}),
                'name': ('%s %s' % (sec['code'], sec['name'])).strip(),
                'level': 0,
                'unfoldable': False,
                'columns': [{} for _c in cols],     # 段头无值：空列（renderer 跳过）
                'cn_gl_code': sec['code'],
                'cn_gl_name': sec['name'],
                'cn_gl_row_type': 'section',
            }))

            def row(period, summary, debit, credit, direction, balance, rtype, i):
                nonlocal seq
                seq += 1
                return (seq, {
                    'id': report._get_generic_line_id(
                        None, None, markup={'cn_gl_row': '%s:%s' % (sec['code'], i)}),
                    'name': ('%s %s' % (period, summary)).strip(),
                    'level': 2,
                    'unfoldable': False,
                    'columns': self._cn_gl_cols(
                        report, options, cols, currency, debit, credit, direction, balance),
                    'cn_gl_period': period,
                    'cn_gl_summary': summary,
                    'cn_gl_row_type': rtype,
                })

            o = sec['opening']
            out.append(row(sec['open_period'], '期初余额', None, None, o['direction'],
                           o['balance'], 'opening', 'o'))
            for idx, pr in enumerate(sec['periods']):
                cu, yt = pr['current'], pr['ytd']
                out.append(row(pr['label'], '本期合计', cu['debit'], cu['credit'],
                               cu['direction'], cu['balance'], 'current', '%s.c' % idx))
                out.append(row(pr['label'], '本年累计', yt['debit'], yt['credit'],
                               yt['direction'], yt['balance'], 'ytd', '%s.y' % idx))
            if not sec['periods']:
                # 只期初无发生额科目：补一条 本年累计(0) 行（累计为 0、余额=期初）。
                t = sec['total']
                out.append(row(sec['open_period'], '本年累计', t['debit'], t['credit'],
                               t['direction'], t['balance'], 'ytd', 't'))
        return out

    def _cn_gl_cols(self, report, options, cols, currency, debit, credit, direction, balance):
        """按 options['columns'] 顺序造列字典。debit/credit/balance 数值列(留空 name，框架
        据 no_format 格式化；None ⇒ 空 blank，含「平」余额与期初发生额)；direction string 列
        预置 name 原样保留。"""
        by_label = {'debit_amt': debit, 'credit_amt': credit,
                    'direction': direction, 'balance': balance}
        out = []
        for c in cols:
            label = c.get('expression_label')
            val = by_label.get(label)
            d = report._build_column_dict(val, c, options=options, currency=currency)
            if label == 'direction' and val not in (None, ''):
                d['name'] = val          # string 列：预置 name ⇒ 框架不再覆盖
            out.append(d)
        return out

    # ----------------------------------------------------------------- helpers
    def _cn_gl_company(self, report, options):
        comp_ids = report.get_report_company_ids(options)
        return (self.env['res.company'].browse(comp_ids[0])
                if comp_ids else self.env.company)
