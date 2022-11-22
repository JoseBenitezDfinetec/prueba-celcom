
"""
	EN ODOO 14 EN VEZ DE USAR account.invoice.tax USAN EL MODELO account.move.line DE LOS
	TAXES QUE TENGAN NOMBRE DE IMPUESTO Y tax_line_id
"""


def get_query_ventas(mes, anho, iva_venta_10, iva_venta_5, exenta_venta, iva_compra_10, iva_compra_5, exenta_compra):
	return ('''-- OBTIENE EL MONTO DEL IVA 10% E IVA 5% DE LOS MOVE.LINE DE TAXES
WITH IVA AS (SELECT
CASE WHEN aml.tax_line_id = {2} OR aml.tax_line_id = {5} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS iva_10,
CASE WHEN aml.tax_line_id = {3} OR aml.tax_line_id = {6} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS iva_5, 
aml.id AS id_linea_iva,
aml.*
FROM account_move_line aml
JOIN account_move acc_move ON acc_move.id = aml.move_id
WHERE aml.tax_line_id IS NOT NULL 
AND (acc_move.move_type = 'out_invoice' OR acc_move.move_type = 'in_refund') 
AND extract(month from acc_move.invoice_date)={0}
AND extract(year from acc_move.invoice_date)={1}),


-- OBTIENE LOS MOVE.LINE QUE TIENEN ALGUN TIPO DE IVA
MONTOS AS (SELECT 
CASE WHEN tax.id = {2} OR tax.id = {5} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN -aml.debit ELSE 0 END ELSE 0 END AS monto_10,
CASE WHEN tax.id = {3} OR tax.id = {6} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN -aml.debit ELSE 0 END ELSE 0 END AS monto_5,
CASE WHEN tax.id = {4} OR tax.id = {7} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN -aml.debit ELSE 0 END ELSE 0 END AS monto_exento,
aml.id AS id_linea,
aml.*, 
tax.* 
FROM account_move_line aml
JOIN account_move acc_move ON acc_move.id = aml.move_id
JOIN account_move_line_account_tax_rel line_tax ON aml.id = line_tax.account_move_line_id
JOIN account_tax tax ON line_tax.account_tax_id = tax.id
WHERE (acc_move.move_type = 'out_invoice' OR acc_move.move_type = 'in_refund')
AND extract(month from acc_move.invoice_date)={0}
AND extract(year from acc_move.invoice_date)={1}
ORDER BY acc_move),

--JOIN DE LOS PRODUCTOS CON IVA Y LAS LINEAS DE IVA
IVA_MONTOS AS (SELECT 
CASE WHEN IVA.move_id IS NULL THEN montos.move_id ELSE iva.move_id END AS factura_id,
* FROM IVA 
FULL JOIN MONTOS ON IVA.id = montos.id_linea),

--SUMA DE LOS MOVE.LINE QUE SON DE LAS MISMAS FACTURAS
IVA_SUMAS AS( SELECT 
	factura_id, 
	round(sum(monto_10))::int AS monto_10,
	round(sum(iva_10))::int AS iva_10,
	round(sum(monto_5))::int AS monto_5,
	round(sum(iva_5))::int AS iva_5,
	round(sum(monto_exento))::int AS monto_exento
from IVA_MONTOS 
GROUP BY factura_id
ORDER BY factura_id),

-- OBTIENE EL CLIENTE
CLIENTE AS( 
	SELECT
		partner.id,
		partner.ruc,
		partner.dv,
		partner.name,
		partner.is_company,
		partner.type,
		parent.id AS parent_id,
		parent.ruc AS parent_ruc,
		parent.dv AS parent_dv,
		parent.name AS parent_name
	FROM res_partner AS partner
	LEFT JOIN res_partner AS parent ON partner.id = parent.id
), 
RUC_GENERICO AS (SELECT
	min(invoice.id) AS factura_id,
	round(sum(iva_sumas.monto_10))::int AS monto_10,
	round(sum(iva_sumas.iva_10))::int AS iva_10,
	round(sum(iva_sumas.monto_5))::int AS monto_5,
	round(sum(iva_sumas.iva_5))::int AS iva_5,
	round(sum(iva_sumas.monto_exento))::int AS monto_exento
FROM account_move invoice
JOIN IVA_SUMAS ON IVA_SUMAS.factura_id = invoice.id
JOIN CLIENTE AS partner ON partner.id = invoice.partner_id
WHERE invoice.state = 'posted' 
AND ((invoice.move_type = 'in_refund' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401')) 
OR invoice.move_type = 'out_invoice' 
AND ((partner.ruc IS NULL AND partner.parent_ruc IS NULL) OR partner.ruc = '44444401' OR partner.ruc = '66666601' OR partner.ruc = '77777701' OR partner.ruc = '88888801' OR partner.parent_ruc IS NULL OR partner.parent_ruc = '44444401' OR partner.parent_ruc = '66666601' OR partner.parent_ruc = '77777701' OR partner.parent_ruc = '88888801' OR invoice.tipo_venta = '12')
OR invoice.tipo_cliente IN ('2','3','4'))
AND extract(month FROM invoice.invoice_date)={0}
AND extract(year FROM invoice.invoice_date)={1}
GROUP BY invoice.tipo_cliente
),
IVA_SUMAS_2 AS( SELECT 
	factura_id, 
	partner.ruc,
	partner.parent_ruc,
	monto_10,
	iva_10,
	monto_5,
	iva_5,
	monto_exento
FROM IVA_SUMAS AS iva
JOIN account_move AS invoice ON invoice.id=iva.factura_id
JOIN CLIENTE AS partner ON partner.id = invoice.partner_id
WHERE invoice.state = 'posted' 
AND NOT((invoice.move_type = 'in_refund' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401')) OR invoice.move_type = 'out_invoice' AND (partner.ruc = '44444401' OR partner.ruc = '66666601' OR partner.ruc = '77777701' OR partner.ruc = '88888801' OR partner.parent_ruc = '44444401' OR partner.parent_ruc = '66666601' OR partner.parent_ruc = '77777701' OR partner.parent_ruc = '88888801' OR invoice.tipo_venta = '12') OR invoice.tipo_cliente IN ('2','3','4'))
),

IVA_SUMAS_3 AS ( SELECT
	'2'::text AS tipo,
	CASE WHEN invoice.tipo_venta = '12' THEN '66666601' WHEN invoice.tipo_cliente = '3' THEN '77777701' WHEN invoice.tipo_cliente = '4' THEN '88888801' WHEN partner.ruc IS NULL AND partner.parent_ruc IS NULL THEN '44444401' WHEN partner.is_company THEN partner.ruc ELSE partner.parent_ruc END AS ruc,
	CASE WHEN invoice.tipo_venta = '12' THEN '6' WHEN invoice.tipo_cliente = '3' THEN '0' WHEN invoice.tipo_cliente = '4' THEN '5' WHEN partner.ruc IS NULL AND partner.parent_ruc IS NULL THEN '0' WHEN partner.is_company THEN partner.dv ELSE partner.parent_dv END AS dv,
	CASE WHEN invoice.tipo_venta = '12' THEN 'Clientes de Exportación' WHEN invoice.tipo_cliente = '4' THEN 'Clientes del Exterior' WHEN invoice.tipo_cliente = '3' THEN 'Ventas a Agentes Diplomáticos' WHEN partner.parent_ruc = '44444401' OR partner.ruc = '44444401' OR (partner.ruc IS NULL AND partner.parent_ruc IS NULL) THEN 'Importes consolidados' WHEN partner.is_company THEN partner.name ELSE partner.parent_name END AS name,
	CASE WHEN partner.parent_ruc = '44444401' AND NOT invoice.tipo_cliente = '4' AND NOT invoice.tipo_cliente = '3' AND NOT invoice.tipo_venta = '12' THEN '0' ELSE CASE WHEN invoice.move_type = 'in_refund' THEN 3::text ELSE invoice.tipo_venta END END AS tipo_documento,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN partner.parent_ruc = '44444401' AND NOT invoice.tipo_cliente = '4' AND NOT invoice.tipo_cliente = '3' AND NOT invoice.tipo_venta = '12' THEN '0' ELSE invoice.numeracion END ELSE invoice.numeracion END AS number,
	to_char(invoice.invoice_date::DATE, 'DD/MM/YYYY') AS fecha,
	monto_10 AS monto_10,
	iva_10 AS iva_10,
	monto_5 AS monto_5,
	iva_5 AS iva_5,
	monto_exento AS monto_exento,
	(monto_10 + iva_10 + monto_5 + iva_5 + monto_exento) AS monto_ingreso,
	1::TEXT condicion_compra,
	0 cuotas,
	CASE WHEN invoice.tipo_venta = '7' OR invoice.tipo_venta = '13' OR partner.parent_ruc = '44444401' THEN '0' WHEN invoice.move_type = 'out_invoice' OR invoice.move_type = 'in_refund' THEN CASE WHEN partner.parent_ruc = '44444401' THEN '0' ELSE invoice.timbrado END ELSE '0' END AS timbrado
FROM RUC_GENERICO AS iva
JOIN account_move AS invoice ON invoice.id=iva.factura_id
JOIN CLIENTE AS partner ON partner.id = invoice.partner_id
WHERE invoice.state = 'posted' 
AND extract(month from invoice.invoice_date)={0}
AND extract(year from invoice.invoice_date)={1}
AND ((invoice.move_type = 'in_refund' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401')) OR invoice.move_type = 'out_invoice' AND ((partner.ruc IS NULL AND partner.parent_ruc IS NULL) OR partner.ruc = '44444401' OR partner.ruc = '66666601' OR (partner.ruc IS NULL AND partner.parent_ruc IS NULL) OR partner.ruc = '77777701' OR partner.ruc = '88888801' OR partner.parent_ruc = '44444401' OR partner.parent_ruc = '66666601' OR partner.parent_ruc = '77777701' OR partner.parent_ruc = '88888801' OR invoice.tipo_venta = '12') OR invoice.tipo_cliente IN ('2','3','4'))
),
T3 AS (SELECT
	'2'::text AS tipo,
	CASE WHEN invoice.tipo_venta = '12' THEN '66666601' WHEN partner.is_company THEN partner.ruc ELSE partner.parent_ruc END AS ruc,
	CASE WHEN invoice.tipo_venta = '12' THEN '6' WHEN partner.is_company THEN partner.dv ELSE partner.parent_dv END AS dv,
	CASE WHEN invoice.tipo_venta = '12' THEN 'Clientes de Exportación' WHEN invoice.tipo_cliente = '4' THEN 'Clientes del Exterior' WHEN invoice.tipo_cliente = '3' THEN 'Ventas a Agentes Diplomáticos' WHEN invoice.tipo_cliente = '1' AND partner.is_company THEN partner.name ELSE partner.parent_name END AS name,
	CASE WHEN partner.parent_ruc = '44444401' THEN '0' ELSE CASE WHEN invoice.move_type = 'in_refund' THEN 3::text ELSE invoice.tipo_venta END END AS tipo_documento,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN partner.parent_ruc = '44444401' THEN '0' ELSE invoice.numeracion END ELSE invoice.numeracion END AS number,
	to_char(invoice.invoice_date::DATE, 'DD/MM/YYYY') AS fecha,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN (invoice.tipo_venta = '12' OR invoice.tipo_cliente = '3' OR invoice.tipo_cliente = '4') THEN ruc_generico.monto_10 WHEN invoice.tipo_cliente = '1' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401') THEN ruc_generico.monto_10 ELSE iva_sumas.monto_10 END ELSE iva_sumas.monto_10 END AS monto_10,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN (invoice.tipo_venta = '12' OR invoice.tipo_cliente = '3' OR invoice.tipo_cliente = '4') THEN ruc_generico.iva_10 WHEN invoice.tipo_cliente = '1' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401') THEN ruc_generico.iva_10 ELSE iva_sumas.iva_10 END ELSE iva_sumas.iva_10 END AS iva_10,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN (invoice.tipo_venta = '12' OR invoice.tipo_cliente = '3' OR invoice.tipo_cliente = '4') THEN ruc_generico.monto_5 WHEN invoice.tipo_cliente = '1' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401') THEN ruc_generico.monto_5 ELSE iva_sumas.monto_5 END ELSE iva_sumas.monto_5 END AS monto_5,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN (invoice.tipo_venta = '12' OR invoice.tipo_cliente = '3' OR invoice.tipo_cliente = '4') THEN ruc_generico.iva_5 WHEN invoice.tipo_cliente = '1' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401') THEN ruc_generico.iva_5 ELSE iva_sumas.iva_5 END ELSE iva_sumas.iva_5 END AS iva_5,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN (invoice.tipo_venta = '12' OR invoice.tipo_cliente = '3' OR invoice.tipo_cliente = '4') THEN ruc_generico.monto_exento WHEN invoice.tipo_cliente = '1' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401') THEN ruc_generico.monto_exento ELSE iva_sumas.monto_exento END ELSE iva_sumas.monto_exento END AS monto_exento,
	CASE WHEN invoice.move_type = 'out_invoice' THEN CASE WHEN (invoice.tipo_venta = '12' OR invoice.tipo_cliente = '3' OR invoice.tipo_cliente = '4') THEN (ruc_generico.monto_10 + ruc_generico.iva_10 + ruc_generico.monto_5 + ruc_generico.iva_5 + ruc_generico.monto_exento) WHEN invoice.tipo_cliente = '1' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401') THEN (ruc_generico.monto_10 + ruc_generico.iva_10 + ruc_generico.monto_5 + ruc_generico.iva_5 + ruc_generico.monto_exento) ELSE (iva_sumas.monto_10 + iva_sumas.iva_10 + iva_sumas.monto_5 + iva_sumas.iva_5 + iva_sumas.monto_exento) END ELSE (iva_sumas.monto_10 + iva_sumas.iva_10 + iva_sumas.monto_5 + iva_sumas.iva_5 + iva_sumas.monto_exento) END AS monto_ingreso,
	CASE WHEN invoice.move_type = 'in_refund' THEN '1' WHEN invoice.invoice_payment_term_id IS NULL THEN 1::text ELSE CASE WHEN term.es_credito = TRUE THEN 2::text ELSE 1::text END END AS condicion_compra,
	CASE WHEN invoice.move_type = 'in_refund' THEN '0' WHEN term.es_credito = TRUE THEN term.cuotas ELSE 0::integer END AS cuotas,
	CASE WHEN invoice.tipo_venta = '7' OR invoice.tipo_venta = '13' OR partner.parent_ruc = '44444401' THEN '0' WHEN invoice.move_type = 'out_invoice' OR invoice.move_type = 'in_refund' THEN CASE WHEN partner.parent_ruc = '44444401' THEN '0' ELSE invoice.timbrado END ELSE '0' END AS timbrado
FROM account_move invoice
LEFT JOIN account_payment_term AS term ON invoice.invoice_payment_term_id = term.id
JOIN IVA_SUMAS_2 AS iva_sumas ON iva_sumas.factura_id = invoice.id
JOIN CLIENTE AS partner ON partner.id = invoice.partner_id
LEFT JOIN RUC_GENERICO AS ruc_generico ON ruc_generico.factura_id = invoice.id
WHERE invoice.move_type IN ('out_invoice', 'in_refund') AND invoice.state LIKE 'posted'
AND extract(month from invoice.invoice_date)={0}
AND extract(year from invoice.invoice_date)={1}
AND NOT((invoice.move_type = 'in_refund' AND (partner.ruc = '44444401' OR partner.parent_ruc = '44444401')) OR invoice.move_type = 'out_invoice' AND (partner.ruc = '44444401' OR partner.ruc = '66666601' OR partner.ruc = '77777701' OR partner.ruc = '88888801' OR partner.parent_ruc = '44444401' OR partner.parent_ruc = '66666601' OR partner.parent_ruc = '77777701' OR partner.parent_ruc = '88888801' OR invoice.tipo_venta = '12'))
UNION SELECT * from IVA_SUMAS_3 AS ruc_generico
)''').format(mes, anho, iva_venta_10, iva_venta_5, exenta_venta, iva_compra_10, iva_compra_5, exenta_compra)


def get_query_compras(mes, anho, iva_compra_10, iva_compra_5, exenta_compra, iva_venta_10, iva_venta_5, exenta_venta, comp):
	return ('''-- OBTIENE EL MONTO DEL IVA 10% E IVA 5% DE LOS MOVE.LINE DE TAXES
WITH IVA AS (SELECT
CASE WHEN aml.tax_line_id = {2} OR aml.tax_line_id = {5} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS iva_10,
CASE WHEN aml.tax_line_id = {3} OR aml.tax_line_id = {6} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS iva_5, 
aml.id AS id_linea_iva,
aml.*
FROM account_move_line aml
JOIN account_move acc_move ON acc_move.id = aml.move_id
WHERE tax_line_id IS NOT NULL AND (acc_move.move_type = 'in_invoice' OR acc_move.move_type = 'out_refund')),

-- OBTIENE LOS MOVE.LINE QUE TIENEN ALGUN TIPO DE IVA
MONTOS AS (SELECT 
CASE WHEN tax.id = {2} OR tax.id = {5} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS monto_10,
CASE WHEN tax.id = {3} OR tax.id = {6} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS monto_5,
CASE WHEN tax.id = {4} OR tax.id = {7} THEN CASE WHEN aml.credit > 0 THEN aml.credit WHEN aml.debit > 0 THEN aml.debit ELSE 0 END ELSE 0 END AS monto_exento,
aml.id AS id_linea,
aml.*, 
tax.* 
FROM account_move_line aml
JOIN account_move acc_move ON acc_move.id = aml.move_id
JOIN account_move_line_account_tax_rel line_tax ON aml.id = line_tax.account_move_line_id
JOIN account_tax tax ON line_tax.account_tax_id = tax.id
WHERE acc_move.move_type = 'in_invoice' OR acc_move.move_type = 'out_refund'
ORDER BY acc_move),

--JOIN DE LOS PRODUCTOS CON IVA Y LAS LINEAS DE IVA
IVA_MONTOS AS (SELECT 
CASE WHEN IVA.move_id IS NULL THEN montos.move_id ELSE iva.move_id END AS factura_id,
* FROM IVA FULL JOIN MONTOS ON IVA.id = montos.id_linea),
IVA_SUMAS AS( SELECT 
factura_id, 
CASE WHEN sum(monto_10) IS NOT NULL THEN round(sum(monto_10))::integer ELSE 0::integer END AS monto_10,
CASE WHEN sum(iva_10) IS NOT NULL THEN round(sum(iva_10))::integer ELSE 0::integer END AS iva_10,
CASE WHEN sum(monto_5) IS NOT NULL THEN round(sum(monto_5))::integer ELSE 0::integer END AS monto_5,
CASE WHEN sum(iva_5) IS NOT NULL THEN round(sum(iva_5))::integer ELSE 0::integer END AS iva_5,
CASE WHEN sum(monto_exento) IS NOT NULL THEN round(sum(monto_exento))::integer ELSE 0::integer END AS monto_exento
from IVA_MONTOS 
GROUP BY factura_id
ORDER BY factura_id),

-- OBTIENE EL PROVEEDOR
PROVEEDOR AS( 
select
partner.id,
partner.ruc,
partner.dv,
partner.name,
partner.is_company,
partner.type,
parent.id AS parent_id,
parent.ruc AS parent_ruc,
parent.dv AS parent_dv,
parent.name AS parent_name
from res_partner AS partner
left join res_partner AS parent ON partner.id = parent.id
), T3 AS(
SELECT
'2'::text AS tipo,
CASE WHEN invoice.tipo_compra = '11' THEN '22222201' WHEN invoice.tipo_compra = '8' THEN '99999901' WHEN partner.is_company THEN partner.ruc ELSE partner.parent_ruc END AS ruc,
CASE WHEN invoice.tipo_compra = '11' THEN '8' WHEN invoice.tipo_compra = '8' THEN '0' WHEN partner.is_company THEN partner.dv ELSE partner.parent_dv END AS dv,
CASE WHEN invoice.tipo_compra = '8' THEN 'Proveedores del Exterior' WHEN partner.is_company THEN partner.name ELSE partner.parent_name END AS name,
CASE WHEN invoice.move_type = 'out_refund' OR (invoice.move_type = 'in_invoice' AND (invoice.tipo_compra = '1' OR invoice.tipo_compra = '2' OR invoice.tipo_compra = '3' OR invoice.tipo_compra = '5')) THEN invoice.timbrado ELSE 0::text END AS timbrado,
CASE WHEN partner.ruc = '{8}' AND invoice.move_type != 'out_refund' THEN '5' WHEN invoice.move_type = 'out_refund' THEN '3' ELSE invoice.tipo_compra END AS tipo_documento,
CASE WHEN invoice.move_type = 'out_refund' OR (invoice.move_type = 'in_invoice' AND (invoice.tipo_compra != '11')) THEN invoice.numeracion ELSE 0::text END AS number,
to_char(invoice.invoice_date::DATE, 'DD/MM/YYYY') AS fecha,
iva_sumas.monto_10,
iva_sumas.iva_10,
iva_sumas.monto_5,
iva_sumas.iva_5,
iva_sumas.monto_exento,
0 tipo_operacion,
--CASE WHEN company.exportador = FALSE THEN '0' WHEN invoice.tipo_operacion IS NULL THEN '8' ELSE invoice.tipo_operacion END tipo_operacion,
CASE WHEN invoice.move_type = 'out_refund' THEN '1' WHEN invoice.invoice_payment_term_id IS NULL THEN 1::text ELSE CASE WHEN term.es_credito = TRUE THEN 2::text ELSE 1::text END END AS condicion_compra,
CASE WHEN invoice.move_type = 'out_refund' THEN '0' WHEN term.es_credito = TRUE THEN term.cuotas ELSE 0::integer END AS cuotas
FROM account_move invoice
LEFT JOIN account_payment_term AS term ON invoice.invoice_payment_term_id = term.id
JOIN IVA_SUMAS ON IVA_SUMAS.factura_id = invoice.id
JOIN PROVEEDOR AS partner ON partner.id = invoice.partner_id
JOIN res_company AS company ON invoice.company_id = company.id
where invoice.move_type in ('in_invoice', 'out_refund') AND invoice.state like 'posted'
AND extract(month from invoice.invoice_date)={0}
AND extract(year from invoice.invoice_date)={1}
ORDER BY ruc
)''').format(mes, anho, iva_compra_10, iva_compra_5, exenta_compra, iva_venta_10, iva_venta_5, exenta_venta, comp.partner_id.ruc, comp.exportador)
