# -*- coding: utf-8 -*-
"""发行中国科目表 wizard (R33-A §4.8.2)。

post_init 已自动发【通用 88 条】;本 wizard 让人【选纳税人身份】补税费档,亦可重跑补齐。
🔴 身份【必须是人选】——业务事实,程序猜不出(一般 vs 小规模决定税费三级树 vs 二级增值税)。
认领优先:重跑不重复建通用 88 条,只补身份差异条。
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PublishCnCoa(models.TransientModel):
    _name = 'suite.cn.coa.publish'
    _description = '发行中国科目表（小企业会计准则）'

    company_ids = fields.Many2many(
        'res.company', string='公司', required=True,
        default=lambda self: self._default_companies(),
        help='只列出使用小企业会计准则(ASSBE / chart cn)的公司。')
    taxpayer = fields.Selection(
        [('small', '小规模纳税人'), ('general', '一般纳税人')],
        string='纳税人身份', required=True, default='small',
        help='小规模 → 发二级「增值税」(2221.01);一般 → 发三级增值税树'
             '(2221.01 应交增值税 + 10 个明细)。通用档两者都发。')
    result = fields.Text(string='结果', readonly=True)

    @api.model
    def _default_companies(self):
        publisher = self.env['suite.cn.coa.publisher']
        return (publisher._supported_companies() & self.env.companies).ids

    def action_run(self):
        self.ensure_one()
        if not self.company_ids:
            raise UserError(_('请至少选择一个公司。'))
        report = self.env['suite.cn.coa.publisher']._publish(
            self.company_ids, taxpayer=self.taxpayer)
        lines = []
        for company in self.company_ids:
            rep = report.get(company.id) or {}
            # R37-T4-a:非 cn 准则公司被 _publish 拒绝 —— 界面直接说清公司/准则/为什么,
            # 不写「见日志」(惯例5)。此前此分支是死代码(_publish 从不回 rejected)。
            if rep.get('rejected'):
                lines.append('%s：⛔ 已拒绝发行。%s' % (company.name, rep['reason']))
                continue
            msg = ('%s（%s档）：目标 %s 条，新建 %s、认领 %s。'
                   % (company.name,
                      dict(self._fields['taxpayer'].selection)[rep['taxpayer']],
                      rep['target'], rep['created'], rep['claimed']))
            # T2-a (R43,惯例5 + B-72):货币资金 type 告警。裁定=选 A(认领不改 type,仅告警;
            # 新建时才写 asset_cash)。文案须写明【后果 + 不确定性】,且显示 type 用【原始英文
            # 类型码】(B-72:Odoo 的中文类型标签不是中国会计要素术语,直接显示译名会被误解)。
            if rep.get('cash_warn'):
                parts = ['编码 %s 当前类型 %s（Odoo 原始类型码，应为 asset_cash）'
                         % (d['code'], d['current_type'])
                         for d in rep.get('cash_details', [])]
                msg += ('⚠ %s 个货币资金科目类型非 asset_cash：%s。现金流量表按 asset_cash '
                        '判定现金，该科目当前不计入现金流量。【若手工改为 asset_cash，已出报表的'
                        '现金流量数字会变化】。本模块不自动修改已存在科目，认领不改、请人工核对。'
                        % (rep['cash_warn'], '；'.join(parts)))
            # R43-T1c 撞号：我方号段目标码被他人占用 → 已跳过、留痕、不覆盖。
            if rep.get('collision'):
                msg += ('⚠ %s 个我方号段（2221.51+）编码已被既有科目占用，已跳过不覆盖，'
                        '详见发行台账（发行动作=撞号跳过）。' % rep['collision'])
            # R43-T4:默认归档科目必须在回执明列 + 给启用路径。归档科目界面默认不显示,
            # 回执不说=等于没发,客户照样自建(指标3零省、反增隐形科目)——T4 理由链靠这条闭合。
            archived = rep.get('archived') or []
            if archived:
                names = ' / '.join(a['name'] for a in archived)
                msg += ('ℹ 另发 %s 条地方税种科目（%s），默认已归档、界面不显示。如需使用：'
                        '会计 → 配置 → 科目表 → 过滤器「已归档」→ 选中 → 操作 / 取消归档。'
                        % (len(archived), names))
            # R43-T1d 旧版连号残留：只报不动（不删不改，「发行的科目留库」承诺）。
            legacy = rep.get('legacy_lianhao') or []
            if legacy:
                shown = '、'.join(legacy[:10]) + ('…' if len(legacy) > 10 else '')
                msg += ('⚠ 本库存在旧版【连号】科目 %s 条（编码：%s）。本版（3.0）已改用点分'
                        '编码；建议【重建库】或手工归档这些科目。本模块【不会自动删除或改动'
                        '它们】。' % (len(legacy), shown))
            lines.append(msg)
        self.result = '\n'.join(lines)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name, 'res_id': self.id,
            'view_mode': 'form', 'target': 'new',
        }
