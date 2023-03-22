import datetime
import logging
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteSaleExtended(WebsiteSale):
    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def confirm_order(self, **post):
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        order = request.website.sale_get_order()
        terminos_condiciones = order.order_line[0].product_id.categ_id.terminos_condiciones
        terminos_condiciones_name = order.order_line[0].product_id.categ_id.terminos_condiciones_name
        politicas = order.order_line[0].product_id.categ_id.politicas
        politicas_name = order.order_line[0].product_id.categ_id.politicas_name
        vals = {'date': datetime.datetime.now(), 'ip': ip_address, 'order_id': order.id,
                'sponsor_id': order.order_line[0].product_id.categ_id.sponsor_id.id,
                'identificacion_cliente': order.partner_id.identification_document,
                'terminos_condiciones': terminos_condiciones, 'politicas': politicas,
                'terminos_condiciones_name': terminos_condiciones_name, 'politicas_name': politicas_name}
        request.env['log.aceptacion.politicas'].create(vals)
        res = super(WebsiteSaleExtended, self).confirm_order(**post)
        return res
