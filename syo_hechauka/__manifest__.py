# -*- coding: utf-8 -*-
{
    'name': "Hechauka",

    'summary': """
        Modulo de Odoo 14 que agrega funciones y modelos para generar y manejar reportes de Hechauka""",

    'description': """
        Modulo de Odoo 14 que agrega funciones y modelos para generar y manejar reportes de Hechauka
    """,

    'author': "DfineTec",
    'website': "http://www.dfinetec.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'talonario_py'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/hechauka.xml',
        'views/company.xml',
        'views/hechauka_setting.xml'
    ],
    # only loaded in demonstration mode

    'application': True,
}