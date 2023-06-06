from odoo import fields, models

class Website(models.Model):
    _inherit = 'website'

    pixel_meta_id = fields.Char(string='ID del pixel de Meta')