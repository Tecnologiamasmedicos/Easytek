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
                
    @http.route(['/shop/payment/payulatam-gateway-api/pse_process'], type='http', auth="public", website=True, sitemap=False)
    def payulatam_gateway_api_pse(self, **post):
        order = request.website.sale_get_order()
        """ Proceso de Pago """
        referenceCode = str(request.env['api.payulatam'].payulatam_get_sequence())
        accountId = request.env['api.payulatam'].payulatam_get_accountId()
        descriptionPay = "Payment Origin from " + str(order.name)
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
            "phone": order.partner_id.phone if order.partner_id.phone else order.partner_id.mobile
        }
        buyer = {
            "merchantBuyerId": order.partner_id.id,
            "fullName": order.partner_id.name,
            "emailAddress": order.partner_id.email,
            "contactPhone": order.partner_id.phone,
            "dniNumber": order.partner_id.identification_document,
            "shippingAddress": shippingAddress
        }
        billingAddressPayer = {
            "street1": post['pse_partner_street'],
            "street2": "",
            "city": request.env['api.payulatam'].search_city_name(post['pse_city']),
            "state": request.env['api.payulatam'].search_state_name(post['pse_state_id']),
            "country": request.env['api.payulatam'].search_country_code(post['pse_country_id']),
            "postalCode": post['pse_zip'],
            "phone": post['pse_partner_phone']
        } 
        payer = {
            "fullName": post['pse_billing_firstname'] + ' ' + post['pse_billing_lastname'],
            "emailAddress": post['pse_billing_email'],
            "contactPhone": post['pse_partner_phone'],
            "dniNumber": post['pse_billing_partner_document'],
            "billingAddress": billingAddressPayer
        }
        order_api = {
            "accountId": accountId,
            "referenceCode": referenceCode,
            "description": descriptionPay,
            "language": "es",
            "signature": signature,
            #"notifyUrl": "https://easytek-confacturacion-2123332.dev.odoo.com/shop/payment/payulatam-gateway-api/response",
            "additionalValues": additionalValues,
            "buyer": buyer
        }
        
        extraParameters = {
            "RESPONSE_URL": payulatam_response_url,
            "PSE_REFERENCE1": "127.0.0.1",
            "FINANCIAL_INSTITUTION_CODE": post['pse_bank'],
            "USER_TYPE": post['pse_person_type'],
            "PSE_REFERENCE2": post['pse_partner_type'],
            "PSE_REFERENCE3": post['pse_partner_document']
        }    
        transaction = {
            "order": order_api,
            "payer": payer,
            "extraParameters": extraParameters,
            "type": "AUTHORIZATION_AND_CAPTURE",
            "paymentMethod": "PSE",
            "paymentCountry": "CO",
            "deviceSessionId": request.httprequest.cookies.get('session_id'),
            "ipAddress": "127.0.0.1",
            "cookie": request.httprequest.cookies.get('session_id'),
            "userAgent": "Firefox"
        }
        pse_payment_values = {
            "command": "SUBMIT_TRANSACTION",
            "transaction": transaction,
        }
        response = request.env['api.payulatam'].payulatam_credit_cards_payment_request(pse_payment_values)
        if response['code'] != 'SUCCESS':
            body_message = """
                <b><span style='color:red;'>PayU Latam - Error en pago con PSE</span></b><br/>
                <b>Código:</b> %s<br/>
                <b>Error:</b> %s
            """ % (
                response['code'],
                "Error de comunicación con PayU Latam"
            )
            if not request.session['sale_order_id']:
                checkout_landpage_redirect = request.env.user.company_id.checkout_landpage_redirect
                if checkout_landpage_redirect:
                    return request.redirect(checkout_landpage_redirect)
                return request.redirect("/web/login")
            else:
                order.message_post(body=body_message, type="comment")
                render_values = {'error': response['error'], 'website_sale_order': order}
                return request.render("web_sale_extended.payulatam_rejected_process", render_values)        

        if response['transactionResponse']['state'] == 'APPROVED':
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'PSE',
                'payulatam_state': 'TRANSACCIÓN CON PSE PENDIENTE DE APROBACIÓN',
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
            order.action_payu_approved()
            render_values = {'error': ''}
            render_values.update({
                'website_sale_order': order,
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'order_id': order
            })
            body_message = """
                <b><span style='color:green;'>PayU Latam - Transacción de pago con PSE</span></b><br/>
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
            return request.render("web_sale_extended.payulatam_success_process_pse", render_values)
        elif response['transactionResponse']['state'] == 'PENDING':
            order.action_payu_confirm()
            #request.session['sale_order_id'] = None
            #request.session['sale_transaction_id'] = None
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'PSE',
                'payulatam_state': 'TRANSACCIÓN CON PSE PENDIENTE DE APROBACIÓN',
                'payulatam_datetime': fields.datetime.now(),
            })
            error = ''
            render_values = {'error': error}
            render_values.update({
                'website_sale_order': order,
                'state': response['transactionResponse']['state'],
                'transactionId': response['transactionResponse']['transactionId'],
                'responseCode': response['transactionResponse']['responseCode'],
                'order_Id': response['transactionResponse']['orderId'],
                'bank_url': response['transactionResponse']['orderId'],
                'order_id': order,
                'bank_url': response['transactionResponse']['extraParameters']['BANK_URL']
            })
            body_message = """
                <b><span style='color:orange;'>PayU Latam - Transacción de pago con PSE</span></b><br/>
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
            return request.render("web_sale_extended.payulatam_success_process_pse", render_values)
        elif response['transactionResponse']['state'] in ['EXPIRED', 'DECLINED']:
            order.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'PSE',
                'payulatam_state': 'TRANSACCIÓN CON PSE RECHAZADA',
                'payulatam_datetime': fields.datetime.now(),
            })
            render_values = {}
            #if 'paymentNetworkResponseErrorMessage' in response['transactionResponse']:
            #    if 'ya se encuentra registrada con la referencia' in response['transactionResponse']['paymentNetworkResponseErrorMessage']:
            render_values = {'error': '', 'website_sale_order': order}
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
                <b><span style='color:red;'>PayU Latam - Transacción de pago con PSE</span></b><br/>
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
            return request.render("web_sale_extended.payulatam_rejected_process_pse", render_values)
        else:
            error = 'Se recibió un estado no reconocido para el pago de PayU Latam %s: %s, set as error' % (
                response['transactionResponse']['transactionId'],response['transactionResponse']['state']
            )
            order.action_cancel()
            render_values = {'error': error, 'website_sale_order': order,}
            return request.render("web_sale_extended.payulatam_rejected_process_pse", render_values)
        
    @http.route(['/shop/payment/payulatam-gateway-api/pse_process_recurring'], type='http', auth="public", website=True, sitemap=False)
    def payulatam_gateway_api_pse_recurring(self, **post):
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
            redirection = self.checkout_redirection(origin_document)
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
        descriptionPay = "Payment Origin from " + str(origin_document.name)
        signature = request.env['api.payulatam'].payulatam_get_signature(origin_document.amount_total,'COP',referenceCode)
        payulatam_api_env = request.env.user.company_id.payulatam_api_env
        if payulatam_api_env == 'prod':
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_url
        else:
            payulatam_response_url = request.env.user.company_id.payulatam_api_response_sandbox_url
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
            "merchantBuyerId": "1",
            "fullName": partner.name,
            "emailAddress": partner.email,
            "contactPhone": partner.phone if partner.phone else partner.mobile,
            "dniNumber": partner.identification_document,
            "shippingAddress": shippingAddress
        }
        payer = {
            "merchantPayerId": "1",
            "fullName": post['pse_billing_firstname'] + ' ' + post['pse_billing_lastname'],
            "emailAddress": post['pse_billing_email'],
            "contactPhone": post['pse_partner_phone'],
            "dniNumber": post['pse_billing_partner_document'],
            "billingAddress": {
                "street1": post['pse_partner_street'],
                "street2": "",
                "city": partner.zip_id.city_id.name,
                "state": partner.zip_id.city_id.state_id.name,
                "country": "CO",
                "postalCode": partner.zip_id.name,
                "phone": post['pse_partner_phone']
            }
        }
        extraParameters = {
            "RESPONSE_URL": str(http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')) + '/shop/payment/payulatam-gateway-api/response_recurring',
            "PSE_REFERENCE1": request.httprequest.environ['REMOTE_ADDR'],
            "FINANCIAL_INSTITUTION_CODE": post['pse_bank'],
            "USER_TYPE": post['pse_person_type'],
            "PSE_REFERENCE2": post['pse_partner_type'],
            "PSE_REFERENCE3": post['pse_partner_document']
        }   
        order_api = {
            "accountId": accountId,
            "referenceCode": referenceCode,
            "description": descriptionPay,
            "language": "es",
            "signature": signature,
            #"notifyUrl": "https://easytek-confacturacion-2123332.dev.odoo.com/shop/payment/payulatam-gateway-api/response",
            "additionalValues": additionalValues,
            "buyer": buyer,
            "shippingAddress": shippingAddress
        }
        transaction = {
            "order": order_api,
            "payer": payer,
            "extraParameters": extraParameters,
            "type": "AUTHORIZATION_AND_CAPTURE",
            "paymentMethod": "PSE",
            "paymentCountry": "CO",
            "deviceSessionId": request.httprequest.cookies.get('session_id'),
            "ipAddress": request.httprequest.environ['REMOTE_ADDR'],
            "cookie": request.httprequest.cookies.get('session_id'),
            "userAgent": "Firefox"
        }
        pse_values = {
            "command": "SUBMIT_TRANSACTION",
            "transaction": transaction,
        }
        response = request.env['api.payulatam'].payulatam_credit_cards_payment_request(pse_values)
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
                <b><span style='color:red;'>PayU Latam - Error en pago con PSE</span></b><br/>
                <b>Código:</b> %s<br/>
                <b>Error:</b> %s
            """ % (
                response['code'],
                "Error de comunicación con PayU Latam"
            )
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        if response['transactionResponse']['state'] == 'APPROVED':
            sale_order.write({
                'payment_method_type': 'PSE',
            })
            origin_document.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'PSE',
                'payulatam_datetime': fields.datetime.now(),
            })
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
                <b><span style='color:green;'>PayU Latam - Transacción de pago con PSE</span></b><br/>
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
            origin_document.message_post(body=body_message, type="comment")
            return request.render("web_sale_extended.payu_transaction_response", render_values)
        elif response['transactionResponse']['state'] == 'PENDING':
            origin_document.write({
                'payulatam_order_id': response['transactionResponse']['orderId'],
                'payulatam_transaction_id': response['transactionResponse']['transactionId'],
                'payulatam_state': response['transactionResponse']['state'],
                'payment_method_type': 'PSE',
                'payulatam_datetime': fields.datetime.now(),
            })
            render_values = {'error': ''}
            render_values.update({
                'website_sale_order': sale_order,
                'amount': amount,
                'image': '/web_sale_extended/static/src/images/Img_warning.png',
                'responseMessage': 'Estamos procesando tu pago por PSE gracias a la tecnología de PayU',
                'colorResponseMessage': '#FF7800',
                'state': 'Estado: PENDIENTE',
                'coloresState': '#FF7800',
                'bank_url': response['transactionResponse']['extraParameters']['BANK_URL'],
                'url': 'https://masmedicos.co',
                'messageButton': 'Gracias por tu pago',
                'messagePayment' : 'Pago Pendiente'
            })
            body_message = """
                <b><span style='color:orange;'>PayU Latam - Transacción de pago con PSE</span></b><br/>
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
                'payment_method_type': 'PSE',
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
                <b><span style='color:red;'>PayU Latam - Transacción de pago con PSE</span></b><br/>
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
            error = 'Se recibió un estado no reconocido para el pago de PayU Latam %s: %s, set as error' % (
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