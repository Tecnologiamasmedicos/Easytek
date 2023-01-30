# -*- coding: utf-8 -*-
{
    'name': "website_tag_manager",

    'summary': """
        Agregar tag manager al sitio web""",

    'description': """
        Agregar tag manager al sitio web
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website', 'website_sale'],

    # always loaded
    'data': [
        'views/templates.xml',
        'views/res_config_settings_view.xml',
    ],

}
