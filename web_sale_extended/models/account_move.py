# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from odoo.http import request
from datetime import datetime, date, timedelta 
from dateutil.relativedelta import relativedelta
from werkzeug import urls
import time, json

import logging, hashlib, hmac
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    sponsor_id = fields.Many2one('res.partner')
    campo_vacio = fields.Boolean('Campo vacio', default=False)  
    state =  fields.Selection(selection_add=[('finalized', 'Finalizado')], selection_remove=['payu_pending','payu_approved'])

    payulatam_order_id = fields.Char('ID de Orden de PayU')
    payulatam_transaction_id = fields.Char('ID de Transacción de PayU')
    payulatam_state = fields.Selection([
        ("APPROVED", "APROBADO"), 
        ("PENDING", "PENDIENTE"), 
        ("EXPIRED", "EXPIRADO"),
        ("DECLINED", "DECLINADO"),
        ("without_payment", "SIN COBRO"),
        ("no_payment", "NO PAGO"),
        ("Cancel", "CANCELADO"),
    ])
    payulatam_datetime = fields.Datetime('Fecha y Hora de la Transacción')
    payulatam_credit_card_token = fields.Char('Token Para Tarjetas de Crédito')
    payulatam_credit_card_masked = fields.Char('Mascara del Número de Tarjeta')
    payulatam_credit_card_identification = fields.Char('Identificación')
    payulatam_credit_card_method = fields.Char('Metodo de Pago')
    payulatam_request_expired = fields.Boolean('Request Expired')
    payment_method_type = fields.Selection([
        ("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),
        ("Product Without Price", "Beneficio"),
    ])

    benefice_payment_method = fields.Selection([
        ("payroll_discount", "Descuento de nómina"),
        ("window_payment", "Pago por ventanilla"),
        ("libranza_discount", "Descuento por libranza"),
    ])
    send_payment = fields.Boolean('Cobro realizado', default=False)
    action_date_billing_cycle = fields.Date(string='Fecha accion ciclo de cobro')
    hubspot_payment_action = fields.Selection([
        ("5_days_before", "5 dias antes"),
        ("1_day_before", "1 dia antes"),
        ("1_days_after", "1 dia despues"),
        ("10_days_after", "10 dias despues"),
        ("20_days_after", "20 dias despues"),
        ("25_days_after", "PC 25 dias despues"),
        ("36_days_after", "C 36 dias despues"),
    ])
    number_payments_sent = fields.Integer('Número de pagos enviados', store=True, default=0)
    msg_payment_reminder = fields.Boolean('Mensaje recordación de cobro', default=False)

    def post(self):
        res = super(AccountMove, self).post()
        if self.sponsor_id:
            self.write({
                'amount_residual': self.amount_total,
                'amount_residual_signed': self.amount_total_signed,
                'invoice_payment_state': 'not_paid',
                'state': 'finalized'
            })
        return res

    def generate_access_token(self, invoice_id):   
        invoice = self.env['account.move'].sudo().browse(invoice_id)
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        token_str = '%s%s%s' % (invoice.partner_id.id, invoice.amount_total, invoice.currency_id.id)
        access_token = hmac.new(secret.encode('utf-8'), token_str.encode('utf-8'), hashlib.sha256).hexdigest()
        return access_token
    
    def generate_link(self, invoice_id):
        token = self.generate_access_token(invoice_id)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = ('%s/website_payment/pay?reference=%s&amount=%s&currency_id=%s&partner_id=%s&invoice_id=%s&access_token=%s') % (
            base_url,
            urls.url_quote_plus(self.name),
            self.amount_total,
            self.currency_id.id,
            self.partner_id.id,
            invoice_id,
            token
        )        
        return link
    
    def send_recurring_payment_credit_card(self):
        template_id = self.env.ref('web_sale_extended.mail_template_recurring_payment_credit_card').id
        template = self.env['mail.template'].browse(template_id)
        template.sudo().send_mail(self.id, force_send=True)
        self.send_payment = True
        
    def send_recurring_payment_pse_cash(self):
        template_id = self.env.ref('web_sale_extended.mail_template_recurring_payment_pse_cash').id
        template = self.env['mail.template'].browse(template_id)
        template.sudo().send_mail(self.id, force_send=True)
        self.send_payment = True

    def send_mail_second_payment(self):
        template_id = self.env.ref('web_sale_extended.mail_template_cancellation_plan').id
        template = self.env['mail.template'].browse(template_id)
        template.sudo().send_mail(self.id, force_send=True)
        self.send_payment = True
    
    def payment_credit_card_by_tokenization(self):
        subscription = self.env['sale.subscription'].sudo().search([('code', '=', self.invoice_origin)])
        if self.payment_method_type == 'Credit Card' and self.payulatam_credit_card_token != '' and self.payulatam_state not in ("APPROVED", "PENDING") and subscription.stage_id not in (4, 5):
            sale_order = request.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
            """ Proceso de Pago """
            referenceCode = str(self.env['api.payulatam'].payulatam_get_sequence())
            accountId = self.env['api.payulatam'].payulatam_get_accountId()
            descriptionPay = "Payment Origin from " + self.name
            signature = self.env['api.payulatam'].payulatam_get_signature(
                self.amount_total,'COP',referenceCode)

            payulatam_api_env = self.env.user.company_id.payulatam_api_env

            if payulatam_api_env == 'prod':
                if sale_order.website_id.domain:
                    payulatam_response_url = "https://" + str(sale_order.website_id.domain) + str(self.env.user.company_id.payulatam_api_response_url)
                else:
                    payulatam_response_url = str(request.env['ir.config_parameter'].sudo().get_param('web.base.url')) + str(self.env.user.company_id.payulatam_api_response_url)
            else:
                if sale_order.website_id.domain:
                    payulatam_response_url = "https://" + str(sale_order.website_id.domain) + str(self.env.user.company_id.payulatam_api_response_sandbox_url)
                else:
                    payulatam_response_url = str(request.env['ir.config_parameter'].sudo().get_param('web.base.url')) + str(self.env.user.company_id.payulatam_api_response_sandbox_url)

            tx_value = {"value": self.amount_total, "currency": "COP"}        
            tx_tax = {"value": 0,"currency": "COP"}
            tx_tax_return_base = {"value": 0, "currency": "COP"}        
            additionalValues = {
                "TX_VALUE": tx_value,
                "TX_TAX": tx_tax,
                "TX_TAX_RETURN_BASE": tx_tax_return_base
            }  
            shippingAddress = {
                "street1": self.partner_id.street,
                "street2": "",
                "city": self.partner_id.zip_id.city_id.name,
                "state": self.partner_id.zip_id.city_id.state_id.name,
                "country": "CO",
                "postalCode": self.partner_id.zip_id.name,
                "phone": self.partner_id.phone
            }    
            buyer = {
                "merchantBuyerId": str(self.partner_id.id),
                "fullName": self.partner_id.name,
                "emailAddress": self.partner_id.email,
                "contactPhone": self.partner_id.phone,
                "dniNumber": self.partner_id.identification_document,
                "shippingAddress": shippingAddress
            }    
            order_api = {
                "accountId": accountId,
                "referenceCode": referenceCode,
                "description": 'PPS - ' + descriptionPay,
                "language": "es",
                "signature": signature,
                "notifyUrl":payulatam_response_url,
                "additionalValues": additionalValues,
                "buyer": buyer,
                "shippingAddress": shippingAddress
            }
            billingAddressPayer = {
                "street1": self.partner_id.street,
                "street2": "",
                "city": self.partner_id.zip_id.city_id.name,
                "state": self.partner_id.zip_id.city_id.state_id.name,
                "country": "CO",
                "postalCode": self.partner_id.zip_id.name,
                "phone": self.partner_id.phone
            }    
            payer = {
                "fullName": self.partner_id.name,
                "emailAddress": self.partner_id.email,
                "contactPhone": self.partner_id.phone,
                "dniNumber": self.partner_id.identification_document,
                "billingAddress": billingAddressPayer
            }
            creditCard = {
                "processWithoutCvv2": "true"
            }
            extraParameters = {
                "INSTALLMENTS_NUMBER": 1
            }
            transaction = {
                "order": order_api,
                "payer": payer,
                "creditCardTokenId": self.payulatam_credit_card_token,
                "creditCard": creditCard,
                "extraParameters": extraParameters,
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": self.payulatam_credit_card_method,
                "paymentCountry": "CO",
                "deviceSessionId": "vghs6tvkcle931686k1900o6e1",
                "ipAddress": "127.0.0.1",
                "cookie": "pt1t38347bs6jc9ruv2ecpv7o2",
                "userAgent": "Firefox"
            }        
            credit_card_values = {
                "command": "SUBMIT_TRANSACTION",
                "transaction": transaction,
            }
            response = self.env['api.payulatam'].payulatam_credit_cards_payment_request(credit_card_values)
            if response['code'] != 'SUCCESS':
                body_message = """
                    <b><span style='color:red;'>PayU Latam - Error en pago con tarjeta de crédito</span></b><br/>
                    <b>Código:</b> %s<br/>
                    <b>Error:</b> %s
                """ % (
                    response['code'],
                    response['error'], 
                )
                self.message_post(body=body_message, type="comment")
                mail_values = {
                    'subject': 'Error cobro liquidación %s'%(self.name),
                    'body_html' : 'Se presento un error en el cobro de la liquidación %s<br/><br/><b>Cliente: </b> %s <span style="color: red;">error:</span> %s<br/><br/>Se envio correo con link de pago. '%(self.name, self.partner_id.name ,response['error']),
                    'email_to': 'dv1@masmedicos.co',
                    # 'email_to': 'analistaprocesos@masmedicos.co, analistaux@masmedicos.co',
                    'email_from': 'contacto@masmedicos.co'
                }
                self.env['mail.mail'].sudo().create(mail_values).send()
                self.send_recurring_payment_pse_cash()
            else:
                if response['transactionResponse']['state'] == 'APPROVED':
                    product = self.invoice_line_ids[0].product_id
                    sale_order = self.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
                    self.write({
                        'payulatam_order_id': response['transactionResponse']['orderId'],
                        'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                        'payulatam_state': response['transactionResponse']['state'],
                        'payment_method_type': 'Credit Card',
                        'payulatam_datetime': fields.datetime.now(),
                    })
                    body_message = """
                        <b><span style='color:green;'>PayU Latam - Transacción de pago con tarjeta de crédito</span></b><br/>
                        <b>Orden ID:</b> %s<br/>
                        <b>Transacción ID:</b> %s<br/>
                        <b>Estado:</b> %s<br/>
                        <b>Código Respuesta:</b> %s
                    """ % (
                        response['transactionResponse']['orderId'], 
                        response['transactionResponse']['transactionId'], 
                        'APROBADO', 
                        response['transactionResponse']['responseCode']
                    )
                    self.message_post(body=body_message, type="comment")
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
                        sale_order.beneficiary0_id.firstname if sale_order.beneficiary0_id.firstname != False else '', 
                        sale_order.beneficiary0_id.othernames if sale_order.beneficiary0_id.othernames != False else '',
                        (str(sale_order.beneficiary0_id.lastname) + ' ' + str(sale_order.beneficiary0_id.lastname2))[:20] if sale_order.beneficiary0_id.lastname != False else '', 
                        sale_order.beneficiary0_id.identification_document if sale_order.beneficiary0_id.identification_document != False else '', 
                        sale_order.beneficiary0_id.birthdate_date if sale_order.beneficiary0_id.birthdate_date != False else '',
                        'R', 
                        product.product_class if product.product_class != False else '', 
                        date.today(), 
                        self.amount_total if self.amount_total != False else '', 
                        1, 
                        self.payment_method_type if self.payment_method_type != False else '', 
                        product.subscription_template_id.recurring_rule_count if product.subscription_template_id.recurring_rule_count  != False else '', 
                        int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                        int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id)])) - int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                        subscription.policyholder if subscription.policyholder != False else '', 
                        self.sponsor_id.id if self.sponsor_id.id != False else 'null', 
                        product.default_code if product.default_code != False else '', 
                        product.name if product.name != False else '', 
                        self.payulatam_order_id if self.payulatam_order_id != False else '', 
                        self.payulatam_transaction_id if self.payulatam_transaction_id != False else '', 
                        self.name if self.name != False else '', 
                        sale_order.id if sale_order.id != False else 'null',
                        subscription.id if subscription.id  != False else 'null',
                        'recurring_payment',
                        self.payulatam_order_id if self.payulatam_order_id != False else ''
                    )
                    self.env.cr.execute(query)
                elif response['transactionResponse']['state'] == 'PENDING':
                    self.write({
                        'payulatam_order_id': response['transactionResponse']['orderId'],
                        'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                        'payulatam_state': response['transactionResponse']['state'],
                        'payment_method_type': 'Credit Card',
                        'payulatam_datetime': fields.datetime.now(),
                    })
                    body_message = """
                        <b><span style='color:orange;'>PayU Latam - Transacción de pago con tarjeta de crédito</span></b><br/>
                        <b>Orden ID:</b> %s<br/>
                        <b>Transacción ID:</b> %s<br/>
                        <b>Estado:</b> %s<br/>
                        <b>Código Respuesta:</b> %s
                    """ % (
                        response['transactionResponse']['orderId'], 
                        response['transactionResponse']['transactionId'], 
                        'PENDIENTE DE APROBACIÓN', 
                        response['transactionResponse']['responseCode']
                    )
                    self.message_post(body=body_message, type="comment")
                elif response['transactionResponse']['state'] in ['EXPIRED', 'DECLINED']:
                    self.write({
                        'payulatam_order_id': response['transactionResponse']['orderId'],
                        'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                        'payulatam_state': response['transactionResponse']['state'],
                        'payment_method_type': 'Credit Card',
                        'payulatam_datetime': fields.datetime.now(),
                    })
                    body_message = """
                        <b><span style='color:red;'>PayU Latam - Transacción de pago con tarjeta de crédito</span></b><br/>
                        <b>Orden ID:</b> %s<br/>
                        <b>Transacción ID:</b> %s<br/>
                        <b>Estado:</b> %s<br/>
                        <b>Código Respuesta:</b> %s
                    """ % (
                        response['transactionResponse']['orderId'], 
                        response['transactionResponse']['transactionId'], 
                        'RECHAZADO', 
                        response['transactionResponse']['responseCode']
                    )
                    self.message_post(body=body_message, type="comment")
                    mail_values = {
                        'subject': 'Cobro liquidación %s %s'%(self.name, response['transactionResponse']['state']),
                        'body_html' : 'El cobro de la liquidación <b>%s</b> fue <b style="color: red;">%s</b><br/><br/>Cliente: %s'%(self.name, response['transactionResponse']['state'], self.partner_id.name),
                        'email_to': 'dv1@masmedicos.co',
                        # 'email_to': 'analistaprocesos@masmedicos.co, analistaux@masmedicos.co',
                        'email_from': 'contacto@masmedicos.co'
                    }
                    self.env['mail.mail'].sudo().create(mail_values).send()
        else:
            raise UserError('El metodo de pago no es Tarjeta de Credito, no tiene token, el pago fue aprobado o esta pendiente o la suscripcion esta en estado cerrado')
            
    def cron_get_status_payu_latam_account_move(self):
        """ selección de liquidaciones de pedidos a procesar, que están pendientes de respuesta de payu """
        invoice_ids = self.env['account.move'].search([
            ('payulatam_transaction_id', '!=', ''),
            ('payulatam_state', '=', 'PENDING'),
            ('payulatam_datetime', '!=', False),
        ])
        for invoice in invoice_ids:
            """ Consultando orden en payu """
            if invoice.payulatam_transaction_id:
                """ si existe una transacción """
                date_now = fields.datetime.now()
                date_difference = date_now - invoice.payulatam_datetime
                if invoice.payment_method_type == 'Cash':
                    time_check = 3600
                else:
                    time_check = 600
                if date_difference.seconds > time_check:
                    """ si existe una transacción """
                    response = self.env['api.payulatam'].payulatam_get_response_transaction(invoice.payulatam_transaction_id)
                    if response['code'] != 'SUCCESS':
                        raise ValidationError("""Error de comunicación con Payu: %s""", (json.dumps(response)))
                    if response['result']['payload']['state'] == 'DECLINED':
                        body_message = """
                            <b><span style='color:red;'>PayU Latam - Transacción de pago declinada</span></b><br/>
                            <b>Orden ID:</b> %s<br/>
                            <b>Transacción ID:</b> %s<br/>
                            <b>Estado:</b> %s<br/>
                            <b>Código Respuesta:</b> %s
                        """ % (
                            self.payulatam_order_id, 
                            self.payulatam_transaction_id, 
                            'DECLINADO',
                            response['result']['payload']['responseCode']
                        )
                        invoice.message_post(body=body_message)
                        invoice.write({
                            'payulatam_state': response['result']['payload']['state'],
                            'payulatam_datetime': datetime.fromtimestamp(int(response['result']['payload']['operationDate']) / 1e3)
                        })
                    if response['result']['payload']['state'] == 'EXPIRED':
                        body_message = """
                            <b><span style='color:red;'>PayU Latam - Transacción de pago expirada</span></b><br/>
                            <b>Orden ID:</b> %s<br/>
                            <b>Transacción ID:</b> %s<br/>
                            <b>Estado:</b> %s<br/>
                            <b>Código Respuesta:</b> %s
                        """ % (
                            self.payulatam_order_id, 
                            self.payulatam_transaction_id, 
                            'EXPIRADO',
                            response['result']['payload']['responseCode']
                        )
                        invoice.message_post(body=body_message)
                        invoice.write({
                            'payulatam_state': response['result']['payload']['state'],
                            'payulatam_datetime': datetime.fromtimestamp(int(response['result']['payload']['operationDate']) / 1e3)
                        })
                    if response['result']['payload']['state'] == 'APPROVED':
                        subscription = self.env['sale.subscription'].sudo().search([('code', '=', invoice.invoice_origin)])
                        product = invoice.invoice_line_ids[0].product_id
                        sale_order = self.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
                        body_message = """
                            <b><span style='color:green;'>PayU Latam - Transacción de pago aprobada</span></b><br/>
                            <b>Orden ID:</b> %s<br/>
                            <b>Transacción ID:</b> %s<br/>
                            <b>Estado:</b> %s<br/>
                            <b>Código Respuesta:</b> %s
                        """ % (
                            self.payulatam_order_id, 
                            self.payulatam_transaction_id, 
                            'APROBADO',
                            response['result']['payload']['responseCode']
                        )
                        invoice.message_post(body=body_message)
                        invoice.write({
                            'payulatam_state': response['result']['payload']['state'],
                            'payulatam_datetime': datetime.fromtimestamp(int(response['result']['payload']['operationDate']) / 1e3)
                        })
                        deal_id = self.env['api.hubspot'].search_deal_id(subscription)
                        if deal_id != False:
                            search_properties = ['estado_de_la_poliza']
                            properties = self.env['api.hubspot'].search_deal_properties_values(deal_id, search_properties)
                            if properties['estado_de_la_poliza'] != 'Activo':
                                # Actualizar valor
                                update_properties = {
                                    "estado_de_la_poliza": "Activo"
                                }
                                self.env['api.hubspot'].update_deal(deal_id, update_properties)
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
                            sale_order.beneficiary0_id.firstname if sale_order.beneficiary0_id.firstname != False else '', 
                            sale_order.beneficiary0_id.othernames if sale_order.beneficiary0_id.othernames != False else '',
                            (str(sale_order.beneficiary0_id.lastname) + ' ' + str(sale_order.beneficiary0_id.lastname2))[:20] if sale_order.beneficiary0_id.lastname != False else '', 
                            sale_order.beneficiary0_id.identification_document if sale_order.beneficiary0_id.identification_document != False else '', 
                            sale_order.beneficiary0_id.birthdate_date if sale_order.beneficiary0_id.birthdate_date != False else '',
                            'R', 
                            product.product_class if product.product_class != False else '', 
                            invoice.payulatam_datetime.date(),
                            invoice.amount_total if invoice.amount_total != False else '', 
                            1, 
                            invoice.payment_method_type if invoice.payment_method_type != False else '', 
                            product.subscription_template_id.recurring_rule_count if product.subscription_template_id.recurring_rule_count  != False else '', 
                            int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                            int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id)])) - int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                            subscription.policyholder if subscription.policyholder != False else '', 
                            invoice.sponsor_id.id if invoice.sponsor_id.id != False else 'null', 
                            product.default_code if product.default_code != False else '', 
                            product.name if product.name != False else '', 
                            invoice.payulatam_order_id if invoice.payulatam_order_id != False else '', 
                            invoice.payulatam_transaction_id if invoice.payulatam_transaction_id != False else '', 
                            invoice.name if invoice.name != False else '', 
                            sale_order.id if sale_order.id != False else 'null',
                            subscription.id if subscription.id  != False else 'null',
                            'recurring_payment',
                            invoice.payulatam_order_id if invoice.payulatam_order_id != False else ''
                        )
                        invoice.env.cr.execute(query)


    def cron_payment_credit_card_by_tokenization(self):
        # TODO: preguntar desde que hora se pueden lanzar los pagos, si se puede desde las 12:01am
        # o sin se debe iniciar desde cierta hora.

        today = fields.Date.today()
        # invoice_date = today - timedelta(days=5)
        invoice_payment_ids = self.env['account.move'].search([
            ('state', '=', 'finalized'),
            ('payment_method_type', '=', 'Credit Card'),
            ('payulatam_state', '=', False),
            ('payulatam_credit_card_token', '!=', False),
            ('invoice_date', '=', today)
        ], limit=45)
        
        _logger.error('////////////////////////////////////////////////')
        _logger.error(invoice_payment_ids)
        
        for invoice_payment in invoice_payment_ids:
            time.sleep(10) #sh da 15 minutos y cada factura en payu tarda 20 segundos aprox
        #if self.payment_method_type == 'Credit Card' and self.payulatam_credit_card_token != '':
            """ Proceso de Pago """
            referenceCode = str(self.env['api.payulatam'].payulatam_get_sequence())
            accountId = self.env['api.payulatam'].payulatam_get_accountId()
            descriptionPay = "Payment Origin from " + invoice_payment.name
            signature = self.env['api.payulatam'].payulatam_get_signature(
                invoice_payment.amount_total,'COP',referenceCode)

            payulatam_api_env = self.env.user.company_id.payulatam_api_env
            if payulatam_api_env == 'prod':
                payulatam_response_url = self.env.user.company_id.payulatam_api_response_url
            else:
                payulatam_response_url = self.env.user.company_id.payulatam_api_response_sandbox_url

            tx_value = {"value": invoice_payment.amount_total, "currency": "COP"}
            tx_tax = {"value": 0,"currency": "COP"}
            tx_tax_return_base = {"value": 0, "currency": "COP"}        
            additionalValues = {
                "TX_VALUE": tx_value,
                "TX_TAX": tx_tax,
                "TX_TAX_RETURN_BASE": tx_tax_return_base
            }
            shippingAddress = {
                "street1": invoice_payment.partner_id.street,
                "street2": "",
                "city": invoice_payment.partner_id.zip_id.city_id.name,
                "state": invoice_payment.partner_id.zip_id.city_id.state_id.name,
                "country": "CO",
                "postalCode": invoice_payment.partner_id.zip_id.name,
                "phone": invoice_payment.partner_id.phone
            }
            buyer = {
                "merchantBuyerId": str(invoice_payment.partner_id.id),
                "fullName": invoice_payment.partner_id.name,
                "emailAddress": invoice_payment.partner_id.email,
                "contactPhone": invoice_payment.partner_id.phone,
                "dniNumber": invoice_payment.partner_id.identification_document,
                "shippingAddress": shippingAddress
            }
            order_api = {
                "accountId": accountId,
                "referenceCode": referenceCode,
                "description": 'PPS - ' + descriptionPay,
                "language": "es",
                "signature": signature,
                "notifyUrl":payulatam_response_url,
                "additionalValues": additionalValues,
                "buyer": buyer,
                "shippingAddress": shippingAddress
            }
            billingAddressPayer = {
                "street1": invoice_payment.partner_id.street,
                "street2": "",
                "city": invoice_payment.partner_id.zip_id.city_id.name,
                "state": invoice_payment.partner_id.zip_id.city_id.state_id.name,
                "country": "CO",
                "postalCode": invoice_payment.partner_id.zip_id.name,
                "phone": invoice_payment.partner_id.phone
            }
            payer = {
                "fullName": invoice_payment.partner_id.name,
                "emailAddress": invoice_payment.partner_id.email,
                "contactPhone": invoice_payment.partner_id.phone,
                "dniNumber": invoice_payment.partner_id.identification_document,
                "billingAddress": billingAddressPayer
            }
            creditCard = {
                "processWithoutCvv2": "true"
            }
            extraParameters = {
                "INSTALLMENTS_NUMBER": 1
            }
            transaction = {
                "order": order_api,
                "payer": payer,
                "creditCardTokenId": invoice_payment.payulatam_credit_card_token,
                "creditCard": creditCard,
                "extraParameters": extraParameters,
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": invoice_payment.payulatam_credit_card_method,
                "paymentCountry": "CO",
                "deviceSessionId": "vghs6tvkcle931686k1900o6e1",
                "ipAddress": "127.0.0.1",
                "cookie": "pt1t38347bs6jc9ruv2ecpv7o2",
                "userAgent": "Firefox"
            }
            credit_card_values = {
                "command": "SUBMIT_TRANSACTION",
                "transaction": transaction,
            }
            response = self.env['api.payulatam'].payulatam_credit_cards_payment_request(credit_card_values)
            _logger.error('***************************************************')
            _logger.error(response)
            if response['code'] != 'SUCCESS':
                body_message = """
                    <b><span style='color:red;'>PayU Latam - Error en pago con tarjeta de crédito</span></b><br/>
                    <b>Código:</b> %s<br/>
                    <b>Error:</b> %s
                """ % (
                    response['code'],
                    response['error'], 
                )
                invoice_payment.message_post(body=body_message, type="comment")
            #TODO: {'code': 'ERROR', 'error': 'Error to find The Credit Card Token with identifier [f584f470-84d4-4b68-94c2-7bb0c49c9a58]', 'transactionResponse': None}
            else:
                if response['transactionResponse']['state'] == 'APPROVED':
                    subscription = self.env['sale.subscription'].sudo().search([('code', '=', invoice_payment.invoice_origin)])
                    product = invoice_payment.invoice_line_ids[0].product_id
                    sale_order = self.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
                    invoice_payment.write({
                        'payulatam_order_id': response['transactionResponse']['orderId'],
                        'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                        'payulatam_state': response['transactionResponse']['state'],
                        'payment_method_type': 'Credit Card',
                        'payulatam_datetime': fields.datetime.now(),
                    })
                    body_message = """
                        <b><span style='color:green;'>PayU Latam - Transacción de pago con tarjeta de crédito</span></b><br/>
                        <b>Orden ID:</b> %s<br/>
                        <b>Transacción ID:</b> %s<br/>
                        <b>Estado:</b> %s<br/>
                        <b>Código Respuesta:</b> %s
                    """ % (
                        response['transactionResponse']['orderId'],
                        response['transactionResponse']['transactionId'],
                        'APROBADO',
                        response['transactionResponse']['responseCode']
                    )
                    invoice_payment.message_post(body=body_message, type="comment")
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
                        sale_order.beneficiary0_id.firstname if sale_order.beneficiary0_id.firstname != False else '', 
                        sale_order.beneficiary0_id.othernames if sale_order.beneficiary0_id.othernames != False else '',
                        (str(sale_order.beneficiary0_id.lastname) + ' ' + str(sale_order.beneficiary0_id.lastname2))[:20] if sale_order.beneficiary0_id.lastname != False else '', 
                        sale_order.beneficiary0_id.identification_document if sale_order.beneficiary0_id.identification_document != False else '', 
                        sale_order.beneficiary0_id.birthdate_date if sale_order.beneficiary0_id.birthdate_date != False else '',
                        'R',
                        product.product_class if product.product_class != False else '',
                        date.today(),
                        invoice_payment.amount_total if invoice_payment.amount_total != False else '',
                        1,
                        invoice_payment.payment_method_type if invoice_payment.payment_method_type != False else '',
                        product.subscription_template_id.recurring_rule_count if product.subscription_template_id.recurring_rule_count  != False else '',
                        int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                        int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id)])) - int(self.env['account.move'].sudo().search_count([('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
                        subscription.policyholder if subscription.policyholder != False else '',
                        invoice_payment.sponsor_id.id if invoice_payment.sponsor_id.id != False else 'null',
                        product.default_code if product.default_code != False else '',
                        product.name if product.name != False else '',
                        invoice_payment.payulatam_order_id if invoice_payment.payulatam_order_id != False else '',
                        invoice_payment.payulatam_transaction_id if invoice_payment.payulatam_transaction_id != False else '',
                        invoice_payment.name if invoice_payment.name != False else '',
                        sale_order.id if sale_order.id != False else 'null',
                        subscription.id if subscription.id  != False else 'null',
                        'recurring_payment',
                        invoice_payment.payulatam_order_id if invoice_payment.payulatam_order_id != False else ''
                    )
                    self.env.cr.execute(query)
                elif response['transactionResponse']['state'] == 'PENDING':
                    invoice_payment.write({
                        'payulatam_order_id': response['transactionResponse']['orderId'],
                        'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                        'payulatam_state': response['transactionResponse']['state'],
                        'payment_method_type': 'Credit Card',
                        'payulatam_datetime': fields.datetime.now(),
                    })
                    body_message = """
                        <b><span style='color:orange;'>PayU Latam - Transacción de pago con tarjeta de crédito</span></b><br/>
                        <b>Orden ID:</b> %s<br/>
                        <b>Transacción ID:</b> %s<br/>
                        <b>Estado:</b> %s<br/>
                        <b>Código Respuesta:</b> %s
                    """ % (
                        response['transactionResponse']['orderId'],
                        response['transactionResponse']['transactionId'],
                        'PENDIENTE DE APROBACIÓN',
                        response['transactionResponse']['responseCode']
                    )
                    invoice_payment.message_post(body=body_message, type="comment")
                elif response['transactionResponse']['state'] in ['EXPIRED', 'DECLINED']:
                    invoice_payment.write({
                        'payulatam_order_id': response['transactionResponse']['orderId'],
                        'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                        'payulatam_state': response['transactionResponse']['state'],
                        'payment_method_type': 'Credit Card',
                        'payulatam_datetime': fields.datetime.now(),
                    })
                    body_message = """
                        <b><span style='color:red;'>PayU Latam - Transacción de pago con tarjeta de crédito</span></b><br/>
                        <b>Orden ID:</b> %s<br/>
                        <b>Transacción ID:</b> %s<br/>
                        <b>Estado:</b> %s<br/>
                        <b>Código Respuesta:</b> %s
                    """ % (
                        response['transactionResponse']['orderId'],
                        response['transactionResponse']['transactionId'],
                        'RECHAZADO',
                        response['transactionResponse']['responseCode']
                    )
                    invoice_payment.message_post(body=body_message, type="comment")

    def _cron_message_payments(self):
        today = fields.Date.today()
        invoice_payment_ids = self.env['account.move'].search([
            ('state', '=', 'finalized'),
            ('payulatam_state', 'in', [False, "EXPIRED", "DECLINED"]),
            ('payment_method_type', '!=', 'Product Without Price'),
            ('action_date_billing_cycle', '!=', today),
            ('sponsor_id', '!=', 5521)
        ], limit=45)
        _logger.info('********************************* Bot Accion de cobro *********************************')
        _logger.info(invoice_payment_ids)
        for invoice in invoice_payment_ids:
            time.sleep(10)
            diff = today - invoice.invoice_date
            subscription = self.env['sale.subscription'].search([('code', '=', invoice.invoice_origin)])
            sale_order = self.env['sale.order'].search([('subscription_id', '=', subscription.id)])
            deal_id = self.env['api.hubspot'].search_deal_id(subscription)
            _logger.info(invoice)
            _logger.info(diff)
            _logger.info(subscription.number)
            _logger.info(subscription.policy_number)
            _logger.info('deal_id')
            _logger.info(deal_id)
            _logger.info('action date billing cycle')
            _logger.info(invoice.action_date_billing_cycle)
            invoice.action_date_billing_cycle = today
            _logger.info('action date billing cycle')
            _logger.info(invoice.action_date_billing_cycle)
            if deal_id == False:
                continue            
            if subscription.stage_id == 4:
                invoice.payulatam_state = 'no_payment'
                continue
            search_policy_state = ['estado_de_la_poliza']
            policy_state = self.env['api.hubspot'].search_deal_properties_values(deal_id, search_policy_state)
            if policy_state['estado_de_la_poliza'] == 'Cancelado':
                invoice.payulatam_state = 'no_payment'
                continue
            # Buscando el comprador
            contact_id = self.env['api.hubspot'].search_contact_id(invoice.partner_id)
            if contact_id:
                _logger.info('*********** Actualizando comprador ***********')
                search_properties = ['es_comprador_']
                properties = self.env['api.hubspot'].search_contact_properties_values(contact_id, search_properties)
                if properties['es_comprador_'] != 'SI':
                    # Actualizar valor
                    update_properties = {
                        "es_comprador_": "SI"
                    }
                    self.env['api.hubspot'].update_contact_id(contact_id, update_properties)
            else:
                _logger.info('*********** Creando comprador ***********')
                contact_id = self.env['api.hubspot'].create_contact(invoice.partner_id)
                self.env['api.hubspot'].associate_deal(str(deal_id), str(contact_id))
                company_id = self.env['api.hubspot'].search_company_id(sale_order.beneficiary0_id)
                _logger.info('*********** Compañia ***********')
                _logger.info(company_id)
                if company_id:
                    self.env['api.hubspot'].associate_company_with_contact(str(company_id), str(contact_id))
            _logger.info('contact_id')
            _logger.info(contact_id)
            if diff.days == -4:
                deal_properties = {
                    "accion_de_cobro": "5 dias antes",
                    "estado_de_accion_de_cobro": "SI"
                }
                contact_properties = {
                    "estado_de_accion_de_cobro": "SI"
                }
                if invoice.payment_method_type == 'Credit Card':
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "Tarjeta de Credito",
                    })
                else:
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "PSE o Efectivo",
                        "link_de_cobro_odoo": str(invoice.generate_link(invoice.id))
                    })
                    contact_properties.update({
                        "link_de_pago": str(invoice.generate_link(invoice.id))
                    })
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                invoice.hubspot_payment_action = "5_days_before"
                body_message = """
                    <b><span style='color: darkblue;'>API HubSpot - Informacion ciclo de cobro</span></b><br/>
                    <b>Acción de cobro:</b> %s<br/>
                    <b>Estado de accion de cobro:</b> %s<br/>
                    <b>Metodo de pago:</b> %s<br/>
                    <b>Link de pago:</b> %s
                """ % (
                    deal_properties['accion_de_cobro'],
                    deal_properties['estado_de_accion_de_cobro'],
                    deal_properties['metodo_de_pago_para_cobro'],
                    deal_properties['link_de_cobro_odoo'] if 'link_de_cobro_odoo' in deal_properties else ''
                )
                invoice.message_post(body=body_message, type="comment")
            elif diff.days == -1:
                deal_properties = {
                    "accion_de_cobro": "1 dia antes",
                    "estado_de_accion_de_cobro": "SI"
                }
                contact_properties = {
                    "estado_de_accion_de_cobro": "SI"
                }
                if invoice.payment_method_type == 'Credit Card':
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "Tarjeta de Credito",
                    })
                else:
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "PSE o Efectivo",
                        "link_de_cobro_odoo": str(invoice.generate_link(invoice.id))
                    })
                    contact_properties.update({
                        "link_de_pago": str(invoice.generate_link(invoice.id))
                    })
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                invoice.hubspot_payment_action = "1_day_before"
                body_message = """
                    <b><span style='color: darkblue;'>API HubSpot - Informacion ciclo de cobro</span></b><br/>
                    <b>Acción de cobro:</b> %s<br/>
                    <b>Estado de accion de cobro:</b> %s<br/>
                    <b>Metodo de pago:</b> %s<br/>
                    <b>Link de pago:</b> %s
                """ % (
                    deal_properties['accion_de_cobro'],
                    deal_properties['estado_de_accion_de_cobro'],
                    deal_properties['metodo_de_pago_para_cobro'],
                    deal_properties['link_de_cobro_odoo'] if 'link_de_cobro_odoo' in deal_properties else ''
                )
                invoice.message_post(body=body_message, type="comment")
            elif diff.days == 0:
                _logger.info(invoice.payment_method_type)
                _logger.info(invoice.payulatam_credit_card_token)
                if invoice.payment_method_type == 'Credit Card' and invoice.payulatam_credit_card_token != '':
                    _logger.info("Puede pagar por token")
                    invoice.payment_credit_card_by_tokenization()
                    time.sleep(5)
            elif diff.days == 1:
                deal_properties = {
                    "accion_de_cobro": "1 dia despues",
                    "estado_de_accion_de_cobro": "SI",
                    "estado_de_la_poliza": "En mora"
                }
                contact_properties = {
                    "estado_de_accion_de_cobro": "SI"
                }
                if invoice.payment_method_type == 'Credit Card':
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "Tarjeta de Credito",
                    })
                else:
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "PSE o Efectivo",
                        "link_de_cobro_odoo": str(invoice.generate_link(invoice.id))
                    })
                    contact_properties.update({
                        "link_de_pago": str(invoice.generate_link(invoice.id))
                    })
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                invoice.hubspot_payment_action = "1_days_after"
                body_message = """
                    <b><span style='color: darkblue;'>API HubSpot - Informacion ciclo de cobro</span></b><br/>
                    <b>Acción de cobro:</b> %s<br/>
                    <b>Estado de accion de cobro:</b> %s<br/>
                    <b>Metodo de pago:</b> %s<br/>
                    <b>Link de pago:</b> %s
                """ % (
                    deal_properties['accion_de_cobro'],
                    deal_properties['estado_de_accion_de_cobro'],
                    deal_properties['metodo_de_pago_para_cobro'],
                    deal_properties['link_de_cobro_odoo'] if 'link_de_cobro_odoo' in deal_properties else ''
                )
                invoice.message_post(body=body_message, type="comment")
            elif diff.days == 10:
                deal_properties = {
                    "accion_de_cobro": "10 dias despues",
                    "estado_de_accion_de_cobro": "SI",
                    "estado_de_la_poliza": "En mora"
                }
                contact_properties = {
                    "estado_de_accion_de_cobro": "SI"
                }
                if invoice.payment_method_type == 'Credit Card':
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "Tarjeta de Credito",
                    })
                else:
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "PSE o Efectivo",
                        "link_de_cobro_odoo": str(invoice.generate_link(invoice.id))
                    })
                    contact_properties.update({
                        "link_de_pago": str(invoice.generate_link(invoice.id))
                    })
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                invoice.hubspot_payment_action = "10_days_after"
                body_message = """
                    <b><span style='color: darkblue;'>API HubSpot - Informacion ciclo de cobro</span></b><br/>
                    <b>Acción de cobro:</b> %s<br/>
                    <b>Estado de accion de cobro:</b> %s<br/>
                    <b>Metodo de pago:</b> %s<br/>
                    <b>Link de pago:</b> %s
                """ % (
                    deal_properties['accion_de_cobro'],
                    deal_properties['estado_de_accion_de_cobro'],
                    deal_properties['metodo_de_pago_para_cobro'],
                    deal_properties['link_de_cobro_odoo'] if 'link_de_cobro_odoo' in deal_properties else ''
                )
                invoice.message_post(body=body_message, type="comment")
            elif diff.days == 20:
                deal_properties = {
                    "accion_de_cobro": "20 dias despues",
                    "estado_de_accion_de_cobro": "SI",
                    "estado_de_la_poliza": "En mora"
                }
                contact_properties = {
                    "estado_de_accion_de_cobro": "SI"
                }
                if invoice.payment_method_type == 'Credit Card':
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "Tarjeta de Credito",
                    })
                else:
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "PSE o Efectivo",
                        "link_de_cobro_odoo": str(invoice.generate_link(invoice.id))
                    })
                    contact_properties.update({
                        "link_de_pago": str(invoice.generate_link(invoice.id))
                    })
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                invoice.hubspot_payment_action = "20_days_after"
                body_message = """
                    <b><span style='color: darkblue;'>API HubSpot - Informacion ciclo de cobro</span></b><br/>
                    <b>Acción de cobro:</b> %s<br/>
                    <b>Estado de accion de cobro:</b> %s<br/>
                    <b>Metodo de pago:</b> %s<br/>
                    <b>Link de pago:</b> %s
                """ % (
                    deal_properties['accion_de_cobro'],
                    deal_properties['estado_de_accion_de_cobro'],
                    deal_properties['metodo_de_pago_para_cobro'],
                    deal_properties['link_de_cobro_odoo'] if 'link_de_cobro_odoo' in deal_properties else ''
                )
                invoice.message_post(body=body_message, type="comment")
            elif diff.days == 25:
                deal_properties = {
                    "accion_de_cobro": "PC 25 dias despues",
                    "estado_de_accion_de_cobro": "SI",
                    "estado_de_la_poliza": "En proceso de cancelación"
                }
                contact_properties = {
                    "estado_de_accion_de_cobro": "SI"
                }
                if invoice.payment_method_type == 'Credit Card':
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "Tarjeta de Credito",
                    })
                else:
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "PSE o Efectivo",
                        "link_de_cobro_odoo": str(invoice.generate_link(invoice.id))
                    })
                    contact_properties.update({
                        "link_de_pago": str(invoice.generate_link(invoice.id))
                    })
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                invoice.hubspot_payment_action = "25_days_after"
                body_message = """
                    <b><span style='color: darkblue;'>API HubSpot - Informacion ciclo de cobro</span></b><br/>
                    <b>Acción de cobro:</b> %s<br/>
                    <b>Estado de accion de cobro:</b> %s<br/>
                    <b>Metodo de pago:</b> %s<br/>
                    <b>Link de pago:</b> %s
                """ % (
                    deal_properties['accion_de_cobro'],
                    deal_properties['estado_de_accion_de_cobro'],
                    deal_properties['metodo_de_pago_para_cobro'],
                    deal_properties['link_de_cobro_odoo'] if 'link_de_cobro_odoo' in deal_properties else ''
                )
                invoice.message_post(body=body_message, type="comment")
            elif diff.days >= 36:
                deal_properties = {
                    "accion_de_cobro": "C 36 dias despues",
                    "estado_de_accion_de_cobro": "SI",
                    "estado_de_la_poliza": "Cancelado",
                    "causal_de_cancelacion": "Falta de pago",
                    "fecha_efectiva_de_cancelacion": today
                }
                contact_properties = {
                    "estado_de_accion_de_cobro": "SI"
                }
                if invoice.payment_method_type == 'Credit Card':
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "Tarjeta de Credito",
                    })
                else:
                    deal_properties.update({
                        "metodo_de_pago_para_cobro": "PSE o Efectivo",
                        "link_de_cobro_odoo": str(invoice.generate_link(invoice.id))
                    })
                    contact_properties.update({
                        "link_de_pago": str(invoice.generate_link(invoice.id))
                    })
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                invoice.payulatam_state = 'no_payment'
                invoice.hubspot_payment_action = "36_days_after"
                body_message = """
                    <b><span style='color: darkblue;'>API HubSpot - Informacion ciclo de cobro</span></b><br/>
                    <b>Acción de cobro:</b> %s<br/>
                    <b>Estado de accion de cobro:</b> %s<br/>
                    <b>Metodo de pago:</b> %s<br/>
                    <b>Link de pago:</b> %s
                """ % (
                    deal_properties['accion_de_cobro'],
                    deal_properties['estado_de_accion_de_cobro'],
                    deal_properties['metodo_de_pago_para_cobro'],
                    deal_properties['link_de_cobro_odoo'] if 'link_de_cobro_odoo' in deal_properties else ''
                )
                invoice.message_post(body=body_message, type="comment")
                subscription.write({
                    'stage_id': 4, 
                    'to_renew': False, 
                    'date': today,
                    'close_reason_id': 13
                })
                sale_order.write({
                    'state': 'done',
                    'cancel_date': today
                })