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
    
    def create_flow(self, cr, uid, DataIn, DataOut, context=None, **kwargs):
        if context == None:
            context = {}
        sintetico = False
        account_analitic_id = False
        journal_id = False
        account_id = False
        account_cd = False
        tipo = 'all'
        transf = False
        SaldoAnterior = 0
        if kwargs:
            if 'transf' in kwargs:
                transf = kwargs['transf']
            if 'tipo' in kwargs:
                tipo = kwargs['tipo']
            if 'sintetico' in kwargs:
                sintetico = kwargs['sintetico']
            if 'account_analitic_id' in kwargs:
                account_analitic_id = kwargs['account_analitic_id']
            if 'journal_id' in kwargs:
                journal_id = kwargs['journal_id']
                journal = self.pool.get('account.journal').browse(cr,uid,journal_id,context=None)
                account_id = journal.default_debit_account_id.id
                account_cd = journal.default_debit_account_id.code
                tipo = 'real'
                
                
        _logger.info('DataIn = '+str(DataIn))    
        _logger.info('DataOut = '+str(DataOut))    
        hoje = datetime.today()
        dFlow = {
                 'date_from': DataIn,
                 'date_to': DataOut,
                 'date': hoje,
                 'target_move': tipo,
                 }
        _logger.info('SQL = '+str(dFlow))
        FlowCash = self.pool.get('account.flow_cash')
        FlowCashLine = self.pool.get('account.flow_cash.line')
        idFlowCash = FlowCash.create(cr,uid,dFlow,context)
        AccMoveLine = self.pool.get('account.move.line')
        
        sql = "SELECT a.account_id as id, sum(a.credit) as vlcred, sum(a.debit) as vldebit " \
              "FROM account_move_line a " \
              "JOIN account_account b ON a.account_id = b.id " \
              "WHERE CAST(date AS DATE) < '%s'" % datetime.strftime(DataIn,'%Y-%m-%d')+" " \
              "AND b.type = 'liquidity' "\
              "GROUP BY a.account_id"

#"AND b.code similar to '(1.01.01.)%'"
        
        _logger.info('SQL = {'+sql+'}')
        
        cr.execute(sql)

#         res = cr.fetchone()
#         
#         vlCred = float(res[0] or 0)
#         vlDeb = float(res[1] or 0)
        vlCred = float(0)
        vlDeb = float(0)
        for r in cr.fetchall():
            if account_id:
                if int(account_id) == int(r[0]):
                    vlCred =+ float(r[1] or 0)
                    vlDeb =+ float(r[2] or 0)
            else:
                vlCred =+ float(r[1] or 0)
                vlDeb =+ float(r[2] or 0)
                
            
        _logger.info('Creditos/Debitos = '+str(vlCred)+' / '+str(vlDeb))

        #vlAcum = vlDeb - vlCred
        if journal_id:
            if account_cd == '1.01.01.02.003':
                vlAcum = vlDeb - (vlCred + (-5116.06))
            elif account_cd == '1.01.01.02.004':
                vlAcum = vlDeb - (vlCred + 11431.33)
            elif account_cd == '1.01.01.02.005':
                vlAcum = vlDeb - (vlCred + (-688,24))
            elif account_cd == '1.01.01.02.006':
                vlAcum = vlDeb - (vlCred + (-805.95))
            elif account_cd == '1.01.01.02.007':
                vlAcum = vlDeb - (vlCred + (-192.81))
        else:
            vlAcum = vlDeb - (vlCred + 4628.27)
        
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
        dtFinal = False
        if tipo=='all' or tipo=='real': 
            _logger.info('realizado: '+tipo)  #        if journal_id:sql = sql + " AND a.journal_id = %d" % (journal_id,)
            #MoveLineIds = AccMoveLine.search(cr, uid, [('date', '>=', DataIn), ('date', '<=', DataOut),('account_id.name', '=like', '%s%%' % '1.01.01.'),], order='date,id')
            if account_id:
                MoveLineIds = AccMoveLine.search(cr, uid, [('date', '>=', DataIn), ('date', '<=', DataOut),('account_id','=',account_id)], order='date,id')
            else:
                MoveLineIds = AccMoveLine.search(cr, uid, [('date', '>=', DataIn), ('date', '<=', DataOut),('account_id.type','=','liquidity'),], order='date,id')
                
            for MoveLine in AccMoveLine.browse(cr, uid, MoveLineIds, context):
                computa = True
                if transf == False:
                    CPartidaIds = AccMoveLine.search(cr, uid,[('move_id', '=', MoveLine.move_id.id), ('id', '<>', MoveLine.id),('account_id.type','=','liquidity'),],order='date')
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
                    dtFinal = MoveLine.date

        if tipo=='all' or tipo=='prev':
            _logger.info('previsto')
            #MoveLineIds = AccMoveLine.search(cr, uid, [('date_maturity','<>',False),('date_maturity', '<=', DataOut),('account_id.type', 'in', ['receivable', 'payable']),('reconcile_id', '=', False),], order='date_maturity,id')
            MoveLineIds = AccMoveLine.search(cr, uid, [('date_maturity','<>',False),('date_maturity', '<=', DataOut),('account_id.type', 'in', ['receivable', 'payable']),('reconcile_id', '=', False),], order='date_maturity,id')
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
                dtFinal = DateDue
        if dtFinal:
            dLineFlow = {
                         'name': 'Saldo Final',
                         'flowcash_id': idFlowCash,
                         'seq': Seq,
                         #'date': dtFinal,
                         'val_sum': vlAcum,
                         }
            LineFlowId = FlowCashLine.create(cr,uid,dLineFlow,context)
        
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
        'journal_id': fields.many2one('account.journal', u'Diário',domain=['|',('type', '=', 'cash'),('type', '=', 'bank')]),
        'analytic_account_id': fields.many2one('account.analytic.account', u'Conta Analítica',),
        'sintetico': fields.boolean(u'Sintético'),
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