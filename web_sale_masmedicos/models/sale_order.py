# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from ..tools import sftp_utils
import time, json, logging
from datetime import date, timedelta, datetime
import os
from ..models.respuestas_bancolombia import respuestas
from odoo.exceptions import AccessError, MissingError, UserError
from stat import S_ISDIR

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tusdatos_reported = fields.Boolean('Reportado', default=False, help='Este campo será verdadero cuando se encuentre en la lista ONU o OFAC')
    nro_intentos = fields.Integer(string='Intentos de cobro automatico', default=1, copy=False)


    def conection_sftp(self):
        company = self.env.company
        if company.sftp_server_env_bancolombia == 'test':
            host = company.sftp_hostname_QA_bancolombia
            port = int(company.sftp_port_QA_bancolombia)
            password = company.sftp_password_QA_bancolombia
            user = company.sftp_user_QA_bancolombia
            path = company.sftp_path_output_QA_bancolombia
            path_processed = company.sftp_path_processed_QA_bancolombia
        elif company.sftp_server_env == 'prod':
            host = company.sftp_hostname_bancolombia
            port = int(company.sftp_port_bancolombia)
            password = company.sftp_password_bancolombia
            user = company.sftp_user_bancolombia
            path = company.sftp_path_output_bancolombia
            path_processed = company.sftp_path_processed_bancolombia
        else:
            raise UserError(_('No hay un servidor SFTP configurado'))

        return sftp_utils.connect(host, user, password, port), path, path_processed

    def _cron_read_files_sftp(self):
        current_date = fields.Date.today()
        connection, path, path_processed = self.conection_sftp()
        with connection as sftp:
            filelist = sftp.listdir_attr(path)
            lines_cuentas_incorrectas = []
            for filename in filelist:
                mode = filename.st_mode
                filename = filename.filename
                if not filename.startswith('OK_') and not S_ISDIR(mode) and \
                        (filename.startswith('REC') or filename.startswith('rec')):
                    with sftp.open(path + filename) as f:
                        leer = f.read()
                        lines = leer.splitlines()
                        encabezado = lines[0].decode("latin-1")
                        lines_cuentas_incorrectas = [encabezado] if len(lines) > 1 else []
                        for line in lines[1:]:
                            line = line.decode("latin-1")
                            referencia = line[110:140].strip().upper()
                            codigo_respuesta = line[171:174].strip()
                            collection_date = datetime.strptime(line[174:182].strip(), '%Y%m%d').date()
                            collection_datetime = datetime.now().replace(year=collection_date.year, month=collection_date.month, day=collection_date.day)
                            order = self.env['sale.order'].search([('name', '=ilike', referencia)])
                            if order:
                                if order.state != 'sale':
                                    if codigo_respuesta in ['OK0', 'OK1', 'OK2', 'OK3', 'OK4']:
                                        print('recaudo exitoso')
                                        #Se comenta para no hacer validacion SARLAFT en pruebas, en producción se debe descomentar
                                        # if not order.tusdatos_send:
                                        #     order.get_status_tusdatos_order()
                                        # if order.tusdatos_approved:
                                        order.action_confirm()
                                        order._send_order_confirmation_mail()
                                        order.write({
                                            'payulatam_state': 'APPROVED',
                                            'payulatam_order_id': order.name,
                                            'payulatam_datetime': collection_datetime
                                        })
                                        order._registrar_archivo_pagos()

                                    elif codigo_respuesta in respuestas:
                                        if codigo_respuesta in ['D12', 'D03', 'D10', 'R04', 'R17']:
                                            lines_cuentas_incorrectas.append("\n" + line)
                                        order.notify_contact_center_rechazo_bancolombia(codigo_respuesta)

                                        body_message = """
                                            <b><span style='color:red;'>Respuesta Bancolombia</span></b><br/>
                                            <b>Respuesta:</b> %s<br/>
                                        """ % (respuestas[codigo_respuesta],)
                                        order.message_post(body=body_message, type="comment")
                                else:
                                    order.notificar_error_en_recaudo()
                            elif referencia.startswith('LIS'):
                                move = self.env['account.move'].search([('name', '=ilike', referencia)])
                                if move:
                                    if move.payulatam_state:
                                        move.notificar_error_recaudo()
                                    elif codigo_respuesta in ['OK0', 'OK1', 'OK2', 'OK3', 'OK4']:
                                        subscription = self.env['sale.subscription'].sudo().search([('code', '=', move.invoice_origin)])
                                        sale_order = self.env['sale.order'].sudo().search([('subscription_id', '=', subscription.id)])
                                        move.write({'payulatam_state': 'APPROVED',
                                                    'payulatam_order_id': sale_order.name,
                                                    'payulatam_datetime': collection_datetime})
                                        move.invoice_line_ids[0].subscription_id.stage_id = 2
                                        move._registrar_archivo_pagos()
                                        body_message = """<b><span style='color:green;'>Respuesta Bancolombia</span></b><br/>
                                                                                    <b>Respuesta:</b> %s<br/>""" % (
                                            respuestas[codigo_respuesta],
                                        )
                                        move.message_post(body=body_message, type="comment")

                                    elif codigo_respuesta in respuestas:
                                        if codigo_respuesta in ['D12', 'D03', 'D10', 'R04', 'R17']:
                                            lines_cuentas_incorrectas.append("\n" + line)

                                        if move.nro_intentos > 1:
                                            move.notify_contact_center_rechazo_bancolombia(codigo_respuesta)
                                            subscription = self.env['sale.subscription'].search(
                                                [('code', '=', move.invoice_origin)])
                                            if subscription:
                                                subscription.write({'stage_id': 4, 'close_reason_id': 13})
                                            sale_order = self.env['sale.order'].sudo().search(
                                                [('subscription_id', '=', subscription.id)])
                                            if sale_order:
                                                sale_order.write({'state': 'done',
                                                                  'cancel_date': fields.Datetime.now()})
                                            deal_id = self.env['api.hubspot'].search_deal_id(subscription)
                                            deal_properties = {
                                                "estado_de_la_poliza": "Cancelado",
                                                "causal_de_cancelacion": "Falta de pago",
                                                "fecha_efectiva_de_cancelacion": fields.Date.today()
                                            }
                                            self.env['api.hubspot'].update_deal(deal_id, deal_properties)
                                            subscription._send_bancolombia_cancellation_plan_email()
                                        else:
                                            move.mensaje_recordacion_cobro = True
                                            move.send_payment = False
                                            if current_date.day >= 15:
                                                if current_date.day == 2:
                                                    dif = 28 - current_date.day
                                                else:
                                                    dif = 30 - current_date.day
                                            else:
                                                dif = 15 - current_date.day
                                            move.action_date_billing_cycle = current_date + timedelta(days=dif)

                                            subscription = self.env['sale.subscription'].search([('code', '=', move.invoice_origin)])
                                            deal_id = self.env['api.hubspot'].search_deal_id(subscription)
                                            update_properties = {
                                                "estado_de_la_poliza": "En mora",
                                                "accion_de_cobro": "Bancolombia SMS2",
                                                "estado_de_accion_de_cobro": "SI"
                                            }
                                            self.env['api.hubspot'].update_deal(deal_id, update_properties)
                                            contact_id = self.env['api.hubspot'].search_contact_id(move.partner_id)
                                            contact_properties = {
                                                "estado_de_accion_de_cobro": "SI"
                                            }
                                            self.env['api.hubspot'].update_contact_id(contact_id, contact_properties)
                                            body_message = """<b><span style='color:red;'>Respuesta Bancolombia</span></b><br/>
                                                                                        <b>Respuesta:</b> %s<br/>""" % (
                                                respuestas[codigo_respuesta],
                                            )
                                            move.message_post(body=body_message, type="comment")
                                    move.write({'nro_intentos': move.nro_intentos + 1})

                        sftp.rename(path + filename, path_processed + "/OK_" + filename)

                    if len(lines_cuentas_incorrectas) > 1:
                        try:
                            os.stat('tmp/error/')
                        except:
                            os.makedirs('tmp/error/')
                        with open('tmp/error/%s_%s.txt' % ('error', filename), 'w') as file:
                            for line in lines_cuentas_incorrectas:
                                file.write(line)
                elif not filename.startswith('OK_') and not S_ISDIR(mode) and \
                        (filename.startswith('RNOV') or filename.startswith('rnov')):
                    with sftp.open(path + filename) as f:
                        leer = f.read()
                        lines = leer.splitlines()
                        for line in lines[0:]:
                            line = line.decode("latin-1")
                            referencia = line.split(',')[8].strip().upper()
                            codigo_respuesta = line.split(',')[-1].strip().upper()
                            order = self.env["sale.order"].search([('name', '=ilike', referencia)])
                            if codigo_respuesta not in ['OK0', 'OK1', 'OK2', 'OK3', 'OK4']:
                                if order:
                                    order.novedad_rechazada(codigo_respuesta)

                        sftp.rename(path + filename, path_processed + '/OK_' + filename)
                elif not filename.startswith('Cargados-a-Easytek'):
                    sftp.rename(path + filename, path_processed + '/' + filename)

    def _registrar_archivo_pagos(self):
        for order in self:
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
                order.subscription_id.number if order.subscription_id.number != False else '',
                order.subscription_id.policy_number if order.subscription_id.policy_number != False else '',
                order.beneficiary0_id.firstname if order.beneficiary0_id.firstname != False else '',
                order.beneficiary0_id.othernames if order.beneficiary0_id.othernames != False else '',
                (str(order.beneficiary0_id.lastname) + ' ' + str(order.beneficiary0_id.lastname2))[:20] if order.beneficiary0_id.lastname != False else '',
                order.beneficiary0_id.identification_document if order.beneficiary0_id.identification_document != False else '',
                str(order.beneficiary0_id.birthdate_date.strftime("%Y-%m-%d")) if order.beneficiary0_id.birthdate_date != False else 'null',
                'R',
                order.main_product_id.product_class if order.main_product_id.product_class != False else '',
                order.payulatam_datetime.date(),
                order.amount_total if order.amount_total != False else '',
                1,
                order.payment_method_type if order.payment_method_type != False else '',
                order.main_product_id.subscription_template_id.recurring_rule_count if order.main_product_id.subscription_template_id.recurring_rule_count != False else '',
                1,
                0,
                order.subscription_id.policyholder if order.subscription_id.policyholder != False else '',
                order.sponsor_id.id if order.sponsor_id.id != False else 'null',
                order.main_product_id.default_code if order.main_product_id.default_code != False else '',
                order.main_product_id.name if order.main_product_id.name != False else '',
                order.payulatam_order_id if order.payulatam_order_id != False else '',
                order.payulatam_transaction_id if order.payulatam_transaction_id != False else '',
                order.name if order.name != False else '',
                order.id if order.id != False else 'null',
                order.subscription_id.id if order.subscription_id.id != False else 'null',
                'new_sale',
            )
            order.env.cr.execute(query)

    def get_status_tusdatos_order(self):
        self.ensure_one()
        """
        Se envia peticion a tus datos de la orden de venta
        """
        need_to_send_tusdatos_sale_ids = self.env['sale.order'].search(
            [('tusdatos_send', '=', False), ('tusdatos_typedoc', '!=', ''), ('id', '=', self.id)])
        _logger.error('***************************** ENVIANDO PETICIONES A TUSDATOS ++++++++++++++++++++++++++++++++++')
        for need_to_send_tusdatos_sale_id in need_to_send_tusdatos_sale_ids:
            expedition_date = str(need_to_send_tusdatos_sale_id.partner_id.expedition_date)
            expedition_date = '/'.join(expedition_date.split('-')[::-1])
            tusdatos_validation = self.env['api.tusdatos'].launch_query_tusdatos(
                str(need_to_send_tusdatos_sale_id.partner_id.identification_document),
                str(need_to_send_tusdatos_sale_id.tusdatos_typedoc),
                expedition_date)

            if tusdatos_validation and tusdatos_validation.get('process_id'):
                need_to_send_tusdatos_sale_id.write(
                    {'tusdatos_send': True, 'tusdatos_request_id': tusdatos_validation['process_id']})
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
            ('tusdatos_reported', '=', False),
            ('tusdatos_approved', '=', False),
            ('tusdatos_request_id', '!=', ''),
            ('tusdatos_request_expired', '=', False),
            ('id', '=', self.id)
        ])
        _logger.error(
            '***************************** INICIANDO CRON DE CONSULTAS EN TUSDATOS ++++++++++++++++++++++++++++++++++')
        _logger.error(sale_ids)
        for sale_id in sale_ids:
            approval = sale_id.tusdatos_approved
            process_id = sale_id.tusdatos_request_id
            type_doc = sale_id.tusdatos_typedoc
            if process_id and not approval:
                _logger.info(' '.join([str(approval), process_id]))
                _logger.error('***************************** CONSULTA EN TUS DATOS ++++++++++++++++++++++++++++++++++')
                # approval = self.env['api.tusdatos'].personal_data_approval(process_id)
                approval = self.env['api.tusdatos'].personal_data_approval('6460fc34-4154-43db-9438-8c5a059304c0')

                if approval[1]['estado'] == 'finalizado':
                    sale_id.write({'tusdatos_request_id': approval[1].get('id')})
                    if 'LISTA_ONU' in approval[1]['errores'] or 'lista_onu' in approval[1]['errores'] or 'OFAC' in \
                            approval[1]['errores'] or 'ofac' in approval[1]['errores']:
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
                            _logger.error(
                                '***************************** LLEGA POSITIVO LA VERIFICACION EN TUS DATOS ++++++++++++++++++++++++++++++++++')
                            _logger.error(approval[0])
                            _logger.error(approval[0])
                            sale_id.write({'tusdatos_approved': True,
                                           })
                            _logger.error('prodcesssssssss')
                            _logger.error(process_id)
                            # if '-' in process_id:
                            # sale_id.write({'tusdatos_request_id': approval[1]['id']})
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
                                                ver si la respuesta en positiva o negativa </b><br/><b>Respuesta:</b> %s""" % (
                                        json.dumps(approval),
                                    )
                                    sale_id.write({'tusdatos_request_expired': True, })
                                    sale_id.message_post(body=message)
                                else:
                                    message = """<b><span style='color:red;'>TusDatos - Solicitud de Verificación Rechazada</span></b><br/>
                                    <b>Respuesta:</b> %s
                                    """ % (
                                        json.dumps(approval),
                                    )
                                    sale_id.write({'tusdatos_request_expired': True, })
                                    sale_id.message_post(body=message)
                            else:
                                message = """<b><span style='color:red;'>TusDatos - Solicitud de Verificación Rechazada</span></b><br/>
                                Esta respuesta se da por que el documento del comprador se encuentra reportado
                                en las lista Onu o OFAC<br/>
                                <b>Respuesta:</b> %s""" % (
                                    json.dumps(approval),
                                )
                                sale_id.write({'tusdatos_request_expired': True, 'tusdatos_reported': True})
                                sale_id.message_post(body=message)
                                sale_id.action_cancel()
                                sale_id.notify_contact_center()

                else:
                    continue

    def notify_contact_center(self):
        if self.env.company.contact_center_id:
            template = self.env.ref('web_sale_masmedicos.email_template_tus_datos')
            self.env['mail.template'].browse(template.id).send_mail(self.id)

    def notify_contact_center_rechazo_bancolombia(self, codigo):
        if self.env.company.contact_center_id:
            ctx = {
                'rechazo': respuestas[codigo],
            }
            template = self.env.ref('web_sale_masmedicos.email_template_rechazo_bancolombia')
            self.env['mail.template'].browse(template.id).with_context(ctx).send_mail(self.id)

    def cron_get_status_tusdatos(self):
        """
        Se tienen en cuenta las ordenes que no han enviado peticiones a tusdatos
        """
        need_to_send_tusdatos_sale_ids = self.env['sale.order'].search(
            [('tusdatos_send', '=', False), ('tusdatos_typedoc', '!=', '')])
        _logger.error('***************************** ENVIANDO PETICIONES A TUSDATOS ++++++++++++++++++++++++++++++++++')
        for need_to_send_tusdatos_sale_id in need_to_send_tusdatos_sale_ids:
            expedition_date = str(need_to_send_tusdatos_sale_id.partner_id.expedition_date)
            expedition_date = '/'.join(expedition_date.split('-')[::-1])
            tusdatos_validation = self.env['api.tusdatos'].launch_query_tusdatos(
                str(need_to_send_tusdatos_sale_id.partner_id.identification_document),
                str(need_to_send_tusdatos_sale_id.tusdatos_typedoc),
                expedition_date)

            if tusdatos_validation and tusdatos_validation.get('process_id'):
                need_to_send_tusdatos_sale_id.write(
                    {'tusdatos_send': True, 'tusdatos_request_id': tusdatos_validation['process_id']})
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
            ('tusdatos_reported', '=', False),
            ('tusdatos_request_id', '!=', ''),
            ('tusdatos_request_expired', '=', False)
        ])
        _logger.error(
            '***************************** INICIANDO CRON DE CONSULTAS EN TUSDATOS ++++++++++++++++++++++++++++++++++')
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
                    if 'LISTA_ONU' in approval[1]['errores'] or 'lista_onu' in approval[1]['errores'] or 'OFAC' in \
                            approval[1]['errores'] or 'ofac' in approval[1]['errores']:
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
                            _logger.error(
                                '***************************** LLEGA POSITIVO LA VERIFICACION EN TUS DATOS ++++++++++++++++++++++++++++++++++')
                            _logger.error(approval[0])
                            _logger.error(approval[0])
                            sale_id.write({'tusdatos_approved': True})
                            _logger.error('prodcesssssssss')
                            _logger.error(process_id)
                            # if '-' in process_id:
                            # sale_id.write({'tusdatos_request_id': approval[1]['id']})
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
                                                ver si la respuesta en positiva o negativa </b><br/><b>Respuesta:</b> %s""" % (
                                        json.dumps(approval),
                                    )
                                    sale_id.write({'tusdatos_request_expired': True, })
                                    sale_id.message_post(body=message)
                                else:
                                    message = """<b><span style='color:red;'>TusDatos - Solicitud de Verificación Rechazada</span></b><br/>
                                    <b>Respuesta:</b> %s
                                    """ % (
                                        json.dumps(approval),
                                    )
                                    sale_id.write({'tusdatos_request_expired': True, })
                                    sale_id.message_post(body=message)
                            else:
                                message = """<b><span style='color:red;'>TusDatos - Solicitud de Verificación Rechazada</span></b><br/>
                                Esta respuesta se da por que el documento del comprador se encuentra reportado
                                en las lista Onu o OFAC<br/>
                                <b>Respuesta:</b> %s""" % (
                                    json.dumps(approval),
                                )
                                sale_id.write({'tusdatos_request_expired': True, 'tusdatos_reported': True})
                                sale_id.message_post(body=message)
                                sale_id.notify_contact_center()

                else:
                    continue

    def notificar_error_en_recaudo(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        ctx = {'fecha': fields.Date.today()}
        template_id = self.env.ref('web_sale_masmedicos.error_en_recaudo').with_context(ctx)
        if template_id:
            for order in self:
                template_id.sudo().send_mail(order.id, force_send=True)

    def novedad_rechazada(self, rechazo):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)

        ctx = {'rechazo': respuestas[rechazo], 'fecha': fields.Date.today()}
        template_id = self.env.ref('web_sale_masmedicos.novedad_rechazada').with_context(ctx)
        if template_id:
            for order in self:
                template_id.sudo().send_mail(order.id, force_send=True)
