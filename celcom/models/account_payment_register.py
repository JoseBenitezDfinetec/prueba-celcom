from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime


class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = "account.payment.register"

    talonario = fields.Many2one('x_talonario_recibo', string="Talonario de Recibo", readonly=False)
    nro_talonario = fields.Char("Número de Recibo", readonly=False)
    documento_de_pago = fields.Boolean('Documentos de Pago')
    doc_pago = fields.Many2one('x_documento_pago', string='Documento de Pago')
    vencimiento_doc = fields.Date(string='Vencimiento', related='doc_pago.x_studio_vencimiento', readonly=True)
    monto_doc = fields.Float(string='Monto del documento', related='doc_pago.x_studio_monto', readonly=True)
    referencia_proveedor = fields.Char("Referencia de Proveedor")
    ref_cliente = fields.Char("Memo")
    docs_pago = fields.Many2many('x_documento_pago', 'pago_ref_doc_pago_rel', 'account_payment_register_id', 'x_documento_pago_id',
                                 string="Documentos de Pago Vinculados",
                                 domain=[('x_studio_estado', 'not in', ['cobrado', 'cancelado'])])

    @api.onchange('talonario')
    def _onchange_talonario(self):
        if self.talonario:
            self.nro_talonario = self.talonario.x_studio_nmero_actual

    @api.onchange('docs_pago')
    def _onchange_docs_pago(self):
        if self.docs_pago:
            monto = 0
            for doc in self.docs_pago:
                monto += doc.x_studio_monto
            self.amount = monto

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date')
    def _compute_amount(self):
        for wizard in self:
            super(AccountPaymentRegisterInherit, self)._compute_amount()
            batches = wizard._get_batches()
            lineas_factura = batches[0]['lines']
            move = lineas_factura.move_id
            lineas_factura = move.line_ids
            lineas_vencidas = [aml for aml in list(lineas_factura) if aml.date_maturity and (aml.date_maturity - datetime.date.today()).days < 1]
            monto = 0
            for aml in lineas_vencidas:
                monto += abs(aml.amount_residual)
            if monto == 0:
                lineas_no_vencidas = [aml for aml in list(lineas_factura) if aml.date_maturity and (aml.date_maturity - datetime.date.today()).days >= 1 and abs(aml.amount_residual) > 0]
                if len(lineas_no_vencidas) > 0:
                    lineas_no_vencidas = sorted(lineas_no_vencidas, key=lambda x: x.date_maturity)
                    monto = abs(lineas_no_vencidas[0].amount_residual)
                else:
                    monto = 0
            self.amount = monto

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegisterInherit, self)._create_payment_vals_from_wizard()
        if self.talonario.id:
            payment_vals['x_studio_talonario_recibo'] = self.talonario.id
            payment_vals['x_studio_nro_talonario'] = self.nro_talonario
            payment_vals['x_studio_nro_recibo'] = self.nro_talonario
        if self.referencia_proveedor:
            payment_vals['referencia_proveedor'] = self.referencia_proveedor
        if self.ref_cliente:
            payment_vals['ref_cliente'] = self.ref_cliente
        if self.documento_de_pago:
            payment_vals['x_studio_documento_de_pago'] = self.documento_de_pago
            if self.docs_pago:
                payment_vals['docs_pago'] = self.docs_pago
            if self.doc_pago:
                payment_vals['x_studio_doc_pago'] = self.doc_pago.id
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = super(AccountPaymentRegisterInherit, self)._create_payment_vals_from_batch(batch_result)
        if self.talonario.id:
            batch_values['x_studio_talonario_recibo'] = self.talonario.id
            batch_values['x_studio_nro_talonario'] = self.nro_talonario
            batch_values['x_studio_nro_recibo'] = self.nro_talonario
        if self.referencia_proveedor:
            batch_values['referencia_proveedor'] = self.referencia_proveedor
        if self.ref_cliente:
            batch_values['ref_cliente'] = self.ref_cliente
        if self.documento_de_pago:
            batch_values['x_studio_documento_de_pago'] = self.documento_de_pago
            batch_values['x_studio_doc_pago'] = self.doc_pago.id
        return batch_values


class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    referencia_proveedor = fields.Char("Referencia de Proveedor")
    ref_cliente = fields.Char("Memo")
    doc_pago_check = fields.Boolean('Documentos de Pago', default=False)
    docs_pago = fields.Many2many('x_documento_pago', 'pago_doc_pago_rel', 'account_payment_id', 'x_documento_pago_id',
                                 string="Documentos de Pago Vinculados",
                                 domain=[('x_studio_estado', 'not in', ['cobrado', 'cancelado'])])

    @api.onchange('docs_pago')
    def _onchange_docs_pago(self):
        if self.docs_pago:
            monto = 0
            for doc in self.docs_pago:
                monto += doc.x_studio_monto
            self.amount = monto

    @api.onchange('partner_type', 'ref_cliente', 'referencia_proveedor')
    def _compute_ref(self):
        if self.partner_type == 'customer':
            self.referencia_proveedor = None
            self.ref = None
            if self.ref_cliente:
                self.ref = self.ref_cliente
        elif self.partner_type == 'supplier':
            self.ref_cliente = None
            self.ref = None
            if self.referencia_proveedor:
                self.ref = self.referencia_proveedor

    @api.model_create_multi
    def create(self, vals):
        payment = super(AccountPaymentInherit, self).create(vals)
        move = payment.move_id
        if move.payment_id and move.payment_id.partner_type == 'supplier' and move.payment_id.payment_type == 'outbound' and move.journal_id.type in ('cash', 'bank'):
            move.write({'pago_proveedor': True})
        return payment

    def action_post(self):
        if self.docs_pago:
            for doc in self.docs_pago:
                if not doc.x_studio_moneda.id == self.currency_id.id:
                    raise UserError('La moneda del pago es distinta a la moneda del documento ' + doc.x_name)
        super(AccountPaymentInherit, self).action_post()


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    refund_method = fields.Selection(selection=[
            ('refund', 'Partial Refund'),
            ('cancel', 'Full Refund'),
            ('modify', 'Full refund and new draft invoice')
        ], string='Credit Method', required=True, default='refund',
        help='Choose how you want to credit this invoice. You cannot "modify" nor "cancel" if the invoice is already reconciled.')
