# China – Cash Flow × Statement Bridge (`suite_cn_cashflow_statement`)

A **bridge** module that couples `suite_cn_cashflow` (the Cash Flow Statement) to
`suite_cn_statement` (the statement-presentation mechanism). It holds only the data that
is meaningless unless **both** sides are installed — the row-number mapping (行次) of the
Cash Flow Statement onto the R21 statement renderer.

## Boundary

- **Not** rendering logic → that lives in `suite_cn_statement`.
- **Not** the cash-flow report definition or items → those live in `suite_cn_cashflow`.
- Only the mapping data that joins the two.

## auto_install

`auto_install = True`. Odoo installs this module automatically once both
`suite_cn_cashflow` and `suite_cn_statement` are present, and uninstalls it as soon as
either side is removed. It is intentionally **not** listed in any module's `depends`
(including the `suite_cn` umbrella) — that would defeat the automatic on/off behaviour.

## This version (R21)

Ships the Cash Flow Statement reporting form as data: one `suite.cn.statement.form` on
`suite_cn_cashflow.cn_cash_flow_s` (single layout, period `YYYY年M期`, columns 本月金额 =
`balance` / 本年累计金额 = `ytd`, note the 本月-before-本年累计 order) plus the 22 statutory
行次 rows and 3 section titles, each 行 bound to its `cn_cf_s_*` report line.

Because the button and renderer live in `suite_cn_statement` and are gated on "does this
report have a form record", installing this bridge makes the **中式版式 XLSX** button appear
on the Cash Flow Statement automatically — this module adds only data, no code (verified
R21: bridge off → CF button gone, BS/PL keep theirs; bridge on → CF button back).

R20 shipped this as an empty skeleton; R21 filled the 行次映射 (design §11.2).
