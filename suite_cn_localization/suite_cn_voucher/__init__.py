# -*- coding: utf-8 -*-
from . import models


def uninstall_hook(env):
    """P-01 清洁卸载：懒创建的凭证号 ir.sequence（及其 date_range 子序列，cascade）
    不属本模块 ir.model.data，须显式清掉，避免留下孤儿序列。两个字段列由 ORM 随模块
    卸载自动删除；原生 account.move.name 不受影响（B-52 两套机制独立）。"""
    seqs = env['ir.sequence'].sudo().search([('code', '=like', 'l10n_cn.voucher.%')])
    seqs.unlink()
