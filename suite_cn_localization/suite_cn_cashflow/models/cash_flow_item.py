# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CashFlowItem(models.Model):
    _name = 'cash.flow.item'
    _description = 'Cash Flow Statement Item'
    _order = 'sequence, code'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Referenced by the report line domains (cn_cash_flow_item_id.code).")
    sequence = fields.Integer(default=10)
    category = fields.Selection([
        ('operating', 'Operating'),
        ('investing', 'Investing'),
        ('financing', 'Financing'),
    ], required=True, default='operating')
    # Which accounting standard this item belongs to. Informational only:
    # the reports match items by `code` (disjoint A*/S* prefixes), not by this
    # field, so domains stay single-term. Used for list grouping/filtering.
    standard = fields.Selection([
        ('asbe', 'ASBE (企业会计准则)'),
        ('assbe', 'ASSBE (小企业会计准则)'),
    ], string='Accounting Standard')
    # Statutory items are identical for every company, so they ship as global
    # records (company_id empty). The field is kept to allow company-specific
    # additions without touching the shared set.
    company_id = fields.Many2one(
        'res.company', string='Company',
        help="Leave empty for a statutory item shared by all companies.")
    active = fields.Boolean(default=True)

    _code_company_uniq = models.Constraint(
        'unique(code, company_id)',
        'Cash flow item code must be unique per company.',
    )

    @api.constrains('code', 'company_id')
    def _check_code_unique_global(self):
        """Python guard on top of the SQL unique(code, company_id): Postgres
        treats every NULL company_id as distinct, so the SQL constraint does NOT
        catch two *global* items (company_id empty) sharing a code (R11-T2/P3).
        `active_test=False` so an archived duplicate can't slip through."""
        for item in self:
            domain = [('code', '=', item.code), ('id', '!=', item.id)]
            if not item.company_id:
                domain += [('company_id', '=', False)]
            else:
                domain += ['|', ('company_id', '=', item.company_id.id),
                           ('company_id', '=', False)]
            if self.sudo().with_context(active_test=False).search_count(domain):
                raise ValidationError(_(
                    "Cash flow item code %s already exists.", item.code))

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for item in self:
            item.display_name = f"[{item.code}] {item.name}" if item.code else item.name
