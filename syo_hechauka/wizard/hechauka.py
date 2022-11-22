# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
import base64
from .hechauka_query import get_query_compras, get_query_ventas

from odoo.exceptions import ValidationError, UserError

CANT_REGISTROS_HECHAUKA = 15000

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

TIPOS_FORMULARIOS = [
    ('211', 'Compras'),
    ('221', 'Ventas')
]

TIPOS_REPORTES = [
    ('1', 'Original'),
    ('2', 'Rectificativa'),
]


# FUNCION QUE DIVIDE LA LISTA EN SUBLISTAS
def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


class Archivos(models.Model):
    _name = 'syo_hechauka.hechauka.archivo'
    _description = "Archivo generado para hechauka"
    _order = "fecha_creacion desc"

    name = fields.Char('name')
    nombre = fields.Char('Nombre')
    archivo = fields.Binary('archivo', filename='nombre')
    hechauka = fields.Many2one('syo_hechauka.hechauka.wizard', ondelete='cascade', string="Hechauka", required=True)
    fecha_creacion = fields.Datetime("Fecha de Creacion")

    @api.model
    def create(self, vals):
        vals.update({'fecha_creacion': datetime.datetime.now()})
        return super(Archivos, self).create(vals)


class Hechauka(models.Model):
    _name = "syo_hechauka.hechauka.wizard"
    _description = "Generar informe para el Hechauka"

    name = fields.Char('Name')
    periodo = fields.Char('Periodo', size=6)
    anho = fields.Char('anho', size=4)
    mes = fields.Selection(MESES, "Mes")
    binario = fields.Binary("binario", filename='name')
    tipo_reporte = fields.Selection(TIPOS_REPORTES, "Tipo Reporte")
    archivos = fields.One2many('syo_hechauka.hechauka.archivo', "hechauka")
    tipo_formulario = fields.Selection(TIPOS_FORMULARIOS, "Libro")

    @api.onchange('anho')
    def onchange_anho(self):
        if not self.anho:
            return {}
        if self.anho and not self.anho.isdigit():
            raise ValidationError('El campo "año" debe ser un numero entero')
        if self.anho and len(self.anho) < 4 or int(self.anho) < 1900 or int(self.anho) > 2100:
            raise ValidationError('Año inválido')
        return {}

    def generar_informe_ventas(self, doc):
        for rec in self:
            #LIBRO VENTAS

            iva = self.get_default_iva()

            vals = doc
            periodo = vals['anho'] + vals['mes']
    
            nombre_mes = vals['mes']
            for m in MESES:
                if m[0] == vals['mes']:
                    nombre_mes = m[1]
                    break
    
            usuario = rec.env['res.users'].browse([rec._uid])
            QUERY = get_query_ventas(mes=str(int(vals['mes'])), anho=vals['anho'], iva_venta_10=str(iva['iva_10_venta']), iva_venta_5=str(iva['iva_5_venta']), exenta_venta=str(iva['exento_venta']), iva_compra_10=str(iva['iva_10_compra']), iva_compra_5=str(iva['iva_5_compra']), exenta_compra=str(iva['exento_compra']))
    
            rec._cr.execute(QUERY + ' SELECT * FROM T3 order by tipo_documento, fecha, number')
    
            ventas = rec._cr.fetchall()
            if not ventas:
                mensaje = 'No posee ningun movimiento de ventas para ' + MESES[int(vals['mes'])-1][1]+' del '+vals['anho']
                raise ValidationError(mensaje)
    
            lista_archivos = []
            cant_archivos = list(chunks(ventas, CANT_REGISTROS_HECHAUKA))
    
            for ii, ventas in enumerate(cant_archivos):
                # los datos como cantidad de registros y monto total se cargan despues de los detalles
                # quedan vacios temporalmente hasta calcular los datos
                texto = [[]]
                monto_total = 0
                for v in ventas:
                    monto_total += int(v[12])  # controlar que este sumando en la columna correcta
                    texto.append("\t".join([str(x) for x in v]))

                # Validaciones de los campos de la Companhia

                if usuario.company_id.vat:
                    ruc_company = usuario.company_id.vat.split('-')
                else:
                    raise UserError('La Compañía NO posee RUC, por favor verifique en detalles de Compañía')
                try:
                    if not ruc_company[0]:
                        mensaje = 'La Compañía NO posee RUC, por favor verifique en detalles de Compañía'
                        raise ValidationError(mensaje)

                    if not ruc_company[1]:
                        mensaje = 'La Compañía NO posee DV, por favor verifique en detalles de Compañía'
                        raise ValidationError(mensaje)
                except:
                    mensaje = 'La Compañia tiene el formato incorrecto de RUC, por favor verifique en detalles de Compañía'
                    raise ValidationError(mensaje)

                if not usuario.company_id.razon_social:
                    mensaje = 'No posee Razón Social, por favor verifique en detalles de Compañía'
                    raise ValidationError(mensaje)

                if not usuario.company_id.ruc_representante == '0':
                    ruc_rep_legal = usuario.company_id.ruc_representante.split('-')
                    if not ruc_rep_legal[0]:
                        mensaje = 'No posee RUC representante Legal, por favor verifique en detalles de Compañía'
                        raise ValidationError(mensaje)

                    if not ruc_rep_legal[1]:
                        mensaje = 'No posee DV representante legal, por favor verifique en detalles de Compañía'
                        raise ValidationError(mensaje)
                else:
                    ruc_rep_legal = ['0', '0']
    
                encabezado = "\t".join(['1',
                                        periodo,
                                        str(vals['tipo_reporte']),
                                        str('921'),
                                        str('221'),
                                        ruc_company[0],
                                        ruc_company[1],
                                        usuario.company_id.razon_social,
                                        ruc_rep_legal[0],  # RUC REPRESENTANTE LEGAL
                                        ruc_rep_legal[1],  # DV REPRESENTANTE LEGAL
                                        usuario.company_id.representante_legal if usuario.company_id.representante_legal else '0',
                                        str(len(ventas)),  # cantidad registros
                                        str(monto_total),  # monto total
                                        '2',  # VERSION DEL FORMULARIO
                                        ])
    
                texto[0] = encabezado
                contenido = ("\n".join(texto)).encode('utf-8')
    
                filename = 'ventas_' + str(nombre_mes) + '_' + vals['anho'] + '_' + str(ii + 1) + '.txt'
                datos = {
                    'archivo': base64.b64encode(contenido),
                    'name': vals['anho'] + vals['mes'],
                    'nombre': filename,
                }
                lista_archivos.append([0, False, datos])
            return lista_archivos

    def generar_informe_compras(self, doc):
        for rec in self:
            iva = self.get_default_iva()
            # LIBRO COMPRAS
            vals = doc
            periodo = vals['anho'] + vals['mes']
    
            nombre_mes = vals['mes']
            for m in MESES:
                if m[0] == vals['mes']:
                    nombre_mes = m[1]
                    break
    
            usuario = rec.env['res.users'].browse([rec._uid])

            if usuario.company_id.vat:
                ruc_company = usuario.company_id.vat.split('-')
            else:
                raise UserError('La Compañía NO posee RUC, por favor verifique en detalles de Compañía')
            try:
                if not ruc_company[0]:
                    mensaje = 'La Compañía NO posee RUC, por favor verifique en detalles de Compañía'
                    raise ValidationError(mensaje)

                if not ruc_company[1]:
                    mensaje = 'La Compañía NO posee DV, por favor verifique en detalles de Compañía'
                    raise ValidationError(mensaje)
            except:
                mensaje = 'La Compañia tiene el formato incorrecto de RUC, por favor verifique en detalles de Compañía'
                raise ValidationError(mensaje)

    
            if not usuario.company_id.razon_social:
                mensaje = 'No posee Razón Social, por favor verifique en detalles de Compañía'
                raise ValidationError(mensaje)

            if not usuario.company_id.ruc_representante == '0':
                ruc_rep_legal = usuario.company_id.ruc_representante.split('-')
                if not ruc_rep_legal[0]:
                    mensaje = 'No posee RUC representante Legal, por favor verifique en detalles de Compañía'
                    raise ValidationError(mensaje)

                if not ruc_rep_legal[1]:
                    mensaje = 'No posee DV representante legal, por favor verifique en detalles de Compañía'
                    raise ValidationError(mensaje)
            else:
                ruc_rep_legal = ['0', '0']

            QUERY = get_query_compras(mes=str(int(vals['mes'])), anho=vals['anho'], iva_compra_10=str(iva['iva_10_compra']), iva_compra_5=str(iva['iva_5_compra']), exenta_compra=str(iva['exento_compra']), iva_venta_10=str(iva['iva_10_venta']), iva_venta_5=str(iva['iva_5_venta']), exenta_venta=str(iva['exento_venta']), comp=self.env.company)
            rec._cr.execute(QUERY + ' SELECT * FROM T3 order by fecha, number')
            compras = rec._cr.fetchall()
            if not compras:
                mensaje = 'No posee ningun movimiento de compra para '+MESES[int(vals['mes'])-1][1]+' del '+vals['anho']
                raise ValidationError(mensaje)
    
            lista_archivos = []
            cant_archivos = list(chunks(compras, CANT_REGISTROS_HECHAUKA))
    
            for ii, compras in enumerate(cant_archivos):
                # los datos como cantidad de registros y monto total se cargan despues de los detalles
                # quedan vacios temporalmente hasta calcular los datos
                texto = []
                texto.append(u'')
                monto_total = 0
                # SACAR EL GUION Y EL DIGITO VERIFICADOR DEL RUC
                # VERIFICAR EL TIPO DE OPERACION
                for c in compras:
                    # compra tasa 10% + compra tasa 5% + exenta sin iva
                    monto_total += int(c[8]) + int(c[10]) + int(c[12])
                    texto.append("\t".join([str(x) for x in c]))
                # import pdb
                # pdb.set_trace()
                encabezado = "\t".join([
                    '1',
                    periodo,
                    str(vals['tipo_reporte']),
                    str('911'),
                    str('211'),
                    ruc_company[0],  # RUC DE AGENTE DE INFORMACION
                    ruc_company[1],  # DV DE AGENTE DE INFORMACION
                    usuario.company_id.razon_social,  # NOMBRE O DENOMINACION AGENTE DE INFORMACION
                    ruc_rep_legal[0] if usuario.company_id.ruc_representante else '0',  # RUC REPRESENTANTE LEGAL
                    ruc_rep_legal[1] if usuario.company_id.ruc_representante else '0',   # DV REPRESENTANTE LEGAL
                    usuario.company_id.representante_legal if usuario.company_id.representante_legal else '0',  # REPRESENTANTE LEGAL
                    str(len(compras)) if compras else '0',  # cantidad registros
                    str(monto_total) if monto_total else '0',  # monto total
                    'SI' if usuario.company_id.exportador else 'NO',  # EXPORTADOR
                    '2',
                ])
    
                texto[0] = encabezado
    
                contenido = ("\n".join(texto)).encode('utf-8')
    
                filename = 'compras_' + str(nombre_mes) + '_' + vals['anho'] + '_' + str(ii + 1) + '.txt'
    
                datos = {
                    'archivo': base64.b64encode(contenido),
                    'name': vals['anho'] + vals['mes'],
                    'nombre': filename,
                }
    
                lista_archivos.append([0, False, datos])
            return lista_archivos

    def report_hecha(self, vals=None):
        for rec in self:
            if rec.anho:
                doc = {}
                if rec.anho and rec.mes and rec.tipo_formulario and rec.tipo_reporte:
                    if len(rec.anho) < 4 or int(rec.anho) < 1900 or int(rec.anho) > 2100:
                        raise ValidationError('Año inválido')
    
                    if not rec.anho.isdigit():
                        raise ValidationError('El campo "año" debe ser un número entero')
    
                    if not rec._uid:
                        raise ValidationError('No se puede determinar la compañía')
    
                    doc.update({'name': rec.anho + rec.mes})
                    doc.update({'anho': rec.anho})
                    doc.update({'mes': rec.mes})
                    doc.update({'tipo_reporte': rec.tipo_reporte})
                    doc.update({'tipo_formulario': rec.tipo_formulario})
    
                    if rec.tipo_formulario == '211':
                        doc.update({'archivos': rec.generar_informe_compras(doc)})
    
                    elif rec.tipo_formulario == '221':
                        doc.update({'archivos': rec.generar_informe_ventas(doc)})
                    else:
                        raise ValidationError('Este tipo de formulario aún no ha sido implementado')
                else:
                    raise ValidationError('Complete correctamente todos los campos')
    
            else:
                return rec.browse(0)
    
            return super(Hechauka, rec).create(doc)

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

    # @api.multi
    # def create(self, vals=None):
    #     if 'anho' in vals:
    #         if vals['anho'] and vals['mes'] and vals['tipo_formulario'] and vals['tipo_reporte']:
    #             if len(vals['anho']) < 4 or int(vals['anho']) < 1900 or int(vals['anho']) > 2100:
    #                 raise ValidationError('Año inválido')
    #
    #             if not vals['anho'].isdigit():
    #                 raise ValidationError('El campo "año" debe ser un núnmero entero')
    #
    #             if not self._uid:
    #                 raise ValidationError('No se puede determinar la compañía')
    #
    #             vals.update({'name': vals['anho'] + vals['mes']})
    #
    #             if vals['tipo_formulario'] == '211':
    #                 vals.update({'archivos': self.generar_informe_compras(vals)})
    #
    #             elif vals['tipo_formulario'] == '221':
    #                 vals.update({'archivos': self.generar_informe_ventas(vals)})
    #             else:
    #                 raise ValidationError('Este tipo de formulario aún no ha sido implementado')
    #         else:
    #             raise ValidationError('Complete correctamente todos los campos')
    #
    #     else:
    #         return self.browse(self)
    #
    #     return super(Hechauka, self).create(vals)

    def _get_month_default():
        mes = datetime.datetime.now().month - 1
        mes = str(12 if mes == 0 else mes)
        return '0' + mes if len(mes) == 1 else mes

    _defaults = {
        'tipo_reporte': '1',
        'tipo_formulario': '211',
        'anho': str(datetime.datetime.now().year),
        'mes': str(_get_month_default()),

    }
