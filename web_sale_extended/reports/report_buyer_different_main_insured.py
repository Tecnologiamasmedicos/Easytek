# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, tools, api,_

_logger = logging.getLogger(__name__)
    
class CollectionsReportLine(models.Model):
    _name = 'report.buyer.different.main_insured'
    _auto = False
    _description = 'Este reporte muestra informacion en donde el asegurado principal es diferente del comprador'    
    
    buyer_name = fields.Char('Nombre del comprador', readonly=True)
    buyer_phone = fields.Char('Telefono del comprador', readonly=True)
    buyer_mobile = fields.Char('Celular del comprador', readonly=True)
    buyer_email = fields.Char('Correo del comprador', readonly=True)    
    ap_name = fields.Char('Nombre del asegurado principal', readonly=True)
    ap_phone = fields.Char('Telefono del asegurado principal', readonly=True)
    ap_mobile = fields.Char('Celular del asegurado principal', readonly=True)
    ap_email = fields.Char('Correo del asegurado principal', readonly=True)
     
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_buyer_different_main_insured')
        query = """
        CREATE or REPLACE VIEW report_buyer_different_main_insured AS(        
        select 
        row_number() OVER (ORDER BY sub.id) as id,
        pbuyer.name as buyer_name,        
        pbuyer.phone as buyer_phone, 
        pbuyer.mobile as buyer_mobile,       
        pbuyer.email as buyer_email,
        pap.name as ap_name,
        pap.phone as ap_phone,
        pap.mobile as ap_mobile,
        pap.email as ap_email
                
        from sale_subscription sub
        left join sale_order sorder on sorder.subscription_id = sub.id       
        left join res_partner pbuyer on pbuyer.id = sorder.partner_id         
        left join res_partner pap on pap.id = sorder.beneficiary0_id
        
        
        where pbuyer.buyer='t' and (pbuyer.main_insured='f' or pbuyer.main_insured is null)
        order by sub.id desc
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,
#         reporte entre dos fechas
#         where date_start BETWEEN '2021-05-20' AND '2021-05-26'
    
    