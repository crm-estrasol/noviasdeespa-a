# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import clean_context
from datetime import datetime
from dateutil.relativedelta import relativedelta

class NoviasSaleOrder(models.Model):
    _inherit  = "sale.order"
    
    #@api.model
    #def _default_warehouse_id(self):
    #   return self.env.user.warehouse_id.id
    #warehouse_id = fields.Many2one(
    #    'stock.warehouse', string='Warehouse',
    #    required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #    default=_default_warehouse_id, check_company=True)
    selection_ejemplo= fields.Selection([('var','Estatus 1'),('var2','Estatus 2')]) 
  
    shedule_confirm = fields.Boolean("Confirmar prueba",tracking=True)
    date_sheddule = fields.Datetime('Fecha prueba',tracking=True)
    paid = fields.Boolean("Liquidado",tracking=True)
    shedule_deliver = fields.Boolean("Vestido listo",tracking=True)
    date_workshop = fields.Datetime('Nueva fecha prueba',tracking=True)
    delivered = fields.Boolean("Entregado",tracking=True)
    event_date = fields.Datetime('Fecha evento',tracking=True)
    total_invoiced = fields.Float('Total Facturado',compute='_compute_invoice_ids')
    ready_sale = fields.Boolean("Venta lista",compute='_compute_invoice_ids')
    sale_note = fields.Char('Nota de venta',tracking=True)
    comment_workshop = fields.Char('Note')
    general_status = fields.Selection([('none', 'Ninguno'), ('ready', 'Listo'),('empty', 'Pendiente'),('empty_closest', 'Pendiente(Urgente)')], string='Disponibilidad',default='none',compute='_compute_general_status')
    #inherit
    #order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True, compute='_compute_order_line')
    
    #ON COMPUTE
    @api.depends('total_invoiced','invoice_ids','ready_sale','amount_total','order_line')
    def _compute_invoice_ids(self):
        for record in self:
            if record.invoice_ids:
                sum = 0
                for invoice in record.invoice_ids:
                    if invoice.invoice_payment_state == "paid":
                        sum += invoice.amount_total_signed
                record.total_invoiced = sum
                #Is delivered product
                amount_untaxed = amount_tax = 0.0
                for line in record.order_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                total = amount_untaxed+amount_tax
                if record.total_invoiced >= total:
                    record.ready_sale = 1
                    
                else:
                    record.ready_sale = 0
            else:
                record.total_invoiced = 0
                record.ready_sale = 0
    @api.depends('general_status')
    def _compute_general_status(self):
         
        for sale in self:
            ready = 0
            if sale.date_sheddule:
                date_inf = sale.date_sheddule-relativedelta(months=4)
                date_sup = sale.date_sheddule
                ready = 0
                for sale_pick in sale.picking_ids:
                    if "Reservados" in sale_pick.location_id.name:
                        if  sale_pick.state == 'done' :
                            ready = 1
                        else:
                            ready = 0        
                if  datetime.today() >= date_inf and datetime.today() <= date_sup:
                    if ready == 0:
                        sale.general_status = 'empty_closest'
                    else:
                        sale.general_status = 'ready'
                elif ready == 0:
                    sale.general_status = 'empty'
                else:
                    sale.general_status = 'ready'
            else:
                if ready == 0:
                    sale.general_status = 'empty'
                else:
                    sale.general_status = 'ready'

                     




    #ON COMPUTE END
    
    #ON CHANGE
    @api.onchange('order_line')
    def _change_lines(self):
        cr = self._cr
        cr.execute("SELECT * FROM public.sale_order ") 
        _logger.info("-----------------------------------"+str(cr.dictfetchall()) )
        for orl in self.order_line:
            sales = self.env['sale.order'].search( ['&',('order_line.product_id.id','=',orl.product_id.id),('date_sheddule','!=',False)])               
            _logger.info( "----------------------------------- "+str(sales) )
            #sales_test = [ (sale.date_sheddule,sale.date_sheddule-relativedelta(months=4) ) for sale in sales if sale.date_sheddule  ]
            #_logger.info( "----------------------------------- "+str(sales_test) )
            sales_qulified = [ sale for sale in sales if self.date_order<sale.date_sheddule-relativedelta(months=4) if sale.date_sheddule]
            _logger.info( "----------------------------------- "+str(sales_qulified) )
            #sales = [sale for sale in  sales_qulified.picking_ids if sale.state == 'assigned' and "Reservados" in sale.location_id.name  ]
            pickings = []
            for sale_q in sales_qulified:
                for picking in sale_q.picking_ids:
                    if picking.state == 'assigned' and "Reservados" in picking.location_id.name :
                        pickings.append(picking.id)
            if pickings:
                orl.count_transfers = len(pickings)
    @api.onchange('shedule_confirm')
    def _change_shedule_confirm(self): 
        if self.shedule_confirm:
            stages = self.env["crm.stage"].search([('name','like','Prueba')])
            self.opportunity_id.stage_id = stages[0].id       
    @api.onchange('paid')
    def _change_paid(self):

        if self.paid:
            stages = self.env["crm.stage"].search([('name','like','Entrega vestido')])
            self.opportunity_id.stage_id = stages[0].id
        
        self.write( {'shedule_confirm': self.shedule_confirm} )
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
           pass
    
    #ON BUTTON ACTIONS
    def button_shedule_confirm(self):
       view_id = self.env.ref('mail.mail_activity_view_form_popup').id
       model_id = self.env['ir.model']._get('sale.order').id
       view = {
           'name': ('Nombre'),
           'view_mode': 'form',
           'res_model': 'mail.activity',
           'views':  [(view_id,'form')],
           'type': 'ir.actions.act_window',
           'target': 'new',
           'res_id': 0,
           'context':{  'default_selection_actividades':'var',
                        'default_res_model':'sale.order',
                        'default_res_id': self.id,
                        'default_res_model_id':'model_id',
                        'default_flagsh_shedule': 1 ,
                        'default_summary': "Recordatorio para 1er prueba vestido" ,
                          'default_summary': "Recordatorio para 1er prueba vestido" ,
                          'default_activity_type_id': 2 
                        
                        }
       }
       return view
    def button_shedule_workshop(self):

       view_id = self.env.ref('mail.mail_activity_view_form_popup').id
       model_id = self.env['ir.model']._get('sale.order').id
       view = {
           'name': ('Nombre'),
           'view_mode': 'form',
           'res_model': 'mail.activity',
           'views':  [(view_id,'form')],
           'type': 'ir.actions.act_window',
           'target': 'new',
           'res_id': 0,
           'context':{  'default_selection_actividades':'var2',
                        'default_res_model':'sale.order',
                        'default_res_id': self.id,
                        'default_res_model_id':'model_id',
                        'default_flagdeliv_shedule': 1,
                        'default_summary': "Recordatorio para prueba vestido correcciones taller",
                         'default_activity_type_id': 2       
                        
                        }
       }
       return view
    def button_delivered(self):
        self.delivered = 1
        stages = self.env["crm.stage"].search([('name','=','Won')])
        self.opportunity_id.action_set_won_rainbowman()

    #ON BUTTON ACTIONS END

    #REPORT TEST
    def generate_report_example(self):
       
        data = {'date_start': self.shedule_confirm, 'date_stop': self.shedule_confirm, 'config_ids': self.order_line.ids}
        return self.env.ref('test.sale_details_report_2').report_action([], data=data)
          
    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        sales = self.env["sale.order"].search([])
        products = [{ 'product':product.product_id.name } for product in products.order_line for products in sales ]
        _logger.info("-----------------------------------"+str(products))
        return { 'products':products}
   
    def render_pdf(self, data=None):
        sales = self.env["sale.order"].search([])
        _logger.info("-----------------------------------"+str([products.order_line for products in sales]) )
        #prods_t = [products.order_line for products in sales]
        #prods = [{ 'product':product.product_id.name } for product in lines for lines in prods_t  ]
                            
        return {

            'type': 'ir.actions.report.xml',

            'report_name': 'test.sale_details_report_2',

            'products': [ { 'product':1}, {'product':1} , {'product':2}  ]

            }
    def init(self):
        """ change index on partner_id to a multi-column index on (partner_id, ref), the new index will behave in the
            same way when we search on partner_id, with the addition of being optimal when having a query that will
            search on partner_id and ref at the same time (which is the case when we open the bank reconciliation widget)
        """
        cr = self._cr
        cr.execute("SELECT * FROM public.sale_order ")  
        po = self.env['purchase.order'].search( [('partner_id','=',3)] )
        #._cr.dictfetchall()
        _logger.info("-----------------------------------"+str(self.env.user.warehouse_id.name ) )
        
    def purchase_service_prepare_order_values_n(self, supplierinfo):
        """ Returns the values to create the purchase order from the current SO line.
            :param supplierinfo: record of product.supplierinfo
            :rtype: dict
        """
        self.ensure_one()
        partner_supplier = supplierinfo.name
        fiscal_position_id = self.env['account.fiscal.position'].sudo().get_fiscal_position(partner_supplier.id)
        date_order = self.purchase_get_date_order_c(supplierinfo)
        return {
            'partner_id': partner_supplier.id,
            'partner_ref': partner_supplier.ref,
            'company_id': self.company_id.id,
            'currency_id': partner_supplier.property_purchase_currency_id.id or self.env.company.currency_id.id,
            'dest_address_id': self.partner_shipping_id.id,
            'origin': self.name,
            'payment_term_id': partner_supplier.property_supplier_payment_term_id.id,
            'date_order': date_order,
            'fiscal_position_id': fiscal_position_id,
        }
    def purchase_get_date_order_c(self, supplierinfo):
        """ return the ordered date for the purchase order, computed as : SO commitment date - supplier delay """
        commitment_date = fields.Datetime.from_string(self.commitment_date or fields.Datetime.now())
        return commitment_date - relativedelta(days=int(supplierinfo.delay))
    def unescape(self,s):
        s = s.replace("&lt;", "<")
        s = s.replace("&gt;", ">")
        # this has to be last:
        s = s.replace("&amp;", "&")
        return s
    