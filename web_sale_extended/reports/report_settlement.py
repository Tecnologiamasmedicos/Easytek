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
    
    sale_order = fields.Many2one('sale.order', string='Orden de Venta', readonly=True)
    subscription = fields.Many2one('sale.subscription', string='Suscripcion', readonly=True)
    invoice = fields.Many2one('account.move', string='Liquidacion', readonly=True)    
    policy_number = fields.Char('Número de Póliza',readonly=True)
    certificate_number = fields.Char('Número de Certificado',readonly=True)
    subscription_date_start = fields.Date('Fecha de Inicio',readonly=True)
    subscription_date_end = fields.Date('Fecha Final',readonly=True)
    invoice_date = fields.Date('Fecha Liquidación',readonly=True)
    product_code = fields.Char(string='Código producto', readonly=True)
    value = fields.Float('Valor', readonly=True)
    sponsor_id = fields.Many2one('res.partner', string="Sponsor", store=True)
    payulatam_order_id = fields.Char('Order ID PayU', readonly=True)
    payulatam_state = fields.Selection([
        ("APPROVED", "APROBADO"), 
        ("PENDING", "PENDIENTE"), 
        ("EXPIRED", "EXPIRADO"),
        ("DECLINED", "DECLINADO"),
    ], string="Estado PayU")
    payulatam_datetime = fields.Datetime('Fecha y hora de transaccion', readonly=True)
    ap_name = fields.Char('Comprador',readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_subscription_settlement')
        query = """
        CREATE or REPLACE VIEW report_subscription_settlement AS(
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        sorder.id as sale_order,
        sub.id as subscription,
        inv.id as invoice,
        sub.number as policy_number,
        sub.policy_number as certificate_number,
        sub.date_start as subscription_date_start,
        sub.date as subscription_date_end,
        inv.invoice_date as invoice_date,
        pro.default_code as product_code,
        inv.amount_total as value,
        inv.sponsor_id as sponsor_id,
        inv.payulatam_order_id as payulatam_order_id,
        inv.payulatam_state as payulatam_state,
        inv.payulatam_datetime as payulatam_datetime,
        p.name as ap_name

        from account_move inv
        left join sale_subscription sub on sub.code = inv.invoice_origin
        left join sale_order sorder on sorder.subscription_id = sub.id
        left join res_partner p on p.id = inv.partner_id
        left join account_move_line line on line.move_id = inv.id
        left join product_product pro on pro.id = line.product_id
        
        where 1=1 and inv.state='finalized'
	and inv.invoice_origin is not null
        order by inv.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,
        
    
