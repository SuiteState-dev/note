# -*- coding: utf-8 -*-
# =============================================================================
# HARD BOUNDARY — READ BEFORE EDITING (R20-S4)
# -----------------------------------------------------------------------------
# This module is a BRIDGE. It holds ONLY the mapping data that couples the
# Cash Flow Statement to the statement-presentation mechanism — i.e. data that
# is meaningless unless BOTH sides are installed.
#
# It MUST NOT contain:
#   - rendering / presentation logic          → belongs in suite_cn_statement
#   - the cash-flow report definition or items → belongs in suite_cn_cashflow
#
# It ``auto_install``s: Odoo installs it automatically once (and only once) both
# suite_cn_cashflow and suite_cn_statement are present, and uninstalls it as soon
# as either side goes away. Do not add it to any module's ``depends`` — that would
# defeat the automatic on/off behaviour.
#
# This round (R20) it ships NO data — it is a skeleton. The 行次映射 (row-number
# mapping of the Cash Flow Statement onto the R21 statement renderer) lands here
# in R21. See l10n_cn_design.md §11.2.
# =============================================================================
{
    'name': 'China - Cash Flow × Statement Bridge',
    'version': '19.0.1.2.0',
    'category': 'Accounting/Localizations/Reporting',
    'summary': 'Bridge: couples the Chinese Cash Flow Statement to the statement '
               'presentation mechanism (row-number mapping lands in R21)',
    'description': """
Bridge module (桥接) between ``suite_cn_cashflow`` and ``suite_cn_statement``.

It carries only the data that is meaningful when **both** sides are installed — the
row-number mapping (行次) of the Cash Flow Statement onto the statement renderer. That
mapping arrives in R21; this round the module is a skeleton so the structure exists and
its ``auto_install`` behaviour can be relied on.

``auto_install`` is True: Odoo installs this module automatically once both
``suite_cn_cashflow`` and ``suite_cn_statement`` are present, and removes it when either
side is uninstalled. It is intentionally **not** listed in any module's ``depends``.
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'OPL-1',
    'depends': [
        'suite_cn_cashflow',
        'suite_cn_statement',
    ],
    # NB: no ``countries`` here on purpose. For an auto_install module, Odoo gates
    # auto-installation on the company country (ir_module.button_install → must_install:
    # ``module.country_ids & company_countries``). Both dependencies are already
    # China-specific, so the CN-ness is guaranteed transitively; adding countries here
    # would only make the bridge fail to auto-install whenever a Chinese company's
    # res.company.country_id is unset — a common oversight. Verified R20.
    'data': [
        'data/cashflow_form.xml',  # R21: 现金流量表 reporting-form mapping (22 lines).
    ],
    'installable': True,
    'auto_install': True,
}
