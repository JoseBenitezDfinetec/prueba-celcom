# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Notificacion(models.TransientModel):
    _name = 'marangatu.notificacion.wizard'
    _description = 'Ventana emergente de notificacion'

    mensaje = fields.Char()