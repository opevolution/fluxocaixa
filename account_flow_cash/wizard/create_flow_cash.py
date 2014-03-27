# -*- coding: utf-8 -*-

import logging
import time
from openerp.osv import fields, osv
from datetime import datetime, date, timedelta

_logger = logging.getLogger(__name__)

class create_flow_cash(osv.osv_memory):
    """
    Create Flow Cash
    """
    _name = "create.flow_cash"
    _description = "Account flow cash"
    _columns = {
        'date_from': fields.date('Data Inicial', required=True),
        'date_to': fields.date('Data Final', required=True),
        'date_ger': fields.date('Data Geração'),
        'comp_transf': fields.boolean(u'Computa Transferências'),
        'target_move': fields.selection([('ok', 'Realizado'),
                                         ('pv', 'Previsto'),
                                         ('all', 'Realizado e Previsto')
                                        ], 'Filtro', required=True),
        'journal_id': fields.many2one('account.journal', u'Diário',domain=['|',('type', '=', 'cash'),('type', '=', 'bank')]),
        'sintetico': fields.boolean(u'Sintético'),
    }   
    def _get_datefrom(self, cr, uid, ids, context=None):
        dt_atual = datetime.today()
        dt_new   = dt_atual + timedelta(days=-30)
        return dt_new.strftime('%Y-%m-%d')
    
    def show_flow_cash(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        FCa_obj = self.pool.get('account.flow_cash')
        today = datetime.today()
        
        if context == None:
            context = {}

        [wizard] = self.browse(cr, uid, ids)
        
        kwargs={}
        
        if wizard.target_move=='ok':
            DataIn = datetime.strptime(wizard.date_from,'%Y-%m-%d')
            DataOut = today
            kwargs['tipo'] = 'real'
        elif wizard.target_move=='pv':
            DataIn = today
            DataOut = datetime.strptime(wizard.date_to,'%Y-%m-%d')
            kwargs['tipo'] = 'prev'
        else:
            DataIn = datetime.strptime(wizard.date_from,'%Y-%m-%d')
            DataOut = datetime.strptime(wizard.date_to,'%Y-%m-%d')
            kwargs['tipo'] = 'all'
        
        _logger.info('DataIn = '+str(DataIn))    
        _logger.info('DataOut = '+str(DataOut))    
        
        kwargs['transf'] = wizard.comp_transf
        
        if wizard.journal_id:
            kwargs['journal_id'] = wizard.journal_id.id
                
        FlowCashId = FCa_obj.create_flow(cr,uid,DataIn,DataOut,context=context,**kwargs)
        
        result = mod_obj.get_object_reference(cr, uid, 'account_flow_cash', 'action_flow_cash_line_tree')
        _logger.info('ID1 = '+str(result))
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('flowcash_id','=',"+str(FlowCashId)+")]"
        _logger.info('ID2 = '+str(result))
        
        return result
    
    _defaults = {
                'comp_transf': lambda *a: True,
                'date_from': _get_datefrom,
                'date_to': lambda *a: time.strftime('%Y-%m-%d'),
                'date_ger': lambda *a: time.strftime('%Y-%m-%d'),
                'target_move': lambda *a: 'all',
                'comp_transf': lambda *a: False,
                }
        
create_flow_cash()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: