from openerp.osv import osv, fields

class res_company(osv.osv):

    _inherit = 'res.company'
    _columns = {
                'account_expense_id': fields.many2one('account.account', u'Conta Despesa Padrao',domain="[('type','=','other'),('user_type.code','=','expense')]"),
                'account_revenue_id': fields.many2one('account.account', u'Conta Receita Padrao',domain="[('type','=','other'),('user_type.code','=','income')]"),
                }

res_company()