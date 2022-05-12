# -*- coding: utf-8 -*-
import logging, time, csv
from odoo import fields, models, tools, api,_
from datetime import date, timedelta, datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class ReportSubscription(models.Model):
    _name = 'report.subscription'
    _auto = False
    _description = 'subscription report'
    
    policy_number = fields.Char('Número de Grupo / Póliza',readonly=True)
    certificate_number = fields.Char('Número de Certificado',readonly=True)
    ap_name = fields.Char('Asegurado Principal',readonly=True)
    ap_identification_type = fields.Char('Identificacion Asegurado Principal',readonly=True)
    ap_identification = fields.Char('Identificacion Asegurado Principal',readonly=True)
    plan_name = fields.Char('Nombre Plan',readonly=True)
    subscription_date = fields.Date('Fecha Suscripción',readonly=True)
    sub_name = fields.Char('Nombre Suscripción',readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_subscription')
        query = """
        CREATE or REPLACE VIEW report_subscription AS(
        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sub.policy_number as certificate_number,
        LPAD(sub.number::text, 5, '0') as policy_number,
        p.name as ap_name,
        rpdt.name as ap_identification_type,
        p.identification_document as ap_identification,
        tmpl.name as plan_name,
        sub.date_start as subscription_date,
        sub.code as sub_name
        
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
        
    