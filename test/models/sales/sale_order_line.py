# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import clean_context
from datetime import datetime
from dateutil.relativedelta import relativedelta

class NoviasSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    count_transfers = fields.Float('Apartado',compute='_compute_order_line')
    #ON COMPUTE
    @api.depends('count_transfers','product_id')
    def _compute_order_line(self):
        for record in self:
            if record.order_id:
                sales = self.env['sale.order'].search( ['&',('order_line.product_id.id','=',record.product_id.id),('date_sheddule','!=',False)])
                sales_qulified = [ sale for sale in sales if record.order_id.date_order<sale.date_sheddule-relativedelta(months=4) if sale.date_sheddule]
                #sales = [sale for sale in  sales_qulified.picking_ids if sale.state == 'assigned' and "Reservados" in sale.location_id.name  ]
                pickings = []
                for sale_q in sales_qulified:
                    for picking in sale_q.picking_ids:
                        if picking.state == 'assigned' and "Reservados" in picking.location_id.name :
                            pickings.append(picking.id)
                if pickings:
                    record.count_transfers = len(pickings)
                else:
                    record.count_transfers = len(pickings)
            else:
                record.count_transfers = 0
    #ON COMPUTE END           
    #ON BUTTON ACTIONS       
    def busqueda_activos(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        sales = self.env['sale.order'].search(['&', ('order_line.product_id.id', '=', self.product_id.id), ('date_sheddule','!=',False)])
        sales_qulified = [ sale for sale in sales if self.order_id.date_order<sale.date_sheddule-relativedelta(months=4) if sale.date_sheddule]     
        pickings = []
        for sale_q in sales_qulified:
            for picking in sale_q.picking_ids:
                if picking.state == 'assigned':
                    pickings.append(picking.id)
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings[0]
        # Prepare the context.
        #Temp value
        #pickings = sales.picking_ids
        #picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        #if picking_id:
        #    picking_id = picking_id[0]
        #else:
        #    picking_id = pickings[0]
        action['context'] = dict(self._context, default_origin=self.name )
        action['create'] = "false"
        return action
    #ON BUTTON ACTIONS END
