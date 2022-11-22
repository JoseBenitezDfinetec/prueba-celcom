# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char('RUC', size=15, default='44444401-7')
    ruc = fields.Char('RUC', size=15, default='44444401', compute="_compute_dv", store=True)
    dv = fields.Char('DV', size=1, default='7', compute="_compute_dv", store=True)

    @api.model
    def create(self, vals):
        if 'vat' in vals:
            if vals['vat']:
                ruc = self.validar_vat(vals['vat'])
                vals['ruc'] = ruc[0]
                vals['dv'] = ruc[1]
        return super(Partner, self).create(vals)

    def write(self, vals):
        if 'vat' in vals:
            if vals['vat']:
                ruc = self.validar_vat(vals['vat'])
                vals['ruc'] = ruc[0]
                vals['dv'] = ruc[1]

        return super(Partner, self).write(vals)

    @api.depends('vat')
    def _compute_dv(self):
        for partner in self:
            if partner.vat:
                try:
                    ruc = partner.vat.split('-')
                except:
                    continue
                try:
                    int(ruc[0])
                    int(ruc[1])
                except:
                    continue
                if len(ruc) != 2:
                    continue
                if len(ruc[1]) != 1:
                    continue
                partner.ruc = ruc[0]
                partner.dv = ruc[1]

    def validar_vat(self, vat):
        try:
            ruc = vat.split('-')
        except:
            raise UserError('No se ha introducido el RUC.')
        try:
            int(ruc[0])
            int(ruc[1])
        except:
            raise UserError('Introduzca solo números en formato XXXXXXXX-X, ejemplo: 80011111-8.')
        if len(ruc) != 2:
            raise UserError('Introduzca el RUC en formato XXXXXXXX-X, ejemplo: 80011111-8.')
        if len(ruc[1]) != 1:
            raise UserError('Introduzca un solo numero para el Digito Verificador.')
        return ruc
