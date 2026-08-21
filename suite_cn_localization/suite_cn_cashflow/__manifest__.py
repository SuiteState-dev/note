# -*- coding: utf-8 -*-
{
    'name': 'China - SME Cash Flow Statement',
    'version': '19.0.1.9.0',
    'category': 'Accounting/Localizations/Reporting',
    'summary': 'Direct-method Cash Flow Statement (22 lines), single standard: PRC Small Business Accounting Standard (ASSBE)',
    'description': """
Cash Flow Statement for the PRC Small Business Accounting Standard (direct method,
22 statutory lines).

The PRC standard treats cash-flow classification as an independent input dimension
that cannot be derived from the journal entry structure alone. This module adds a
per-line classification field (`cn_cash_flow_item_id`) whose value drives a pure-data
`account.report`. An explicit "unclassified" line makes any un-tagged cash flow
visible instead of silently mis-classifying it.

The per-account default is direction-split (R22): an account carries a separate
default cash-flow item for its debit side and its credit side, because a
double-direction account (e.g. 预付账款) classifies the two directions differently.
A line pre-fills from the side its balance sign falls on; a single-direction account
simply sets the same item on both. A value-preserving migration copies the former
single default into both new fields.

Uninstall note: this module adds a column on account.move.line. Uninstalling removes
that column, so classification data is lost — EXPORT IT FIRST via Accounting →
Configuration → 现金流量项目归属 导出/回填 (a plain UTF-8 CSV, re-importable onto the
same database after reinstall; P-05 可移交性, R27-T3). Debit / credit / account of
every journal item are unchanged (P-01). An ``uninstall_hook`` nulls the references
first so the ``ondelete='restrict'`` foreign key (a deliberate runtime protection
against silently dropping historical classifications — see models/account_move_line.py)
does not block the uninstall. Retire an item in normal use by archiving it, not deleting.
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'OPL-1',
    'depends': ['account', 'account_reports'],
    'countries': ['cn'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/cash_flow_item_data.xml',
        'data/account_report_cash_flow.xml',
        'views/cash_flow_item_views.xml',
        'views/account_views.xml',
        'wizards/cashflow_config_views.xml',
        'wizards/cashflow_line_export_views.xml',
    ],
    # NB: data/draft/* (ASBE report + A* items) are intentionally NOT loaded —
    # ASBE is out of delivery scope until first-hand material lands (R11-T5).
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'auto_install': False,
}
