# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import ValidationError

# Cash aperture = single source of truth `asset_cash`, identical on both the
# Python (constraint) side and the report (domain) side. `liability_credit_card`
# was dropped here in R11-T1 to match the report, which only ever summed
# `asset_cash` (design.md §6.3): a mismatch made the constraint demand items on
# entries the statement never counted.
CASH_TYPES = ('asset_cash',)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('line_ids', 'state')
    def _check_cn_cash_flow_item(self):
        """When a posted entry touches a cash/bank account, every non-cash
        counterpart line must carry a cash flow item. Gated per company by
        res.company.cn_cashflow_item_required (default off) so historical data
        and companies that don't need it are never blocked."""
        for move in self:
            if move.state != 'posted':
                continue
            if not move.company_id.cn_cashflow_item_required:
                continue
            if not any(l.account_id.account_type in CASH_TYPES for l in move.line_ids):
                continue
            # A "counterpart" = any line that carries an account, is not itself a
            # cash line, and has no item yet. `l.account_id` already excludes the
            # pure display rows (line_section / line_note carry no account), so we
            # must NOT filter on `display_type`: in v19 real posting lines have
            # display_type='product' (not False), and the old `not l.display_type`
            # test silently excluded every real line, so the gate never fired
            # (found in R11-T1 testing). This now matches the report's
            # "unclassified" domain, which counts exactly these lines.
            missing = move.line_ids.filtered(
                lambda l: l.account_id
                and l.account_id.account_type not in CASH_TYPES
                and not l.cn_cash_flow_item_id
            )
            if missing:
                raise ValidationError(_(
                    "Entry %(name)s touches a cash/bank account, so each "
                    "counterpart line must have a Cash Flow Item. Missing on: "
                    "%(accounts)s",
                    name=move.display_name,
                    accounts=", ".join(missing.mapped('account_id.code')),
                ))
