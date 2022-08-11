# -*- coding: utf-8 -*-
import logging, traceback
from collections import Counter
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from uuid import uuid4

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import format_date, float_compare
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"
    
    
    #recurring_sale_order_line_ids = fields.One2many('sale.subscription.line', 'analytic_account_id', string='Subscription Lines', copy=True)
    subscription_partner_ids = fields.One2many('res.partner', 'subscription_id', string="Beneficiarios")
    policy_number = fields.Char('Número de Certificado')
    number = fields.Char(string='Número de Póliza')
    recurring_next_date = fields.Date(string='Date of Next Invoice', help="The next invoice will be created on this date then the period will be extended.")
    sponsor_id = fields.Many2one('res.partner')
    campo_vacio = fields.Boolean('Campo vacio', default=False) 
    policyholder = fields.Char('Tomador de Póliza')


    @api.model
    def create(self, vals):
        res = super(SaleSubscription, self).create(vals)
        if res.recurring_invoice_line_ids[0].product_id.product_tmpl_id.sequence_id:
            sequence_id = res.recurring_invoice_line_ids[0].product_id.product_tmpl_id.sequence_id
        else:
            sequence_id = res.recurring_invoice_line_ids[0].product_id.product_tmpl_id.categ_id.sequence_id
        if res.recurring_invoice_line_ids[0].product_id.product_tmpl_id.sequence_id.sponsor_name:
            policyholder = res.recurring_invoice_line_ids[0].product_id.product_tmpl_id.sequence_id.sponsor_name
        else:
            policyholder = res.recurring_invoice_line_ids[0].product_id.product_tmpl_id.categ_id.sequence_id.sponsor_name
        res.write({
            'policy_number': str(sequence_id.number_next_actual).zfill(10),
            'number': str(sequence_id.code),
            'recurring_next_date': date.today(),
            'sponsor_id': res.recurring_invoice_line_ids[0].product_id.categ_id.sponsor_id,
            'policyholder': str(policyholder),
        })
        sequence_id.write({
            'number_next_actual': int(sequence_id.number_next_actual) + 1,
        })
        
        '''
        order_line = self.env['sale.order.line'].search([('subscription_id','=',res.id)], limit=1)
        order = self.env['sale.order'].browse(order_line.id)
        order.write({
            'subscription_id': order.id,
        })
        '''
        
        return res
    
    
    def _prepare_invoice_data(self):
        res = super(SaleSubscription, self)._prepare_invoice_data()
        sale_order = self.env['sale.order'].search([('subscription_id', '=', self.id)])
        recurring_next_date = self._get_recurring_next_date(self.recurring_rule_type, self.recurring_interval, self.recurring_next_date, self.recurring_invoice_day)
        end_date = fields.Date.from_string(recurring_next_date) - relativedelta(days=1) 
        res.update({
            'amount_residual': sale_order.amount_total,
            'amount_residual_signed': sale_order.amount_total,
            'payment_method_type': sale_order.payment_method_type
        })
        if sale_order.payment_method_type == 'Product Without Price':
            res.update({
                'benefice_payment_method': sale_order.benefice_payment_method
            })
        else:
            if self.invoice_count == 0:
                res.update({
                    'payulatam_order_id': sale_order.payulatam_order_id,
                    'payulatam_transaction_id': sale_order.payulatam_transaction_id,
                    'payulatam_state': 'APPROVED',
                    'payulatam_datetime': sale_order.payulatam_datetime
                })
                if sale_order.payment_method_type == 'Credit Card':
                    res.update({
                        'payulatam_credit_card_token': sale_order.payulatam_credit_card_token,
                        'payulatam_credit_card_masked': sale_order.payulatam_credit_card_masked,
                        'payulatam_credit_card_identification': sale_order.payulatam_credit_card_identification,
                        'payulatam_credit_card_method': sale_order.payulatam_credit_card_method
                    })
            else:
                res.update({
                    'invoice_date': self.recurring_next_date + timedelta(days=4),
                    'narration': ('Esta factura cubre el siguiente periodo: %s - %s') % (format_date(self.env, self.recurring_next_date + timedelta(days=4)) , format_date(self.env, end_date))
                })
                if sale_order.payment_method_type == 'Credit Card' and sale_order.payulatam_credit_card_token != '':
                    res.update({
                        'payment_method_type': 'Credit Card',
                        'payulatam_credit_card_token': sale_order.payulatam_credit_card_token,
                        'payulatam_credit_card_masked': sale_order.payulatam_credit_card_masked,
                        'payulatam_credit_card_identification': sale_order.payulatam_credit_card_identification,
                        'payulatam_credit_card_method': sale_order.payulatam_credit_card_method
                    })
        if self.recurring_invoice_line_ids[0].product_id.categ_id.journal_id:
            journal = self.recurring_invoice_line_ids[0].product_id.categ_id.journal_id
        else:
            journal = self.template_id.journal_id or self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.company_id.id)], limit=1)
        res.update({
            'journal_id': journal.id,
            'sponsor_id': self.sponsor_id,
            'payment_mean_id': 1
        })
        return res

    def validate_and_send_invoice(self, invoice):
        self.ensure_one()
        if invoice.state != 'posted':
            invoice.post()

    def _cron_start_subscriptions(self):
        current_date = date.today()
        subscription_ids = self.env['sale.subscription'].search([('stage_id', '=', 1), ('date_start', '<=', current_date)])
        _logger.info(subscription_ids)
        for subscription in subscription_ids:
            sale_order = self.env['sale.order'].search([('subscription_id', '=', subscription.id)])
            subscription.stage_id = 2
            subscription.recurring_next_date = current_date
            sale_order._send_order_confirmation_mail()

    @api.onchange('date_start', 'template_id')
    def onchange_date_start(self):
        if self.date_start and self.recurring_rule_boundary == 'limited':
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            self.date = fields.Date.from_string(self.date_start) + relativedelta(**{
                periods[self.recurring_rule_type]: self.template_id.recurring_rule_count * self.template_id.recurring_interval}) - relativedelta(days=1)
        else:
            self.date = False

    def _recurring_create_invoice(self, automatic=False):
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        invoices = self.env['account.move']
        current_date = date.today()
        imd_res = self.env['ir.model.data']
        template_res = self.env['mail.template']
        if len(self) > 0:
            subscriptions = self
        else:
            domain = [('recurring_next_date', '<=', current_date),
                      ('template_id.payment_mode', '!=','manual'),
                      '|',('in_progress', '=', True),('to_renew', '=', True)]
            subscriptions = self.search(domain)
        if subscriptions:
            sub_data = subscriptions.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id'] for s in sub_data if s['company_id'][0] == company_id]
                subs = self.with_context(company_id=company_id, force_company=company_id).browse(sub_ids)
                context_invoice = dict(self.env.context, type='out_invoice', company_id=company_id, force_company=company_id)
                for subscription in subs:
                    subscription = subscription[0]  # Trick to not prefetch other subscriptions, as the cache is currently invalidated at each iteration
                    if subscription.invoice_count < subscription.template_id.recurring_rule_count:
                        if subscription.sponsor_id.generates_accounting:
                            if automatic and auto_commit:
                                cr.commit()

                            # if we reach the end date of the subscription then we close it and avoid to charge it
                            if automatic and subscription.date and subscription.date <= current_date:
                                subscription.set_close()
                                continue

                            # payment + invoice (only by cron)
                            if subscription.template_id.payment_mode in ['validate_send_payment', 'success_payment'] and subscription.recurring_total and automatic:
                                try:
                                    payment_token = subscription.payment_token_id
                                    tx = None
                                    if payment_token:
                                        invoice_values = subscription.with_context(lang=subscription.partner_id.lang)._prepare_invoice()
                                        new_invoice = self.env['account.move'].with_context(context_invoice).create(invoice_values)
                                        if subscription.analytic_account_id or subscription.tag_ids:
                                            for line in new_invoice.invoice_line_ids:
                                                if subscription.analytic_account_id:
                                                    line.analytic_account_id = subscription.analytic_account_id
                                                if subscription.tag_ids:
                                                    line.analytic_tag_ids = subscription.tag_ids
                                        new_invoice.message_post_with_view(
                                            'mail.message_origin_link',
                                            values={'self': new_invoice, 'origin': subscription},
                                            subtype_id=self.env.ref('mail.mt_note').id)
                                        tx = subscription._do_payment(payment_token, new_invoice, two_steps_sec=False)[0]
                                        # commit change as soon as we try the payment so we have a trace somewhere
                                        if auto_commit:
                                            cr.commit()
                                        if tx.renewal_allowed:
                                            msg_body = _('Automatic payment succeeded. Payment reference: <a href=# data-oe-model=payment.transaction data-oe-id=%d>%s</a>; Amount: %s. Invoice <a href=# data-oe-model=account.move data-oe-id=%d>View Invoice</a>.') % (tx.id, tx.reference, tx.amount, new_invoice.id)
                                            subscription.message_post(body=msg_body)
                                            if subscription.template_id.payment_mode == 'validate_send_payment':
                                                subscription.validate_and_send_invoice(new_invoice)
                                            else:
                                                # success_payment
                                                if new_invoice.state != 'posted':
                                                    new_invoice.post()
                                            subscription.send_success_mail(tx, new_invoice)
                                            if auto_commit:
                                                cr.commit()
                                        else:
                                            _logger.error('Fail to create recurring invoice for subscription %s', subscription.code)
                                            if auto_commit:
                                                cr.rollback()
                                            new_invoice.unlink()
                                    if tx is None or not tx.renewal_allowed:
                                        amount = subscription.recurring_total
                                        date_close = (
                                            subscription.recurring_next_date +
                                            relativedelta(days=subscription.template_id.auto_close_limit or
                                                          15)
                                        )
                                        close_subscription = current_date >= date_close
                                        email_context = self.env.context.copy()
                                        email_context.update({
                                            'payment_token': subscription.payment_token_id and subscription.payment_token_id.name,
                                            'renewed': False,
                                            'total_amount': amount,
                                            'email_to': subscription.partner_id.email,
                                            'code': subscription.code,
                                            'currency': subscription.pricelist_id.currency_id.name,
                                            'date_end': subscription.date,
                                            'date_close': date_close
                                        })
                                        if close_subscription:
                                            model, template_id = imd_res.get_object_reference('sale_subscription', 'email_payment_close')
                                            template = template_res.browse(template_id)
                                            template.with_context(email_context).send_mail(subscription.id)
                                            _logger.debug("Sending Subscription Closure Mail to %s for subscription %s and closing subscription", subscription.partner_id.email, subscription.id)
                                            msg_body = _('Automatic payment failed after multiple attempts. Subscription closed automatically.')
                                            subscription.message_post(body=msg_body)
                                            subscription.set_close()
                                        else:
                                            model, template_id = imd_res.get_object_reference('sale_subscription', 'email_payment_reminder')
                                            msg_body = _('Automatic payment failed. Subscription set to "To Renew".')
                                            if (datetime.date.today() - subscription.recurring_next_date).days in [0, 3, 7, 14]:
                                                template = template_res.browse(template_id)
                                                template.with_context(email_context).send_mail(subscription.id)
                                                _logger.debug("Sending Payment Failure Mail to %s for subscription %s and setting subscription to pending", subscription.partner_id.email, subscription.id)
                                                msg_body += _(' E-mail sent to customer.')
                                            subscription.message_post(body=msg_body)
                                            subscription.set_to_renew()
                                    if auto_commit:
                                        cr.commit()
                                except Exception:
                                    if auto_commit:
                                        cr.rollback()
                                    # we assume that the payment is run only once a day
                                    traceback_message = traceback.format_exc()
                                    _logger.error(traceback_message)
                                    last_tx = self.env['payment.transaction'].search([('reference', 'like', 'SUBSCRIPTION-%s-%s' % (subscription.id, datetime.date.today().strftime('%y%m%d')))], limit=1)
                                    error_message = "Error during renewal of subscription %s (%s)" % (subscription.code, 'Payment recorded: %s' % last_tx.reference if last_tx and last_tx.state == 'done' else 'No payment recorded.')
                                    _logger.error(error_message)

                            # invoice only
                            elif subscription.template_id.payment_mode in ['draft_invoice', 'manual', 'validate_send']:
                                try:
                                    invoice_values = subscription.with_context(lang=subscription.partner_id.lang)._prepare_invoice()
                                    new_invoice = self.env['account.move'].with_context(context_invoice).create(invoice_values)
                                    if subscription.analytic_account_id or subscription.tag_ids:
                                        for line in new_invoice.invoice_line_ids:
                                            if subscription.analytic_account_id:
                                                line.analytic_account_id = subscription.analytic_account_id
                                            if subscription.tag_ids:
                                                line.analytic_tag_ids = subscription.tag_ids
                                    new_invoice.message_post_with_view(
                                        'mail.message_origin_link',
                                        values={'self': new_invoice, 'origin': subscription},
                                        subtype_id=self.env.ref('mail.mt_note').id)
                                    invoices += new_invoice
                                    next_date = subscription.recurring_next_date + timedelta(days=4) or current_date
                                    rule, interval = subscription.recurring_rule_type, subscription.recurring_interval
                                    new_date = subscription._get_recurring_next_date(rule, interval, next_date, subscription.recurring_invoice_day)
                                    # Felipeeeee
                                    new_date = new_date - timedelta(days=4)
                                    # When `recurring_next_date` is updated by cron or by `Generate Invoice` action button,
                                    # write() will skip resetting `recurring_invoice_day` value based on this context value
                                    subscription.with_context(skip_update_recurring_invoice_day=True).write({'recurring_next_date': new_date})
                                    if subscription.template_id.payment_mode == 'validate_send':
                                        subscription.validate_and_send_invoice(new_invoice)
                                    if automatic and auto_commit:
                                        cr.commit()
                                except Exception:
                                    if automatic and auto_commit:
                                        cr.rollback()
                                        _logger.exception('Fail to create recurring invoice for subscription %s', subscription.code)
                                    else:
                                        raise
        return invoices

    def set_close(self, end_date=(datetime.now() - timedelta(hours=5)).date()):
        search = self.env['sale.subscription.stage'].search
        for sub in self:
            stage = search([('in_progress', '=', False), ('sequence', '>=', sub.stage_id.sequence)], limit=1)
            if not stage:
                stage = search([('in_progress', '=', False)], limit=1)
            sub.write({'stage_id': stage.id, 'to_renew': False, 'date': end_date})
        return True

class SaleSubscriptionCloseReasonWizard(models.TransientModel):
    _inherit = "sale.subscription.close.reason.wizard"
    
    end_date = fields.Date('Fecha cancelación', required=True)
    
    def set_close(self):
        self.ensure_one()
        subscription = self.env['sale.subscription'].browse(self.env.context.get('active_id'))
        order = self.env['sale.order'].search([('subscription_id', '=', subscription.id)], limit=1)
        subscription.close_reason_id = self.close_reason_id
        subscription.set_close(self.end_date)
        order.write({'state': 'done', 'cancel_date': self.end_date})
        deal_id = self.env['api.hubspot'].search_deal_id(subscription)
        if deal_id != False:
            deal_properties = {
                "estado_de_la_poliza": "Cancelado",
                "causal_de_cancelacion": subscription.close_reason_id.name,
                "fecha_efectiva_de_cancelacion": self.end_date
            }
            self.env['api.hubspot'].update_deal(deal_id, deal_properties)
            body_message = """
                <b><span style='color: darkblue;'>API HubSpot - Cancelación poliza</span></b><br/>
                <b>Estado:</b> %s<br/>
                <b>Causal de cancelación:</b> %s<br/>
                <b>Fecha efectiva de cancelación:</b> %s
            """ % (
                deal_properties['estado_de_la_poliza'],
                deal_properties['causal_de_cancelacion'],
                deal_properties['fecha_efectiva_de_cancelacion']
            )
            subscription.message_post(body=body_message, type="comment")
        else:
            body_message = """
                <b><span style='color: red;'>API HubSpot - Error buscar poliza</span></b><br/>
                <b>N° Poliza:</b> %s<br/>
                <b>N° Certificado:</b> %s
            """ % (
                subscription.number,
                subscription.policy_number
            )
            subscription.message_post(body=body_message, type="comment")