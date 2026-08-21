# -*- coding: utf-8 -*-
# suite_cn_statement — Chinese financial-statement presentation.
# R20: data-only (year-begin / YTD columns, moved from suite_cn_ledger).
# R21: reporting-form (报送版式) mapping models + XLSX export renderer.
# R23: install/upgrade self-check for the generated year-begin / YTD expressions.
from . import models
from . import wizards
from .hooks import post_init_hook
