# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
import base64
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError, UserError
from ..models.account_move import formatear_numero_comprobante

CANT_REGISTROS_MARANGATU = 5000

MESES = [
    ('01', 'Enero'),
    ('02', 'Febrero'),
    ('03', 'Marzo'),
    ('04', 'Abril'),
    ('05', 'Mayo'),
    ('06', 'Junio'),
    ('07', 'Julio'),
    ('08', 'Agosto'),
    ('09', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
]

TIPOS_REPORTES = [
    ('1', 'Ventas'),
    ('2', 'Compras'),
  # ('3', 'Ingresos'),
  # ('4', 'Egresos'),
    ('5', 'Todos los tipos de registros')
]


TIPOS_FORMULARIOS = [
    ('1', '955-Registro Mensual de Comprobantes'),
    ('2', '956-Registro Anual de Comprobantes'),
]


# FUNCION QUE DIVIDE LA LISTA EN SUBLISTAS
def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


class Archivos(models.Model):
    _name = 'marangatu.archivo'
    _description = "Archivo generado para Marangatu"
    _order = "fecha_creacion desc"

    name = fields.Char('Nombre')
    periodo = fields.Char('Periodo', size=7)
    archivo = fields.Binary('Archivo', filename='name')
    fecha_creacion = fields.Datetime("Fecha de Creacion")
    marangatu = fields.Many2one('marangatu.reporte', ondelete='cascade', string="Marangatu", required=True)

    @api.model
    def create(self, vals):
        vals.update({'fecha_creacion': datetime.datetime.now()})
        return super(Archivos, self).create(vals)


class Marangatu(models.Model):
    _name = "marangatu.reporte"
    _description = "Generar informe para el Marangatu"
    _order = "fecha_creacion desc"

    name = fields.Char('Nombre')
    periodo = fields.Char('Periodo', size=7)
    anho = fields.Char('Año', size=4)
    mes = fields.Selection(MESES, "Mes")
    tipo_reporte = fields.Selection(TIPOS_REPORTES, "Tipo Reporte")
    tipo_formulario = fields.Selection(TIPOS_FORMULARIOS, "Tipo de Formulario")
    fecha_creacion = fields.Datetime("Fecha de Creacion")
    archivos = fields.One2many('marangatu.archivo', "marangatu")

    @api.model
    def create(self, vals):
        vals.update({'fecha_creacion': datetime.datetime.now()})
        return super(Marangatu, self).create(vals)

    @api.onchange('anho')
    def onchange_anho(self):
        if not self.anho:
            return {}
        if self.anho and not self.anho.isdigit():
            raise ValidationError('El campo "año" debe ser un numero entero')
        if self.anho and len(self.anho) < 4 or int(self.anho) < 1900 or int(self.anho) > 2100:
            raise ValidationError('Año inválido')
        return {}

    def report_marangatu(self, vals=None):
        for rec in self:
            if rec.anho and rec.tipo_formulario:
                doc = {}
                if rec.anho and rec.tipo_reporte:
                    if len(rec.anho) < 4 or int(rec.anho) < 1900 or int(rec.anho) > 2100:
                        raise ValidationError('Año inválido')
                    if not rec.anho.isdigit():
                        raise ValidationError('El campo "año" debe ser un número entero')
                    if not rec._uid:
                        raise ValidationError('No se puede determinar la compañía')
                    if rec.tipo_formulario == '1':
                        if not rec.anho:
                            raise ValidationError('No especifico el mes')
                        periodo = rec.mes + '/' + rec.anho
                    elif rec.tipo_formulario == '2':
                        periodo = rec.anho
                    cant_reportes_previos = len(self.env['marangatu.reporte'].search([('periodo', '=', periodo), ('tipo_reporte', '=', rec.tipo_reporte)]))
                    if rec.tipo_reporte == '5':
                        doc.update({'name': 'Reporte ' + str(cant_reportes_previos + 1) + ' completo del periodo ' + periodo, 'periodo': periodo})
                    elif rec.tipo_reporte == '1':
                        doc.update({'name': 'Reporte ' + str(cant_reportes_previos + 1) + ' de tipo Ventas del periodo ' + periodo,'periodo': periodo})
                    else:
                        doc.update({'name': 'Reporte ' + str(cant_reportes_previos + 1) + ' de tipo Compras del periodo ' + periodo, 'periodo': periodo})
                    doc.update({'anho': rec.anho})
                    doc.update({'tipo_formulario': rec.tipo_formulario})
                    doc.update({'tipo_reporte': rec.tipo_reporte})
                    doc.update({'fecha_creacion': rec.fecha_creacion})
                    if rec.tipo_formulario == '1':
                        doc.update({'mes': rec.mes})
                    doc.update({'archivos': rec.generar_informe(doc)})

                return super(Marangatu, rec).create(doc)

    def generar_informe(self, doc):
        for rec in self:

            company = self.env.user.company_id
            ruc_company = company.get_ruc_sin_dv()
            if not ruc_company:
                raise ValidationError('La Compañía actual no tiene RUC asignado')
            iva = self.get_default_iva()
            vals = doc
            anho = vals['anho']
            tipo_reporte = vals['tipo_reporte']
            primera_fecha = datetime.datetime(int(anho), 1, 1)
            if vals['tipo_formulario'] == '1':
                periodo = vals['mes'] + '/' + vals['anho']
                mes = vals['mes']
                primera_fecha = primera_fecha.replace(month=int(mes))
                ultimo_dia = ultimo_dia_del_mes(primera_fecha).day
                documentos_ventas_compras = self.env['account.move'].search([('date','<=',anho+'-'+mes+'-'+str(ultimo_dia)),('date','>=',anho+'-'+mes+'-01'),('move_type','in',('in_invoice','out_invoice','in_refund','out_refund')),('state','=','posted')])
                # documentos_ingresos_egresos = self.env['account.payment'].search([('date','<=',anho+'-'+mes+'-'+str(ultimo_dia)),('date','>=',anho+'-'+mes+'-01'),('state','=','posted')])
                documentos_ingresos_egresos = []
            elif vals['tipo_formulario'] == '2':
                periodo = vals['anho']
                documentos_ventas_compras = self.env['account.move'].search(
                    [('date', '<=', anho + '-12-31'), ('date', '>=', anho + '-01-01'),
                     ('move_type', 'in', ('in_invoice', 'out_invoice', 'in_refund', 'out_refund')),('state','=','posted')])
                # documentos_ingresos_egresos = self.env['account.payment'].search(
                #     [('date', '<=', anho + '-12-31'), ('date', '>=', anho + '-01-01'),('state','=','posted')])
                documentos_ingresos_egresos = []
            else:
                raise ValidationError('Solo elija entre reporte mensual o anual')

            cant_reportes_previos = len(self.env['marangatu.reporte'].search([('periodo', '=', periodo)]))
            nro_archivo_actual = cant_reportes_previos + 1
            lista_archivos = []
            documentos_ventas_compras_sobrantes = []
            documentos_ingresos_egresos_sobrantes = []

            while len(documentos_ventas_compras) + len(documentos_ingresos_egresos) > 0:
                if len(documentos_ventas_compras) + len(documentos_ingresos_egresos) > CANT_REGISTROS_MARANGATU:
                    if len(documentos_ventas_compras) <= CANT_REGISTROS_MARANGATU:
                        lineas_ingresos_egresos = CANT_REGISTROS_MARANGATU - len(documentos_ventas_compras)
                        documentos_ventas_compras_sobrantes = []
                        documentos_ingresos_egresos_sobrantes = documentos_ingresos_egresos[lineas_ingresos_egresos:]
                        documentos_ingresos_egresos = documentos_ingresos_egresos[:lineas_ingresos_egresos]
                    else:
                        documentos_ventas_compras_sobrantes = documentos_ventas_compras[CANT_REGISTROS_MARANGATU:]
                        documentos_ventas_compras = documentos_ventas_compras[:CANT_REGISTROS_MARANGATU]
                        documentos_ingresos_egresos_sobrantes = documentos_ingresos_egresos[:]
                        documentos_ingresos_egresos = []

                ventas = len(documentos_ventas_compras) > 0 and documentos_ventas_compras.filtered(lambda l: l.move_type == 'out_invoice' or l.move_type == 'out_refund') or False
                compras = len(documentos_ventas_compras) > 0 and documentos_ventas_compras.filtered(lambda l: l.move_type == 'in_invoice' or l.move_type == 'in_refund') or False
                # ingresos = len(documentos_ingresos_egresos) > 0 and documentos_ingresos_egresos.filtered(lambda l: l.payment_type == 'inbound') or False
                # egresos = len(documentos_ingresos_egresos) > 0 and documentos_ingresos_egresos.filtered(lambda l: l.payment_type == 'outbound') or False
                ingresos = []
                egresos = []
                texto = []
                if ventas and tipo_reporte in ('1', '5'):
                    for v in ventas:
                        linea = []
                        if v.date > datetime.date(year=2021, month=1, day=1) or v.date < datetime.date(year=2021, month=1, day=1) and v.invoice_payment_term_id and v.invoice_payment_term_id.es_credito:
                            linea.append('1')
                            linea.append(v.partner_id.tipo_documento)
                            linea.append(v.partner_id.tipo_documento == '11' and v.partner_id.get_ruc_sin_dv() or v.partner_id.nro_documento)
                            linea.append(v.partner_id.tipo_documento not in ('11', '12', '15') and v.partner_id.name or '')
                            linea.append(v.move_type == 'out_invoice' and v.tipo_comprobante_venta or v.tipo_comprobante_venta_nota)
                            linea.append(v.date.strftime('%d/%m/%Y'))
                            linea.append(v.timbrado)
                            linea.append(v.tipo_comprobante_venta not in ['112', '106'] and formatear_numero_comprobante(v.numeracion) or '')
                            iva_10 = int(sum([l.credit > 0 and l.credit or l.debit for l in v.line_ids if iva['iva_10_venta'] in l.tax_ids.ids or iva['iva_10_venta'] in l.tax_line_id.ids]))
                            iva_5 = int(sum([l.credit > 0 and l.credit or l.debit for l in v.line_ids if iva['iva_5_venta'] in l.tax_ids.ids or iva['iva_5_venta'] in l.tax_line_id.ids]))
                            exenta = int(sum([l.credit > 0 and l.credit or l.debit for l in v.line_ids if iva['exento_venta'] in l.tax_ids.ids or iva['exento_venta'] in l.tax_line_id.ids]))
                            suma_ivas = iva_10 + iva_5 + exenta
                            linea.append(str(iva_10) + ',' + str(iva_5) + ',' + str(exenta) + ',' + str(suma_ivas))
                            linea.append(v.partner_id.tipo_documento != '109' and '' or (v.invoice_payment_term_id and v.invoice_payment_term_id.es_credito) and '2' or '1')
                            linea.append(v.currency_id.name == 'PYG' and 'N' or 'S')
                            linea.append(v.imputacion_iva and 'S' or 'N')
                            linea.append(v.imputacion_ire and 'S' or 'N')
                            linea.append(v.imputacion_irp and 'S' or 'N')
                            linea.append(v.move_type == 'out_refund' and v.numero_doc_asoc or '')
                            linea.append(v.move_type == 'out_refund' and v.timbrado_doc_asoc or '')
                        else:
                            raise ValidationError('El comprobante ', formatear_numero_comprobante(v.numeracion), ' no es de tipo credito y tiene fecha anterior a 01/01/2021')
                        texto.append(','.join([arg for arg in linea]))

                if compras and tipo_reporte in ('2', '5'):
                    for c in compras:
                        linea = []
                        if c.date > datetime.date(year=2021, month=1, day=1) or c.date < datetime.date(year=2021, month=1, day=1) and c.invoice_payment_term_id and c.invoice_payment_term_id.es_credito:
                            linea.append('2')
                            linea.append(c.tipo_comprobante_compra in ['101', '107'] and c.partner_id.tipo_documento or '11')
                            linea.append(c.partner_id.tipo_documento == '11' and c.partner_id.get_ruc_sin_dv() or c.partner_id.nro_documento)
                            linea.append(c.partner_id.tipo_documento not in ['11', '12'] and c.partner_id.name or '')
                            linea.append(
                                c.move_type == 'in_invoice' and c.tipo_comprobante_compra or c.tipo_comprobante_compra_nota)
                            linea.append(c.date.strftime('%d/%m/%Y'))
                            linea.append(c.tipo_comprobante_compra != '107' and c.timbrado or '0')
                            linea.append(c.tipo_comprobante_compra not in ['112', '106', '107'] and formatear_numero_comprobante(c.numeracion) or '')
                            iva_10 = c.tipo_comprobante_compra not in ['101', '112', '104', '105'] and int(sum([l.credit > 0 and l.credit or l.debit for l in c.line_ids if iva['iva_10_compra'] in l.tax_ids.ids or iva['iva_10_compra'] in l.tax_line_id.ids])) or 0
                            iva_5 = c.tipo_comprobante_compra not in ['101', '112', '104', '105'] and int(sum([l.credit > 0 and l.credit or l.debit for l in c.line_ids if iva['iva_5_compra'] in l.tax_ids.ids or iva['iva_5_compra'] in l.tax_line_id.ids])) or 0
                            exenta = c.tipo_comprobante_compra not in ['101', '112', '104', '105'] and int(sum([l.credit > 0 and l.credit or l.debit for l in c.line_ids if iva['exento_compra'] in l.tax_ids.ids or iva['exento_compra'] in l.tax_line_id.ids])) or 0
                            suma_ivas = c.tipo_comprobante_compra not in ['101', '112', '104', '105'] and iva_10 + iva_5 + exenta or int(abs(c.amount_total_signed))
                            linea.append(str(iva_10) + ',' + str(iva_5) + ',' + str(exenta) + ',' + str(suma_ivas))
                            linea.append(
                                c.partner_id.tipo_documento != '109' and '' or (c.invoice_payment_term_id and c.invoice_payment_term_id.es_credito) and '2' or '1')
                            linea.append(c.currency_id.name == 'PYG' and 'N' or 'S')
                            linea.append(c.imputacion_iva and 'S' or 'N')
                            linea.append(c.imputacion_ire and 'S' or 'N')
                            linea.append(c.imputacion_irp and 'S' or 'N')
                            linea.append(c.no_imputa and 'S' or 'N')
                            linea.append(c.move_type == 'in_refund' and c.numero_doc_asoc or '')
                            linea.append(c.move_type == 'in_refund' and c.timbrado_doc_asoc or '')
                        else:
                            raise ValidationError('El comprobante ', formatear_numero_comprobante(c.numeracion),
                                                  ' no es de tipo credito y tiene fecha anterior a 01/01/2021')
                        texto.append(','.join([arg for arg in linea]))

                if ingresos:
                    for i in ingresos:
                        linea = []
                        if i.date > datetime.date(year=2021, month=1, day=1) or i.date < datetime.date(year=2021, month=1, day=1) and i.invoice_payment_term_id and i.invoice_payment_term_id.es_credito:
                            linea.append('3')
                            linea.append(i.tipo_comprobante_ingreso)
                            linea.append(i.tipo_comprobante_ingreso == '208' and i.date.strftime('%m/%Y') or i.date.strftime('%d/%m/%Y'))
                            linea.append(i.tipo_comprobante_ingreso != '208' and i.x_studio_nro_recibo or '')
                            linea.append(i.tipo_comprobante_ingreso == '210' and i.partner_id.tipo_documento in ['11', '12', '13'] and i.partner_id.tipo_documento or i.tipo_comprobante_ingreso == '208' and '11' or i.tipo_comprobante_ingreso not in ['208', '210'] and i.partner_id.tipo_documento or i.partner_id.tipo_documento)
                            linea.append(i.partner_id.tipo_documento == '11' and i.partner_id.get_ruc_sin_dv() or i.partner_id.nro_documento)
                            linea.append(i.partner_id.tipo_documento not in ['11', '12'] and i.partner_id.name or '')
                            gravado = i.tipo_comprobante_ingreso != '203' and int(i.monto_gravado_gs) or 0
                            no_gravado = i.tipo_comprobante_ingreso != '203' and int(i.monto_no_gravado_gs) or 0
                            suma_ivas = i.tipo_comprobante_ingreso != '203' and gravado + no_gravado or int(abs(i.amount_total_signed))
                            linea.append(str(gravado) + ',' + str(no_gravado) + ',' + str(suma_ivas))
                            linea.append(i.imputacion_ire and 'S' or 'N')
                            linea.append(i.imputacion_irp and 'S' or 'N')
                            linea.append(i.tipo_comprobante_ingreso == '210' and i.tipo_doc_asoc or '')
                            linea.append(i.tipo_comprobante_ingreso == '203' and i.numero_doc_asoc or '')
                            linea.append(i.tipo_comprobante_ingreso == '203' and i.timbrado_doc_asoc or '')
                        else:
                            raise ValidationError('El comprobante ', i.x_studio_nro_recibo,
                                                  ' no es de tipo credito y tiene fecha anterior a 01/01/2021')
                        texto.append(','.join([arg for arg in linea]))

                if egresos:
                    for e in egresos:
                        linea = []
                        if e.date > datetime.date(year=2021, month=1, day=1) or e.date < datetime.date(year=2021, month=1, day=1) and e.invoice_payment_term_id and e.invoice_payment_term_id.es_credito:
                            linea.append('4')
                            linea.append(e.tipo_comprobante_egreso)
                            linea.append(e.tipo_comprobante_egreso in ['208', '206'] and e.date.strftime('%m/%Y') or e.date.strftime('%d/%m/%Y'))
                            linea.append(e.tipo_comprobante_egreso not in ['205', '207', '208','206'] and e.numero_comprobante or '')
                            linea.append(e.tipo_comprobante_egreso == '202' and '17' or e.tipo_comprobante_egreso in ['204', '205'] and '11' or e.tipo_comprobante_egreso not in ['206', '207', '211'] and e.partner_id.tipo_documento or '')
                            linea.append(e.tipo_comprobante_egreso not in ['206', '207', '211'] and (e.partner_id.tipo_documento == '11' and e.partner_id.get_ruc_sin_dv() or e.partner_id.nro_documento) or '')
                            linea.append(e.tipo_comprobante_egreso in ['202', '207', '211'] and e.partner_id.name or e.partner_id.tipo_documento not in ['11', '12'] and e.tipo_comprobante_egreso != '202' and e.partner_id.name or '')
                            linea.append(str(int(abs(e.amount_total_signed))))
                            linea.append(e.tipo_comprobante_egreso == '207' and e.imputacion_iva and 'S' or 'N')
                            linea.append(e.imputacion_ire and 'S' or 'N')
                            linea.append(e.imputacion_irp and 'S' or 'N')
                            linea.append(e.no_imputa and 'S' or 'N')
                            linea.append(e.tipo_comprobante_egreso in ['207', '211'] and e.nro_cta_tarjeta or '')
                            linea.append(e.tipo_comprobante_egreso in ['207', '211'] and e.entidad_financiera or '')
                            linea.append(e.tipo_comprobante_egreso == '206' and e.id_empleador or '')
                            linea.append(e.tipo_comprobante_egreso == '209' and e.tipo_doc_asoc or '')
                            linea.append(e.tipo_comprobante_egreso == '201' and e.numero_doc_asoc or '')
                            linea.append(e.tipo_comprobante_egreso == '201' and e.timbrado_doc_asoc or '')
                        else:
                            raise ValidationError('El comprobante ', e.numero_comprobante,
                                                  ' no es de tipo credito y tiene fecha anterior a 01/01/2021')
                        texto.append(','.join([arg for arg in linea]))

                texto_final = ('\n'.join([linea for linea in texto])).encode('utf-8')


                if vals['tipo_formulario'] == '1':
                    filename = ruc_company + '_REG_' + vals['mes'] + vals['anho'] + '_' + str(nro_archivo_actual).zfill(5) + '.csv'
                elif vals['tipo_formulario'] == '2':
                    filename = ruc_company + '_REG_' + vals['anho'] + '_' + str(nro_archivo_actual).zfill(5) + '.csv'
                datos = {
                    'archivo': base64.b64encode(texto_final),
                    'periodo': periodo,
                    'name': filename,
                }
                lista_archivos.append([0, False, datos])

                nro_archivo_actual += 1

                documentos_ventas_compras = documentos_ventas_compras_sobrantes
                documentos_ingresos_egresos = documentos_ingresos_egresos_sobrantes
                documentos_ventas_compras_sobrantes = []
                documentos_ingresos_egresos_sobrantes = []

            return lista_archivos

    def get_default_iva(self):
        config_param_obj = self.env['ir.config_parameter']
        dic = {}
        if config_param_obj.sudo().get_param('iva_10_venta'):
            dic['iva_10_venta'] = int(config_param_obj.sudo().get_param('iva_10_venta'))
        else:
            raise UserError(
                'No ha ingresado el impuesto por defecto para IVA Débito Fiscal 10% (Ventas), por favor verifique en Ajustes/Facturación.')

        if config_param_obj.sudo().get_param('iva_5_venta'):
            dic['iva_5_venta'] = int(config_param_obj.sudo().get_param('iva_5_venta'))
        else:
            raise UserError(
                'No ha ingresado el impuesto por defecto para IVA Débito Fiscal 5% (Ventas), por favor verifique en Ajustes/Facturación.')

        if config_param_obj.sudo().get_param('exento_venta'):
            dic['exento_venta'] = int(config_param_obj.sudo().get_param('exento_venta'))
        else:
            raise UserError(
                'No ha ingresado el impuesto por defecto para Ventas Extentas, por favor verifique en Ajustes/Facturación.')
        if config_param_obj.sudo().get_param('iva_10_compra'):
            dic['iva_10_compra'] = int(config_param_obj.sudo().get_param('iva_10_compra'))
        else:
            raise UserError(
                'No ha ingresado el impuesto por defecto para IVA Crédito Fiscal 10% (Compras), por favor verifique en Ajustes/Facturación.')

        if config_param_obj.sudo().get_param('iva_5_compra'):
            dic['iva_5_compra'] = int(config_param_obj.sudo().get_param('iva_5_compra'))
        else:
            raise UserError(
                'No ha ingresado el impuesto por defecto para IVA Crédito Fiscal 5% (Compras), por favor verifique en Ajustes/Facturación.')

        if config_param_obj.sudo().get_param('exento_compra'):
            dic['exento_compra'] = int(config_param_obj.sudo().get_param('exento_compra'))
        else:
            raise UserError(
                'No ha ingresado el impuesto por defecto para Compras Extentas, por favor verifique en Ajustes/Facturación.')
        return dic


    def _get_month_default():
        mes = datetime.datetime.now().month - 1
        mes = str(12 if mes == 0 else mes)
        return '0' + mes if len(mes) == 1 else mes

    _defaults = {
        'tipo_reporte': '1',
        'tipo_formulario': '5',
        'anho': str(datetime.datetime.now().year),
        'mes': str(_get_month_default()),

    }


def ultimo_dia_del_mes(fecha):
    return fecha.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
