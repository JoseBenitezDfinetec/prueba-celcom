import re
import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from .number_to_letter import to_word
from odoo import models, fields, api
from odoo.exceptions import UserError


class InvoiceInherit(models.Model):
    _inherit = "account.move"

    monto_texto = fields.Char("Monto en Texto", compute="_compute_monto_texto")
    timbrado_proveedor = fields.Char("Timbrado")
    vencimiento_timbrado = fields.Date("Vencimiento Timbrado")
    pago_proveedor = fields.Boolean("Move de pago de proveedor", default=False)
    diario_doc_pago = fields.Boolean(related='journal_id.doc_pago')
    docs_pago = fields.Many2many('x_documento_pago', 'documento_move_rel', 'move_id', 'documento_id',
                                 string='Documentos de Pagos Relacionados',
                                 domain=[('x_studio_estado', 'not in', ['cobrado', 'cancelado'])])

    @api.depends('amount_total')
    def _compute_monto_texto(self):
        try:
            for move in self:
                move.monto_texto = ""
                if move.amount_total:
                    if move.amount_total > 0:
                        move.monto_texto = to_word(float(move.amount_total), move.currency_id.name)
        except Exception as e:
            print(e)
            pass

    def _post(self, soft=True):
        if self.move_type == 'in_invoice':
            timbrado = self.timbrado_proveedor
            nro_doc = self.x_studio_numero_de_factura

            facturas_repetidas = self.env['account.move'].search([('timbrado_proveedor','=',timbrado),('x_studio_numero_de_factura','=',nro_doc),('state','=','posted'),('partner_id','=',self.partner_id.id),('tipo_comprobante_compra','=',self.tipo_comprobante_compra),('tipo_comprobante_venta','=',self.tipo_comprobante_venta),('tipo_comprobante_compra_nota','=',self.tipo_comprobante_compra_nota),('tipo_comprobante_venta_nota','=',self.tipo_comprobante_venta_nota)])
            if facturas_repetidas:
                raise UserError("Ya existe una factura con el mismo numero y timbrado.")

        return super(InvoiceInherit, self)._post(soft)

    @api.depends('posted_before', 'state', 'journal_id', 'date', 'pago_proveedor')
    def _compute_name(self):
        pagos_a_proveedores = self.filtered(
            lambda m: m.payment_id and m.payment_id.partner_type == 'supplier' and m.payment_id.state == 'posted' and m.payment_id.payment_type == 'outbound' and m.journal_id.type in ('cash', 'bank'))
        otros = self.filtered(
            lambda m: not(m.payment_id and m.payment_id.partner_type == 'supplier' and m.payment_id.state == 'posted' and m.payment_id.payment_type == 'outbound' and m.journal_id.type in ('cash', 'bank')))

        def journal_key(move):
            return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

        def date_key(move):
            return (move.date.year, move.date.month)

        grouped = defaultdict(  # key: journal_id, move_type
            lambda: defaultdict(  # key: first adjacent (date.year, date.month)
                lambda: {
                    'records': self.env['account.move'],
                    'format': False,
                    'format_values': False,
                    'reset': False
                }
            )
        )
        self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
        highest_name = self[0]._get_last_sequence() if self else False

        # Group the moves by journal and month
        for move in self:
            if not highest_name and move == self[0] and not move.posted_before:
                # In the form view, we need to compute a default sequence so that the user can edit
                # it. We only check the first move as an approximation (enough for new in form view)
                pass
            elif (move.name and move.name != '/') or move.state != 'posted':
                try:
                    if not move.posted_before:
                        move._constrains_date_sequence()
                    # Has already a name or is not posted, we don't add to a batch
                    continue
                except ValidationError:
                    # Has never been posted and the name doesn't match the date: recompute it
                    pass
            group = grouped[journal_key(move)][date_key(move)]
            if not group['records']:
                # Compute all the values needed to sequence this whole group
                move._set_next_sequence()
                group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
                group['reset'] = move._deduce_sequence_number_reset(move.name)
            group['records'] += move

        # Fusion the groups depending on the sequence reset and the format used because `seq` is
        # the same counter for multiple groups that might be spread in multiple months.
        final_batches = []
        for journal_group in grouped.values():
            journal_group_changed = True
            for date_group in journal_group.values():
                if (
                    journal_group_changed
                    or final_batches[-1]['format'] != date_group['format']
                    or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
                ):
                    final_batches += [date_group]
                    journal_group_changed = False
                elif date_group['reset'] == 'never':
                    final_batches[-1]['records'] += date_group['records']
                elif (
                    date_group['reset'] == 'year'
                    and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
                ):
                    final_batches[-1]['records'] += date_group['records']
                else:
                    final_batches += [date_group]

        # Give the name based on previously computed values
        for batch in final_batches:
            for move in batch['records']:
                move.name = batch['format'].format(**batch['format_values'])
                batch['format_values']['seq'] += 1
            batch['records']._compute_split_sequence()

        self.filtered(lambda m: not m.name).name = '/'

        # el move corresponde a un pago entonces tiene payment_id
        # para move con diarios de tipo 'bank' o de tipo 'cash'
        # el pago tiene que ser de tipo 'outbound'
        if pagos_a_proveedores:
            for p in pagos_a_proveedores:
                hoy = datetime.date.today()
                move_pagos = self.env['account.move'].search(
                    [('id','!=',p.id),('date', '<', (hoy + relativedelta(months=1)).strftime('%Y-%m-01')),
                     ('date', '>=', hoy.strftime('%Y-%m-01')),('payment_id','!=',False)])
                cant = len(move_pagos.filtered(lambda
                                                   m: p.id != m.id and m.payment_id.payment_type == 'outbound' and m.payment_id.partner_type == 'supplier' and m.payment_id.state == 'posted' and m.journal_id.type in (
                'cash', 'bank')))
                p.name = 'OP-%04d-%02d-%04d' % (hoy.year, hoy.month, cant+1)

    def _get_last_sequence_domain(self, relaxed=False):
        self.ensure_one()
        if not self.date or not self.journal_id:
            return "WHERE FALSE", {}
        where_string = "WHERE journal_id = %(journal_id)s AND name != '/'"
        param = {'journal_id': self.journal_id.id}
        if self.pago_proveedor:
            where_string += " AND pago_proveedor = true"
        else:
            where_string += " AND pago_proveedor = false"

        if not relaxed:
            if self.pago_proveedor:
                domain = [('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', False)),('pago_proveedor','=',True)]
            else:
                domain = [('journal_id', '=', self.journal_id.id), ('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', False)),('pago_proveedor','=',False)]
            if self.journal_id.refund_sequence:
                refund_types = ('out_refund', 'in_refund')
                domain += [('move_type', 'in' if self.move_type in refund_types else 'not in', refund_types)]
            reference_move_name = self.search(domain + [('date', '<=', self.date)], order='date desc', limit=1).name
            if not reference_move_name:
                reference_move_name = self.search(domain, order='date asc', limit=1).name
            sequence_number_reset = self._deduce_sequence_number_reset(reference_move_name)
            if sequence_number_reset == 'year':
                where_string += " AND date_trunc('year', date::timestamp without time zone) = date_trunc('year', %(date)s) "
                param['date'] = self.date
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_monthly_regex.split('(?P<seq>')[0]) + '$'
            elif sequence_number_reset == 'month':
                where_string += " AND date_trunc('month', date::timestamp without time zone) = date_trunc('month', %(date)s) "
                param['date'] = self.date
            else:
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_yearly_regex.split('(?P<seq>')[0]) + '$'

            if param.get('anti_regex') and not self.journal_id.sequence_override_regex:
                where_string += " AND sequence_prefix !~ %(anti_regex)s "

        if self.journal_id.refund_sequence:
            if self.move_type in ('out_refund', 'in_refund'):
                where_string += " AND move_type IN ('out_refund', 'in_refund') "
            else:
                where_string += " AND move_type NOT IN ('out_refund', 'in_refund') "

        return where_string, param
