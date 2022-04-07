import hashlib
import hmac
import logging
from unicodedata import normalize
import psycopg2
import werkzeug

from odoo import http, _
from odoo.http import request
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, consteq, ustr
from odoo.tools.float_utils import float_repr
from datetime import datetime, date, timedelta

from odoo.addons.payment.controllers.portal import WebsitePayment
from . import controllers


_logger = logging.getLogger(__name__)

class CustomWebsitePayment(WebsitePayment):
    @http.route(['/website_payment/pay'], type='http', auth='public', website=True, sitemap=False)
    def pay(self, reference='', order_id=None, amount=False, currency_id=None, acquirer_id=None, partner_id=False, access_token=None, **kw):
        """
        Generic payment page allowing public and logged in users to pay an arbitrary amount.

        In the case of a public user access, we need to ensure that the payment is made anonymously - e.g. it should not be
        possible to pay for a specific partner simply by setting the partner_id GET param to a random id. In the case where
        a partner_id is set, we do an access_token check based on the payment.link.wizard model (since links for specific
        partners should be created from there and there only). Also noteworthy is the filtering of s2s payment methods -
        we don't want to create payment tokens for public users.

        In the case of a logged in user, then we let access rights and security rules do their job.
        """
        env = request.env
        user = env.user.sudo()
        reference = normalize('NFKD', reference).encode('ascii','ignore').decode('utf-8')
        if partner_id and not access_token:
            raise werkzeug.exceptions.NotFound
        if partner_id and access_token:
            token_ok = request.env['payment.link.wizard'].check_token(access_token, int(partner_id), float(amount), int(currency_id))
            if not token_ok:
                raise werkzeug.exceptions.NotFound

        invoice_id = kw.get('invoice_id')

        # Default values
        values = {
            'amount': 0.0,
            'currency': user.company_id.currency_id,
        }

        # Check sale order
        if order_id:
            try:
                order_id = int(order_id)
                if partner_id:
                    # `sudo` needed if the user is not connected.
                    # A public user woudn't be able to read the sale order.
                    # With `partner_id`, an access_token should be validated, preventing a data breach.
                    order = env['sale.order'].sudo().browse(order_id)
                    product_id = order.main_product_id
                else:
                    order = env['sale.order'].browse(order_id)
                    product_id = order.main_product_id
#                 if 'APROBADA' in estado or 'PENDIENTE' in estado:
#                     raise werkzeug.exceptions.NotFound     
                values.update({
                    'currency': order.currency_id,
                    'amount': order.amount_total,
                    'order_id': order_id
                })
            except:
                order_id = None

        if invoice_id:
            try:
                values['invoice_id'] = int(invoice_id)
                invoice = request.env['account.move'].sudo().browse(int(invoice_id))
                if invoice.payulatam_state in ('APPROVED', 'PENDING'):
                    raise werkzeug.exceptions.NotFound                    
                invoice_origin = invoice.invoice_origin
                subscription_id = request.env['sale.subscription'].sudo().search([('code', '=', str(invoice_origin))])
                _logger.info('cosasasas')
                _logger.info(subscription_id)
                sale_order_id = request.env['sale.order'].sudo().search([('subscription_id', '=', int(subscription_id.id))])
                product_id = sale_order_id.main_product_id
            except ValueError:
                invoice_id = None

        # Check currency
        if currency_id:
            try:
                currency_id = int(currency_id)
                values['currency'] = env['res.currency'].browse(currency_id)
            except:
                pass

        # Check amount
        if amount:
            try:
                amount = float(amount)
                values['amount'] = amount
            except:
                pass

        # Check reference
        reference_values = order_id and {'sale_order_ids': [(4, order_id)]} or {}
        values['reference'] = env['payment.transaction']._compute_reference(values=reference_values, prefix=reference)

        # Check acquirer
        acquirers = None
        if order_id and order:
            cid = order.company_id.id
        elif kw.get('company_id'):
            try:
                cid = int(kw.get('company_id'))
            except:
                cid = user.company_id.id
        else:
            cid = user.company_id.id

        # Check partner
        if not user._is_public():
            # NOTE: this means that if the partner was set in the GET param, it gets overwritten here
            # This is something we want, since security rules are based on the partner - assuming the
            # access_token checked out at the start, this should have no impact on the payment itself
            # existing besides making reconciliation possibly more difficult (if the payment partner is
            # not the same as the invoice partner, for example)
            partner_id = user.partner_id.id
        elif partner_id:
            partner_id = int(partner_id)

        values.update({
            'partner_id': partner_id,
            'bootstrap_formatting': True,
            'error_msg': kw.get('error_msg')
        })

        acquirer_domain = ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', cid)]
        if partner_id:
            partner = request.env['res.partner'].browse([partner_id])
            acquirer_domain = expression.AND([
            acquirer_domain,
            ['|', ('country_ids', '=', False), ('country_ids', 'in', [partner.sudo().country_id.id])]
        ])
        if acquirer_id:
            acquirers = env['payment.acquirer'].browse(int(acquirer_id))
        if order_id:
            acquirers = env['payment.acquirer'].search(acquirer_domain)
        if not acquirers:
            acquirers = env['payment.acquirer'].search(acquirer_domain)

        # s2s mode will always generate a token, which we don't want for public users
        valid_flows = ['form', 's2s'] if not user._is_public() else ['form']
        values['acquirers'] = [acq for acq in acquirers if acq.payment_flow in valid_flows]
        if partner_id:
            values['pms'] = request.env['payment.token'].search([
                ('acquirer_id', 'in', acquirers.ids),
                ('partner_id', '=', partner_id)
            ])
        else:
            values['pms'] = []
            
        
        _logger.info('Valuesss')
        _logger.info(values)
        
        
        
        
#         order = request.env['sale.order'].sudo().browse(order_id)
#         request.session['sale_last_order_id'] = order.id
#         request.session['sale_order_id'] = order.id
#         inst = controllers.WebsiteSaleExtended()
#         render_values = inst._get_shop_payment_values(order, **kw)
#         render_values['only_services'] = order and order.only_services or False

#         if render_values['errors']:
#             render_values.pop('acquirers', '')
#             render_values.pop('tokens', '')

        try:
            """ PayU Latam Api """
            endpoint = 'PING' # connect status
            ping_response = request.env['api.payulatam'].payulatam_ping()
            credit_card_methods = []
            bank_list = []
            _logger.info('ping_response')
            _logger.info(ping_response)
            if ping_response['code'] == 'SUCCESS':
                credit_card_methods = request.env['api.payulatam'].payulatam_get_credit_cards_methods()
                bank_list_pse = request.env['api.payulatam'].payulatam_get_bank_list()
                _logger.info('bank_list_pse')
                _logger.info(bank_list_pse)
                
        except:
            raise ValidationError("La pasarela de pagos no se encuentra disponible. Intente más tarde.")       
        
        mode = (False, False)
        country = request.env['res.country'].browse(49)
        current_year = int(date.today().year)
        credit_card_due_year_ids = list(range(current_year, current_year + 40))
        forma_pago = ''
        
        if product_id.subscription_template_id.recurring_rule_type == 'monthly' and product_id.subscription_template_id.recurring_interval == 1:
            forma_pago = 'Mensual'
        elif product_id.subscription_template_id.recurring_rule_type == 'monthly' and product_id.subscription_template_id.recurring_interval == 3:
            forma_pago = 'Trimestral'
        elif product_id.subscription_template_id.recurring_rule_type == 'monthly' and product_id.subscription_template_id.recurring_interval == 6:
            forma_pago = 'Semestral'
        elif product_id.subscription_template_id.recurring_rule_type == 'monthly' and product_id.subscription_template_id.recurring_interval == 12:
            forma_pago = 'Anual'
        elif product_id.subscription_template_id.recurring_rule_type == 'yearly' and product_id.subscription_template_id.recurring_interval == 1:
            forma_pago = 'Anual'
        else:
            forma_pago = 'cada ' + str(product_id.subscription_template_id.recurring_rule_type)+ ' ' + str(product_id.subscription_template_id.recurring_rule_type)
            
        
        
        
        values.update({
            'mode' : mode,
            'cities' : [],
            'product_id': product_id,
            'partner_id': request.env['res.partner'].browse(int(partner_id)),
#             'partner': (int(partner_id)),
            'country': request.env['res.country'].browse(int(49)),
            'country_states' : country.get_website_sale_states(mode=mode[1]),
            'countries': country.get_website_sale_countries(mode=mode[1]),
            'credit_card_due_year_ids': credit_card_due_year_ids,
            'credit_card_methods': credit_card_methods,
            'bank_list': bank_list_pse,
            'forma_pago': forma_pago,
            
        })
#         render_values.update({
#             'cities' : [],
#             'partner_id': request.env['res.partner'].browse(int(partner_id)),
#             'country': request.env['res.country'].browse(int(49)),
#             'country_states' : country.get_website_sale_states(mode=mode[1]),
#             'countries': country.get_website_sale_countries(mode=mode[1]),
#             'credit_card_due_year_ids': credit_card_due_year_ids,
#             'credit_card_methods': credit_card_methods,
#             'bank_list': bank_list_pse,
#         })
        
#         _logger.info('render values')
#         _logger.info(render_values)
        
        


        return request.render('web_sale_extended.payment_recurring', values)
