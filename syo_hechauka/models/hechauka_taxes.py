# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfiTaxesInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    iva_10_compra = fields.Many2one('account.tax', string='Iva 10% Crédito Fiscal')
    iva_5_compra = fields.Many2one('account.tax', string='Iva 5% Crédito Fiscal')
    exento_compra = fields.Many2one('account.tax', string='Exento Crédito Fiscal')

    iva_10_venta = fields.Many2one('account.tax', string='Iva 10% Débito Fiscal')
    iva_5_venta = fields.Many2one('account.tax', string='Iva 5% Débito Fiscal')
    exento_venta = fields.Many2one('account.tax', string='Exento Débito Fiscal')

    def get_values(self):
        res = super(ResConfiTaxesInherit, self).get_values()
        config_param_obj = self.env['ir.config_parameter']
        res.update(
            iva_10_compra=int(
                config_param_obj.sudo().get_param('iva_10_compra')) if config_param_obj.sudo().get_param(
                'iva_10_compra') else False,
            iva_5_compra=int(
                config_param_obj.sudo().get_param('iva_5_compra')) if config_param_obj.sudo().get_param(
                'iva_5_compra') else False,
            exento_compra=int(
                config_param_obj.sudo().get_param('exento_compra')) if config_param_obj.sudo().get_param(
                'exento_compra') else False,
            exento_venta=int(
                config_param_obj.sudo().get_param('exento_venta')) if config_param_obj.sudo().get_param(
                'exento_venta') else False,
            iva_10_venta=int(
                config_param_obj.sudo().get_param('iva_10_venta')) if config_param_obj.sudo().get_param(
                'iva_10_venta') else False,
            iva_5_venta=int(
                config_param_obj.sudo().get_param('iva_5_venta')) if config_param_obj.sudo().get_param(
                'iva_5_venta') else False
        )
        return res

    def set_values(self):
        res = super(ResConfiTaxesInherit, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('iva_10_compra',
                                                         self.iva_10_compra and self.iva_10_compra.id or False)
        self.env['ir.config_parameter'].sudo().set_param('iva_5_compra',
                                                         self.iva_5_compra and self.iva_5_compra.id or False)
        self.env['ir.config_parameter'].sudo().set_param('exento_compra',
                                                         self.exento_compra and self.exento_compra.id or False)
        self.env['ir.config_parameter'].sudo().set_param('exento_venta',
                                                         self.exento_venta and self.exento_venta.id or False)
        self.env['ir.config_parameter'].sudo().set_param('iva_10_venta',
                                                         self.iva_10_venta and self.iva_10_venta.id or False)
        self.env['ir.config_parameter'].sudo().set_param('iva_5_venta',
                                                         self.iva_5_venta and self.iva_5_venta.id or False)
        return res
