# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class Company(models.Model):
    _inherit = 'res.company'
    _name = 'res.company'

    razon_social = fields.Char('Razon Social', size=80)
    representante_legal = fields.Char('Representante Legal', size=80)
    ruc_representante = fields.Char('Ruc del Representante Legal', size=15, default='0')
    exportador = fields.Boolean()

    @api.onchange('ruc_representante')
    def onchange_ruc_representante(self):
        ruc = self.ruc_representante.split('-')
        try:
            int(ruc[0])
            int(ruc[1])
        except:
            raise UserError('Introduzca solo numeros en formato XXXXXXXX-X, ejemplo: 80011111-8.')
        if len(ruc) != 2:
            raise UserError('Introduzca el RUC en formato XXXXXXXX-X, ejemplo: 80011111-8.')
        if len(ruc[1]) != 1:
            raise UserError('Introduzca un solo numero para el Digito Verificador.')

    @api.onchange('vat')
    def onchange_ruc_company(self):
        ruc = self.vat.split('-')
        try:
            int(ruc[0])
            int(ruc[1])
        except:
            raise UserError('Introduzca solo numeros en formato XXXXXXXX-X, ejemplo: 80011111-8.')
        if len(ruc) != 2:
            raise UserError('Introduzca el RUC en formato XXXXXXXX-X, ejemplo: 80011111-8.')
        if len(ruc[1]) != 1:
            raise UserError('Introduzca un solo numero para el Digito Verificador.')
