# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    logo = fields.Binary(related="company_id.logo")
    # TusDatos.co
    tusdatos_request_id = fields.Char('Report id', default='')
    tusdatos_approved = fields.Boolean('Approved', default=False)
    tusdatos_email = fields.Char('Client e-mail', default='')

    subscription_id = fields.Many2one('sale.subscription', 'Suscription ID')

    beneficiary0_id = fields.Many2one('res.partner', compute="_compute_beneficiary_partner", store=True)
    beneficiary1_id = fields.Many2one('res.partner', compute="_compute_beneficiary_partner", store=True)
    beneficiary2_id = fields.Many2one('res.partner', compute="_compute_beneficiary_partner", store=True)
    beneficiary3_id = fields.Many2one('res.partner', compute="_compute_beneficiary_partner", store=True)
    beneficiary4_id = fields.Many2one('res.partner', compute="_compute_beneficiary_partner", store=True)
    beneficiary5_id = fields.Many2one('res.partner', compute="_compute_beneficiary_partner", store=True)
    beneficiary6_id = fields.Many2one('res.partner', compute="_compute_beneficiary_partner", store=True)

    @api.depends('order_line.write_date')
    def _compute_beneficiary_partner(self):

        _logger.error('****************************************666666666666666666666\++++++++++++++++++++++++')

        for rec in self:
            if rec.order_line[0].subscription_id:
                for partner in rec.order_line[0].subscription_id.subscription_partner_ids:
                    if partner.beneficiary_number == 1:
                        rec.beneficiary0_id = partner
                    if partner.beneficiary_number == 2:
                        rec.beneficiary1_id = partner
                    if partner.beneficiary_number == 3:
                        rec.beneficiary2_id = partner
                    if partner.beneficiary_number == 4:
                        rec.beneficiary3_id = partner
                    if partner.beneficiary_number == 5:
                        rec.beneficiary4_id = partner
                    if partner.beneficiary_number == 6:
                        rec.beneficiary5_id = partner
                    if partner.beneficiary_number == 7:
                        rec.beneficiary6_id = partner




    def tusdatos_approval(self):
        for record in self:
            approval = record.tusdatos_approved
            process_id = record.tusdatos_request_id
            # user_id = record.user_id
            if process_id and not approval:
                _logger.info(' '.join([str(approval), process_id]))
                # TusDatos API!!!!
                approval = self.env['api.tusdatos'].personal_data_approval(process_id)
                _logger.info(' '.join([str(approval)]))
                if approval[0]:
                    record.write({'tusdatos_approval': approval})
                    if '-' in process_id:
                        record.write({'tusdatos_request_id': approval[1]['id']})
                    # EMAIL!!! (subir)
                    record.action_quatition_send()
                else:
                    template = request.env.ref('web_sale_extended_template_sale_update',
                                               raise_if_not_found=False)
                    context = dict(self.env.context)
                    if template:
                        template_values = template.generate_email(record.id, fields=None)
                        template_values.update({
                            'email_to': record.tusdatos_email,
                            'auto_delete': False,
                            'partner_to': False,
                            'scheduled_date': False,
                        })

                        template.write(template_values)
                        cleaned_ctx = dict(self.env.context)
                        cleaned_ctx.pop('default_type', None)
                        template.with_context(lang=self.env.user.lang).send_mail(record.id, force_send=True, raise_exception=True)


    #@api.model
    #def create(self, vals):

    """
    def action_quotation_sent(self):
        _logger.error('*****************************ORDEN DE VENTA CREADA ++++++++++++++++++++++++++++++++++')
        _logger.error(self)
        super(SaleOrder, self).action_quotation_sent()
        self.action_confirm()
    """
