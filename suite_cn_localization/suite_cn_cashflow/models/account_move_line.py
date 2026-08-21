# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Editable stored computed field (compute + store + readonly=False):
    #  - fires on UI, on import and on ORM/API writes (an onchange would only
    #    cover the UI form), so batch-created or API-created entries still get
    #    the account's default;
    #  - a manual choice survives because the compute only reassigns a value it
    #    can recognise as auto-filled (see _compute below).
    cn_cash_flow_item_id = fields.Many2one(
        'cash.flow.item', string='Cash Flow Item', index=True,
        ondelete='restrict',
        compute='_compute_cn_cash_flow_item_id', store=True, readonly=False,
        copy=True,
        help="PRC cash-flow classification of this line. Set it on the "
             "counterpart of a cash/bank line; it drives the Cash Flow Statement.\n"
             "A reversal (红冲 / 反过账 via Add Reversal Entry) keeps this "
             "classification from the original line so it cancels on the same "
             "statement line. This does NOT apply to a red-ink entry you build by "
             "hand or by keying a negative amount — that has no link to an original "
             "entry, so it follows the account's own default like any other line.")
    # copy=True is written EXPLICITLY, not left to the default: this is a
    # computed + stored + readonly=False field, whose `copy` default is not
    # guaranteed stable across versions, and the whole R23-T5-1 reversal guard
    # RELIES on the reversed line inheriting the original classification via
    # copy_data(). If copy were False the reversal line would come in empty, the
    # guard would skip it, and the compute would not re-fill it — turning the old
    # "double-count" bug into a worse "under-count" (the line shows nothing).
    # ondelete='restrict' (not the default 'set null'): deleting a referenced item
    # would silently drop the classification on historical journal items and shift
    # the cash-flow statement with no warning. Referenced items can't be deleted;
    # archive them instead (active=False). Verified R12-A1: the report domain
    # matches by `code` and is NOT active-filtered, so an archived item keeps its
    # historical figures on the statement.

    def _cn_default_for(self, account, balance):
        """The account's default cash-flow item for a line on the direction
        implied by `balance` (R22-T1). Direction = the balance SIGN — verified
        R22-T1: `debit` / `credit` / `balance` are all populated at create for
        both misc entries and invoice lines, so the sign is reliable at compute
        time. balance < 0 -> credit side; balance >= 0 -> debit side (a zero
        line takes the debit default and contributes nothing to the statement).

        Before R22 there was one default per account regardless of direction; a
        single-direction account is just 'same item on both sides', so this keeps
        the old result for those accounts and only differs on double-direction
        accounts, which is the whole point of the split."""
        if not account:
            return self.env['cash.flow.item']
        if balance < 0:
            return account.cn_default_cash_flow_item_credit_id
        return account.cn_default_cash_flow_item_debit_id

    @api.depends('account_id', 'balance')
    def _compute_cn_cash_flow_item_id(self):
        """Follow the account AND the direction (R22-T1, extends R11-T3 option a).

        An *auto-filled* value re-derives when the account or the balance sign
        changes; a *manual* value is kept — even when the new account+direction
        has a default of its own (R22-T1-V4). 'Auto' = the value equals the
        default the line held under its PREVIOUS account+direction (the equality
        heuristic chosen R22-T1: a manual value that happens to equal that
        default is indistinguishable from auto — an accepted limitation).

        Covers create and the UI onchange, where `_origin` is the saved record
        and so exposes the OLD account+balance. A direct ORM write on a persisted
        record is NOT covered here — there `_origin` is the record itself, already
        holding the new values, so the previous default can't be recovered;
        `write()` below handles that path by capturing state before the write.
        """
        for line in self:
            if line.move_id.reversed_entry_id:
                # Reversal line (R23-T5-1): keep the classification copied from the
                # original line. A red-ink reversal is the NEGATION of the original
                # entry, not a new opposite-direction cash flow. `_reverse_moves`
                # copies the line (cn_cash_flow_item_id has copy=True → the original
                # item is carried) then flips debit/credit; re-deriving from the
                # flipped balance sign would pull the OPPOSITE-side default and
                # double-inflate the statement (the original inflow is never undone
                # AND a phantom outflow appears on the opposite line — net is right,
                # the two line totals are not). Leave the copied value untouched so
                # the reversal cancels the original on its own line.
                # BOUNDARY (design §7.2 T5-1): this only catches `_reverse_moves`
                # reversals (they set `reversed_entry_id`). A hand-keyed negative
                # "红字" entry has no `reversed_entry_id` and is indistinguishable
                # from a genuine manual direction edit; and Odoo's non-negative
                # debit/credit store a 借方红字 as a 贷方蓝字, so that second common
                # red-ink form cannot be represented natively at all (framework-level).
                continue
            origin = line._origin
            prev_default = line._cn_default_for(origin.account_id, origin.balance)
            new_default = line._cn_default_for(line.account_id, line.balance)
            cur = line.cn_cash_flow_item_id
            if not cur or cur == prev_default:
                # empty, or previously auto-filled -> follow to the new default
                # (which may be empty, clearing a stale auto value); a manual
                # value (cur != prev_default) is left untouched.
                line.cn_cash_flow_item_id = new_default

    def write(self, vals):
        """ORM path for the follow-account-and-direction semantics (see compute).

        A persisted ORM write hides the old account/balance from the compute
        (`_origin` is the record itself), so before the write we remember the
        lines holding an *auto* value (equal to their present account+direction
        default). After the write we re-derive that value from the NEW
        account+direction — a new default, or clear if that side has none.
        Manual values are never in the set, so they survive, including a
        direction flip (edited debit/credit/balance) onto a side that has a
        default (R22-T1-V4/V6/V7)."""
        touches = bool({'account_id', 'balance', 'debit', 'credit'} & vals.keys())
        reassign = self.browse()
        if touches and 'cn_cash_flow_item_id' not in vals:
            reassign = self.filtered(
                lambda l: l.cn_cash_flow_item_id
                and not l.move_id.reversed_entry_id   # R23-T5-1: keep on reversal
                and l.cn_cash_flow_item_id
                == l._cn_default_for(l.account_id, l.balance))
        res = super().write(vals)
        for line in reassign:
            new_default = line._cn_default_for(line.account_id, line.balance)
            if line.cn_cash_flow_item_id != new_default:
                line.cn_cash_flow_item_id = new_default
        return res
