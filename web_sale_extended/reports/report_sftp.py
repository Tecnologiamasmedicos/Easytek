# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, tools, api,_
from datetime import datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class SftpReportLine(models.Model):
    _name = 'report.sftp'
    _auto = False
    _description = 'This is the lines in the sftp report'
    
    #name = fields.Char('Subscription ID',readonly=True)
    policy_number = fields.Char('Número de Poliza',readonly=True)
    certificate_number = fields.Char('Número de Certificado',readonly=True)
    firstname = fields.Char('Primer Nombre',readonly=True)
    othernames = fields.Char('Segundo Nombre',readonly=True)
    lastname = fields.Char('Primer Apellido',readonly=True)
    lastname2 = fields.Char('Segundo Apellido',readonly=True)
    birthdate_date = fields.Date('Fecha de Nacimiento',readonly=True)
    date_start = fields.Date('Fecha de Inicio',readonly=True)
    gender = fields.Char('Sexo',readonly=True)
    identification_document = fields.Char('Número de Identificación',readonly=True)
    default_code = fields.Char('Código Producto',readonly=True)
    recurring_interval = fields.Char('Subscripción',readonly=True)
    sponsor_name = fields.Char('Tomador',readonly=True)
    sponsor_nit = fields.Char('Nit del Tomador',readonly=True)
    sponsor_payment_url = fields.Char('Pasarela de Pagos',readonly=True)
    country = fields.Char('País',readonly=True)
    email = fields.Char('Email',readonly=True)
    phone = fields.Char('Teléfono Fijo',readonly=True)
    mobile = fields.Char('Teléfono',readonly=True)
    street = fields.Char('Dirección',readonly=True)
    state_id = fields.Char('Departamento',readonly=True)
    zip_id = fields.Char('Ciudad',readonly=True)
    ocupation = fields.Char('Ocupación',readonly=True)
    
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_sftp')
        query = """
        CREATE or REPLACE VIEW report_sftp AS(
        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sub.policy_number,
        seq.code as certificate_number,
        p.firstname,
        p.othernames,
        p.lastname,
        p.lastname2,
        p.birthdate_date,
        sub.date_start,
        p.gender,
        p.identification_document,
        pro.default_code,
        subtmpl.recurring_interval,
        seq.sponsor_name,
        seq.sponsor_nit,
        seq.sponsor_payment_url,
        'COLOMBIA'::text as country,
        p.email,
        p.phone,
        p.mobile,
        p.street,
        p.state_id,
        p.zip_id,
        p.ocupation
        
        
        from sale_subscription sub
        left join res_partner p on p.subscription_id = sub.id
        left join sale_subscription_line line on line.analytic_account_id = sub.id
        left join product_product pro on pro.id = line.product_id
        left join product_template tmpl on tmpl.id = pro.product_tmpl_id
        left join product_category cat on cat.id = tmpl.categ_id
        left join ir_sequence seq on seq.id = cat.sequence_id
        left join sale_subscription_template subtmpl on subtmpl.id = sub.template_id
        
        where 1=1
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,