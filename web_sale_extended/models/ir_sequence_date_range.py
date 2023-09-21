# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    number_from = fields.Float(string='Initial Number', default=False, store=True, copied=True, size=15, digits=(15, 0))
    number_next = fields.Float(string='Próximo número', required=True, default=1, store=True, copied=True, help="Número siguiente de esta secuencia", size=15, digits=(15, 0))
    number_next_actual = fields.Float(compute='_get_number_next_actual', inverse='_set_number_next_actual',string='Número Siguiente Real', help="Próximo número que se utilizará. Este número puede incrementarse frecuentemente por lo que el valor mostrado puede estar ya obsoleto.", size=15, digits=(15, 0))
    number_to = fields.Float(string='Final Number', default=False, store=True, copied=True, size=15, digits=(15, 0))
