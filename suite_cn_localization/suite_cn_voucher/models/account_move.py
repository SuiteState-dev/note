# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import api, fields, models, _
from odoo.tools import mute_logger, float_round

# 凭证字（Chinese voucher word）。首版取封闭 4 值：法定三类（收/付/转）+ 通用「记」。
# 🔴 这不是「法定封闭集」——《会计基础工作规范》§50 是「可以」分收付转、也「可以」用
# 通用凭证，非穷尽列举（实务中金蝶凭证字是可维护的基础资料，五字账套「现收/现付/
# 银收/银付/转」不少）。取 Selection 是**产品决策**：加值廉价可逆（子模块 selection_add，
# 零迁移），只有 Selection→m2o 才不可逆有迁移成本，首版吃这个敞口。扩展走 selection_add。
VOUCHER_WORDS = [
    ('receipt', '收款'),
    ('payment', '付款'),
    ('transfer', '转账'),
    ('general', '记'),
]
VOUCHER_WORD_LABELS = dict(VOUCHER_WORDS)

# —— T2-c (缺陷#8) 凭证科目路径:父名前缀分隔符【枚举集】(不用贪婪正则)——————————————
# 官方明细科目名自带父名前缀(「应交税费 - 应交增值税（销项税额）」),拼「一级/明细」会重复。
# 剥除前缀须满足【父名 + 分隔符】(必须有分隔符:「应收」+「应收账款」无分隔符 ⇒ 不剥,防误剥)。
# 集合按【长的在前】匹配(带空格的 ' - ' 先于裸 '-'),枚举官方/常见写法,不含裸空格(防过剥)。
VOUCHER_PATH_SEPARATORS = (
    ' - ', ' — ', ' / ', ' · ', ' _ ', ' : ', ' ： ',
    '--', '-', '—', '/', '·', '_', '：', ':',
)

# —— T2 中文财务大写金额(人民币)常量,依据中国人民银行《正确填写票据和结算凭证的基本规定》——
_CN_DIGITS = '零壹贰叁肆伍陆柒捌玖'      # 数字大写
_CN_UNIT = ('', '拾', '佰', '仟')        # 组内四位单位(个/拾/佰/仟)
_CN_GROUP = ('', '万', '亿', '兆')       # 四位一组的分级单位


class AccountMove(models.Model):
    _inherit = 'account.move'

    # —— T1-1 只加 2 个存储字段，别扩 ——
    l10n_cn_voucher_word = fields.Selection(
        VOUCHER_WORDS, string='凭证字', default='general', copy=False, tracking=True,
        help="中式记账凭证的凭证字。多数企业只用通用「记」；需要分收/付/转的账套可改。")
    l10n_cn_voucher_number = fields.Integer(
        string='凭证号', copy=False, readonly=True, tracking=True,
        help="按（公司 × 凭证字 × 会计期间）连续编号，过账时分配。「记-N」的前缀是呈现层格式，"
             "不入存储 —— 断号检查因此是一条 SQL 而非字符串解析。")
    # 呈现层显示串「记-1」，不入存储
    l10n_cn_voucher_display = fields.Char(
        string='凭证字号', compute='_compute_l10n_cn_voucher_display')

    @api.depends('l10n_cn_voucher_word', 'l10n_cn_voucher_number')
    def _compute_l10n_cn_voucher_display(self):
        for move in self:
            if move.l10n_cn_voucher_number:
                label = VOUCHER_WORD_LABELS.get(move.l10n_cn_voucher_word or 'general', '记')
                move.l10n_cn_voucher_display = '%s-%s' % (label, move.l10n_cn_voucher_number)
            else:
                move.l10n_cn_voucher_display = False

    # —— T1-2 取号：过账才给号（同构 name，§16.2 verified）——
    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted._l10n_cn_assign_voucher_number()
        return posted

    def _l10n_cn_voucher_sequence(self):
        """每（公司 × 凭证字）一条 ir.sequence，use_date_range=True。
        懒创建（多公司下装机时不知道有哪些公司）；卸载由 uninstall_hook 清理。
        implementation='standard'：PG nextval 并发安全、允许断号——与「删除释放号=接受
        gap」的处置(a)一致；no_gap 的 FOR UPDATE NOWAIT 会在并发过账时直接抛错，更差。
        """
        self.ensure_one()
        word = self.l10n_cn_voucher_word or 'general'
        code = 'l10n_cn.voucher.%s' % word
        Seq = self.env['ir.sequence'].sudo()
        seq = Seq.search(
            [('code', '=', code), ('company_id', '=', self.company_id.id)], limit=1)
        if not seq:
            seq = Seq.create({
                'name': '中式凭证号 · %s（%s）' % (VOUCHER_WORD_LABELS[word], self.company_id.name),
                'code': code,
                'company_id': self.company_id.id,
                'implementation': 'standard',
                'use_date_range': True,
                'prefix': '', 'suffix': '', 'padding': 1,
                'number_next': 1, 'number_increment': 1,
            })
        return seq

    @mute_logger('odoo.sql_db')
    def _l10n_cn_ensure_month_range(self, seq, move_date):
        """确保 seq 下存在覆盖 move_date 所在**月**的 date_range（Odoo 自动建的是**年**粒度，
        中式凭证号按会计期间=月归零，故须自建月区间）。search-then-create，靠
        UNIQUE(sequence_id,date_from,date_to) 幂等；并发下撞唯一约束则回查。"""
        month_start = move_date.replace(day=1)
        month_end = month_start + relativedelta(months=1) - timedelta(days=1)
        DR = self.env['ir.sequence.date_range'].sudo()
        domain = [('sequence_id', '=', seq.id),
                  ('date_from', '=', month_start), ('date_to', '=', month_end)]
        dr = DR.search(domain, limit=1)
        if dr:
            return dr
        try:
            with self.env.cr.savepoint():
                dr = DR.create({
                    'sequence_id': seq.id,
                    'date_from': month_start, 'date_to': month_end,
                })
        except IntegrityError:
            dr = DR.search(domain, limit=1)
        return dr

    def _l10n_cn_assign_voucher_number(self):
        """给已过账、尚无号的凭证分配号。作废/草稿不清号（跳号不释放）；
        删除随记录消失=接受 gap（处置 a）；反过账另编新号（红冲同构）。"""
        for move in self:
            if move.l10n_cn_voucher_number or move.state != 'posted' or not move.date:
                continue
            seq = move._l10n_cn_voucher_sequence()
            move._l10n_cn_ensure_month_range(seq, move.date)
            num_str = seq._next(sequence_date=move.date)
            digits = ''.join(ch for ch in (num_str or '') if ch.isdigit())
            move.l10n_cn_voucher_number = int(digits or '0')

    # —— T1-3 一级—明细科目串（按编码结构；取不到原样打全名，不报错不猜）——
    def _l10n_cn_account_path(self, line):
        """返回「一级科目名 / 明细科目名」。三档顺序判定（R34，Safi 定案连号）：

          档1  code 含 `.`         → `split('.',1)[0]`（官方点分体系，如 2221.01.01）
          档2  无点 且 len>4 且     → 取 `code[:4]`（连号体系，R33-A 我方发行件:一级4/二级7/
               `code[:4]` 本公司存在   三级10、code=parent+3位）。🔴 第三个条件是【边界非装饰】:
                                     只在前4位确实是本公司真实存在的一级科目时才截 → 我方发行表
                                     恒成立（我方发行=我方保证一级4位）,客户自带的怪表自然失效落
                                     档3。故不违 R28-T2-7「连号非任意客户编码通解」(那条管别人的表)。
          档3  以上都不满足         → `display_name` 全名，绝不报错、绝不猜连号边界

        依据实测（R34-T2 verified）：`2221001001 进项税额` 档2 前有本规则时打全名，加档2后
        截 `2221` → 「应交税费 / 进项税额」。"""
        account = line.account_id
        if not account:
            return ''
        Account = self.env['account.account'].with_company(self.company_id)
        code = account.with_company(self.company_id).code or ''
        top_code = None
        if '.' in code:                                  # 档1 点分
            cand = code.split('.', 1)[0]
            if cand and cand != code:
                top_code = cand
        elif len(code) > 4:                              # 档2 连号取前4位一级
            top_code = code[:4]
        if top_code:
            # 单次查存在性:档2 的「前4位须真实存在」边界与档1 的「一级须存在才截」同此一查;
            # 查不到 → 落档3 全名（含档2 客户怪表 code[:4] 不存在的情形）。
            top = Account.search([('code', '=', top_code)], limit=1)
            if top and top.id != account.id and top.name:
                # T2-c(缺陷#8):官方明细名自带父名前缀 → 剥除,避免「应交税费 / 应交税费 - …」。
                detail = self._l10n_cn_strip_parent_prefix(top.name, account.name)
                return '%s / %s' % (top.name, detail)
        return account.display_name                      # 档3 全名

    @api.model
    def _l10n_cn_strip_parent_prefix(self, parent_name, detail_name):
        """T2-c(缺陷#8):若明细名以【父名 + 分隔符】开头,剥除该前缀(否则凭证上父名重复)。

        🔴 触发面仅【官方点分科目】(名带前缀);我方发行件是短名(不带前缀)→ 不触发、不误剥
        (这解释了它为何一直没被 dev 库测出——dev 库我方科目占多数)。R43-T1 改点分【不消除
        本缺陷】:我方改的是编码不是名称,我方仍短名、官方仍带前缀。
        必须有分隔符:「应收」+「应收账款」无分隔符 ⇒ 不剥(防误剥,语义不同)。"""
        if not parent_name or not detail_name:
            return detail_name
        if detail_name.startswith(parent_name):
            rest = detail_name[len(parent_name):]
            for sep in VOUCHER_PATH_SEPARATORS:
                if rest.startswith(sep):
                    return rest[len(sep):].strip() or detail_name
        return detail_name

    # —— T2 缺陷#5 中文财务大写金额 ——————————————————————————————————————————
    @api.model
    def _convert_to_amount_in_word(self, number):
        """中文财务大写金额(人民币)。override 上游 l10n_cn 同名方法。

        🔴 为什么必须自研(非改官方数据,是方法 override,不受偏离清单封顶约束):
          * 上游 l10n_cn `_convert_to_amount_in_word` 依赖 cn2an,未装则返回 None ⇒ QWeb
            `t-esc` 渲染空白 ⇒ 凭证「金额合计(大写)」格空白。
          * 原生 `currency_id.amount_to_text` 走 num2words 产【英文】(One Hundred...)。
          ⇒ 原生与上游均不可用,自研且不依赖外部库。

        币种守卫:仅 `currency_id` 为 CNY(人民币)时产中文大写;其他币种落回上游行为
          (super → cn2an 或 None),不对所有币种硬套。

        规则(中国人民银行《正确填写票据和结算凭证的基本规定》):
          数字 零壹贰叁肆伍陆柒捌玖;单位 拾佰仟万亿、元角分。到元为止「元」后写「整」;
          到角为止「角」后不写「整」;有分「分」后不写「整」;中间 0 写「零」、连续 0 只写一个。

        🔴 负数形态【已定】(R43-T2-b,缺陷#5 销号,证据级 observed 单人样本):二姐口径
          「红字是手工登记账的标识／现在没有手工帐啦／没红字」⇒ 取绝对值、方向由借贷栏承载、
          不做红字。与 R36 既有实现(本方法取 abs)一致 ⇒ 零代码改动。两位小数以外(浮点误差/
          三位小数):四舍五入到分(HALF-UP)。
        """
        currency = (self.currency_id[:1] or self.company_id[:1].currency_id
                    or self.env.company.currency_id)
        if currency.name != 'CNY':
            return super()._convert_to_amount_in_word(number)
        if number is None:
            return None
        return self._l10n_cn_rmb_upper(number)

    @api.model
    def _l10n_cn_int_upper(self, n):
        """非负整数 → 中文大写(财务体:10→壹拾)。四位一组,组内零折叠、跨组零折叠成一个「零」,
        组末全零则跳过该级 万/亿 单位。"""
        if n <= 0:
            return _CN_DIGITS[0]
        s = str(n)
        length = len(s)
        out = ''
        zero_pending = False
        for i, ch in enumerate(s):
            d = int(ch)
            pos = length - 1 - i          # 自右起的位次(0=个)
            unit = pos % 4                 # 组内位(0拾1佰2仟... 实为 个拾佰仟)
            group = pos // 4               # 分级(0个组 1万 2亿)
            if d == 0:
                zero_pending = True        # 暂挂,遇下一个非零才落一个「零」
            else:
                if zero_pending:
                    out += _CN_DIGITS[0]
                    zero_pending = False
                out += _CN_DIGITS[d] + _CN_UNIT[unit]
            if unit == 0 and group > 0:
                # 到达某分级组的个位:该组四位非零才补 万/亿,否则跳过(连续零由 zero_pending 收敛)
                grp = int(s[max(0, length - (group + 1) * 4): length - group * 4])
                if grp != 0:
                    out += _CN_GROUP[group]
                    zero_pending = False
        return out

    @api.model
    def _l10n_cn_rmb_upper(self, amount):
        """金额(元, float)→ 人民币大写。取绝对值(负数红字待定);四舍五入到分。"""
        total_fen = int(float_round(abs(amount) * 100.0, precision_digits=0,
                                    rounding_method='HALF-UP'))
        int_part = total_fen // 100
        jiao = (total_fen % 100) // 10
        fen = total_fen % 10
        head = (self._l10n_cn_int_upper(int_part) if int_part else _CN_DIGITS[0]) + '元'
        if jiao == 0 and fen == 0:
            return head + '整'                       # 到元为止 → 元后「整」
        tail = ''
        if jiao == 0:
            # 元后直接是分(角位为 0)→ 补一个「零」再接分
            tail += _CN_DIGITS[0] + _CN_DIGITS[fen] + '分'
        else:
            if int_part and int_part % 10 == 0:
                tail += _CN_DIGITS[0]                # 元位为 0 且有角 → 元后补「零」
            tail += _CN_DIGITS[jiao] + '角'
            if fen:
                tail += _CN_DIGITS[fen] + '分'       # 有分「分」后不写「整」;无分到角为止亦不写「整」
        return head + tail
