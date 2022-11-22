from odoo import models, fields, api
from odoo.exceptions import UserError


class Company(models.Model):
    _inherit = "res.company"

    def get_ruc_sin_dv(self):
        try:
            return self.vat[:-2]
        except:
            raise UserError('Ingrese el RUC de la compañía actual')


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    tipo_documento = fields.Selection([
        ('11', 'RUC'),
        ('12', 'CÉDULA DE IDENTIDAD'),
        ('13', 'PASAPORTE'),
        ('14', 'CÉDULA EXTRANJERA'),
        ('15', 'SIN NOMBRE'),
        ('16', 'DIPLOMÁTICO'),
        ('17', 'IDENTIFICACIÓN TRIBUTARIA')
    ], string='Tipo de Identificación', default='11', required=True)
    nro_documento = fields.Char(string='Número de Documento')

    @api.onchange('nro_documento', 'tipo_documento')
    def _onchange_nro_documento(self):
        if self.tipo_documento == '12':
            self.vat = '44444401-7'
        elif self.tipo_documento == '11':
            self.vat = self.nro_documento
        elif self.tipo_documento == '15':
            self.nro_documento = '44444401-7'
            self.vat = '44444401-7'
        else:
            self.vat = '44444401-7'

    def get_ruc_sin_dv(self):
        try:
            if self.tipo_documento == '11':
                return self.vat[:-2]
        except:
            raise UserError('El contacto "', self.name, '" no tiene RUC asignado')

    # todo: Ver la forma que se asigne el nro_documento al vat del contacto sin que se ejecute el
    #        validador de ruc en write de talonario_py (Este se ejecuta por defecto si no es de tipo CI)

    def validar_nro_doc(self, nro_doc, tipo_documento):
        if tipo_documento == '11':
            try:
                ruc = nro_doc.split('-')
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
        elif tipo_documento == '12':
            if not nro_doc.isnumeric():
                raise UserError('Solo introduzca números en el campo CI.')