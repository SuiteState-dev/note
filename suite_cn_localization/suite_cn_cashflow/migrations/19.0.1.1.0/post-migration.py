# -*- coding: utf-8 -*-
"""Clear stale `subformula` on cash-flow report expressions.

Why this migration exists
-------------------------
Between R8 and R9 several report expressions changed `engine` from `domain`
to `aggregation` while keeping the same XML id (e.g. CN_CF_S_7 / CN_CF_S_19,
which turned from a domain detail/unclassified line into a subtotal).

XML data updates only overwrite the fields present in the record; a field that
is *omitted* keeps its previous value. The R9 XML no longer emits `subformula`
for aggregation expressions, so the old `-sum` (valid only for the `domain`
engine) survived on records upgraded in place. Under the aggregation engine
`-sum` is parsed as a bounds sub-formula and makes the report raise / mis-total.

A clean install is unaffected (no prior value); only `-u` upgrades of an
existing install hit this. This script clears `subformula` on every aggregation
expression of the two cash-flow reports so upgraded databases match a fresh
install.
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    reports = env['account.report'].search([
        ('id', 'in', [
            env.ref('suite_cn_cashflow.cn_cash_flow_a', raise_if_not_found=False).id
            if env.ref('suite_cn_cashflow.cn_cash_flow_a', raise_if_not_found=False) else 0,
            env.ref('suite_cn_cashflow.cn_cash_flow_s', raise_if_not_found=False).id
            if env.ref('suite_cn_cashflow.cn_cash_flow_s', raise_if_not_found=False) else 0,
        ]),
    ])
    stale = env['account.report.expression'].search([
        ('report_line_id.report_id', 'in', reports.ids),
        ('engine', '=', 'aggregation'),
        ('subformula', '!=', False),
    ])
    if stale:
        stale.write({'subformula': False})
