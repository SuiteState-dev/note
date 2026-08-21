# -*- coding: utf-8 -*-
{
    'name': 'China - Accounting Voucher (记账凭证)',
    'version': '19.0.1.3.1',
    'category': 'Accounting/Localizations',
    'summary': '中式记账凭证呈现层：凭证字 + 凭证号 + 中文版式（M3a）',
    'description': """
中式记账凭证（M3a 呈现层）
==========================

在上游 l10n_cn 记账凭证打印报表基础上补齐中式法定要素，**纯呈现层**：

- **凭证字**（收款/付款/转账/记，首版 Selection，扩展走 selection_add）
- **凭证号**（按 公司 × 凭证字 × 会计期间 连续编号，过账时分配，月度归零）
- 版式中文化 + 一级—明细科目串 + 签章栏位（工作流属 M3b，本模块不做）

设计边界
--------
- **完全不碰 account.move.name**（B-52：account.move 走 sequence.mixin、不走 ir.sequence，
  两套机制独立；卸载删两列，原生编号不受影响）。
- 凭证号删除释放号=接受断号（运营走红冲不删已过账凭证）；断号检查另行提供。
- 借方红字属框架层限制（debit/credit 非负），呈现层无法凭空还原 → 仅显示注意项。
- 不做：签章工作流、凭证规则引擎、分数编号（首版）、跨 journal 号重排。
""",
    'author': 'SuiteState (ElectroState FZCO)',
    'website': 'https://suitestate.com',
    'license': 'LGPL-3',
    'depends': [
        'l10n_cn',
    ],
    'data': [
        'views/account_move_view.xml',
        'views/report_voucher.xml',
    ],
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'auto_install': False,
}
