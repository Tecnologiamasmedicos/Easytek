from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.depends('website_id')
    def has_google_tag_manager_method(self):
        self.has_google_tag_manager = bool(self.google_tag_manager_key)

    def inverse_has_google_tag_manager(self):
        if not self.has_google_tag_manager:
            self.google_tag_manager_key = False

    google_tag_manager_key = fields.Char(
        related='website_id.google_tag_manager_key',
        readonly=False, string='Key Google Tag Manager')
    has_google_tag_manager = fields.Boolean(
        'Google Tag Manager',
        compute=has_google_tag_manager_method,
        inverse=inverse_has_google_tag_manager)



