# -*- coding: utf-8 -*-
from . import models
from . import wizard


def post_init_hook(env):
    """R33-A: `suite_cn_coa` 由「分级树生成器」升级为「科目表发行方」。装机时:

      1. 发行 ASSBE 通用科目(88 条)到每个装 cn chart 的公司(§4.8.2 post_init 自动;
         身份档由 wizard 补,§4.8.3 认领优先、幂等);
      2. 套上官方 ASSBE 报表的国标口径覆盖(§4.10 二选一,先存原值以便卸载还原);
      3. (原有,§3 不动)构建 account.group 分级树。

    全部幂等,安全 re-run on -u。"""
    env['suite.cn.coa.publisher']._publish_all_companies(taxpayer='common')
    env['suite.cn.coa.report.override']._apply_all()
    env['suite.cn.coa.group.builder']._build_all_companies(mode='create')


def uninstall_hook(env):
    """Leave the database as install found it (R22-T2).

    Two kinds of groups carry this module's ir.model.data: the ones we CREATED
    and the manual/dev-residue ones we ADOPTED (claimed + renamed). Letting the
    standard uninstall delete both would erase the user's own adopted groups.
    So we do the teardown here, in order:

      1. release each adopted group — restore its original name (all languages)
         and drop our ownership, keep the group;
      2. delete the module-created groups, but first detach any surviving group
         parented under one of them, because ``account.group.parent_id`` is
         ``ondelete='cascade'`` and would otherwise take the user's groups down
         with ours;
      3. rebuild the prefix-derived parent chain, which reproduces the original
         nesting among the surviving groups.

    After this the module's remaining data (the adoption ledger rows were unlinked
    in step 1) is gone and standard uninstall finds nothing left to remove.

    R33-A additions (order matters — do BEFORE the group teardown):
      0a. 恢复官方 ASSBE 报表 formula 原值(§4.9.2 🔴 卸载不回滚字段值,残留会让客户卸载后
          官方报表仍读我方口径且看起来正常,比科目被删更隐蔽 → 必须主动写回);
      0b. 发行的【科目本身不动】(§4.9.1 无 xmlid,卸载器看不见,等同客户手工建的科目)——
          发行台账行随标准 uninstall 删除,科目留库。
    """
    env['suite.cn.coa.report.override']._restore_all()   # 0a
    builder = env['suite.cn.coa.group.builder']
    Group = env['account.group']
    for company in env['res.company'].search([]):
        adopted = env['suite.cn.coa.adopted.group'].search(
            [('company_id', '=', company.id)])
        # 1. restore + release the user's adopted groups (also unlinks the ledger)
        builder._release_adopted(adopted.mapped('group_id'))
        # 2. delete our created groups (adopted ones are no longer owned)
        created = builder._owned_groups(company)
        if created:
            survivors = Group.search([
                ('parent_id', 'in', created.ids),
                ('id', 'not in', created.ids)])
            if survivors:
                env.cr.execute(
                    "UPDATE account_group SET parent_id = NULL WHERE id IN %s",
                    (tuple(survivors.ids),))
                survivors.invalidate_recordset(['parent_id'])
            builder._delete_created(created)
        # 3. reproduce the original prefix-derived parent chain
        Group._adapt_parent_account_group(company=company)
