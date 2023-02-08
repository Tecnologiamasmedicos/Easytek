# -*- coding: utf-8 -*-

from odoo import models, fields, api

import datetime
from datetime import timedelta


class LogAceptacion(models.Model):
    _name = 'log.aceptacion.politicas'
    _description = "Guarda los datos de los usuarios cuando ingresan a comprar un producto"

    date = fields.Datetime("Fecha y hora")
    ip = fields.Char("IP")
    identificacion_cliente = fields.Char("Identificación Cliente")
    sponsor_id = fields.Many2one("res.partner", "Sponsor")
    estado = fields.Selection(selection=[('no_efectivo', 'No efectivo'), ('efectivo', 'Efectivo')], default='no_efectivo')
    order_id = fields.Many2one("sale.order", "Relación con la venta")
    campo_vacio = fields.Boolean('Campo vacio', default=False)

    def eliminar_no_validos(self):
        self.env['log.aceptacion.politicas'].search([('date', '<=', datetime.datetime.now() - timedelta(days=30)),
                                                    ('estado', '=', 'no_efectivo')]).unlink()


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        log = self.env['log.aceptacion.politicas'].search([("order_id", '=', self.id)])
        log.write({'estado': 'efectivo'})
        super(SaleOrderExtend, self).action_confirm()
