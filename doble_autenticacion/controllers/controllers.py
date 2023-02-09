import datetime
import logging
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from datetime import date, timedelta
import json

_logger = logging.getLogger(__name__)


class WebsiteSaleExtended(http.Controller):
    @http.route(['/send/code'], type='json', auth="public", method=['POST'], website=True)
    def send_code_mail(self, **kwargs):
        order = request.website.sale_get_order()
        correo = kwargs.get('correo')
        order.send_code(correo)
        data = {'respuesta': 'Correo enviado correctamente'}
        return json.dumps(data)

    @http.route(['/verificar'], type='json', auth="public", method=['POST'], website=True)
    def verificar(self, **kwargs):
        order = request.website.sale_get_order()
        correo = kwargs.get('correo')
        codigo = kwargs.get('codigo')
        data = {}
        if not order.partner_id.email == correo:
            data['correo'] = 'Correo diferente'
        else:
            data['correo'] = 'Correo igual'

        order.VerificarCodigo(codigo, datetime.datetime.now())
        if order.verificado:
            data['respuesta'] = 'Correcto'
        else:
            data['respuesta'] = 'Incorrecto'
        return json.dumps(data)
