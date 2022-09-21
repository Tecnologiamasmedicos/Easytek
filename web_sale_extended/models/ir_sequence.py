# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class IrSequence(models.Model):
    _inherit = 'ir.sequence'
    
    logo_website_pdf  = fields.Binary(string="Image del Plan para el documento PDF", readonly=False)
    logo_header_website_sponsor  = fields.Binary(string="Image del Plan del Patrocinador en el encabezado", readonly=False)
    logo_body_website_sponsor  = fields.Binary(string="Image del Patrocinador en el cuerpo del documento", readonly=False)
    beneficiaries_number = fields.Integer(string="Número Máximo de Beneficiarios", required=True)
    sponsor_name = fields.Char('Nombre del Sponsor')
    sponsor_nit = fields.Char('Identificación del Sponsor')
    sponsor_payment_url = fields.Char('URL de la Plataforma de Pagos')
    value_policy = fields.Float('Valor Poliza')
    number_next_actual = fields.Float(compute='_get_number_next_actual', inverse='_set_number_next_actual', string='Actual Next Number', help="Next number that will be used. This number can be incremented ", size=15, digits=(15, 0))
    number_next = fields.Float(string='Next Number', required=True, default=1, help="Next number of this sequence", size=15, digits=(15, 0))
    