# -*- coding: utf-8 -*-
import logging, time, csv
from odoo import fields, models, tools, api,_
from datetime import date, timedelta, datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class ReportSubscriptionSettlement(models.Model):
    _name = 'report.subscription.settlement'
    _auto = False
    _description = 'Subscription Settlement Report'
    
    policy_number = fields.Char('Número de Póliza', readonly=True)
    certificate_number = fields.Char('Número de Certificado', readonly=True)
    buyer_name = fields.Char('Comprador', readonly=True)
    ap_name = fields.Char('Asegurado Principal', readonly=True)
    sponsor_id = fields.Many2one('res.partner', string="Sponsor", store=True)
    subscription_date_start = fields.Date('Fecha de Inicio', readonly=True)
    subscription_date_end = fields.Date('Fecha Final', readonly=True)
    product_code = fields.Char(string='Código producto', readonly=True)
    product_name = fields.Char(string='Nombre producto', readonly=True)
    value = fields.Float('Valor', readonly=True)
    payment_method_type = fields.Selection([
        ("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),
        ("Product Without Price", "Beneficio"),
    ], string="Metodo de pago")
    payulatam_datetime = fields.Datetime('Fecha y hora de transaccion', readonly=True)
    payulatam_order_id = fields.Char('Order ID PayU', readonly=True)
    payulatam_transaction_id = fields.Char('Transacción ID', readonly=True)
    action_date_billing_cycle = fields.Date(string='Fecha accion ciclo de cobro')
    hubspot_payment_action = fields.Selection([
        ("5_days_before", "5 dias antes"),
        ("1_day_before", "1 dia antes"),
        ("1_days_after", "1 dia despues"),
        ("10_days_after", "10 dias despues"),
        ("20_days_after", "20 dias despues"),
        ("25_days_after", "PC 25 dias despues"),
        ("36_days_after", "C 36 dias despues"),
    ], string="Accion de Cobro")
    invoice_id = fields.Many2one('account.move', string='Liquidacion', readonly=True)
    invoice_date = fields.Date('Fecha Liquidación',readonly=True)
    payulatam_state = fields.Selection([
        ("APPROVED", "APROBADO"), 
        ("PENDING", "PENDIENTE"), 
        ("EXPIRED", "EXPIRADO"),
        ("DECLINED", "DECLINADO"),
        ("without_payment", "SIN COBRO"),
        ("no_payment", "NO PAGO"),
    ], string="Estado PayU")
    subscription_id = fields.Many2one('sale.subscription', string='Suscripcion', readonly=True)
    subscription_code = fields.Char('Suscripcion', readonly=True)
    number_of_plan_installments = fields.Integer('Cuotas plan', readonly=True)
    subscription_duration = fields.Integer('Duración de Suscripción', readonly=True)
    recurring_rule_type = fields.Selection(
        [("daily", "Dias"), 
        ("weekly", "Semanas"), 
        ("monthly", "Meses"),
        ("yearly", "Años"),],
        string="Recurencia"
    )
    subscription_state = fields.Char('Estado Suscripcion', readonly=True)
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
    send_payment = fields.Boolean('Cobro realizado', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_subscription_settlement')
        query = """
        CREATE or REPLACE VIEW report_subscription_settlement AS(
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sub.number as policy_number,
        sub.policy_number as certificate_number,
        p.name as buyer_name,
        pap.name as ap_name,
        inv.sponsor_id as sponsor_id,
        sub.date_start as subscription_date_start,
        sub.date as subscription_date_end,
        pro.default_code as product_code,
        pro.name as product_name,
        inv.amount_total as value,
        inv.payment_method_type as payment_method_type,
        inv.payulatam_datetime as payulatam_datetime,
        inv.payulatam_order_id as payulatam_order_id,
        inv.payulatam_transaction_id as payulatam_transaction_id,
        inv.action_date_billing_cycle as action_date_billing_cycle,
        inv.hubspot_payment_action as hubspot_payment_action,
        inv.id as invoice_id,
        inv.invoice_date as invoice_date,
        inv.payulatam_state as payulatam_state,
        sub.id as subscription_id,
        sub.code as subscription_code,
        substage.name as subscription_state,
        subtmpl.recurring_rule_count as number_of_plan_installments,
        subtmpl.recurring_interval as subscription_duration,
        subtmpl.recurring_rule_type as recurring_rule_type,  
        sorder.id as sale_order_id,
        sorder.state as sale_order_state,
        inv.send_payment as send_payment

        from account_move inv
        left join sale_subscription sub on sub.code = inv.invoice_origin
        left join sale_subscription_stage substage on substage.id = sub.stage_id
        left join sale_subscription_template subtmpl on subtmpl.id = sub.template_id
        left join sale_order sorder on sorder.subscription_id = sub.id
        left join res_partner p on p.id = inv.partner_id
        left join res_partner pap on pap.id = sorder.beneficiary0_id
        left join sale_subscription_line line on line.analytic_account_id = sub.id
        left join product_product pro on pro.id = line.product_id
        
        where 1=1 and inv.state='finalized'	and inv.invoice_origin is not null
        order by inv.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,