from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    es_credito = fields.Boolean(string='Credito', default=False, help="Chequee si el termino de pago es Credito.")
    cuotas = fields.Integer(string="Cantidad de Cuotas del Termino de Pago", default=0)

    @api.onchange('es_credito')
    def onchange_credito(self):
        if not self.es_credito:
            self.cuotas = 0
