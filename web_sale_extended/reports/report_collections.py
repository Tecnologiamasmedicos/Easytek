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

    
class CollectionsReportLine(models.Model):
    _name = 'report.collections'
    _auto = False
    _description = 'This is the lines in the collections report'
    
    
#     Número de grupo/póliza: Va el número de póliza expedido por PALIG para ese sponsor o producto, según aplique.
#     Certificado: Consecutivo único del certificado. Va entre los rangos que aparecen en el archivo.
#     Primer nombre, segundo nombre, apellidos y número de cédula no creo que haya necesidad de explicarlos (Tampoco los de arriba,        pero bueno).
#     Tipo de transacción: Siempre va a ir R de Recaudo.
#     Código de clase: El atributo Clase del producto.
#     Fecha de cambio: Es la fecha del recaudo. Ten cuidado con el formato de fecha usado por PALIG.
#     Valor recaudo no hay necesidad de explicarlo.
#     Número de cuotas: Es el número de cuotas recaudadas con el pago. Debido a la naturaleza del negocio, el cliente siempre va a        pagar 1 o 2 cuotas en el recaudo, no más.
#     Medio de pago es otro que no tiene necesidad de ser explicado, creo.
#     Número de cuotas plan: es el número de cuotas para pagar su suscripción. Es decir, 12 si es de pago mensual, 4 si es de pago    trimestral, 2 si es de pago semestral y 1 si es de pago anual.
#     Total de cuotas: La suma de todas las cuotas recaudadas hasta el momento. Por ejemplo, 3 se interpreta como que el cliente ha    pagado 3 cuotas.
#     Número de cuotas en mora: Es el número de cuotas que ha dejado de pagar el cliente hasta la fecha. Se reportará 1, cuando el    cliente que deba pagar dos cuotas para no entrar en cancelación, solamente abone una cuota y deje la cuota en mora. 
    
    
    policy_number = fields.Char('Número de Poliza', readonly=True)
    certificate_number = fields.Char('Número de Certificado', readonly=True)
    firstname = fields.Char('Primer Nombre', readonly=True)
    othernames = fields.Char('Segundo Nombre', readonly=True)
    lastname = fields.Char('Apellidos', readonly=True)
    identification_document = fields.Char('Número de Identificación', readonly=True)
    transaction_type = fields.Char('Tipo de transacción', readonly=True)
    clase = fields.Char('Clase', readonly=True)    
    change_date = fields.Date('Fecha de cambio', readonly=True)    
    collected_value = fields.Float('Valor recaudo', readonly=True)    
    number_of_installments = fields.Integer('Cuotas recaudo', readonly=True)    
    payment_method = fields.Selection(
        [("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),
        ("Product Without Price", "Beneficio"),],
        string="Método de Pago"
    )
    number_of_plan_installments = fields.Integer('Cuotas plan', readonly=True)    
    total_installments = fields.Integer('Pagadas a la fecha', readonly=True)    
    number_of_installments_arrears = fields.Char('Cuotas en mora', readonly=True)
    policyholder = fields.Char('Tomador de Póliza', readonly=True)    
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', readonly=True)
    product_code = fields.Char('Codigo del producto', readonly=True)
    product_name = fields.Char('Nombre del producto', readonly=True)
    payulatam_order_id = fields.Char('Orden ID', readonly=True)
    payulatam_transaction_id = fields.Char('Transacción ID', readonly=True)
    birthday_date = fields.Date('Fecha de nacimiento', readonly=True)
    sub_name = fields.Char('Sub name', readonly=True)
    order_name = fields.Char('Order name', readonly=True)
    state_order = fields.Char('Estado de la orden', readonly=True)
    
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_collections')
        query = """
        CREATE or REPLACE VIEW report_collections AS(        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sub.policy_number as certificate_number,
        LPAD(sub.number::text, 5, '0') as policy_number,
        p.firstname,
        p.othernames,
        p.lastname || ' ' || p.lastname2 as lastname,
        p.identification_document,
        p.birthdate_date as birthday_date,
        'R'::text as transaction_type,
        tmpl.product_class as clase,
        sub.date_start as change_date,
        sub.recurring_total as collected_value,        
        1::int as number_of_installments,        
        sorder.payment_method_type as payment_method,
        subtmpl.recurring_rule_count as number_of_plan_installments,
        1::int as total_installments,
        ''::text as number_of_installments_arrears,        
        sub.policyholder as policyholder,        
        sub.sponsor_id as sponsor_id,
        tmpl.default_code as product_code,
        tmpl.name as product_name,
        sorder.payulatam_order_id as payulatam_order_id,
        sorder.payulatam_transaction_id as payulatam_transaction_id,
        sub.code as sub_name,
        sorder.name as order_name,
        sorder.state as state_order
        
        from sale_subscription sub
        left join res_partner p on p.subscription_id = sub.id
        left join res_partner_document_type rpdt on rpdt.id = p.document_type_id
        left join res_city_zip rcz on rcz.id = p.zip_id
        left join res_city city on rcz.city_id = city.id
        left join sale_subscription_line line on line.analytic_account_id = sub.id
        left join product_product pro on pro.id = line.product_id
        left join product_template tmpl on tmpl.id = pro.product_tmpl_id
        left join product_category cat on cat.id = tmpl.categ_id
        left join ir_sequence seq on seq.id = cat.sequence_id
        left join sale_subscription_template subtmpl on subtmpl.id = sub.template_id
        left join sale_order sorder on sorder.subscription_id = sub.id
        
        where p.main_insured='t'
        order by sub.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,
#         reporte entre dos fechas
#         where date_start BETWEEN '2021-05-20' AND '2021-05-26'