# -*- coding: utf-8 -*-
from odoo import models, fields


class CnCoaAdoptedGroup(models.Model):
    """Uninstall-restore ledger for account.group records this module ADOPTED
    (R22-T2).

    The builder claims an existing manual / dev-residue ``account.group`` whose
    prefix matches a target prefix — it registers an ``ir.model.data`` on it and
    renames it. Without a record of the pre-adoption state, uninstall would
    delete the user's own group (it now carries our imd) and its rename would be
    lost. This model captures the original name (all languages) and parent so the
    ``uninstall_hook`` can restore the group and release it instead of deleting
    it. Module-*created* groups have no such record and are deleted normally.
    """
    _name = 'suite.cn.coa.adopted.group'
    _description = 'China COA — Adopted account.group (uninstall-restore ledger)'

    group_id = fields.Many2one(
        'account.group', string='Adopted Group',
        required=True, index=True, ondelete='cascade')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='cascade')
    original_name = fields.Json(
        string='Original Name (all languages)',
        help="The account.group.name jsonb exactly as it was BEFORE this module "
             "renamed the group. Restored verbatim on uninstall.")
    original_parent_id = fields.Many2one(
        'account.group', string='Original Parent', ondelete='set null',
        help="The parent at adoption time. Parent chains are prefix-derived and "
             "rebuilt by _adapt_parent_account_group once our created groups are "
             "gone, so this is a safety-net / verification record, not the "
             "primary restore path.")

    _group_uniq = models.Constraint(
        'unique(group_id)',
        'An account group can be adopted only once.')
