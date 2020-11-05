# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
# from odoo.addons.base.models.ir_qweb_fields import nl2br
# from odoo.addons.http_routing.models.ir_http import slug
# from odoo.addons.payment.controllers.portal import PaymentProcessing
# from odoo.addons.website.controllers.main import QueryURL
# from odoo.addons.website.models.ir_http import sitemap_qs2dom
# from odoo.exceptions import ValidationError
# from odoo.addons.portal.controllers.portal import _build_url_w_params
# from odoo.addons.website.controllers.main import Website
# from odoo.addons.website_form.controllers.main import WebsiteForm
# from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import WebsiteSale
_logger = logging.getLogger(__name__)



class WebsiteSaleExtended(WebsiteSale):

    # def _get_pricelist_context(self):
    #     pricelist_context = dict(request.env.context)
    #     pricelist = False
    #     if not pricelist_context.get('pricelist'):
    #         pricelist = request.website.get_current_pricelist()
    #         pricelist_context['pricelist'] = pricelist.id
    #     else:
    #         pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

    #     return pricelist_context, pricelist

    # def _get_search_order(self, post):
    #     # OrderBy will be parsed in orm and so no direct sql injection
    #     # id is added to be sure that order is a unique sort key
    #     order = post.get('order') or 'website_sequence ASC'
    #     return 'is_published desc, %s, id desc' % order

    # def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
    #     domains = [request.website.sale_product_domain()]
    #     if search:
    #         for srch in search.split(" "):
    #             subdomains = [
    #                 [('name', 'ilike', srch)],
    #                 [('product_variant_ids.default_code', 'ilike', srch)]
    #             ]
    #             if search_in_description:
    #                 subdomains.append([('description', 'ilike', srch)])
    #                 subdomains.append([('description_sale', 'ilike', srch)])
    #             domains.append(expression.OR(subdomains))

    #     if category:
    #         domains.append([('public_categ_ids', 'child_of', int(category))])

    #     if attrib_values:
    #         attrib = None
    #         ids = []
    #         for value in attrib_values:
    #             if not attrib:
    #                 attrib = value[0]
    #                 ids.append(value[1])
    #             elif value[0] == attrib:
    #                 ids.append(value[1])
    #             else:
    #                 domains.append([('attribute_line_ids.value_ids', 'in', ids)])
    #                 attrib = value[0]
    #                 ids = [value[1]]
    #         if attrib:
    #             domains.append([('attribute_line_ids.value_ids', 'in', ids)])

    #     return expression.AND(domains)

    # def sitemap_shop(env, rule, qs):
    #     if not qs or qs.lower() in '/shop':
    #         yield {'loc': '/shop'}

    #     Category = env['product.public.category']
    #     dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
    #     dom += env['website'].get_current_website().website_domain()
    #     for cat in Category.search(dom):
    #         loc = '/shop/category/%s' % slug(cat)
    #         if not qs or qs.lower() in loc:
    #             yield {'loc': loc}

    # @http.route([
    #     '''/shop''',
    #     '''/shop/page/<int:page>''',
    #     '''/shop/category/<model("product.public.category"):category>''',
    #     '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    # ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    # def shop(self, page=0, category=None, search='', ppg=False, **post):
    #     add_qty = int(post.get('add_qty', 1))
    #     Category = request.env['product.public.category']
    #     if category:
    #         category = Category.search([('id', '=', int(category))], limit=1)
    #         if not category or not category.can_access_from_current_website():
    #             raise NotFound()
    #     else:
    #         category = Category

    #     if ppg:
    #         try:
    #             ppg = int(ppg)
    #             post['ppg'] = ppg
    #         except ValueError:
    #             ppg = False
    #     if not ppg:
    #         ppg = request.env['website'].get_current_website().shop_ppg or 20

    #     ppr = request.env['website'].get_current_website().shop_ppr or 4

    #     attrib_list = request.httprequest.args.getlist('attrib')
    #     attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
    #     attributes_ids = {v[0] for v in attrib_values}
    #     attrib_set = {v[1] for v in attrib_values}

    #     domain = self._get_search_domain(search, category, attrib_values)

    #     keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

    #     pricelist_context, pricelist = self._get_pricelist_context()

    #     request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

    #     url = "/shop"
    #     if search:
    #         post["search"] = search
    #     if attrib_list:
    #         post['attrib'] = attrib_list

    #     Product = request.env['product.template'].with_context(bin_size=True)

    #     search_product = Product.search(domain, order=self._get_search_order(post))
    #     website_domain = request.website.website_domain()
    #     categs_domain = [('parent_id', '=', False)] + website_domain
    #     if search:
    #         search_categories = Category.search([('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
    #         categs_domain.append(('id', 'in', search_categories.ids))
    #     else:
    #         search_categories = Category
    #     categs = Category.search(categs_domain)

    #     if category:
    #         url = "/shop/category/%s" % slug(category)

    #     product_count = len(search_product)
    #     pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
    #     offset = pager['offset']
    #     products = search_product[offset: offset + ppg]

    #     ProductAttribute = request.env['product.attribute']
    #     if products:
    #         # get all products without limit
    #         attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
    #     else:
    #         attributes = ProductAttribute.browse(attributes_ids)

    #     layout_mode = request.session.get('website_sale_shop_layout_mode')
    #     if not layout_mode:
    #         if request.website.viewref('website_sale.products_list_view').active:
    #             layout_mode = 'list'
    #         else:
    #             layout_mode = 'grid'

    #     values = {
    #         'search': search,
    #         'category': category,
    #         'attrib_values': attrib_values,
    #         'attrib_set': attrib_set,
    #         'pager': pager,
    #         'pricelist': pricelist,
    #         'add_qty': add_qty,
    #         'products': products,
    #         'search_count': product_count,  # common for all searchbox
    #         'bins': TableCompute().process(products, ppg, ppr),
    #         'ppg': ppg,
    #         'ppr': ppr,
    #         'categories': categs,
    #         'attributes': attributes,
    #         'keep': keep,
    #         'search_categories_ids': search_categories.ids,
    #         'layout_mode': layout_mode,
    #     }
    #     if category:
    #         values['main_object'] = category
    #     return request.render("website_sale.products", values)

    # @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    # def product(self, product, category='', search='', **kwargs):
    #     if not product.can_access_from_current_website():
    #         raise NotFound()

    #     return request.render("website_sale.product", self._prepare_product_values(product, category, search, **kwargs))

    # @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=False)
    # def old_product(self, product, category='', search='', **kwargs):
    #     # Compatibility pre-v14
    #     return request.redirect(_build_url_w_params("/shop/%s" % slug(product), request.params), code=301)

    # def _prepare_product_values(self, product, category, search, **kwargs):
    #     add_qty = int(kwargs.get('add_qty', 1))

    #     product_context = dict(request.env.context, quantity=add_qty,
    #                            active_id=product.id,
    #                            partner=request.env.user.partner_id)
    #     ProductCategory = request.env['product.public.category']

    #     if category:
    #         category = ProductCategory.browse(int(category)).exists()

    #     attrib_list = request.httprequest.args.getlist('attrib')
    #     attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
    #     attrib_set = {v[1] for v in attrib_values}

    #     keep = QueryURL('/shop', category=category and category.id, search=search, attrib=attrib_list)

    #     categs = ProductCategory.search([('parent_id', '=', False)])

    #     pricelist = request.website.get_current_pricelist()

    #     if not product_context.get('pricelist'):
    #         product_context['pricelist'] = pricelist.id
    #         product = product.with_context(product_context)

    #     # Needed to trigger the recently viewed product rpc
    #     view_track = request.website.viewref("website_sale.product").track

    #     return {
    #         'search': search,
    #         'category': category,
    #         'pricelist': pricelist,
    #         'attrib_values': attrib_values,
    #         'attrib_set': attrib_set,
    #         'keep': keep,
    #         'categories': categs,
    #         'main_object': product,
    #         'product': product,
    #         'add_qty': add_qty,
    #         'view_track': view_track,
    #     }

    # @http.route(['/shop/change_pricelist/<model("product.pricelist"):pl_id>'], type='http', auth="public", website=True, sitemap=False)
    # def pricelist_change(self, pl_id, **post):
    #     if (pl_id.selectable or pl_id == request.env.user.partner_id.property_product_pricelist) \
    #             and request.website.is_pricelist_available(pl_id.id):
    #         request.session['website_sale_current_pl'] = pl_id.id
    #         request.website.sale_get_order(force_pricelist=pl_id.id)
    #     return request.redirect(request.httprequest.referrer or '/shop')

    # @http.route(['/shop/pricelist'], type='http', auth="public", website=True, sitemap=False)
    # def pricelist(self, promo, **post):
    #     redirect = post.get('r', '/shop/cart')
    #     # empty promo code is used to reset/remove pricelist (see `sale_get_order()`)
    #     if promo:
    #         pricelist = request.env['product.pricelist'].sudo().search([('code', '=', promo)], limit=1)
    #         if (not pricelist or (pricelist and not request.website.is_pricelist_available(pricelist.id))):
    #             return request.redirect("%s?code_not_available=1" % redirect)

    #     request.website.sale_get_order(code=promo)
    #     return request.redirect(redirect)

    # @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    # def cart(self, access_token=None, revive='', **post):
    #     """
    #     Main cart management + abandoned cart revival
    #     access_token: Abandoned cart SO access token
    #     revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
    #     """
    #     order = request.website.sale_get_order()
    #     if order and order.state != 'draft':
    #         request.session['sale_order_id'] = None
    #         order = request.website.sale_get_order()
    #     values = {}
    #     if access_token:
    #         abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
    #         if not abandoned_order:  # wrong token (or SO has been deleted)
    #             raise NotFound()
    #         if abandoned_order.state != 'draft':  # abandoned cart already finished
    #             values.update({'abandoned_proceed': True})
    #         elif revive == 'squash' or (revive == 'merge' and not request.session.get('sale_order_id')):  # restore old cart or merge with unexistant
    #             request.session['sale_order_id'] = abandoned_order.id
    #             return request.redirect('/shop/cart')
    #         elif revive == 'merge':
    #             abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
    #             abandoned_order.action_cancel()
    #         elif abandoned_order.id != request.session.get('sale_order_id'):  # abandoned cart found, user have to choose what to do
    #             values.update({'access_token': abandoned_order.access_token})

    #     values.update({
    #         'website_sale_order': order,
    #         'date': fields.Date.today(),
    #         'suggested_products': [],
    #     })
    #     if order:
    #         order.order_line.filtered(lambda l: not l.product_id.active).unlink()
    #         _order = order
    #         if not request.env.context.get('pricelist'):
    #             _order = order.with_context(pricelist=order.pricelist_id.id)
    #         values['suggested_products'] = _order._cart_accessories()

    #     if post.get('type') == 'popover':
    #         # force no-cache so IE11 doesn't cache this XHR
    #         return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})

    #     return request.render("website_sale.cart", values)

    # @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    # def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
    #     """This route is called when adding a product to cart (no options)."""
    #     sale_order = request.website.sale_get_order(force_create=True)
    #     if sale_order.state != 'draft':
    #         request.session['sale_order_id'] = None
    #         sale_order = request.website.sale_get_order(force_create=True)

    #     product_custom_attribute_values = None
    #     if kw.get('product_custom_attribute_values'):
    #         product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

    #     no_variant_attribute_values = None
    #     if kw.get('no_variant_attribute_values'):
    #         no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

    #     sale_order._cart_update(
    #         product_id=int(product_id),
    #         add_qty=add_qty,
    #         set_qty=set_qty,
    #         product_custom_attribute_values=product_custom_attribute_values,
    #         no_variant_attribute_values=no_variant_attribute_values
    #     )

    #     if kw.get('express'):
    #         return request.redirect("/shop/checkout?express=1")

    #     return request.redirect("/shop/cart")

    # @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    # def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
    #     """This route is called when changing quantity from the cart or adding
    #     a product from the wishlist."""
    #     order = request.website.sale_get_order(force_create=1)
    #     if order.state != 'draft':
    #         request.website.sale_reset()
    #         return {}

    #     value = order._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)

    #     if not order.cart_quantity:
    #         request.website.sale_reset()
    #         return value

    #     order = request.website.sale_get_order()
    #     value['cart_quantity'] = order.cart_quantity

    #     if not display:
    #         return value

    #     value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
    #         'website_sale_order': order,
    #         'date': fields.Date.today(),
    #         'suggested_products': order._cart_accessories()
    #     })
    #     value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
    #         'website_sale_order': order,
    #     })
    #     return value

    # @http.route('/shop/save_shop_layout_mode', type='json', auth='public', website=True)
    # def save_shop_layout_mode(self, layout_mode):
    #     assert layout_mode in ('grid', 'list'), "Invalid shop layout mode"
    #     request.session['website_sale_shop_layout_mode'] = layout_mode

    # ------------------------------------------------------
    # Checkout
    # ------------------------------------------------------

    # def checkout_redirection(self, order):
    #     # must have a draft sales order with lines at this point, otherwise reset
    #     if not order or order.state != 'draft':
    #         request.session['sale_order_id'] = None
    #         request.session['sale_transaction_id'] = None
    #         return request.redirect('/shop')

    #     if order and not order.order_line:
    #         return request.redirect('/shop/cart')

    #     # if transaction pending / done: redirect to confirmation
    #     tx = request.env.context.get('website_sale_transaction')
    #     if tx and tx.state != 'draft':
    #         return request.redirect('/shop/payment/confirmation/%s' % order.id)

    # def checkout_values(self, **kw):
    #     order = request.website.sale_get_order(force_create=1)
    #     shippings = []
    #     if order.partner_id != request.website.user_id.sudo().partner_id:
    #         Partner = order.partner_id.with_context(show_address=1).sudo()
    #         shippings = Partner.search([
    #             ("id", "child_of", order.partner_id.commercial_partner_id.ids),
    #             '|', ("type", "in", ["delivery", "other"]), ("id", "=", order.partner_id.commercial_partner_id.id)
    #         ], order='id desc')
    #         if shippings:
    #             if kw.get('partner_id') or 'use_billing' in kw:
    #                 if 'use_billing' in kw:
    #                     partner_id = order.partner_id.id
    #                 else:
    #                     partner_id = int(kw.get('partner_id'))
    #                 if partner_id in shippings.mapped('id'):
    #                     order.partner_shipping_id = partner_id
    #             elif not order.partner_shipping_id:
    #                 last_order = request.env['sale.order'].sudo().search([("partner_id", "=", order.partner_id.id)], order='id desc', limit=1)
    #                 order.partner_shipping_id.id = last_order and last_order.id

    #     values = {
    #         'order': order,
    #         'shippings': shippings,
    #         'only_services': order and order.only_services or False
    #     }
    #     return values

    # def _get_mandatory_billing_fields(self):
    #     return ["name", "email", "street", "city", "country_id"]

    # def _get_mandatory_shipping_fields(self):
    #     return ["name", "street", "city", "country_id"]

    # def checkout_form_validate(self, mode, all_form_values, data):
    #     # mode: tuple ('new|edit', 'billing|shipping')
    #     # all_form_values: all values before preprocess
    #     # data: values after preprocess
    #     error = dict()
    #     error_message = []

    #     # Required fields from form
    #     required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]
    #     # Required fields from mandatory field function
    #     required_fields += mode[1] == 'shipping' and self._get_mandatory_shipping_fields() or self._get_mandatory_billing_fields()
    #     # Check if state required
    #     _logger.info("***CHECKOUT FORM ***")
    #     _logger.info(request.env)
    #     country = request.env['res.country']
    #     if data.get('country_id'):
    #         country = country.browse(int(data.get('country_id')))
    #         if country.state_required:
    #             required_fields += ['state_id']
    #         if country.zip_required:
    #             required_fields += ['zip']

    #     # error message for empty required fields
    #     for field_name in required_fields:
    #         if not data.get(field_name):
    #             error[field_name] = 'missing'

    #     # email validation
    #     if data.get('email') and not tools.single_email_re.match(data.get('email')):
    #         error["email"] = 'error'
    #         error_message.append(_('Invalid Email! Please enter a valid email address.'))

    #     # vat validation
    #     Partner = request.env['res.partner']
    #     if data.get("vat") and hasattr(Partner, "check_vat"):
    #         if data.get("country_id"):
    #             data["vat"] = Partner.fix_eu_vat_number(data.get("country_id"), data.get("vat"))
    #         partner_dummy = Partner.new({
    #             'vat': data['vat'],
    #             'country_id': (int(data['country_id'])
    #                            if data.get('country_id') else False),
    #         })
    #         try:
    #             partner_dummy.check_vat()
    #         except ValidationError:
    #             error["vat"] = 'error'

    #     if [err for err in error.values() if err == 'missing']:
    #         error_message.append(_('Some required fields are empty.'))

    #     return error, error_message

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':
            _logger.info("****CHECKOUT FORM*****")
            _logger.info(mode)
            _logger.info(checkout)
            _logger.info(all_values)
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

    # def values_preprocess(self, order, mode, values):
    #     # Convert the values for many2one fields to integer since they are used as IDs
    #     partner_fields = request.env['res.partner']._fields
    #     return {
    #         k: (bool(v) and int(v)) if k in partner_fields and partner_fields[k].type == 'many2one' else v
    #         for k, v in values.items()
    #     }

    # def values_postprocess(self, order, mode, values, errors, error_msg):
    #     new_values = {}
    #     authorized_fields = request.env['ir.model']._get('res.partner')._get_form_writable_fields()
    #     for k, v in values.items():
    #         # don't drop empty value, it could be a field to reset
    #         if k in authorized_fields and v is not None:
    #             new_values[k] = v
    #         else:  # DEBUG ONLY
    #             if k not in ('field_required', 'partner_id', 'callback', 'submitted'): # classic case
    #                 _logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)

    #     new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id
    #     new_values['user_id'] = request.website.salesperson_id and request.website.salesperson_id.id

    #     if request.website.specific_user_account:
    #         new_values['website_id'] = request.website.id

    #     if mode[0] == 'new':
    #         new_values['company_id'] = request.website.company_id.id

    #     lang = request.lang.code if request.lang.code in request.website.mapped('language_ids.code') else None
    #     if lang:
    #         new_values['lang'] = lang
    #     if mode == ('edit', 'billing') and order.partner_id.type == 'contact':
    #         new_values['type'] = 'other'
    #     if mode[1] == 'shipping':
    #         new_values['parent_id'] = order.partner_id.commercial_partner_id.id
    #         new_values['type'] = 'delivery'

    #     return new_values, errors, error_msg

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()
        _logger.info("*** GET METHOD ***")
        _logger.info(Partner)

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
                _logger.info("****ELSE*****")
                _logger.info(mode)
                _logger.info(post)
                _logger.info(kw)
                post['firstname'] = kw['name']
                post['othernames'] = kw['othernames']
                post['lastname'] = kw['lastname']
                post['lastname2'] = kw['lastname2']
                post['identification_document'] = kw["identification_document"]
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
        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'country': country,
            'country_states': country.get_website_sale_states(mode=mode[1]),
            'countries': country.get_website_sale_countries(mode=mode[1]),
            'error': errors,
            'callback': kw.get('callback'),
            'only_services': order and order.only_services,
        }
        return request.render("web_sale_extended.address", render_values)
    

    @http.route(['/add/beneficiary'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def beneficiary(self, **kwargs):
        return request.render("web_sale_extended.beneficiary")
   
