# -*- coding: utf-8 -*-
# R23-T2: retire the CN_TCI.ytd orphan and run the dangling-expression self-check.
#
# Odoo auto-deletes records dropped from a noupdate="0" data file, but only in
# `_process_end`, which runs AFTER every module's post-migration. So a self-check
# run here would still see the not-yet-cleaned orphan and emit a spurious WARNING
# on the very upgrade that fixes it. We therefore retire the orphan explicitly
# first (standard "retired record" migration idiom; the later `_process_end` is a
# harmless no-op on the already-gone record), so the self-check that follows
# observes the true steady state and stays silent unless a *real* regression ships.
from odoo import api, SUPERUSER_ID

from odoo.addons.suite_cn_statement.hooks import _log_dangling_expressions


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Retire CN_TCI.ytd (综合收益总额 本年累计) — see data/report_columns_asbe.xml
    # and design §7.2 C4-3 / R23-T2 for why it must not exist.
    orphan = env['account.report.expression'].search([
        ('report_line_id.code', '=', 'CN_TCI'),
        ('label', '=', 'ytd'),
    ])
    if orphan:
        env['ir.model.data'].search([
            ('model', '=', 'account.report.expression'),
            ('res_id', 'in', orphan.ids),
        ]).unlink()
        orphan.unlink()
    _log_dangling_expressions(env)
