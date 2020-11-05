# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
logger = logging.getLogger(name_)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    website_partner_type = fields.Char(string='partner_type', compute='_get_website_partner_type', store=False)
    
    
    @api.depends('zip','city_id')
    def _get_website_partner_type(self):
        for record in self:
            record.website_partner_type = record.zip + record.street


# class web_sale_extended(models.Model):
#     _name = 'web_sale_extended.web_sale_extended'
#     _description = 'web_sale_extended.web_sale_extended'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100