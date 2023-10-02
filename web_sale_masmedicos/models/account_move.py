from odoo import models, fields, api, _, SUPERUSER_ID
from ..models.respuestas_bancolombia import respuestas


class AccountMove(models.Model):
    _inherit = 'account.move'

    nro_intentos = fields.Integer(string='Intentos de cobro automatico', default=1, copy=False)
    mensaje_recordacion_cobro = fields.Boolean(string="Mensaje recordación de cobro", default=False)

    def notify_contact_center_rechazo_bancolombia(self, codigo):
        if self.env.company.contact_center_id:
            ctx = {
                'rechazo': respuestas[codigo],
            }
            template = self.env.ref('web_sale_masmedicos.email_template_rechazo_bancolombia_liquidaciones')
            self.env['mail.template'].browse(template.id).with_context(ctx).send_mail(self.id)

    def notificar_error_recaudo(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        ctx = {'fecha': fields.Date.today()}
        template_id = self.env.ref('web_sale_masmedicos.invoice_error_recaudo').with_context(ctx)
        if template_id:
            for order in self:
                template_id.sudo().send_mail(order.id, force_send=True)

    def _registrar_archivo_pagos(self):
        subscription = self.env['sale.subscription'].sudo().search([('code', '=', self.invoice_origin)])
        product = self.invoice_line_ids[0].product_id
        sale_order = self.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
        query = """
            INSERT INTO payments_report (
                policy_number,
                certificate_number, 
                firstname,
                othernames, 
                lastname, 
                identification_document, 
                birthday_date,
                transaction_type, 
                clase,
                change_date, 
                collected_value,
                number_of_installments,
                payment_method,
                number_of_plan_installments,
                total_installments,
                number_of_installments_arrears,
                policyholder,
                sponsor_id,
                product_code,
                product_name,
                payulatam_order_id,
                payulatam_transaction_id,
                origin_document,
                sale_order,
                subscription,
                payment_type
            )
            SELECT '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s, '%s', %s, %s, %s, '%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s';
            """ % (
            subscription.number if subscription.number != False else '',
            subscription.policy_number if subscription.policy_number != False else '',
            sale_order.beneficiary0_id.firstname if sale_order.beneficiary0_id.firstname != False else '',
            sale_order.beneficiary0_id.othernames if sale_order.beneficiary0_id.othernames != False else '',
            (str(sale_order.beneficiary0_id.lastname) + ' ' + str(sale_order.beneficiary0_id.lastname2))[
            :20] if sale_order.beneficiary0_id.lastname != False else '',
            sale_order.beneficiary0_id.identification_document if sale_order.beneficiary0_id.identification_document != False else '',
            sale_order.beneficiary0_id.birthdate_date if sale_order.beneficiary0_id.birthdate_date != False else '',
            'R',
            product.product_class if product.product_class != False else '',
            self.payulatam_datetime.date(),
            self.amount_total if self.amount_total != False else '',
            1,
            self.payment_method_type if self.payment_method_type != False else '',
            product.subscription_template_id.recurring_rule_count if product.subscription_template_id.recurring_rule_count != False else '',
            int(self.env['account.move'].sudo().search_count(
                [('invoice_line_ids.subscription_id', '=', subscription.id), ('payulatam_state', '=', 'APPROVED')])),
            int(self.env['account.move'].sudo().search_count(
                [('invoice_line_ids.subscription_id', '=', subscription.id)])) - int(
                self.env['account.move'].sudo().search_count(
                    [('invoice_line_ids.subscription_id', '=', subscription.id),
                     ('payulatam_state', '=', 'APPROVED')])),
            subscription.policyholder if subscription.policyholder != False else '',
            self.sponsor_id.id if self.sponsor_id.id != False else 'null',
            product.default_code if product.default_code != False else '',
            product.name if product.name != False else '',
            self.payulatam_order_id if self.payulatam_order_id != False else '',
            self.payulatam_transaction_id if self.payulatam_transaction_id != False else '',
            self.name if self.name != False else '',
            sale_order.id if sale_order.id != False else 'null',
            subscription.id if subscription.id != False else 'null',
            'recurring_payment',
        )
        self.env.cr.execute(query)
