# -*- coding: utf-8 -*-
"""ASSBE 科目表发行方 —— R33-A §4.8.

由「科目分级树生成器」升级为「科目表发行方」的新职责(分级树 builder 保持不动,§3)。

发行语义(§4.8.3 认领优先,不是重建):
  * 按 (company, code) 查:编码已存在 → 【认领,不改名/type/reconcile】;不存在 → 建。
  * 唯一例外:1001/1002/1012 已存在且非 asset_cash → 【告警不改】(CF 靠它判现金)。
  * 幂等:重跑不重复建、不覆盖客户改动。
  * 🔴 纯 ORM create,【不写 ir.model.data】(§4.8.3);另记发行台账。

两件套(§4.8.2):
  * post_init_hook → _publish_all_companies(): 装模块时自动发【通用档 88 条】。
  * wizard → _publish(companies, taxpayer): 选纳税人身份补税费档(一般 +11 / 小规模 +1)。

§4.7 建表校验: 发行后核每公司每科目必有 code(编码是取数键;F3/B-63 静默错报形态防线)。
"""
import logging

from odoo import _, api, models

from .assbe_chart_data import ASSBE_CHART, CASH_CODES, is_our_detail_segment

_logger = logging.getLogger(__name__)

# ASSBE = 小企业会计准则 = 官方 chart_template 'cn'。R33-A 只做 ASSBE(§9:不做 ASBE)。
ASSBE_CHART_TEMPLATE = 'cn'

# R38-T3 (#4/#7 前置校验, status s-11 §8-14):发行前必须 zh_CN 已激活。
# 🔴 为什么是【前置拒绝】而非【写双键】:R37-T5 verified —— 未激活语言的 context 直接
# UserError「Invalid language code」,想写 zh_CN 键也得先激活。且我方发行是【运行时 create 的
# 用户数据】,与官方 chart 不同 —— 官方走模块翻译(name@zh_CN CSV + _load_module_terms →
# _load_translations),激活语言时会【回填】;我方账户激活语言【不回填】(R37-T5 场景4 verified)
# ⇒ 若在 zh_CN 未激活时发行, 科目名只落 en_US 单键、中文环境靠回落显示、且事后永久缺 zh_CN 键。
# 故:发行前 zh_CN 未激活 → 拒绝 + 可读原因(不静默继续);激活后以显式 lang='zh_CN' 建, 双键齐全。
PUBLISH_LANG = 'zh_CN'


class CoaPublisher(models.AbstractModel):
    _name = 'suite.cn.coa.publisher'
    _description = 'China COA — ASSBE 科目表发行方'

    # ------------------------------------------------------------------ scope
    @api.model
    def _supported_companies(self):
        return self.env['res.company'].search(
            [('chart_template', '=', ASSBE_CHART_TEMPLATE)])

    @api.model
    def _accounts_for(self, taxpayer):
        """taxpayer ∈ {'common','general','small'}。common 恒发;身份档叠加对应条。"""
        wanted = {'common'}
        if taxpayer in ('general', 'small'):
            wanted.add(taxpayer)
        return [a for a in ASSBE_CHART if a['taxpayer'] in wanted]

    # ---------------------------------------------------------------- publish
    @api.model
    def _publish_all_companies(self, taxpayer='common'):
        """post_init 入口:给每个装 ASSBE chart 的公司发通用档。"""
        companies = self._supported_companies()
        if companies:
            self._publish(companies, taxpayer=taxpayer)
        return companies

    @api.model
    def _publish(self, companies, taxpayer='common', dry_run=False):
        """认领优先、幂等发行。返回 {company_id: report_dict}。

        R37-T4-a (缺陷#1) 门控:逐公司以 chart_template 为判据,仅 ASSBE(cn) 可发行;
        ASBE(cn_large_bis)/非CN chart 一律【拒绝】(不发一条科目)并回可读原因。"""
        Account = self.env['account.account']
        Ledger = self.env['suite.cn.coa.published.account']
        rows = self._accounts_for(taxpayer)
        report = {}
        # R38-T3 前置校验:zh_CN 未激活 → 全部公司拒绝(语言是系统级,不分公司),不发一条。
        if not dry_run and not self._publish_lang_active():
            for company in companies:
                report[company.id] = self._lang_rejected(company)
            _logger.warning(
                'suite_cn_coa: 拒绝发行 —— 语言 %s 未激活。发行的科目名会只落 en_US 单键、'
                '事后无法回填(与官方 chart 走模块翻译不同)。请先激活中文再发行。', PUBLISH_LANG)
            return report
        # 激活态下以显式 zh_CN context 建科目 → jsonb 双键齐全(en_US + zh_CN,均为我方中文名)。
        AccPub = Account.with_context(lang=PUBLISH_LANG)
        for company in companies:
            # 🔴 唯一强制点:此前 wizard 默认只滤 supported、_publish 从不复核 → 用户手动往
            # m2m 加 cn_large_bis 公司即绕过(R35 实污染:大企业库新建43+认领14)。判据必须是
            # 目标公司自己的 chart_template,不是环境公司。
            if company.chart_template != ASSBE_CHART_TEMPLATE:
                report[company.id] = self._rejected(company)
                _logger.warning(
                    'suite_cn_coa: 拒绝向公司 %s 发行 —— chart_template=%s 非 %s。',
                    company.id, company.chart_template or '(无)', ASSBE_CHART_TEMPLATE)
                continue
            created = claimed = cash_warn = collision = 0
            cash_details = []  # T2-b:回执界面直说明细(编码/当前type),不写「见日志」(惯例5)
            collided_codes = []  # R43-T1c:撞号跳过的码(不计入「已发行归档」清单)
            AccC = Account.with_company(company).with_context(active_test=False)
            for a in rows:
                acc = AccC.search(
                    [('code', '=', a['code']),
                     ('company_ids', 'in', company.id)], limit=1)
                if acc:
                    # R43-T1c 撞号哨兵:我方号段(2221.51+)的目标码已被【非我方】科目占用
                    # (无我方 created 台账痕迹)⇒ 不覆盖、不认领、跳过、留痕。形状同 E-7 原值
                    # 哨兵(current 既非 expected 亦非 new-by-us ⇒ 报出不硬改)。
                    if (is_our_detail_segment(a['code'])
                            and not Ledger.search_count([
                                ('company_id', '=', company.id),
                                ('code', '=', a['code']),
                                ('action', '=', 'created')])):
                        collision += 1
                        collided_codes.append(a['code'])
                        _logger.error(
                            'suite_cn_coa: 撞号跳过 —— 公司 %s 目标码 %s 属我方自建号段'
                            '(2221.51–.99),却已被既有科目「%s」占用(非我方发行)。不覆盖、'
                            '不认领,请人工核对(官方可能新占了该号段)。',
                            company.id, a['code'], acc.display_name)
                        if not dry_run:
                            self._record_collision(Ledger, company, a, acc)
                        continue
                    claimed += 1
                    if a['code'] in CASH_CODES and acc.account_type != 'asset_cash':
                        cash_warn += 1
                        cash_details.append(
                            {'code': a['code'], 'current_type': acc.account_type})
                        _logger.warning(
                            'suite_cn_coa: 公司 %s 已有科目 %s 但 account_type=%s(非 '
                            'asset_cash);CF 现金判据靠它,【认领不改,请人工核对】。',
                            company.id, a['code'], acc.account_type)
                    if not dry_run:
                        self._record_claim(Ledger, company, a, acc)
                    continue
                if dry_run:
                    created += 1
                    continue
                acc = AccPub.with_company(company).create({
                    'code': a['code'], 'name': a['name'],
                    'account_type': a['account_type'], 'reconcile': a['reconcile'],
                    # R43-T4:6 条地方税种默认归档(active=False);其余默认 True。
                    'active': a.get('active', True),
                })
                Ledger.create({
                    'company_id': company.id, 'code': a['code'],
                    'account_id': acc.id, 'taxpayer': a['taxpayer'],
                    'action': 'created'})
                created += 1
            if not dry_run:
                self._validate_codes(company)
            # R43-T1d:旧版连号残留检测(只报不动——「发行的科目留库」承诺不破)。
            legacy = self._detect_legacy_lianhao(company)
            if legacy:
                _logger.warning(
                    'suite_cn_coa: 公司 %s 存在 %d 条旧版【连号】科目(%s%s)——本版(3.0)'
                    '已改点分编码;建议【重建库】或手工归档这些科目。本模块【不会自动删除或'
                    '改动它们】。', company.id, len(legacy), ', '.join(legacy[:10]),
                    '…' if len(legacy) > 10 else '')
            # R43-T4:默认归档(active=False)的科目须在回执明列 —— 否则「发了又藏」=
            # 等于没发(归档科目界面默认不显示),客户照样自建、指标3零省、反增隐形科目。
            archived = [{'code': a['code'], 'name': a['name']}
                        for a in rows
                        if not a.get('active', True) and a['code'] not in collided_codes]
            report[company.id] = {
                'company': company.display_name, 'taxpayer': taxpayer,
                'target': len(rows), 'created': created,
                'claimed': claimed, 'cash_warn': cash_warn,
                'cash_details': cash_details, 'collision': collision,
                'legacy_lianhao': legacy, 'archived': archived}
        return report

    @api.model
    def _publish_lang_active(self):
        """R38-T3:zh_CN 是否已【激活】(res.lang.active)。单独成方法便于测试打桩。"""
        return bool(self.env['res.lang'].with_context(active_test=False).search_count(
            [('code', '=', PUBLISH_LANG), ('active', '=', True)]))

    @api.model
    def _lang_rejected(self, company):
        """T4-a 门控同形状的语言拒绝项(可读原因:缺什么语言/去哪装/为什么必须先装,
        不写「见日志」——惯例5;不得静默继续)。"""
        return {
            'company': company.display_name, 'rejected': True,
            'reason': ('发行前必须先激活中文（%(lang)s）。当前该语言未激活 → 发行的科目名'
                       '只会写入 en_US 单键，中文界面靠回落显示、且【事后永久无法补全 %(lang)s '
                       '键】（我方科目是运行时创建的用户数据，与官方科目走模块翻译不同——'
                       '官方在激活语言时会自动回填，我方不会）。请先到 设置 → 翻译 → 语言，'
                       '安装并激活「中文（简体）」，再发行。装机顺序应【先装语言、再建公司 / '
                       '装科目表】。' % {'lang': PUBLISH_LANG}),
        }

    @api.model
    def _rejected(self, company):
        """T4-a:非 cn 准则公司的拒绝报告项(可读原因,不写「见日志」——惯例5)。"""
        chart = company.chart_template or '(未设置)'
        return {
            'company': company.display_name, 'rejected': True,
            'chart_template': chart,
            'reason': ('公司「%s」的科目表准则是 %s，不是小企业会计准则（cn）。本模块只向 '
                       'ASSBE（小企业会计准则）账套发行科目表；不向企业会计准则'
                       '（cn_large_bis）或非中国科目表发行，以免污染其科目表——例如编码 '
                       '4001 在两套准则语义相反（ASSBE=生产成本 / ASBE=实收资本）。'
                       % (company.display_name, chart)),
        }

    @api.model
    def _record_claim(self, Ledger, company, a, acc):
        """T4-b (缺陷#3):认领留痕。仅在【无既有台账行】时记一条 action='claimed' 快照
        (code / 认领前名称 / 认领前 type / 是否与我方同名 / 时间=create_date)。

        幂等:我方 created 的科目在第二轮发行会走认领分支,但台账已有其 'created' 行 →
        跳过,不翻转。首次遇到【无台账行的既有科目】= 真·认领客户科目 → 记快照。
        🔴 同名判定按环境语言取 acc.name(CN 部署 zh_CN 激活时即中文名);主审计价值在
        claimed_name/claimed_type 两个快照字段,恒captured,same_name 只是便捷标。"""
        exists = Ledger.search(
            [('company_id', '=', company.id), ('code', '=', a['code'])], limit=1)
        if exists:
            return exists
        cur_name = acc.with_company(company).name or ''
        return Ledger.create({
            'company_id': company.id, 'code': a['code'], 'account_id': acc.id,
            'taxpayer': a['taxpayer'], 'action': 'claimed',
            'claimed_name': cur_name, 'claimed_type': acc.account_type,
            'claimed_same_name': (cur_name == a['name']),
        })

    @api.model
    def _record_collision(self, Ledger, company, a, acc):
        """R43-T1c:撞号留痕。我方号段(2221.51+)目标码被非我方科目占用 → 记 action=
        'collision' 快照(占用者名/type),幂等(已有台账行则不重复)。"""
        exists = Ledger.search(
            [('company_id', '=', company.id), ('code', '=', a['code'])], limit=1)
        if exists:
            return exists
        return Ledger.create({
            'company_id': company.id, 'code': a['code'], 'account_id': acc.id,
            'taxpayer': a['taxpayer'], 'action': 'collision',
            'claimed_name': acc.with_company(company).name or '',
            'claimed_type': acc.account_type, 'claimed_same_name': False,
        })

    # ----------------------------------------------- R43-T1d 旧版连号残留检测
    @api.model
    def _detect_legacy_lianhao(self, company):
        """只读检测本库残留的【旧版连号形态·我方科目】(2.x 装过、升 3.0 未重建)。

        🔴 只报不动:不 unlink、不改码、不合并(R43-T1d 裁定)——manifest「发行的科目留库」
        是保护客户数据的承诺,一段会 unlink account.account 的迁移即便删我方发的也破这条
        承诺,而它服务 0 个客户。故 3.0 不提供自动迁移,仅告警 + 建议重建库。

        判据(R45-T1 收窄为【且】):无 '.'、位数 > 4、【2221 段纯数字】、【且有我方发行台账痕迹】。
        —— 原判据末项是【或】:只要 `2221`+纯数字即命中、不要求台账痕迹。但【中国实务主流编码
        就是连号】——金蝶星辰(小企业)真实科目表有一整套 `2221001 应交增值税`/`2221011 应交
        所得税` 等规规矩矩的应交税费明细(实测 34 条命中该分支),它们是【从金蝶迁来的正常客户
        的自有科目】,不是我方 2.x 残留。产品上线前无任何客户装过 2.x ⇒「有我方残留」的服务
        人群为空,而「或」分支的唯一现实受众反而是【被误报的连号客户】(惯例29:载体可见人群
        应 ∩ 问题相关人群)。改【且】的真阳不丢证明:真·我方残留 = 2.x 用 create 分支建的科目,
        create【写过发行台账】(缺陷#3 只影响【认领】留痕、不影响【新建】;R35 实证新建 43 条
        皆有迹)⇒ 台账痕迹恒在 ⇒ 仍命中;而客户自有连号(金蝶迁入、无我方台账)⇒ 痕迹缺 ⇒
        不再误报。返回排序后的 code 列表。"""
        AccC = self.env['account.account'].with_company(company).with_context(
            active_test=False)
        Ledger = self.env['suite.cn.coa.published.account']
        tracked = set(Ledger.search(
            [('company_id', '=', company.id)]).mapped('code'))
        legacy = []
        for acc in AccC.search([('company_ids', 'in', company.id)]):
            code = acc.with_company(company).code or ''
            if '.' in code or len(code) <= 4:
                continue
            if (code.startswith('2221') and code[4:].isdigit()) and code in tracked:
                legacy.append(code)
        return sorted(legacy)

    # -------------------------------------------------------- T4-c 存量污染扫描
    @api.model
    def _scan_foreign_publications(self):
        """只读扫描(缺陷#3 收尾,任意库可跑):找出【公司 chart_template 非 cn、却有我方
        发行台账痕迹】的科目。返回 {'by_ledger': [...], 'untracked_note': str}。

        🔴 可靠面 = 台账法:published.account 行 join 公司 chart≠cn —— 抓 R35 那批【新建】的
        43 条(create 分支写过台账,有迹)。
        🔴 盲区(诚实标注,惯例12「查到0≠真为0」):R35 那 14 条【认领】在旧版【不写台账】
        (正是缺陷#3),故【无痕迹、扫不到】。且非 cn 公司上大量编码(1001/1122…)本就与官方
        ASBE 表重合,纯靠码集命中会把官方科目全误报 → 不产出噪声启发式清单。这 14 条历史认领
        用编码无法与官方区分;T4-b 起认领已留痕,未来同类可查。
        只报不修:处置(回收/归档/留)是 Safi 拍板项,不在本方法职责。"""
        Ledger = self.env['suite.cn.coa.published.account']
        by_ledger = []
        for rec in Ledger.search([]):
            comp = rec.company_id
            if comp.chart_template == ASSBE_CHART_TEMPLATE:
                continue
            by_ledger.append({
                'company_id': comp.id, 'company': comp.display_name,
                'chart_template': comp.chart_template or '(无)',
                'code': rec.code, 'action': rec.action,
                'account_id': rec.account_id.id,
                'account_name': rec.account_id.with_company(comp).name,
                'claimed_name': rec.claimed_name or '',
                'claimed_type': rec.claimed_type or '',
                'taxpayer': rec.taxpayer,
            })
        note = ('台账法抓到 %d 条【非 cn 公司上的我方发行痕迹】。⚠ 盲区:旧版【认领】不写台账'
                '(缺陷#3),故历史误认领无痕、扫不到;非 cn 公司编码与官方 ASBE 大量重合,纯码集'
                '命中会全误报官方科目,故不产启发式清单。T4-b 起认领已留痕。' % len(by_ledger))
        return {'by_ledger': by_ledger, 'untracked_note': note}

    # --------------------------------------------------------------- validate
    @api.model
    def _validate_codes(self, company):
        """§4.7:发行后核该公司无【有记录无 code】科目(F3/B-63 静默错报形态)。

        Odoo 原生 _ensure_code_is_unique 在 create 时已强制"每公司必有 code",本方法是
        发行层的复核:若因多公司 context 处理不净漏出空码科目,立刻告警(不静默)。"""
        empty = self.env['account.account'].with_company(company).with_context(
            active_test=False).search([
                ('company_ids', 'in', company.id), ('code', '=', False)])
        if empty:
            _logger.warning(
                'suite_cn_coa: 公司 %s 存在 %d 个【有记录无 code】科目(id=%s)——'
                'F3/B-63 静默错报形态,请核对多公司 code 上下文。',
                company.id, len(empty), empty.ids)
        return not empty
