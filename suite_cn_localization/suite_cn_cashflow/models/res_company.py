# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    cn_cashflow_item_required = fields.Boolean(
        string='Require Cash Flow Item on cash entries',
        default=False,
        help="When enabled, posting an entry that touches a cash/bank account "
             "requires a Cash Flow Item on every counterpart line. Off by "
             "default so historical entries are never blocked.")
