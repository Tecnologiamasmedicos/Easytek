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

    
class ReportSubscriptionFundsLine(models.Model):
    _name = 'report.subscription.funds'
    _auto = False
    _description = 'This is the lines in the funds report'
    
    policy_number = fields.Char('Número de Poliza', readonly=True)
    certificate_number = fields.Char('Número de Certificado', readonly=True)
    buyer_name = fields.Char('Comprador', readonly=True)
    ap_name = fields.Char('Asegurado Principal', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', string='Suscripcion', readonly=True)
    subscription_code = fields.Char('Codigo Suscripcion', readonly=True)
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', readonly=True)
    subscription_date_start = fields.Date('Fecha de Inicio', readonly=True)
    subscription_date_end = fields.Date('Fecha Final', readonly=True)
    payment_method = fields.Selection(
        [("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),
        ("Product Without Price", "Beneficio"),],
        string="Método de Pago"
    )
    product_code = fields.Char('Codigo del producto', readonly=True)
    product_name = fields.Char('Nombre del producto', readonly=True)
    value = fields.Float('Valor', readonly=True)
    subscription_state = fields.Char('Estado Suscripcion', readonly=True)
    cancel_date = fields.Date('Fecha de cancelacion', readonly=True)
    number_of_plan_installments = fields.Integer('Cuotas plan', readonly=True)
    subscription_duration = fields.Integer('Duración de Suscripción', readonly=True)
    recurring_rule_type = fields.Char('Recurrencia', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta', readonly=True)
    sale_order_state = fields.Selection([
        ('draft', 'Presupuesto'),
        ('sent', 'Presupuesto enviado'),
        ('sale', 'Pedido de Venta'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado'),
        ('payu_pending', 'PAYU ESPERANDO APROBACIÓN'),
        ('payu_approved', 'PAYU APROBADO')
    ])
    
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_subscription_funds')
        query = """
        CREATE or REPLACE VIEW report_subscription_funds AS(        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sub.policy_number as certificate_number,
        LPAD(sub.number::text, 5, '0') as policy_number,
        p.name as buyer_name,
        pap.name as ap_name,
        sub.id as subscription_id,
        sub.code as subscription_code,
        sub.sponsor_id as sponsor_id,
        sub.date_start as subscription_date_start,
        sub.date as subscription_date_end,
        sorder.payment_method_type as payment_method,
        tmpl.default_code as product_code,
        tmpl.name as product_name,
        sub.recurring_total as value,
        substage.name as subscription_state,
        sorder.cancel_date as cancel_date,
        subtmpl.recurring_rule_count as number_of_plan_installments,
        subtmpl.recurring_interval as subscription_duration,
        subtmpl.recurring_rule_type as recurring_rule_type, 
        sorder.id as sale_order_id,
        sorder.state as sale_order_state


        from sale_subscription sub
        left join sale_order sorder on sorder.subscription_id = sub.id
        left join res_partner p on p.subscription_id = sub.id
        left join res_partner pap on pap.id = sorder.beneficiary0_id
        left join sale_subscription_stage substage on substage.id = sub.stage_id
        left join sale_subscription_line line on line.analytic_account_id = sub.id
        left join product_product pro on pro.id = line.product_id
        left join product_template tmpl on tmpl.id = pro.product_tmpl_id
        left join sale_subscription_template subtmpl on subtmpl.id = sub.template_id
        
        
        where p.main_insured='t' and tmpl.is_beneficiary='t' and sorder.payment_method_type='Product Without Price' and sub.sponsor_id!=298
        order by sub.id desc
        );
        """
        self.env.cr.execute(query)