# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import clean_context
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
class Stock_Picking(models.Model):
    _inherit  = "stock.picking"
    
    def write(self, vals):
        is_notify = 0
        PurchaseOrder = self.env['purchase.order']
        if vals.get('picking_type_id') and self.state != 'draft':
            raise UserError(_("Changing the operation type of this record is forbidden at this point."))
        #Override re order
        if vals.get('move_line_ids_without_package') and self.location_id.name in "Reservados":
            #Get products eleminated to re-order
            products_lines = self.env['stock.move.line'].search(
                                                [ 
                                                    ('id','in', [ mwp[1] for mwp in vals.get('move_line_ids_without_package') if not mwp[2] ] )
                                                ] )
            
            #Validate if product are in stock                                   ) 
            products_re_store = [{'product':product.product_id,'qty':product.product_uom_qty} for product in products_lines if product.product_id.virtual_available <= 0 ]
            
            for product in products_re_store:
                is_notify = 1
                for product_suppliers in product['product'].seller_ids:
                    suppliers = product_suppliers.filtered(lambda vendor: vendor.product_id == product['product'] )
                    if  suppliers:
                        supplierinfo = suppliers[0]
                        partner_supplier = supplierinfo.name
                        #Exist purchase order partner_id
                        po = self.env['purchase.order'].search( ['&',('partner_id.id','like',partner_supplier.id),('state','=','draft')] ) 
                        if po:
                            po[0].write( {'order_line': [ (0,0,{
                                                                'name':"Restablecer negativo  orden "+self.sale_id.name,
                                                                'product_id':product['product'].id,
                                                                'product_qty': product['qty'],
                                                                 #'product_uom_qty':1,
                                                                'price_unit':supplierinfo.price,
                                                                'order_id':po[0].id,
                                                                'product_uom':product['product'].uom_id.id,
                                                                'date_planned':self.sale_id.date_sheddule

                                                              }
                                                          )
                                                        ],
                                          'origin':str(po[0].origin)+","+self.sale_id.name if not self.sale_id.name in po[0].origin else po[0].origin
                                          } 
                                       )
                        else:                            
                            po_or = self.sale_id.purchase_service_prepare_order_values_n(supplierinfo)                    
                            po_or['order_line'] = [ (0,0,{
                                                                'name':"Restablecer negativo  orden "+self.sale_id.name,
                                                                'product_id':product['product'].id,
                                                                'product_qty': product['qty'],
                                                                 #'product_uom_qty':1,
                                                                'price_unit':supplierinfo.price,
                                                                'product_uom':product['product'].uom_id.id,
                                                                'date_planned':self.sale_id.date_sheddule

                                                              }
                                                          )
                                                        ]
                            purchase_order = PurchaseOrder.create(po_or)
                          
        
                 
        res = super(Stock_Picking, self).write(vals)
        if(is_notify == 1 ): 
                sale= self.sale_id
                template_id = self.env.ref('test.mail_template_dropshiping').id
                lang = self.env.context.get('lang')
                template = self.env['mail.template'].browse(template_id)
                taller = self.env["res.partner"].search([('name','like','Taller')])
                if template.lang:
                    lang = template._render_template(template.lang, 'sale.order', sale.id)
                
                html = """
                         <table style="width:1000px;margin:0px auto;background:white;border:1px solid #e1e1e1;">
                            <tbody>
                                <tr>
                                    <td style="padding:15px 20px 10px 20px; font-size:20px;">
                                        <p>
                                            Estimado colaborador se han retirado productos de la venta <strong>"""+sale.name+"""</strong>
                                        </p>
                                        <p>
                                            Se genero una orden de compra(si proveedor existe).                              
                                        </p>
                                        <p>Fecha programada para entrega : <strong>"""+sale.event_date.strftime('%Y-%m-%d')+"""</strong> </p>
                                        <div style="margin: 16px 0px 16px 0px;">
                                        </div>
                                    </td>
                                    <td style="padding:15px 20px 10px 20px;">
                                        <p style="text-align: center;">
                                            
                                        </p>
                                    </td>
                                </tr>
                            </tbody>
                             </table>
                        </div>
                        """
                vals = {
                          'subject': "Venta negativo-"+sale.name+"-"+stsale.date_workshop,
                        'model': 'sale.order',
                        'res_id': sale.id,
                        'body':html,
                        'template_id': template_id,
                        'composition_mode': 'comment',
                      
                }
                ctx = {
                      'mark_so_as_sent': True,
                      'proforma': self.env.context.get('proforma', False),
                      'force_email': True,
                      'model_description': sale.with_context(lang=lang).type_name
                }
                self = self.with_context(ctx)
                post = self.env["mail.compose.message"].create(vals)
                post.send_mail()
        #_logger.info( "----------------------------------- "+str(products_lines )  )  
        after_vals = {}
        if vals.get('location_id'):
            after_vals['location_id'] = vals['location_id']
        if vals.get('location_dest_id'):
            after_vals['location_dest_id'] = vals['location_dest_id']
        if after_vals:
            self.mapped('move_lines').filtered(lambda move: not move.scrapped).write(after_vals)
  
        if vals.get('move_lines'):     
            # Do not run autoconfirm if any of the moves has an initial demand. If an initial demand
            # is present in any of the moves, it means the picking was created through the "planned
            # transfer" mechanism.
            pickings_to_not_autoconfirm = self.env['stock.picking']
            for picking in self:
                if picking.state != 'draft':
                    continue
                for move in picking.move_lines:
                    if not float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                        pickings_to_not_autoconfirm |= picking
                        break
            (self - pickings_to_not_autoconfirm)._autoconfirm_picking()
        return res

    def do_unreserve(self):
        PurchaseOrder = self.env['purchase.order']
        is_notify = 0
        for picking in self:
            if self.move_line_ids_without_package  and self.location_id.name in "Reservados":
                is_notify = 1
                products_re_store = [{'product':product.product_id,'qty':product.product_uom_qty} for product in self.move_line_ids_without_package if product.product_id.virtual_available <= 0 ]
                for product in products_re_store:
                    for product_suppliers in product['product'].seller_ids:
                        suppliers = product_suppliers.filtered(lambda vendor: vendor.product_id == product['product'] )
                        if  suppliers:
                            
                            supplierinfo = suppliers[0]
                            partner_supplier = supplierinfo.name
                            #Exist purchase order partner_id
                            po = self.env['purchase.order'].search( ['&',('partner_id.id','like',partner_supplier.id),('state','=','draft')] ) 
                            if po:
                                po[0].write( {'order_line': [ (0,0,{
                                                                    'name':"Restablecer negativo  orden "+self.sale_id.name,
                                                                    'product_id':product['product'].id,
                                                                    'product_qty': product['qty'],
                                                                    #'product_uom_qty':1,
                                                                    'price_unit':supplierinfo.price,
                                                                    'order_id':po[0].id,
                                                                    'product_uom':product['product'].uom_id.id,
                                                                    'date_planned':self.sale_id.date_sheddule

                                                                }
                                                            )
                                                            ],
                                            'origin':str(po[0].origin)+","+self.sale_id.name if not self.sale_id.name in po[0].origin else po[0].origin
                                            } 
                                        )
                            else:                            
                                po_or = self.sale_id.purchase_service_prepare_order_values_n(supplierinfo)                    
                                po_or['order_line'] = [ (0,0,{
                                                                    'name':"Restablecer negativo  orden "+self.sale_id.name,
                                                                    'product_id':product['product'].id,
                                                                    'product_qty': product['qty'],
                                                                    #'product_uom_qty':1,
                                                                    'price_unit':supplierinfo.price,
                                                                    'product_uom':product['product'].uom_id.id,
                                                                    'date_planned':self.sale_id.date_sheddule

                                                                }
                                                            )
                                                            ]
                                purchase_order = PurchaseOrder.create(po_or)

            picking.move_lines._do_unreserve()
            picking.package_level_ids.filtered(lambda p: not p.move_ids).unlink()
            if(is_notify == 1 ):
                sale= self.sale_id
                template_id = self.env.ref('test.mail_template_dropshiping').id
                lang = self.env.context.get('lang')
                template = self.env['mail.template'].browse(template_id)
                taller = self.env["res.partner"].search([('name','like','Taller')])
                if template.lang:
                    lang = template._render_template(template.lang, 'sale.order', sale.id)
                
                html = """
                         <table style="width:1000px;margin:0px auto;background:white;border:1px solid #e1e1e1;">
                            <tbody>
                                <tr>
                                    <td style="padding:15px 20px 10px 20px; font-size:20px;">
                                        <p>
                                            Estimado colaborador se han retirado productos de la venta <strong>"""+sale.name+"""</strong>
                                        </p>
                                        <p>
                                            Se genero una orden de compra(si proveedor existe).                              
                                        </p>
                                        <p>Fecha programada para entrega : <strong>"""+sale.event_date.strftime('%Y-%m-%d')+"""</strong> </p>
                                        <div style="margin: 16px 0px 16px 0px;">
                                        </div>
                                    </td>
                                    <td style="padding:15px 20px 10px 20px;">
                                        <p style="text-align: center;">
                                            
                                        </p>
                                    </td>
                                </tr>
                            </tbody>
                             </table>
                        </div>
                        """
                vals = {
                      'subject': "Venta negativo-"+sale.name+"-"+str(sale.date_workshop),
                         'model': 'sale.order',
                        'res_id': sale.id,
                        'body':html,
                        
                        'template_id': template_id,
                        'composition_mode': 'comment',
                      
                }
                ctx = {
                      'mark_so_as_sent': True,
                      'proforma': self.env.context.get('proforma', False),
                      'force_email': True,
                      'model_description': sale.with_context(lang=lang).type_name
                }
                self = self.with_context(ctx)
                post = self.env["mail.compose.message"].create(vals)
                post.send_mail()
               
                
    

                
                #template_id = self.env.ref('test.mail_template_dropshiping').id
                #template =self.env['mail.template'].browse(template_id)
                #template.send_mail(self.sale_id.id, force_send=True)  
                 
   