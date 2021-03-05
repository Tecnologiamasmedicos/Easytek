# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import uuid

from hashlib import md5
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare


_logger = logging.getLogger(__name__)


class PayULatamApi(models.TransientModel):
    _name = "api.payulatam"
    _description = "Api PayU Latam"
    
    def request_payulatam_api(self, endpoint: str, query: dict) -> dict:
        payulatam_merchant_id = self.env.user.company_id.payulatam_merchant_id
        payulatam_account_id = self.env.user.company_id.payulatam_account_id
        payulatam_api_key = self.env.user.company_id.payulatam_api_key
        payulatam_api_login = self.env.user.company_id.payulatam_api_login
        api_post = ['PING']
        #api_get = ['retry', 'results', 'report_json', 'plans', 'querys']
        
        if endpoint in api_post:
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            url = f'{hostname}{endpoint}'
            response = requests.post(url, json=query, auth=HTTPBasicAuth(username, passwrd), headers=headers)
            
            
            
        elif endpoint in api_get:
            headers = {'accept': 'application/json'}
            if query.get('jobid'):
                endpoint = f'{endpoint}/{query["jobid"]}'
                url = f'{hostname}{endpoint}'
                response = requests.get(url, auth=HTTPBasicAuth(username, passwrd), headers=headers)
            elif query.get('id'):
                endpoint = f'{endpoint}/{query["id"]}'
                url = f'{hostname}{endpoint}'
                response = requests.get(url, auth=HTTPBasicAuth(username, passwrd), headers=headers)
            else:
                _logger.error(f"****** ERROR: invalid request url: \n{url}\n{query}. ******")
        else:
            raise 'Error: Bad endpoint'
        
        


    def payulatam_form_generate_values_api(self, values):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        tx = self.env['payment.transaction'].search([('reference', '=', values.get('reference'))])
        # payulatam will not allow any payment twise even if payment was failed last time.
        # so, replace reference code if payment is not done or pending.
        if tx.state not in ['done', 'pending']:
            tx.reference = str(uuid.uuid4())
        payulatam_values = dict(
            values,
            merchantId=self.payulatam_merchant_id,
            accountId=self.payulatam_account_id,
            description=values.get('reference'),
            referenceCode=tx.reference,
            amount=values['amount'],
            tax='0',  # This is the transaction VAT. If VAT zero is sent the system, 19% will be applied automatically. It can contain two decimals. Eg 19000.00. In the where you do not charge VAT, it should should be set as 0.
            taxReturnBase='0',
            currency=values['currency'].name,
            buyerEmail=values['partner_email'],
            responseUrl=urls.url_join(base_url, '/payment/payulatam-gateway-api/response'),
        )
        payulatam_values['signature'] = self._payulatam_generate_sign("in", payulatam_values)
        return payulatam_values

    def payulatam_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_payulatam_urls(environment)


