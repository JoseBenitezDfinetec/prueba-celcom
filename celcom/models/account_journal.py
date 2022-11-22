from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    doc_pago = fields.Boolean('Diario de Documento de Pagos')
