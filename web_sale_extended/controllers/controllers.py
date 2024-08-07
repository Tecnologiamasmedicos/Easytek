# -*- coding: utf-8 -*-
import json
import logging, base64
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import Forbidden, NotFound
import werkzeug.utils
import werkzeug.wrappers
from odoo.exceptions import AccessError, MissingError, UserError
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.osv import expression
from Crypto.Cipher import AES
from base64 import b64encode
import time, os

from odoo import api, fields, models, _
from odoo.tools import ustr, consteq, float_compare
import hashlib
import hmac

_logger = logging.getLogger(__name__)


class WebsiteSaleExtended(WebsiteSale):

    def encrypt_aes_gcm(self, msg, secretkey=None):
        secretkey = os.urandom(32) if not secretkey else secretkey
        msg = bytes(msg, 'utf-8')
        aes_cipher = AES.new(secretkey, AES.MODE_GCM)
        ciphertext, auth_tag = aes_cipher.encrypt_and_digest(msg)
        return ciphertext, aes_cipher.nonce, auth_tag, secretkey

    def generate_access_token(self, order_id):        
        order = request.env['sale.order'].sudo().browse(order_id)
        secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        token_str = '%s%s%s' % (order.partner_id.id, order.amount_total, order.currency_id.id)
        access_token = hmac.new(secret.encode('utf-8'), token_str.encode('utf-8'), hashlib.sha256).hexdigest()
        return access_token
    
    
    def generate_link(self, order_id):        
        token = self.generate_access_token(order_id)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = ('%s/shop/payment/assisted_purchase/%s?access_token=%s') % (
            base_url,
            order_id,
            token
        )        
        return link

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':
            _logger.info("****CREANDO TERCERO NUEVO*****")
            _logger.info(checkout)
            #zip_id = checkout.pop('zip_id')
            if "name" in checkout:
                checkout.pop('name')
            partner_id = Partner.sudo().with_context(tracking_disable=True, skip_check_zip=True).create(checkout)
            #partner_id.write({'zip_id': zip_id})
        elif mode[0] == 'edit':
            _logger.info("****EDITANDO TERCERO*****")
            _logger.info(checkout)
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
                    return Forbidden()
                if "zip" in checkout:
                    checkout.pop('zip')
                if "city" in checkout:
                    checkout.pop('city')
                if "user_id" in checkout:
                    checkout.pop('user_id')
                if "name" in checkout:
                    checkout.pop('name')
                if "zip_id" in checkout:
                    checkout.update({'zip_id': int(checkout['zip_id'])})
                if "state_address_id" in checkout:
                    checkout.update({'state_id': int(checkout['state_address_id'])})
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    @http.route(['/shop/tusdatos_request_confirmation'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def tusdatos_request_confirmation(self, **kw):
        order = request.website.sale_get_order()
        #redirection = self.checkout_redirection(order)
        #if redirection:
        #    return redirection
        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        extra_step = request.website.viewref('website_sale.extra_info_option')
        if extra_step.active:
            return request.redirect("/shop/extra_info")
        render_values = {
            'order': order,
        }
        return request.render("web_sale_extended.tusdatos_request_confirmation", render_values)
    
    
    
    def checkout_form_validate(self, mode, all_form_values, data):
        # mode: tuple ('new|edit', 'billing|shipping')
        # all_form_values: all values before preprocess
        # data: values after preprocess
        error = dict()
        error_message = []
        
        
        _logger.info("****ID Pais fieldname*****")
        _logger.info(data.get('country_address_id'))
        _logger.info("****Dataaa fieldname*****")
        _logger.info(data)
        

        # Required fields from form
        required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]
        # Required fields from mandatory field function
        required_fields += mode[1] == 'shipping' and self._get_mandatory_shipping_fields() or self._get_mandatory_billing_fields()
        # Check if state required
        country = request.env['res.country']
        if data.get('country_address_id'):
            country = country.browse(int(data.get('country_address_id')))
            if 'state_code' in country.get_address_fields() and country.state_ids:
                required_fields += ['state_address_id']

        # error message for empty required fields
        for field_name in required_fields:
            if field_name == 'country_id':
                field_name = 'country_address_id'
            elif field_name == 'state_id':
                if int(data.get('country_address_id')) == 49:
                    field_name = 'state_address_id'
                else:
                    field_name = 'state_id_text'
            elif field_name == 'city':
                if int(data.get('country_address_id')) == 49:
                    field_name = 'state_address_id'
                else:
                    field_name = 'city'
            if not data.get(field_name):
                error[field_name] = 'missing'
                _logger.info("****Error fieldname*****")
                _logger.info(field_name)

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        # vat validation
        Partner = request.env['res.partner']
        if data.get("vat") and hasattr(Partner, "check_vat"):
            if data.get("country_address_id"):
                data["vat"] = Partner.fix_eu_vat_number(data.get("country_address_id"), data.get("vat"))
            partner_dummy = Partner.new({
                'vat': data['vat'],
                'country_id': (int(data['country_address_id'])
                               if data.get('country_address_id') else False),
            })
            try:
                partner_dummy.check_vat()
            except ValidationError:
                error["vat"] = 'error'

        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        return error, error_message
    
    
    
    
    

    # toma de datos de pago y se crea el asegurador principal
    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, errortusdatos= '', **kw):
        qcontext = ''
        params = {}
        assisted_purchase = 0
        if 'assisted_purchase' in request.params and request.params['assisted_purchase']:
            assisted_purchase = request.params['assisted_purchase']
            params["assisted_purchase"] = assisted_purchase
        if request.params.get('_ga'):
            ag = request.params['_ga']
            params["_ga"] = ag
        if request.params.get('_gl'):
            gl = request.params['_gl']
            params["_gl"] = gl
        if params:
            params = [f"{param}={value}" for param, value in params.items()]
            qcontext = "?" + "&".join(params)
        if request.params.get('qcontext'):
            qcontext = request.params['qcontext']

        ''' Toma de datos de pago y se crea el asegurador principal '''
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()
        order_detail = request.env['sale.order.line'].sudo().search([('order_id', "=", int(order.id))])
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        def_country_id = order.partner_id.country_id
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))
        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
            else:
                def_country_id = request.website.user_id.sudo().country_id
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else:# no mode - refresh without post?
                _logger.info("****FORMULARIO PAGO!!!!!*****")
                return request.redirect('/shop/checkout%s' % qcontext)

        # IF POSTED
        if 'submitted' in kw:
            if int(assisted_purchase) == 1:
                order.write({'assisted_purchase': True})
            if 'type_payment' in kw and int(assisted_purchase) == 1 and order_detail.product_id.is_beneficiary:
                order.write({
                    'benefice_payment_method': kw['type_payment'],
                    'payment_method_type': 'Product Without Price'
                })
            if 'bancolombia_types_account' in kw:
                encrypt_msg = self.encrypt_aes_gcm(kw['account_number'])
                ciphertext = b64encode(encrypt_msg[0]).decode('utf-8')
                nonce = b64encode(encrypt_msg[1]).decode('utf-8')
                auth_tag = b64encode(encrypt_msg[2]).decode('utf-8')
                secretkey = b64encode(encrypt_msg[3]).decode('utf-8')
                order.write({
                    'buyer_account_type': kw['bancolombia_types_account'],
                    'buyer_account_number': ciphertext,
                    'nonce': nonce,
                    'auth_tag': auth_tag,
                    'secretkey': secretkey
                })
            order.write({'tusdatos_email': kw['email']})
            _logger.info("****FORMULARIO*****")
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            _logger.info(errors)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)
            _logger.info(errors)
            if errors:
                _logger.info("****con errores*****")
                errors['error_message'] = error_msg
                values = kw
            else:
                _logger.info("****sin errores*****")
                if kw['othernames'] == '':
                    post['othernames'] = ''
                else:
                    post['othernames'] = kw['othernames'].strip()
                
                post['firstname'] = kw['name'].strip()
                post['lastname'] = kw['lastname'].strip()
                post['lastname2'] = kw['lastname2'].strip()
                post['document_type_id'] = int(kw["document"])
                post['person_type'] = "2"
                post['identification_document'] = kw["identification_document"]
                post["birthdate_date"] = kw["birthdate_date"]
                #post["city_id"] = kw["city"]
                post["country_id"] = int(kw["country_address_id"])
                
                post["buyer"] = True

                phone_form = kw['phone']
                phone_form = phone_form.split(')')
                number = phone_form[-1].strip()
                phone_code_country = request.env['res.country'].sudo().search([('id', '=', int(kw['country_address_id']))], limit=1)
                if len(number) == 7:                    
                    post["phone"] = '(+' + str(phone_code_country.phone_code) + ') ' + str(kw["phone"])
                    post["mobile"] = ''
                elif len(number) == 10:
                    post["mobile"] = '(+' + str(phone_code_country.phone_code) + ') ' + str(kw["phone"])
                    post["phone"] = ''
                
                if kw['country_address_id'] =='49':                    
                    post["zip"] = kw["zip"]
                    post["zip_id"] = kw["zip_id"]
                    post["state_id"] = int(kw["state_address_id"])                    
                else:
                    post["state_2"] = kw["state_id_text"]
                    post["city_2"] = kw["city_id_text"]
                if 'estado_civil' in kw:
                    post["marital_status"] = kw["estado_civil"]
                if 'expedition_date' in kw:
                    _logger.error(kw["expedition_date"])
                    post["expedition_date"] = kw["expedition_date"]
                if 'relationship' in kw:
                    post["relationship"] = kw["relationship"]

                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                order.write({'require_signature': False, 'require_payment': True,})
                if not errors:
                    if not order.tusdatos_request_id:
                        document_types = {'3': 'CC', '5':'CE', '8':'PEP', '7':'PP', '16':'CD'}
                        order.write({'tusdatos_typedoc': document_types[str(kw["document"])]})  
                            
                        render_values = {'email': kw['email'],}
                        return request.redirect(kw.get('callback%s' % qcontext) or ('/shop/confirm_order%s' % qcontext))
                        #if not errors:
                        #    return request.redirect('/shop/tusdatos_request_confirmation')
                    elif not order.tusdatos_approved and order.tusdatos_request_id:
                        _logger.info("\n****TUS DATOS ORDER2*****\n")
                        return request.redirect(kw.get('callback%s' % qcontext) or ('/shop/confirm_order%s' % qcontext))
                        #return request.redirect('/shop/tusdatos_request_confirmation')

                    if not errors:
                        return request.redirect(kw.get('callback%s' % qcontext) or ('/shop/confirm_order%s' % qcontext))

        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
        country = country and country.exists() or def_country_id
        fiscal_position_ids = request.env['account.fiscal.position'].sudo().search([
            ('active', '=', True),
            ('website_published', '=', True),
        ])
        
        if errortusdatos:
            _logger.error(errortusdatos)
            errors['error_message'] = errortusdatos
        
        if 'name' in values and values['name']:
            values = values
        elif order:
            values.update({
                'name': order.partner_id.firstname,
                'firstname': order.partner_id.firstname,
                'othernames': order.partner_id.othernames,
                'lastname': order.partner_id.lastname,
                'lastname2': order.partner_id.lastname2,
                'email': order.partner_id.email,
                'phone': order.partner_id.phone,
                'birthdate_date': order.partner_id.birthdate_date,
                'street': order.partner_id.street,
                'expedition_date': order.partner_id.expedition_date,
            })
        
        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'country': country,
            'country_states': country.get_website_sale_states(mode=mode[1]),
            'countries': country.get_website_sale_countries(mode=mode[1]),
            'fiscal_position_ids': fiscal_position_ids,
            'error': errors,
            'callback': kw.get('callback'),
            #'cities': self.get_cities(),
            'cities': [],
            'document_types': self.get_document_types('payment'),
            'payment_types': self.get_payment_types('beneficio'),
            'bancolombia_types_account': self.get_bancolombia_types_account(),
            'product': request.env['product.template'].sudo().browse(order_detail.product_id.id),
            # 'fiscal_position': self.get_fiscal_position(),
            'only_services': order and order.only_services,
            'order_detail': order_detail,
            'assisted_purchase': assisted_purchase,
            'qcontext': qcontext,
        }
        if order_detail.product_id.categ_id.buyer_view:
            return request.render(order_detail.product_id.categ_id.buyer_view.xml_id, render_values)
        else:
            return request.render("web_sale_extended.address", render_values)
    

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def confirm_order(self, **post):
        params = dict(request.params)
        assisted_purchase = 0
        params = [f"{param}={value}" for param, value in params.items()]
        qcontext = "&" + "&".join(params)
        
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        extra_step = request.website.viewref('website_sale.extra_info_option')
        if extra_step.active:
            return request.redirect("/shop/extra_info")
        
        """ Evaluando si es una venta asistida """
        if 'assisted_purchase' in request.params and request.params['assisted_purchase']:
            body_message = """
                <b><span style='color:green;'>PayU Latam - VENTA ASISTIDA </span></b><br/>
                Se ha iniciado una transacción de venta asistida y el usuario ha sido redirigido al formulario 
                para el registro de Asegurado y Beneficiarios<br/>
            """
            order.message_post(body=body_message, type="comment")
            return request.redirect("/my/order/beneficiaries/" + str(order.id) + '?access_token=' + str(self.generate_access_token(order.id)) + qcontext)
        
        """ Evaluando si el producto es un beneficio """
        if order.main_product_id.is_beneficiary:
            order.write({
                'payment_method_type': 'Product Without Price',
            })
            body_message = """
                <b><span style='color:green;'>PayU Latam - Producto de beneficio</span></b><br/>
                Se ha iniciado una transacción con Producto un producto de beneficio y el usuario ha sido redirigido al formulario 
                para el registro de Asegurado y Beneficiarios<br/>
            """
            order.message_post(body=body_message, type="comment")
            return request.redirect("/my/order/beneficiaries/" + str(order.id) + '?access_token=' + str(self.generate_access_token(order.id)) + qcontext)
        if order.main_product_id.categ_id.sponsor_id.id == 5521:
            return request.redirect("/my/order/beneficiaries/" + str(order.id) + '?access_token=' + str(self.generate_access_token(order.id)) + qcontext)
        return request.redirect("/shop/payment")
    
    
    def get_cities(self, department=None):
        ''' LISTADOS DE TODAS LAS CIUDADES '''
        domain = []
        if department:
            domain.append(('city_id.state_id', '=', department))
        complete_cities_with_zip = request.env['res.city.zip'].sudo().search(domain)
        return complete_cities_with_zip

    def get_document_types(self, type='All'):
        ''' LISTADOS DE TODOS LOS TIPOS DE DOCUMENTO '''
        if type == "payment":
            document_type = request.env['res.partner.document.type'].sudo().search([
                ('id','not in',[11,1,2,4,6,10,9,12]),
            ], order='name')
        elif type == "beneficiary":
            document_type = request.env['res.partner.document.type'].sudo().search([
                ('id','not in',[4,6,10,9,12]),
            ], order='name')
        else:
            document_type = request.env['res.partner.document.type'].sudo().search([], order='name')
        return document_type

    def get_payment_types(self, type='All'):
        if type == 'beneficio':
            payment_type = (dict(request.env['sale.order'].fields_get(allfields=['benefice_payment_method'])['benefice_payment_method']['selection']))
        else:
            payment_type = (dict(request.env['sale.order'].fields_get(allfields=['payment_method_type'])['payment_method_type']['selection']))
        return payment_type

    def get_bancolombia_types_account(self):
        bancolombia_types_account = (dict(request.env['sale.order'].fields_get(allfields=['buyer_account_type'])['buyer_account_type']['selection']))
        return bancolombia_types_account

    @http.route(['/my/order/beneficiaries/<int:order_id>'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def get_data_beneficiary(self, order_id, access_token=None, **kwargs):        
        if order_id:        
            correct_token = self.generate_access_token(order_id)
            if consteq(ustr(access_token), correct_token):
                ''' Captura de datos del beneficiario más no guarda informacion '''
                order = request.env['sale.order'].sudo().browse(order_id)
                if order.state == 'sale':
                    redirection = self.checkout_redirection(order)
                    if redirection:
                        return redirection

                product = order.order_line[0].product_id

                if product.sequence_id:
                    beneficiaries_number = product.sequence_id.beneficiaries_number
                else:
                    beneficiaries_number = product.categ_id.sequence_id.beneficiaries_number

                if beneficiaries_number > 6:
                    beneficiaries_number = 6

                country = request.env['res.country'].browse(int(order.partner_id.country_id))
                render_values = {
                    "partner": order.partner_id,
                    'country_states': request.env['res.country'].browse(49).get_website_sale_states(),
                    'cities': self.get_cities(1386),
                    'countries': country.get_website_sale_countries().filtered(lambda line: line.id == 49),
                    'document_types': self.get_document_types('beneficiary'),
                    'document_types_main_insured': self.get_document_types('payment'),
                    'country': country,
                    'order_detail': order.order_line[0],
                    'current_city':order.partner_id.zip_id.city_id.id,
                    'beneficiaries_number': beneficiaries_number,
                    'order_id': order.id,
                    'website_sale_order': order
                }
                _logger.info(render_values)
                if order.main_product_id.categ_id.sponsor_id.id == 5521:
                    return request.render("web_sale_extended.beneficiaries_bancolombia", render_values)
                else:
                    return request.render("web_sale_extended.beneficiary", render_values)
            else:
                raise werkzeug.exceptions.NotFound


    @http.route(['/beneficiary-detail'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def create_beneficiary(self, print_policy=0, **kwargs):
        ''' Guarda datos de los beneficiarios y los deja inactivo  '''
        _logger.info("***INFORME BENEFICIARIO***")
        _logger.info(kwargs)

        order = request.website.sale_get_order()
        if not order and kwargs['order_id']:
            order = request.env['sale.order'].sudo().browse(int(kwargs['order_id']))
            
        """ si la orden esta en estado confirmado hay que reenviar a landpage"""
        if order.state == 'sale':
            redirection = self.checkout_redirection(order)
            if redirection:
                return redirection
        order_detail = order.order_line[0]

        if order_detail.product_id.categ_id.sponsor_id:
            sponsor_id = order_detail.product_id.categ_id.sponsor_id

        if 'send_email' in request.params and request.params['send_email']: 
            order._send_payment_link_assisted_purchase_email()
            render_values = {
                'order': order,
            }
            
            return request.render("web_sale_extended.confirm_assisted_purchase", render_values)
        
        if 'send_email_account_registration_Bancolombia' in request.params and request.params['send_email_account_registration_Bancolombia']:
            order.register_bancolombia_account()
            render_values = {
                'order': order,
            }
            return request.render("web_sale_extended.confirm_assisted_purchase_bancolombia", render_values)

        if 'download_documents' in request.params and request.params['download_documents']: 
            render_values = {
                'order_detail': order_detail,
                'website_sale_order': order,
            }
            
            if order.state == 'payu_approved':
                order.action_confirm()
                order._send_order_confirmation_mail()
            return request.render("web_sale_extended.beneficiary_detail", render_values)
        
        Partner = order.partner_id
        BeneficiaryPartner = request.env['res.partner'].sudo()

        if 'infoBuyer' in kwargs:
            Partner.sudo().write({
                'company_type': 'person',
                'active': True,
                'beneficiary_number': 1,
                'beneficiary_country_id': Partner.country_id,
                'beneficiary_state_id': Partner.state_id,
                'beneficiary_zip_id': Partner.zip_id,
                'ocupation': kwargs['ocupation'],
                'gender' : kwargs['sex'],
                'marital_status' : kwargs['estado_civil'],
                'main_insured': True,
                'sponsor_id': sponsor_id.id
            })

            phone_code_country = request.env['res.country'].sudo().search([('id', '=', int(Partner.country_id.id))], limit=1)
        
            if len(kwargs['phone']) > 0:
                Partner.sudo().write({
                    'mobile' : '(+' + str(phone_code_country.phone_code) + ') ' + str(kwargs['phone'])
                })
            
            if len(kwargs['fijo']) > 0:
                 Partner.sudo().write({                    
                    'phone' : '(+' + str(phone_code_country.phone_code) + ') ' + str(kwargs['fijo'])
                })
        
            order.write({
                'beneficiary0_id': Partner.id
            })
        else:
            suggested_zipcode = request.env['res.city.zip'].sudo().search([('city_id', '=', int(kwargs['city']))], limit=1)
            phone_code_country = request.env['res.country'].sudo().search([('id', '=', int(kwargs['country_id']))], limit=1)

            Partner.sudo().write({                
                'sponsor_id': sponsor_id.id,                
            })

            if len(kwargs['phone']) > 0:                
                kwargs['phone'] = '(+' + str(phone_code_country.phone_code) + ') ' + str(kwargs["phone"])
                
            if len(kwargs['fijo']) > 0:
                kwargs['fijo'] = '(+' + str(phone_code_country.phone_code) + ') ' + str(kwargs["fijo"])
            
            NewBeneficiaryPartner = BeneficiaryPartner.create({
                'firstname': kwargs['name'],
                'lastname': kwargs['lastname'],
                'lastname2':kwargs['lastname2'],
                'othernames': kwargs['othername'],
                'email': kwargs['email'],
                'person_type': "2",
                "mobile": kwargs['phone'],
                'phone': kwargs['fijo'],
                'document_type_id': int(kwargs['document_type']),
                'identification_document': kwargs['numero_documento'],
                'company_type': 'person',
                'active': True,
                'parent_id': Partner.id,
                'beneficiary_country_id': int(kwargs['country_id']),
                'beneficiary_state_id': int(kwargs['deparment']),
                'beneficiary_zip_id': suggested_zipcode.id,
                'birthdate_date': kwargs['date'],
                'expedition_date' : kwargs['expedition_date'],
                'marital_status' : kwargs['estado_civil'],
                'ocupation': kwargs['ocupation'],
                'gender': kwargs['sex'],
                'address_beneficiary': kwargs['address'],
                'beneficiary_number': 1,
                'main_insured': True,
                'sponsor_id': sponsor_id.id
            })
            order.write({
                'beneficiary0_id': NewBeneficiaryPartner.id
            })
            
        cont_d, cont_h, cont_c, cont_m, cont_s = 0,0,0,0,0
        for i in range(int(kwargs['beneficiario'])):
            checkBox = "bfCheckBox"+str(i+1)
            if checkBox in kwargs:
                if 'infoBuyer' in kwargs:
                    state_id = Partner.state_id
                    zip_id = Partner.zip_id
                else:                    
                    state_id = kwargs['deparment'] 
                    zip_id = request.env['res.city.zip'].sudo().search([('city_id', '=', int(kwargs['city']))], limit=1)
            else:                
                state_id = kwargs["bfdeparment"+str(i+1)] 
                zip_id = request.env['res.city.zip'].sudo().search([('city_id', '=', int(kwargs["bfcity"+str(i+1)]))], limit=1)
            firtst_name = "bfirstname"+str(i+1)
            other_name = "bfothername"+str(i+1)
            last_name = "bflastname"+str(i+1)
            last_name2 = "bflastname"+str(i+1)+"2"
            email = "bfemail"+str(i+1)
            document_type = "bfdocument"+str(i+1)
            identification_document = "bfnumero_documento"+str(i+1)
            country_id =  "bfcountry_id"+str(i+1)
            birthdate = "bfdate"+str(i+1)
            ocupation = "bfocupacion"+str(i+1)
            gender = "bfsex"+str(i+1)
            relationship = "bfparentesco"+str(i+1)
            address_beneficiary = "bfaddress"+str(i+1)
            phone = "bffijo"+str(i+1)
            mobile = "bfphone"+str(i+1)

            clerk_code = ''
            if kwargs[relationship] == 'C':
                cont_c+=1
                clerk_code = 'C' + str(cont_c)
            elif kwargs[relationship] == 'D':
                cont_d+=1
                clerk_code = 'D' + str(cont_d)
            elif kwargs[relationship] == 'H':
                cont_h+=1
                clerk_code = 'H' + str(cont_h)
            elif kwargs[relationship] == 'M':
                cont_m+=1
                clerk_code = 'M' + str(cont_m)
            elif kwargs[relationship] == 'S':
                cont_s+=1
                clerk_code = 'S' + str(cont_s)


            if kwargs[other_name] == '':
                kwargs[other_name] = ' '
            
            phone_code_country = request.env['res.country'].sudo().search([('id', '=', int(kwargs[country_id]))], limit=1)
                
            if len(kwargs[phone]) > 0:                
               kwargs[phone] = '(+' + str(phone_code_country.phone_code) + ') ' + str(kwargs[phone])
                
            if len(kwargs[mobile]) > 0:
                kwargs[mobile] = '(+' + str(phone_code_country.phone_code) + ') ' + str(kwargs[mobile])
            
            NewBeneficiaryPartner = BeneficiaryPartner.create({
                'firstname': kwargs[firtst_name],
                'lastname': kwargs[last_name],
                'lastname2':kwargs[last_name2],
                'othernames': kwargs[other_name],
                'email': kwargs[email],
                'person_type': "2",
                "phone": kwargs[phone],
                'mobile': kwargs[mobile],
                'document_type_id': int(kwargs[document_type]),
                'identification_document': kwargs[identification_document],
                'company_type': 'person',
                'active': True,
                'parent_id': Partner.id,
                'beneficiary_country_id': int(kwargs[country_id]),
                'beneficiary_state_id': int(state_id),
                'beneficiary_zip_id': zip_id.id,
                'birthdate_date': kwargs[birthdate],
                'ocupation': kwargs[ocupation],
                'gender': kwargs[gender],
                'relationship': kwargs[relationship],
                'address_beneficiary': kwargs[address_beneficiary],
                'beneficiary_number': i+2,
                'beneficiary': True,
                'clerk_code': clerk_code,
                'sponsor_id': sponsor_id.id
            })
            if i == 0:
                order.write({
                    'beneficiary1_id': NewBeneficiaryPartner.id
                })
            if i == 1:
                order.write({
                    'beneficiary2_id': NewBeneficiaryPartner.id
                })
            if i == 2:
                order.write({
                    'beneficiary3_id': NewBeneficiaryPartner.id
                })
            if i == 3:
                order.write({
                    'beneficiary4_id': NewBeneficiaryPartner.id
                })
            if i == 4:
                order.write({
                    'beneficiary5_id': NewBeneficiaryPartner.id
                })
            if i == 5:
                order.write({
                    'beneficiary6_id': NewBeneficiaryPartner.id
                })

        if order.assisted_purchase:
            render_values = {
            'link': self.generate_link(order.id),
            "access_token": order.access_token,            
            'order_detail': order_detail,
            'order': order,
            'website_sale_order': order,
            }
            if order_detail.product_id.is_beneficiary:
                """ Confirmando Orden de Venta luego del proceso exitoso de beneficiarios """
                order.action_confirm()
                if order.sponsor_id != 3225:
                    if (order.subscription_id.template_id.is_fixed_policy and date.today().day <= order.subscription_id.template_id.cutoff_day) or not order.subscription_id.template_id.is_fixed_policy:
                        order._send_order_confirmation_mail()

                request.session['sale_order_id'] = None
                request.session['sale_transaction_id'] = None
                return request.render("web_sale_extended.confirm_assisted_purchase_benefice", render_values)
            elif order.sponsor_id.id == 5521:
                order.action_payu_confirm()
                return request.render("web_sale_extended.confirm_assisted_purchase_bancolombia", render_values)
                
            else:
                return request.render("web_sale_extended.confirm_assisted_purchase", render_values)
        else:
            kwargs['order_detail'] = order_detail
            kwargs['partner'] = Partner
            kwargs['website_sale_order'] = order
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None

            if sponsor_id.id == 5521:
                order.action_payu_confirm()
                return request.render("web_sale_extended.bancolombia_confirmation_sale", kwargs)
            else:
                """ Confirmando Orden de Venta luego del proceso exitoso de beneficiarios """
                order.action_confirm()
                order._send_order_confirmation_mail()
                return request.render("web_sale_extended.beneficiary_detail", kwargs)


    @http.route(['/beneficiary-submit'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def beneficiary_submit(self, **kwargs):
        ''' Actualiza el estado de los beneficiarios a true '''
        InsurerPartner = request.env['res.partner'].search([('email', '=', request.env.user.email)], limit=1)
        InsurerPartner_childs = request.env['res.partner'].search([
            ('parent_id', '=', InsurerPartner[0].id), ('active', '=', False),
        ], limit=6)

        for beneficiary in InsurerPartner_childs:
            BeneficiaryPartner = request.env['res.partner'].browse(beneficiary.id)
            BeneficiaryPartner.sudo().write({'active': True})

        confirm_mail_template = request.env.ref('web_sale_extended.email_beneficiary_confirm_template')
        confirm_mail_template.sudo().send_mail(InsurerPartner[0].id)
        return "Datos eviados correctamente"


    @http.route(['/report/beneficiary/<int:order_id>'],  methods=['GET'], type='http', auth="public", website=True)
    def report_poliza(self, order_id, **kwargs):
        order = request.env['sale.order'].sudo().browse(order_id)
        report_obj = request.env['ir.actions.report']
        report = report_obj.sudo()._get_report_from_name('sale.report_saleorder')
        pdf = report.sudo().render_qweb_pdf(order_id)[0]
        pdfhttpheaders = [ ('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)), ('Content-Disposition', 'attachment; filename="Certificado Individual P%s C%s.pdf"'%(order.subscription_id.number, order.subscription_id.policy_number)), ]
        return request.make_response(pdf, headers=pdfhttpheaders)


    # search cities by ajax peticion
    @http.route(['/search/cities'],  methods=['GET'], type='http', auth="public", website=True)
    def search_cities(self, city_id=None, **kwargs):
        ''' Busca las ciudades por departamentos en peticiones ajax retorna un json '''
        cities = []
        suggested_cities = request.env['res.city'].sudo().search([
            ('state_id', '=', int(kwargs['departamento']))
        ])
        complete_cities_with_zip = request.env['res.city.zip'].sudo().search([]).filtered(
            lambda line: line.city_id.state_id.id == int(kwargs['departamento'])).sorted(key=lambda r: r.city_id.name)

        #for city in suggested_cities:
        for city in complete_cities_with_zip:
            if city.city_id.state_id.id == int(kwargs['departamento']):
                cities.append({
                    'city': city.city_id.name.lower().title(),
                    'city_id': city.city_id.id,
                })
        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {'cities': cities}
        return json.dumps(data)
    
    
    # search states by ajax peticion
    @http.route(['/search/states'],  methods=['GET'], type='http', auth="public", website=True)
    def search_states(self, city_id=None, **kwargs):
        ''' Busca los estados del pais en peticiones ajax retorna un json '''
        states = []
        suggested_states = request.env['res.country'].browse(49).get_website_sale_states()

         #for states in suggested_states:
        for state in suggested_states: 
            states.append({
                    'state': state.name.lower().title(),
                    'state_id': state.id,
                })
        
        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {'states': states}
        return json.dumps(data)


    # search cities by ajax peticion
    @http.route(['/search/zipcodes'],  methods=['GET'], type='http', auth="public", website=True)
    def search_zipcodes(self, **kwargs):
        suggested_zipcode = request.env['res.city.zip'].sudo().search([('city_id', '=', int(kwargs['city_id']))], limit=1)
        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {'zipcode': suggested_zipcode.name, 'zipid': suggested_zipcode.id}
        return json.dumps(data)
    
    # search phone code country by ajax peticion
    @http.route(['/search/phonecode'],  methods=['GET'], type='http', auth="public", website=True)
    def search_phonecodes(self, **kwargs):
        suggested_phonecode = request.env['res.country'].sudo().search([('id', '=', int(kwargs['id']))], limit=1)
        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {'phonecode': suggested_phonecode.phone_code, 'countryid': suggested_phonecode.id}
        return json.dumps(data)
    
    
    # search buyer information by order_id by ajax peticion
    @http.route(['/search/buyer/info'],  methods=['GET'], type='http', auth="public", website=True)
    def search_buyer_info(self, **kwargs):
        order = request.env['sale.order'].sudo().browse(int(kwargs['order_id']))
        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {            
            'firstname': order.partner_id.firstname,
            'othernames': order.partner_id.othernames,
            'lastname': order.partner_id.lastname,
            'lastname2':order.partner_id.lastname2,            
            'email': order.partner_id.email,
            "phone": order.partner_id.phone,
            'mobile': order.partner_id.mobile,
            'document_type_id': order.partner_id.document_type_id.id,
            'identification_document': order.partner_id.identification_document,
            'birthdate_date': order.partner_id.birthdate_date.strftime("%Y-%m-%d"),
            'expedition_date': order.partner_id.expedition_date.strftime("%Y-%m-%d"),
            'address': order.partner_id.street,
            'country_id': order.partner_id.country_id.id,
            'state_id': order.partner_id.state_id.id,
            'city_id': order.partner_id.zip_id.city_id.id
        }
        return json.dumps(data)


    def _get_shop_payment_values(self, order, **kwargs):
        values = dict(
            website_sale_order=order,
            errors=[],
            partner=order.partner_id.id,
            order=order,
            payment_action_id=request.env.ref('payment.action_payment_acquirer').id,
            return_url= '/shop/payment/validate',
            bootstrap_formatting= True
        )

        domain = expression.AND([
            ['&', ('state', 'in', ['enabled','test']), ('company_id', '=', order.company_id.id)],
            ['|', ('website_id', '=', False), ('website_id', '=', request.website.id)],
            ['|', ('country_ids', '=', False), ('country_ids', 'in', [order.partner_id.country_id.id])]
        ])
        acquirers = request.env['payment.acquirer'].search(domain)

        values['access_token'] = order.access_token
        values['acquirers'] = [acq for acq in acquirers if (acq.payment_flow == 'form' and acq.view_template_id) or
                                    (acq.payment_flow == 's2s' and acq.registration_view_template_id)]
        values['tokens'] = request.env['payment.token'].search(
            [('partner_id', '=', order.partner_id.id),
            ('acquirer_id', 'in', acquirers.ids)])

        if order:
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order.amount_total, order.currency_id, order.partner_id.country_id.id)
        return values


    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        if not product.can_access_from_current_website(): # Comentar para efectos de pruebas
            raise NotFound()                              # Comentar para efectos de pruebas
        #if product.id in (1,2,3):
        if product.is_product_landpage:
            """This route is called when adding a product to cart (no options)."""
            sale_order = request.website.sale_get_order(force_create=True)
            if sale_order.state != 'draft':
                request.session['sale_order_id'] = None
                sale_order = request.website.sale_get_order(force_create=True)

            product_custom_attribute_values = None
            if kwargs.get('product_custom_attribute_values'):
                product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

            no_variant_attribute_values = None
            if kwargs.get('no_variant_attribute_values'):
                no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))
            sale_order.website_order_line.unlink()

            cant = 1
            producto = request.env['product.product'].sudo().browse(product.id)
            if producto.subscription_template_id.is_fixed_policy:
                hoy = date.today()
                r = relativedelta(producto.subscription_template_id.final_date, hoy)  
                if (producto.subscription_template_id.final_date.day - r.days) <= producto.subscription_template_id.cutoff_day:
                    cant = r.months + 1
                else:
                    cant = r.months
            #for line in sale_order.get_order_lines
            sale_order._cart_update(
                product_id=int(product.id),
                add_qty=cant,
                set_qty=0,
                product_custom_attribute_values=product_custom_attribute_values,
                no_variant_attribute_values=no_variant_attribute_values
            )
            #request.website.sale_reset()
            #return request.redirect("/shop/checkout?express=1&product_id=" + str(product.id))
            qcontext = ''
            if 'params' in request.params and request.params['params']:
                parametros = {}
                pa = request.params['params'].split('?')
                _logger.info(pa)
                for x in pa:
                    parametros[x.split('=')[0]] = x.split('=')[1]
                
                if 'user' in parametros.keys():
                    _logger.info('Tiene usuario')
                    sale_order.write({'user_id': int(parametros['user'])})
                    
                if 'assisted_purchase' in parametros.keys():
                    qcontext = '?assisted_purchase=' + str(parametros['assisted_purchase'])

            if request.params.get('_ga'):
                ag = request.params['_ga']
                qcontext = '?_ga=' + ag
                if request.params.get('_gl'):
                    gl = request.params['_gl']
                    qcontext += '&_gl=' + gl
            """ 
                Redireccionando al formulario de datos del comprador.
                1er Paso, lanzado desde landpage(no hay proceso de token para saber si la petición es valida),
                de esta manera se puede iniciar una compra directamente en la página de odoo apuntando
                a /shop/ + el nombre de un producto publicado para venta en landpage
            """
            return request.redirect("/shop/address%s" % qcontext)
            
        checkout_landpage_redirect = request.env.user.company_id.checkout_landpage_redirect
        if checkout_landpage_redirect:
            return request.redirect(checkout_landpage_redirect)
        return request.redirect("/web/login")

    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}
        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}
    

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        checkout_landpage_redirect = request.env.user.company_id.checkout_landpage_redirect
        if checkout_landpage_redirect:
            #return request.redirect(request.httprequest.referrer or '/web/login')
            return request.redirect(checkout_landpage_redirect)
        raise UserError('Landpage de Productos sin definir. Revise la configuración de PayU Latam')


    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :
         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if order.action_confirm():
                return request.render("website_sale.confirmation", {'order': order})
        else:
            return request.redirect('/shop')

    @http.route('/shop/payment/token', type='http', auth='public', website=True, sitemap=False)
    def payment_token(self, pm_id=None, **kwargs):
        """ Method that handles payment using saved tokens
        :param int pm_id: id of the payment.token that we want to use to pay.
        """
        order = request.website.sale_get_order()
        # do not crash if the user has already paid and try to pay again
        if not order:
            return request.redirect('/shop/?error=no_order')

        assert order.partner_id.id != request.website.partner_id.id

        try:
            pm_id = int(pm_id)
        except ValueError:
            return request.redirect('/shop/?error=invalid_token_id')

        # We retrieve the token the user want to use to pay
        if not request.env['payment.token'].sudo().search_count([('id', '=', pm_id)]):
            return request.redirect('/shop/?error=token_not_found')

        # Create transaction
        vals = {'payment_token_id': pm_id, 'return_url': '/shop/payment/validate'}

        tx = order._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(tx)
        return request.redirect('/payment/process')

    @http.route('/update/bancolombia/account', type='http', auth='public', website=True, sitemap=False)
    def update_bancolombia_account(self, order_id=None, partner_id=None, access_token=None, **kwargs):
        order_id = request.env['sale.order'].sudo().browse(int(order_id))
        partner_id = order_id.partner_id
        amount = order_id.amount_total
        currency_id = order_id.currency_id.id
        if 'submitted' in kwargs:
            encrypt_msg = self.encrypt_aes_gcm(kwargs['account_number'])
            ciphertext = b64encode(encrypt_msg[0]).decode('utf-8')
            nonce = b64encode(encrypt_msg[1]).decode('utf-8')
            auth_tag = b64encode(encrypt_msg[2]).decode('utf-8')
            secretkey = b64encode(encrypt_msg[3]).decode('utf-8')
            order_id.write({
                'update_account_bancolombia': False,
                'debit_request': False,
                'buyer_account_type': kwargs['bancolombia_types_account'],
                'buyer_account_number': ciphertext,
                'nonce': nonce,
                'auth_tag': auth_tag,
                'secretkey': secretkey
            })
            return request.render("web_sale_extended.bancolombia_confirmation_update_account", {})

        # sponsor_id.id 5521 = "Bancolombia"
        if partner_id and not access_token or order_id.sponsor_id.id != 5521 or order_id.update_account_bancolombia != True:
            raise werkzeug.exceptions.NotFound
        if partner_id and access_token:
            token_ok = request.env['payment.link.wizard'].check_token(access_token, int(partner_id.id), float(amount), int(currency_id))
            if not token_ok:
                raise werkzeug.exceptions.NotFound
        
        render_values = {
            'bancolombia_types_account': self.get_bancolombia_types_account(),
            'website_sale_order': order_id,
            'partner_id': partner_id
        }
        return request.render("web_sale_extended.update_bancolombia_account", render_values)
    
    # Consulta por cedula si ya posee una poliza activa
    @http.route(['/unique/buyer/bancolombia/<int:cedula_comprador>'], methods=['GET'], type='http', auth="public", website=True, csrf=True)
    def unique_payment_bancolombia(self, cedula_comprador=None, access_token=None, **kwargs):
        # _logger.info('on unique_payment_bancolombia')
        # _logger.info(cedula_comprador)

        # init values
        unique = True
        polizas_activas = 0

        # Consulta el cliente por la cedula
        cliente = request.env['res.partner'].sudo().search([('identification_document', '=', cedula_comprador)], limit=1)

        # Si existe el cliente
        if cliente:
            # Consulta las polizas activas
            polizas_activas = request.env['sale.order'].sudo().search_count([
                ('state', 'in', ['sale', 'payu_pending']),
                ('partner_id', '=', cliente.id),
                ('sponsor_id', '=', 5521), # sponpor_id = 5521 (Bancolombia)
            ])

            if polizas_activas > 0:
                unique = False

        # respuesta
        data = {}
        data['cedula'] = cedula_comprador,
        data['name'] = cliente.name,
        data['polizas'] = polizas_activas,
        data['unique'] = unique,
        data['status'] = True,
        data['error'] = None,
        return json.dumps(data)

class SalePortalExtended(CustomerPortal):

    # note dbo: website_sale code
    @http.route(['/my/orders/<int:order_id>/transaction/'], type='json', auth="public", website=True)
    def payment_transaction_token(self, acquirer_id, order_id, save_token=False, access_token=None, **kwargs):
        """ Json method that creates a payment.transaction, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.
        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        """
        # Ensure a payment acquirer is selected
        if not acquirer_id:
            return False

        try:
            acquirer_id = int(acquirer_id)
        except:
            return False

        order = request.env['sale.order'].sudo().browse(order_id)
        if not order or not order.order_line or not order.has_to_be_paid():
            return False

        # Create transaction
        vals = {
            'acquirer_id': acquirer_id,
            'type': order._get_payment_type(save_token),
            'return_url': order.get_portal_url(),
        }

        transaction = order._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(transaction)
        order = request.website.sale_get_order()

        return transaction.render_sale_button(
            order,
            submit_txt=_('Pay & Confirm'),
            render_values={
                'type': order._get_payment_type(save_token),
                'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.'),
            }
        )

    @http.route(['/my/orders/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_quote_accept(self, order_id, access_token=None, name=None, signature=None):
        
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not order_sudo.has_to_be_signed():
            return {'error': _('The order is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            order_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}

        if not order_sudo.has_to_be_paid():
            order_sudo.action_confirm()
            order_sudo._send_order_confirmation_mail()

        pdf = request.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([order_sudo.id])[0]

        _message_post_helper(
            'sale.order', order_sudo.id, _('Order signed by %s') % (name,),
            attachments=[('%s.pdf' % order_sudo.name, pdf)],
            **({'token': access_token} if access_token else {}))

        query_string = '&message=sign_ok'
        if order_sudo.has_to_be_paid(True):
            query_string += '#allow_payment=yes'

        return {
            'force_refresh': True,
            'redirect_url': order_sudo.get_portal_url(query_string=query_string),
        }


class WebsitePaymentExtended(PaymentProcessing):

    @http.route(['/payment/process'], type="http", auth="public", website=True, sitemap=False)
    def payment_status_page(self, **kwargs):
        time.sleep(4)
        # When the customer is redirect to this website page,
        # we retrieve the payment transaction list from his session
        tx_ids_list = self.get_payment_transaction_ids()
        payment_transaction_ids = request.env['payment.transaction'].sudo().browse(tx_ids_list).exists()
        order = request.website.sale_get_order()
        render_ctx = {
            'payment_tx_ids': payment_transaction_ids.ids,
            'message': 'sign_ok',
            'sale_order': order.id,
        }
        order = request.website.sale_get_order()
        url = "/my/order/beneficiaries/" + str(order.id) + '?access_token=' + self.generate_access_token(order.id)

        order.action_confirm()
        return request.redirect(url)


class OdooWebsiteSearchCity(http.Controller):

    @http.route(['/search/suggestion_city'],  methods=['GET'], type='http', auth="public", website=True)
    def search_suggestion(self, city_id=None, **post):
        time.sleep(4)
        cities = []
        complete_cities_with_zip = request.env['res.city.zip'].sudo().search([])
        prueba = request.env['res.country.state'].sudo().search([('country_id', '=', 49),])
        for states in prueba:
            _logger.info(states.name)
            cities.append({
                'state': states.name,
                'country_id': states.country_id
            })

        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {'cities': cities}
        return json.dumps(data)

    @http.route(['/shop/assisted_purchase'], methods=['GET'], type='http', auth="user", website=True)
    def assisted_purchase(self):       
        Products = request.env['product.template'].search([])   
        products_search_ids = []
        data = {}  
        user = request.env.user
        
        if 'search' in request.params and request.params['search']: 
            for product in Products:
                if len(request.params['search']) < 3:
                    if (product.categ_id.name).lower().startswith(str(request.params['search']).lower()):
                        products_search_ids.append(int(product.categ_id))
                else:
                    if str(request.params['search']).lower() in (product.categ_id.name).lower():
                        products_search_ids.append(int(product.categ_id))
                        
            Products = request.env['product.template'].search([('categ_id', 'in', products_search_ids)])       
        
        for product in Products:
            if product.categ_id.sponsor_id in user.sponsor_ids:
                if product.categ_id.name in data:
                    data[product.categ_id.name].append(product)
                else:
                    data[product.categ_id.name] = [product]
        
        values = {
            'products': Products,
            'data': data
        }
        return request.render("web_sale_extended.alternativo", values)
   
    @http.route(['/shop/payment/assisted_purchase/<int:order_id>'], methods=['GET'], type='http', auth="public", website=True, csrf=True)
    def get_payment_assisted_purchase(self, order_id, access_token=None, **kwargs):     
        if order_id:
            order = request.env['sale.order'].sudo().browse(order_id)
            request.session['sale_order_id'] = order_id
            request.session['sale_transaction_id'] = None
            inst = WebsiteSaleExtended()
            correct_token = inst.generate_access_token(order_id)
            if consteq(ustr(access_token), correct_token) and order.assisted_purchase == True:
                return request.redirect('/shop/confirm_order')
            else:
                raise werkzeug.exceptions.NotFound