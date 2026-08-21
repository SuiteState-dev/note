# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..models.cn_group_builder import SUPPORTED_CHARTS


class GenerateCnGroups(models.TransientModel):
    _name = 'suite.cn.coa.generate'
    _description = '生成中国科目分级'

    company_ids = fields.Many2many(
        'res.company', string='公司', required=True,
        default=lambda self: self._default_companies(),
        help='要生成科目分级的公司。只列出使用受支持的中国科目表的公司。')
    mode = fields.Selection(
        [('create', '新建（跳过已存在）'),
         ('rebuild', '重建（先清后建）'),
         ('validate', '仅校验（只报告差异，不改动）')],
        string='模式', required=True, default='create')
    result = fields.Text(string='结果', readonly=True)

    @api.model
    def _default_companies(self):
        supported = self.env['suite.cn.coa.group.builder']._supported_companies()
        allowed = self.env.companies
        return (supported & allowed).ids

    def action_run(self):
        self.ensure_one()
        if not self.company_ids:
            raise UserError(_('请至少选择一个公司。'))
        builder = self.env['suite.cn.coa.group.builder']
        report = builder._build_groups(self.company_ids, mode=self.mode)
        lines = []
        for company in self.company_ids:
            rep = report.get(company.id, {})
            if not rep.get('supported', False):
                lines.append('%s：科目表 %r 不受支持，已跳过。'
                             % (company.name, rep.get('chart')))
                continue
            if self.mode == 'validate':
                lines.append(
                    '%s（%s）：应有 %s 组，现有 %s 组；待新建 %s、待移除 %s。'
                    % (company.name, rep['chart'], rep['desired'],
                       rep['existing'], rep['to_create'], rep['to_remove']))
            else:
                lines.append(
                    '%s（%s）：新建 %s、认领 %s、更名 %s、移除 %s，目标共 %s 组。'
                    % (company.name, rep['chart'], rep.get('created', 0),
                       rep.get('claimed', 0), rep.get('healed', 0),
                       rep.get('removed', 0), rep['desired']))
                # Spell out which manual groups were adopted, so the user knows
                # exactly what this run took over and renamed (T2-3). Their
                # original names are restored if the module is uninstalled.
                for prefix, orig_name in rep.get('claimed_group_list', []):
                    lines.append('    · 认领手工分组 %s（原名「%s」，卸载时还原）'
                                 % (prefix, orig_name))
        self.result = '\n'.join(lines)
        # keep the wizard open so the user can read `result`
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
