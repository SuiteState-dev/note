# -*- coding: utf-8 -*-
from . import models
from . import wizards


def uninstall_hook(env):
    """Clear every account.move.line reference to this module's cash.flow.item
    records *before* they are deleted during uninstall, so the foreign key
    (``ondelete='restrict'``) does not abort the uninstall.

    Why a hook instead of ``ondelete='set null'``: the ``restrict`` on
    ``account.move.line.cn_cash_flow_item_id`` is a deliberate runtime
    protection (R12-A1) — deleting an item that classifies historical journal
    items would silently shift the Cash Flow Statement. That protection stays;
    items are retired by archiving (``active=False``), never deleted. This hook
    fires only on module uninstall, where dropping the column is the intent
    anyway. Direct SQL: fast, and no ORM recompute is wanted while tearing down.
    """
    env.cr.execute(
        "UPDATE account_move_line SET cn_cash_flow_item_id = NULL "
        "WHERE cn_cash_flow_item_id IS NOT NULL"
    )
