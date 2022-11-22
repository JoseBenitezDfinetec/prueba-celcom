from odoo import models, api, fields, _
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain
from odoo.exceptions import UserError


class ReportCelcomIva(models.AbstractModel):
    _name = "celcom.reporte.iva"
    _description = "Reporte IVA"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter': 'last_month'}
    filter_unfold_all = True

    @api.model
    def _get_options(self, previous_options=None):
        options = super(ReportCelcomIva, self)._get_options(previous_options=previous_options)
        # We do not want multi company for this report
        options.setdefault('date', {})
        options['date'].setdefault('date_to', fields.Date.context_today(self))
        return options

    def _get_report_name(self):
        return _("Reporte IVA")

    def _get_columns_name(self, options):
        columns = [{'name': _('Mes')}, {'name': _('Fecha'), 'class': 'date'},
                   {'name': _('Importe Gravado 5%'), 'class': 'number'},
                   {'name': _('Importe Gravado 10%'), 'class': 'number'},
                   {'name': _('Exentas'), 'class': 'number'}, {'name': _('IVA 5%'), 'class': 'number'},
                   {'name': _('IVA 10%'), 'class': 'number'}, {'name': _('Total'), 'class': 'number'}]
        return columns

    def _get_sum(self, results, lambda_filter):
        sum_gravado_5 = self.format_value(sum([r['monto_5'] for r in results if lambda_filter(r)]))
        sum_gravado_10 = self.format_value(sum([r['monto_10'] for r in results if lambda_filter(r)]))
        sum_exentas = self.format_value(sum([r['monto_exento'] for r in results if lambda_filter(r)]))
        sum_5 = self.format_value(sum([r['iva_5'] for r in results if lambda_filter(r)]))
        sum_10 = self.format_value(sum([r['iva_10'] for r in results if lambda_filter(r)]))
        sum_total = self.format_value(sum([r['total'] for r in results if lambda_filter(r)]))
        return [sum_gravado_5, sum_gravado_10, sum_exentas, sum_5, sum_10, sum_total]

    def _get_anho_line(self, options, current_anho, results, record):
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        columns = [{'name': n} for n in self._get_sum(results, lambda x: x['anho'] == current_anho)]
        columns.insert(0, {})
        return {
                'id': 'anho_%s' % current_anho,
                'name': convert_date('%s-01' % (current_anho), {'format': 'yyyy'}),
                'level': 1,
                'columns': columns,
                'unfoldable': True,
                'unfolded': self._need_to_unfold('anho_%s' % current_anho, options),
            }

    def _get_mes_line(self, options, current_anho, current_mes, results, record):
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        columns = [{'name': n} for n in self._get_sum(results, lambda x: x['mes'] == current_mes)]
        columns.insert(0, {})
        return {
                'id': 'mes_%s_%s' % (current_mes, current_anho),
                'name': convert_date('%s-%s-01' % (current_anho, current_mes), {'format': 'MMM yyyy'}),
                'level': 1,
                'columns': columns,
                'unfoldable': True,
                'unfolded': self._need_to_unfold('mes_%s_%s' % (current_mes, current_anho), options),
                'parent_id': 'anho_%s' % current_anho,
            }

    def _get_tipo_line(self, options, current_anho, current_mes, current_tipo, results, record):
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        columns = [{'name': n} for n in self._get_sum(results, lambda x: x['tipo'] == current_tipo and x['mes'] == current_mes and x['anho'] == current_anho)]
        columns.insert(0, {})
        return {
                'id': 'tipo_%s_%s_%s' % (current_tipo, current_mes, current_anho),
                'name': current_tipo == 'out_invoice' and 'Facturas Venta' or current_tipo == 'in_invoice' and 'Facturas Compra',
                'level': 2,
                'columns': columns,
                'unfoldable': True,
                'unfolded': self._need_to_unfold('tipo_%s_%s_%s' % (current_tipo, current_mes, current_anho), options),
                'parent_id': 'mes_%s_%s' % (current_mes, current_anho),
            }

    def _get_line_total_per_month(self, options, current_anho, results):
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        lines = []
        columns = [{'name': n} for n in self._get_sum(results, lambda x: x['anho'] == current_anho)]
        columns.insert(0, {})
        lines.append({
                    'id': 'Total_all_%s' % (current_anho),
                    'name': _('Total'),
                    'class': 'total',
                    'level': 1,
                    'columns': columns
        })
        lines.append({
                    'id': 'blank_line_after_total_%s' % (current_anho),
                    'name': '',
                    'columns': [{'name': ''} for n in ['sum_gravado_5', 'sum_gravado_10', 'sum_exentas', 'sum_5', 'sum_10']]
        })
        return lines

    @api.model
    def _need_to_unfold(self, line_id, options):
        return line_id in options.get('unfolded_lines') or options.get('unfold_all')

    @api.model
    def _get_lines(self, options, line_id=None):

        # 1.Build SQL query
        lines = []
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        iva = self.get_default_iva()
        iva_ventas_10 = str(iva['iva_10_venta'])
        iva_ventas_5 = str(iva['iva_5_venta'])
        exentas_ventas = str(iva['exento_venta'])
        iva_compra_10 = str(iva['iva_10_compra'])
        iva_compra_5 = str(iva['iva_5_compra'])
        exenta_compra = str(iva['exento_compra'])
        select = ("""
                -- OBTIENE EL MONTO DEL IVA 10 E IVA 5 DE LOS MOVE.LINE DE TAXES
                WITH IVA AS (SELECT
                CASE WHEN aml.tax_line_id = {0} OR aml.tax_line_id = {3} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS iva_10,
                CASE WHEN aml.tax_line_id = {1} OR aml.tax_line_id = {4} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS iva_5, 
                aml.id AS id_linea_iva,
                acc_move.numeracion as nombre_factura_iva,
                acc_move.date as fecha_iva,
                to_char(acc_move.date, 'YYYY') as anho_iva,
                to_char(acc_move.date, 'MM') as mes_iva,
                to_char(acc_move.date, 'YYYY') as yyyy_iva,
                to_char(acc_move.date, 'MM') as month_iva,
                acc_move.move_type as tipo_iva,
                aml.*
                FROM account_move_line aml
                JOIN account_move acc_move ON acc_move.id = aml.move_id
                WHERE (aml.date <= %s) AND (aml.date >= %s)
                AND aml.tax_line_id IS NOT NULL and state = 'posted'
                AND (acc_move.move_type = 'out_invoice' OR acc_move.move_type = 'in_invoice')),
                -- OBTIENE LOS MOVE.LINE QUE TIENEN ALGUN TIPO DE IVA
                MONTOS AS (SELECT 
                CASE WHEN tax.id = {0} OR tax.id = {3} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS monto_10,
                CASE WHEN tax.id = {1} OR tax.id = {4} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS monto_5,
                CASE WHEN tax.id = {2} OR tax.id = {5} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS monto_exento,
                aml.id AS id_linea_monto,
                acc_move.numeracion as nombre_factura_monto,
                acc_move.date as fecha_monto,
                to_char(acc_move.date, 'YYYY') as anho_monto,
                to_char(acc_move.date, 'MM') as mes_monto,
                to_char(acc_move.date, 'YYYY') as yyyy_monto,
                to_char(acc_move.date, 'MM') as month_monto,
                aml.id AS id_linea,
                acc_move.move_type as tipo_monto,
                aml.*, 
                tax.* 
                FROM account_move_line aml
                JOIN account_move acc_move ON acc_move.id = aml.move_id
                JOIN account_move_line_account_tax_rel line_tax ON aml.id = line_tax.account_move_line_id
                JOIN account_tax tax ON line_tax.account_tax_id = tax.id
                WHERE (aml.date <= %s) AND (aml.date >= %s)
AND (acc_move.move_type = 'out_invoice' OR acc_move.move_type = 'in_invoice') and state = 'posted'
                ORDER BY acc_move),
                --JOIN DE LOS PRODUCTOS CON IVA Y LAS LINEAS DE IVA
                IVA_MONTOS AS (SELECT 
                CASE WHEN IVA.move_id IS NULL THEN montos.move_id ELSE iva.move_id END AS factura_id,
                CASE WHEN iva.id_linea_iva IS NULL THEN montos.id_linea_monto ELSE iva.id_linea_iva END AS id_linea_suma,
                CASE WHEN IVA.fecha_iva IS NULL THEN montos.fecha_monto ELSE iva.fecha_iva END AS fecha,
                CASE WHEN IVA.nombre_factura_iva IS NULL THEN montos.nombre_factura_monto ELSE iva.nombre_factura_iva END AS nombre_factura,
                CASE WHEN IVA.anho_iva IS NULL THEN montos.anho_monto ELSE iva.anho_iva END AS anho,
                CASE WHEN IVA.mes_iva IS NULL THEN montos.mes_monto ELSE iva.mes_iva END AS mes,
                CASE WHEN IVA.yyyy_iva IS NULL THEN montos.yyyy_monto ELSE iva.yyyy_iva END AS yyyy,              
                CASE WHEN IVA.month_iva IS NULL THEN montos.month_monto ELSE iva.month_iva END AS month,                
                CASE WHEN IVA.tipo_iva IS NULL THEN montos.tipo_monto ELSE iva.tipo_iva END AS tipo,                
                * FROM IVA 
                FULL JOIN MONTOS ON IVA.id = montos.id_linea),
                --SUMA DE LOS MOVE.LINE QUE SON DE LAS MISMAS FACTURAS
                IVA_SUMAS AS( SELECT 
                    factura_id,
                    nombre_factura,
                    min(id_linea_suma) as id_linea,
                    min(fecha) as fecha,
                    tipo,
                    anho,
                    mes,
                    yyyy,
                    month,
                    round(sum(monto_10))::int AS monto_10,
                    CASE WHEN SUM(iva_10)::int IS NULL THEN 0 ELSE round(sum(iva_10))::int END AS iva_10,
                    round(sum(monto_5))::int AS monto_5,
                    CASE WHEN SUM(iva_5) IS NULL THEN 0 ELSE round(sum(iva_5))::int END AS iva_5,
                    round(sum(monto_exento))::int AS monto_exento
                from IVA_MONTOS
                GROUP BY factura_id, nombre_factura, anho, mes, yyyy, month, tipo
                ORDER BY mes, tipo, fecha, factura_id),
                final as ( select
                    iva_sumas.*,
                    monto_10+iva_10+monto_5+iva_5+monto_exento as total
                    from iva_sumas
                ) select * from final
        """).format(iva_ventas_10, iva_ventas_5, exentas_ventas, iva_compra_10, iva_compra_5, exenta_compra)
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        line_model = None
        if line_id:
            split_line_id = line_id.split('_')
            line_model = split_line_id[0]
            model_id = split_line_id[1]
        #     where_clause += line_model == 'account' and ' AND account_id = %s AND j.id = %s' or  ' AND j.id = %s'
            where_params += [str(model_id)]
            if line_model == 'account':
                where_params += [str(split_line_id[2])] # We append the id of the parent journal in case of an account line


        # 2.Fetch data from DB
        # select = select % (where_clause, where_clause)
        self.env.cr.execute(select, [options['date']['date_to'], options['date']['date_from']]*2)
        results = self.env.cr.dictfetchall()
        if not results:
            return lines

        # 3.Build report lines
        current_mes = None
        previous_mes = None
        current_tipo = None
        current_anho = results[0]['anho']
        for values in results:
            if values['anho'] != current_anho:
                current_anho = values['anho']
                lines.append(self._get_anho_line(options, current_anho, results, values))

            if self._need_to_unfold('anho_%s' % (current_anho,), options) and values['mes'] != current_mes:
                current_mes = values['mes']
                lines.append(self._get_mes_line(options, current_anho, current_mes, results, values))

            if self._need_to_unfold('mes_%s_%s' % (current_mes, current_anho), options) and (previous_mes != current_mes or values['tipo'] != current_tipo):
                previous_mes = current_mes
                current_tipo = values['tipo']
                lines.append(self._get_tipo_line(options, current_anho, current_mes, current_tipo, results, values))

            # If we need to unfold the line
            if self._need_to_unfold('tipo_%s_%s_%s' % (current_tipo, current_mes, current_anho), options):
                vals = {
                    'id': values['id_linea'],
                    'name': values['nombre_factura'],
                    'caret_options': 'account.move',
                    'level': 5,
                    'parent_id': "tipo_%s_%s_%s" % (values['tipo'], values['mes'], values['anho']),
                    'columns': [{'name': n} for n in [convert_date(values['fecha'], {'format': 'dd/MM/yyyy'}), self.format_value(values['monto_5']), self.format_value(values['monto_10']), self.format_value(values['monto_exento']), self.format_value(values['iva_5']), self.format_value(values['iva_10']), self.format_value(values['total'])]],
                }
                lines.append(vals)

        # Append detail per month section
        if not line_id:
            lines.extend(self._get_line_total_per_month(options, values['anho'], results))
        return lines

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