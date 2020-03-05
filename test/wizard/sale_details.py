# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleDetails(models.TransientModel):
    _name = 'test.sale.details.wizard'
    
    _description = 'Point of Sale Details Report'
    start_date = fields.Datetime(required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(required=True, default=fields.Datetime.now)
    def generate_report(self):
        data = {'date_start':self.start_date, 'date_stop': self.end_date, 'config_ids': ""}
        return self.env.ref('test.sale_details_report_dos').report_action([], data=data)
    