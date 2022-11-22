# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = "res.partner"

    dv = fields.Char('DV', size=1, default='7', compute="_compute_dv", store=True)

    @api.depends('vat')
    def _compute_dv(self):
        for partner in self:
            if partner.vat:
                try:
                    ruc = partner.vat.split('-')
                except:
                    raise UserError('No se ha introducido el RUC.')
                try:
                    int(ruc[0])
                    int(ruc[1])
                except:
                    # raise UserError('Introduzca solo números en formato XXXXXXXX-X, ejemplo: 80011111-8.')
                    return
                if len(ruc) != 2:
                    # raise UserError('Introduzca el RUC en formato XXXXXXXX-X, ejemplo: 80011111-8.')
                    return
                if len(ruc[1]) != 1:
                    # raise UserError('Introduzca un solo numero para el Digito Verificador.')
                    return
                partner.dv = ruc[1]


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
