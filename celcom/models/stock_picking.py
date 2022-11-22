from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PickingInherit(models.Model):
    _inherit = "stock.picking"

    talonario = fields.Many2one('x_talonario', string="Talonario del Documento")
    timbrado = fields.Many2one('x_timbrado2')
    numeracion = fields.Char('Numeracion del Documento')
    es_nota_remision = fields.Boolean('Nota de Remision')

    @api.onchange('talonario')
    def _onchange_talonario(self):
        self.numeracion = self.talonario.x_studio_numero_actual
        self.timbrado = self.talonario.x_studio_timbrado

    def button_validate(self):
        ret = super(PickingInherit, self).button_validate()
        if self.talonario:
            notas_remision = self.env['stock.picking'].search([('id', '!=', self.id), ('talonario', '=', self.talonario.id), ('numeracion', '=', self.numeracion), ('state', '=', 'done')])
            if notas_remision:
                raise UserError('Ya existe una Nota de Remision con ese numero')
            if self.talonario.x_studio_numero_actual == self.numeracion:
                self.talonario.x_studio_numero_actual = str(int(self.talonario.x_studio_numero_actual) + 1)
        return ret