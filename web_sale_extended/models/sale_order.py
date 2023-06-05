# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import time, json, logging
from odoo.http import request
from odoo.tools import ustr, consteq, float_compare
import hashlib
import hmac

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    logo = fields.Binary(related="company_id.logo")
    tusdatos_request_id = fields.Char('Report id', default='')
    tusdatos_approved = fields.Boolean('Approved', default=False)
    tusdatos_email = fields.Char('Client e-mail', default='')
    tusdatos_request_expired = fields.Boolean('Request Expired')
    
    tusdatos_typedoc = fields.Char('Tipo de documento', default='')
    tusdatos_send = fields.Boolean('Solicitud enviada', default=False)  
    
    campo_vacio = fields.Boolean('Campo vacio', default=False)  
    assisted_purchase = fields.Boolean('Venta Asistida', default=False) 
    recovery_email_sent = fields.Boolean('Email recuperacion', default=False)  
    product_code = fields.Char(string='Código producto', related='order_line.product_id.default_code', store=True)
    cancel_date = fields.Datetime('Fecha cancelación')
    product_name = fields.Char(string='Nombre producto', related='main_product_id.name', store=True)

    subscription_id = fields.Many2one('sale.subscription', 'Suscription ID')
    beneficiary0_id = fields.Many2one('res.partner')
    beneficiary1_id = fields.Many2one('res.partner')
    beneficiary2_id = fields.Many2one('res.partner')
    beneficiary3_id = fields.Many2one('res.partner')
    beneficiary4_id = fields.Many2one('res.partner')
    beneficiary5_id = fields.Many2one('res.partner')
    beneficiary6_id = fields.Many2one('res.partner')
    pet1_id = fields.Many2one('res.partner')
    pet2_id = fields.Many2one('res.partner')
    pet3_id = fields.Many2one('res.partner')
    pet4_id = fields.Many2one('res.partner')
    pet5_id = fields.Many2one('res.partner')
    pet6_id = fields.Many2one('res.partner')
    payulatam_order_id = fields.Char('ID de Orden de PayU')
    payulatam_transaction_id = fields.Char('ID de Transacción de PayU')
    payulatam_signature = fields.Char('Signature de la Transacción')
    payulatam_state = fields.Char('Estado Transacción de PayU')
    payulatam_datetime = fields.Datetime('Fecha y Hora de la Transacción')
    payulatam_credit_card_token = fields.Char('Token Para Tarjetas de Crédito')
    payulatam_credit_card_masked = fields.Char('Mascara del Número de Tarjeta')
    payulatam_credit_card_identification = fields.Char('Identificación')
    payulatam_credit_card_method = fields.Char('Metodo de Pago')
    payulatam_request_expired = fields.Boolean('Request Expired')
    payulatam_request_pending = fields.Boolean('Request Pending')
    state =  fields.Selection(selection_add=[('payu_pending', 'Esperando Aprobación'),('payu_approved', 'Pago Aprobado')])
    main_product_id = fields.Many2one('product.product', string="Plan Elegido", compute="_compute_main_product_id", store=True)
    payment_method_type = fields.Selection([
        ("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),
        ("Product Without Price", "Beneficio"),
    ])

    benefice_payment_method = fields.Selection([
        ("payroll_discount", "Descuento de nómina"),
        ("window_payment", "Pago por ventanilla"),
        ("libranza_discount", "Descuento por libranza"),
    ], string="Tipo descuento Sponsor")
    collection_attempts = fields.Integer('Intentos de cobro', store=True, default=0)
    buyer_account_type = fields.Selection([
        ("1", "Cuenta Corriente"), 
        ("7", "A la mano / Ahorros"), 
        # ("2", "Tarjeta de Crédito MasterCard"),
        # ("3", "Tarjeta de Crédito Visa"),
        # ("4", "Tarjeta de Crédito Amex"),
    ])
    buyer_account_number = fields.Char('Numero de cuenta')
    nonce = fields.Char('nonce')
    auth_tag = fields.Char('auth_tag')
    secretkey = fields.Char('secretkey')
    debit_request = fields.Boolean('Solicitud debito', default=False, store=True)
    debit_request_date = fields.Date(string='Fecha accion ciclo de cobro', store=True)
    update_account_bancolombia = fields.Boolean('Actualizar cuenta bancolombia', default=False, store=True)
    sent_hubspot = fields.Boolean('Enviado a HubSpot', default=False, store=True)
    
    @api.depends('order_line', 'state', 'partner_id')
    def _compute_sponsor_id(self):
        for rec in self:
            if rec.partner_id.id != 4:
                if rec.main_product_id.categ_id.sponsor_id: 
                    rec.sponsor_id = rec.main_product_id.categ_id.sponsor_id
                    
    sponsor_id = fields.Many2one('res.partner', compute=_compute_sponsor_id, store=True)

    def action_cancel(self):
        self.write({
            'cancel_date': fields.Datetime.now()
        })
        return super(SaleOrder, self).action_cancel()
    
    def action_payu_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'payu_pending',
            'date_order': fields.Datetime.now()
        })

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        #self.with_context(context)._action_confirm()
        #if self.env.user.has_group('sale.group_auto_done_setting'):
        #    self.action_done()
        return True
    
    def action_payu_approved(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))
        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'payu_approved',
            'date_order': fields.Datetime.now()
        })
        context = self._context.copy()
        context.pop('default_name', None)
        return True
    
    @api.depends('order_line')
    def _compute_main_product_id(self):
        for line in self.order_line:
            if line.product_id.is_product_landpage:
                self.main_product_id = line.product_id
            
            
            
    def _send_order_confirmation_mail(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        """
        template_id = self._find_mail_template(force_confirmation_template=True)
        if template_id:
            for order in self:
                order.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow")
        """
        if self.main_product_id.categ_id.welcome_mail_template_id:
            template_id = self.main_product_id.categ_id.welcome_mail_template_id
        else:
            template_id = self.env['mail.template'].search([('payulatam_welcome_process', '=', True)], limit=1)
        if template_id:
            for order in self:
                #order.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment')
                template_id.sudo().send_mail(order.id)

    def send_welcome_email(self):
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)
        if self.main_product_id.categ_id.welcome_mail_template_id:
            template_id = self.main_product_id.categ_id.welcome_mail_template_id
        else:
            template_id = self.env['mail.template'].search([('payulatam_welcome_process', '=', True)], limit=1)
        if template_id:
            for order in self:
                template_id.sudo().send_mail(order.id)
                
    def _send_order_payu_latam_approved(self):
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)
        template_id = self.env['mail.template'].search([('payulatam_approved_process', '=', True)], limit=1)
        if template_id:
            for order in self:
                template_id.sudo().send_mail(order.id)
                
                
    def _send_order_payu_latam_rejected(self):
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)
        template_id = self.env['mail.template'].search([('payulatam_rejected_process', '=', True)], limit=1)
        if template_id:
            for order in self:
                template_id.sudo().send_mail(order.id)
                
            

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
    
    
    def cron_get_status_tusdatos(self):
        """
        Se tienen en cuenta las ordenes que no han enviado peticiones a tusdatos
        """
        need_to_send_tusdatos_sale_ids = self.env['sale.order'].search([('tusdatos_send', '=', False), ('tusdatos_typedoc', '!=', '')])
        _logger.error('***************************** ENVIANDO PETICIONES A TUSDATOS ++++++++++++++++++++++++++++++++++')
        for need_to_send_tusdatos_sale_id in need_to_send_tusdatos_sale_ids:
            expedition_date = str(need_to_send_tusdatos_sale_id.partner_id.expedition_date)
            expedition_date = '/'.join(expedition_date.split('-')[::-1])
            tusdatos_validation = self.env['api.tusdatos'].launch_query_tusdatos(
                str(need_to_send_tusdatos_sale_id.partner_id.identification_document),
                str(need_to_send_tusdatos_sale_id.tusdatos_typedoc),
                expedition_date)

            if tusdatos_validation and tusdatos_validation.get('process_id'):            
                need_to_send_tusdatos_sale_id.write({'tusdatos_send': True, 'tusdatos_request_id': tusdatos_validation['process_id']})
                body_message = """
                    <b><span style='color:blue;'>TusDatos - Solicitud de Verificación</span></b><br/>
                    <b>No. Solicitud:</b> %s<br/>
                    <b>Respuesta:</b> %s
                """ % (
                    tusdatos_validation['process_id'],
                    json.dumps(tusdatos_validation),
                )
                _logger.error('******************* Response request tusdatos --------------------------')
                _logger.error(json.dumps(tusdatos_validation))
                need_to_send_tusdatos_sale_id.message_post(body=body_message, type="comment")
            """Aseguramos que las transacciones ocurren cada 5 segundos"""
            time.sleep(6)

        """Se tienen en cuenta únicamente ordenes de venta que no esten aprobadas pero que tengan un número de proceso
        de parte de tusdatos."""
        sale_ids = self.env['sale.order'].search([
            ('tusdatos_send', '=', True),
            ('tusdatos_approved', '=', False),
            ('tusdatos_request_id', '!=', ''),
            ('tusdatos_request_expired', '=', False)
        ])
        _logger.error('***************************** INICIANDO CRON DE CONSULTAS EN TUSDATOS ++++++++++++++++++++++++++++++++++')
        _logger.error(sale_ids)
        for sale_id in sale_ids:
            approval = sale_id.tusdatos_approved
            process_id = sale_id.tusdatos_request_id
            type_doc = sale_id.tusdatos_typedoc
            if process_id and not approval:
                _logger.info(' '.join([str(approval), process_id]))
                _logger.error('***************************** CONSULTA EN TUS DATOS ++++++++++++++++++++++++++++++++++')
                approval = self.env['api.tusdatos'].personal_data_approval(process_id)

                if approval[1]['estado'] == 'finalizado':      
                    sale_id.write({'tusdatos_request_id': approval[1].get('id')})              
                    if 'LISTA_ONU' in approval[1]['errores'] or 'lista_onu' in approval[1]['errores'] or 'OFAC' in approval[1]['errores'] or 'ofac' in approval[1]['errores']:
                        # Enviar retry y obtener el nuevo jobid
                        _logger.error('-----------------------------------Retry----------------------')
                        endpoint = 'retry'
                        _logger.error('-----------------------------------Query retry----------------------')
                        if '-' in process_id:
                            query = {'id': approval[1].get('id'), 'typedoc': type_doc}
                        else:
                            query = {'id': process_id, 'typedoc': type_doc}
                        _logger.error(query)
                        validation = self.env['api.tusdatos'].request_tusdatos_api(endpoint, query)
                        # obtengo nuevo jobid
                        _logger.error('-----------------------------------Respuesta Retry----------------------')
                        _logger.error(validation)
                        process_id2 = validation.get('jobid')
                        # Vuelvo a hacer el request a results con el nuevo jobid
                        # sale_id.write({'tusdatos_request_id': approval[1].get('id')})
                        approval = self.env['api.tusdatos'].personal_data_approval(process_id2)
                        _logger.error('-----------------------------------New request----------------------')
                        _logger.error(approval)
                        if approval[1].get('estado') == 'procesando':
                            _logger.error('-----------------------------------Entro al continue----------------------')
                            continue
                    else:
                        approval = self.env['api.tusdatos'].personal_data_approval(approval[1].get('id'))
                        
                        if approval[0]:
                            _logger.error('***************************** LLEGA POSITIVO LA VERIFICACION EN TUS DATOS ++++++++++++++++++++++++++++++++++')
                            _logger.error(approval[0])
                            _logger.error(approval[0])
                            sale_id.write({'tusdatos_approved': True})
                            _logger.error('prodcesssssssss')
                            _logger.error(process_id)
                            #if '-' in process_id:
                                #sale_id.write({'tusdatos_request_id': approval[1]['id']})
                            body_message = """
                                <b><span style='color:green;'>TusDatos - Solicitud de Verificación Aprobada</span></b><br/>
                                <b>Respuesta:</b> %s<br/>
                            """ % (
                                json.dumps(approval),
                            )
                            sale_id.message_post(body=body_message, type="comment")
                        else:
                            if approval[1] and 'estado' in approval[1]:
                                if approval[1]['estado'] in ('error, tarea no valida'):
                                    message = """<b><span style='color:red;'>TusDatos - Solicitud de Verificación Rechazada</span></b><br/>
                                                <b>Respuesta Error en Tusdatos.co: Esta respuesta se puede dar por que transcurrieron 4 horas o más 
                                                entre la consulta en tusdatos al momento de la compra y la verificación de Odoo en tus datos para 
                                                ver si la respuesta en positiva o negativa </b><br/><b>Respuesta:</b> %s"""% (
                                                    json.dumps(approval),
                                                )
                                    sale_id.write({'tusdatos_request_expired' : True,})
                                    sale_id.message_post(body=message)
                                else:
                                    message = """<b><span style='color:red;'>TusDatos - Solicitud de Verificación Rechazada</span></b><br/>
                                    <b>Respuesta:</b> %s
                                    """ % (
                                        json.dumps(approval),
                                    )
                                    sale_id.write({'tusdatos_request_expired' : True,})
                                    sale_id.message_post(body=message)
                            else:
                                message = """<b><span style='color:red;'>TusDatos - Solicitud de Verificación Rechazada</span></b><br/>
                                Esta respuesta se da por que el documento del comprador se encuentra reportado
                                en las lista Onu o OFAC<br/>
                                <b>Respuesta:</b> %s""" % (
                                    json.dumps(approval),
                                )
                                sale_id.write({'tusdatos_request_expired' : True,})
                                sale_id.message_post(body=message)
                               
                else:
                    continue

    def _prepare_subscription_data(self, template):
        res = super(SaleOrder, self)._prepare_subscription_data(template) 
        current_date = date.today()     
        if template.is_fixed_policy:
            _logger.info('El template es de una poliza fija')               
            if current_date.day > template.cutoff_day:
                date_start = current_date + relativedelta(months=1)
                date_start = date_start.replace(day=1)
                stage_id = 1
            else:
                date_start = current_date.replace(day=1)
                stage_id = 2
            res.update({
                'date_start': date_start,
                'date': template.final_date,
                'stage_id': stage_id
            })
        else:
            date_start = current_date + timedelta(days=1)
            res.update({
                'date_start': date_start
            })
        return res

    def create_subscriptions(self):
        """
        Create subscriptions based on the products' subscription template.

        Create subscriptions based on the templates found on order lines' products. Note that only
        lines not already linked to a subscription are processed; one subscription is created per
        distinct subscription template found.

        :rtype: list(integer)
        :return: ids of newly create subscriptions
        """
        res = []
        for order in self:
            to_create = self._split_subscription_lines()
            # create a subscription for each template with all the necessary lines
            for template in to_create:
                values = order._prepare_subscription_data(template)
                values['recurring_invoice_line_ids'] = to_create[template]._prepare_subscription_line_data()
                subscription = self.env['sale.subscription'].sudo().create(values)
                if not template.is_fixed_policy:
                    subscription.onchange_date_start()
                res.append(subscription.id)
                to_create[template].write({'subscription_id': subscription.id})
                subscription.message_post_with_view(
                    'mail.message_origin_link', values={'self': subscription, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id, author_id=self.env.user.partner_id.id
                )
                """ Una sola subscripción por orden de venta """
                order.write({
                    'subscription_id': subscription.id,
                })
        return res
    
    
    def cron_get_status_payu_latam(self):
        """ selección de ordenes de venta a procesar, que están pendientes de respuesta de payu """
        sale_ids = self.env['sale.order'].search([
            ('payulatam_transaction_id', '!=', ''),
            ('state', '=', 'payu_pending'),
            ('payulatam_request_expired', '=', False),
            ('payulatam_datetime', '!=', False),
        ])
        _logger.error(sale_ids)
        for sale in sale_ids:
            """ Consultando orden en payu """
            if sale.payulatam_transaction_id:
                _logger.error(sale.payulatam_transaction_id)
                _logger.error(sale.payment_method_type)
                """ si existe una transacción """
                date_now = fields.datetime.now()
                date_difference = date_now - sale.payulatam_datetime
                if sale.payment_method_type == 'Cash':
                    _logger.error(date_difference.seconds)
                    if date_difference.seconds > 3600:
                        """ si existe una transacción """
                        response = self.env['api.payulatam'].payulatam_get_response_transaction(sale.payulatam_transaction_id)
                        #_send_order_payu_latam_approved
                        _logger.error('++++++++++++++++++++++++++ respuesta cron payu latam +++++++++++++++++++++++++++++++++++++++')
                        _logger.error(response)
                        if response['code'] != 'SUCCESS':
                            raise ValidationError("""Error de comunicación con Payu: %s""", (json.dumps(response)))
                        if response['result']['payload']['state'] == 'DECLINED':
                            message = """<b><span style='color:red;'>PayU Latam - Transacción en efectivo declinada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_rejected()
                            sale.action_cancel()
                        if response['result']['payload']['state'] == 'EXPIRED':
                            message = """<b><span style='color:red;'>PayU Latam - Transacción en efectivo expirada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_rejected()
                            sale.action_cancel()
                        if response['result']['payload']['state'] == 'APPROVED':
                            sale.write({
                                'payulatam_state': 'TRANSACCIÓN EN EFECTIVO APROBADA',
                                'payulatam_datetime': datetime.fromtimestamp(int(response['result']['payload']['operationDate']) / 1e3)
                            })
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
                                SELECT '%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', %s, %s, '%s', %s, %s, %s, '%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s' WHERE NOT EXISTS(SELECT * FROM payments_report WHERE payulatam_order_id='%s');
                            """ %(
                                sale.subscription_id.number if sale.subscription_id.number != False else '',
                                sale.subscription_id.policy_number if sale.subscription_id.policy_number != False else '',
                                sale.beneficiary0_id.firstname if sale.beneficiary0_id.firstname != False else '', 
                                sale.beneficiary0_id.othernames if sale.beneficiary0_id.othernames != False else '',
                                (str(sale.beneficiary0_id.lastname) + ' ' + str(sale.beneficiary0_id.lastname2))[:20] if sale.beneficiary0_id.lastname != False else '', 
                                sale.beneficiary0_id.identification_document if sale.beneficiary0_id.identification_document != False else '', 
                                str(sale.beneficiary0_id.birthdate_date) if sale.beneficiary0_id.birthdate_date != False else 'null',
                                'R', 
                                sale.main_product_id.product_class if sale.main_product_id.product_class != False else '', 
                                sale.payulatam_datetime.date(), 
                                sale.amount_total if sale.amount_total != False else '', 
                                1, 
                                sale.payment_method_type if sale.payment_method_type != False else '', 
                                sale.main_product_id.subscription_template_id.recurring_rule_count if sale.main_product_id.subscription_template_id.recurring_rule_count  != False else '', 
                                1, 
                                0, 
                                sale.subscription_id.policyholder if sale.subscription_id.policyholder != False else '', 
                                sale.sponsor_id.id if sale.sponsor_id.id != False else 'null', 
                                sale.main_product_id.default_code if sale.main_product_id.default_code != False else '', 
                                sale.main_product_id.name if sale.main_product_id.name != False else '', 
                                sale.payulatam_order_id if sale.payulatam_order_id != False else '', 
                                sale.payulatam_transaction_id if sale.payulatam_transaction_id != False else '', 
                                sale.name if sale.name != False else '', 
                                sale.id if sale.id != False else 'null',
                                sale.subscription_id.id if sale.subscription_id.id  != False else 'null',
                                'new_sale',
                                sale.payulatam_order_id if sale.payulatam_order_id != False else ''
                            )
                            sale.env.cr.execute(query)
                            sale.action_payu_approved()
                            message = """<b><span style='color:green;'>PayU Latam - Transacción en efectivo aprobada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_approved()
                if sale.payment_method_type == 'PSE':
                    _logger.error(date_difference.seconds)
                    if date_difference.seconds > 600:
                        """ si existe una transacción """
                        response = self.env['api.payulatam'].payulatam_get_response_transaction(sale.payulatam_transaction_id)
                        #_send_order_payu_latam_approved
                        _logger.error('++++++++++++++++++++++++++ respuesta cron payu latam +++++++++++++++++++++++++++++++++++++++')
                        _logger.error(response)
                        if response['code'] != 'SUCCESS':
                            raise ValidationError("""Error de comunicación con Payu: %s""" % (json.dumps(response)))
                        if response['result']['payload']['state'] == 'DECLINED':
                            message = """<b><span style='color:red;'>PayU Latam - Transacción PSE declinada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_rejected()
                            sale.action_cancel()
                        if response['result']['payload']['state'] == 'EXPIRED':
                            message = """<b><span style='color:red;'>PayU Latam - Transacción PSE expirada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_rejected()
                            sale.action_cancel()
                        if response['result']['payload']['state'] == 'APPROVED':
                            sale.write({
                                'payulatam_state': 'TRANSACCIÓN PSE APROBADA',
                                'payulatam_datetime': datetime.fromtimestamp(int(response['result']['payload']['operationDate']) / 1e3)
                            })
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
                                SELECT '%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', %s, %s, '%s', %s, %s, %s, '%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s' WHERE NOT EXISTS(SELECT * FROM payments_report WHERE payulatam_order_id='%s');
                            """ %(
                                sale.subscription_id.number if sale.subscription_id.number != False else '',
                                sale.subscription_id.policy_number if sale.subscription_id.policy_number != False else '',
                                sale.beneficiary0_id.firstname if sale.beneficiary0_id.firstname != False else '', 
                                sale.beneficiary0_id.othernames if sale.beneficiary0_id.othernames != False else '',
                                (str(sale.beneficiary0_id.lastname) + ' ' + str(sale.beneficiary0_id.lastname2))[:20] if sale.beneficiary0_id.lastname != False else '', 
                                sale.beneficiary0_id.identification_document if sale.beneficiary0_id.identification_document != False else '', 
                                str(sale.beneficiary0_id.birthdate_date) if sale.beneficiary0_id.birthdate_date != False else 'null',
                                'R', 
                                sale.main_product_id.product_class if sale.main_product_id.product_class != False else '', 
                                sale.payulatam_datetime.date(), 
                                sale.amount_total if sale.amount_total != False else '', 
                                1, 
                                sale.payment_method_type if sale.payment_method_type != False else '', 
                                sale.main_product_id.subscription_template_id.recurring_rule_count if sale.main_product_id.subscription_template_id.recurring_rule_count  != False else '', 
                                1, 
                                0, 
                                sale.subscription_id.policyholder if sale.subscription_id.policyholder != False else '', 
                                sale.sponsor_id.id if sale.sponsor_id.id != False else 'null', 
                                sale.main_product_id.default_code if sale.main_product_id.default_code != False else '', 
                                sale.main_product_id.name if sale.main_product_id.name != False else '', 
                                sale.payulatam_order_id if sale.payulatam_order_id != False else '', 
                                sale.payulatam_transaction_id if sale.payulatam_transaction_id != False else '', 
                                sale.name if sale.name != False else '', 
                                sale.id if sale.id != False else 'null',
                                sale.subscription_id.id if sale.subscription_id.id  != False else 'null',
                                'new_sale',
                                sale.payulatam_order_id if sale.payulatam_order_id != False else ''
                            )
                            sale.env.cr.execute(query)
                            sale.action_payu_approved()
                            message = """<b><span style='color:green;'>PayU Latam - Transacción PSE aprobada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_approved()
                if sale.payment_method_type == 'Credit Card':
                    _logger.error(date_difference.seconds)
                    if date_difference.seconds > 600:
                        """ si existe una transacción """
                        response = self.env['api.payulatam'].payulatam_get_response_transaction(sale.payulatam_transaction_id)
                        #_send_order_payu_latam_approved
                        _logger.error('++++++++++++++++++++++++++ respuesta cron payu latam +++++++++++++++++++++++++++++++++++++++')
                        _logger.error(response)
                        if response['code'] != 'SUCCESS':
                            raise ValidationError("""Error de comunicación con Payu: %s""" % (json.dumps(response)))
                        if response['result']['payload']['state'] == 'DECLINED':
                            message = """<b><span style='color:red;'>PayU Latam - Transacción con tarjeta de crédito declinada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_rejected()
                            sale.action_cancel()
                        if response['result']['payload']['state'] == 'EXPIRED':
                            message = """<b><span style='color:red;'>PayU Latam - Transacción con tarjeta de crédito expirada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_rejected()
                            sale.action_cancel()
                        if response['result']['payload']['state'] == 'APPROVED':
                            sale.write({
                                'payulatam_state': 'TRANSACCIÓN CON TARJETA DE CRÉDITO APROBADA',
                                'payulatam_datetime': datetime.fromtimestamp(int(response['result']['payload']['operationDate']) / 1e3)
                            })
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
                                SELECT '%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', %s, %s, '%s', %s, %s, %s, '%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s' WHERE NOT EXISTS(SELECT * FROM payments_report WHERE payulatam_order_id='%s');
                            """ %(
                                sale.subscription_id.number if sale.subscription_id.number != False else '',
                                sale.subscription_id.policy_number if sale.subscription_id.policy_number != False else '',
                                sale.beneficiary0_id.firstname if sale.beneficiary0_id.firstname != False else '', 
                                sale.beneficiary0_id.othernames if sale.beneficiary0_id.othernames != False else '',
                                (str(sale.beneficiary0_id.lastname) + ' ' + str(sale.beneficiary0_id.lastname2))[:20] if sale.beneficiary0_id.lastname != False else '', 
                                sale.beneficiary0_id.identification_document if sale.beneficiary0_id.identification_document != False else '', 
                                str(sale.beneficiary0_id.birthdate_date) if sale.beneficiary0_id.birthdate_date != False else 'null',
                                'R', 
                                sale.main_product_id.product_class if sale.main_product_id.product_class != False else '', 
                                sale.payulatam_datetime.date(), 
                                sale.amount_total if sale.amount_total != False else '', 
                                1, 
                                sale.payment_method_type if sale.payment_method_type != False else '', 
                                sale.main_product_id.subscription_template_id.recurring_rule_count if sale.main_product_id.subscription_template_id.recurring_rule_count  != False else '', 
                                1, 
                                0, 
                                sale.subscription_id.policyholder if sale.subscription_id.policyholder != False else '', 
                                sale.sponsor_id.id if sale.sponsor_id.id != False else 'null', 
                                sale.main_product_id.default_code if sale.main_product_id.default_code != False else '', 
                                sale.main_product_id.name if sale.main_product_id.name != False else '', 
                                sale.payulatam_order_id if sale.payulatam_order_id != False else '', 
                                sale.payulatam_transaction_id if sale.payulatam_transaction_id != False else '', 
                                sale.name if sale.name != False else '', 
                                sale.id if sale.id != False else 'null',
                                sale.subscription_id.id if sale.subscription_id.id  != False else 'null',
                                'new_sale',
                                sale.payulatam_order_id if sale.payulatam_order_id != False else ''
                            )
                            sale.env.cr.execute(query)
                            sale.action_payu_approved()
                            message = """<b><span style='color:green;'>PayU Latam - Transacción de pago con tarjeta de crédito aprobada</span></b><br/>
                            <b>Respuesta:</b> %s
                            """ % (response['result']['payload'])
                            sale.message_post(body=message)
                            sale._send_order_payu_latam_approved()

    def cron_confirm_order_approved_payu_latam(self):
        """ Selección de ordenes de venta que estan aprobadas por PayU y confirmmarlas """
        sale_ids = self.env['sale.order'].search([('state', '=', 'payu_approved'),('assisted_purchase', '=', True)])
        _logger.error(sale_ids)
        beneficiary_list = []
        for sale in sale_ids:            
            sale.action_confirm()
            sale._send_order_confirmation_mail()
            
            sale.partner_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            sale.beneficiary0_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            sale.beneficiary1_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            sale.beneficiary2_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            sale.beneficiary3_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            sale.beneficiary4_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            sale.beneficiary5_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            sale.beneficiary6_id.write({
                'subscription_id': sale.subscription_id.id
            })
            
            beneficiary_list.append((4, sale.partner_id.id))
            beneficiary_list.append((4, sale.beneficiary0_id.id))
            beneficiary_list.append((4, sale.beneficiary1_id.id))
            beneficiary_list.append((4, sale.beneficiary2_id.id))
            beneficiary_list.append((4, sale.beneficiary3_id.id))
            beneficiary_list.append((4, sale.beneficiary4_id.id))
            beneficiary_list.append((4, sale.beneficiary5_id.id))
            beneficiary_list.append((4, sale.beneficiary6_id.id))

            sale.pet1_id.write({
                'subscription_id': sale.subscription_id.id
            })

            sale.pet2_id.write({
                'subscription_id': sale.subscription_id.id
            })

            sale.pet3_id.write({
                'subscription_id': sale.subscription_id.id
            })

            sale.pet4_id.write({
                'subscription_id': sale.subscription_id.id
            })

            sale.pet5_id.write({
                'subscription_id': sale.subscription_id.id
            })

            sale.pet6_id.write({
                'subscription_id': sale.subscription_id.id
            })

            beneficiary_list.append((4, sale.pet1_id.id))
            beneficiary_list.append((4, sale.pet2_id.id))
            beneficiary_list.append((4, sale.pet3_id.id))
            beneficiary_list.append((4, sale.pet4_id.id))
            beneficiary_list.append((4, sale.pet5_id.id))
            beneficiary_list.append((4, sale.pet6_id.id))
            
            sale.subscription_id.write({
                'subscription_partner_ids': beneficiary_list
            })

    def generate_access_token(self, order_id):        
        order = self.env['sale.order'].sudo().browse(order_id)
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        token_str = '%s%s%s' % (order.partner_id.id, order.amount_total, order.currency_id.id)
        access_token = hmac.new(secret.encode('utf-8'), token_str.encode('utf-8'), hashlib.sha256).hexdigest()
        return access_token
    
    
    def generate_link(self, order_id):        
        token = self.generate_access_token(order_id)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = ('%s/shop/payment/assisted_purchase/%s?access_token=%s') % (
            base_url,
            order_id,
            token
        )        
        return link
    
    def generate_link_update_bancolombia_account(self, sale_order_id):
        token = self.generate_access_token(sale_order_id)
        order_id = self.env['sale.order'].sudo().browse(sale_order_id)
        product_id = order_id.main_product_id
        base_url = "https://" + product_id.website_id.domain if product_id.website_id.domain else self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = ('%s/update/bancolombia/account?reference=%s&order_id=%s&partner_id=%s&access_token=%s') % (
            base_url,
            order_id.name,
            order_id.id,
            order_id.partner_id.id,
            token
        )        
        return link
    
    def _send_payment_link_assisted_purchase_email(self):        
        template_id = self.env.ref('web_sale_extended.payment_link_assisted_purchase_email_template').id
        template = self.env['mail.template'].browse(template_id)
        template.sudo().send_mail(self.id, force_send=True)

    def send_recovery_email(self):
        template_id = self.env.ref('web_sale_extended.recovery_main_insured_email_template').id
        template = self.env['mail.template'].browse(template_id)
        template.sudo().send_mail(self.id, force_send=True)

    def _cron_send_recovery_email_main_insured(self):
        """ Selección de ordenes de venta que estan aprobadas por PayU y que no se envio correo """
        sale_ids = self.env['sale.order'].search([('state', '=', 'payu_approved'), ('recovery_email_sent', '=', False)])
        for sale in sale_ids:
            new_date = sale.date_order + timedelta(hours=2)
            current_date = datetime.now()
            if current_date > new_date: 
                sale.send_recovery_email()
                sale.recovery_email_sent = True

    def write(self, vals):
        if 'state' in vals and vals['state'] == 'sale' and self.partner_id.id == 4:
            _logger.info('La orden de venta pertenece a Public user, No puede pasar al estado pedido de venta.')
            _logger.info(self)
            raise ValidationError('La orden de venta pertenece a Public user, No puede pasar al estado pedido de venta.')
        else:
            return super(SaleOrder, self).write(vals)

    def delete_token_payulatam(self):
        if self.payment_method_type == 'Credit Card' and self.payulatam_credit_card_token != '':           
            command = "REMOVE_TOKEN"
            removeCreditCardToken = {
                "payerId": self.partner_id.id,
                "creditCardTokenId": self.payulatam_credit_card_token
            }
            credit_card_values = {
                "command": command,
                "removeCreditCardToken": removeCreditCardToken
            }
            response = request.env['api.payulatam'].request_payulatam_api(command, credit_card_values)
            if response['code'] != 'SUCCESS':
                body_message = """
                    <b><span style='color:red;'>PayU Latam - Error en procesi de eliminacion del token</span></b><br/>
                    <b>Código:</b> %s<br/>
                    <b>Error:</b> %s
                """ % (
                    response['code'],
                    response['error'], 
                )
                self.message_post(body=body_message, type="comment")
            else:
                body_message = """
                    <b><span style='color:green;'>PayU Latam - Proceso de eliminacion del token exitoso</span></b><br/>
                    <b>Token:</b> %s<br/> 
                    <b>Mascara:</b> %s<br/>
                    <b>Documento:</b> %s<br/>
                    <b>Metodo:</b> %s
                """ % (
                    response['creditCardToken']['creditCardTokenId'],
                    response['creditCardToken']['maskedNumber'],
                    response['creditCardToken']['identificationNumber'],
                    response['creditCardToken']['paymentMethod'],
                )
                self.message_post(body=body_message, type="comment")
                self.write({
                    'payulatam_credit_card_token': '',
                    'payulatam_credit_card_masked': '',
                    'payulatam_credit_card_identification': '',
                    'payulatam_credit_card_method': ''
                })
        else:
            raise UserError('El metodo de pago no es Tarjeta de Credito o no tiene token')
        
    def update_bancolombia_account(self):
        self.update_account_bancolombia = True
        template_id = self.env.ref('web_sale_extended.email_template_update_bancolombia_account').id
        template = self.env['mail.template'].browse(template_id)
        template.sudo().send_mail(self.id, force_send=True)

    def register_bancolombia_account(self):
        self.update_account_bancolombia = True
        template_id = self.env.ref('web_sale_extended.email_template_assisted_purchase_bancolombia').id
        template = self.env['mail.template'].browse(template_id)
        template.sudo().send_mail(self.id, force_send=True)
        
    def _cron_register_assisted_purchase_hubspot(self):
        sale_order_ids = self.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('date_order', '<=', fields.datetime.now() - timedelta(hours=24)),
            ('sent_hubspot', '=', False)
        ], limit=45)
        for sale_order_id in sale_order_ids:
            time.sleep(2)
            subscription = sale_order_id.subscription_id
            deal_id = self.env['api.hubspot'].search_deal_id(subscription)
            if deal_id == False:
                continue
            else:
                sale_order_id.sent_hubspot = True
                if sale_order_id.assisted_purchase == True:
                    deal_properties = {
                        "venta_asistida": "SI"
                    }
                else:
                    deal_properties = {
                        "venta_asistida": "NO"
                    }
                self.env['api.hubspot'].update_deal(deal_id, deal_properties)