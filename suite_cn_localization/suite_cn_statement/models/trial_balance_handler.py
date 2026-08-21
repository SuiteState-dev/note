# -*- coding: utf-8 -*-
"""科目余额表 —— 严格六 / 八栏 (R47-T1).

一张【新建】的 account.report（挂官方 Trial Balance 变体），自带 custom_handler。
🔴 官方 Trial Balance 记录 / 官方 account_report.py / 官方 handler 【三个都不碰】——
本 handler 只在【我方新建报表】上取数（R47 裁决：「不加 custom handler」的真实内容是
「不碰官方机件」，官方试算平衡表本身就是 custom_handler 实现的，手段中性）。

为什么必须 custom_handler（而不是 account_codes 前缀）——
    「本期发生额·借/贷」「本年累计发生额·借/贷」是【毛额】：同一账户借方发生 100、贷方
    发生 80 两个数都要，不是净额 +20。account_codes / domain 引擎只 SUM(balance)=净额，
    分不出 SUM(debit) 与 SUM(credit)；数学上「期末=期初+借−贷」是一个方程两个未知数，
    从余额推不出两个毛额，必须回原始分录取 debit/credit 字段。全 Odoo 里唯一分借贷毛额
    的就是官方 Trial Balance 的 custom_handler（account_trial_balance_report.py:285）。

取数 SQL 与官方 Trial Balance【逐字同款范式】(R47 追加要求1)：SUM(debit)/SUM(credit)/
SUM(balance) 三列、`_get_report_query(options, date_scope)` 出日期窗、`_currency_table_*`
出汇率——目的是官方将来改了取数，我方照抄即可。

列的日期口径（date_scope，R47-T2 裁决）——
    期初余额·借/贷   to_beginning_of_period   累计到期首前一天（新列，非复用 bal_begin）
    本期发生额·借/贷 strict_range             仅选定期间内（毛额）
    本年累计发生额·借/贷 from_fiscalyear       年度首日→期末（毛额，八栏才显）
    期末余额·借/贷   from_beginning            累计到期末（余额按净额符号分借贷）

一级 roll-up（判据6）——
    动态 groupby=account_id 只出叶子账户（覆盖客户自建账户，Σ借=Σ贷 全集才完整）。
    一级汇总全部在【本 handler 的 _custom_line_postprocessor 里按点分前缀合成】(R47 选 B)：
    handler 与官方形状逐字一致，层级是我方自己报表上的纯 Python 后处理，官方机件零接触。
    roll-up 键（R47 规则①，须覆盖非点分连号编码）：有点→首个点前那段；无点→前 4 位。
    只合成【一级】（首段那层），中间层不合成（规则②）。
"""
from collections import OrderedDict

from odoo import api, models, _
from odoo.tools import SQL, float_is_zero


_MONETARY = {'monetary', 'integer', 'float'}
_YTD_LABELS = {'ytd_d', 'ytd_c'}      # 本年累计发生额 借/贷 —— 八栏专有列
# 余额列对（期初/期末），父行按方向重排只动这两对；发生额列(本期/本年累计)不动。
_BAL_PAIRS = (('open_d', 'open_c'), ('close_d', 'close_c'))


class CnTrialBalanceReportHandler(models.AbstractModel):
    _name = 'suite.cn.trial.balance.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = '科目余额表 Custom Handler (严格六/八栏)'

    # ------------------------------------------------------------ 六/八栏开关
    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        # 六/八栏 = 同一张报表两种列集，一个开关切换（R47：不做两个 account.report）。
        # 默认【八栏】(全列)；'six' 抽掉本年累计两列。屏幕端默认八栏(超集，列集恒一致)，
        # 中式版式导出向导按 六/八 单选把本项塞进 options 再取数。
        mode = (previous_options or {}).get('cn_tb_columns') or 'eight'
        options['cn_tb_columns'] = mode
        if mode == 'six':
            options['columns'] = [
                c for c in options['columns']
                if c.get('expression_label') not in _YTD_LABELS
            ]

    # -------------------------------------------------------------- 取数引擎
    def _report_custom_engine_cn_trial_balance(self, expressions, options, date_scope,
                                               current_groupby, next_groupby,
                                               offset=0, limit=None, warnings=None):
        """SQL 与官方 Trial Balance 逐字同款范式（R47 追加要求1）：SUM(debit)/SUM(credit)/
        SUM(balance) 三列。额外在【我方 handler 内】派生方向拆分键 bal_debit / bal_credit。

        🔴 R48-T1 方向落栏改造：余额落哪一栏由【科目自身余额方向属性】决定，【不随符号
        迁移】；实际净额在反向时【于原栏写负数】（二姐实务 observed）。故对 groupby 出的每
        个账户按 `_cn_resolve_direction` 定栏，把 signed balance 整个放进方向栏、另一栏留 0：
            方向=借 → bal_debit = balance（可负）, bal_credit = 0
            方向=贷 → bal_credit = -balance（可负）, bal_debit = 0
        (借-贷 == signed balance 恒成立，与旧「符号选栏」在无负数时同结果、有负数时不同：
         3103 属性贷、净额在借 ⇒ 贷栏写负数，而非旧法挪去借栏。)
        发生额列（本期/本年累计，subformula debit/credit）走原始 SUM，【不受方向影响】(T2)。
        subformula 选键、date_scope 出窗口。"""
        report = self.env['account.report'].browse(options['report_id'])
        current_groupbys = (
            [current_groupby] if current_groupby and not isinstance(current_groupby, list)
            else current_groupby or []
        )
        report._check_groupby_fields(current_groupbys)

        query = report._get_report_query(options, date_scope)

        select_groupby = SQL('')
        if current_groupbys:
            select_groupby = SQL('\n').join(
                SQL("%s AS %s,",
                    self.env['account.move.line']._field_to_sql("account_move_line", gb, query),
                    SQL.identifier(f'groupby_key_{gb}'))
                for gb in current_groupbys
            )
            query.groupby = SQL(',').join(
                SQL.identifier(f'groupby_key_{gb}') for gb in current_groupbys)

        sql = SQL(
            """
            SELECT
                %(select_groupby)s
                COALESCE(SUM(%(balance)s), 0.0) AS balance,
                COALESCE(SUM(%(debit)s), 0.0) AS debit,
                COALESCE(SUM(%(credit)s), 0.0) AS credit
            FROM %(tables)s
            %(currency_join)s
            WHERE %(where)s
            %(groupby_clause)s
            """,
            select_groupby=select_groupby,
            balance=report._currency_table_apply_rate(SQL("account_move_line.balance")),
            debit=report._currency_table_apply_rate(SQL("account_move_line.debit")),
            credit=report._currency_table_apply_rate(SQL("account_move_line.credit")),
            tables=query.from_clause,
            currency_join=report._currency_table_aml_join(options),
            where=query.where_clause,
            groupby_clause=SQL("GROUP BY %s", query.groupby) if query.groupby else SQL(),
        )
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()

        def split_signed(row, direction):
            # signed balance 整个落方向栏（反向即负数），另一栏 0 → 配 blank_if_zero 留空。
            bal = row['balance']
            if direction == 'debit':
                row['bal_debit'], row['bal_credit'] = bal, 0.0
            elif direction == 'credit':
                row['bal_debit'], row['bal_credit'] = 0.0, -bal
            else:
                # 退化路径（无 groupby 的聚合行，我方后处理器会丢弃、不进输出）：按符号。
                row['bal_debit'] = bal if bal > 0 else 0.0
                row['bal_credit'] = -bal if bal < 0 else 0.0
            return row

        if not current_groupbys:
            if not results:
                return {'balance': 0.0, 'debit': 0.0, 'credit': 0.0,
                        'bal_debit': 0.0, 'bal_credit': 0.0, 'has_sublines': False}
            r = split_signed(results[0], None)
            r['has_sublines'] = True
            return r

        # groupby=account_id：逐账户按余额方向属性落栏。
        gkey = current_groupbys[0]
        acc_ids = [r[f'groupby_key_{gkey}'] for r in results]
        accounts = self.env['account.account'].browse([a for a in acc_ids if a])
        dir_of = {a.id: self._cn_resolve_direction(a)[0] for a in accounts}
        return [
            (r[f'groupby_key_{gkey}'],
             {**split_signed(r, dir_of.get(r[f'groupby_key_{gkey}'])), 'has_sublines': False})
            for r in results
        ]

    # ------------------------------------------------------- 一级 roll-up (选 B)
    @api.model
    def _cn_tb_rollup_key(self, code):
        """R47 规则①：有点 → 首个点之前那段；无点 → 前 4 位。
        连号客户（金蝶星辰迁来的 2221001 那批，R45 已证实真实人群）无点，取前 4 位，
        故 2221001 与点分 2221.01 都归到键 '2221'。"""
        code = code or ''
        if '.' in code:
            return code.split('.', 1)[0]
        return code[:4]

    # ---------------------------------------------------------- 余额方向解析 (T1)
    @api.model
    def _cn_direction_by_code(self):
        """我方发行件（ASSBE_CHART）的 code→余额方向 快查（唯一权威值，R48 裁决）。
        星辰 CSV 是制备期底稿，【不入此运行时路径】。守卫导入同 national_names：coa 缺席
        则退空、handler 自会回落 account_type 推导（§11.2 两模块不硬绑）。"""
        try:
            from odoo.addons.suite_cn_coa.models.assbe_chart_data import ASSBE_DIRECTION_BY_CODE
        except ImportError:
            return {}
        return ASSBE_DIRECTION_BY_CODE

    @api.model
    def _cn_derive_direction(self, account_type):
        """account_type 推导兜底（仅客户自建、无字段无发行件时）。资产/成本→借；
        负债/权益/收入→贷。🔴 备抵类（累计折旧/减值等 account_type 仍是资产、方向却是贷）
        推导必翻车（R48-Q4），故凡走到本层即 source='derived'、由 handler 随件告警。"""
        at = account_type or ''
        if at.startswith('asset') or at.startswith('expense'):
            return 'debit'
        return 'credit'

    def _cn_resolve_direction(self, account):
        """余额方向三层解析，返回 (direction, source)。source ∈ {field, issued, derived}：
            field   客户在 account.account 上显式指定（自建/覆盖，最高优先）
            issued  我方发行件方向列（ASSBE_CHART，标准科目权威值）
            derived account_type 推导兜底（真发生推导 ⇒ 触发告警，判据5/Q5）"""
        d = account.cn_balance_direction
        if d:
            return d, 'field'
        issued = self._cn_direction_by_code().get(account.code or '')
        if issued:
            return issued, 'issued'
        return self._cn_derive_direction(account.account_type), 'derived'

    def _cn_tb_zero_cols(self, template_cols):
        """按模板列（某叶子行的 columns，键/label/figure_type/column_group_key 已对齐
        options['columns']）造一份清零的列，用于累加合计。照 general_ledger 合计做法：
        复制既有列再改 no_format，不自造 _build_column_dict 参数。"""
        out = []
        for c in template_cols:
            nc = dict(c)
            nc['no_format'] = 0.0
            nc['is_zero'] = True
            out.append(nc)
        return out

    def _cn_tb_add_cols(self, acc, src, currency):
        for i, c in enumerate(src):
            val = c.get('no_format')
            if c.get('figure_type') in _MONETARY and isinstance(val, (int, float)) \
                    and not isinstance(val, bool):
                acc[i]['no_format'] = (acc[i]['no_format'] or 0.0) + val
                acc[i]['is_zero'] = float_is_zero(
                    acc[i]['no_format'], precision_rounding=currency.rounding)

    def _cn_prefix_direction(self, prefix, anchor_dir):
        """一级父行的余额方向（判据4）：先公司内锚账户（编码==前缀）解析值，再我方发行件
        方向列；都无 ⇒ None，父行保持列式合计不重排（退化分支，原样回报）。"""
        return anchor_dir.get(prefix) or self._cn_direction_by_code().get(prefix)

    def _cn_replace_balance_by_direction(self, cols, direction, currency):
        """父行【余额列对】(期初/期末)按父行自身方向重排：signed=借−贷 整个落方向栏、另栏
        0（判据4 设计：父行落栏由父科目固有方向定，不随子行方向或数值符号迁移，与二姐规则
        同构）。发生额列(本期/本年累计)不动——毛额随子行相加。借−贷==signed 恒成立 ⇒ 逐行
        勾稽、四组合计仍平。direction 为 None（无锚无发行）时不重排，退回列式合计。"""
        if direction not in ('debit', 'credit'):
            return
        idx = {c.get('expression_label'): i for i, c in enumerate(cols)}
        for dl, cl in _BAL_PAIRS:
            di, ci = idx.get(dl), idx.get(cl)
            if di is None or ci is None:
                continue
            signed = (cols[di].get('no_format') or 0.0) - (cols[ci].get('no_format') or 0.0)
            if direction == 'debit':
                cols[di]['no_format'], cols[ci]['no_format'] = signed, 0.0
            else:
                cols[di]['no_format'], cols[ci]['no_format'] = 0.0, -signed
            for i in (di, ci):
                cols[i]['is_zero'] = float_is_zero(
                    cols[i]['no_format'], precision_rounding=currency.rounding)

    @api.model
    def _cn_tb_national_names(self):
        """一级键 → 我方国标科目表标准名（R47 复核②）。连号客户（金蝶迁入，R45 证实真实
        人群）库里可能只有 2221001…、没有一条编码恰是 2221 ⇒ 公司内锚账户查不到 ⇒ 父行名
        本会显示光秃秃「2221」。回落改查我方 ASSBE 科目表（`suite_cn_coa` 手上全表）取
        『应交税费』。纯数据常量、无 ORM，故用带守卫的惰性导入：coa 在同套件恒在场；万一
        缺席则退回裸前缀，不硬依赖（保住 §11.2 两模块分立）。"""
        try:
            from odoo.addons.suite_cn_coa.models.assbe_chart_data import ASSBE_CHART
        except ImportError:
            return {}
        return {r['code']: r['name'] for r in ASSBE_CHART if r.get('parent') is None}

    def _custom_line_postprocessor(self, report, options, lines):
        """把动态 groupby 出的叶子账户行，按点分前缀合成【一级】父行；整表科目编码升序、
        合成父行紧排在其子行之前（规则③）；末尾一条合计行。判据6「一级==Σ明细」by
        construction（父行各列即其下子行同列之和）。"""
        # 分离叶子账户行（其余——如原 groupby 父行——不进合成，直接丢弃：合计由本处重建）。
        leaves = []
        for line in lines:
            acc_id = report._get_res_id_from_line_id(line['id'], 'account.account')
            if acc_id:
                leaves.append((acc_id, line))
        if not leaves:
            return lines

        company = self._cn_report_company_from_options(report, options)
        currency = company.currency_id
        accounts = self.env['account.account'].browse([a for a, _l in leaves])
        code_of = {a.id: (a.code or '') for a in accounts}
        name_of = {a.id: (a.name or '') for a in accounts}
        # 逐叶子解析方向来源；source='derived' 即真发生 account_type 推导 ⇒ 计入告警（判据5）。
        dir_src_of = {a.id: self._cn_resolve_direction(a) for a in accounts}
        derived_codes = sorted(
            (a.code or '') for a in accounts if dir_src_of[a.id][1] == 'derived')

        # 按一级键分组；组内、组间都按科目编码升序（规则③，装订顺序不能错）。
        groups = OrderedDict()
        for acc_id, line in sorted(leaves, key=lambda t: code_of.get(t[0], '')):
            key = self._cn_tb_rollup_key(code_of.get(acc_id, ''))
            groups.setdefault(key, []).append((acc_id, line))

        # 一级父行取名：编码恰等于前缀的账户名（我方发行的一级账户通常在），否则回落前缀本身。
        company_ids = report.get_report_company_ids(options)
        anchors = self.env['account.account'].search(
            [('code', 'in', list(groups.keys())), ('company_ids', 'in', company_ids)])
        anchor_name = {a.code: a.name for a in anchors}
        anchor_dir = {a.code: self._cn_resolve_direction(a)[0] for a in anchors}
        national = self._cn_tb_national_names()   # 无锚时的标准名回落（复核②）

        def parent_name_of(prefix):
            # 先公司内锚账户名（客户自定名优先），无锚回落我方国标标准名，再无回落裸前缀。
            return anchor_name.get(prefix) or national.get(prefix, '')

        result = []
        grand = None
        unmapped = 0  # 未归入任何一级的叶子行数（判据6 回报项，期望 0）
        for prefix in sorted(groups.keys()):
            children = groups[prefix]
            if not prefix:
                unmapped += len(children)  # 空编码账户无法归并（异常，原样计数上报）
            template = children[0][1]['columns']

            # 复核①：单叶子一级组折叠。组内恰一个叶子且其编码 == 一级键 ⇒ 该叶子【就是】
            # 一级账户本身、其下无明细，合成父行只会与它数值相同并排重复（金蝶/用友单叶子
            # 不重复出行，会计见重复行会先问「怎么两行」）⇒ 默认折叠成一行（非开关）。
            # 注意：单叶子但编码 != 键（如只有 2221001 无 2221）不折叠——那是「一级 + 单条
            # 明细」的合法两行，父行名与明细名不同。
            if len(children) == 1 and code_of.get(children[0][0]) == prefix:
                acc_id, line = children[0]
                line['level'] = 1
                line['parent_id'] = None
                line['cn_code'] = code_of.get(acc_id, '')
                line['cn_name'] = name_of.get(acc_id, '')
                line['cn_collapsed'] = True   # 折叠出来的顶层单行（非未归并异常）
                result.append(line)
                if grand is None:
                    grand = self._cn_tb_zero_cols(line['columns'])
                self._cn_tb_add_cols(grand, line['columns'], currency)
                continue

            sub_cols = self._cn_tb_zero_cols(template)
            for acc_id, line in children:
                self._cn_tb_add_cols(sub_cols, line['columns'], currency)
            parent_id = report._get_generic_line_id(None, None, markup={'cn_tb_rollup': prefix})
            pname = parent_name_of(prefix)
            parent = {
                'id': parent_id,
                'name': ('%s %s' % (prefix, pname)).strip(),
                'level': 1,
                'unfoldable': False,
                'columns': sub_cols,
                'cn_code': prefix,
                'cn_name': pname,
                'cn_is_parent': True,
            }
            result.append(parent)
            for acc_id, line in children:
                line['level'] = 3
                line['parent_id'] = parent_id
                line['cn_code'] = code_of.get(acc_id, '')
                line['cn_name'] = name_of.get(acc_id, '')
                result.append(line)
            if grand is None:
                grand = self._cn_tb_zero_cols(template)
            self._cn_tb_add_cols(grand, sub_cols, currency)   # 合计取叶子级（重排前）
            # 父行余额列按父自身方向重排（判据4）——在并入 grand 之后，故 grand 仍是叶子真值。
            self._cn_replace_balance_by_direction(
                sub_cols, self._cn_prefix_direction(prefix, anchor_dir), currency)

        if grand is not None:
            for c in grand:
                c['blank_if_zero'] = False   # 合计行恒显，不因 0 留空
            result.append({
                'id': report._get_generic_line_id(None, None, 'total'),
                'name': _('合计'),
                'level': 0,
                'unfoldable': False,
                'columns': grand,
                'cn_code': '',
                'cn_name': _('合计'),
                'cn_is_total': True,
            })

        # 判据5 / Q5：真发生 account_type 推导时才出条件告警（非恒显声明）；给条数 + 科目
        # 编码 + 去哪改，不写「见日志」（惯例5）。账簿对内+审计，提示放表内无 T3 受众问题。
        if derived_codes:
            wcols = self._cn_tb_zero_cols(grand) if grand is not None else []
            for c in wcols:
                c['blank_if_zero'] = True
            result.append({
                'id': report._get_generic_line_id(None, None, markup={'cn_tb_dir_warn': 1}),
                'name': _(
                    '注：以下 %(n)s 个科目无「余额方向」属性，已按科目类型推定落栏，备抵类'
                    '可能因此摆反，请在【会计 › 配置 › 科目表】相应科目上设置「余额方向」后'
                    '复核：%(codes)s',
                    n=len(derived_codes), codes='、'.join(c for c in derived_codes if c)),
                'level': 0,
                'unfoldable': False,
                'columns': wcols,
                'cn_code': '',
                'cn_name': '',
                'cn_is_dir_warning': True,
            })
        return result

    # ----------------------------------------------------------------- helpers
    def _cn_report_company_from_options(self, report, options):
        comp_ids = report.get_report_company_ids(options)
        return (self.env['res.company'].browse(comp_ids[0])
                if comp_ids else self.env.company)
