# -*- coding: utf-8 -*-

import logging
import time
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from datetime import datetime

_logger = logging.getLogger(__name__)

TYPE_STATUS = {
                 'ok': 'OK',
                 'pv': 'Prev',
                 'at': 'Atra'
                }

TYPE_FILTRO = {
                 }


class account_flow_cash(osv.osv_memory):
    """
    For Flow Cash
    """
    _name = "account.flow_cash"
    _description = "Account flow cash"
    _columns = {
        'date_from': fields.date('Data Inicial', readonly=True),
        'date_to': fields.date('Data Final', readonly=True),
        'date': fields.date('Data Emissão', readonly=True),
        'linhas_ids' : fields.one2many('account.flow_cash.line','flowcash_id','Movimento',readonly=True),
        'target_move': fields.selection([('all', 'Realizado + Previsto'),
                                         ('real', 'Realizado'),
                                         ('prev', 'Previsto')
                                        ], 'Filtro', required=True,readonly=True),
    }
    
    def create_flow(self, cr, uid, DataIn, DataOut, Tipo='all', Transf=False, context=None):
        if context == None:
            context = {}
        _logger.info('DataIn = '+str(DataIn))    
        _logger.info('DataOut = '+str(DataOut))    
        hoje = datetime.today()
        dFlow = {
                 'date_from': DataIn,
                 'date_to': DataOut,
                 'date': hoje,
                 'target_move': Tipo,
                 }
        _logger.info('SQL = '+str(dFlow))
        FlowCash = self.pool.get('account.flow_cash')
        FlowCashLine = self.pool.get('account.flow_cash.line')
        idFlowCash = FlowCash.create(cr,uid,dFlow,context)
        AccMoveLine = self.pool.get('account.move.line')
        
        sql = "SELECT sum(credit) as vlcred, sum(debit) as vldebit " \
              "FROM account_move_line a " \
              "JOIN account_account b ON a.account_id = b.id " \
              "WHERE CAST(date AS DATE) < '%s'" % datetime.strftime(DataIn,'%Y-%m-%d')+" " \
              "AND b.code similar to '(1.01.01.)%'"
        
        _logger.info('SQL = '+sql)
        
        cr.execute(sql)
        res = cr.fetchone()
        
        vlCred = float(res[0] or 0)
        vlDeb = float(res[1] or 0)

        _logger.info('Creditos/Debitos = '+str(vlCred)+' / '+str(vlDeb))

        vlAcum = vlDeb - vlCred
        dLineFlow = {
                     'name': 'Saldo Anterior',
                     'flowcash_id': idFlowCash,
                     'seq': 0,
                     'date': DataIn,
                     'val_sum': vlAcum,
                     }
        LineFlowId = FlowCashLine.create(cr,uid,dLineFlow,context)
        Seq = 1
        vlSaldo = 0
        if Tipo=='all' or Tipo=='real': 
            _logger.info('realizado: '+Tipo)
            MoveLineIds = AccMoveLine.search(cr, uid,[('date', '>=', DataIn), ('date', '<=', DataOut),('account_id', '=like', '%s%%' % '1.01.01.'),],order='date,id')
            for MoveLine in AccMoveLine.browse(cr, uid, MoveLineIds, context):
                computa = True
                if Transf == False:
                    CPartidaIds = AccMoveLine.search(cr, uid,[('move_id', '=', MoveLine.move_id.id), ('id', '<>', MoveLine.id),('account_id', '=like', '%s%%' % '1.01.01.'),],order='date')
                    if len(CPartidaIds) > 0:
                        computa = False
                if computa:
                    if MoveLine.credit > 0:
                        vlCredito = MoveLine.credit
                    else:
                        vlCredito = 0
                    if MoveLine.debit > 0:
                        vlDebito = MoveLine.debit
                    else:
                        vlDebito = 0
                    vlSaldo = vlDebito - vlCredito
                    vlAcum  = vlAcum + vlSaldo
                    name = MoveLine.ref or MoveLine.name or ''
                    if MoveLine.partner_id:
                        if name: name = name + ", "
                        name = name + MoveLine.partner_id.name
                    dLineFlow = {
                                 'name': name,
                                 'flowcash_id': idFlowCash,
                                 'seq': Seq,
                                 'date': MoveLine.date,
                                 'val_in': vlDebito,
                                 'val_out': vlCredito,
                                 'val_add': vlSaldo, 
                                 'val_sum': vlAcum,
                                 'state': 'ok'
                                 }
                    LineFlowId = FlowCashLine.create(cr,uid,dLineFlow,context)
                    Seq = Seq + 1

        if Tipo=='all' or Tipo=='prev':
            _logger.info('previsto')
            MoveLineIds = AccMoveLine.search(cr, uid,[('date_maturity','<>',False),
                                                      ('date_maturity', '<=', DataOut),
                                                      ('account_id.type', 'in', ['receivable', 'payable']), 
                                                      ('reconcile_id', '=', False),],order='date_maturity,id')
            for MoveLine in AccMoveLine.browse(cr, uid, MoveLineIds, context):
                if datetime.strptime(MoveLine.date_maturity,'%Y-%m-%d') < datetime.today():
                    DateDue = datetime.today()
                    Status = 'at'
                else:
                    DateDue = datetime.strptime(MoveLine.date_maturity,'%Y-%m-%d')
                    Status = 'pv' 
                if MoveLine.credit > 0:
                    vlCredito = MoveLine.amount_to_pay
                else:
                    vlCredito = 0
                if MoveLine.debit > 0:
                    vlDebito = MoveLine.amount_to_pay * (-1)
                else:
                    vlDebito = 0
                vlSaldo = vlDebito - vlCredito
                vlAcum  = vlAcum + vlSaldo
                name = MoveLine.ref or MoveLine.name or ''
                if MoveLine.partner_id:
                    if name: name = name + ", "
                    name = name + MoveLine.partner_id.name
                dLineFlow = {
                             'name': name,
                             'flowcash_id': idFlowCash,
                             'seq': Seq,
                             'date': DateDue,
                             'val_in': vlDebito,
                             'val_out': vlCredito,
                             'val_add': vlSaldo, 
                             'val_sum': vlAcum,
                             'state': Status,
                             }
                LineFlowId = FlowCashLine.create(cr,uid,dLineFlow,context)
                Seq = Seq + 1
        
        return idFlowCash
    
account_flow_cash()

class account_flow_cash_line(osv.osv_memory):
    """
    For Flow Cash
    """
    _name = "account.flow_cash.line"
    _description = "Account flow cash line"
    _order = "seq asc, id asc"
    _columns = {
        'name': fields.char(u'Descrição', size=64),
        'flowcash_id': fields.many2one('account.flow_cash',u'Fluxo de Caixa'),
        'seq': fields.integer(u'Sq'),
        'date': fields.date(u'Data'),
        'val_in': fields.float(u'Entradas', digits_compute=dp.get_precision('Account')), 
        'val_out': fields.float(u'Saídas', digits_compute=dp.get_precision('Account')),
        'val_add': fields.float(u'Saldo', digits_compute=dp.get_precision('Account')), 
        'val_sum': fields.float(u'Acumulado', digits_compute=dp.get_precision('Account')), 
        'state': fields.selection([
            ('ok','OK'),
            ('pv','Prev'),
            ('at','Atra'),
            ],'St', select=True,),
    }
    
    _defaults = {
        #'date': lambda *a: time.strftime('%Y-%m-%d'),
        #'val_in': lambda *a: 0,
        #'val_out': lambda *a: 0,
        #'val_add': lambda *a: 0,
        #'val_sum': lambda *a: 0,
    }
    
account_flow_cash_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: