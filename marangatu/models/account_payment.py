# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from ..models.account_move import formatear_numero_comprobante
#
# TIPOS_COMPROBANTES = {
#     '201': 'Comprobante de Egresos por Compras a Crédito',
#     '202': 'Comprobante del Exterior Legalizado',
#     '203': 'Comprobante de Ingresos por Ventas a Crédito',
#     '204': 'Comprobante de Ingresos Entidades Públicas, Religiosas o de Beneficio Público',
#     '205': 'Extracto de Cuenta - Billetaje Electrónico',
#     '206': 'Extracto de Cuenta de IPS',
#     '207': 'Extracto de Cuenta TC/TD',
#     '208': 'Liquidación de Salario',
#     '209': 'Otros Comprobantes de Egresos',
#     '210': 'Otros Comprobantes de Ingreso',
#     '211': 'Transferencias o Giros Bancarios/Boleta de Depósito'
# }
#
# TIPOS_IDENTIFICACION = {
#     '11': 'RUC',
#     '12': 'Cédula de Identidad',
#     '13': 'Pasaporte',
#     '14': 'Cédula Extranjera',
#     '15': 'Sin Nombre',
#     '16': 'Diplomático',
#     '17': 'Identificación Tributaria'
# }
#
#
# class AccountPayment(models.Model):
#     _inherit = "account.payment"
#
#     # Campo en el modelo de pagos para elegir el tipo de comprobantes de ingreso
#     tipo_comprobante_ingreso = fields.Selection(
#         [('203', 'Comprobante de Ingresos por Ventas a Crédito'),
#          ('208', 'Liquidación de Salario'),
#          ('210', 'Otros Comprobantes de Ingreso')], string='Tipo de Comprobante de Ingreso')
#
#     # Campo en el modelo de pagos para elegir el tipo de comprobantes de egreso
#     tipo_comprobante_egreso = fields.Selection(
#         [('201', 'Comprobante de Egresos por Compras a Crédito'),
#          ('202', 'Comprobante del Exterior Legalizado'),
#          ('204', 'Comprobante de Ingresos Entidades Públicas, Religiosas o de Beneficio Público'),
#          ('205', 'Extracto de Cuenta - Billetaje Electrónico'),
#          ('206', 'Extracto de Cuenta de IPS'),
#          ('207', 'Extracto de Cuenta TC/TD'),
#          ('208', 'Liquidación de Salario'),
#          ('209', 'Otros Comprobantes de Egresos'),
#          ('211', 'Transferencias o Giros Bancarios/Boleta de Depósito')], string='Tipo de Comprobante de Egreso')
#
#     # Impuestos a los cuales puede imputar el comprobante
#     imputacion_iva = fields.Boolean('Imputa al IVA', default=True)
#     imputacion_ire = fields.Boolean('Imputa al IRE', default=False)
#     imputacion_irp = fields.Boolean('Imputa al IRP-RSP', default=False)
#     no_imputa = fields.Boolean('No imputa', default=False)
#
#     # Se separan los montos para los comprobantes de ingresos que necesitan realizar esta diferenciación
#     monto_gravado = fields.Monetary('Monto Gravado', default=0)
#     monto_gravado_gs = fields.Monetary('Monto Gravado Gs', default=0)
#     monto_no_gravado = fields.Monetary('Monto No Gravado', default=0)
#     monto_no_gravado_gs = fields.Monetary('Monto No Gravado Gs', default=0)
#
#     # Campos requeridos para los distintos tipos de comprobantes
#     numero_comprobante = fields.Char('Número de Comprobante')
#     nro_cta_tarjeta = fields.Char('Número de Cuenta o Tarjeta')
#     entidad_financiera = fields.Char('Banco/Financiera/Cooperativa')
#     id_empleador = fields.Char('Identificación del Empleador')
#     tipo_doc_asoc = fields.Char('Tipo de Documento Asociado')
#     numero_doc_asoc = fields.Char('Número de Documento Asociado')
#     timbrado_doc_asoc = fields.Char('Timbrado de Documento Asociado')
#
#     @api.onchange('payment_type', 'tipo_comprobante_ingreso', 'tipo_comprobante_egreso')
#     def _compute_domain_partner_id(self):
#         if self.payment_type == 'outbound':
#             if self.tipo_comprobante_egreso in ('204', '205'):
#                 return {
#                     'domain': {
#                         'partner_id': [('tipo_documento', '=', '11')]
#                     }
#                 }
#             elif self.tipo_comprobante_egreso == '202':
#                 return {
#                     'domain': {
#                         'partner_id': [('tipo_documento', '=', '17')]
#                     }
#                 }
#             else:
#                 return {
#                     'domain': {
#                         'partner_id': [('tipo_documento', '!=', '15')]
#                     }
#                 }
#         else:
#             if self.payment_type == 'inbound' and self.tipo_comprobante_ingreso == '210':
#                 return {
#                     'domain': {
#                         'partner_id': [('tipo_documento', 'in', ('11', '12', '13'))]
#                     }
#                 }
#             elif self.payment_type == 'inbound' and self.tipo_comprobante_ingreso == '208':
#                 return {
#                     'domain': {
#                         'partner_id': [('tipo_documento', '=', '11')]
#                     }
#                 }
#             else:
#                 return {
#                     'domain': {
#                         'partner_id': [('tipo_documento', '!=', '15')]
#                     }
#                 }
#
#     def write(self, vals):
#         if 'payment_type' in vals and vals['payment_type'] in ('inbound', 'outbound') or self.payment_type in ('inbound', 'outbound'):
#
#             # Se controla que si es un comprobante de ingreso o egreso tenga al menos uno de los impuestos asignados
#             # Si se edito alguno se compara para ver si es que esta al menos uno asignado
#
#             if ('payment_type' in vals and vals['payment_type'] == 'outbound' and not self.payment_type == 'outbound' or self.payment_type == 'outbound') and ('tipo_comprobante_egreso' in vals and vals['tipo_comprobante_egreso'] == '207' or 'tipo_comprobante_egreso' not in vals and self.tipo_comprobante_egreso == '207'):
#                 imputa_iva_aux = self.imputacion_iva
#                 if 'imputacion_iva' in vals:
#                     imputa_iva_aux = vals['imputacion_iva']
#             else:
#                 imputa_iva_aux = False
#
#             imputa_ire_aux = self.imputacion_ire
#             imputa_irp_aux = self.imputacion_irp
#             if 'imputacion_ire' in vals:
#                 imputa_ire_aux = vals['imputacion_ire']
#             if 'imputacion_irp' in vals:
#                 imputa_irp_aux = vals['imputacion_irp']
#             if not imputa_ire_aux and not imputa_irp_aux and not imputa_iva_aux:
#                 raise ValidationError('Un comprobante se debe imputar a algún impuesto.')
#
#             """
#             Verifica que el tipo de partner sea permitido para el tipo de documento, ejemplo, el comprobante de
#             ingreso Liquidación de Salario solo permite un pagador con tipo de documento RUC.
#             """
#
#             tipo_ingreso_egreso = self.payment_type
#             if 'payment_type' in vals:
#                 if vals['payment_type']:
#                     tipo_ingreso_egreso = vals['payment_type']
#                 else:
#                     tipo_ingreso_egreso = False
#
#             if tipo_ingreso_egreso == 'inbound':
#                 tipo_documento = self.tipo_comprobante_ingreso
#                 if 'tipo_comprobante_ingreso' in vals:
#                     if vals['tipo_comprobante_ingreso']:
#                         tipo_documento = vals['tipo_comprobante_ingreso']
#                     else:
#                         tipo_documento = False
#             else:
#                 tipo_documento = self.tipo_comprobante_egreso
#                 if 'tipo_comprobante_egreso' in vals:
#                     if vals['tipo_comprobante_egreso']:
#                         tipo_documento = vals['tipo_comprobante_egreso']
#                     else:
#                         tipo_documento = False
#
#             tipo_partner = False
#             if self.partner_id:
#                 tipo_partner = self.partner_id.tipo_documento
#                 if 'partner_id' in vals:
#                     if vals['partner_id']:
#                         tipo_partner = self.env['res.partner'].browse(int(vals['partner_id'])).tipo_documento
#
#             if tipo_partner and tipo_documento:
#                 #COMPROBANTE INGRESOS
#                 if tipo_ingreso_egreso == 'inbound':
#                     if tipo_documento == '210' and tipo_partner not in ('11', '12', '13'):
#                         error_comprobante_identificacion(tipo_documento, tipo_partner)
#                     elif tipo_documento == '208' and tipo_partner != '11':
#                         error_comprobante_identificacion(tipo_documento, tipo_partner)
#                 #COMPROBANTES EGRESOS
#                 else:
#                     if tipo_documento in ('204', '205') and tipo_partner != '11':
#                         error_comprobante_identificacion(tipo_documento, tipo_partner)
#                     if tipo_documento == '202' and tipo_partner != '17':
#                         error_comprobante_identificacion(tipo_documento, tipo_partner)
#
#
#         return super(AccountPayment, self).write(vals)
#
#     @api.onchange('numero_doc_asoc')
#     def onchange_numero_doc_asoc(self):
#         if self.numero_doc_asoc:
#             numeraciones = self.numero_doc_asoc.split('-')
#             if len(numeraciones) == 3 and len(numeraciones[0]) == 3 and len(numeraciones[1]) == 3 and len(
#                     numeraciones[2]) == 7:
#                 try:
#                     int(numeraciones[0])
#                     int(numeraciones[1])
#                     int(numeraciones[2])
#                 except:
#                     raise ValidationError(
#                         'Para el número de comprobante asociado, ingrese solo numeros entre los guiones. Ej.: 001-001-0000001')
#             else:
#                 raise ValidationError(
#                     'El número del documento asociado debe tener el formato ###-###-#######, solo se permiten números y guiones')
#
#     @api.onchange('monto_gravado', 'monto_no_gravado', 'currency_id')
#     def _onchange_monto_gravado_no_gravado(self):
#         """
#         Con este onchange se suman los montos gravados y no gravados para el total del pago y también se guarda el
#         monto en guaraníes para los montos gravados y no gravados con el cambio de ese dia por si se este pagando
#         en alguna moneda extranjera que no sea Guaraní
#         :return:
#         """
#         if self.monto_gravado:
#             if self.monto_no_gravado:
#                 if self.currency_id.name != 'PYG':
#                     moneda_guarani = self.env['res.currency'].search([('name', '=', 'PYG')])
#                     moneda_extranjera = self.env['res.currency'].search([('name', '=', self.currency_id.name)])
#                     self.monto_gravado_gs = moneda_extranjera.compute(self.monto_gravado, moneda_guarani)
#                     self.monto_no_gravado_gs = moneda_extranjera.compute(self.monto_no_gravado, moneda_guarani)
#                 else:
#                     self.monto_gravado_gs = self.monto_gravado
#                     self.monto_no_gravado_gs = self.monto_no_gravado
#                 self.amount = self.monto_gravado + self.monto_no_gravado
#             else:
#                 self.monto_no_gravado_gs = 0
#                 if self.currency_id.name != 'PYG':
#                     moneda_guarani = self.env['res.currency'].search([('name', '=', 'PYG')])
#                     moneda_extranjera = self.env['res.currency'].search([('name', '=', self.currency_id.name)])
#                     self.monto_gravado_gs = moneda_extranjera.compute(self.monto_gravado, moneda_guarani)
#                 else:
#                     self.monto_gravado_gs = self.monto_gravado
#                 self.amount = self.monto_gravado
#         else:
#             self.monto_gravado_gs = 0
#             if self.monto_no_gravado:
#                 if self.currency_id.name != 'PYG':
#                     moneda_guarani = self.env['res.currency'].search([('name', '=', 'PYG')])
#                     moneda_extranjera = self.env['res.currency'].search([('name', '=', self.currency_id.name)])
#                     self.monto_no_gravado_gs = moneda_extranjera.compute(self.monto_no_gravado, moneda_guarani)
#                 else:
#                     self.monto_no_gravado_gs = self.monto_no_gravado
#                 self.amount = self.monto_no_gravado
#             else:
#                 self.monto_no_gravado_gs = 0
#
#
# class AccountPaymentRegister(models.TransientModel):
#     _inherit = "account.payment.register"
#
#     tipo_comprobante_ingreso = fields.Selection(
#         [('203', 'Comprobante de Ingresos por Ventas a Crédito'),
#          ('208', 'Liquidación de Salario'),
#          ('210', 'Otros Comprobantes de Ingreso')], string='Tipo de Comprobante de Ingreso')
#     tipo_comprobante_egreso = fields.Selection(
#         [('201', 'Comprobante de Egresos por Compras a Crédito'),
#          ('202', 'Comprobante del Exterior Legalizado'),
#          ('204', 'Comprobante de Ingresos Entidades Públicas, Religiosas o de Beneficio Público'),
#          ('205', 'Extracto de Cuenta - Billetaje Electronico'),
#          ('206', 'Extracto de Cuenta de IPS'),
#          ('207', 'Extracto de Cuenta TC/TD'),
#          ('208', 'Liquidación de Salario'),
#          ('209', 'Otros Comprobantes de Egresos'),
#          ('211', 'Transferencias o Giros Bancarios/Boleta de Depósito')], string='Tipo de Comprobante de Egreso')
#     numero_comprobante = fields.Char('Número de Comprobante')
#     monto_gravado = fields.Monetary('Monto Gravado', default=0)
#     monto_gravado_gs = fields.Monetary('Monto Gravado Gs', default=0)
#     monto_no_gravado = fields.Monetary('Monto No Gravado', default=0)
#     monto_no_gravado_gs = fields.Monetary('Monto No Gravado Gs', default=0)
#     imputacion_iva = fields.Boolean('Imputa al IVA', default=True)
#     imputacion_ire = fields.Boolean('Imputa al IRE', default=False)
#     imputacion_irp = fields.Boolean('Imputa al IRP-RSP', default=False)
#     no_imputa = fields.Boolean('No imputa', default=False)
#     nro_cta_tarjeta = fields.Char('Número de Cuenta o Tarjeta')
#     entidad_financiera = fields.Char('Banco/Financiera/Cooperativa')
#     id_empleador = fields.Char('Identificacion del Empleador')
#     tipo_doc_asoc = fields.Char('Tipo de Documento Asociado')
#     numero_doc_asoc = fields.Char('Número de Documento Asociado')
#     timbrado_doc_asoc = fields.Char('Timbrado de Documento Asociado')
#
#     @api.onchange('monto_gravado', 'monto_no_gravado', 'currency_id')
#     def _onchange_monto_gravado_no_gravado(self):
#         """
#         Con este onchange se suman los montos gravados y no gravados para el total del pago y también se guarda el
#         monto en guaraníes para los montos gravados y no gravados con el cambio de ese dia por si se este pagando
#         en alguna moneda extranjera que no sea Guaraní
#         :return:
#         """
#         if self.monto_gravado:
#             if self.monto_no_gravado:
#                 if self.currency_id.name != 'PYG':
#                     moneda_guarani = self.env['res.currency'].search([('name', '=', 'PYG')])
#                     moneda_extranjera = self.env['res.currency'].search([('name', '=', self.currency_id.name)])
#                     self.monto_gravado_gs = moneda_extranjera.compute(self.monto_gravado, moneda_guarani)
#                     self.monto_no_gravado_gs = moneda_extranjera.compute(self.monto_no_gravado, moneda_guarani)
#                 else:
#                     self.monto_gravado_gs = self.monto_gravado
#                     self.monto_no_gravado_gs = self.monto_no_gravado
#                 self.amount = self.monto_gravado + self.monto_no_gravado
#             else:
#                 self.monto_no_gravado_gs = 0
#                 if self.currency_id.name != 'PYG':
#                     moneda_guarani = self.env['res.currency'].search([('name', '=', 'PYG')])
#                     moneda_extranjera = self.env['res.currency'].search([('name', '=', self.currency_id.name)])
#                     self.monto_gravado_gs = moneda_extranjera.compute(self.monto_gravado, moneda_guarani)
#                 else:
#                     self.monto_gravado_gs = self.monto_gravado
#                 self.amount = self.monto_gravado
#         else:
#             self.monto_gravado_gs = 0
#             if self.monto_no_gravado:
#                 if self.currency_id.name != 'PYG':
#                     moneda_guarani = self.env['res.currency'].search([('name', '=', 'PYG')])
#                     moneda_extranjera = self.env['res.currency'].search([('name', '=', self.currency_id.name)])
#                     self.monto_no_gravado_gs = moneda_extranjera.compute(self.monto_no_gravado, moneda_guarani)
#                 else:
#                     self.monto_no_gravado_gs = self.monto_no_gravado
#                 self.amount = self.monto_no_gravado
#             else:
#                 self.monto_no_gravado_gs = 0
#
#     @api.onchange('numero_doc_asoc')
#     def onchange_numero_doc_asoc(self):
#         if self.numero_doc_asoc:
#             numeraciones = self.numero_doc_asoc.split('-')
#             if len(numeraciones) == 3 and len(numeraciones[0]) == 3 and len(numeraciones[1]) == 3 and len(
#                     numeraciones[2]) == 7:
#                 try:
#                     int(numeraciones[0])
#                     int(numeraciones[1])
#                     int(numeraciones[2])
#                 except:
#                     raise ValidationError(
#                         'Para el número de comprobante asociado, ingrese solo numeros entre los guiones. Ej.: 001-001-0000001')
#             else:
#                 raise ValidationError(
#                     'El número del documento asociado debe tener el formato ###-###-#######, solo se permiten números y guiones')
#
#     def _create_payment_vals_from_wizard(self):
#         payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
#         if self.tipo_comprobante_ingreso:
#             payment_vals['tipo_comprobante_ingreso'] = self.tipo_comprobante_ingreso
#         if self.tipo_comprobante_egreso:
#             payment_vals['tipo_comprobante_egreso'] = self.tipo_comprobante_egreso
#         if self.numero_comprobante:
#             payment_vals['numero_comprobante'] = self.numero_comprobante
#         if self.monto_gravado:
#             payment_vals['monto_gravado'] = self.monto_gravado
#             payment_vals['monto_gravado_gs'] = self.monto_gravado_gs
#         if self.monto_no_gravado:
#             payment_vals['monto_no_gravado'] = self.monto_no_gravado
#             payment_vals['monto_no_gravado_gs'] = self.monto_no_gravado_gs
#         payment_vals['imputacion_iva'] = self.imputacion_iva
#         payment_vals['imputacion_ire'] = self.imputacion_ire
#         payment_vals['imputacion_irp'] = self.imputacion_irp
#         payment_vals['no_imputa'] = self.no_imputa
#         if self.nro_cta_tarjeta:
#             payment_vals['nro_cta_tarjeta'] = self.nro_cta_tarjeta
#         if self.entidad_financiera:
#             payment_vals['entidad_financiera'] = self.entidad_financiera
#         if self.id_empleador:
#             payment_vals['id_empleador'] = self.id_empleador
#         if self.tipo_doc_asoc:
#             payment_vals['tipo_doc_asoc'] = self.tipo_doc_asoc
#         if self.numero_doc_asoc:
#             payment_vals['numero_doc_asoc'] = self.numero_doc_asoc
#         if self.timbrado_doc_asoc:
#             payment_vals['timbrado_doc_asoc'] = self.timbrado_doc_asoc
#         return payment_vals
#
#     def _create_payment_vals_from_batch(self, batch_result):
#         batch_values = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)
#         if self.tipo_comprobante_ingreso:
#             batch_values['tipo_comprobante_ingreso'] = self.tipo_comprobante_ingreso
#         if self.tipo_comprobante_egreso:
#             batch_values['tipo_comprobante_egreso'] = self.tipo_comprobante_egreso
#         if self.numero_comprobante:
#             batch_values['numero_comprobante'] = self.numero_comprobante
#         if self.monto_gravado:
#             batch_values['monto_gravado'] = self.monto_gravado
#             batch_values['monto_gravado_gs'] = self.monto_gravado_gs
#         if self.monto_no_gravado:
#             batch_values['monto_no_gravado'] = self.monto_no_gravado
#             batch_values['monto_no_gravado_gs'] = self.monto_no_gravado_gs
#         batch_values['imputacion_iva'] = self.imputacion_iva
#         batch_values['imputacion_ire'] = self.imputacion_ire
#         batch_values['imputacion_irp'] = self.imputacion_irp
#         batch_values['no_imputa'] = self.no_imputa
#         if self.nro_cta_tarjeta:
#             batch_values['nro_cta_tarjeta'] = self.nro_cta_tarjeta
#         if self.entidad_financiera:
#             batch_values['entidad_financiera'] = self.entidad_financiera
#         if self.id_empleador:
#             batch_values['id_empleador'] = self.id_empleador
#         if self.tipo_doc_asoc:
#             batch_values['tipo_doc_asoc'] = self.tipo_doc_asoc
#         if self.numero_doc_asoc:
#             batch_values['numero_doc_asoc'] = self.numero_doc_asoc
#         if self.timbrado_doc_asoc:
#             batch_values['timbrado_doc_asoc'] = self.timbrado_doc_asoc
#         return batch_values
#
#     @api.model
#     def _get_wizard_values_from_batch(self, batch_result):
#         wizard_values = super(AccountPaymentRegister, self)._get_wizard_values_from_batch(batch_result)
#         comprobante = batch_result['lines'].move_id
#         wizard_values['numero_doc_asoc'] = formatear_numero_comprobante(comprobante.numeracion)
#         wizard_values['timbrado_doc_asoc'] = comprobante.timbrado
#         return wizard_values
#
#
# def error_comprobante_identificacion(cod_comprobante, cod_identificacion):
#     raise ValidationError('Para el tipo de comprobante "' + TIPOS_COMPROBANTES[cod_comprobante] +
#                           '" no se puede elegir un Contacto con identificacion de tipo "' +
#                           TIPOS_IDENTIFICACION[cod_identificacion]+'"')