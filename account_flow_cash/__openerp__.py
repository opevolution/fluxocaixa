# -*- coding: utf-8 -*-

{
    "name": "FlowCash",
    "version": "0.0.09",
    "author": "Alexandre Defendi",
    "category": "Account",
    "website": "http://evoluirinformatica.com.br",
    "description": "",
    'depends': ['l10n_br_account','report_xls',],
    'js': [],
    'init_xml': [],
    'update_xml': [
        'account_flow_cash.xml',
        'chart_dre_view.xml',
        'wizard/create_flow_cash.xml',
        'wizard/create_chart_dre.xml',
        'report/chart_dre_xls.xml',
        ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
