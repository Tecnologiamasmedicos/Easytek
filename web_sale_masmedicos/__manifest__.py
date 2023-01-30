# -*- coding: utf-8 -*-
{
    'name': "web_sale_masmedicos",

    'summary': """
        Extender funcionalidades del modulo web_sale_extended""",

    'description': """
        Extender funcionalidades del modulo web_sale_extended
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web_sale_extended', 'product', 'sale', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_category.xml',
        'views/res_company.xml',
        'wizard/wizard_files_bank.xml',
        'reports/bancolombia_policy_certificate.xml',
        #'reports/bancolombia_policy_certificate1.xml',
        'data/cron_tusdatos.xml',
        'data/cron_sftp_bancolombia.xml',
        'data/data_mail_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
