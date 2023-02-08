# -*- coding: utf-8 -*-
{
    'name': "Log aceptación política de tratamiento de datos",

    'summary': """
        Registro de datos del usuario al aceptar tratamiento de datos al realizar una suscripción""",

    'description': """
        Registro de datos del usuario al aceptar tratamiento de datos al realizar una suscripción
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
        'security/ir.model.access.csv',
        'security/rule.xml',
        'views/views.xml',
        'views/accion_planificada.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
