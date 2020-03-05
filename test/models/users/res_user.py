from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import clean_context
class NoviasResUser(models.Model):
    _inherit = "res.users"
    warehouse_id = fields.Many2one('stock.warehouse')
    
    def algo(self):
        pass