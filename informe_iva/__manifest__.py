# -*- coding: utf-8 -*-
{
    'name': "Informe de IVA",

    'summary': """
        Modulo de Odoo para mostrar un informe dinamico del IVA.""",

    'description': """
        Modulo de Odoo para mostrar un informe dinamico del IVA
    """,

    'author': "Definetec",
    'website': "http://www.definetec.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['syo_hechauka', 'account_reports'],

    # always loaded
    'data': [
        'views/reporte_iva.xml'
    ]
}
