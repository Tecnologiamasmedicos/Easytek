from odoo import models, fields, api, _
import base64


class FilesBankUpdate(models.TransientModel):
    _name = 'files.bank.update'
    _description = 'actualizar cuentas con archivo'

    file_import = fields.Binary("Archivo")
    file_name = fields.Char("Nombre archivo")
    orders_update = fields.Text('Datos a actualizar')

    def update_data(self):
        file = base64.b64decode(self.file_import)
        lines = file.decode().split('\n')[:-1]
        self.orders_update = "REFERENCIA | NRO DOCUMENTO | NRO CUENTA"
        for line in lines[1:]:
            nro_documento = line[1:14].lstrip('0')
            nro_cuenta = line[43:60].lstrip('0')
            referencia = line[80:110].strip()
            self.orders_update += "\n %s | %s | %s" % (
            referencia.ljust(10, ' '), nro_documento.ljust(13, ' '), nro_cuenta)
        view_id = self.env.ref('web_sale_masmedicos.view_files_bank_update_form').id
        return {
            'name': _('Actualizar cuentas archivo banco'),
            'res_model': 'files.bank.update',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'views': [[view_id, 'form']],
        }

    def apply(self):
        file = base64.b64decode(self.file_import)
        lines = file.decode().split('\n')[:-1]
        for line in lines[1:]:
            nro_documento = line[1:14].lstrip('0')
            nro_cuenta = line[43:60].lstrip('0')
            referencia = line[80:110].strip()
            order = self.env['sale.order'].search([('name', '=ilike', referencia)])
            if order:
                order.write({'buyer_account_number': nro_cuenta})
