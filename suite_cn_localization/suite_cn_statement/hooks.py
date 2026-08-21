# -*- coding: utf-8 -*-
"""Install/upgrade self-check for the generated year-begin / YTD expressions.

R23-T2: the 年初余额 / 本年累计 columns are a *static, offline-generated* set of
``account.report.expression`` records (this module's ``data/report_columns_*.xml``).
The generator's guard must only emit an aggregation expression for a new label
(``bal_begin`` / ``ytd``) when *every* line its formula references will also carry
that label — otherwise the report raises ``Could not expand term CODE.label`` the
moment a user opens it. That failure is invisible until someone opens the report in
the browser (every prior round's programmatic ``_get_lines`` acceptance missed it).

This hook makes the failure visible at install/upgrade time instead: it re-runs the
fixed-point reachability check the generator should satisfy and logs a WARNING (with
the offending line code and the missing ``CODE.label``) for every dangling reference
it finds. Zero WARNING == every generated aggregation expression is fully expandable.
"""
import logging
import re

_logger = logging.getLogger(__name__)

# Matches an aggregation term ``CODE.label`` (identifiers only — never a bare
# account-code number such as ``600`` or ``1231.01``, which start with a digit).
_TERM = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)')


def _log_dangling_expressions(env):
    """Scan this module's aggregation expressions for references to a
    ``CODE.label`` that does not exist, and log one WARNING per dangling term.

    Returns the list of ``(line_code, label, formula, missing)`` tuples so tests
    and migrations can assert on it.
    """
    imd = env['ir.model.data'].search([
        ('module', '=', 'suite_cn_statement'),
        ('model', '=', 'account.report.expression'),
    ])
    our_exprs = env['account.report.expression'].browse(imd.mapped('res_id')).exists()
    if not our_exprs:
        return []

    # Availability set: (line_code, label) for every expression on every report
    # our expressions touch — this is the ground truth the aggregation terms
    # resolve against, exactly like the report engine's own expansion.
    reports = our_exprs.report_line_id.report_id
    have = set()
    for line in env['account.report.line'].search([('report_id', 'in', reports.ids)]):
        if not line.code:
            continue
        for expr in line.expression_ids:
            have.add((line.code, expr.label))

    dangling = []
    for expr in our_exprs:
        if expr.engine != 'aggregation':
            continue
        line_code = expr.report_line_id.code
        missing = [
            '%s.%s' % (code, label)
            for code, label in _TERM.findall(expr.formula or '')
            if (code, label) not in have
        ]
        if missing:
            dangling.append((line_code, expr.label, expr.formula, missing))

    if dangling:
        for line_code, label, formula, missing in dangling:
            _logger.warning(
                "suite_cn_statement self-check: report line %s.%s references "
                "non-existent term(s) %s in aggregation formula %r — the report "
                "will raise 'Could not expand term' when opened. The generator "
                "guard must drop this expression (see design §7.2 C4-3 / R23-T2).",
                line_code, label, ', '.join(missing), formula,
            )
        _logger.warning(
            "suite_cn_statement self-check: %d dangling aggregation expression(s) "
            "found across %d generated expression(s).",
            len(dangling), len(our_exprs),
        )
    else:
        _logger.info(
            "suite_cn_statement self-check: OK — %d generated aggregation "
            "expression(s), zero dangling references.",
            sum(1 for e in our_exprs if e.engine == 'aggregation'),
        )
    return dangling


def post_init_hook(env):
    """Run the dangling-expression self-check after a fresh install."""
    _log_dangling_expressions(env)
