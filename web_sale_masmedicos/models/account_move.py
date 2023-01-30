from odoo import models, fields, api, _
from ..models.respuestas_bancolombia import respuestas




class AccountMove(models.Model):
    _inherit = 'account.move'

    nro_intentos = fields.Integer(string='Intentos de cobro automatico', default=1, copy=False)

    def notify_contact_center_rechazo_bancolombia(self, codigo):
        if self.env.company.contact_center_id:
            ctx = {
                'rechazo': respuestas[codigo],
            }
            template = self.env.ref('web_sale_masmedicos.email_template_rechazo_bancolombia_liquidaciones')
            self.env['mail.template'].browse(template.id).with_context(ctx).send_mail(self.id)