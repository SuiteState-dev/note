# Official tax-bureau template fixtures (R26-T1)

`test_template_alignment` asserts our 中式版式 XLSX export matches the **official**
tax-bureau template cell-for-cell on the header block (rows 0–4). The expected values
are **parsed from the original files** — never transcribed into the test (the prose
spec was wrong once: it missed the blank column A).

Drop the two official templates here, with these **exact** filenames:

- `财务报表报送与信息采集（小企业会计准则）月季报.xls`
- `财务报表报送与信息采集（小企业会计准则）年报.xls`

Until they are present, `test_template_alignment` `skipTest`s (and the meanwhile
`test_template_geometry_single` / `_two_column` guard our renderer's geometry).

These are `.xls` (BIFF8); the alignment test will parse them with `xlrd`. If a future
ASBE template arrives (`…（企业会计准则）…`), add it here and reuse the same assertions.
