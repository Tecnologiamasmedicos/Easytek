# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    """ Logos que aplican a todas las compras y son usados en el pdf de poliza """
    logo_website_pdf  = fields.Binary(string="Logo Website PDF", readonly=False)
    logo_supervigilado  = fields.Binary(string="Logo Supervigilado", readonly=False)
    firma  = fields.Binary(string="Firma Certificado", readonly=False)
    
    """ Datos de conexión al api de tusdatos.co """
    mail_tusdatos = fields.Char("Cuenta - E-mail")
    password_tusdatos = fields.Char("Password")
    hostname_tusdatos = fields.Char("Hostname")
    
    """ Datos de conexión al api de PayU Latam """
    checkout_landpage_redirect = fields.Char(string="Landpage Productos", groups='base.group_user')
    payulatam_api_env = fields.Selection(
        [("test", "Sandbox - Test"), ("prod", "Producción")]
    )
    payulatam_cash_expiration = fields.Integer(string="Horas expiración pago efectivo", 
        help="Horas de Expiración para el método de pago de efectivo y durante los cuales es valido el recibo de pago",
        groups='base.group_user')
    payulatam_api_hostname = fields.Char(string="PayU Latam Hostname", groups='base.group_user')
    payulatam_api_report_hostname = fields.Char(string="PayU Latam Report Hostname", groups='base.group_user')
    payulatam_merchant_id = fields.Char(string="PayU Latam Merchant ID", groups='base.group_user')
    payulatam_account_id = fields.Char(string="PayU Latam Account ID", groups='base.group_user')
    payulatam_api_key = fields.Char(string="PayU Latam API Key", groups='base.group_user')
    payulatam_api_login = fields.Char(string="PayU Latam API Login", groups='base.group_user')
    payulatam_api_ref_seq_id = fields.Many2one('ir.sequence','Referencia API')
    payulatam_api_response_url = fields.Char(string="PayU Latam Response URL", groups='base.group_user')
    
    payulatam_api_sandbox_hostname = fields.Char(string="PayU Latam Hostname", groups='base.group_user')
    payulatam_api_sandbox_report_hostname = fields.Char(string="PayU Latam Report Hostname", groups='base.group_user')
    payulatam_merchant_sandbox_id = fields.Char(string="PayU Latam Merchant ID", groups='base.group_user')
    payulatam_account_sandbox_id = fields.Char(string="PayU Latam Account ID", groups='base.group_user')
    payulatam_api_sandbox_key = fields.Char(string="PayU Latam API Key", groups='base.group_user')
    payulatam_api_sandbox_login = fields.Char(string="PayU Latam API Login", groups='base.group_user')
    payulatam_api_ref_seq_sandbox_id = fields.Many2one('ir.sequence','Referencia API')
    payulatam_api_response_sandbox_url = fields.Char(string="PayU Latam Response URL", groups='base.group_user')
    
    """Datos de conexión HubSpot"""
    hubspot_api_env = fields.Selection(
        [("test", "QA - Test"), ("prod", "Producción")]
    )
    hubspot_api_key = fields.Char(string="Api Key HubSpot", groups='base.group_user')
    hubspot_api_key_QA = fields.Char(string="Api Key HubSpot QA", groups='base.group_user')
    
    """Datos de conexión servidor SFTP"""
    sftp_server_env = fields.Selection(
        [("test", "QA - Test"), ("prod", "Producción")]
    )
    sftp_hostname = fields.Char(string="Hostname SFTP", groups='base.group_user')
    sftp_port = fields.Char(string="Puerto Servidor", groups='base.group_user')
    sftp_user = fields.Char(string="Usuario", groups='base.group_user')
    sftp_password = fields.Char(string="Contraseña", groups='base.group_user')
    sftp_path_ap = fields.Char(string="Directorio Asegurado principal", groups='base.group_user')
    sftp_path_bef = fields.Char(string="Directorio beneficiarios", groups='base.group_user')
    
    sftp_hostname_QA = fields.Char(string="Hostname SFTP QA", groups='base.group_user')
    sftp_port_QA = fields.Char(string="Puerto Servidor QA", groups='base.group_user')
    sftp_user_QA = fields.Char(string="Usuario QA", groups='base.group_user')
    sftp_password_QA = fields.Char(string="Contraseña QA", groups='base.group_user')
    sftp_path_ap_QA = fields.Char(string="Directorio Asegurado principal QA", groups='base.group_user')
    sftp_path_bef_QA = fields.Char(string="Directorio beneficiarios QA", groups='base.group_user')