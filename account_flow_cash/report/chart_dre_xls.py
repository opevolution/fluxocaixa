# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import xlwt
import time
from datetime import datetime
from openerp.osv import orm
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.tools.translate import translate, _
from openerp import pooler
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'chart_dre_line.xls'


class chart_dre_line_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(chart_dre_line_xls_parser, self).__init__(cr, uid, name, context=context)
        move_obj = self.pool.get('chart_dre_line')
        self.context = context
        wanted_list = move_obj._report_xls_fields(cr, uid, context)
        template_changes = move_obj._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
            'template_changes': template_changes,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'pt_BR')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) or src


class chart_dre_line_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(chart_dre_line_xls, self).__init__(name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_center = xlwt.easyxf(aml_cell_format + _xs['center'])
        self.aml_cell_style_date = xlwt.easyxf(aml_cell_format + _xs['left'], num_format_str=report_xls.date_format)
        self.aml_cell_style_decimal = xlwt.easyxf(aml_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(rt_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)

        # XLS Template
        self.col_specs_template = {
            'name': {
                'header': [1, 42, 'text', _render(u"_('Descrição')")],
                'lines': [1, 0, 'text', _render("line.name or ''")],
                'totals': [1, 0, 'text', None]},
            'code': {
                'header': [1, 42, 'text', _render(u"_('Código')")],
                'lines': [1, 0, 'text', _render("line.code or ''")],
                'totals': [1, 0, 'text', None]},
            'period': {
                'header': [1, 12, 'text', _render(u"_('Período')")],
                'lines': [1, 0, 'text', _render("line.period_id.code or line.period_id.name")],
                'totals': [1, 0, 'text', None]},
            'parent': {
                'header': [1, 12, 'text', _render(u"_('Superior')")],
                'lines': [1, 0, 'text', _render("line.parent_id.code or line.parent_id.name")],
                'totals': [1, 0, 'text', None]},
            'account': {
                'header': [1, 36, 'text', _render(u"_('Conta')")],
                'lines': [1, 0, 'text', _render("line.account_id.code or line.account_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'type': {
                'header': [1, 36, 'text', _render(u"_('Tipo')")],
                'lines': [1, 0, 'text', _render("line.type")],
                'totals': [1, 0, 'text', None]},
            'value': {
                'header': [1, 18, 'text', _render(u"_('Valor')"), None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("line.value"), None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'sum': {
                'header': [1, 18, 'text', _render(u"_('Soma')"), None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("line.sum"), None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
        }

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        wanted_list = _p.wanted_list
        self.col_specs_template.update(_p.template_changes)
        _ = _p._

        sum_pos = 'sum' in wanted_list and wanted_list.index('sum')
        if not sum_pos:
            raise orm.except_orm(_(u'Erro de Customização!'),
                _(u"A coluna 'Soma' é um campo calculado e sua presença é obrigatória!"))

        #report_name = objects[0]._description or objects[0]._name
        report_name = _(u"DRE do Mês")
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
        row_pos += 1

        # Column headers
        c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}), wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        # account move lines
        for line in objects:
            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'lines'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)


chart_dre_line_xls('report.chart_dre_line.xls',
    'chart_dre_line',
    parser=chart_dre_line_xls_parser)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
