# -*- coding: utf-8 -*-
from odoo import fields, models


class CnStatementForm(models.Model):
    """One reporting-form (报送版式) definition per official account.report.

    Renderer-private mapping data (R21-B1): the row numbers (行次), reporting-form
    row names and column order live here, NOT on the official report records. The
    export renderer reads these to shape the official report values into the PRC
    reporting form. Nothing is ever written onto the official ``account.report`` /
    ``account.report.line`` records — ``report_id`` / ``report_line_id`` are plain
    foreign keys stored on THIS module's tables, so ``-u l10n_cn_reports`` is safe.
    """
    _name = 'suite.cn.statement.form'
    _description = 'Chinese Reporting-Form Layout'
    _order = 'report_id'

    report_id = fields.Many2one(
        'account.report', string='Official report', required=True,
        ondelete='cascade', index=True,
        help='The official account.report whose values this form re-shapes.')
    title = fields.Char(
        string='报表名', required=True, translate=True,
        help='Chinese statutory statement name, e.g. 资产负债表.')
    title_suffix = fields.Char(
        string='适用说明后缀', translate=True,
        help='Statutory 适用说明 appended to the title on row 0, e.g. '
             '（适用执行小企业会计准则的企业）. Per-form (会小企 vs 会企 wording '
             'differs), never hard-coded in the renderer (R26-T1).')
    form_no = fields.Char(
        string='表号',
        help='Statutory form number printed on row 1 (last column), e.g. 会小企01表 '
             '/ 会企01表. Per-form (R26-T1).')
    sheet_name = fields.Char(
        string='工作表名',
        help='XLSX worksheet name mandated by the filing system, e.g. 资产负债表 / '
             '利润表_月季报 / 利润表_年. Per-form: BS carries NO period suffix (月季报 '
             'and 年报 are cell-identical), PL/CF do (R26-T2). Falls back to title.')
    layout = fields.Selection(
        [('single', '单栏'), ('two_column', '两栏对开')],
        string='版式', default='single', required=True,
        help='two_column = the Balance-Sheet 资产 / 负债权益 side-by-side layout.')
    footer_note = fields.Text(
        string='页脚取数口径披露',
        help='中式版式导出件页脚的【静态口径声明】——恒真、不依赖数值，故以【中性格式】'
             '渲染（非 dc_notice 勾稽告警的红字：§4.5.7.1(ii) 告警与声明的载体规范不同，'
             'R44-T2）。与官方报表尾部 account.report.line 披露行【文案一字一致】，'
             '专补【中式版式 XLSX】这条 form 驱动的导出路径——它按 form 行取数、不含'
             '官方 account.report.line，故披露行不进这条路径（惯例29：载体可见人群须∩问题'
             '相关人群）。translate=False：恒渲染中文，不随用户界面语言回落。')
    period_scope = fields.Selection(
        [('monthly_quarterly', '月季报'), ('annual', '年报'), ('any', '通用(月季=年报)')],
        string='报送期间', default='monthly_quarterly', required=True,
        help='Which filing cadence this form serves (R26-T2). The export wizard '
             'lets the accountant pick 月季报/年报 (isomorphic to the tax-bureau '
             '报送期间 单选). 单选 default = 月季报 (used 4×/yr vs 年报 1×). '
             "'any' = the two cadences are cell-identical so ONE form serves both "
             '(ASSBE Balance Sheet only — verified R26). A report that has a '
             "monthly_quarterly form but NO annual form (ASBE, whose 年报 column "
             'layout has no source material) must NOT silently fall back — the '
             'wizard raises 该准则的年报版式尚未支持 instead.')
    standard_version = fields.Selection(
        [('na', '不适用(ASSBE)'), ('executed', '已执行版'), ('not_executed', '未执行版')],
        string='准则版本', default='na', required=True,
        help='准则版本开关, only meaningful for ASBE (执行企业会计准则的企业): the '
             '已执行版 / 未执行版 distinction (R24). ASSBE has no such switch → na. '
             'Built into the uniqueness key now so unfreezing the ASBE 未执行版 later '
             'needs no schema migration (R26-T2, per §4.5.2 three-dim enum).')
    period_mode = fields.Selection(
        [('point', '时点 (YYYY-MM-DD)'), ('range', '期间 (YYYY年M期)')],
        string='期间格式', default='range', required=True)
    has_row_no = fields.Boolean(
        string='含行次列', default=True,
        help='Whether the reporting form prints a 行次 (row-number) column. The '
             'tax-bureau ASBE Profit & Loss has no row-number column at all → set '
             'False (the renderer then drops the column and collapses the offset). '
             'ASSBE forms and both Balance Sheets keep it True (R24-T2).')
    column_ids = fields.One2many(
        'suite.cn.statement.column', 'form_id', string='Columns')
    row_ids = fields.One2many(
        'suite.cn.statement.row', 'form_id', string='Rows')
    rows_from_id = fields.Many2one(
        'suite.cn.statement.form', string='行结构借用自', ondelete='restrict',
        help='R26-T2: an 年报 form differs from its 月季报 sibling ONLY in column '
             '口径 (本年累计|上年 vs 本期|本年累计) — the 行次/行名/取数行 are identical. '
             'Rather than duplicate ~40–70 rows (which would drift), the 年报 form '
             'leaves row_ids empty and borrows them from the 月季报 form named here. '
             'Single source of truth: the two cadences can never diverge. Empty = '
             'this form owns its own rows.')

    def _effective_rows(self):
        """The rows to render — own rows, or the borrowed sibling's (rows_from_id).
        Keeps the 年报/月季报 row structure single-sourced (R26-T2)."""
        self.ensure_one()
        return (self.rows_from_id or self).row_ids

    _sql_constraints = [
        # R26-T2: a report may now carry MORE THAN ONE form — the same official
        # report (e.g. l10n_cn_assbe_pl) feeds both the 月季报 and the 年报 form,
        # which differ only in column 口径 (本期|本年累计 vs 本年累计|上年). The key
        # is the full three-dim enum (报送小类 = report_id, 报送期间 = period_scope,
        # 准则版本 = standard_version) so unfreezing the ASBE 未执行版 later is a pure
        # data add. Replaces the old unique(report_id).
        ('report_period_version_uniq',
         'unique(report_id, period_scope, standard_version)',
         'A report can have only one Chinese reporting-form per (报送期间 × 准则版本).'),
    ]


class CnStatementColumn(models.Model):
    """A value column of a reporting form, in reporting-form order.

    ``expression_label`` names which of the report's column expressions to read
    (e.g. ``balance`` / ``bal_begin`` / ``ytd``). The order here overrides the
    on-screen column ``sequence`` — that is how the P&L shows 本年累计 before 本月
    even though the on-screen year-to-date column sits at ``sequence=900``.
    """
    _name = 'suite.cn.statement.column'
    _description = 'Chinese Reporting-Form Column'
    _order = 'form_id, sequence, id'

    form_id = fields.Many2one(
        'suite.cn.statement.form', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    header = fields.Char(string='列名', required=True, translate=True)
    expression_label = fields.Char(
        string='取值来源 (expression_label)', required=True,
        help='Which report column expression to read for this reporting column.')
    column_group = fields.Selection(
        [('primary', '本期 / 期末'), ('comparison', '上期')],
        string='列组', default='primary', required=True,
        help="Which report column GROUP feeds this column. 'primary' = the report's "
             "own current-period group. 'comparison' = the prior comparable period "
             "(上期金额): the export forces a same_last_year comparison, so an annual "
             "filing gets the prior fiscal year and a quarterly filing gets the same "
             "quarter last year (R24-T1, verified). The tax-bureau ASBE P&L 上期金额 "
             "column is the only comparison column so far; every other column is "
             "primary (期末余额 / 本年累计 / 本月 all live in the current group).")


class CnStatementRow(models.Model):
    """A reporting-form row: a 行次 line, or an un-numbered section-title row.

    ``report_line_id`` may be empty — a reporting-form row that has no official
    source line (section titles, or statutory rows the chart cannot fill). Such
    rows keep their 行次 and 行名 and render with an empty value (never crash,
    never collapse). See the module README for the empty-value policy.
    """
    _name = 'suite.cn.statement.row'
    _description = 'Chinese Reporting-Form Row'
    _order = 'form_id, sequence, id'

    form_id = fields.Many2one(
        'suite.cn.statement.form', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    row_no = fields.Char(
        string='行次', help='Statutory line number; empty for section-title rows.')
    name = fields.Char(
        string='行名', required=True, translate=True,
        help='Reporting-form (报送口径) row name; may differ from the official line.')
    report_line_id = fields.Many2one(
        'account.report.line', string='Source line', ondelete='cascade',
        help='Official report line whose value feeds this row. Empty = no source '
             '(section title, or a statutory row with no chart source): value blank.')
    section = fields.Selection(
        [('left', '左 (资产)'), ('right', '右 (负债和所有者权益)')],
        string='栏位', help='Only for the two-column Balance-Sheet layout.')
    is_header = fields.Boolean(
        string='标题行', default=False,
        help='Section-title row: no 行次, no value.')
