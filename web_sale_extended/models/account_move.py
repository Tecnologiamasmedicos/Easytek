# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    sponsor_id = fields.Many2one('res.partner')
    campo_vacio = fields.Boolean('Campo vacio', default=False)  
    state =  fields.Selection(selection_add=[('finalized', 'Finalizado')], selection_remove=['payu_pending','payu_approved'])
        
    def post(self):
        res = super(AccountMove, self).post()
        if self.sponsor_id:
            if not self.sponsor_id.generates_accounting:
                self.write({
                    'state': 'finalized'
                })
        return res
    
    
    def _cron_payment_invoice(self):
        invoices_ids = self.env['account.move'].search([('amount_residual', '>', 0), ('type', '=', 'out_invoice'), ('state', '=', 'posted'), ('journal_id', '=', 14)])
        for invoice in invoices_ids:
            Payment = self.env['account.payment'].with_context(active_ids=invoice.ids, active_model='account.move', active_id=invoice.id)
            payments_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'company_id': 1,
                'amount': invoice.amount_residual,
                'payment_date': fields.Datetime.now(),
                'journal_id': 9,
                'payment_method_id': 1
            }
            payments = Payment.create(payments_vals)
            payments.post()