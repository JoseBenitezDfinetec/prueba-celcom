from odoo import models, fields, api


class Factura(models.Model):
    _inherit = "account.move"

    # numeracion = fields.Char("Numeración", size=15)
    # timbrado = fields.Char("Timbrado", size=20, related="x_studio_field_QV8yr.x_studio_timbrado.x_name", store=True)
