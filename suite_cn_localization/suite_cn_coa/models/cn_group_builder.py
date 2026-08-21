# -*- coding: utf-8 -*-
"""Builds a Chinese account.group hierarchy on the official charts.

Design (verified R15-A1 / R16 probes):
  * account.group HAS company_id (required, stored) -> per-company trees coexist
    even when two charts reuse the same prefix with opposite meaning.
  * account.group.parent_id is store=True/readonly and auto-maintained by
    _adapt_parent_account_group from the prefix nesting -> we set ONLY
    code_prefix_start/end; the parent chain builds itself.
  * account.account.group_id is a NON-stored compute -> deleting groups leaves
    zero residue on accounts.
  * Static XML cannot carry these records (company_id must point at a concrete,
    user-owned company) -> we create them in Python but register an
    ir.model.data row per group so uninstall removes them and re-install does
    not duplicate.

Tree shape:
  L1 大类   - one group per top-level category, hand-named per chart (a digit has
             a different meaning across charts: '3' = 权益 in cn but 共同类 in
             cn_large_bis), single-char prefix.
  L2/L3...  - one group per dot-prefix that is the parent of >=1 account, named
             after that account's leaf name. Derived from the account codes, so
             it only ever materialises levels the chart actually has.
"""
from psycopg2.extras import Json

from odoo import api, models

# digit -> 大类 name, per chart_template. Order = display order.
DALEI = {
    'cn': [
        ('1', '资产类'), ('2', '负债类'), ('3', '所有者权益类'),
        ('4', '成本类'), ('5', '损益类'),
    ],
    'cn_common': [
        ('1', '资产类'), ('2', '负债类'),
    ],
    'cn_large_bis': [
        ('1', '资产类'), ('2', '负债类'), ('3', '共同类'),
        ('4', '所有者权益类'), ('5', '成本类'), ('6', '损益类'),
    ],
}

SUPPORTED_CHARTS = tuple(DALEI)


class CnGroupBuilder(models.AbstractModel):
    _name = 'suite.cn.coa.group.builder'
    _description = 'China Account Group Builder'

    # ------------------------------------------------------------------ helpers
    @api.model
    def _supported_companies(self):
        return self.env['res.company'].search(
            [('chart_template', 'in', SUPPORTED_CHARTS)])

    @api.model
    def _xmlid_name(self, company, prefix):
        # deterministic, dots are illegal in xmlids
        return 'group_%s_%s' % (company.id, prefix.replace('.', '_'))

    @api.model
    def _leaf(self, name):
        """Keep only the last ' - ' segment, so a nested group shows its own
        label (应交税费 - 应交增值税 -> 应交增值税)."""
        if name and ' - ' in name:
            return name.rsplit(' - ', 1)[-1]
        return name

    @api.model
    def _desired_groups(self, company):
        """Return {prefix: {lang: name}} of every group the chart should have.
        The name is a per-language dict so groups stay bilingual regardless of
        the language the build runs under. None if the chart is unsupported."""
        dalei = DALEI.get(company.chart_template)
        if dalei is None:
            return None
        langs = [code for code, _name in self.env['res.lang'].get_installed()]
        if not langs:
            langs = ['en_US']
        accounts = self.env['account.account'].with_company(company).search(
            [('company_ids', 'in', company.id)])
        acc_by_code = {}
        for acc in accounts:
            acc = acc.with_company(company)
            if acc.code:
                acc_by_code[acc.code] = acc

        desired = {}
        # L1 大类 — hand-named (Chinese) for every language slot
        for digit, name in dalei:
            desired[digit] = {lang: name for lang in langs}
        # L2/L3... every dot-prefix that parents >=1 account
        for code in acc_by_code:
            parts = code.split('.')
            for i in range(1, len(parts)):
                prefix = '.'.join(parts[:i])
                if prefix in desired:
                    continue
                acc = acc_by_code.get(prefix)
                if acc:
                    desired[prefix] = {
                        lang: self._leaf(acc.with_context(lang=lang).name)
                        for lang in langs}
                else:
                    desired[prefix] = {lang: prefix for lang in langs}
        return desired

    @api.model
    def _default_name(self, name_dict):
        """Pick the English (or any) value as the record's base name."""
        return name_dict.get('en_US') or next(iter(name_dict.values()))

    @api.model
    def _apply_name(self, group, name_dict):
        """Write every language slot of a translatable name."""
        for lang, val in name_dict.items():
            grp = group.with_context(lang=lang)
            if grp.name != val:
                grp.name = val

    @api.model
    def _owned_groups(self, company):
        """Groups of this company that belong to this module (via ir.model.data)."""
        imds = self.env['ir.model.data'].search([
            ('module', '=', 'suite_cn_coa'),
            ('model', '=', 'account.group')])
        groups = self.env['account.group'].browse(imds.mapped('res_id')).exists()
        return groups.filtered(lambda g: g.company_id == company)

    @api.model
    def _imd_for_group(self, group):
        """(my_imd, any_imd) for a group."""
        any_imd = self.env['ir.model.data'].search(
            [('model', '=', 'account.group'), ('res_id', '=', group.id)])
        mine = any_imd.filtered(lambda d: d.module == 'suite_cn_coa')
        return mine, any_imd

    @api.model
    def _claim_group(self, company, prefix, group):
        """Register ir.model.data ownership for a group we created OR adopted.
        Idempotent: if the xmlid already exists (half-built state, re-run),
        repoint it instead of tripping the (module, name) unique constraint."""
        IMD = self.env['ir.model.data']
        name = self._xmlid_name(company, prefix)
        existing = IMD.search(
            [('module', '=', 'suite_cn_coa'), ('name', '=', name)], limit=1)
        if existing:
            if existing.res_id != group.id:
                existing.res_id = group.id
            return
        IMD.create({
            'name': name,
            'module': 'suite_cn_coa',
            'model': 'account.group',
            'res_id': group.id,
            'noupdate': True,
        })

    # ------------------------------------------------------------------- public
    @api.model
    def _build_all_companies(self, mode='create'):
        return self._build_groups(self._supported_companies(), mode=mode)

    @api.model
    def _build_groups(self, companies, mode='create'):
        """mode: 'create' (create/claim missing, refresh labels)
                 | 'rebuild' (wipe owned, then create/claim)
                 | 'validate' (report only, zero writes).
        Never raises on a prefix that already exists (created by us, a manual
        group, or dev residue): it is claimed or left alone, never duplicated
        (duplicating would trip account.group's no-overlap constraint).
        Returns a per-company report dict."""
        report = {}
        Group = self.env['account.group']
        for company in companies:
            desired = self._desired_groups(company)
            if desired is None:
                report[company.id] = {'chart': company.chart_template,
                                      'supported': False}
                continue

            desired_keys = {(p, p) for p in desired}
            owned = {(g.code_prefix_start, g.code_prefix_end): g
                     for g in self._owned_groups(company)}
            # every group of this company, regardless of owner, keyed by prefix
            all_by_key = {(g.code_prefix_start, g.code_prefix_end): g
                          for g in Group.search([('company_id', '=', company.id)])}
            to_create = desired_keys - set(all_by_key)   # no group there at all
            to_remove = set(owned) - desired_keys        # ours, no longer wanted

            rep = {'chart': company.chart_template, 'supported': True,
                   'desired': len(desired), 'existing': len(owned),
                   'to_create': len(to_create), 'to_remove': len(to_remove),
                   'mode': mode}

            if mode == 'validate':
                report[company.id] = rep
                continue

            if mode == 'rebuild' and owned:
                # Wipe only the groups we CREATED; keep adopted (manual) groups
                # owned and in place so the loop re-heals their name without
                # churning the adoption ledger (which would corrupt the captured
                # original name). Their original stays recorded for uninstall.
                owned_recs = self.env['account.group'].browse(
                    [g.id for g in owned.values()])
                adopted_ids = set(self.env['suite.cn.coa.adopted.group'].search(
                    [('group_id', 'in', owned_recs.ids)]).mapped('group_id').ids)
                created_owned = owned_recs.filtered(
                    lambda g: g.id not in adopted_ids)
                self._unlink_groups(created_owned)
                owned = {k: g for k, g in owned.items() if g.id in adopted_ids}
                all_by_key = {(g.code_prefix_start, g.code_prefix_end): g
                              for g in Group.search([('company_id', '=', company.id)])}
                to_create = desired_keys - set(all_by_key)

            created = claimed = healed = 0
            claimed_groups = []  # (prefix, original_name) of groups adopted now
            ctx_group = Group.with_context(delay_account_group_sync=True)
            for prefix, name_dict in desired.items():
                key = (prefix, prefix)
                grp = all_by_key.get(key)
                if grp is None:
                    grp = ctx_group.with_company(company).create({
                        'name': self._default_name(name_dict),
                        'code_prefix_start': prefix,
                        'code_prefix_end': prefix,
                        'company_id': company.id,
                    })
                    self._apply_name(grp, name_dict)
                    self._claim_group(company, prefix, grp)
                    created += 1
                    continue
                # a group already sits on this prefix
                mine, any_imd = self._imd_for_group(grp)
                if mine:
                    if grp.name != name_dict.get(self.env.lang or 'en_US',
                                                 self._default_name(name_dict)):
                        self._apply_name(grp, name_dict)
                        healed += 1
                elif not any_imd:
                    # orphan (manual / dev residue): adopt it. Record its
                    # pre-rename name and parent FIRST, so uninstall can restore
                    # the user's group instead of deleting it (T2).
                    claimed_groups.append((prefix, grp.display_name))
                    self._record_adoption(company, grp)
                    self._claim_group(company, prefix, grp)
                    self._apply_name(grp, name_dict)
                    claimed += 1
                # else: owned by another module -> leave it untouched

            if to_remove:
                self._unlink_groups([owned[k] for k in to_remove])

            # one authoritative parent-chain rebuild for this company
            Group._adapt_parent_account_group(company=company)

            rep.update(created=created, claimed=claimed, healed=healed,
                       removed=len(to_remove), claimed_group_list=claimed_groups)
            report[company.id] = rep
        return report

    # -------------------------------------------------------- adoption ledger
    @api.model
    def _record_adoption(self, company, group):
        """Remember a manual group's pre-rename name (all languages) and parent,
        once, so uninstall can restore instead of delete it (T2). Idempotent:
        never overwrites an existing record, so a later rebuild that re-adopts
        the same group cannot capture the already-renamed name."""
        Adopted = self.env['suite.cn.coa.adopted.group']
        if Adopted.search_count([('group_id', '=', group.id)]):
            return
        # Read the raw translatable jsonb straight from the column, so every
        # language slot is captured exactly (not just the active language).
        self.env.cr.execute(
            "SELECT name FROM account_group WHERE id = %s", (group.id,))
        row = self.env.cr.fetchone()
        Adopted.create({
            'group_id': group.id,
            'company_id': company.id,
            'original_name': row[0] if row else False,
            'original_parent_id': group.parent_id.id or False,
        })

    @api.model
    def _release_adopted(self, groups):
        """Restore adopted (manual) groups to their pre-adoption name and drop
        this module's ownership WITHOUT deleting them; delete the adoption
        records. Returns the account.group records actually released."""
        if not groups:
            return self.env['account.group']
        Adopted = self.env['suite.cn.coa.adopted.group']
        recs = Adopted.search([('group_id', 'in', groups.ids)])
        released = self.env['account.group']
        for rec in recs:
            grp = rec.group_id
            if not grp.exists():
                continue
            if rec.original_name:
                # Reset the WHOLE name jsonb to the captured original, so any
                # language slot our rename added (e.g. a zh_CN it never had) is
                # removed too — a per-language overwrite would leave that
                # pollution behind and break byte-for-byte restore.
                self.env.cr.execute(
                    "UPDATE account_group SET name = %s WHERE id = %s",
                    (Json(rec.original_name), grp.id))
                grp.invalidate_recordset(['name', 'display_name'])
            # drop our imd so the group is no longer owned by this module
            self.env['ir.model.data'].search([
                ('module', '=', 'suite_cn_coa'),
                ('model', '=', 'account.group'),
                ('res_id', '=', grp.id)]).unlink()
            released |= grp
        recs.unlink()
        return released

    # ------------------------------------------------------------- teardown
    @api.model
    def _unlink_groups(self, groups):
        """Remove a set of groups safely (rebuild / no-longer-desired path).

        Adopted (manual) groups in the set are RESTORED and released, never
        deleted. Module-created groups are deleted with their ir.model.data.
        Before deleting, any SURVIVING group whose parent is in the delete set
        is detached — account.group.parent_id is ``ondelete='cascade'`` (verified
        in source), so without this a user's adopted group parented under one of
        our created groups would be silently cascade-deleted (T2)."""
        if not groups:
            return
        groups = self.env['account.group'].browse(
            [g.id for g in groups]).exists()
        released = self._release_adopted(groups)
        to_delete = groups - released
        if not to_delete:
            return
        survivors = self.env['account.group'].search([
            ('parent_id', 'in', to_delete.ids),
            ('id', 'not in', to_delete.ids)])
        if survivors:
            self.env.cr.execute(
                "UPDATE account_group SET parent_id = NULL WHERE id IN %s",
                (tuple(survivors.ids),))
            survivors.invalidate_recordset(['parent_id'])
        self.env['ir.model.data'].search([
            ('module', '=', 'suite_cn_coa'),
            ('model', '=', 'account.group'),
            ('res_id', 'in', to_delete.ids)]).unlink()
        to_delete.unlink()

    @api.model
    def _delete_created(self, groups):
        """Delete module-created groups + their ir.model.data (uninstall path).
        Caller has already released adopted groups and detached survivors."""
        if not groups:
            return
        self.env['ir.model.data'].search([
            ('module', '=', 'suite_cn_coa'),
            ('model', '=', 'account.group'),
            ('res_id', 'in', groups.ids)]).unlink()
        groups.exists().unlink()
