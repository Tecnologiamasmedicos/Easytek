# -*- coding: utf-8 -*-
import json
import logging, base64
from datetime import datetime, timedelta
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

    @http.route(['/shop/payment/payulatam-gateway-api/cash_process'], type='http', auth="public", website=True, sitemap=False, csrf=False)
    def payulatam_gateway_api_cash_payment(self, **post):
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
        
        """ Si existe una orden activa y llegan sin el metodo de pago """
        if not post['cash_bank']:
            return request.redirect('/shop/payment')
        """ Proceso de Pago """
        referenceCode = str(request.env['api.payulatam'].payulatam_get_sequence())
        accountId = request.env['api.payulatam'].payulatam_get_accountId()
        descriptionPay = "Payment Cash Origin from " + order.name
        signature = request.env['api.payulatam'].payulatam_get_signature(
            order.amount_total,'COP',referenceCode)
        
        payulatam_api_env = request.env.user.company_id.payulatam_api_env
        if payulatam_api_env == 'prod':
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_url
        else:
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_sandbox_url
        tx_value = {"value": order.amount_total, "currency": "COP"}
        tx_tax = {"value": 0,"currency": "COP"}
        tx_tax_return_base = {"value": 0, "currency": "COP"}
        expiration_cash = request.env.user.company_id.payulatam_cash_expiration
        expiration_date = str((fields.datetime.now() + timedelta(hours=expiration_cash))).replace(' ','T').split('.')[0]
        additionalValues = {
            "TX_VALUE": tx_value,
            "TX_TAX": tx_tax,
            "TX_TAX_RETURN_BASE": tx_tax_return_base
        }
        full_name = post['cash_billing_firstname']
        if 'cash_billing_lastname' in post:
            fullName = post['cash_billing_firstname'] + ' ' + post['cash_billing_lastname'],
        buyer = {
            "merchantBuyerId": "1",
            "fullName": full_name,
            "emailAddress": order.partner_id.email,
            "contactPhone": order.partner_id.phone,
            "dniNumber": order.partner_id.identification_document,
        }
        order_api = {
            "accountId": accountId,
            "referenceCode": referenceCode,
            "description": 'PPS-' + descriptionPay,
            "language": "es",
            "signature": signature,
            "notifyUrl": payulatam_response_url,
            "additionalValues": additionalValues,
            "buyer": buyer,
        }
        transaction = {
            "order": order_api,
            "type": "AUTHORIZATION_AND_CAPTURE",
            "paymentMethod": post['cash_bank'],
            "expirationDate": expiration_date,
            "paymentCountry": "CO",
            "ipAddress": "127.0.0.1",
        }
        cash_payment_values = {
            "command": "SUBMIT_TRANSACTION",
            "transaction": transaction,
        }
        response = request.env['api.payulatam'].payulatam_cash_payment_request(cash_payment_values)
        render_values = {'error': response['error']}
        if response['code'] != 'SUCCESS':
            """ Retornando error manteniendo la misma orden y dando la oportunidad de intentar de nuevo """
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en Transacción de Pago en Efectivo</span></b><br/>
                <b>Código:</b> %s<br/>
                <b>Error:</b> %s
            """ % (
                response['code'],
                response['error'], 
            )
            order.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payulatam_rejected_process_cash", render_values)

        if response['transactionResponse']['state'] == 'PENDING':
            """ Orden en estado Pendiente por confirmación PayU, se da por terminada la transacción como exitosa """
            order.action_payu_confirm()
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Cash',
                'payulatam_state': 'PENDIENTE DE PAGO',
                'payulatam_datetime': fields.datetime.now(),
            })
            if request.session.get('sale_order_id'):
                request.session['sale_order_id'] = None
                request.session['sale_transaction_id'] = None
                
            """ Mensaje en la orden de venta con la respuesta de PayU """
            body_message = """
                <b><span style='color:orange;'>PayU Latam - Transacción de Pago en Efectivo</span></b><br/>
                <b>Orden ID:</b> %s<br/>
                <b>Transacción ID:</b> %s<br/>
                <b>Estado:</b> %s<br/>
                <b>Código Respuesta:</b> %s<br/>
                <b>Motivo Pendiente:</b> %s<br/>
                <b>Fecha de Expiración:</b> %s
                <b>Url Recibo de Pago:</b> %s
            """ % (
                response['transactionResponse']['orderId'], 
                response['transactionResponse']['transactionId'], 
                response['transactionResponse']['state'], 
                response['transactionResponse']['responseCode'],
                response['transactionResponse']['pendingReason'],
                response['transactionResponse']['extraParameters']['EXPIRATION_DATE'],
                response['transactionResponse']['extraParameters']['URL_PAYMENT_RECEIPT_HTML']
            )
            order.message_post(body=body_message, type="comment")
            error = 'Transacción en estado %s: %s' % (
                response['transactionResponse']['transactionId'],response['transactionResponse']['state']
            )
            render_values = {'error': error}
            render_values.update({
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order,
                'url_payment_receipt_html': response['transactionResponse']['extraParameters']['URL_PAYMENT_RECEIPT_HTML'],
                'url_payment_receipt_pdf': response['transactionResponse']['extraParameters']['URL_PAYMENT_RECEIPT_PDF']
            })
            return request.render("web_sale_extended.payulatam_success_process_cash", render_values)
        elif response['transactionResponse']['state'] in ['EXPIRED', 'DECLINED']:
            """ Mensaje en la orden de venta con la respuesta de PayU """
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Cash',
                'payulatam_state': 'TRANSACCIÓN RECHAZADA',
                'payulatam_datetime': fields.datetime.now(),
            })
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en Transacción de Pago en Efectivo</span></b><br/>
                <b>Orden ID:</b> %s<br/>
                <b>Transacción ID:</b> %s<br/>
                <b>Estado:</b> %s<br/>
                <b>Código Respuesta:</b> %s
            """ % (
                response['transactionResponse']['orderId'], 
                response['transactionResponse']['transactionId'], 
                response['transactionResponse']['state'], 
                response['transactionResponse']['responseCode']
            )
            order.message_post(body=body_message, type="comment")
            render_values = {'error': '',}
            if response['transactionResponse']['paymentNetworkResponseErrorMessage']:
                render_values.update({'error': response['transactionResponse']['paymentNetworkResponseErrorMessage']})
            render_values.update({
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order,
            })
            #order.action_cancel()
            return request.render("web_sale_extended.payulatam_rejected_process_cash", render_values)
        else:
            error = 'Transacción en estado %s: %s' % (
                response['transactionResponse']['transactionId'],response['status']
            )
            order.action_cancel()
            if request.session.get('sale_order_id'):
                request.session['sale_order_id'] = None
            render_values = {'error': error}
            render_values.update({
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order
            })
            return request.render("web_sale_extended.payulatam_rejected_process_cash", render_values)
        
    @http.route(['/shop/payment/payulatam-gateway-api/cash_process_recurring'], type='http', auth="public", website=True, sitemap=False, csrf=False)
    def payulatam_gateway_api_cash_payment_recurring(self, **post):
        
        if post['invoice_id']:
            origin_document = request.env['account.move'].sudo().browse(int(post['invoice_id']))
        elif post['order_id']:
            origin_document = request.env['sale.order'].sudo().browse(int(post['order_id']))
        
        if post['partner_id']:
            partner = request.env['res.partner'].sudo().browse(int(post['partner']))
        else:
            partner = origin_document.partner_id
            
        if post['amount']:
            amount = float(post['amount'])
        else:
            amount = origin_document.amount_total
        
        """ Proceso de Pago """
        referenceCode = str(request.env['api.payulatam'].payulatam_get_sequence())
        accountId = request.env['api.payulatam'].payulatam_get_accountId()
        descriptionPay = "Payment Cash Origin from " + origin_document.name
        signature = request.env['api.payulatam'].payulatam_get_signature(amount, 'COP', referenceCode)
        
        payulatam_api_env = request.env.user.company_id.payulatam_api_env
        if payulatam_api_env == 'prod':
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_url
        else:
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_sandbox_url
        tx_value = {"value": amount, "currency": "COP"}
        tx_tax = {"value": 0,"currency": "COP"}
        tx_tax_return_base = {"value": 0, "currency": "COP"}
        expiration_cash = request.env.user.company_id.payulatam_cash_expiration
        expiration_date = str((fields.datetime.now() + timedelta(hours=expiration_cash))).replace(' ','T').split('.')[0]
        additionalValues = {
            "TX_VALUE": tx_value,
            "TX_TAX": tx_tax,
            "TX_TAX_RETURN_BASE": tx_tax_return_base
        }
        full_name = post['cash_billing_firstname']
        if 'cash_billing_lastname' in post:
            fullName = post['cash_billing_firstname'] + ' ' + post['cash_billing_lastname'],
            
        shippingAddress = {
            "street1": partner.street,
            "street2": "",
            "city": partner.zip_id.city_id.name,
            "state": partner.zip_id.city_id.state_id.name,
            "country": "CO",
            "postalCode": partner.zip_id.name,
            "phone": partner.phone if partner.phone else partner.mobile
        }
        buyer = {
            "merchantBuyerId": "1",
            "fullName": full_name,
            "emailAddress": post['cash_billing_email'],
            "contactPhone": post['cash_partner_phone'],
            "dniNumber": post['cash_partner_document'],
            "shippingAddress": shippingAddress
        }
        payer = {
            "merchantPayerId": "1",
            "fullName": full_name,
            "emailAddress": post['cash_billing_email'],
            "contactPhone": post['cash_partner_phone'],
            "dniNumber": post['cash_partner_document'],
            "billingAddress": {
                "street1": post['cash_partner_street'],
                "street2": "",
                "city": partner.zip_id.city_id.name,
                "state": partner.zip_id.city_id.state_id.name,
                "country": "CO",
                "postalCode": partner.zip_id.name,
                "phone": post['cash_partner_phone'],
            }
        }
        order_api = {
            "accountId": accountId,
            "referenceCode": referenceCode,
            "description": 'PPS-' + descriptionPay,
            "language": "es",
            "signature": signature,
            "notifyUrl": payulatam_response_url,
            "additionalValues": additionalValues,
            "buyer": buyer,
            "shippingAddress": shippingAddress,            
        }
        transaction = {
            "order": order_api,
            "payer": payer,
            "type": "AUTHORIZATION_AND_CAPTURE",
            "paymentMethod": post['cash_bank'],
            "expirationDate": expiration_date,
            "paymentCountry": "CO",
            "ipAddress": request.httprequest.environ['REMOTE_ADDR'],
        }
        cash_payment_values = {
            "command": "SUBMIT_TRANSACTION",
            "transaction": transaction,
        }
        response = request.env['api.payulatam'].payulatam_cash_payment_request(cash_payment_values)
        render_values = {'error': response['error']}
        if response['code'] != 'SUCCESS':
            render_values.update({
                'amount': amount,
                'image': '/web/image/1110/Img_failure%283%29.png?access_token=65b88bf9-b659-4486-ad0d-b8d066b52278',
                'responseMessage': 'Fallido',
                'colores': 'red',
                'url': post['full_url'],
                'messageButton': 'Volver a la pasarela de pago',
                'messagePayment' : 'Pago No Realizado'
            })
            """ Retornando error manteniendo la misma orden y dando la oportunidad de intentar de nuevo """
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en Transacción de Pago en Efectivo</span></b><br/>
                <b>Código:</b> %s<br/>
                <b>Error:</b> %s
            """ % (
                response['code'],
                response['error'], 
            )
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payu_transaction_response", render_values)

        if response['transactionResponse']['state'] == 'PENDING':
            """ Orden en estado Pendiente por confirmación PayU, se da por terminada la transacción como exitosa """
            
            origin_document.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Cash',
                'payulatam_datetime': fields.datetime.now(),
            })
            
                
            """ Mensaje en la orden de venta con la respuesta de PayU """
            body_message = """
                <b><span style='color:orange;'>PayU Latam - Transacción de Pago en Efectivo</span></b><br/>
                <b>Orden ID:</b> %s<br/>
                <b>Transacción ID:</b> %s<br/>
                <b>Estado:</b> %s<br/>
                <b>Código Respuesta:</b> %s<br/>
                <b>Motivo Pendiente:</b> %s<br/>
                <b>Fecha de Expiración:</b> %s<br/>
                <b>Url Recibo de Pago:</b> %s
            """ % (
                response['transactionResponse']['orderId'], 
                response['transactionResponse']['transactionId'], 
                response['transactionResponse']['state'], 
                response['transactionResponse']['responseCode'],
                response['transactionResponse']['pendingReason'],
                response['transactionResponse']['extraParameters']['EXPIRATION_DATE'],
                response['transactionResponse']['extraParameters']['URL_PAYMENT_RECEIPT_HTML']
            )
            origin_document.message_post(body=body_message, type="comment")
            error = 'Transacción en estado %s: %s' % (
                response['transactionResponse']['transactionId'],
                response['transactionResponse']['state']
            )
            render_values = {'error': error}
            render_values.update({
                'amount': amount,
                'image': '/web/image/1109/Img_success%282%29.png?access_token=a79d70ef-5174-4077-b854-a03eff98c0be',
                'responseMessage': 'Recibo de Pago generado exitosamente gracias a PayU',
                'colorResponseMessage': '#39b54a',
                'state': 'Estado: PENDIENTE DE PAGO',
                'coloresState': '#FF7800',
                'url_payment_receipt_html': response['transactionResponse']['extraParameters']['URL_PAYMENT_RECEIPT_HTML'],
                'url_payment_receipt_pdf': response['transactionResponse']['extraParameters']['URL_PAYMENT_RECEIPT_PDF'],
                'url': 'https://masmedicos.co',
                'messageButton': 'Gracias por tu pago',
                'messagePayment' : 'Pago Pendiente'
            })
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        elif response['transactionResponse']['state'] in ['EXPIRED', 'DECLINED']:
            """ Mensaje en la orden de venta con la respuesta de PayU """
            origin_document.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Cash',
                'payulatam_datetime': fields.datetime.now(),
            })
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en Transacción de Pago en Efectivo</span></b><br/>
                <b>Orden ID:</b> %s<br/>
                <b>Transacción ID:</b> %s<br/>
                <b>Estado:</b> %s<br/>
                <b>Código Respuesta:</b> %s
            """ % (
                response['transactionResponse']['orderId'], 
                response['transactionResponse']['transactionId'], 
                response['transactionResponse']['state'], 
                response['transactionResponse']['responseCode']
            )
            origin_document.message_post(body=body_message, type="comment")
            render_values = {'error': '',}
            if response['transactionResponse']['paymentNetworkResponseErrorMessage']:
                render_values.update({'error': response['transactionResponse']['paymentNetworkResponseErrorMessage']})
            render_values.update({
                'amount': amount,
                'image': '/web/image/1110/Img_failure%283%29.png?access_token=65b88bf9-b659-4486-ad0d-b8d066b52278',
                'responseMessage': 'Recibo de pago NO generado',
                'colorResponseMessage': 'red',
                'aditionalInfo': 'Por favor intentelo de nuevo',
                'url': post['full_url'],
                'messageButton': 'Volver a la pasarela de pago',
                'messagePayment' : 'Pago No Realizado'
            })
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        else:
            error = 'Transacción en estado %s: %s' % (
                response['transactionResponse']['transactionId'],
                response['status']
            )
            render_values = {'error': error}
            render_values.update({
                'amount': amount,
                'image': '/web/image/1110/Img_failure%283%29.png?access_token=65b88bf9-b659-4486-ad0d-b8d066b52278',
                'responseMessage': error,
                'colorResponseMessage': 'red',
                'aditionalInfo': 'Por favor intentelo de nuevo',
                'url': post['full_url'],
                'messageButton': 'Volver a la pasarela de pago',
                'messagePayment' : 'Pago No Realizado'
            })
            return request.render("web_sale_extended.payu_transaction_response", render_values)