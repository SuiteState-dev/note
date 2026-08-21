# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cn_cashflow_item_required = fields.Boolean(
        related='company_id.cn_cashflow_item_required',
        readonly=False,
        string='Require Cash Flow Item on cash entries')
