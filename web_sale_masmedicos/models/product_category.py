# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    certified_policy_id = fields.Many2one('ir.ui.view', string='Certificado de poliza')
    policy_type = fields.Selection([('individual', 'Individual'), ('collective', 'Colectiva')],
                                   string='Tipo de poliza')
