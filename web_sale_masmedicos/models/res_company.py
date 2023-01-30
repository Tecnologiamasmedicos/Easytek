from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'res.company'

    contact_center_id = fields.Many2one('res.partner', string='Coordinador Contact Center')
    sftp_server_env_bancolombia = fields.Selection(
        [("test", "QA - Test"), ("prod", "Producción")]
    )
    sftp_hostname_bancolombia = fields.Char(string="Hostname SFTP", groups='base.group_user')
    sftp_port_bancolombia = fields.Char(string="Puerto Servidor", groups='base.group_user')
    sftp_user_bancolombia = fields.Char(string="Usuario", groups='base.group_user')
    sftp_password_bancolombia = fields.Char(string="Contraseña", groups='base.group_user')
    sftp_path_output_bancolombia = fields.Char(string="Directorio archivo de salida", groups='base.group_user')

    sftp_hostname_QA_bancolombia = fields.Char(string="Hostname SFTP QA", groups='base.group_user')
    sftp_port_QA_bancolombia = fields.Char(string="Puerto Servidor QA", groups='base.group_user')
    sftp_user_QA_bancolombia = fields.Char(string="Usuario QA", groups='base.group_user')
    sftp_password_QA_bancolombia = fields.Char(string="Contraseña QA", groups='base.group_user')
    sftp_path_output_QA_bancolombia = fields.Char(string="Directorio archivo de salida QA", groups='base.group_user')