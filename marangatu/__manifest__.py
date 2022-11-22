# -*- coding: utf-8 -*-
{
    'name': "Marangatu",

    'summary': """
        Modulo de Odoo 14 que agrega funciones y modelos para generar archivos de compra, venta, ingresos y egresos para Marangatu
    """,

    'description': """
        Modulo de Odoo 14 que agrega funciones y modelos para generar archivos de compra, venta, ingresos y egresos para Marangatu
    """,

    'author': "DefineTec",
    'website': "https://www.definetec.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['talonario_py', 'base', 'account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/marangatu.xml',
        'views/marangatu_setting.xml',
        'views/account_move_views.xml',
        'views/account_payment_view.xml',
        'views/res_partner_views.xml'
    ],
    # only loaded in demonstration mode

    'application': True,
}