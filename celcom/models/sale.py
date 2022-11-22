from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        if self.partner_id and (not self.partner_id.nro_documento or not self.partner_id.street):
            raise ValidationError("El cliente debe tener RUC y dirección")
        sale = super(SaleOrder, self).action_confirm()
