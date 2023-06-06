from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.depends('website_id')
    def has_pixel_meta_method(self):
        self.has_pixel_meta = bool(self.pixel_meta_id)

    def inverse_has_pixel_meta(self):
        if not self.has_pixel_meta:
            self.pixel_meta_id = False

    pixel_meta_id = fields.Char(
        related='website_id.pixel_meta_id',
        readonly=False, string='ID de pixel de Meta')
    has_pixel_meta = fields.Boolean(
        'Pixel de Meta',
        compute=has_pixel_meta_method,
        inverse=inverse_has_pixel_meta)