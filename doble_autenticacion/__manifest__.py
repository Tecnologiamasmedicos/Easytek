# -*- coding: utf-8 -*-
{
    'name': "Doble autenticación",

    'summary': """
        Enviar código de verificación al correo para verificar y continuar con el pago""",

    'description': """
        Enviar código de verificación al correo para verificar y continuar con el pago
    """,

    'author': "PETI Soluciones Productivas",
    'website': "https://peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web_sale_extended'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/template.xml',
        'data/data_mail_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
