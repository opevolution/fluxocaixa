# -*- coding: utf-8 -*-

try:
    import account_flow_cash
    import chart_dre
    import wizard
    import report
except ImportError:
    import logging
    logging.getLogger('openerp.module').warning('report_xls not available in addons path. account_financial_report_webkit_xls will not be usable')
