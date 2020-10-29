# -*- coding: utf-8 -*-
from odoo import http


class WebSaleExtended(http.Controller):
    @http.route('/web_sale_extended/web_sale_extended/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    # @http.route('/web_sale_extended/web_sale_extended/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('web_sale_extended.listing', {
    #         'root': '/web_sale_extended/web_sale_extended',
    #         'objects': http.request.env['web_sale_extended.web_sale_extended'].search([]),
    #     })

    # @http.route('/web_sale_extended/web_sale_extended/objects/<model("web_sale_extended.web_sale_extended"):obj>/', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('web_sale_extended.object', {
    #         'object': obj
    #     })
