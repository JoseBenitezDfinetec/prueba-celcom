from odoo import models, fields, api
from odoo.exceptions import ValidationError

TIPOS_COMPROBANTES = {
        '101': 'Autofactura',
        '102': 'Boleta de Transporte Público de Pasajeros',
        '103': 'Boleta de Venta',
        '104': 'Boleta Resimple',
        '105': 'Boleta de Loterías, Juegos de Azar',
        '106': 'Boleto o Ticket de Transporte Aéreo',
        '107': 'Despacho de Importación',
        '108': 'Entrada a Espectáculos Públicos',
        '109': 'Factura',
        '110': 'Nota de Crédito',
        '111': 'Nota de Débito',
        '112': 'Ticket de Máquina Registradora'
}

TIPOS_IDENTIFICACION = {
    '11': 'RUC',
    '12': 'Cédula de Identidad',
    '13': 'Pasaporte',
    '14': 'Cédula Extranjera',
    '15': 'Sin Nombre',
    '16': 'Diplomático',
    '17': 'Identificación Tributaria'
}


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_default_iva(self):
        return self.env['ir.config_parameter'].sudo().get_param('imputacion_iva')

    def _get_default_ire(self):
        return self.env['ir.config_parameter'].sudo().get_param('imputacion_ire')

    def _get_default_irp(self):
        return self.env['ir.config_parameter'].sudo().get_param('imputacion_irp')

    # Los tipos de comprobantes de ventas que se muestran en las facturas de cliente
    tipo_comprobante_venta = fields.Selection(
        [('102', 'Boleta de Transporte Público de Pasajeros'),
         ('103', 'Boleta de Venta'),
         ('105', 'Boleta de Loterías, Juegos de Azar'),
         ('106', 'Boleto o Ticket de Transporte Aéreo'),
         ('108', 'Entrada a Espectáculos Públicos'),
         ('109', 'Factura'),
         ('112', 'Ticket de Máquina Registradora')],
        string='Tipo de Comprobante de Venta', default='109')

    # Los tipos de comprobantes que se muestran en las facturas rectificativas de cliente
    tipo_comprobante_venta_nota = fields.Selection(
        [('110', 'Nota de Crédito'),
         ('111', 'Nota de Débito')],
        string='Tipo de Comprobante de Venta', default='110')

    # Los tipos de comprobantes que se muestran en la factura de proveedor
    tipo_comprobante_compra = fields.Selection(
        [('101', 'Autofactura'),
         ('102', 'Boleta de Transporte Público de Pasajeros'),
         ('103', 'Boleta de Venta'),
         ('104', 'Boleta Resimple'),
         ('105', 'Boleta de Loterías, Juegos de Azar'),
         ('106', 'Boleto o Ticket de Transporte Aéreo'),
         ('107', 'Despacho de Importación'),
         ('108', 'Entrada a Espectáculos Públicos'),
         ('109', 'Factura'),
         ('112', 'Ticket de Máquina Registradora')], string='Tipo de Comprobante de Compra', default='109')

    # Los tipos de comprobantes que se muestran en las facturas rectificativas de proveedor
    tipo_comprobante_compra_nota = fields.Selection(
        [('110', 'Nota de Crédito'),
         ('111', 'Nota de Débito')],
        string='Tipo de Comprobante de Compra', default='110')

    # Booleanos de los impuestos que pueden ser imputados los comprobantes
    imputacion_iva = fields.Boolean('Imputa al IVA', default=_get_default_iva)
    mostrar_iva = fields.Boolean('Mostrar el campo de IVA', default=_get_default_iva)
    imputacion_ire = fields.Boolean('Imputa al IRE', default=_get_default_ire)
    mostrar_ire = fields.Boolean('Mostrar el campo de IRE', default=_get_default_ire)
    imputacion_irp = fields.Boolean('Imputa al IRP-RSP', default=_get_default_irp)
    mostrar_irp = fields.Boolean('Mostrar el campo de IRP-RSP', default=_get_default_irp)
    no_imputa = fields.Boolean('No imputa', default=False)

    # Campos que aparecen solamente en las notas, osea en las facturas rectificativas tanto de cliente como proveedor
    numero_doc_asoc = fields.Char('Número de Documento Asociado', store=True)
    timbrado_doc_asoc = fields.Char('Timbrado de Documento Asociado', store=True)

    @api.onchange('move_type', 'tipo_comprobante_compra', 'tipo_comprobante_venta', 'tipo_comprobante_compra_nota', 'tipo_comprobante_venta_nota')
    def _compute_domain_partner_id(self):
        if self.move_type in ('out_invoice', 'out_refund', 'out_receipt'):
            return {
                'domain': {
                    'partner_id': []
                }
            }
        else:
            if self.move_type in ('in_invoice', 'in_refund') and self.tipo_comprobante_compra not in ('107', '101'):
                return {
                    'domain': {
                        'partner_id': [('tipo_documento', '=', '11')]
                    }
                }
            elif self.move_type in ('in_invoice', 'in_refund') and self.tipo_comprobante_compra == '101':
                return {
                    'domain': {
                        'partner_id': [('id', '=', self.env.user.company_id.partner_id.id)]
                    }
                }
            else:
                return {
                    'domain': {
                        'partner_id': [('tipo_documento', '!=', '15')]
                    }
                }

    @api.onchange('tipo_comprobante_venta', 'tipo_comprobante_venta_nota')
    def _compute_domain_talonario_venta(self):
        if self.move_type == 'out_invoice':
            if self.tipo_comprobante_venta:
                return {
                    'domain': {
                        'x_studio_field_QV8yr': [('x_studio_tipo_de_talonario', '=', self.tipo_comprobante_venta)]
                    }
                }
            else:
                return {
                    'domain': {
                        'x_studio_field_QV8yr': [('x_studio_tipo_de_talonario', '=', '109')]
                    }
                }
        elif self.move_type == 'out_refund':
            if self.tipo_comprobante_venta_nota:
                return {
                    'domain': {
                        'x_studio_talonario_nota_credito': [('x_studio_tipo_de_talonario', '=', self.tipo_comprobante_venta_nota)]
                    }
                }
            else:
                return {
                    'domain': {
                        'x_studio_talonario_nota_credito': []
                    }
                }
        else:
            return {
                'domain': {
                    'x_studio_field_QV8yr': [],
                    'x_studio_talonario_nota_credito': [('x_studio_tipo_de_talonario', '=', '110')]
                }
            }

    @api.onchange('tipo_comprobante_compra')
    def onchange_tipo_comprobante_compra(self):
        if self.tipo_comprobante_compra == '101':
            self.partner_id = self.env.user.company_id.partner_id

    @api.onchange('numero_doc_asoc')
    def onchange_numero_doc_asoc(self):
        if self.numero_doc_asoc:
            numeraciones = self.numero_doc_asoc.split('-')
            if len(numeraciones) == 3 and len(numeraciones[0]) == 3 and len(numeraciones[1]) == 3 and len(numeraciones[2]) == 7:
                try:
                    int(numeraciones[0])
                    int(numeraciones[1])
                    int(numeraciones[2])
                except:
                    raise ValidationError('Para el número de comprobante asociado, ingrese solo numeros entre los guiones. Ej.: 001-001-0000001')
            else:
                raise ValidationError(
                    'El número del documento asociado debe tener el formato ###-###-#######, solo se permiten números y guiones')

    @api.model_create_multi
    def create(self, vals):
        move = super(AccountMove, self).create(vals)

        if move.partner_id and not move.partner_id.nro_documento:
            raise ValidationError("El cliente/proveedor no cuenta con número de documento")

        # Al crear una factura de venta o rectificativa de cliente se verifica que cuente con al menos un impuesto
        if move.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
            if not move.imputacion_iva and not move.imputacion_ire and not move.imputacion_irp:
                raise ValidationError('Un comprobante de Ventas se debe imputar a algún impuesto.')

            tipo = None
            talonario = None

            move_type = move.move_type
            if 'move_type' in vals:
                move_type = vals['move_type']

            if move_type == 'out_invoice':
                tipo = move.tipo_comprobante_venta
                if 'tipo_comprobante_venta' in vals:
                    tipo = vals['tipo_comprobante_venta']
                talonario = move.x_studio_field_QV8yr
                if 'x_studio_field_QV8yr' in vals:
                    if vals['x_studio_field_QV8yr']:
                        talonario = move.env['x_talonario'].browse(int(vals['x_studio_field_QV8yr']))
                    else:
                        talonario = False

            elif move_type == 'out_refund':
                tipo = move.tipo_comprobante_venta_nota
                if 'tipo_comprobante_venta_nota' in vals:
                    tipo = vals['tipo_comprobante_venta_nota']
                talonario = move.x_studio_talonario_nota_credito
                if 'x_studio_talonario_nota_credito' in vals:
                    if vals['x_studio_talonario_nota_credito']:
                        talonario = move.env['x_talonario'].browse(int(vals['x_studio_talonario_nota_credito']))
                    else:
                        talonario = False

            if talonario and talonario.x_studio_tipo_de_talonario != tipo:
                raise ValidationError('El tipo de comprobante de venta no concuerda con el tipo del talonario.')


            # COMPRAS
            if move.move_type == 'in_invoice' or move.move_type == 'in_refund':
                tipo_documento = move.tipo_comprobante_compra
                if 'tipo_comprobante_compra' in vals:
                    if vals['tipo_comprobante_compra']:
                        tipo_documento = vals['tipo_comprobante_compra']
                    else:
                        tipo_documento = False
                if move.partner_id:
                    tipo_partner = move.partner_id.tipo_documento
                    if 'partner_id' in vals:
                        if vals['partner_id']:
                            tipo_partner = move.env['res.partner'].browse(int(vals['partner_id'])).tipo_documento
                        else:
                            tipo_partner = False

                if tipo_partner and tipo_documento:
                    if tipo_documento not in ('101', '107') and tipo_partner != '11':
                        error_comprobante_identificacion(tipo_documento, tipo_partner)
                    elif tipo_documento == '101' and move.partner_id != move.env.user.company_id.partner_id:
                        raise ValidationError('Solo puede elegir a la compañía actual como proveedor con el tipo Autofactura')
        return move

    def write(self, vals):
        if 'move_type' in vals and vals['move_type'] in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund') or self.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):

            if self.partner_id and not self.partner_id.nro_documento:
                raise ValidationError("El cliente/proveedor no cuenta con número de documento")

            # Se controla que si es un documento de venta (factura o nota) tenga al menos uno de los impuestos asignados
            # Si se edito alguno se compara para ver si es que esta al menos uno asignado
            imputa_iva_aux = self.imputacion_iva
            imputa_ire_aux = self.imputacion_ire
            imputa_irp_aux = self.imputacion_irp
            if 'imputacion_iva' in vals:
                imputa_iva_aux = vals['imputacion_iva']
            if 'imputacion_ire' in vals:
                imputa_ire_aux = vals['imputacion_ire']
            if 'imputacion_irp' in vals:
                imputa_irp_aux = vals['imputacion_irp']
            if not imputa_iva_aux and not imputa_ire_aux and not imputa_irp_aux:
                raise ValidationError('Un comprobante se debe imputar a algún impuesto.')

            tipo = None
            talonario = None

            move_type = self.move_type
            if 'move_type' in vals:
                move_type = vals['move_type']

            if move_type == 'out_invoice':
                tipo = self.tipo_comprobante_venta
                if 'tipo_comprobante_venta' in vals:
                    tipo = vals['tipo_comprobante_venta']
                talonario = self.x_studio_field_QV8yr
                if 'x_studio_field_QV8yr' in vals:
                    if vals['x_studio_field_QV8yr']:
                        talonario = self.env['x_talonario'].browse(int(vals['x_studio_field_QV8yr']))
                    else:
                        talonario = False

            elif move_type == 'out_refund':
                tipo = self.tipo_comprobante_venta_nota
                if 'tipo_comprobante_venta_nota' in vals:
                    tipo = vals['tipo_comprobante_venta_nota']
                talonario = self.x_studio_talonario_nota_credito
                if 'x_studio_talonario_nota_credito' in vals:
                    if vals['x_studio_talonario_nota_credito']:
                        talonario = self.env['x_talonario'].browse(int(vals['x_studio_talonario_nota_credito']))
                    else:
                        talonario = False

            if talonario and talonario.x_studio_tipo_de_talonario != tipo:
                raise ValidationError('El tipo de comprobante de venta no concuerda con el tipo del talonario.')

            """ 
            Verifica que el tipo de partner sea permitido para el tipo de documento, ejemplo, el comprobante de
            ingreso Liquidación de Salario solo permite un pagador con tipo de documento RUC. 
            """

            #COMPRAS
            if self.move_type == 'in_invoice' or self.move_type == 'in_refund':
                tipo_documento = self.tipo_comprobante_compra
                if 'tipo_comprobante_compra' in vals:
                    if vals['tipo_comprobante_compra']:
                        tipo_documento = vals['tipo_comprobante_compra']
                    else:
                        tipo_documento = False
                tipo_partner = False
                if self.partner_id:
                    tipo_partner = self.partner_id.tipo_documento
                    if 'partner_id' in vals:
                        if vals['partner_id']:
                            tipo_partner = self.env['res.partner'].browse(int(vals['partner_id'])).tipo_documento

                if tipo_partner and tipo_documento:
                    if tipo_documento not in ('101', '107') and tipo_partner != '11':
                        error_comprobante_identificacion(tipo_documento, tipo_partner)
                    elif tipo_documento == '101':
                        partner_actual = self.partner_id.id
                        if 'partner_id' in vals:
                            if vals['partner_id']:
                                partner_actual = vals['partner_id']
                            else:
                                partner_actual = False
                        if partner_actual != self.env.user.company_id.partner_id.id:
                            raise ValidationError('Solo puede elegir a la compañía actual como proveedor con el tipo Autofactura')

        return super(AccountMove, self).write(vals)


def error_comprobante_identificacion(cod_comprobante, cod_identificacion):
    raise ValidationError('Para el tipo de comprobante "' + TIPOS_COMPROBANTES[cod_comprobante] +
                          '" no se puede elegir un Contacto con identificacion de tipo "' +
                          TIPOS_IDENTIFICACION[cod_identificacion] + '"')


def formatear_numero_comprobante(numero):
    numeros = numero.split('-')
    numeros[2] = numeros[2].zfill(7)
    return '-'.join(numeros)
