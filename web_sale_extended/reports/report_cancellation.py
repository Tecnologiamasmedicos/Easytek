# -*- coding: utf-8 -*-
import logging, time, csv
from odoo import fields, models, tools, api,_
from datetime import date, timedelta, datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class ReportSubscriptionCancellation(models.Model):
    _name = 'report.subscription.cancellation'
    _auto = False
    _description = 'Subscription cancelation Report'

    sale_order = fields.Many2one('sale.order', string='Orden de Venta', readonly=True)
    subscription = fields.Many2one('sale.subscription', string='Suscripcion', readonly=True)
    policy_number = fields.Char('Número de Póliza',readonly=True)
    certificate_number = fields.Char('Número de Certificado',readonly=True)
    subscription_date_start = fields.Date('Fecha de Inicio',readonly=True)
    subscription_date_end = fields.Date('Fecha Final',readonly=True)
    close_reason_id = fields.Char('Razón de cierre', readonly=True)
    ap_name = fields.Char('Comprador',readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_subscription_cancellation')
        query = """
        CREATE or REPLACE VIEW report_subscription_cancellation AS(
        
        select 
        row_number() OVER (ORDER BY sub.id) as id,

        so.id as sale_order,    
        sub.id as subscription, 
        sub.number as policy_number,
        sub.policy_number as certificate_number,
        sub.date_start as subscription_date_start,
        sub.date as subscription_date_end,
        close.name as close_reason_id,
        p.name as ap_name

        from sale_subscription sub
        left join sale_order so on so.subscription_id = sub.id
        left join sale_subscription_close_reason close on close.id = sub.close_reason_id
        left join res_partner p on p.id = sub.partner_id
        
        where 1=1 and so.state = 'done'
        order by sub.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,
        
    