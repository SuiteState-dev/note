# -*- coding: utf-8 -*-
{
    'name': 'China - Financial Statement Presentation (报表版式)',
    'version': '19.0.1.27.0',
    'category': 'Accounting/Localizations/Reporting',
    'summary': 'Chinese reporting-form presentation for the official Balance '
               'Sheet / Profit & Loss: 年初余额 / 本年累计 columns (rendering forms in R21)',
    'description': """
Presentation-layer localisation (呈现层, L0) that shapes the **official** Chinese
Balance Sheet / Profit & Loss reports into the Chinese reporting form (报送形态).
Read-only over accounting data — no journal item, balance or account is modified.

This first version ships only the year-begin / YTD columns. The row-number mapping
(行次), Chinese header/footer, the two-sided Balance-Sheet layout and the XLSX / PDF
renderers arrive in R21.

Year-begin / YTD columns (年初余额 / 本年累计) append a second column to the four
official Chinese reports — 年初余额 (``to_beginning_of_fiscalyear``) on the two Balance
Sheets ``l10n_cn_assbe_bs`` / ``l10n_cn_asbe_bs``, and 本年累计金额 (``from_fiscalyear``)
on the two Profit & Loss reports ``l10n_cn_assbe_pl`` / ``l10n_cn_asbe_pl``.

Additive only — no official record is modified, so the columns survive ``-u`` of
``l10n_cn_reports`` (verified R16, re-verified R20). The unaffected-earnings lines are
handled explicitly (本年利润 year-begin is 0 by definition; 以前年度未分配 re-scopes its
sub-formulas to the fiscal-year start).

These columns were shipped by ``suite_cn_ledger`` through R19; R20 moved them here so the
account-group builder (state + install hook) and the pure report-presentation data live in
separate modules (see design §11.2). The move is pure data — the ``account.report.column``
and ``account.report.expression`` records are re-created identically, and deleting then
re-creating them loses zero accounting data.

Depends on ``l10n_cn_reports`` explicitly (it owns the report records these columns
extend) — a dependency ``suite_cn_ledger`` implied but never declared.
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'OPL-1',
    'depends': ['account', 'account_reports', 'l10n_cn_reports'],
    'countries': ['cn'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_account_views.xml',
        'data/report_columns_assbe.xml',
        'data/report_columns_asbe.xml',
        'data/statement_forms.xml',
        'data/statement_forms_asbe.xml',
        'data/trial_balance.xml',
        'data/general_ledger.xml',
        'data/subsidiary_ledger.xml',
        'data/quantity_ledger.xml',
        'wizards/export_wizard_views.xml',
        'wizards/tb_export_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
