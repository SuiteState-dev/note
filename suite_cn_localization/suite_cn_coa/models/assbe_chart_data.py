# -*- coding: utf-8 -*-
"""ASSBE (小企业会计准则) 科目表发行数据 —— R33-A。

来源: 星辰 ASSBE 原件筛净 + 二姐实务修正 (l10n_cn_assbe_chart_R33A.csv, note 仓库)。
68 一级 + 23 二级 + 10 三级 = 101 条。编码=国标财会〔2011〕17号 号段。
由 CSV 确定性生成，勿手改；改数据改 CSV 再重生成。

字段: code/parent/name/account_type/cf_cash/reconcile/taxpayer(general|small|common)。
taxpayer=common 通用发行; general=仅一般纳税人; small=仅小规模。
"""

ASSBE_CHART = [
    {'code': '1001', 'parent': None, 'name': '库存现金', 'account_type': 'asset_cash', 'cf_cash': True, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1002', 'parent': None, 'name': '银行存款', 'account_type': 'asset_cash', 'cf_cash': True, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1012', 'parent': None, 'name': '其他货币资金', 'account_type': 'asset_cash', 'cf_cash': True, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1101', 'parent': None, 'name': '短期投资', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1121', 'parent': None, 'name': '应收票据', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '1122', 'parent': None, 'name': '应收账款', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '1123', 'parent': None, 'name': '预付账款', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '1131', 'parent': None, 'name': '应收股利', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '1132', 'parent': None, 'name': '应收利息', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '1221', 'parent': None, 'name': '其他应收款', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '1401', 'parent': None, 'name': '材料采购', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1402', 'parent': None, 'name': '在途物资', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1403', 'parent': None, 'name': '原材料', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1404', 'parent': None, 'name': '材料成本差异', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1405', 'parent': None, 'name': '库存商品', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1406', 'parent': None, 'name': '发出商品', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1407', 'parent': None, 'name': '商品进销差价', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1408', 'parent': None, 'name': '委托加工物资', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1411', 'parent': None, 'name': '周转材料', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1421', 'parent': None, 'name': '消耗性生物资产', 'account_type': 'asset_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1501', 'parent': None, 'name': '长期债券投资', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1511', 'parent': None, 'name': '长期股权投资', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1601', 'parent': None, 'name': '固定资产', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1602', 'parent': None, 'name': '累计折旧', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1604', 'parent': None, 'name': '在建工程', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1605', 'parent': None, 'name': '工程物资', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1606', 'parent': None, 'name': '固定资产清理', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1621', 'parent': None, 'name': '生产性生物资产', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1622', 'parent': None, 'name': '生产性生物资产累计折旧', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1701', 'parent': None, 'name': '无形资产', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1702', 'parent': None, 'name': '累计摊销', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1801', 'parent': None, 'name': '长期待摊费用', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '1901', 'parent': None, 'name': '待处理财产损溢', 'account_type': 'asset_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2001', 'parent': None, 'name': '短期借款', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2201', 'parent': None, 'name': '应付票据', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '2202', 'parent': None, 'name': '应付账款', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '2203', 'parent': None, 'name': '预收账款', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '2211', 'parent': None, 'name': '应付职工薪酬', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221', 'parent': None, 'name': '应交税费', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2231', 'parent': None, 'name': '应付利息', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '2232', 'parent': None, 'name': '应付利润', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '2241', 'parent': None, 'name': '其他应付款', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': True, 'taxpayer': 'common'},
    {'code': '2401', 'parent': None, 'name': '递延收益', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2501', 'parent': None, 'name': '长期借款', 'account_type': 'liability_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2701', 'parent': None, 'name': '长期应付款', 'account_type': 'liability_non_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '3001', 'parent': None, 'name': '实收资本', 'account_type': 'equity', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '3002', 'parent': None, 'name': '资本公积', 'account_type': 'equity', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '3101', 'parent': None, 'name': '盈余公积', 'account_type': 'equity', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '3103', 'parent': None, 'name': '本年利润', 'account_type': 'equity', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '3104', 'parent': None, 'name': '利润分配', 'account_type': 'equity', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '4001', 'parent': None, 'name': '生产成本', 'account_type': 'expense_direct_cost', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '4101', 'parent': None, 'name': '制造费用', 'account_type': 'expense_direct_cost', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '4301', 'parent': None, 'name': '研发支出', 'account_type': 'expense_direct_cost', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '4401', 'parent': None, 'name': '工程施工', 'account_type': 'expense_direct_cost', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '4403', 'parent': None, 'name': '机械作业', 'account_type': 'expense_direct_cost', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5001', 'parent': None, 'name': '主营业务收入', 'account_type': 'income', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5051', 'parent': None, 'name': '其他业务收入', 'account_type': 'income_other', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5111', 'parent': None, 'name': '投资收益', 'account_type': 'income_other', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5301', 'parent': None, 'name': '营业外收入', 'account_type': 'income_other', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5401', 'parent': None, 'name': '主营业务成本', 'account_type': 'expense_direct_cost', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5402', 'parent': None, 'name': '其他业务成本', 'account_type': 'expense', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5403', 'parent': None, 'name': '税金及附加', 'account_type': 'expense_direct_cost', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5601', 'parent': None, 'name': '销售费用', 'account_type': 'expense', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5602', 'parent': None, 'name': '管理费用', 'account_type': 'expense', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5603', 'parent': None, 'name': '财务费用', 'account_type': 'expense', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5711', 'parent': None, 'name': '营业外支出', 'account_type': 'expense', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '5801', 'parent': None, 'name': '所得税费用', 'account_type': 'expense', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '6000', 'parent': None, 'name': '以前年度损益调整', 'account_type': 'equity', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    # —— 2221 应交税费 明细 —— R43-T1:连号 → 点分,与官方 l10n_cn 对齐 ——————————————
    # 🔴 措辞边界(status s-13 §8 / background v17):点分 = 统一到【Odoo 的形态】,不是统一
    #   到中国标准。中国实务编码传统是连号(金蝶/用友),不得对客户写「我们按国标编码」。
    # 判据只用 code + 官方权威码(硬编码逐条对照,非名称匹配算法):官方数据带毛刺
    #   (2221.02 名尾有空格;「应交所得税」vs「应交企业所得税」名不等义同)。
    # CLAIM(官方已有,改点分即命中认领,不再新建)= 25 条(一般档)/ 15 条(小规模档);
    # NEW(官方 2221 下无地方税负债侧明细,我方真实补缺)= 6 条,走我方号段 2221.51–.56。
    #
    # 增值税 二级 + 三级(仅一般纳税人档)—— 全部 CLAIM 官方 2221.01 / 2221.01.0x:
    {'code': '2221.01', 'parent': '2221', 'name': '应交增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.02', 'parent': '2221.01', 'name': '进项税额', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.03', 'parent': '2221.01', 'name': '销项税额的抵减', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.10', 'parent': '2221.01', 'name': '已交税金', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.07', 'parent': '2221.01', 'name': '转出未交增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.11', 'parent': '2221.01', 'name': '减免税款', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.06', 'parent': '2221.01', 'name': '出口抵减内销产品应纳税额', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.01', 'parent': '2221.01', 'name': '销项税额', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.05', 'parent': '2221.01', 'name': '出口退税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.04', 'parent': '2221.01', 'name': '进项税额转出', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    {'code': '2221.01.08', 'parent': '2221.01', 'name': '转出多交增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'general'},
    # 增值税 二级(小规模档,flat)—— CLAIM 官方 2221.01(与一般档 2221.01 同码、按 taxpayer 互斥):
    {'code': '2221.01', 'parent': '2221', 'name': '增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'small'},
    # 通用二级(common)—— CLAIM 官方 14 条:
    {'code': '2221.02', 'parent': '2221', 'name': '未交增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.03', 'parent': '2221', 'name': '预交增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.05', 'parent': '2221', 'name': '待抵扣进项税额', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.04', 'parent': '2221', 'name': '待认证进项税额', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.06', 'parent': '2221', 'name': '待转销项税额', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.07', 'parent': '2221', 'name': '增值税留抵税额', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.09', 'parent': '2221', 'name': '简易计税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.10', 'parent': '2221', 'name': '转让金融商品应交增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.11', 'parent': '2221', 'name': '应交所得税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.13', 'parent': '2221', 'name': '教育费附加', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.14', 'parent': '2221', 'name': '地方教育费附加', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.12', 'parent': '2221', 'name': '应交城市维护建设税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.15', 'parent': '2221', 'name': '应交消费税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    {'code': '2221.16', 'parent': '2221', 'name': '应交印花税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common'},
    # NEW 6 条 —— 我方号段 2221.51–.56(官方 2221 无地方税负债侧明细,只在 5403.xx 建费用侧)。
    #   R43-T4:默认 active=False(从业者小企业库归档 27%,含这批;发出来是「装完先关一堆」,
    #   完全不发是「工业客户自己建」;归档态同时优化「不用建」与「不用每客户建一遍」)。
    {'code': '2221.51', 'parent': '2221', 'name': '应交个人所得税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common', 'active': False},
    {'code': '2221.52', 'parent': '2221', 'name': '应交资源税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common', 'active': False},
    {'code': '2221.53', 'parent': '2221', 'name': '应交土地增值税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common', 'active': False},
    {'code': '2221.54', 'parent': '2221', 'name': '应交房产税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common', 'active': False},
    {'code': '2221.55', 'parent': '2221', 'name': '应交土地使用税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common', 'active': False},
    {'code': '2221.56', 'parent': '2221', 'name': '应交车船使用税', 'account_type': 'liability_current', 'cf_cash': False, 'reconcile': False, 'taxpayer': 'common', 'active': False},
]

# —— R48-T1 余额方向 (借/贷) —————————————————————————————————————————————
# 科目余额表落栏由【科目自身余额方向属性】决定,不随数值符号迁移;实际方向与属性相反时
# 在原栏写负数(二姐实务口径,金蝶实现,observed)。方向值【唯一 home 在此】——发行件带列,
# 值须能自证依据:基值=准则科目类别映射(资产/成本→借,负债/权益/收入→贷),逐条例外见下。
# 星辰 CSV 仅制备期工作底稿/交叉核对,【不上运行时路径】(§9.8 材料分层,R48 裁决)。
#
# 例外表(方向与 account_type 大类相反的科目)——每条自带因由:
#   备抵资产(资产类,余额却在贷方,冲减对应资产原值):
#     1602 累计折旧 / 1622 生产性生物资产累计折旧 / 1702 累计摊销
#   增值税借方专栏/预交类(负债类"应交税费"下,余额却在借方,代表已付/可抵/留抵):
#     2221.01.02 进项税额 / 2221.01.03 销项税额的抵减 / 2221.01.06 出口抵减内销产品应纳税额
#     2221.01.07 转出未交增值税 / 2221.01.10 已交税金 / 2221.01.11 减免税款
#     2221.03 预交增值税 / 2221.04 待认证进项税额 / 2221.05 待抵扣进项税额 / 2221.07 增值税留抵税额
# 交叉核对(制备期,R48):我方例外集 vs 星辰同名方向——星辰另有 教育费附加/地方教育费附加/
# 应付利润/以前年度损益调整 记借方,系【该客户账套用法】(准则均为贷方:附加税费与应付利润是
# 应付项、以前年度损益调整期末结平),我方发行件从准则、不随单一账套,故不纳入例外。
_CN_DIR_EXCEPTIONS = {
    '1602': 'credit', '1622': 'credit', '1702': 'credit',
    '2221.01.02': 'debit', '2221.01.03': 'debit', '2221.01.06': 'debit',
    '2221.01.07': 'debit', '2221.01.10': 'debit', '2221.01.11': 'debit',
    '2221.03': 'debit', '2221.04': 'debit', '2221.05': 'debit', '2221.07': 'debit',
}


def cn_base_direction(account_type):
    """准则科目类别 → 余额方向基值。资产/成本→借;负债/权益/收入→贷。
    🔴 备抵/借方专栏子目由 _CN_DIR_EXCEPTIONS 覆盖(大类判不出:它们 account_type
    仍是资产/负债,方向却相反,正是 account_type 推导会翻车之处 R48-Q4)。"""
    at = account_type or ''
    if at.startswith('asset') or at.startswith('expense'):
        return 'debit'
    return 'credit'   # liability* / equity / income*


def cn_direction_for(code, account_type):
    """发行件某科目的余额方向(唯一权威口径)。例外优先,否则准则大类基值。"""
    return _CN_DIR_EXCEPTIONS.get(code) or cn_base_direction(account_type)


# 把 direction 落成 ASSBE_CHART 每条的真实键(发行件带方向列)。
for _entry in ASSBE_CHART:
    _entry['direction'] = cn_direction_for(_entry['code'], _entry['account_type'])

# code → direction 快查(运行时 handler 取我方发行方向用;星辰不入此路径)。
ASSBE_DIRECTION_BY_CODE = {r['code']: r['direction'] for r in ASSBE_CHART}

# 现金判据硬约束 (CF 靠 asset_cash 判现金, §4.2)
CASH_CODES = ('1001', '1002', '1012')

# 往来成对守卫 (§4.5): 缺一则方向分流失效
TRADE_PAIRS = (('1122', '2203'), ('1123', '2202'))

# —— R43-T1c 我方自建明细号段 + 撞号哨兵判据 —————————————————————————————————
# 官方 2221 二级已用到 .16;我方补缺的 6 条一律走 .51–.99,给官方留 .17–.50 缓冲带,
# 避免官方下版新增即撞(B-59 撞号同族)。写死为常量,不散落进发行代码。
OUR_DETAIL_SEGMENT = '2221'
OUR_DETAIL_SEGMENT_MIN = 51
OUR_DETAIL_SEGMENT_MAX = 99


def is_our_detail_segment(code):
    """True ⇔ code 属我方自建二级号段 2221.51–2221.99(点分二级)。

    撞号哨兵据此判「本该我方新建的码,却已被他人(官方/客户)占用」:该码存在、且无我方
    发行台账 created 痕迹 ⇒ 报出不覆盖(形状同 E-7 原值哨兵:current 既非 expected 亦非
    new-by-us ⇒ 不硬改)。"""
    parts = (code or '').split('.')
    return (len(parts) == 2 and parts[0] == OUR_DETAIL_SEGMENT
            and parts[1].isdigit()
            and OUR_DETAIL_SEGMENT_MIN <= int(parts[1]) <= OUR_DETAIL_SEGMENT_MAX)

