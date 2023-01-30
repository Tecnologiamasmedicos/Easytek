# -*- coding: utf-8 -*-
# from odoo import http


# class WebSaleMasmedicos(http.Controller):
#     @http.route('/web_sale_masmedicos/web_sale_masmedicos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/web_sale_masmedicos/web_sale_masmedicos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('web_sale_masmedicos.listing', {
#             'root': '/web_sale_masmedicos/web_sale_masmedicos',
#             'objects': http.request.env['web_sale_masmedicos.web_sale_masmedicos'].search([]),
#         })

#     @http.route('/web_sale_masmedicos/web_sale_masmedicos/objects/<model("web_sale_masmedicos.web_sale_masmedicos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('web_sale_masmedicos.object', {
#             'object': obj
#         })
