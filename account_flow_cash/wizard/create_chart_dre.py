# -*- coding: utf-8 -*-

import logging
import time
from openerp.osv import fields, osv
#from datetime import datetime, date, timedelta

_logger = logging.getLogger(__name__)

class wiz_create_chart_dre(osv.osv_memory):
    """
    Assitente para criar o DRE do período
    """
    _name = "wiz.create.chart_dre"
    _description = ""
    _columns = {
        'date_ger': fields.date(u'Data Geração'),
        'period_from': fields.many2one('account.period', u'Período', required=True),
    }   


    def action_wiz_create_chart_dre(self, cr, uid, ids, context=None):
        _logger.info(self._name)
        if context == None:
            context = {}

        [wizard] = self.browse(cr, uid, ids)
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        objChartDRE = self.pool.get('chart_dre')
        
        chart = {
                 'date': time.strftime('%Y-%m-%d'),
                 'period_id': wizard.period_from.id,
        }
        
        _logger.info(u'Cria Chart: '+str(chart))
        
        idChartDRE = objChartDRE.create(cr,uid,chart,context=None)
        
        #ChartFlowCash = objChartFlowCash.browse(cr,uid,id_ChartFlowCash,context)
        
        objChartDRE.cria_dre(cr,uid,idChartDRE,wizard.period_from.id)
        
        result = mod_obj.get_object_reference(cr, uid, 'account_flow_cash', 'action_chart_dre_line')
        _logger.info('ID1 = '+str(result))
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('chart_id','=',"+str(idChartDRE)+")]"
        _logger.info('ID2 = '+str(result))
        
        return result
    
    _defaults = {
                 'date_ger': lambda *a: time.strftime('%Y-%m-%d'),
                }
        
wiz_create_chart_dre()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: