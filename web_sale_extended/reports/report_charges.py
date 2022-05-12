# -*- coding: utf-8 -*-
import logging, time, csv
import paramiko
from odoo import fields, models, tools, api,_
from datetime import date, timedelta, datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class SftpReportLine(models.Model):
    _name = 'report.charges'
    _auto = False

    product_code = fields.Char('Código producto', readonly=True)
    product_name = fields.Char('Nombre producto', readonly=True)
    saleorder_name =  fields.Char('Orden de venta', readonly=True)
    payment_method = fields.Selection([
        ("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),
        ("Product Without Price", "Beneficio"),
        ("payroll_discount", "Descuento de nómina"),
        ("window_payment", "Pago por ventanilla"),
    ], string="Método de Pago")
    buyer_name = fields.Char('Nombre comprador', readonly=True)
    total = fields.Float('Total', readonly=True)
    state = fields.Char('Estado', readonly=True)
    policy_number = fields.Char('Número de Grupo / Póliza', readonly=True)
    certificate_number = fields.Char('Número de Certificado', readonly=True)
    firstname = fields.Char('Primer Nombre', readonly=True)
    othernames = fields.Char('Segundo Nombre', readonly=True)
    lastname = fields.Char('Apellidos', readonly=True)
    identification_document = fields.Char('Número de Seguro Social / Cédula', readonly=True)
    birthdate_date = fields.Date('Fecha de Nacimiento', readonly=True)
    date_of_membership = fields.Date('Fecha afiliacion', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_charges')
        query = """
        CREATE or REPLACE VIEW report_charges AS(
        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        tmpl.default_code as product_code,
        tmpl.name as product_name,
        sorder.name as saleorder_name,
        sorder.payment_method_type as payment_method,
        pbuyer.name as buyer_name, 
        sorder.amount_total as total, 
        sorder.state as state,
        sub.policy_number as certificate_number,
        LPAD(sub.number::text, 5, '0') as policy_number,
        p.firstname,
        p.othernames,
        p.lastname || ' ' || p.lastname2 as lastname,        
        p.identification_document,
        p.birthdate_date,
        sub.date_start as date_of_membership
        
        from sale_subscription sub
        left join res_partner p on p.subscription_id = sub.id
        left join res_partner pbuyer on pbuyer.id = sub.partner_id
        left join res_partner_document_type rpdt on rpdt.id = p.document_type_id
        left join res_city_zip rcz on rcz.id = p.beneficiary_zip_id
        left join res_city city on rcz.city_id = city.id
        left join sale_subscription_line line on line.analytic_account_id = sub.id
        left join product_product pro on pro.id = line.product_id
        left join product_template tmpl on tmpl.id = pro.product_tmpl_id
        left join product_category cat on cat.id = tmpl.categ_id
        left join ir_sequence seq on seq.id = cat.sequence_id
        left join sale_subscription_template subtmpl on subtmpl.id = sub.template_id
        left join sale_order sorder on sorder.subscription_id = sub.id
        
        where 1=1 and p.main_insured='t' and sub.stage_id=2
        order by sub.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,
