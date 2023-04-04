# -*- coding: utf-8 -*-
{
    'name': "web_sale_extended",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website_sale', 'portal', 'product', 'sale', 'sale_subscription', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/web_sale_shop_address.xml',
        'views/payulatam_payment_process.xml',
        'views/product_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/mail_template_view.xml',
        'views/account.xml',
        'views/beneficiary.xml',
        'views/beneficiary_detail.xml',
        'views/sale_order_view.xml',
        'views/sale_subscription_view.xml',
        'views/ir_sequence_view.xml',
        'views/assistand_purchase_view.xml',
        'views/assistand_purchase_confirmation_view.xml',
        'views/sale_subscription_template_view.xml',
        'views/sale_subscription_close_reason_view.xml',
        'views/payment_recurring.xml',
        'views/response_transaction.xml',
        'views/sale_cancellation_view.xml',
        'views/sale_settlement_view.xml',
        'views/sale_funds_view.xml',
        'views/payu_payment_methods_view.xml',
        'views/bancolombia_reports_view.xml',
        'views/beneficiaries_bancolombia.xml',
        'views/web_sale_shop_address_bancolombia.xml',
        'views/bancolombia_update_account_view.xml',
        #'reports/sale_order_report.xml',
        #'reports/res_partner_report.xml',
        'data/mail_template_cancellation_plan.xml',
        'data/sftp_report_bot.xml',
        'data/payment_assisted_purchase_mail_template.xml',
        'data/confirm_order_bot.xml',
        'data/recovery_main_insured.xml',
        'data/start_subscriptions_bot.xml',
        'data/shop_address.xml',
        'data/tus_datos_bot.xml',
        'data/payu_latam_bot.xml',
        'data/collection_file_bot.xml',
        'data/beneficiary_confirm_template.xml',
        'views/res_users_view.xml',
        'data/mail_template_recurring_payment_credit_card.xml',
        'data/mail_template_recurring_payment_pse_cash.xml',
        'data/assign_email_beneficiaries_bot.xml',
        'data/complete_payment_information_bot.xml',
        'data/payu_latam_creditcard_payment_bot.xml',
        'data/payu_latam_account_move_bot.xml',
        'data/billing_cycle_api_hubspot_bot.xml',
        'data/mail_template_welcome_falabella.xml',
        'data/mail_template_welcome_bancolombia.xml',
        'data/mail_template_update_bancolombia_account.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
