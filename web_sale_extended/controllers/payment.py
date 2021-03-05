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
    
    
    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :
         - a draft sales order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False

        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')
            
        mode = (False, False)
        country = request.env['res.country'].browse(49)
        credit_card_due_year_ids = list(range(2021, 2061))
        
        render_values.update({
            'error' : [],
            'mode' : mode,
            'cities' : [],
            'country': request.env['res.country'].browse(int(49)),
            'country_states' : country.get_website_sale_states(mode=mode[1]),
            'countries': country.get_website_sale_countries(mode=mode[1]),
            'credit_card_due_year_ids': credit_card_due_year_ids,
        })
        return request.render("website_sale.payment", render_values)
    
    
    
     
    @http.route(['/shop/payment/payulatam-gateway-api'], type='http', auth="public", website=True, sitemap=False)
    def payulatam_gateway_api(self, **post):
        
        _logger.error('*********************77777777777777777777777777777777777777**********************')
        
        #haciendo ping payu
        provider = 'https://sandbox.api.payulatam.com/reports-api/4.0/service.cgi'
        payulatam_merchant_id = '508029'
        payulatam_account_id = '512321'
        payulatam_api_key = '4Vj8eK4rloUd272L48hsrarnUA'
        payulatam_login = 'pRRXKOl8ikMmt9u'
        
        ping = {
           "test": True,
           "language": "en",
           "command": "PING",
           "merchant": {
              "apiLogin": payulatam_login,
              "apiKey": payulatam_api_key
           }
        }
        auth = HTTPBasicAuth('apikey', payulatam_api_key)
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(provider, json=ping, auth=HTTPBasicAuth('apikey', payulatam_api_key), headers=headers)
        if response.status_code != 200:
            _logger.error(f'****** ERROR {response.status_code}: validation failed, {response.json()}. ******')
            response.close
            response = response.json()
        else:
            response.close
            response = response.json()
            
        if response['code'] != 'SUCCESS':
            _logger.error(f'****** ERROR PING RESPUESTA INVALIDA ******')
        else:
            _logger.error(f'****** ENVIANDO TRANSACCIÓN DE PAGO ******')

            #_logger.error(request.session.get('session_id'))
            #_logger.error(request.httprequest.cookies)
            order = request.website.sale_get_order()
            
            
            
            merchant = {
                "apiKey": payulatam_api_key,
                "apiLogin": payulatam_login
            }
            
            tx_value = {
                "value": order.amount_total,
                "currency": "COP"
            }
            tx_tax = {
                "value": order.amount_total / 1.19,
                "currency": "COP"
            }
            tx_tax_return_base = {
                "value": order.amount_total,
                "currency": "COP"
            }
            
            
            data_string = ('~').join((payulatam_api_key, payulatam_merchant_id, str(order.id),
                                      str(tx_value['value']), tx_value['currency']))
            
            data_string = md5(data_string.encode('utf-8')).hexdigest()
            
            additionalValues = {
                "TX_VALUE": {
                   "value": order.amount_total,
                   "currency": "COP"
                },
                "TX_TAX": {
                   "value": order.amount_total / 1.19,
                   "currency": "COP"
                },
                "TX_TAX_RETURN_BASE": {
                   "value": order.amount_total,
                   "currency": "COP"
                }
            }

            
            shippingAddress = {
                "street1": order.partner_id.street,
                "street2": "",
                "city": "Medellin",
                "state": "Antioquia",
                "country": "CO",
                "postalCode": order.partner_id.zip_id.name,
                "phone": order.partner_id.street
            }
            
            buyer = {
                "merchantBuyerId": "1",
                "fullName": order.partner_id.name,
                "emailAddress": order.partner_id.email,
                "contactPhone": order.partner_id.phone,
                "dniNumber": order.partner_id.identification_document,
                "shippingAddress": shippingAddress            }
            
            order_api = {
                "accountId": "512321",
                "referenceCode": order.id,
                "description": "payment test",
                "language": "es",
                "signature": data_string,
                "notifyUrl": "https://easytek-confacturacion-2123332.dev.odoo.com/shop/payment/payulatam-gateway-api/response",
                "additionalValues": additionalValues,
                "buyer": buyer,
                "shippingAddress": shippingAddress
            }
            
            billingAddressPayer = {
                "street1": post['credit_card_partner_street'],
                "street2": "",
                "city": "Bogota",
                "state": "Bogota DC",
                "country": "CO",
                "postalCode": "000000",
                "phone": post['credit_card_partner_phone']
            }
            
            payer = {
                "merchantPayerId": "1",
                "fullName": post['credit_card_billing_firstname'] + ' ' + post['credit_card_billing_lastname'],
                "emailAddress": post['credit_card_billing_email'],
                "contactPhone": post['credit_card_partner_phone'],
                "dniNumber": '234234234234234',
                "billingAddress": post['credit_card_partner_street']
            }

            credit_card = {
                "number": "",
                "securityCode": "123",
                "expirationDate": "2021/12",
                "name": "REJECTED"
            }
            
            transaction = {
                "order": order_api,
                "payer": payer,
                "creditCard": credit_card,
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": "VISA",
                "paymentCountry": "CO",
                "deviceSessionId": request.httprequest.cookies.get('session_id'),
                "ipAddress": "127.0.0.1",
                "cookie": "pt1t38347bs6jc9ruv2ecpv7o2",
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101"
            }

            credit_card_values = {
                "test": True,
                "language": "es",
                "command": "SUBMIT_TRANSACTION",
                "merchant": merchant,
                "transaction": transaction,
             }
            
            _logger.error(credit_card_values)
            
            
            nuevo = {
               "language": "es",
               "command": "SUBMIT_TRANSACTION",
               "merchant": {
                  "apiKey": "4Vj8eK4rloUd272L48hsrarnUA",
                  "apiLogin": "pRRXKOl8ikMmt9u"
               },
               "transaction": {
                  "order": {
                     "accountId": "512321",
                     "referenceCode": "TestPayU",
                     "description": "payment test",
                     "language": "es",
                     "signature": "7ee7cf808ce6a39b17481c54f2c57acc",
                     "notifyUrl": "http://www.tes.com/confirmation",
                     "additionalValues": {
                        "TX_VALUE": {
                           "value": 20000,
                           "currency": "COP"
                         }
                     },
                     "buyer": {
                        "merchantBuyerId": "1",
                        "fullName": "First name and second buyer  name",
                        "emailAddress": "buyer_test@test.com",
                        "contactPhone": "7563126",
                        "dniNumber": "11233206",
                        "shippingAddress": {
                           "street1": "calle 100",
                           "street2": "5555487",
                           "city": "Medellin",
                           "state": "Antioquia",
                           "country": "CO",
                           "postalCode": "000000",
                           "phone": "7563126"
                        }
                     },
                     "shippingAddress": {
                        "street1": "calle 100",
                        "street2": "5555487",
                        "city": "Medellin",
                        "state": "Antioquia",
                        "country": "CO",
                        "postalCode": "0000000",
                        "phone": "7563126"
                     }
                  },
                  "payer": {
                     "merchantPayerId": "1",
                     "fullName": "First name and second payer name",
                     "emailAddress": "payer_test@test.com",
                     "contactPhone": "7563126",
                     "dniNumber": "11233206",
                     "billingAddress": {
                        "street1": "calle 93",
                        "street2": "125544",
                        "city": "Bogota",
                        "state": "Bogota DC",
                        "country": "CO",
                        "postalCode": "000000",
                        "phone": "7563126"
                     }
                  },
                  "creditCard": {
                     "number": '4111111111111111',
                     "securityCode": "666",
                     "expirationDate": "2021-12",
                     "name": "REJECTED"
                  },
                  "extraParameters": {
                     "INSTALLMENTS_NUMBER": 1
                  },
                  "type": "AUTHORIZATION_AND_CAPTURE",
                  "paymentMethod": "VISA",
                  "paymentCountry": "CO",
                  "deviceSessionId": request.httprequest.cookies.get('session_id'),
                  "ipAddress": socket.gethostbyname(hostname),
                  "cookie": "vghs6tvkcle931686k1900o6e1",
                  "userAgent": "Mozilla/5.0 (Windows NT 5.1; rv:18.0) Gecko/20100101 Firefox/18.0"
               },
               "test": "True"
            }
            
            nuevo = json.dumps(nuevo)
            _logger.error(nuevo)
            
            
            nuevo = {
               "language": "es",
               "command": "SUBMIT_TRANSACTION",
               "merchant": {
                  "apiKey": "4Vj8eK4rloUd272L48hsrarnUA",
                  "apiLogin": "pRRXKOl8ikMmt9u"
               },
               "transaction": {
                  "order": {
                     "accountId": "512322",
                     "referenceCode": "payment_test_00000001",
                     "description": "payment test",
                     "language": "es",
                     "signature": "95d7e92b23cae0cae6a98e34cc54be39",
                     "notifyUrl": "http://www.tes.com/confirmation",
                     "additionalValues": {
                        "TX_VALUE": {
                           "value": 100,
                           "currency": "ARS"
                        }
                     },
                     "buyer": {
                        "merchantBuyerId": "1",
                        "fullName": "First name and second buyer  name",
                        "emailAddress": "buyer_test@test.com",
                        "contactPhone": "7563126",
                        "dniNumber": "5415668464654",
                        "shippingAddress": {
                           "street1": "Viamonte",
                           "street2": "1366",
                           "city": "Buenos Aires",
                           "state": "Buenos Aires",
                           "country": "AR",
                           "postalCode": "000000",
                           "phone": "7563126"
                        }
                     },
                     "shippingAddress": {
                        "street1": "Viamonte",
                        "street2": "1366",
                        "city": "Buenos Aires",
                        "state": "Buenos Aires",
                        "country": "AR",
                        "postalCode": "0000000",
                        "phone": "7563126"
                     }
                  },
                  "payer": {
                     "merchantPayerId": "1",
                     "fullName": "First name and second payer name",
                     "emailAddress": "payer_test@test.com",
                     "contactPhone": "7563126",
                     "dniNumber": "5415668464654",
                     "billingAddress": {
                        "street1": "Avenida entre rios",
                        "street2": "452",
                        "city": "Plata",
                        "state": "Buenos Aires",
                        "country": "AR",
                        "postalCode": "64000",
                        "phone": "7563126"
                     }
                  },
                  "creditCard": {
                     "number": "4850110000000000",
                     "securityCode": "321",
                     "expirationDate": "2014/12",
                     "name": "REJECTED"
                  },
                  "extraParameters": {
                     "INSTALLMENTS_NUMBER": 1
                  },
                  "type": "AUTHORIZATION_AND_CAPTURE",
                  "paymentMethod": "VISA",
                  "paymentCountry": "AR",
                  "deviceSessionId": "vghs6tvkcle931686k1900o6e1",
                  "ipAddress": "127.0.0.1",
                  "cookie": "pt1t38347bs6jc9ruv2ecpv7o2",
                  "userAgent": "Mozilla/5.0 (Windows NT 5.1; rv:18.0) Gecko/20100101 Firefox/18.0"
               },
               "test": "true"
            }
            
            
            #response = requests.post(provider, json=nuevo, auth=HTTPBasicAuth('apikey', payulatam_api_key), headers=headers)
            #response = []
            response = {
               "code": "SUCCESS",
               "error": '',
               "status_code": 200,
               "transactionResponse": {
                  "orderId": 3018500,
                  "transactionId": "b5369274-4b51-4cd3-a634-61db79b3eb9c",
                  "state": "APPROVED",
                  "paymentNetworkResponseCode": '',
                  "paymentNetworkResponseErrorMessage": '',
                  "trazabilityCode": "00000000",
                  "authorizationCode": "00000000",
                  "pendingReason": '',
                  "responseCode": "APPROVED",
                  "errorCode": '',
                  "responseMessage": '',
                  "transactionDate": '',
                  "transactionTime": '',
                  "operationDate": 1393966959622,
                  "extraParameters": ''
               }
            }
            _logger.error(response)
            """
            #if response.status_code != 200:
            if response['status_code'] != 200:
                _logger.error(f'****** 200 no valido ******')
                
                response.close
                response = response.json()
                #_logger.error(response)
            else:
                response.close
                response = response.json()

            if response['code'] != 'APPROVED':
                _logger.error(f'****** TRANSACCION APPROVED ******')
                _logger.error(response)
            else:
                _logger.error(response)
            """
            render_values = {}
            if response['status_code'] == 200:
                render_values.update({
                    'error' : [],
                    'code' : 'SUCCESS',
                    'message': '¡El pago ha sido realizado exitosamente!',
                    'order_id': order.id
                })
                _logger.error('99999922222222222222222222211111111111111111111111111111111111111111111111')
                _logger.error(render_values)
                if order.action_confirm():
                    return request.render("web_sale_extended.payulatam_success_process", render_values)
                else:
                    return request.render("web_sale_extended.payulatam_rejected_process", render_values)
                    
                    
   



    @http.route(['/shop/payment/payulatam-gateway-api/cash_process'], type='http', auth="public", website=True, sitemap=False)
    def payulatam_gateway_api_cash(self, **post):

        provider = 'https://sandbox.api.payulatam.com/reports-api/4.0/service.cgi'
        payulatam_merchant_id = '508029'
        payulatam_account_id = '512321'
        payulatam_api_key = '4Vj8eK4rloUd272L48hsrarnUA'
        payulatam_login = 'pRRXKOl8ikMmt9u'
        
        ping = {
           "test": True,
           "language": "en",
           "command": "PING",
           "merchant": {
              "apiLogin": payulatam_login,
              "apiKey": payulatam_api_key
           }
        }
        auth = HTTPBasicAuth('apikey', payulatam_api_key)
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(provider, json=ping, auth=HTTPBasicAuth('apikey', payulatam_api_key), headers=headers)
        if response.status_code != 200:
            _logger.error(f'****** ERROR {response.status_code}: validation failed, {response.json()}. ******')
            response.close
            response = response.json()
        else:
            response.close
            response = response.json()
            
        if response['code'] != 'SUCCESS':
            _logger.error(f'****** ERROR PING RESPUESTA INVALIDA ******')
        else:
            _logger.error(f'****** ENVIANDO TRANSACCIÓN DE PAGO ******')
            order = request.website.sale_get_order()
            
        
            response = {
               "code": "SUCCESS",
               "error": '',
               "status_code": 200,
               "transactionResponse": {
                  "orderId": 3018500,
                  "transactionId": "b5369274-4b51-4cd3-a634-61db79b3eb9c",
                  "state": "APPROVED",
                  "paymentNetworkResponseCode": '',
                  "paymentNetworkResponseErrorMessage": '',
                  "trazabilityCode": "00000000",
                  "authorizationCode": "00000000",
                  "pendingReason": '',
                  "responseCode": "APPROVED",
                  "errorCode": '',
                  "responseMessage": '',
                  "transactionDate": '',
                  "transactionTime": '',
                  "operationDate": 1393966959622,
                  "extraParameters": ''
               }
            }
        
        
        
            render_values = {}
            if response['status_code'] == 200:
                render_values.update({
                    'error' : [],
                    'code' : 'SUCCESS',
                    'message': '¡El pago ha sido realizado exitosamente!',
                    'order_id': order.id
                })
                _logger.error('99999922222222222222222222211111111111111111111111111111111111111111111111')
                _logger.error(render_values)
                if order.action_confirm():
                    return request.render("web_sale_extended.payulatam_success_process_cash", render_values)
                else:
                    return request.render("web_sale_extended.payulatam_rejected_process_cash", render_values)
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
    @http.route(['/shop/payment/payulatam-gateway-api/pse_process'], type='http', auth="public", website=True, sitemap=False)
    def payulatam_gateway_api_pse(self, **post):

        provider = 'https://sandbox.api.payulatam.com/reports-api/4.0/service.cgi'
        payulatam_merchant_id = '508029'
        payulatam_account_id = '512321'
        payulatam_api_key = '4Vj8eK4rloUd272L48hsrarnUA'
        payulatam_login = 'pRRXKOl8ikMmt9u'
        
        ping = {
           "test": True,
           "language": "en",
           "command": "PING",
           "merchant": {
              "apiLogin": payulatam_login,
              "apiKey": payulatam_api_key
           }
        }
        auth = HTTPBasicAuth('apikey', payulatam_api_key)
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(provider, json=ping, auth=HTTPBasicAuth('apikey', payulatam_api_key), headers=headers)
        if response.status_code != 200:
            _logger.error(f'****** ERROR {response.status_code}: validation failed, {response.json()}. ******')
            response.close
            response = response.json()
        else:
            response.close
            response = response.json()
            
        if response['code'] != 'SUCCESS':
            _logger.error(f'****** ERROR PING RESPUESTA INVALIDA ******')
        else:
            _logger.error(f'****** ENVIANDO TRANSACCIÓN DE PAGO ******')
            order = request.website.sale_get_order()
            
        
            response = {
               "code": "SUCCESS",
               "error": '',
               "status_code": 200,
               "transactionResponse": {
                  "orderId": 3018500,
                  "transactionId": "b5369274-4b51-4cd3-a634-61db79b3eb9c",
                  "state": "APPROVED",
                  "paymentNetworkResponseCode": '',
                  "paymentNetworkResponseErrorMessage": '',
                  "trazabilityCode": "00000000",
                  "authorizationCode": "00000000",
                  "pendingReason": '',
                  "responseCode": "APPROVED",
                  "errorCode": '',
                  "responseMessage": '',
                  "transactionDate": '',
                  "transactionTime": '',
                  "operationDate": 1393966959622,
                  "extraParameters": ''
               }
            }
        
        
        
            render_values = {}
            if response['status_code'] == 200:
                render_values.update({
                    'error' : [],
                    'code' : 'SUCCESS',
                    'message': '¡El pago ha sido realizado exitosamente!',
                    'order_id': order.id
                })
                _logger.error('99999922222222222222222222211111111111111111111111111111111111111111111111')
                _logger.error(render_values)
                if order.action_confirm():
                    return request.render("web_sale_extended.payulatam_success_process_pse", render_values)
                else:
                    return request.render("web_sale_extended.payulatam_rejected_process_pse", render_values)