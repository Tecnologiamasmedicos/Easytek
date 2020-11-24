# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'sale.order'
    
    logo = fields.Binary(related="company_id.logo")
    
   