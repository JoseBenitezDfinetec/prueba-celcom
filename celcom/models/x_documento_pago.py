from odoo import models, fields, api
import datetime


class DocumentoPagoInherit(models.Model):
    _inherit = "x_documento_pago"

    """
        Las modificaciones del modelo x_documento_pago se deben realizar en Odoo Studio porque da error al 
        intentar tomar de aca, este archivo no se encuentra incluido en el __init__.py
    """

    move_ids = fields.Many2many('account.move', 'documento_move_rel', 'documento_id', 'move_id',
                                string='Asientos relacionados')
