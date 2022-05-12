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

    
class CollectionsReportLineRecurring(models.Model):
    _name = 'report.collections.recurring'
    
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
    total_installments = fields.Char('Pagadas a la fecha', readonly=True)    
    number_of_installments_arrears = fields.Char('Cuotas en mora', readonly=True)
    policyholder = fields.Char('Tomador de Póliza', readonly=True)    
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', readonly=True)
    product_code = fields.Char('Codigo del producto', readonly=True)
    product_name = fields.Char('Nombre del producto', readonly=True)
    payulatam_order_id = fields.Char('Orden ID', readonly=True)
    payulatam_transaction_id = fields.Char('Transacción ID', readonly=True)
    birthday_date = fields.Date('Fecha de nacimiento', readonly=True)  
    origin_payment = fields.Char('Origin INSERT', readonly=True)
    sub_name = fields.Char('Sub name', readonly=True)
    order_name = fields.Char('Order name', readonly=True)
    