# -*- coding: utf-8 -*-
# =============================================================================
# HARD BOUNDARY — READ BEFORE EDITING (R19-C2)
# -----------------------------------------------------------------------------
# This module is a DEPENDENCY AGGREGATOR ONLY. It exists so a single install
# pulls the whole China localization set in one click.
#
# It MUST NEVER contain any code, model, field, data, view, security rule,
# report, asset, hook, or wizard. Not now, not "just this once".
#
# Each child module (suite_cn_coa, suite_cn_statement, suite_cn_cashflow, ...)
# attaches DIRECTLY to the official base (account / account_reports / l10n_cn_reports),
# installs independently, and does NOT depend on this aggregator. This is deliberate:
# it keeps us out of the l10n_cn_sme trap (a shared code base层 that every
# module was forced to depend on). See l10n_cn_design.md §11.5 and §C3.
#
# If you are about to add a `data`, `models`, or code file here: STOP. Put it
# in the relevant child module instead. If no child fits, create a new child.
# =============================================================================
{
    'name': 'China Localization Suite (SuiteState)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'One-click install of the SuiteState China localization set '
               '(dependency aggregator — contains no code)',
    'description': """
China Localization Suite — dependency aggregator
================================================

Installing this module installs the full SuiteState China localization set in
one step. **This module contains no code, models, data, views or security** —
it is nothing but a ``depends`` list.

Currently aggregates:

- ``suite_cn_coa`` — account-group hierarchy (科目分级); makes the native Trial
  Balance (科目余额表) and General Ledger (三栏式明细账) fold the Chinese way.
- ``suite_cn_statement`` — year-begin / YTD columns (年初余额 / 本年累计) on the
  official Balance Sheet / P&L (report-presentation data; renderers land in R21).
- ``suite_cn_cashflow`` — direct-method Cash Flow Statement (ASSBE, 22 lines).

Not listed in ``depends`` but pulled in automatically: ``suite_cn_cashflow_statement``,
a bridge that ``auto_install``s only when both ``suite_cn_cashflow`` and
``suite_cn_statement`` are present.

Each child module attaches directly to the official ``account`` /
``account_reports`` / ``l10n_cn_reports`` base and installs on its own. Children do
not depend on this aggregator; the only sibling dependency is the ``auto_install``
bridge above (that is its whole purpose). Install only the pieces you need, or install
this module to get everything.

**Boundary (do not remove):** this module will never hold shared code. Common
behaviour, if ever needed, extends the official base inside the module that
needs it — never a shared layer here (see l10n_cn_design.md §11.5).
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'OPL-1',
    'depends': [
        'suite_cn_coa',
        'suite_cn_statement',
        'suite_cn_cashflow',
        # suite_cn_cashflow_statement is NOT listed here on purpose — it is an
        # auto_install bridge, pulled in automatically once its two sides are present.
    ],
    'countries': ['cn'],
    'data': [],  # MUST stay empty — see HARD BOUNDARY above.
    'installable': True,
    'auto_install': False,
}
