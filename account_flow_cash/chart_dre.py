# -*- coding: utf-8 -*-

import logging
import time
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from datetime import datetime
from unittest import result

_logger = logging.getLogger(__name__)


def conta_dot(texto):
    i = 0
    for caracter in texto:
        if caracter == '.':
            i = i + 1
            _logger.info('caracter = {'+str(caracter)+'}')
    return i

class chart_dre(osv.osv):
    _name="chart_dre"
    _description= u"DRE Extraído do fluxo de caixa"

    _columns={
              'date': fields.date(u'Data Geração', required=True, readonly=True),
              'period_id': fields.many2one('account.period', u'Período', required=True, readonly=True),
              'linhas_ids': fields.one2many('chart_dre_line','chart_id',u'Linhas do Gráfico', readonly=True),
    }

    _defaults = {
                 'date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def cria_dre(self, cr, uid, id_chart, id_periodo):
        context = {}
        dre = self.browse(cr, uid, id)
        obj_dre_line = self.pool.get('chart_dre_line')
        obj_account = self.pool.get('account.account')
        objPeriodo  = self.pool.get('account.period')
        objContaTipo = self.pool.get('account.account.type')
        objAcMoveLine = self.pool.get('account.move.line')
        objPartner = self.pool.get('res.partner')
        objCompany = self.pool.get('res.company')
        
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        bwCompany = objCompany.browse(cr,uid,company_id)

        Periodo = objPeriodo.browse(cr,uid,id_periodo)
        
        DataIn = datetime.strptime(Periodo.date_start,'%Y-%m-%d')
        DataOut = datetime.strptime(Periodo.date_stop,'%Y-%m-%d')
        #_logger.info('Data Inicio = {'+datetime.strftime(DataIn,'%Y-%m-%d')+'} Data Fim = {'+datetime.strftime(DataOut,'%Y-%m-%d')+'}')
        
        #sql = "delete from account_chart_flow_cash where period_id = %s" % str(id_periodo)
        sql = "delete from chart_dre_line"
        #_logger.info('Delete SQL = {'+sql+'}')
        cr.execute(sql)
         
        sql = "delete from chart_dre where id <> %s" % id_chart
        #_logger.info('Delete SQL = {'+sql+'}')
        cr.execute(sql)
        
        sql = "select id, code, name, parent_id, type, user_type from account_account "\
              " where code like '%s' and company_id = %s order by code" % ('3%',str(company_id))
        
        cr.execute(sql)

        for rcAccount in cr.fetchall():
            vlAcum = 0.0
            CtTipo = False

            ContaTipo = objContaTipo.browse(cr, uid, rcAccount[5], context).code

            if ContaTipo in ['view','income','expense']:
                if ContaTipo == 'income':
                    CtTipo = 'receita'
                elif ContaTipo == 'expense':
                    CtTipo = 'despesa'
                elif ContaTipo == 'view':
                    CtTipo = 'total'

                cdParentAccount = obj_account.browse(cr, uid, rcAccount[0], context).parent_id.code
                
                parentid = False
                if cdParentAccount:
                    shIds = obj_dre_line.search(cr, uid,[('code','=',cdParentAccount)])
                    if shIds:
                        parentid = shIds[0] 

                linha = {
                         'chart_id': id_chart, 
                         'account_id': rcAccount[0],
                         'code': rcAccount[1],
                         'name': rcAccount[2],
                         'period_id': id_periodo,
                         'parent_id': parentid,
                         'chart': CtTipo,
                         'type': 'synthetic',
                         'value': 0,
                         }
                
                line_id = obj_dre_line.create(cr,uid,linha,context)

        sql1 = "SELECT a.id, a.move_id FROM account_move_line a " + \
               "JOIN account_account b ON a.account_id = b.id " + \
               "WHERE CAST(a.date AS DATE) >= '%s'" % datetime.strftime(DataIn,'%Y-%m-%d') + \
               " and CAST(a.date AS DATE) <= '%s'" %  datetime.strftime(DataOut,'%Y-%m-%d') + \
               " and b.type = 'liquidity' order by a.date, a.id"

        _logger.info(sql1)
        cr.execute(sql1)
        for mvLiq in cr.fetchall():
            lancado = False
            _logger.info(str(mvLiq))

            sql2 = "select id, date, account_id, name, partner_id, credit, debit, reconcile_id, move_id from account_move_line " + \
                   "where move_id = %s " % str(mvLiq[1]) + \
                   " and id <> %s " % str(mvLiq[0]) + \
                   " order by date, id" 
            _logger.info(sql2)
            cr.execute(sql2)
            
            for mvCP in cr.fetchall():

                account = obj_account.browse(cr,uid,mvCP[2],context)

                if account.type == 'liquidity':
                    lancado = True
                else:

                    vlSaldo = float(mvCP[5])-float(mvCP[6])
    
                    descricao = '> Em '+str(mvCP[1])
                    
                    if mvCP[3]:
                        descricao = descricao + ', '+mvCP[3]
                    
                    Partner = objPartner.browse(cr,uid,mvCP[4],context)
                    if Partner:
                        descricao = descricao + ', parceiro '+Partner.name
    
                    descricao = descricao + ' ['+str(mvCP[0])+']'
        
                    sql3 = "select id, parent_id from chart_dre_line where chart_id = %s and " % id_chart + \
                           "account_id = '%s'" % mvCP[2]
                    cr.execute(sql3)
                    cl = cr.fetchone()
    
                    if cl:
                        lancado = False
                        lanca = {
                                  'chart_id': id_chart, 
                                  'account_id': False,
                                  'code': str(account.code)+'-%03d' % int(mvCP[0]),
                                  'name': descricao,
                                  'period_id': id_periodo,
                                  'parent_id': cl[0],
                                  'type': 'lancamento',
                                  'value': vlSaldo,
                                  }
                        _logger.info("Direto: "+str(lanca))
                        obj_dre_line.create(cr,uid,lanca,context)
                        lancado = True
                    else:
                        if mvCP[7]:
                            sql3 = "select account_id from account_move_line where move_id = (" + \
                                   "select b.move_id from account_move_line a " + \
                                   "join account_move_line b " + \
                                   "on a.reconcile_id = b.reconcile_id " + \
                                   "where a.id <> b.id and a.id = %s)" % mvCP[0]
                            _logger.info("SQL3: "+str(sql3))
                            cr.execute(sql3)
                            for y in cr.fetchall():
                                sql4 = "select id, parent_id from chart_dre_line where chart_id = %s and " % id_chart + \
                                       "account_id = '%s'" % y[0]
                                _logger.info("SQL4: "+str(sql4))
                                cr.execute(sql4)
                                cx = cr.fetchone()
                                if cx:
                                    account2 = obj_account.browse(cr,uid,y[0],context)
                                    lanca = {
                                             'chart_id': id_chart, 
                                             'account_id': False,
                                             'code': str(account2.code)+'-%03d' % int(mvCP[0]),
                                             'name': descricao,
                                             'period_id': id_periodo,
                                             'parent_id': cx[0],
                                             'type': 'lancamento',
                                             'value': vlSaldo,
                                             }
                                    _logger.info("Lanca Reconcile: "+str(lanca))
                                    obj_dre_line.create(cr,uid,lanca,context)
                                    lancado = True
                                    break
            if not lancado:
                account = obj_account.browse(cr,uid,mvCP[2],context)
                
                if vlSaldo > 0:
                    nw_account_id = bwCompany.account_revenue_id.id
                else:
                    nw_account_id = bwCompany.account_expense_id.id

                sql4 = "select id, parent_id from chart_dre_line where chart_id = %s and " % id_chart + \
                       "account_id = '%s'" % nw_account_id 
                _logger.info("SQL4: "+str(sql4))
               
                cr.execute(sql4)
                cx = cr.fetchone()
                if cx:
                    account2 = obj_account.browse(cr,uid,nw_account_id,context)
                    lanca = {
                             'chart_id': id_chart, 
                             'account_id': False,
                             'code': str(account2.code)+' -%03d' % int(mvCP[0]),
                             'name': '['+account.code + '] '+descricao,
                             'period_id': id_periodo,
                             'parent_id': cx[0],
                             'type': 'lancamento',
                             'value': vlSaldo,
                             }
                    obj_dre_line.create(cr,uid,lanca,context)
                else:
                    lanca = {
                             'chart_id': id_chart, 
                             'account_id': False,
                             'code': '9.' + str(account.code)+'-%03d' % int(mvCP[0]),
                             'name': descricao,
                             'period_id': id_periodo,
                             'parent_id': False,
                             'type': 'lancamento',
                             'value': vlSaldo,
                             }
                    obj_dre_line.create(cr,uid,lanca,context)
                
chart_dre()

class chart_dre_line(osv.osv):
    _name="chart_dre_line"
    _description= u"Linhas do DRE Extraído do fluxo de caixa"
    _order = "code,id"

    # override list in custom module to add/drop columns or change order
    def _report_xls_fields(self, cr, uid, context=None):
        return [
            'period', 'code', 'name', 'sum',
        ]

    # Change/Add Template entries
    def _report_xls_template(self, cr, uid, context=None):
        """
        Template updates, e.g.

        my_change = {
            'move':{
                'header': [1, 20, 'text', _('My Move Title')],
                'lines': [1, 0, 'text', _render("line.move_id.name or ''")],
                'totals': [1, 0, 'text', None]},
        }
        return my_change
        """
        return {}

    def _get_child_ids(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for rcLine in self.browse(cr, uid, ids, context=context):
            if rcLine.child_parent_ids:
                result[rcLine.id] = [x.id for x in rcLine.child_parent_ids]
            else:
                result[rcLine.id] = []
        return result

    def _sum_child(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        res = 0.0;
        for i in ids:
            Dreline = self.browse(cr, uid, i.id, context=context)
            if Dreline.type == 'synthetic':
                res = res + self._sum_child(cr, uid, Dreline.child_parent_ids, context)
            else:
                if Dreline.value:
                    res = res + float(Dreline.value)
        return res
                    
    def __compute(self, cr, uid, ids, field_names, arg=None, context=None):
        res = {} 
        for id in ids:
            chartdreline = self.browse(cr, uid, id, context=context)
            if chartdreline.type == 'analytic' or chartdreline.type == 'lancamento':
                res[id] = chartdreline.value
            else:
                res[id] = self._sum_child(cr, uid, chartdreline.child_parent_ids, context)
        return res

    _columns={
              'name': fields.char(u'Descrição', size=256, required=True, select=True),
              'code': fields.char(u'Código', size=64, required=True, select=1),
              'parent_id': fields.many2one('chart_dre_line', 'Parent', ondelete='cascade'),
              'period_id': fields.many2one('account.period', u'Período', required=True),
              'account_id': fields.many2one('account.account', 'Account'),
              'child_parent_ids': fields.one2many('chart_dre_line','parent_id','Children'),
              'child_id': fields.function(_get_child_ids, type='many2many', relation="chart_dre_line", string="Child Accounts"),
              'chart_id': fields.many2one('chart_dre', 'chart_flow_cash'),
              'type': fields.selection([
                    ('synthetic', u'Sintética'),
                    ('analytic', u'Analítica'),
                    ('other', 'Outra'),
                    ('lancamento', u'Lançamento')], 'Tipo'),
              'chart': fields.selection([
                    ('despesa', u'Despesa'),
                    ('receita', u'Receita'),
                    ('total', u'Totalização'),], u'Valorização'), 
              'value': fields.float(u'Valor', digits_compute=dp.get_precision('Account')),
              'sum': fields.function(__compute, type='float',), 
    }

    
chart_dre_line()
