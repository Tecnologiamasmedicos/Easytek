# -*- coding: utf-8 -*-
import json
import logging, base64
from datetime import datetime
from datetime import date
from werkzeug.exceptions import Forbidden, NotFound
import werkzeug.utils
import werkzeug.wrappers
from odoo.exceptions import AccessError, MissingError
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.osv import expression
import requests
from requests.auth import HTTPBasicAuth
from hashlib import md5
from werkzeug import urls
import socket
hostname = socket.gethostname()

_logger = logging.getLogger(__name__)


class WebsiteSaleExtended(WebsiteSale):
    
    def checkout_redirection(self, order):
        """ sobreescribiendo método nativo """
        # must have a draft sales order with lines at this point, otherwise reset
        if not order or order.state != 'draft':
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.redirect('/shop')
        
        checkout_landpage_redirect = request.env.user.company_id.checkout_landpage_redirect
        if order and not order.order_line:
            #return request.redirect('/shop/cart')
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.redirect('/shop')

        # if transaction pending / done: redirect to confirmation
        tx = request.env.context.get('website_sale_transaction')
        if tx and tx.state != 'draft':
            return request.redirect('/shop/payment/confirmation/%s' % order.id)

    
    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        """ sobreescribiendo método nativo """
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False

        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')
        
        """ PayU Latam Api """
        endpoint = 'PING' # connect status
        ping_response = request.env['api.payulatam'].payulatam_ping()
        credit_card_methods = []
        bank_list = []
        if ping_response['code'] == 'SUCCESS':
            # get payment methods
            credit_card_methods = request.env['api.payulatam'].payulatam_get_credit_cards_methods()
            bank_list_pse = request.env['api.payulatam'].payulatam_get_bank_list()
            #cash_list = request.env['api.payulatam'].payulatam_get_cash_method_list()
        
        #_logger.error(bank_list)
        
        mode = (False, False)
        country = request.env['res.country'].browse(49)
        current_year = int(date.today().year)
        credit_card_due_year_ids = list(range(current_year, current_year + 40))
        render_values.update({
            'error' : [],
            'mode' : mode,
            'cities' : [],
            'country': request.env['res.country'].browse(int(49)),
            'country_states' : country.get_website_sale_states(mode=mode[1]),
            'countries': country.get_website_sale_countries(mode=mode[1]),
            'credit_card_due_year_ids': credit_card_due_year_ids,
            'credit_card_methods': credit_card_methods,
            'bank_list': bank_list_pse
        })
        return request.render("web_sale_extended.web_sale_extended_payment_process", render_values)
    
    @http.route(['/shop/payment/payulatam-gateway-api/response'], type='http', auth="public", website=True, sitemap=False)
    def payment_payulatam_gateway_api_response(self, **kwargs):
        _logger.error('**********************545+++++++++++++++++++++++++++++++++++++')
        _logger.error(kwargs)
        order = request.website.sale_get_order()
        if not order and kwargs['transactionId']:
            order = request.env['sale.order'].sudo().search([('payulatam_transaction_id', '=', kwargs['transactionId'])])
        if not order:
            redirection = self.checkout_redirection(order)
            if redirection:
                return redirection

        
        #request.session['sale_order_id'] = None
        #request.session['sale_transaction_id'] = None
        domain = [('payulatam_transaction_id', '=', kwargs['transactionId'])]
        lapTransactionState = kwargs['lapTransactionState']
        lapResponseCode = kwargs['lapResponseCode']
        lapResponseCode = kwargs['lapResponseCode']
        payulatam_transaction_id = request.env['sale.order'].sudo().search(domain, limit=1)
        if payulatam_transaction_id:
            if lapTransactionState == 'APPROVED':
                payulatam_transaction_id.write({
                    'payulatam_state': 'TRANSACCIÓN APROBADA',
                    'state': 'payu_approved'
                })
                query = """
                    INSERT INTO payments_report (
                        policy_number,
                        certificate_number, 
                        firstname,
                        othernames, 
                        lastname, 
                        identification_document, 
                        birthday_date,
                        transaction_type, 
                        clase,
                        change_date, 
                        collected_value,
                        number_of_installments,
                        payment_method,
                        number_of_plan_installments,
                        total_installments,
                        number_of_installments_arrears,
                        policyholder,
                        sponsor_id,
                        product_code,
                        product_name,
                        payulatam_order_id,
                        payulatam_transaction_id,
                        origin_document,
                        sale_order,
                        subscription,
                        payment_type
                    )
                    SELECT '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s, '%s', %s, %s, %s, '%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s' WHERE NOT EXISTS(SELECT * FROM payments_report WHERE payulatam_order_id='%s');
                """ %(
                    order.subscription_id.number if order.subscription_id.number != False else '',
                    order.subscription_id.policy_number if order.subscription_id.policy_number != False else '',
                    order.partner_id.firstname if order.partner_id.firstname != False else '', 
                    order.partner_id.othernames, 
                    str(order.partner_id.lastname) + ' ' + str(order.partner_id.lastname2) if order.partner_id.lastname != False else '', 
                    order.partner_id.identification_document if order.partner_id.identification_document != False else '', 
                    order.partner_id.birthdate_date if order.partner_id.birthdate_date != False else '', 
                    'R', 
                    order.main_product_id.product_class if order.main_product_id.product_class != False else '', 
                    date.today(), 
                    order.amount_total if order.amount_total != False else '', 
                    1, 
                    order.payment_method_type if order.payment_method_type != False else '', 
                    order.main_product_id.subscription_template_id.recurring_rule_count if order.main_product_id.subscription_template_id.recurring_rule_count  != False else '', 
                    1, 
                    0, 
                    order.subscription_id.policyholder if order.subscription_id.policyholder != False else '', 
                    order.sponsor_id.id if order.sponsor_id.id != False else 'null', 
                    order.main_product_id.default_code if order.main_product_id.default_code != False else '', 
                    order.main_product_id.name if order.main_product_id.name != False else '', 
                    order.payulatam_order_id if order.payulatam_order_id != False else '', 
                    order.payulatam_transaction_id if order.payulatam_transaction_id != False else '', 
                    order.name if order.name != False else '', 
                    order.id if order.id != False else 'null',
                    order.subscription_id.id if order.subscription_id.id  != False else 'null',
                    'new_sale',
                    order.payulatam_order_id if order.payulatam_order_id != False else ''
                )
                order.env.cr.execute(query)
                if request.session['sale_order_id'] and order == payulatam_transaction_id:
                    """ En este caso el usuario puede continuar directamente la transacción """
                    render_values = {}
                    render_values.update({
                        'website_sale_order': order,
                        'order_id': order,
                        'response': dict(kwargs),
                        'order_detail': order.order_line[0],
                        'access_token': str(request.env['sale.order'].generate_access_token(order.id))
                    })
                    """ Mensaje en la orden de venta con la respuesta de PayU """
                    body_message = """
                        <b><span style='color:green;'>PayU Latam - Transacción de Pago Aprobada</span></b><br/>
                        <b>Orden ID:</b> %s<br/>
                        <b>Transacción ID:</b> %s<br/>
                        <b>Estado:</b> %s<br/>
                        <b>Código Respuesta:</b> %s<br/>
                    """ % (
                        kwargs['reference_pol'], 
                        kwargs['transactionId'],
                        kwargs['lapTransactionState'],
                        kwargs['lapResponseCode'],
                    )
                    payulatam_transaction_id.message_post(body=body_message, type="comment")
                    return request.render("web_sale_extended.web_sale_extended_payment_response_process", render_values)
                else:
                    """ En caso contrario se envía correo con la información para seguir """
                    render_values = {}
                    render_values.update({
                        'website_sale_order': order,
                        'order_id': order,
                        'response': dict(kwargs),
                    })
                    template = request.env['mail.template'].sudo().search([('payulatam_approved_process', '=', True)], limit=1)
                    context = dict(request.env.context)
                    if template:
                        _logger.error('*************+******+++++++++++***+*')
                        _logger.error(template)
                        _logger.error(payulatam_transaction_id.id)
                        #template.sudo().send_mail(payulatam_transaction_id.id)
                        payulatam_transaction_id._send_order_payu_latam_approved()
                        """
                        template_values = template.generate_email(payulatam_transaction_id.id, fields=None)
                        template_values.update({
                            #'email_to': sale_id.tusdatos_email,
                            'email_to': payulatam_transaction_id.partner_id.email,
                            'auto_delete': False,
                            #'partner_to': False,
                            'scheduled_date': False,
                        })
                        template.write(template_values)
                        cleaned_ctx = dict(request.env.context)
                        cleaned_ctx.pop('default_type', None)
                        template.with_context(lang=request.env.user.lang).send_mail(payulatam_transaction_id.id, force_send=True, raise_exception=True)
                        """

                        """ Mensaje en la orden de venta con la respuesta de PayU """
                        body_message = """
                            <b><span style='color:green;'>PayU Latam - Transacción de Pago Aprobada</span></b><br/>
                            <b>Orden ID:</b> %s<br/>
                            <b>Transacción ID:</b> %s<br/>
                            <b>Estado:</b> %s<br/>
                            <b>Código Respuesta:</b> %s<br/>
                        """ % (
                            kwargs['reference_pol'], 
                            kwargs['transactionId'],
                            kwargs['lapTransactionState'],
                            kwargs['lapResponseCode'],
                        )
                        payulatam_transaction_id.message_post(body=body_message, type="comment")
                        return request.render("web_sale_extended.web_sale_extended_payment_response_process", render_values)
                #request.session['sale_order_id'] = None
                #request.session['sale_transaction_id'] = None
            else:
                render_values = {}
                render_values.update({
                    'website_sale_order': order,
                    'order_id': order,
                    'response': dict(kwargs),
                })
                payulatam_transaction_id.write({
                    'payulatam_state': 'TRANSACCIÓN DECLINADA',
                })
                payulatam_transaction_id.action_cancel()
                request.session['sale_order_id'] = None
                request.session['sale_transaction_id'] = None
                body_message = """
                    <b><span style='color:red;'>PayU Latam - Transacción de Pago PSE RECHAZADA</span></b><br/>
                    <b>Orden ID:</b> %s<br/>
                    <b>Transacción ID:</b> %s<br/>
                    <b>Estado:</b> %s<br/>
                    <b>Código Respuesta:</b> %s<br/>
                """ % (
                    kwargs['reference_pol'], 
                    kwargs['transactionId'],
                    kwargs['lapTransactionState'],
                    kwargs['lapResponseCode'],
                )
                payulatam_transaction_id.message_post(body=body_message, type="comment")
                return request.render("web_sale_extended.payulatam_rejected_process_pse", render_values)
            
    @http.route(['/shop/payment/payulatam-gateway-api/response_recurring'], type='http', auth="public", website=True, sitemap=False)
    def payment_payulatam_gateway_api_response_recurring(self, **kwargs):
        origin_document = request.env['sale.order'].sudo().search([('payulatam_transaction_id', '=', kwargs['transactionId'])]) or request.env['account.move'].sudo().search([('payulatam_transaction_id', '=', kwargs['transactionId'])])
        if str(origin_document).split('(')[0] == 'account.move':
            subscription = request.env['sale.subscription'].sudo().search([('code', '=', origin_document.invoice_origin)])
            product = origin_document.invoice_line_ids[0].product_id
            sale_order = request.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
            
        elif str(origin_document).split('(')[0] == 'sale.order':
            subscription = origin_document.subscription_id
            product = origin_document.main_product_id
            sale_order = origin_document.id
        
        if not origin_document:
            redirection = self.checkout_redirection(origin_document)
            if redirection:
                return redirection
            
        amount = float(kwargs['TX_VALUE'])
        
        if kwargs['lapTransactionState'] == 'APPROVED':
            sale_order.write({
                'payment_method_type': origin_document.payment_method_type,
            })
            origin_document.write({
                'payulatam_state': kwargs['lapTransactionState'],
                'payulatam_datetime': fields.datetime.now(),
            })
            render_values = {
                'website_sale_order': sale_order,
                'error': '',
                'amount': amount,
                'image': '/web/image/1109/Img_success%282%29.png?access_token=a79d70ef-5174-4077-b854-a03eff98c0be',
                'responseMessage': 'Proceso de pago Aprobado',
                'colorResponseMessage': '#39b54a',
                'url': 'https://masmedicos.co',
                'messageButton': 'Gracias por tu pago',
                'messagePayment' : 'Pago Realizado'
            }
            """ Mensaje en la orden de venta con la respuesta de PayU """
            body_message = """
                <b><span style='color:green;'>PayU Latam - Transacción de Pago Aprobada</span></b><br/>
                <b>Orden ID:</b> %s<br/>
                <b>Transacción ID:</b> %s<br/>
                <b>Estado:</b> %s<br/>
                <b>Código Respuesta:</b> %s<br/>
            """ % (
                kwargs['reference_pol'], 
                kwargs['transactionId'],
                kwargs['lapTransactionState'],
                kwargs['lapResponseCode'],
            )
            query = """
                INSERT INTO payments_report (
                    policy_number,
                    certificate_number, 
                    firstname,
                    othernames, 
                    lastname, 
                    identification_document, 
                    birthday_date,
                    transaction_type, 
                    clase,
                    change_date, 
                    collected_value,
                    number_of_installments,
                    payment_method,
                    number_of_plan_installments,
                    total_installments,
                    number_of_installments_arrears,
                    policyholder,
                    sponsor_id,
                    product_code,
                    product_name,
                    payulatam_order_id,
                    payulatam_transaction_id,
                    origin_document,
                    sale_order,
                    subscription,
                    payment_type
                )
                SELECT '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s, '%s', %s, %s, %s, '%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s' WHERE NOT EXISTS(SELECT * FROM payments_report WHERE payulatam_order_id='%s');
            """ %(
                subscription.number if subscription.number != False else '',
                subscription.policy_number if subscription.policy_number != False else '',
                origin_document.partner_id.firstname if origin_document.partner_id.firstname != False else '', 
                origin_document.partner_id.othernames, 
                str(origin_document.partner_id.lastname) + ' ' + str(origin_document.partner_id.lastname2) if origin_document.partner_id.lastname != False else '', 
                origin_document.partner_id.identification_document if origin_document.partner_id.identification_document != False else '', 
                origin_document.partner_id.birthdate_date if origin_document.partner_id.birthdate_date != False else '', 
                'R', 
                product.product_class if product.product_class != False else '', 
                date.today(), 
                origin_document.amount_total if origin_document.amount_total != False else '', 
                1, 
                origin_document.payment_method_type if origin_document.payment_method_type != False else '', 
                product.subscription_template_id.recurring_rule_count if product.subscription_template_id.recurring_rule_count  != False else '', 
                int(request.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                int(request.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id)])) - int(request.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                subscription.policyholder if subscription.policyholder != False else '', 
                origin_document.sponsor_id.id if origin_document.sponsor_id.id != False else 'null', 
                product.default_code if product.default_code != False else '', 
                product.name if product.name != False else '', 
                origin_document.payulatam_order_id if origin_document.payulatam_order_id != False else '', 
                origin_document.payulatam_transaction_id if origin_document.payulatam_transaction_id != False else '', 
                origin_document.name if origin_document.name != False else '', 
                sale_order.id if sale_order.id != False else 'null',
                subscription.id if subscription.id  != False else 'null',
                'recurring_payment',
                origin_document.payulatam_order_id if origin_document.payulatam_order_id != False else ''
            )
            origin_document.env.cr.execute(query)
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        else:
            origin_document.write({
                'payulatam_state': kwargs['lapTransactionState'],
                'payulatam_datetime': fields.datetime.now(),
            })
            render_values = {
                'website_sale_order': sale_order,
                'error': '',
                'amount': amount,
                'image': '/web_sale_extended/static/src/images/Img_warning.png',
                'responseMessage': 'Proceso de pago' + str(kwargs['lapTransactionState']),
                'colorResponseMessage': '#FF7800'
            }
            return request.render("web_sale_extended.payu_transaction_response", render_values)