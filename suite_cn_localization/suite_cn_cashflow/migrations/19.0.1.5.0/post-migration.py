# -*- coding: utf-8 -*-
"""R22-T1: seed the direction-split cash-flow defaults from the deprecated
single field.

Before R22 every account carried one default (``cn_default_cash_flow_item_id``),
applied to a line regardless of its direction. R22 splits that into a debit-side
and a credit-side default (``cn_default_cash_flow_item_debit_id`` /
``..._credit_id``). The old single-direction behaviour is exactly "same item on
both sides", so this copies the old value into BOTH new fields for every account
that has one.

This is a value-preserving migration (R22-T1-V8, the hard gate): it touches only
``account.account`` master data — no journal item is read or written and no ORM
recompute is triggered — so the Cash Flow Statement is byte-for-byte identical
before and after the upgrade. Splitting a double-direction account's two sides
apart afterwards is a manual master-data edit, not a migration concern.

The new columns already exist when a post-migration runs (Odoo creates new
fields' columns during model loading, before the migration scripts), so a plain
UPDATE is safe.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE account_account
           SET cn_default_cash_flow_item_debit_id = cn_default_cash_flow_item_id,
               cn_default_cash_flow_item_credit_id = cn_default_cash_flow_item_id
         WHERE cn_default_cash_flow_item_id IS NOT NULL
           AND cn_default_cash_flow_item_debit_id IS NULL
           AND cn_default_cash_flow_item_credit_id IS NULL
    """)
