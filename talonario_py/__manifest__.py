# -*- coding: utf-8 -*-
{
    'name': "Talonarios del Paraguay",

    'summary': """
        Modulo de Odoo que adapta y agrega funciones y modelos a la contabilidad normal de Odoo para poder instalarse y utilizarse en Paraguay(PY).""",

    'description': """
        contaduria
    """,

    'author': "Dfinetec",
    'website': "http://www.dfinetec.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'base', 'stock', 'fleet', 'sale_management'],

    # always loaded
    'data': [
        'views/invoice.xml',
        'views/partner.xml',
        'views/company.xml',
        'views/account_payment_term_views.xml'
    ],
    # only loaded in demonstration mode

    'application': True,
}
