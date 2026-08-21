# -*- coding: utf-8 -*-
# R24-T2: `suite.cn.statement.form.has_row_no` is new (default True). The
# ASSBE Balance Sheet and P&L forms that predate it must stay True — they print
# a 行次 (row-number) column. Adding a non-computed column WITH a default already
# backfills existing rows to True, but set it explicitly so the invariant holds
# regardless of column-init timing (belt and braces; the task book requires a
# migration for the existing forms).
def migrate(cr, version):
    cr.execute(
        "UPDATE suite_cn_statement_form SET has_row_no = TRUE "
        "WHERE has_row_no IS NULL"
    )
