# -*- coding: utf-8 -*-
import logging
import datetime
import traceback

from collections import Counter
from dateutil.relativedelta import relativedelta
from uuid import uuid4

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import format_date, float_compare
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class SaleSubscriptionTemplate(models.Model):
    _inherit = "sale.subscription.template"
    
    @api.depends('recurring_interval', 'recurring_rule_count')
    def _compute_subscription_duration(self):
        for rec in self:
            rec.subscription_duration = int(rec.recurring_interval) * int(rec.recurring_rule_count)
    
    subscription_duration = fields.Integer(compute=_compute_subscription_duration, store=True)
    final_date = fields.Date(string='Fecha final', store=True)
    is_fixed_policy = fields.Boolean(string='Es una poliza fija', default=False) 
    cutoff_day = fields.Integer(string='Dia de corte', store=True)

    @api.onchange('is_fixed_policy')
    def _compute_values_fixed(self):
        if self.is_fixed_policy == True:
            self.recurring_rule_boundary = 'limited'
            self.recurring_rule_count = 1
            self.recurring_interval = 12
            self.payment_mode = 'validate_send'