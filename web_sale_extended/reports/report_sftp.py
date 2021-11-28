# -*- coding: utf-8 -*-
import logging, time, csv
import paramiko
from odoo import fields, models, tools, api,_
from datetime import date, timedelta, datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class SftpReportLine(models.Model):
    _name = 'report.sftp'
    _auto = False
    _description = 'This is the lines in the sftp report'
    
    policy_number = fields.Char('Número de Grupo / Póliza',readonly=True)
    certificate_number = fields.Char('Número de Certificado',readonly=True)
    firstname = fields.Char('Primer Nombre',readonly=True)
    othernames = fields.Char('Segundo Nombre',readonly=True)
    lastname = fields.Char('Apellidos',readonly=True)
    birthdate_date = fields.Char('Fecha de Nacimiento',readonly=True)
    date_start = fields.Char('Fecha Efectiva',readonly=True)
    date_start2 = fields.Char('Fecha de Empleo',readonly=True)
    date_start3 = fields.Char('Fecha de Cambio',readonly=True)
    gender = fields.Char('Sexo',readonly=True)
    identification_document = fields.Char('Número de Seguro Social / Cédula',readonly=True)
    default_code = fields.Char('Código de Plan',readonly=True)
    recurring_interval = fields.Char('Tipo de Inscripción PALIG',readonly=True)
    sponsor_name = fields.Char('Compañía',readonly=True)
    country = fields.Char('País',readonly=True)
    country2 = fields.Char('País 2',readonly=True)
    email = fields.Char('E-Mail',readonly=True)
    marital_status = fields.Char('Estado Civil',readonly=True)
    phone = fields.Char('Teléfono Fijo',readonly=True)
    mobile = fields.Char('Teléfono',readonly=True)
    street = fields.Char('Dirección 1',readonly=True)
    street2 = fields.Char('Dirección 2',readonly=True)
    state_id = fields.Char('Departamento',readonly=True)
    city_name = fields.Char('Ciudad',readonly=True)
    partner_zip_code = fields.Char('Código Postal',readonly=True)
    ocupation = fields.Char('Ocupación',readonly=True)
    localization = fields.Char('Lozalización',readonly=True)
    salary = fields.Char('Salario',readonly=True)
    salary_mode = fields.Char('Modo de Salario',readonly=True)
    lifevolume = fields.Char('Lifevolume',readonly=True)
    addvolume = fields.Char('Addvolume',readonly=True)
    email1 = fields.Char('Dirección de Correo 1',readonly=True)
    email2 = fields.Char('Dirección de Correo 2',readonly=True)
    email_state = fields.Char('Estado de correo',readonly=True)
    email_city = fields.Char('Ciudad de correo',readonly=True)
    email_country = fields.Char('País de Correo',readonly=True)
    zip_code = fields.Char('Código Postal de Correo',readonly=True)
    commentaries = fields.Char('Comentarios',readonly=True)    
    aniversary = fields.Char('Aniversario',readonly=True)
    first_due = fields.Char('Primer Vencimiento',readonly=True)
    change_type = fields.Char('Tipo de Cambio',readonly=True)
    second_identification = fields.Char('Segunda Indentificación',readonly=True)
    second_type_identification = fields.Char('Tipo Segunda Identificación',readonly=True)    
    ocupation2 = fields.Char('Ocupación',readonly=True)
    reference_initial = fields.Char('Inicial de Referencia / Título',readonly=True)
    insegurability_test = fields.Char('Prueba de Asegurabilidad',readonly=True)
    subsidiary = fields.Char('Subsidiaria',readonly=True)
    palig = fields.Char('Código Clase PALIG',readonly=True)
    date_start4 = fields.Date('Fecha creacion',readonly=True)

    sponsor_nit = fields.Char('Nit del Tomador',readonly=True)
    sponsor_payment_url = fields.Char('Pasarela de Pagos',readonly=True)
    phone2 = fields.Char('Teléfono Fijo 2',readonly=True)
  

    
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_sftp')
        query = """
        CREATE or REPLACE VIEW report_sftp AS(
        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sub.policy_number as certificate_number,
        LPAD(sub.number::text, 5, '0') as policy_number,
        p.firstname,
        p.othernames,
        p.lastname || ' ' || p.lastname2 as lastname,
        TO_CHAR(p.birthdate_date, 'mm/dd/yyyy')as birthdate_date,
        TO_CHAR(sub.date_start, 'mm/dd/yyyy') as date_start,        
        TO_CHAR(sub.date_start, 'mm/dd/yyyy') as date_start2,
        (case when subtmpl.is_fixed_policy='t' then TO_CHAR(sub.date_start, 'mm/dd/yyyy') else TO_CHAR(sub.date_start - CAST('1 days' AS INTERVAL), 'mm/dd/yyyy') end)as date_start3,
        sub.date_start as date_start4,
        p.gender,
        p.identification_document,
        pro.default_code,
        --subtmpl.recurring_interval,
        '1'::text as recurring_interval,
        '009'::varchar as sponsor_name,
        seq.sponsor_nit,
        seq.sponsor_payment_url,
        'CO'::varchar as country,
        '79'::varchar as country2,
        p.email as email,

        (case when p.mobile LIKE '%)%' then split_part(p.mobile,')',2) else p.mobile end) as mobile,        
        (case when p.phone LIKE '%)%' then split_part(p.phone,')',2) else p.phone end) as phone,
        (case when p.buyer='t' then p.street else p.address_beneficiary end)as street,
        p.street2,
        p.beneficiary_state_id as state_id,        
        (case when city.name='BOGOTÁ, D.C.' then 'BOGOTÁ D.C.' else city.name end)as city_name,        
        rcz.name as partner_zip_code,
        p.ocupation as ocupation,
        p.ocupation as ocupation2,
        ''::text as email1,
        ''::text as email2,
        ''::text as email_country,
        ''::text as commentaries,
        ''::text as reference_initial,
        ''::text as aniversary,
        TO_CHAR(sub.recurring_next_date, 'mm/dd/yyyy')as first_due,
        ''::text as second_identification,
        rpdt.abbreviation as second_type_identification,
        ''::text as insegurability_test,
        ''::text as subsidiary,
        ''::text as lifevolume,
        ''::text as addvolume,
        ''::text as email_state,
        ''::text as zip_code,
        ''::text as email_city,
        ''::text as salary_mode,
        ''::text as salary,
        ''::text as phone2,
        'A'::text as change_type,
        ''::text as localization,
        tmpl.product_class as palig,
        (case when p.marital_status='Unión Libre' then 'Union Libre' else p.marital_status end)as marital_status
        
        
        
        
        from sale_subscription sub
        left join res_partner p on p.subscription_id = sub.id
        left join res_partner_document_type rpdt on rpdt.id = p.document_type_id
        left join res_city_zip rcz on rcz.id = p.beneficiary_zip_id
        left join res_city city on rcz.city_id = city.id
        left join sale_subscription_line line on line.analytic_account_id = sub.id
        left join product_product pro on pro.id = line.product_id
        left join product_template tmpl on tmpl.id = pro.product_tmpl_id
        left join product_category cat on cat.id = tmpl.categ_id
        left join ir_sequence seq on seq.id = cat.sequence_id
        left join sale_subscription_template subtmpl on subtmpl.id = sub.template_id
        
        where 1=1 and p.main_insured='t' and sub.stage_id=2
        order by sub.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,

    def _cron_generate_ap_sftp_report(self):        
        fecha = '10/21/2021'
        fecha_date = datetime.strptime(fecha, '%m/%d/%Y')
        # current_date = date.today() - timedelta(days=1)
        nombre_archivo_ap = 'Odoo_Prin_' + fecha_date.strftime('%d%m%Y')
        nombre_archivo_bef = 'Odoo_Ben_' + fecha_date.strftime('%d%m%Y')
        data = []
        data2 = []
        beneficiario_topo = ['99999','0000000007','Usuario' ,'Prueba','Hubspot','09/19/1953','10/08/2021','F','11111','D','D1','10/08/2021','A','','MM-023','','','','009','79','1.prueba@gmail.com','3333333333','09/19/1953','Cale 11 #4a-9','','CO','Magdalena','SANTA MARTA','Pensionada']
        records_ap =  self.env['report.sftp'].search([('date_start4', '=', fecha_date)])        
        records_bef =  self.env['report.beneficiary.sftp'].search([('date_start4', '=', fecha_date)])

        for record in records_ap:
            data.append([
                record.policy_number if record.policy_number != False else '', 
                record.certificate_number if record.certificate_number != False else '', 
                record.firstname if record.firstname != False else '', 
                record.othernames if record.othernames != False else '', 
                record.lastname if record.lastname != False else '', 
                record.birthdate_date if record.birthdate_date != False else '', 
                record.date_start if record.date_start != False else '', 
                record.gender if record.gender != False else '', 
                record.identification_document if record.identification_document != False else '', 
                record.date_start2 if record.date_start2 != False else '', 
                record.date_start3 if record.date_start3 != False else '', 
                record.change_type if record.change_type != False else '', 
                record.street if record.street != False else '', 
                record.street2 if record.street2 != False else '', 
                record.city_name if record.city_name != False else '', 
                record.marital_status if record.marital_status != False else '', 
                record.country if record.country != False else '', 
                record.partner_zip_code if record.partner_zip_code != False else '', 
                record.mobile if record.mobile != False else '', 
                record.email if record.email != False else '', 
                record.localization if record.localization != False else '', 
                record.palig if record.palig != False else '', 
                record.recurring_interval if record.recurring_interval != False else '', 
                record.salary if record.salary != False else '', 
                record.salary_mode if record.salary_mode != False else '', 
                record.lifevolume if record.lifevolume != False else '', 
                record.addvolume if record.addvolume != False else '', 
                record.email1 if record.email1 != False else '', 
                record.email2 if record.email2 != False else '', 
                record.email_city if record.email_city != False else '', 
                record.email_state if record.email_state != False else '', 
                record.email_country if record.email_country != False else '', 
                record.zip_code if record.zip_code != False else '', 
                record.default_code if record.default_code != False else '', 
                record.commentaries if record.commentaries != False else '', 
                record.first_due if record.first_due != False else '', 
                record.aniversary if record.aniversary != False else '', 
                record.sponsor_name if record.sponsor_name != False else '', 
                record.country2 if record.country2 != False else '', 
                record.second_identification if record.second_identification != False else '', 
                record.second_type_identification if record.second_type_identification != False else '', 
                record.ocupation if record.ocupation != False else '', 
                record.reference_initial if record.reference_initial != False else '', 
                record.insegurability_test if record.insegurability_test != False else '', 
                record.subsidiary if record.subsidiary != False else '', 
                record.phone if record.phone != False else '', 
                record.ocupation2 if record.ocupation != False else ''
            ])
        for record in records_bef:
            data2.append([
                record.policy_number if record.policy_number != False else '', 
                record.certificate_number if record.certificate_number != False else '', 
                record.firstname if record.firstname != False else '', 
                record.othernames if record.othernames != False else '', 
                record.lastname if record.lastname != False else '', 
                record.birthdate_date if record.birthdate_date != False else '', 
                record.date_start if record.date_start != False else '', 
                record.gender if record.gender != False else '', 
                record.identification_document if record.identification_document != False else '', 
                record.relationship if record.relationship != False else '', 
                record.clerk_code if record.clerk_code != False else '', 
                record.change_date if record.change_date != False else '', 
                record.change_type if record.change_type != False else '', 
                record.date_end if record.date_end != False else '', 
                record.default_code if record.default_code != False else '', 
                record.recurring_interval if record.recurring_interval != False else '', 
                record.date_start2 if record.date_start2 != False else '', 
                record.insegurability_test if record.insegurability_test != False else '', 
                record.sponsor_name if record.sponsor_name != False else '', 
                record.country if record.country != False else '', 
                record.email if record.email != False else '', 
                record.mobile if record.mobile != False else '', 
                record.birthdate_date2 if record.birthdate_date2 != False else '', 
                record.street if record.street != False else '', 
                record.phone if record.phone != False else '', 
                record.country2 if record.country2 != False else '', 
                record.state_id if record.state_id != False else '', 
                record.city_name if record.city_name != False else '', 
                record.ocupation if record.ocupation != False else ''
            ])

        if len(data) != 0:
            if len(data2) == 0:
                data2.append(beneficiario_topo)
        
            with open('tmp/%s.csv'%(nombre_archivo_ap), 'w', encoding='utf-8', newline='') as file, open('tmp/%s.csv'%(nombre_archivo_bef), 'w', encoding='utf-8', newline='') as file2:
                writer = csv.writer(file, delimiter=',')
                writer.writerows(data)
                writer2 = csv.writer(file2, delimiter=',')
                writer2.writerows(data2)  
            
            # HOST = 'sftp.masmedicos.site'
            # USER = 'easytekqa'
            # PASS = 'easytekqa_2021'
        
            # try: 
            #     client = paramiko.SSHClient() 
            #     client.set_missing_host_key_policy( paramiko.AutoAddPolicy )
            #     client.connect(HOST, username=USER, password=PASS)
            #     sftp_client = client.open_sftp()
            #     sftp_client.put(
            #         'tmp/%s.csv'%(nombre_archivo_ap), 
            #         '/home/webapp01/masmedicosqa/origen/asegurados/easytekqa/%s.csv'%(nombre_archivo_ap) 
            #     )
            #     sftp_client.put(
            #         'tmp/%s.csv'%(nombre_archivo_bef), 
            #         '/home/webapp01/masmedicosqa/origen/dependientes/easytekqa/%s.csv'%(nombre_archivo_bef) 
            #     )
            #     sftp_client.close() 
            #     client.close()                
            # except paramiko.ssh_exception.AuthenticationException as e:
            #     _logger.info('Autenticacion fallida en el servidor SFTP')
        
class SftpReportBeneficiaryLine(models.Model):
    _name = 'report.beneficiary.sftp'
    _auto = False
    _description = 'This is the lines in the sftp report'
    
    policy_number = fields.Char('Número de Grupo / Póliza',readonly=True)
    certificate_number = fields.Char('Número de Certificado',readonly=True)
    firstname = fields.Char('Primer Nombre',readonly=True)
    othernames = fields.Char('Segundo Nombre',readonly=True)
    lastname = fields.Char('Apellidos',readonly=True)
    birthdate_date = fields.Char('Fecha de Nacimiento',readonly=True)
    date_start = fields.Char('Fecha Efectiva',readonly=True)
    gender = fields.Char('Sexo',readonly=True)
    identification_document = fields.Char('Número de Seguro Social / Cédula',readonly=True)
    relationship = fields.Char('Relación',readonly=True)
    clerk_code = fields.Char('Código de Dependiente',readonly=True)
    change_date = fields.Char('Fecha de Cambio',readonly=True)
    change_type = fields.Char('Tipo de Cambio',readonly=True)
    date_end = fields.Char('Fecha Terminación',readonly=True)
    default_code = fields.Char('Código de Plan',readonly=True)
    recurring_interval = fields.Char('Tipo de Inscripción',readonly=True)
    date_start2 = fields.Char('Inicial de Referencia / Título',readonly=True)
    insegurability_test = fields.Char('Prueba de Asegurabilidad',readonly=True)
    sponsor_name = fields.Char('Compañía',readonly=True)
    country = fields.Char('País',readonly=True)
    email = fields.Char('Correo Electrónico',readonly=True)
    mobile = fields.Char('Teléfono Móvil',readonly=True)
    birthdate_date2 = fields.Char('Fecha de Nacimiento',readonly=True)
    street = fields.Char('Dirección de Residencia',readonly=True)
    phone = fields.Char('Teléfono Fijo',readonly=True)
    country2 = fields.Char('País',readonly=True)
    state_id = fields.Char('Estado',readonly=True)
    city_name = fields.Char('Ciudad',readonly=True)
    ocupation = fields.Char('Ocupación',readonly=True)
    date_start4 = fields.Date('Fecha creacion',readonly=True)

    street2 = fields.Char('Dirección2',readonly=True)
    partner_zip_code = fields.Char('Ciudad',readonly=True)
    subsidiary = fields.Char('Subsidiaria',readonly=True)
    sponsor_nit = fields.Char('Nit del Tomador',readonly=True)
    sponsor_payment_url = fields.Char('Pasarela de Pagos',readonly=True)
    
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_sftp')
        query = """
        CREATE or REPLACE VIEW report_beneficiary_sftp AS(
        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sub.policy_number as certificate_number,
        LPAD(sub.number::text, 5, '0') as policy_number,
        p.firstname,
        p.othernames,
        p.lastname || ' ' || p.lastname2 as lastname,
        TO_CHAR(p.birthdate_date, 'mm/dd/yyyy')as birthdate_date,
        TO_CHAR(p.birthdate_date, 'mm/dd/yyyy')as birthdate_date2,
        TO_CHAR(sub.date_start, 'mm/dd/yyyy')as date_start,
        sub.date_start as date_start4,
        p.gender,
        p.identification_document,
        pro.default_code,
        --subtmpl.recurring_interval,
        ''::text as recurring_interval,
        '009'::varchar as sponsor_name,
        seq.sponsor_nit,
        seq.sponsor_payment_url,
        '79'::varchar as country,
        'CO'::varchar as country2,
        p.email,
        (case when p.mobile LIKE '%)%' then split_part(p.mobile,')',2) else p.mobile end) as mobile,        
        (case when p.phone LIKE '%)%' then split_part(p.phone,')',2) else p.phone end) as phone,
        p.address_beneficiary as street,
        p.street2,
        (case when state.name='Bogotá, D.C.' then 'Bogotá D.C.' else state.name end)as state_id,
        (case when city.name='BOGOTÁ, D.C.' then 'BOGOTÁ D.C.' else city.name end)as city_name,  
        rcz.name as partner_zip_code,
        p.ocupation,
        p.relationship,
        p.clerk_code as clerk_code,
        ''::text as email2,
        ''::text as email_country,
        ''::text as commentaries,
        ''::text as reference_initial,
        ''::text as aniversary,
        TO_CHAR(sub.recurring_next_date, 'mm/dd/yyyy')as first_due,
        ''::text as second_identification,
        rpdt.name as second_type_identification,
        ''::text as insegurability_test,
        ''::text as subsidiary,
        ''::text as lifevolume,
        ''::text as addvolume,
        ''::text as email_state,
        ''::text as email_city,
        ''::text as zip_code,
        ''::text as salary_mode,
        ''::text as salary,
        ''::text as localization,
        --''::text as palig,
        (case when subtmpl.is_fixed_policy='t' then TO_CHAR(sub.date_start, 'mm/dd/yyyy') else TO_CHAR(sub.date_start - CAST('1 days' AS INTERVAL), 'mm/dd/yyyy') end)as change_date,
        '' as date_start2,
        'A'::text as change_type,
        ''::text as date_end
        
        
        from sale_subscription sub
        left join res_partner p on p.subscription_id = sub.id
        left join res_partner_document_type rpdt on rpdt.id = p.document_type_id
        left join res_city_zip rcz on rcz.id = p.beneficiary_zip_id
        left join res_city city on rcz.city_id = city.id
        left join res_city city2 on p.city = city2.id::varchar
        left join res_country_state state on p.beneficiary_state_id = state.id
        left join sale_subscription_line line on line.analytic_account_id = sub.id
        left join product_product pro on pro.id = line.product_id
        left join product_template tmpl on tmpl.id = pro.product_tmpl_id
        left join product_category cat on cat.id = tmpl.categ_id
        left join ir_sequence seq on seq.id = cat.sequence_id
        left join sale_subscription_template subtmpl on subtmpl.id = sub.template_id
        
        where 1=1 and p.beneficiary='t' and sub.stage_id=2
        order by sub.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,