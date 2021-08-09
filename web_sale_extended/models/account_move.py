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
        
    # def post(self):
    #     # `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
    #     if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
    #         raise AccessError(_("You don't have the access rights to post an invoice."))
    #     for move in self:
    #         if move.state == 'posted':
    #             raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
    #         if not move.line_ids.filtered(lambda line: not line.display_type):
    #             raise UserError(_('You need to add a line before posting.'))
    #         if move.auto_post and move.date > fields.Date.today():
    #             date_msg = move.date.strftime(get_lang(self.env).date_format)
    #             raise UserError(_("This move is configured to be auto-posted on %s" % date_msg))

    #         if not move.partner_id:
    #             if move.is_sale_document():
    #                 raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
    #             elif move.is_purchase_document():
    #                 raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

    #         if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
    #             raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

    #         # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
    #         # lines are recomputed accordingly.
    #         # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
    #         # environment.
    #         if not move.invoice_date and move.is_invoice(include_receipts=True):
    #             move.invoice_date = fields.Date.context_today(self)
    #             move.with_context(check_move_validity=False)._onchange_invoice_date()

    #         # When the accounting date is prior to the tax lock date, move it automatically to the next available date.
    #         # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
    #         # environment.
    #         if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tag_ids):
    #             move.date = move.company_id.tax_lock_date + timedelta(days=1)
    #             move.with_context(check_move_validity=False)._onchange_currency()

    #     # Create the analytic lines in batch is faster as it leads to less cache invalidation.
    #     self.mapped('line_ids').create_analytic_lines()
    #     for move in self.sorted(lambda m: (m.date, m.ref or '', m.id)):
    #         if move.auto_post and move.date > fields.Date.today():
    #             raise UserError(_("This move is configured to be auto-posted on {}".format(move.date.strftime(get_lang(self.env).date_format))))

    #         move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])
            
    #         if move.sponsor_id:
    #             if not move.sponsor_id.generates_accounting:
    #                 to_write = {'state': 'finalized'}
    #             else:
    #                 to_write = {'state': 'posted'}
    #         else:
    #             to_write = {'state': 'posted'}

    #         if move.name == '/':
    #             # Get the journal's sequence.
    #             sequence = move._get_sequence()
    #             if not sequence:
    #                 raise UserError(_('Please define a sequence on your journal.'))

    #             # Consume a new number.
    #             to_write['name'] = sequence.with_context(ir_sequence_date=move.date).next_by_id()

    #         move.write(to_write)

    #         # Compute 'ref' for 'out_invoice'.
    #         if move.type == 'out_invoice' and not move.invoice_payment_ref:
    #             to_write = {
    #                 'invoice_payment_ref': move._get_invoice_computed_reference(),
    #                 'line_ids': []
    #             }
    #             for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
    #                 to_write['line_ids'].append((1, line.id, {'name': to_write['invoice_payment_ref']}))
    #             move.write(to_write)

    #         if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
    #             # For opening moves, we set the reconciliation date threshold
    #             # to the move's date if it wasn't already set (we don't want
    #             # to have to reconcile all the older payments -made before
    #             # installing Accounting- with bank statements)
    #             move.company_id.account_bank_reconciliation_start = move.date

    #     for move in self:
    #         if not move.partner_id: continue
    #         partners = (move.partner_id | move.partner_id.commercial_partner_id)
    #         if move.type.startswith('out_'):
    #             partners._increase_rank('customer_rank')
    #         elif move.type.startswith('in_'):
    #             partners._increase_rank('supplier_rank')
    #         else:
    #             continue

    #     # Trigger action for paid invoices in amount is zero
    #     self.filtered(
    #         lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
    #     ).action_invoice_paid()

    #     # Force balance check since nothing prevents another module to create an incorrect entry.
    #     # This is performed at the very end to avoid flushing fields before the whole processing.
    #     self._check_balanced()
    #     return True
    
    
    def _cron_payment_invoice(self):
        invoices_ids = self.env['account.move'].search([('amount_residual', '>', 0), ('type', '=', 'out_invoice'), ('state', '=', 'posted')])
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