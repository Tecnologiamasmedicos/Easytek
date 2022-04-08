# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api,_
import logging, csv, base64, os, calendar
import numpy as np
from datetime import datetime, date, timedelta
from odoo.osv import expression
from odoo.tools import date_utils
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, MissingError, UserError

_logger = logging.getLogger(__name__)
calendar.setfirstweekday(6)

    
class PaymentsReport(models.Model):
    _name = 'payments.report'
    
    policy_number = fields.Char('Número de Poliza', readonly=True)
    certificate_number = fields.Char('Número de Certificado', readonly=True)
    firstname = fields.Char('Primer Nombre', readonly=True)
    othernames = fields.Char('Segundo Nombre', readonly=True)
    lastname = fields.Char('Apellidos', readonly=True)
    identification_document = fields.Char('Número de Identificación', readonly=True)
    birthday_date = fields.Date('Fecha de nacimiento', readonly=True)    
    transaction_type = fields.Char('Tipo de transacción', readonly=True)
    clase = fields.Char('Clase', readonly=True)    
    change_date = fields.Date('Fecha de cambio', readonly=True)    
    collected_value = fields.Float('Valor recaudo', readonly=True)    
    number_of_installments = fields.Integer('Cuotas recaudo', readonly=True)    
    payment_method = fields.Selection(
        [("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),],
        string="Método de Pago"
    )
    number_of_plan_installments = fields.Integer('Cuotas plan', readonly=True)    
    total_installments = fields.Integer('Pagadas a la fecha', readonly=True)    
    number_of_installments_arrears = fields.Integer('Cuotas en mora', readonly=True)
    policyholder = fields.Char('Tomador de Póliza', readonly=True)    
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', readonly=True)
    product_code = fields.Char('Codigo del producto', readonly=True)
    product_name = fields.Char('Nombre del producto', readonly=True)
    payulatam_order_id = fields.Char('Orden ID', readonly=True)
    payulatam_transaction_id = fields.Char('Transacción ID', readonly=True)
    origin_document = fields.Char('Documento de origen', readonly=True)
    sale_order = fields.Many2one('sale.order', string='Order', readonly=True)
    subscription = fields.Many2one('sale.subscription', string='Suscripcion', readonly=True)
    payment_type = fields.Selection([
        ("new_sale", "Venta Nueva"), 
        ("recurring_payment", "Pago recurrente"), 
    ],
    string="Tipo de Pago"
    )
        
    def _complete_information_first_payment(self):
        """ selección de registros de venta a procesar, que están pendientes de respuesta de payu """
        collections_ids = self.env['payments.report'].search([
            ('policy_number', '=', ''),
            ('certificate_number', '=', ''),
        ])
        _logger.error(collections_ids)
        for collection in collections_ids:
            if collection.sale_order.state == 'sale' and collection.sale_order.subscription_id: 
                subscription = collection.sale_order.subscription_id
                collection.policy_number = subscription.number
                collection.certificate_number = subscription.policy_number
                collection.subscription = subscription.id
                collection.policyholder = subscription.policyholder

    def get_week_of_month(self, year, month, day):
        x = np.array(calendar.monthcalendar(year, month))
        week_of_month = np.where(x==day)[0][0] + 1
        return(week_of_month)
    
    def delete_all_files(self):
        archivos = os.listdir('tmp')
        if '.ipynb_checkpoints' in archivos:
            archivos.remove('.ipynb_checkpoints') 
        if len(archivos) != 0:
            for x in archivos:
                os.remove('/tmp/%s'%(x))
                
    def monthToNum(self, num_month):
        return {
                '1' : 'Enero',
                '2' : 'Febrero',
                '3' : 'Marzo',
                '4' : 'Abril',
                '5' : 'Mayo',
                '6' : 'Junio',
                '7' : 'Julio',
                '8' : 'Agosto',
                '9' : 'Septiembre',
                '10' : 'Octubre',
                '11' : 'Noviembre',
                '12' : 'Diciembre',
        }[num_month]
    
    def action_buttton(self):
        raise UserError('Action button')

    def _cron_send_email_collection_file(self):
        self.delete_all_files()
        p = {}
        current_date = date.today()
        start_date = current_date - timedelta(days=7)
        if start_date.month != current_date.month:
            start_date2 = start_date
            start_date = current_date.replace(day=1) 
            end_date2 = (start_date2.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)   
            start_date2 = start_date2.strftime('%Y-%m-%d')
            end_date2 = end_date2.strftime('%Y-%m-%d')
            start_date2_date = datetime.strptime(start_date2, '%Y-%m-%d').date()
            end_date2_date = datetime.strptime(end_date2, '%Y-%m-%d').date()
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = current_date - timedelta(days=1)
        if end_date.month != current_date.month:
            end_date = (end_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)  
        end_date = end_date.strftime('%Y-%m-%d')
        
        start_date_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_date = datetime.strptime(end_date, '%Y-%m-%d').date()        
        
        headers = ['Número de Poliza', 'Número de Certificado',	'Primer Nombre', 'Segundo Nombre', 'Apellidos', 'Número de Identificación', 'Fecha de nacimiento', 'Tipo de transacción', 'Clase', 'Fecha de cambio', 'Valor recaudo', 'Cuotas recaudo', 'Método de Pago', 'Cuotas plan', 'Pagadas a la fecha', 'Cuotas en mora', 'Sponsor', 'Tomador de poliza', 'Codigo de producto', 'Nombre plan', 'Orden ID', 'Transacción ID']
        records =  self.env['payments.report'].search([('change_date', '>=', start_date), ('change_date', '<=', end_date)])
        payment = ''
        for record in records:
            if record.payment_method == 'Credit Card':
                payment = 'Tarjeta de credito'
            elif record.payment_method == 'Cash':
                payment = 'Efectivo'
            elif record.payment_method == 'PSE':
                payment = 'Pse'
                
            if record.payment_method != 'Product Without Price':
                if record.policy_number in p:
                    p[record.policy_number].append([record.policy_number, record.certificate_number, record.firstname, record.othernames, record.lastname, record.identification_document, record.birthday_date, record.transaction_type, record.clase, record.change_date.strftime('%d/%m/%Y'), record.collected_value, record.number_of_installments, payment, record.number_of_plan_installments, record.total_installments, record.number_of_installments_arrears, record.sponsor_id.name, record.policyholder, record.product_code, record.product_name, record.payulatam_order_id, record.payulatam_transaction_id])
                else:
                    p[record.policy_number] = [[record.policy_number, record.certificate_number, record.firstname, record.othernames, record.lastname, record.identification_document, record.birthday_date, record.transaction_type, record.clase, record.change_date.strftime('%d/%m/%Y'), record.collected_value, record.number_of_installments, payment, record.number_of_plan_installments, record.total_installments, record.number_of_installments_arrears, record.sponsor_id.name, record.policyholder, record.product_code, record.product_name, record.payulatam_order_id, record.payulatam_transaction_id]]
                    
        for x in p:
            suma = 0
            for y in p.get(x):
                suma = suma + y[10]
            p.get(x).append(['Fecha inicio', start_date, 'Fecha fin', end_date, 'Numero de registros', len(p.get(x)), '', '', 'Total', suma])
            
        if 'start_date2' in locals():            
            p2 = {}
            records2 =  self.env['payments.report'].search([('change_date', '>=', start_date2), ('change_date', '<=', end_date2)])
            payment = ''
            for record in records2:
                if record.payment_method == 'Credit Card':
                    payment = 'Tarjeta de credito'
                elif record.payment_method == 'Cash':
                    payment = 'Efectivo'
                elif record.payment_method == 'PSE':
                    payment = 'Pse'
                    
                if record.payment_method != 'Product Without Price':             
                    if record.policy_number in p2:
                        p2[record.policy_number].append([record.policy_number, record.certificate_number, record.firstname, record.othernames, record.lastname, record.identification_document, record.birthday_date, record.transaction_type, record.clase, record.change_date.strftime('%d/%m/%Y'), record.collected_value, record.number_of_installments, payment, record.number_of_plan_installments, record.total_installments, record.number_of_installments_arrears, record.sponsor_id.name, record.policyholder, record.product_code, record.product_name, record.payulatam_order_id, record.payulatam_transaction_id])
                    else:
                        p2[record.policy_number] = [[record.policy_number, record.certificate_number, record.firstname, record.othernames, record.lastname, record.identification_document, record.birthday_date, record.transaction_type, record.clase, record.change_date.strftime('%d/%m/%Y'), record.collected_value, record.number_of_installments, payment, record.number_of_plan_installments, record.total_installments, record.number_of_installments_arrears, record.sponsor_id.name, record.policyholder, record.product_code, record.product_name, record.payulatam_order_id, record.payulatam_transaction_id]]
                    
            for x in p2:
                suma = 0
                for y in p2.get(x):
                    suma = suma + y[10]
                p2.get(x).append(['Fecha inicio', start_date2, 'Fecha fin', end_date2, 'Numero de registros', len(p2.get(x)), '', '', 'Total', suma])
            
            for x in p.keys():
                p[x].insert(0, headers)
                with open('tmp/Recaudos_%s_%s_Semana%s.csv'%(x, start_date_date.strftime('%m%Y'), self.get_week_of_month(start_date_date.year, start_date_date.month, start_date_date.day)), 'w', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file, delimiter=',')
                    writer.writerows(p.get(x))
                    file.close()
                    
            for x in p2.keys():
                p2[x].insert(0, headers)
                with open('tmp/Recaudos_%s_%s_Semana%s.csv'%(x, start_date2_date.strftime('%m%Y'), self.get_week_of_month(start_date2_date.year, start_date2_date.month, start_date2_date.day)), 'w', encoding='utf-8', newline='') as file2:
                    writer2 = csv.writer(file2, delimiter=',')
                    writer2.writerows(p2.get(x))
                    file2.close()
                    
            archivos = os.listdir('tmp')
            if '.ipynb_checkpoints' in archivos:
                archivos.remove('.ipynb_checkpoints') 
                
            if len(archivos) != 0:
                adjuntos = []
                adjuntos2 = []
                for x in archivos:
                    with open ('tmp/%s'%(x), 'rb') as archivo:
                        encoded = base64.b64encode(archivo.read())

                        att = self.env['ir.attachment'].sudo().create({
                            'name': '%s'%(x),
                            'type': 'binary',
                            'datas': encoded,                    
                            'mimetype': 'text/csv'
                        })

                        if x.split('_')[2][0:2] == start_date2[5:7]:                    
                            adjuntos.append(att)
                        else:
                            adjuntos2.append(att)

                mail_values = {
                    'subject': 'Recaudos %s Semana %s - %s hasta %s'%(self.monthToNum(str(start_date_date.month)), self.get_week_of_month(start_date_date.year, start_date_date.month, start_date_date.day), start_date_date.strftime('%d/%m/%Y'), end_date_date.strftime('%d/%m/%Y')),
                    'body_html' : 'Cordial saludo,<br/>Adjunto enviamos el archivo de recaudos semanal del %s al %s.<br/>Quedamos atentos a cualquier inquietud.<br/>Saludos,<br/>Más Médicos'%(start_date_date.strftime('%d/%m/%Y'), end_date_date.strftime('%d/%m/%Y')),
                    'email_to': 'operaciones@masmedicos.co',
                    # 'email_to': 'WMartinez@palig.com',
                    # 'email_cc': 'contabilidad@masmedicos.co, operaciones@masmedicos.co, directordeproyectos@masmedicos.co',
                    'email_from': 'contacto@masmedicos.co',
                    'attachment_ids': [(6, 0 , [x.id for x in adjuntos2])]
                }

                mail_values2 = {
                    'subject': 'Recaudos %s Semana %s - %s hasta %s'%(self.monthToNum(str(start_date2_date.month)), self.get_week_of_month(start_date2_date.year, start_date2_date.month, start_date2_date.day), start_date2_date.strftime('%d/%m/%Y'), end_date2_date.strftime('%d/%m/%Y')),
                    'body_html' : 'Cordial saludo,<br/>Adjunto enviamos el archivo de recaudos semanal del %s al %s.<br/>Quedamos atentos a cualquier inquietud.<br/>Saludos,<br/>Más Médicos'%(start_date2_date.strftime('%d/%m/%Y'), end_date2_date.strftime('%d/%m/%Y')),
                    'email_to': 'operaciones@masmedicos.co',
                    # 'email_to': 'WMartinez@palig.com',
                    # 'email_cc': 'contabilidad@masmedicos.co, operaciones@masmedicos.co, directordeproyectos@masmedicos.co',
                    'email_from': 'contacto@masmedicos.co',
                    'attachment_ids': [(6, 0 , [x.id for x in adjuntos])]
                }

                self.env['mail.mail'].sudo().create(mail_values).send()
                self.env['mail.mail'].sudo().create(mail_values2).send()
        else:            
            for x in p.keys():
                p[x].insert(0, headers)
                with open('tmp/Recaudos_%s_%s_Semana%s.csv'%(x, start_date_date.strftime('%m%Y'), self.get_week_of_month(start_date_date.year, start_date_date.month, start_date_date.day)), 'w', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file, delimiter=',')
                    writer.writerows(p.get(x))
                    file.close()
                
            archivos = os.listdir('tmp')
            if '.ipynb_checkpoints' in archivos:
                archivos.remove('.ipynb_checkpoints') 
                
            if len(archivos) != 0:
                adjuntos = []
                for x in archivos:
                    with open ('tmp/%s'%(x), 'rb') as archivo:
                        encoded = base64.b64encode(archivo.read())

                        att = self.env['ir.attachment'].sudo().create({
                            'name': '%s'%(x),
                            'type': 'binary',
                            'datas': encoded,                    
                            'mimetype': 'text/csv'
                        })
                        adjuntos.append(att)

                mail_values = {
                    'subject': 'Recaudos %s Semana %s - %s hasta %s'%(self.monthToNum(str(start_date_date.month)), self.get_week_of_month(start_date_date.year, start_date_date.month, start_date_date.day), start_date_date.strftime('%d/%m/%Y'), end_date_date.strftime('%d/%m/%Y')),
                    'body_html' : 'Cordial saludo,<br/>Adjunto enviamos el archivo de recaudos semanal del %s al %s.<br/>Quedamos atentos a cualquier inquietud.<br/>Saludos,<br/>Más Médicos'%(start_date_date.strftime('%d/%m/%Y'), end_date_date.strftime('%d/%m/%Y')),
                    'email_to': 'operaciones@masmedicos.co',
                    # 'email_to': 'WMartinez@palig.com',
                    # 'email_cc': 'contabilidad@masmedicos.co, operaciones@masmedicos.co, directordeproyectos@masmedicos.co',
                    'email_from': 'contacto@masmedicos.co',
                    'attachment_ids': [(6, 0 , [x.id for x in adjuntos])]
                }

                self.env['mail.mail'].sudo().create(mail_values).send()