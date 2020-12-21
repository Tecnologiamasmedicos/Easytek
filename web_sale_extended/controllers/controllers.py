# -*- coding: utf-8 -*-
import json
import logging, base64
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
_logger = logging.getLogger(__name__)



class WebsiteSaleExtended(WebsiteSale):

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':

            partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
                    return Forbidden()
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    
    # toma de datos de pago y se crea el asegurador principal
    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):

        ''' Toma de datos de pago y se crea el asegurador principal '''

        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()
        order_detail = request.env['sale.order.line'].sudo().search([('order_id', "=", int(order.id))])
        _logger.info("*** nombre producto ***")
        _logger.info(order)
        _logger.info(order_detail.product_template_id.name)

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
            else: # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            _logger.info("****FORMULARIO*****")
            _logger.info(kw)
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                if kw['othernames'] == '':
                    post['othernames'] = ' '
                else:
                    post['othernames'] = kw['othernames']
                
                post['firstname'] = kw['name']
                post['lastname'] = kw['lastname']
                post['lastname2'] = kw['lastname2']
                post['document_type_id'] = int(kw["document"])
                post['person_type'] = "2"
                post['identification_document'] = kw["identification_document"]
                post["birthdate_date"] = kw["birthdate_date"]
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
                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/confirm_order')

        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
        country = country and country.exists() or def_country_id
        fiscal_position_ids = request.env['account.fiscal.position'].sudo().search([('active', '=', True)])
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
            'cities': self.get_cities(),
            'document_types': self.get_document_types(),
            'product': request.env['product.product'].sudo().browse(7),
            # 'fiscal_position': self.get_fiscal_position(),
            'only_services': order and order.only_services,
            'order_detail': order_detail,
        }
        return request.render("web_sale_extended.address", render_values)
    

    def get_cities(self):
        ''' LISTADOS DE TODAS LAS CIUDADES '''
        complete_cities_with_zip = request.env['res.city.zip'].sudo().search([])
        #return complete_cities_with_zip
        return []

    def get_document_types(self):
        ''' LISTADOS DE TODOS LOS TIPOS DE DOCUMENTO '''

        document_type = request.env['res.partner.document.type'].sudo().search([
            ('id','not in',[11,1,2,4]),
        ], order='name')
        return document_type




    @http.route(['/add/beneficiary'], type='http', methods=['GET', 'POST'], auth="user", website=True, sitemap=False)
    def get_data_beneficiary(self, **kwargs):

        ''' Captura de datos del beneficiario más no guarda informacion '''
        _logger.info("**BENEFICIARY**")

        _logger.info(request.env.user.email)
        InsurerPartner = request.env['res.partner'].search([('email', '=', request.env.user.email)], limit=1)
        
        InsurerPartner_childs = request.env['res.partner'].search([
            ('parent_id', '=', InsurerPartner[0].id),
        ], limit=6)

        order = order_detail = request.env['sale.order'].sudo().search([('partner_id', "=", InsurerPartner[0].id)])
        order_detail = request.env['sale.order.line'].sudo().search([('order_id', "=", int(order.id))])

        country = request.env['res.country'].browse(int(InsurerPartner.country_id))
        render_values = {
            "partner": InsurerPartner[0],
            'country_states': country.get_website_sale_states(),
            'cities': self.get_cities(),
            'countries': country.get_website_sale_countries(),
            'document_types': self.get_document_types(),
            'country': country,
            'order_detail': order_detail,
        }
        return request.render("web_sale_extended.beneficiary", render_values)

    
    @http.route(['/beneficiary-detail'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def create_beneficiary(self, **kwargs):

        ''' Guarda datos de los beneficiarios y los deja inactivo  '''
        _logger.info("***INFORME BENEFICIARIO***")
        _logger.info(kwargs)
        
        
        InsurerPartner = request.env['res.partner'].search([('email', '=', request.env.user.email)], limit=1)
        InsurerPartner_childs = request.env['res.partner'].search([
            ('parent_id', '=', InsurerPartner[0].id),
        ], limit=6)
        order = order_detail = request.env['sale.order'].sudo().search([('partner_id', "=", InsurerPartner[0].id)])
        order_detail = request.env['sale.order.line'].sudo().search([('order_id', "=", int(order.id))])
        _logger.info("***Datos de beneficiario***")
        _logger.info(len(InsurerPartner_childs))
        
        
        BeneficiaryPartner = request.env['res.partner'].sudo()
        
        if len(InsurerPartner_childs)>6:
            raise("Tienes muchos beneficiarios")
        
        for i in range(int(kwargs['beneficiario'])):
            firtst_name = "bfirstname"+str(i+1)
            other_name = "bfothername"+str(i+1)
            last_name = "bflastname"+str(i+1)
            last_name2 = "bflastname"+str(i+1)+"2"
            email = "bfemail"+str(i+1)
            document_type = "bfdocument"+str(i+1)
            identification_document = "bfnumero_documento"+str(i+1)
            country_id =  "bfcountry_id"+str(i+1)
            state_id = "bfdeparment"+str(i+1)
            city = "bfcity"+str(i+1)
            birthdate = "bfdate"+str(i+1)
            ocupation = "bfocupacion"+str(i+1)
            gender = "bfsex"+str(i+1)
            relationship = "bfparentesco"+str(i+1)
            address_beneficiary = "bfaddress"+str(i+1)
            phone = "bffijo"+str(i+1)
            mobile = "bfphone"+str(i+1)
            
            
            if InsurerPartner_childs:
                BeneficiaryPartner.sudo().write({
                    'firstname': kwargs[firtst_name],
                    'lastname': kwargs[last_name],
                    'lastname2':kwargs[last_name2],
                    'othernames': kwargs[other_name],
                    'email': kwargs[email],
                    #'mobile': phone,
                    #'document_type_id': kwargs[document_type],
                    'identification_document': kwargs[identification_document],
                    'company_type': 'person',
                    'active': False,
                    'parent_id': InsurerPartner.id
                    
                })
                

            else:
                if kwargs[other_name] == '':
                    kwargs[other_name] = ' '
                BeneficiaryPartner.create({
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
                    'active': False,
                    'parent_id': InsurerPartner.id,
                    'country_id': int(kwargs[country_id]),
                    'state_id': int(kwargs[state_id]),
                    'city': kwargs[city],
                    'birthdate_date': kwargs[birthdate],
                    'ocupation': kwargs[ocupation],
                    'gender': kwargs[gender],
                    'relationship': kwargs[relationship],
                    'address_beneficiary': kwargs[address_beneficiary],
                })
        kwargs['order_detail'] = order_detail
        kwargs['partner'] = InsurerPartner[0]
        
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
            _logger.info("Beneficiario Activo")
            _logger.info(BeneficiaryPartner.firstname)
            
        #punto ideal para enviar el correo
        _logger.info('****************************************\n\n++++++++++++++++++++++++++++++++++++')
        # Send Mail
        confirm_mail_template = request.env.ref('web_sale_extended.email_beneficiary_confirm_template')
        confirm_mail_template.sudo().send_mail(InsurerPartner[0].id)
        #if 1=1:
        #    context = dict(request.env.context)
        #    if confirm_mail_template:
        #        report_obj = request.env['ir.actions.report']
        #        report = report_obj._get_report_from_name('web_sale_extended.report_customreport_customeasytek_template_res_partner')
        #        pdf = report.render_qweb_pdf(InsurerPartner.id)[0]
        #        file_name = InsurerPartner.name
        #        b64_pdf = base64.b64encode(pdf)
        #        report_file = request.env['ir.attachment'].create({
        #            'name': file_name,
        #            'type': 'binary',
        #            'datas': b64_pdf,
        #            'datas_fname': file_name + '.pdf',
        #            'store_fname': file_name,
        #           'res_model': 'res.partner',
        #            'res_id': InsurerPartner.id,
         #           'mimetype': 'application/x-pdf'
         #       })
         #       values = confirm_mail_template.generate_email(InsurerPartner.id, fields=None)

          #      values['email_to'] = addr_to 
           #     values['email_from'] = ''
           #     values['res_id'] = InsurerPartner.id
           #     values['attachment_ids'] = [(4, report_file.id)]
           #     if not values['email_to'] and not values['email_from']:
            #        pass
             #   mail_mail_obj = request.env['mail.mail']
              #  msg_id = mail_mail_obj.create(values)
               # if msg_id:
                #    mail_mail_obj.send(msg_id)
                 #   sendmail_ok = True

        return "Datos eviados correctamente"

    
    @http.route(['/report/beneficiary'],  methods=['GET'], type='http', auth="public", website=True)
    def report_poliza(self, city_id=None, **kwargs):
        report_obj = request.env['ir.actions.report']
        report = report_obj.sudo()._get_report_from_name('web_sale_extended.report_customreport_customeasytek_template')
        pdf = report.sudo().render_qweb_pdf()[0]
        file_name = "prueba"
        b64_pdf = base64.b64encode(pdf)
        report_file = request.env['ir.attachment'].sudo().create({
            'name': file_name,
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': file_name + '.pdf',
            # 'store_fname': file_name,
            'res_model': 'res.partner',
            # 'res_id': 1,
            'mimetype': 'application/x-pdf'
        })
        return request.render(report_file, kwargs)


    # search cities by ajax peticion
    @http.route(['/search/cities'],  methods=['GET'], type='http', auth="public", website=True)
    def search_cities(self, city_id=None, **kwargs):
        ''' Busca las ciudades por departamentos en peticiones ajax retorna un json '''
        cities = []
        suggested_cities = request.env['res.city'].sudo().search([('state_id', '=', int(kwargs['departamento']))])
        complete_cities_with_zip = request.env['res.city.zip'].sudo().search([])

        #for city in suggested_cities:
        for city in complete_cities_with_zip:
            # _logger.info(zip_city.city_id.name)
            if city.city_id.state_id.id == int(kwargs['departamento']):
                cities.append({
                    'city': city.display_name,
                    'city_id': city.id,
                })
        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {'cities': cities}
        return json.dumps(data)
    
    
    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False
        
        render_values['product'] = request.env['product.product'].sudo().browse(7),
        
        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')

        return request.render("website_sale.payment", render_values)
    
    
    
    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        #if not product.can_access_from_current_website():
        #    raise NotFound()

        if product.id in (3,4,5):
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
            sale_order._cart_update(
                product_id=int(product.id),
                add_qty=1,
                set_qty=0,
                product_custom_attribute_values=product_custom_attribute_values,
                no_variant_attribute_values=no_variant_attribute_values
            )
            #request.website.sale_reset()
            return request.redirect("/shop/checkout?express=1&product_id=" + str(product.id))
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
        # quitando acceso y funcionalidad a /shop*
        return request.redirect(request.httprequest.referrer or '/web/login')
    
    
    
            


class OdooWebsiteSearchCity(http.Controller):

    @http.route(['/search/suggestion_city'],  methods=['GET'], type='http', auth="public", website=True)
    def search_suggestion(self, city_id=None, **post):

        cities = []
        complete_cities_with_zip = request.env['res.city.zip'].sudo().search([])
        prueba = request.env['res.country.state'].sudo().search([('country_id', '=', 49),])
        for states in prueba:
            _logger.info(states.name)
            cities.append({
                'state': states.name,
                'country_id': states.country_id
            })
        # prueba = request.env['account.fiscal.position'].sudo().search([])   consulta posicion fiscal
        # for zip_city in complete_cities_with_zip:
        #     # _logger.info(zip_city.city_id.name)
        #     cities.append({
        #         'city': "{0} - {1} - {2} - {3}".format(zip_city.name, zip_city.city_id.name, zip_city.city_id.state_id.name,
        #          zip_city.city_id.state_id.country_id.name),
        #         'city_id': zip_city.city_id.id,
        #         'state_id': zip_city.city_id.state_id.id,
        #         'country_id': zip_city.city_id.state_id.country_id.id,
        #         'zip_id': zip_city.id,
        #     })
        data = {}
        data['status'] = True,
        data['error'] = None,
        data['data'] = {'cities': cities}
        # _logger.info(data)
        return json.dumps(data)
   

