# Marangatu
## Descripción
Módulo de Odoo V14 Enterprise que permite generar archivos ```.csv``` de Marangatu según las Especificaciones Técnicas
para registro de comprobantes en Marangatu de Junio de 2021.  

## Features
* Permite generar los archivos ```.csv``` para libros de compra, venta, ingreso y egreso que posteriormente son 
  comprimidos en un archivo ```.zip``` para subir al sistema Marangatu.
* Agrega el manejo de Tipos de Documento de Identificación en los partners.
* Agrega la configuración para introducir los impuestos por defecto mediante la creación de impuestos
  proveída por defecto por Odoo.
* Agrega un pop-up para generar los archivos de acuerdo al año, mes y tipo deseado. Una vez generado
  todos los archivos se guardan para descargar posteriormente.

## Instalación
* Instalar desde ```Aplicaciones``` el módulo de ``` marangatu```.
* Configurar el módulo ```talonario_py``` de acuerdo a su guía.
* En el modulo de ```Contabilidad``` crear los impuestos correspondientes a IVA 10%, 5%
  y Exentas tanto para *Compras* como para *Ventas*.
* Ir a ```Configuración → Contabilidad → Impuestos por Defecto``` y asignar los impuestos 
  antes creados a su correspondiente campo.

## Uso
### Manejo de Tipo de Identidad por Partner
El archivo que se genera necesita poder soportar varios tipos de identificación por partner
por lo que se agregaron dos campos al form de partner, tipo de identificación y número de
documento, el campo tipo de identificación es utilizado para filtrar los contactos con 
respecto a aquellos tipos que un determinado tipo de comprobante permite. No se 
permite que un mismo partner tenga más de dos tipos de identificación.
Los valores que contiene el campo tipo de identificación son los siguientes:
- RUC
- CÉDULA DE IDENTIDAD
- PASAPORTE
- CÉDULA EXTRANJERA
- SIN NOMBRE
- DIPLOMÁTICO
- IDENTIFICACIÓN TRIBUTARIA

### Comprobante de Venta
* Se debe crear el talonario correspondiente al tipo de comprobante que se va a utilizar si es que aún no se creó
* Se debe asignar el talonario y el número del comprobante
* Se debe seleccionar el tipo de factura, los cuales pueden ser:
    * Boleta de Transporte Público de Pasajeros
    * Boleta de Venta
    * Boleta de Loterías, Juegos de Azar
    * Boleto o Ticket de Transporte Aéreo
    * Entrada a Espectáculos Públicos
    * Factura
    * Ticket de Máquina Registradora
    * **OBS:** *Los tipos "Nota de Crédito" y "Nota de Débito" se pueden elegir solo al crear una factura rectificativa.*
* Ingresar los datos correspondientes a los campos que requieren cada tipo de documento.
* Elegir si a que impuesto imputa, debe imputar al menos a uno de los tres impuestos disponibles.
* Para determinar la Condición de Venta se debe elegir un término de pago en el campo de fecha de 
vencimiento y dentro del término de pago seleccionar si es Contado o Crédito y si es Crédito ingresar
cuantas cuotas tiene.
### Comprobante de Compra
- Se debe ingresar el timbrado y el número del comprobante
- Se debe seleccionar el tipo de comprobante, los cuales pueden ser:
    - Autofactura
    - Boleta de Transporte Público de Pasajeros
    - Despacho
    - Boleta de Venta
    - Boleta Resimple
    - Boleta de Loterías, Juegos de Azar
    - Boleto o Ticket de Transporte Aéreo
    - Despacho de Importación
    - Entrada a Espectáculos Públicos
    - Factura
    - Ticket de Máquina Registradora
    - **OBS:** *Al elegir el tipo "Autofactura" se asigna automáticamente al partner de la compañía del usuario actual.*
    * **OBS:** *Los tipos "Nota de Crédito" y "Nota de Débito" se pueden elegir solo al crear una factura rectificativa.*
- Ingresar los datos correspondientes a los campos que requieren cada tipo de documento.
- Elegir si a que impuesto imputa, debe imputar al menos a uno de los tres impuestos disponibles y no se permite
elegir el valor "No Imputa" sin que haya algún impuesto seleccionado.
- Para determinar la Condición de Venta se debe elegir un término de pago en el campo de fecha de 
vencimiento y dentro del término de pago seleccionar si es Contado o Crédito y si es Crédito ingresar
cuantas cuotas tiene.
### Comprobante de Ingreso
- Se debe ingresar el número del comprobante
- Se debe seleccionar el tipo de comprobante, los cuales pueden ser:
    - Comprobante de Ingresos por Ventas a Crédito
    - Liquidación de Salario
    - Otros Comprobantes de Ingreso
- Ingresar los datos correspondientes a los campos que requieren cada tipo de documento.
- Ingresar el monto que grava a algún impuesto y el monto que no grava a ninguno.
- Elegir si a que impuesto imputa, debe imputar al menos a uno de los tres impuestos disponibles.
### Comprobante de Engreso
- Se debe ingresar el número del comprobante
- Se debe seleccionar el tipo de comprobante, los cuales pueden ser:
    - Comprobante de Egresos por Compras a Crédito
    - Comprobante del Exterior Legalizado
    - Comprobante de Ingresos Entidades Públicas, Religiosas o de Beneficio Público
    - Extracto de Cuenta - Billetaje Electrónico
    - Extracto de Cuenta de IPS
    - Extracto de Cuenta TC/TD
    - Liquidación de Salario
    - Otros Comprobantes de Egresos
    - Transferencias o Giros Bancarios/Boleta de Depósito
- Ingresar los datos correspondientes a los campos que requieren cada tipo de documento.
- Elegir si a que impuesto imputa, debe imputar al menos a uno de los tres impuestos disponibles.

### Generar reporte
Para generar el reporte de Marangatu ya sea de compras o ventas se debe dirigir a 
```Contabilidad → Informe → Marangatu → Generar Marangatu```, esto abrirá un pop-up que solicita datos 
del reporte que desea generar como si es un reporte Anual o Mensual, el año y el mes en caso de ser reporte mensual,
al completar se presiona el botón de ```GENERAR REPORTE``` esto crea un reporte
tomando todos los comprobantes de compra y venta confirmadas y los almacena 
en el menu ```Contabilidad → Informe → Marangatu → Reportes Marangatu``` donde se encuentran todos los
reportes que fueron generados, para descargar el o los archivos se debe entrar al reporte recien generado donde se 
encuentran todos los archivos correspondientes a dicho reporte en formato ```.csv``` que seran mas de 1 archivo en caso
que se cuente con mas de 5000 movimientos de compra, ventas, ingresos y egresos registrados.