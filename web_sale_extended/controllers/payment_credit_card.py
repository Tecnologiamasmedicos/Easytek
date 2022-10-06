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
    
    @http.route(['/shop/payment/payulatam-gateway-api'], type='http', auth="public", website=True, sitemap=False)
    def payulatam_gateway_api(self, **post):
        order = request.website.sale_get_order()
        
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
        
        """ Si existe una orden activa y llegan sin el metodo de pago """
        if 'method_id' not in post or 'credit_card_number' not in post:
            return request.redirect('/shop/payment')
        """ Proceso de Pago """
        referenceCode = str(request.env['api.payulatam'].payulatam_get_sequence())
        accountId = request.env['api.payulatam'].payulatam_get_accountId()
        descriptionPay = "Payment Origin from " + order.name
        signature = request.env['api.payulatam'].payulatam_get_signature(
            order.amount_total,'COP',referenceCode)
        
        payulatam_api_env = request.env.user.company_id.payulatam_api_env
        if payulatam_api_env == 'prod':
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_url
        else:
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_sandbox_url
        
        """ TARJETA DE CREDITO LUNH """
        luhn_ok = request.env['api.payulatam'].luhn_checksum(post['credit_card_number'])
        if not luhn_ok:
            render_values = {'error': 'Número de tarjeta invalido', 'website_sale_order': order,}
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en Transacción con Tarjeta de Crédito</span></b><br/>
                <b>Error:</b> %s
            """ % (
                render_values['error'], 
            )
            order.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payulatam_rejected_process", render_values)
        
        """ Proceso de Tokenización """
        creditCardToken = {
            "payerId": str(order.partner_id.id),
            #"name": post['credit_card_billing_firstname'] + ' ' + post['credit_card_billing_lastname'],
            "name": post['credit_card_name'],
            "identificationNumber": post['credit_card_partner_document'],
            "paymentMethod": post['method_id'],
            "number": post['credit_card_number'],
            "expirationDate": post['credit_card_due_year'] + "/" + post['credit_card_due_month']
        }
        token_response = request.env['api.payulatam'].payulatam_get_credit_Card_token(creditCardToken)
        if token_response['code'] == 'SUCCESS':
            order.write({
                'payulatam_credit_card_token': token_response['creditCardToken']['creditCardTokenId'],
                'payulatam_credit_card_masked': token_response['creditCardToken']['maskedNumber'],
                'payulatam_credit_card_identification': token_response['creditCardToken']['identificationNumber'],
                'payulatam_credit_card_method': token_response['creditCardToken']['paymentMethod'],
            })
            body_message = """
                <b><span style='color:green;'>PayU Latam - Proceso de tokenización exitoso</span></b><br/>
                <b>Token:</b> %s<br/>
                <b>Mascara:</b> %s<br/>
                <b>Documento:</b> %s<br/>
                <b>Metodo:</b> %s
            """ % (
                token_response['creditCardToken']['creditCardTokenId'],
                token_response['creditCardToken']['maskedNumber'],
                token_response['creditCardToken']['identificationNumber'],
                token_response['creditCardToken']['paymentMethod']
            )
            order.message_post(body=body_message, type="comment")
        else:
            render_values = {'error': token_response['error']}
            render_values.update({
                'website_sale_order': order,
                'order_id': order
            })
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en proceso de tokenizacion</span></b><br/>
                <b>Error:</b> %s
            """ % (
                token_response['error'], 
            )
            order.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payulatam_rejected_process", render_values)
        
        _logger.error(token_response)
        tx_value = {"value": order.amount_total, "currency": "COP"}
        tx_tax = {"value": 0,"currency": "COP"}
        tx_tax_return_base = {"value": 0, "currency": "COP"}
        additionalValues = {
            "TX_VALUE": tx_value,
            "TX_TAX": tx_tax,
            "TX_TAX_RETURN_BASE": tx_tax_return_base
        }
        shippingAddress = {
            "street1": order.partner_id.street,
            "street2": "",
            "city": order.partner_id.zip_id.city_id.name,
            "state": order.partner_id.zip_id.city_id.state_id.name,
            "country": "CO",
            "postalCode": order.partner_id.zip_id.name,
            "phone": order.partner_id.phone
        }    
        buyer = {
            "merchantBuyerId": str(order.partner_id.id),
            "fullName": order.partner_id.name,
            "emailAddress": order.partner_id.email,
            "contactPhone": order.partner_id.phone,
            "dniNumber": order.partner_id.identification_document,
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
            "street1": post['credit_card_partner_street'],
            "street2": "",
            "city": request.env['api.payulatam'].search_city_name(post['credit_card_city']),
            "state": request.env['api.payulatam'].search_state_name(post['credit_card_state_id']),
            "country": request.env['api.payulatam'].search_country_code(post['credit_card_country_id']),
            "postalCode": post['credit_card_zip'],
            "phone": post['credit_card_partner_phone']
        }    
        payer = {
            "fullName": post['credit_card_billing_firstname'] + ' ' + post['credit_card_billing_lastname'],
            "emailAddress": post['credit_card_billing_email'],
            "contactPhone": post['credit_card_partner_phone'],
            "dniNumber": post['credit_card_partner_document'],
            "billingAddress": billingAddressPayer
        }
        extraParameters = {
            "INSTALLMENTS_NUMBER": int(post['credit_card_quotes'])
        }
        
        without_token = 1
        if without_token:
            credit_card = {
                "number": post['credit_card_number'],
                "securityCode": post['credit_card_code'],
                "expirationDate": post['credit_card_due_year'] + "/" + post['credit_card_due_month'],
                "name": post['credit_card_name']
            }
            transaction = {
                "order": order_api,
                "payer": payer,
                "creditCard": credit_card,
                "extraParameters": extraParameters,
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": post['method_id'],
                "paymentCountry": "CO",
                "deviceSessionId": request.httprequest.cookies.get('session_id'),
                "ipAddress": "127.0.0.1",
                "cookie": request.httprequest.cookies.get('session_id'),
                #"userAgent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101"
                "userAgent": "Firefox"
            }
        else:
            transaction = {
                "order": order_api,
                "payer": payer,
                "creditCardTokenId": order.payulatam_credit_card_token,
                "extraParameters": extraParameters,
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": post['method_id'],
                "paymentCountry": "CO",
                "deviceSessionId": request.httprequest.cookies.get('session_id'),
                "ipAddress": "127.0.0.1",
                "cookie": request.httprequest.cookies.get('session_id'),
                #"userAgent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101"
                "userAgent": "Firefox"
            }
        
        credit_card_values = {
            "command": "SUBMIT_TRANSACTION",
            "transaction": transaction,
        }
        _logger.error(credit_card_values)
        response = request.env['api.payulatam'].payulatam_credit_cards_payment_request(credit_card_values)
        if response['code'] != 'SUCCESS':
            render_values = {'error': response['error']}
            render_values.update({
                'website_sale_order': order,
                'order_id': order
            })
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en pago con tarjeta de crédito</span></b><br/>
                <b>Código:</b> %s<br/>
                <b>Error:</b> %s
            """ % (
                response['code'],
                response['error'], 
            )
            order.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payulatam_rejected_process", render_values)
    
        if response['transactionResponse']['state'] == 'APPROVED':
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Credit Card',
                'payulatam_state': 'TRANSACCIÓN CON TARJETA DE CRÉDITO APROBADA',
                'payulatam_datetime': fields.datetime.now(),
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
                order.beneficiary0_id.firstname if order.beneficiary0_id.firstname != False else '', 
                order.beneficiary0_id.othernames, 
                str(order.beneficiary0_id.lastname) + ' ' + str(order.beneficiary0_id.lastname2) if order.beneficiary0_id.lastname != False else '', 
                order.beneficiary0_id.identification_document if order.beneficiary0_id.identification_document != False else '', 
                order.beneficiary0_id.birthdate_date if order.beneficiary0_id.birthdate_date != False else '',
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
            order.action_payu_approved()
            render_values = {
                'website_sale_order': order,
                'error': '',
                'transactionId': response['transactionResponse']['transactionId'],
                'state': 'APROBADO',
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order,
                'access_token': str(request.env['sale.order'].generate_access_token(order.id))
            }
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
            order.message_post(body=body_message, type="comment")
            #order.action_confirm()
            return request.render("web_sale_extended.payulatam_success_process", render_values)
        elif response['transactionResponse']['state'] == 'PENDING':
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Credit Card',
                'payulatam_state': 'TRANSACCIÓN CON TARJETA DE CRÉDITO PENDIENTE DE APROBACIÓN',
                'payulatam_datetime': fields.datetime.now(),
            })
            order.action_payu_confirm()
            error = 'Transacción %s en estado : %s' % (
                response['transactionResponse']['transactionId'],response['transactionResponse']['pendingReason']
            )
            render_values = {'error': error}
            render_values.update({
                'website_sale_order': order,
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order
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
            order.message_post(body=body_message, type="comment")
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.render("web_sale_extended.payulatam_success_process_pending", render_values)
        elif response['transactionResponse']['state'] in ['EXPIRED', 'DECLINED']:
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Credit Card',
                'payulatam_state': 'TRANSACCIÓN CON TARJETA DE CRÉDITO RECHAZADA',
                'payulatam_datetime': fields.datetime.now(),
            })
            render_values = {'error': '', 'website_sale_order': order,}
            if response['transactionResponse']['paymentNetworkResponseErrorMessage']:
                render_values.update({'error': response['transactionResponse']['paymentNetworkResponseErrorMessage']})
            render_values.update({
                'website_sale_order': order,
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order
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
            order.message_post(body=body_message, type="comment")
            #order.action_cancel()
            return request.render("web_sale_extended.payulatam_rejected_process", render_values)
        else:
            error = 'Transacción en estado %s: %s' % (
                response['transactionResponse']['transactionId'],
                response['transactionResponse']['state']
            )
            order.action_cancel()
            render_values = {'error': error}
            render_values.update({
                'website_sale_order': order,
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order
            })
            return request.render("web_sale_extended.payulatam_rejected_process", render_values)

    @http.route(['/shop/payment/payulatam-gateway-api-credit-card'], type='http', auth="public", website=True, sitemap=False)
    def payulatam_gateway_api_credit_card(self, **post):
        if post['invoice_id']:
            origin_document = request.env['account.move'].sudo().browse(int(post['invoice_id']))
            subscription = request.env['sale.subscription'].sudo().search([('code', '=', origin_document.invoice_origin)])
            product = origin_document.invoice_line_ids[0].product_id
            sale_order = request.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
        elif post['order_id']:
            origin_document = request.env['sale.order'].sudo().browse(int(post['order_id']))
            subscription = origin_document.subscription_id
            product = origin_document.main_product_id
            sale_order = origin_document.id
            
        if not origin_document:
            redirection = self.checkout_redirection(sale_order)
            if redirection:
                return redirection
            
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
        descriptionPay = "Payment Origin from " + origin_document.name
        signature = request.env['api.payulatam'].payulatam_get_signature(amount,'COP',referenceCode)
        
        payulatam_api_env = request.env.user.company_id.payulatam_api_env
        if payulatam_api_env == 'prod':
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_url
        else:
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_sandbox_url
        
        """ TARJETA DE CREDITO LUNH """
        luhn_ok = request.env['api.payulatam'].luhn_checksum(post['credit_card_number'])
        if not luhn_ok:
            render_values = {'error': 'Número de tarjeta invalido', 'website_sale_order': sale_order}
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en Transacción con Tarjeta de Crédito</span></b><br/>
                <b>Error:</b> %s
            """ % (
                render_values['error'], 
            )
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payulatam_rejected_process", render_values)
        
        
        tx_value = {"value": amount, "currency": "COP"}
        tx_tax = {"value": 0,"currency": "COP"}
        tx_tax_return_base = {"value": 0, "currency": "COP"}        
        additionalValues = {
            "TX_VALUE": tx_value,
            "TX_TAX": tx_tax,
            "TX_TAX_RETURN_BASE": tx_tax_return_base
        }
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
            "merchantBuyerId": str(partner.id),
            "fullName": partner.name,
            "emailAddress": partner.email,
            "contactPhone": partner.phone if partner.phone else partner.mobile,
            "dniNumber": partner.identification_document,
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
            "street1": partner.street,
            "street2": "",
            "city": partner.zip_id.city_id.name,
            "state": partner.zip_id.city_id.state_id.name,
            "country": "CO",
            "postalCode": partner.zip_id.name,
            "phone": partner.phone if partner.phone else partner.mobile
        }    
        payer = {
            "fullName": partner.name,
            "emailAddress": partner.email,
            "contactPhone": partner.phone if partner.phone else partner.mobile,
            "dniNumber": partner.identification_document,
            "billingAddress": billingAddressPayer
        }
        extraParameters = {
            "INSTALLMENTS_NUMBER": int(post['credit_card_quotes'])
        }
        """ Proceso de Tokenización """
        creditCardToken = {
            "payerId": str(origin_document.partner_id.id),
            "name": post['credit_card_name'],
            "identificationNumber": post['credit_card_partner_document'],
            "paymentMethod": post['method_id'],
            "number": post['credit_card_number'],
            "expirationDate": post['credit_card_due_year'] + "/" + post['credit_card_due_month']
        }
        token_response = request.env['api.payulatam'].payulatam_get_credit_Card_token(creditCardToken)
        if token_response['code'] == 'SUCCESS':
            sale_order.write({
                'payment_method_type': 'Credit Card',
                'payulatam_credit_card_token': token_response['creditCardToken']['creditCardTokenId'],
                'payulatam_credit_card_masked': token_response['creditCardToken']['maskedNumber'],
                'payulatam_credit_card_identification': token_response['creditCardToken']['identificationNumber'],
                'payulatam_credit_card_method': token_response['creditCardToken']['paymentMethod'],
            })
            origin_document.write({
                'payulatam_credit_card_token': token_response['creditCardToken']['creditCardTokenId'],
                'payulatam_credit_card_masked': token_response['creditCardToken']['maskedNumber'],
                'payulatam_credit_card_identification': token_response['creditCardToken']['identificationNumber'],
                'payulatam_credit_card_method': token_response['creditCardToken']['paymentMethod'],
            })
            body_message = """
                <b><span style='color:green;'>PayU Latam - Proceso de tokenización exitoso</span></b><br/>
                <b>Token:</b> %s<br/>
                <b>Mascara:</b> %s<br/>
                <b>Documento:</b> %s<br/>
                <b>Metodo:</b> %s
            """ % (
                token_response['creditCardToken']['creditCardTokenId'],
                token_response['creditCardToken']['maskedNumber'],
                token_response['creditCardToken']['identificationNumber'],
                token_response['creditCardToken']['paymentMethod']
            )
            origin_document.message_post(body=body_message, type="comment")
            
            
            creditCard = {
                "securityCode": post['credit_card_code']
#                 "processWithoutCvv2": "true"
            }
            transaction = {
                "order": order_api,
                "payer": payer,
                "creditCardTokenId": token_response['creditCardToken']['creditCardTokenId'],
                "creditCard": creditCard,
                "extraParameters": extraParameters,
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": post['method_id'],
                "paymentCountry": "CO",
                "deviceSessionId": request.httprequest.cookies.get('session_id'),
#                 "ipAddress": "127.0.0.1",
                "ipAddress": request.httprequest.environ['REMOTE_ADDR'],
                "cookie": request.httprequest.cookies.get('session_id'),
                "userAgent": "Firefox"
            } 
        else:
            render_values = {'error': token_response['error']}
            render_values.update({
                'website_sale_order': sale_order,
                'order_id': origin_document
            })
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en proceso de tokenizacion</span></b><br/>
                <b>Error:</b> %s
            """ % (
                token_response['error'], 
            )
            origin_document.message_post(body=body_message, type="comment")
            credit_card = {
                "number": post['credit_card_number'],
                "securityCode": post['credit_card_code'],
                "expirationDate": post['credit_card_due_year'] + "/" + post['credit_card_due_month'],
                "name": post['credit_card_name']
            }
            transaction = {
                "order": order_api,
                "payer": payer,
                "creditCard": credit_card,
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": post['method_id'],
                "paymentCountry": "CO",
                "deviceSessionId": request.httprequest.cookies.get('session_id'),
                "ipAddress": request.httprequest.environ['REMOTE_ADDR'],
#                 "ipAddress": "127.0.0.1",
                "cookie": request.httprequest.cookies.get('session_id'),
                "userAgent": "Firefox"
            }
            
        credit_card_values = {
            "command": "SUBMIT_TRANSACTION",
            "transaction": transaction,
        }
        response = request.env['api.payulatam'].payulatam_credit_cards_payment_request(credit_card_values)
        if response['code'] != 'SUCCESS':
            render_values = {'error': response['error']}
            render_values.update({
                'website_sale_order': sale_order,
                'amount': amount,
                'image': '/web/image/1110/Img_failure%283%29.png?access_token=65b88bf9-b659-4486-ad0d-b8d066b52278',
                'responseMessage': 'Proceso de pago Fallido',
                'colorResponseMessage': 'red',
                'url': post['full_url'],
                'messageButton': 'Volver a la pasarela de pago',
                'messagePayment' : 'Pago No Realizado'
            })
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en pago con tarjeta de crédito</span></b><br/>
                <b>Código:</b> %s<br/>
                <b>Error:</b> %s
            """ % (
                response['code'],
                response['error'], 
            )
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        if response['transactionResponse']['state'] == 'APPROVED':
            origin_document.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Credit Card',
                'payulatam_datetime': fields.datetime.now(),
#                 'amount_residual': origin_document.amount_residual - amount,
#                 'amount_residual_signed': origin_document.amount_residual_signed - amount,
            })    
#             if origin_document.amount_residual == 0:
#                 origin_document.write({
#                     'invoice_payment_state': 'paid',
#                 })
                
#             Payment = request.env['account.payment'].sudo().with_context(active_ids=origin_document.ids, active_model='account.move', active_id=origin_document.id)
#             payments_vals = {
#                 'payment_type': 'inbound',
#                 'partner_type': 'customer',
#                 'partner_id': partner.id,
#                 'company_id': 1,
#                 'amount': amount,
#                 'payment_date': fields.Datetime.now(),
#                 'journal_id': 9,
#                 'payment_method_id': 1
#             }
#             payments = Payment.create(payments_vals)
#             payments.post()
                
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
            deal_id = request.env['api.hubspot'].search_deal_id(subscription)
            if deal_id != False:
                search_properties = ['estado_de_la_poliza']
                properties = request.env['api.hubspot'].search_deal_properties_values(deal_id, search_properties)
                if properties['estado_de_la_poliza'] != 'Activo':
                    # Actualizar valor
                    update_properties = {
                        "estado_de_la_poliza": "Activo"
                    }
                    request.env['api.hubspot'].update_deal(deal_id, update_properties)
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
                sale_order.beneficiary0_id.othernames, 
                str(sale_order.beneficiary0_id.lastname) + ' ' + str(sale_order.beneficiary0_id.lastname2) if sale_order.beneficiary0_id.lastname != False else '', 
                sale_order.beneficiary0_id.identification_document if sale_order.beneficiary0_id.identification_document != False else '', 
                sale_order.beneficiary0_id.birthdate_date if sale_order.beneficiary0_id.birthdate_date != False else '',
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
        elif response['transactionResponse']['state'] == 'PENDING':
            origin_document.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Credit Card',
                'payulatam_datetime': fields.datetime.now(),
            })
            error = 'Transacción %s en estado : %s' % (
                response['transactionResponse']['transactionId'],
                response['transactionResponse']['pendingReason']
            )
            render_values = {'error': error}
            render_values.update({
                'website_sale_order': sale_order,
                'amount': amount,
                'image': '/web_sale_extended/static/src/images/Img_warning.png',
                'responseMessage': 'Proceso de pago Pendiente',
                'colorResponseMessage': '#FF7800',
                'state': 'Estado: PENDIENTE',
                'coloresState': '#FF7800',
                'url': 'https://masmedicos.co',
                'messageButton': 'Gracias por tu pago',
                'messagePayment' : 'Pago Pendiente'
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
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        elif response['transactionResponse']['state'] in ['EXPIRED', 'DECLINED']:
            origin_document.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'Credit Card',
                'payulatam_datetime': fields.datetime.now(),
            })
            render_values = {'error': '', 'website_sale_order': sale_order}
            if response['transactionResponse']['paymentNetworkResponseErrorMessage']:
                render_values.update({'error': response['transactionResponse']['paymentNetworkResponseErrorMessage']})
            render_values.update({
                'website_sale_order': sale_order,
                'amount': amount,
                'image': '/web/image/1110/Img_failure%283%29.png?access_token=65b88bf9-b659-4486-ad0d-b8d066b52278',
                'responseMessage': 'Proceso de pago Rechazado',
                'colorResponseMessage': 'red',
                'aditionalInfo': 'Por favor intentelo de nuevo',
                'url': post['full_url'],
                'messageButton': 'Volver a la pasarela de pago',
                'messagePayment' : 'Pago No Realizado'
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
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        else:
            error = 'Transacción en estado %s: %s' % (
                response['transactionResponse']['transactionId'],
                response['transactionResponse']['state']
            )
            render_values = {'error': error}
            render_values.update({
                'website_sale_order': sale_order,
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