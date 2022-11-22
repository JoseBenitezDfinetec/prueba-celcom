# -*- coding: utf-8 -*-
{
    'name': "Celcom",

    'summary': """
        Modulo de Odoo para la empresa Celcom S.A. para agregar cambios
        solicitados.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Definetec",
    'website': "http://www.definetec.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale_stock', 'web', 'sale', 'stock'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml'
    ]
}
