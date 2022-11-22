# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from .number_to_letter import to_word

TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'out_refund': 'out_invoice',        # Customer Credit Note
    'in_refund': 'in_invoice',          # Vendor Credit Note
}


class Factura(models.Model):
    _inherit = "account.move"

    numeracion = fields.Char("Numeración", size=15)
    timbrado = fields.Char("Timbrado", size=20)
    amount_text = fields.Char(compute="_compute_amount_text")
    tipo_compra = fields.Selection(selection=[
        ('1', 'Factura'),
        ('4', 'Despacho'),
        ('7', 'Pasaje Aéreo'),
        ('8', 'Factura del Exterior'),
        ('11', 'Retención Absorbida'),
        ('13', 'Pasaje Aéreo Electrónico'),
    ], string='Tipo de Factura', default='1')
    tipo_venta = fields.Selection(selection=[
        ('1', 'Factura'),
        ('6', 'Boleta de Venta'),
        ('7', 'Pasaje Aéreo'),
        ('12', 'Factura de Exportación'),
        ('13', 'Pasaje Aéreo Electrónico'),
    ], string='Tipo de Factura', default='1')
    tipo_cliente = fields.Selection(selection=[
        ('1', 'Clientes Nacionales'),
        ('2', 'Clientes de Exportación'),
        ('3', 'Ventas a Agentes Diplomáticos'),
        ('4', 'Clientes del Exterior')
    ], string="Tipo de Cliente", default='1')
    exportador = fields.Boolean(store=False)


    @api.onchange("exportador")
    def _compute_exportador(self):
        for factura in self:
            factura.exportador = self.env.company.exportador

    @api.depends('amount_total')
    def _compute_amount_text(self):
        try:
            for move in self:
                move.amount_text = ""
                if move.amount_total:
                    if move.amount_total > 0:
                        move.amount_text = to_word(float(move.amount_total), move.currency_id.name)
        except Exception as e:
            print(e)
            pass

    @api.onchange('tipo_venta')
    def onchange_tipo_venta(self):
        if self.tipo_venta == '12':
            self.tipo_cliente = '2'
        elif self.tipo_cliente == '2':
            self.tipo_cliente = '1'

    @api.onchange('x_studio_timbrado')
    def onchange_x_studio_timbrado(self):
        if self.x_studio_timbrado:
            self.timbrado = self.x_studio_timbrado.x_name

    @api.onchange('x_studio_talonario_nota_credito')
    def onchange_x_studio_talonario_nota_credito(self):
        if self.x_studio_talonario_nota_credito:
            self.timbrado = self.x_studio_talonario_nota_credito.x_studio_timbrado.x_name

    @api.onchange('timbrado_proveedor')
    def onchange_timbrado_proveedor(self):
        if self.timbrado_proveedor:
            self.timbrado = self.timbrado_proveedor

    def action_post(self):
        resp = super(Factura, self).action_post()
        if self.move_type in ('out_invoice', 'out_refund'):
            try:
                if self.x_studio_field_QV8yr and self.move_type == 'out_invoice':
                    ini = int(self.x_studio_field_QV8yr.x_studio_numero_inicial)
                    fin = int(self.x_studio_field_QV8yr.x_studio_numero_final)
                    numero = int(self.x_studio_numero_de_factura)
                elif self.x_studio_talonario_nota_credito and self.move_type == 'out_refund':
                    ini = int(self.x_studio_talonario_nota_credito.x_studio_numero_inicial)
                    fin = int(self.x_studio_talonario_nota_credito.x_studio_numero_final)
                    numero = int(self.x_studio_numero_de_factura)
            except:
                raise UserError('Introduzca solo numeros en el campo Número de Comprobante.')
            else:
                talonario = False
                if self.x_studio_field_QV8yr and self.move_type == 'out_invoice':
                    talonario = self.x_studio_field_QV8yr
                elif self.x_studio_talonario_nota_credito and self.move_type == 'out_refund':
                    talonario = self.x_studio_talonario_nota_credito

                if talonario:
                    if numero:
                        if ini <= numero <= fin:
                            facturas = self.env['account.move'].search(
                                [('x_studio_field_QV8yr.id', '=', talonario.id), ('x_studio_numero_de_factura', '=', numero),
                                 ('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('id', '!=', self.id)])
                            notas_credito = self.env['account.move'].search(
                                [('x_studio_talonario_nota_credito.id', '=', talonario.id), ('x_studio_numero_de_factura', '=', numero),
                                 ('state', '=', 'posted'), ('move_type', '=', 'out_refund'), ('id', '!=', self.id)])
                            if self.x_studio_field_QV8yr and self.move_type == 'out_invoice' and not facturas:
                                self.timbrado = self.x_studio_field_QV8yr.x_studio_timbrado.x_name
                                self.numeracion = str(self.x_studio_field_QV8yr.x_studio_codigo_de_establecimiento) + "-" + str(
                                    self.x_studio_field_QV8yr.x_studio_punto_de_expedicion) + "-" + str(numero)
                            elif self.x_studio_talonario_nota_credito and self.move_type == 'out_refund' and not notas_credito:
                                self.timbrado = self.x_studio_talonario_nota_credito.x_studio_timbrado.x_name
                                self.numeracion = str(self.x_studio_talonario_nota_credito.x_studio_codigo_de_establecimiento) + "-" + str(
                                    self.x_studio_talonario_nota_credito.x_studio_punto_de_expedicion) + "-" + str(numero)
                            else:
                                raise UserError(
                                    'El numero de documento ya se encuentra en uso, ingrese uno nuevo.\nEl numero siguiente del talonario es: ' + talonario.x_studio_numero_actual)

                        else:
                            raise UserError("El número del comprobante esta fuera de rango.")
                    else:
                        raise UserError('Ingrese el número de comprobante.')
                else:
                    raise UserError('Seleccione el talonario del comprobante.')
        elif self.move_type in ('in_invoice', 'in_refund'):
            if self.timbrado_proveedor:
                if self.x_studio_numero_de_factura:
                    if self.tipo_compra in ['1', '2', '3', '5']:
                        if len(self.timbrado_proveedor) > 7:
                            if self.timbrado_proveedor.isdigit():
                                self.timbrado = self.timbrado_proveedor
                            else:
                                raise UserError('Ingrese solo números en el campo timbrado.')
                        else:
                            raise UserError('El timbrado debe ser de al menos 8 digitos.')
                        if len(self.x_studio_numero_de_factura) < 16:
                            split_fact = self.x_studio_numero_de_factura.split('-')
                            if len(split_fact) == 3 and len(split_fact[0]) == 3 and len(split_fact[1]) == 3 and len(
                                    split_fact[2]) > 0:
                                try:
                                    int(split_fact[0])
                                    int(split_fact[1])
                                    int(split_fact[2])
                                except:
                                    raise UserError('Ingrese solo números entre los guiones. Ej.: 001-001-0000001')
                                else:
                                    self.numeracion = self.x_studio_numero_de_factura
                            else:
                                raise UserError(
                                    'Ingrese el número de comprobante en el formato XXX-XXX-XXXXXXX. Ej.: 001-001-0000001')
                        else:
                            raise UserError('El numero de factura solo debe tener hasta 15 caracteres.')
                    else:
                        self.timbrado = self.timbrado_proveedor
                        self.numeracion = self.x_studio_numero_de_factura
                else:
                    raise UserError('Ingrese el numero de factura.')
            elif self.tipo_compra in ['1', '2', '3', '5']:
                raise UserError('Ingrese el numero de timbrado.')
            else:
                if self.x_studio_numero_de_factura:
                    self.numeracion = self.x_studio_numero_de_factura
                else:
                    raise UserError('Ingrese el numero de factura.')

        return resp
