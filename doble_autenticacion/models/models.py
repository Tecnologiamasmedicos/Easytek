# -*- coding: utf-8 -*-

from odoo import models, fields, api

import datetime
from datetime import timedelta
import random


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    codigo = fields.Integer("Codigo de verficación")
    tiempovencimiento = fields.Datetime("tiempo en que vence el codigo")
    verificado = fields.Boolean("Verificado", default=False)

    def VerificarCodigo(self, codigo, fecha):
        if self.codigo == int(codigo) and fecha <= self.tiempovencimiento:
            self.verificado = True
        else:
            self.verificado = False

    def send_code(self, correo):
        self.codigo = self.GenerarCodigo()
        self.tiempovencimiento = datetime.datetime.now() + timedelta(minutes=3)
        self.partner_id.email = correo
        ctx = {
            'codigo': str(self.codigo).zfill(6),
        }
        template = self.env.ref('doble_autenticacion.email_template_envio_codigo')
        template.sudo().with_context(ctx).send_mail(self.id, force_send=True)
        self.partner_id.email = False

    def GenerarCodigo(self):
        numero = random.randint(0, 999999)
        if len(str(numero)) < 6:
            numero = str(numero).zfill(6)

        return int(numero)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    servidor_de_correo = fields.Many2one('ir.mail_server', 'Servidor de correo')

