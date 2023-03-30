# -*- coding: utf-8 -*-
import logging, time, csv
import paramiko, holidays_co
from odoo import fields, models, tools, api,_
from datetime import date, timedelta, datetime
from odoo.osv import expression
from odoo.tools import date_utils
from Crypto.Cipher import AES
from base64 import b64decode
_logger = logging.getLogger(__name__)


class BancolombiaNewsEntry(models.Model):
    _name = 'bancolombia.news.entry'
    _auto = False
    
    agreement = fields.Char('Convenio',readonly=True)
    agreement_name = fields.Char('Nombre del convenio',readonly=True)
    buyer_document_type = fields.Char('Tipo de documento del pagador',readonly=True)
    identification_buyer = fields.Char('Identificación del cliente pagador',readonly=True)
    buyer_name = fields.Char('Nombre del Pagador',readonly=True)
    buyer_account_number = fields.Char('Número de la cuenta del pagador',readonly=True)
    buyer_account_type = fields.Char('Tipo de cuenta del pagador',readonly=True)
    efr_id = fields.Char('EFR ID',readonly=True)
    ref1 = fields.Char('Referencia 1',readonly=True)
    ref2 = fields.Char('Referencia 2',readonly=True)
    ref3 = fields.Char('Referencia 3',readonly=True)
    value_to_be_debited = fields.Char('Valor a debitar',readonly=True)
    debit_schedule_start_date = fields.Char('Fecha de inicio de programación de débitos',readonly=True)
    debit_schedule_end_date = fields.Char('Fecha de finalización de la programación de débitos',readonly=True)
    novelty_type = fields.Char('Tipo de novedad',readonly=True)
    number_retry_days = fields.Char('Número de días de reintentos',readonly=True)
    application_criteria = fields.Char('Criterios para la aplicación',readonly=True)
    payment_frequency = fields.Char('Frecuencia de pago',readonly=True)
    n_days = fields.Char('Nro. de días',readonly=True)
    payday = fields.Char('Día de Pago',readonly=True)
    debit_type = fields.Char('Tipo de debito',readonly=True)
    response_code = fields.Char('Código de respuesta',readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Order', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'bancolombia_news_entry')
        query = """
        CREATE or REPLACE VIEW bancolombia_news_entry AS(
        select 
        row_number() OVER (ORDER BY sorder.id) as id,
        '12710'::text as agreement,
        'Plan Familia Protegida'::text as agreement_name,
        (case 
            when rpdt.code='31' then '1'
            when rpdt.code='13' then '2'
            when rpdt.code='22' then '3'
            when rpdt.code='12' then '4'
            when rpdt.code='41' then '5'
            when rpdt.code='11' then '6'
            else rpdt.code end) as buyer_document_type,
        p.identification_document as identification_buyer,
        substr(p.firstname || ' ' || p.lastname, 1, 22) as buyer_name,
        sorder.buyer_account_number as buyer_account_number,
        sorder.buyer_account_type as buyer_account_type,
        '5600078'::text as efr_id,
        sorder.name as ref1,
        ''::text as ref2,
        ''::text as ref3,
        '0'::text as value_to_be_debited,
        ''::text as debit_schedule_start_date,
        ''::text as debit_schedule_end_date,
        'ING'::text as novelty_type,
        '3'::text as number_retry_days,
        '01'::text as application_criteria,
        ''::text as payment_frequency,
        ''::text as n_days,
        ''::text as payday,
        '02'::text as debit_type,
        ''::text as response_code,
        sorder.id as sale_order_id
        
        from sale_order sorder
        left join res_partner p on p.id = sorder.partner_id
        left join res_partner_document_type rpdt on rpdt.id = p.document_type_id
        where 1=1 and sorder.state='payu_pending' and sorder.debit_request='f' and sorder.sponsor_id=5521
        order by sorder.id desc
        );
        """
        self.env.cr.execute(query)
    
class BancolombiaBillingEntry(models.Model):
    _name = 'bancolombia.billing.entry'
    _auto = False
    
    #Facturacion
    type_register = fields.Char('Tipo de registro',readonly=True)
    buyer_nit = fields.Char('Nit del pagador',readonly=True)
    buyer_name = fields.Char('Nombre del pagador',readonly=True)
    buyer_bank_account = fields.Char('Cuenta bancaria del pagador',readonly=True)
    number_account_debited = fields.Char('Número de la cuenta a debitar',readonly=True)
    transaction_type = fields.Char('Tipo de transacción',readonly=True)
    transaction_value = fields.Char('Valor de la transacción',readonly=True)
    validation_indicator = fields.Char('Indicador validación Nit/Cta',readonly=True)
    ref1 = fields.Char('Referencia 1',readonly=True)
    ref2 = fields.Char('Referencia 2',readonly=True)
    expiration_date = fields.Char('Fecha de vencimiento',readonly=True)
    billed_periods = fields.Char('Periodos facturados',readonly=True)
    cycle = fields.Char('Ciclo',readonly=True)
    reserved = fields.Char('Reservado',readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Order', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'bancolombia_billing_entry')
        query = """
        CREATE or REPLACE VIEW bancolombia_billing_entry AS(
        select 
        row_number() OVER (ORDER BY sorder.id) as id,
        '6'::text as type_register,
        LPAD(''::text, 13, ' ') as buyer_nit,
        RPAD(p.firstname || ' ' || p.lastname, 20, ' ') as buyer_name,
        RPAD('5600078'::text, 9, ' ') as buyer_bank_account,
        sorder.buyer_account_number as number_account_debited,
        (case 
            when sorder.buyer_account_type='1' then '57'
            when sorder.buyer_account_type='7' then '67'
            when sorder.buyer_account_type='2' then '77'
            when sorder.buyer_account_type='3' then '87'
            when sorder.buyer_account_type='4' then '97'
            else sorder.buyer_account_type end) as transaction_type,
        LPAD(sorder.amount_total::text, 17, '0') as transaction_value,
        'N'::text as validation_indicator,
        RPAD(sorder.name::text, 30, ' ') as ref1,
        RPAD(''::text, 30, ' ') as ref2,
        ''::text as expiration_date,
        RPAD(''::text, 2, ' ') as billed_periods,
        RPAD(''::text, 3, ' ') as cycle,
        RPAD(''::text, 17, ' ') as reserved,
        sorder.id as sale_order_id
        
        from sale_order sorder
        left join res_partner p on p.id = sorder.partner_id
        left join res_partner_document_type rpdt on rpdt.id = p.document_type_id
        where 1=1 and sorder.state='payu_pending' and sorder.debit_request='f' and sorder.sponsor_id=5521
        order by sorder.id desc
        );
        """
        self.env.cr.execute(query)

    def is_business_day(self, day):
        if day.weekday() in (5, 6) or holidays_co.is_holiday_date(day) == True:
            return False
        else:
            return True

    def decrypt_eas_gcm(self, encrypted_msg):
        (ciphertext, nonce, authTag, secretKey) = encrypted_msg
        aes_cipher = AES.new(secretKey, AES.MODE_GCM, nonce)
        plaintext = aes_cipher.decrypt_and_verify(ciphertext, authTag)
        return plaintext.decode('utf-8')
        
    def _cron_generate_bancolombia_files(self):
        current_date = (datetime.now() - timedelta(hours=5)).date()
        if self.is_business_day(current_date) == True:
            name_billing_file = 'FC_VNUEVA_' + current_date.strftime("%y%m%d")
            name_news_file = 'NV_VNUEVA_' + current_date.strftime("%y%m%d")
            records_billing_entries_bancolombia =  self.env['bancolombia.billing.entry'].search([])
            records_news_entries_bancolombia =  self.env['bancolombia.news.entry'].search([])
            data = []
            data2 = []
            sum = 0
            for record in records_billing_entries_bancolombia:
                decrypted_number_account_debited = self.decrypt_eas_gcm((b64decode(record.number_account_debited), b64decode(record.sale_order_id.nonce), b64decode(record.sale_order_id.auth_tag), b64decode(record.sale_order_id.secretkey)))
                data.append([
                    record.type_register,
                    record.buyer_nit,
                    record.buyer_name,
                    record.buyer_bank_account,
                    str(decrypted_number_account_debited).ljust(17),
                    record.transaction_type,
                    (record.transaction_value).split(".")[0].zfill(15) + str(record.transaction_value).split(".")[-1].zfill(2),
                    record.validation_indicator,
                    record.ref1,
                    record.ref2,
                    current_date.strftime("%Y%m%d"),
                    record.billed_periods,
                    record.cycle,
                    record.reserved
                ])
                sum = sum + float(record.transaction_value)
            for record in records_news_entries_bancolombia:
                decrypted_account_number = self.decrypt_eas_gcm((b64decode(record.buyer_account_number), b64decode(record.sale_order_id.nonce), b64decode(record.sale_order_id.auth_tag), b64decode(record.sale_order_id.secretkey)))
                data2.append([
                    record.agreement,
                    record.agreement_name,
                    record.buyer_document_type,
                    record.identification_buyer,
                    record.buyer_name,
                    decrypted_account_number,
                    record.buyer_account_type,
                    record.efr_id,
                    record.ref1,
                    record.ref2,
                    record.ref3,
                    record.value_to_be_debited,
                    current_date.strftime("%d%m%Y"),
                    record.debit_schedule_end_date,
                    record.novelty_type,
                    record.number_retry_days,
                    record.application_criteria,
                    record.payment_frequency,
                    record.n_days,
                    record.payday,
                    record.debit_type,
                    record.response_code
                ])
            billing_control = ['1', '860038299'.zfill(13), 'Pan American Life de Colombia'[:20], '12710'.zfill(15), current_date.strftime("%Y%m%d"), '1', current_date.strftime("%Y%m%d"), str(len(data)).zfill(8), str(sum).split(".")[0].zfill(15) + str(sum).split(".")[-1].zfill(2), "".ljust(79)]

            if len(data2) != 0:
                with open('tmp/%s.txt'%(name_billing_file), 'w', encoding='utf-8', newline='') as file, open('tmp/%s.txt'%(name_news_file), 'w', encoding='utf-8', newline='') as file2:
                    for x in billing_control:
                        file.write(x)
                    for x in range(len(data)):
                        file.write('\n')
                        for y in data[x]:
                            file.write(y)
                    file.write("\n")
                    writer2 = csv.writer(file2, delimiter=',')
                    writer2.writerows(data2)
                
                sftp_server_env = self.env.user.company_id.sftp_server_env_bancolombia
                if sftp_server_env:
                    if sftp_server_env == 'prod':
                        sftp_hostname = self.env.user.company_id.sftp_hostname_bancolombia
                        sftp_port = self.env.user.company_id.sftp_port_bancolombia
                        sftp_user = self.env.user.company_id.sftp_user_bancolombia
                        sftp_password = self.env.user.company_id.sftp_password_bancolombia
                        sftp_path_input = self.env.user.company_id.sftp_path_input_bancolombia
                    else:
                        sftp_hostname = self.env.user.company_id.sftp_hostname_QA_bancolombia
                        sftp_port = self.env.user.company_id.sftp_port_QA_bancolombia
                        sftp_user = self.env.user.company_id.sftp_user_QA_bancolombia
                        sftp_password = self.env.user.company_id.sftp_password_QA_bancolombia
                        sftp_path_input = self.env.user.company_id.sftp_path_input_QA_bancolombia
                    try: 
                        client = paramiko.SSHClient() 
                        client.set_missing_host_key_policy( paramiko.AutoAddPolicy )
                        client.connect(sftp_hostname, port=int(sftp_port), username=sftp_user, password=sftp_password)
                        sftp_client = client.open_sftp()
                        sftp_client.put(
                            'tmp/%s.txt'%(name_billing_file), 
                            '%s/%s.txt'%(sftp_path_input, name_billing_file) 
                        )
                        sftp_client.put(
                            'tmp/%s.txt'%(name_news_file), 
                            '%s/%s.txt'%(sftp_path_input, name_news_file) 
                        )
                        sftp_client.close() 
                        client.close()
                    except paramiko.ssh_exception.AuthenticationException as e:
                        _logger.info('Autenticacion fallida en el servidor SFTP')
                    else:
                        for record in records_billing_entries_bancolombia:
                            record.sale_order_id.write({
                                'debit_request': True,
                                'debit_request_date': current_date
                            })
                        for record in records_news_entries_bancolombia:
                            record.sale_order_id.write({
                                'debit_request': True,
                                'debit_request_date': current_date
                            })