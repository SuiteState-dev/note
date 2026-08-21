# -*- coding: utf-8 -*-
# R23-T5-3: drop the deprecated single default field
# `account.account.cn_default_cash_flow_item_id` (superseded by the R22-T1
# direction-split debit/credit defaults). Its value was copied into both new
# fields by the 19.0.1.5.0 migration; the field is removed from the model in this
# same release, so this drops the now-orphan column.
#
# Raw SQL rather than `odoo.upgrade.util.remove_field`: that helper is not
# installed in this deployment and pulling it in would add a build-triggering
# dependency for a single column drop. Pre-migration runs before model reflection,
# so dropping the column here is clean; Odoo's `ir.model.fields` reflection removes
# the orphan field metadata on the same upgrade (the field is gone from the code).


def migrate(cr, version):
    # SAFETY NET before the drop (R23 review): guarantee no classification is lost
    # even on a store that somehow never ran the 19.0.1.5.0 value-preserving copy.
    # For any account where the legacy column still holds a value a split field
    # never received, backfill it now. Idempotent — a no-op once 1.5.0 has run, and
    # on a greenfield / empty DB. The DROP stays LAST, after this guarantee holds.
    cr.execute("""
        UPDATE account_account
           SET cn_default_cash_flow_item_debit_id =
                   COALESCE(cn_default_cash_flow_item_debit_id, cn_default_cash_flow_item_id),
               cn_default_cash_flow_item_credit_id =
                   COALESCE(cn_default_cash_flow_item_credit_id, cn_default_cash_flow_item_id)
         WHERE cn_default_cash_flow_item_id IS NOT NULL
           AND (cn_default_cash_flow_item_debit_id IS NULL
                OR cn_default_cash_flow_item_credit_id IS NULL)
    """)

    # Drop LAST — the backfill above has preserved every legacy value into the two
    # split fields. DROP COLUMN also removes the m2o foreign-key constraint. Idempotent.
    cr.execute(
        "ALTER TABLE account_account "
        "DROP COLUMN IF EXISTS cn_default_cash_flow_item_id"
    )
