from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import clean_context
class ReportNoviasReports(models.AbstractModel):
    #It Should be called as xml report.
    _name="report.test.report_saledetails_2"
    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        sales = self.env["sale.order"].search([('state','!=','cancel'),('create_date','>=',date_start),('create_date','<=',date_stop)])
        order_line = [ products.order_line for products in sales ]
        invoices_groups = [ products.invoice_ids for products in sales ]
        invoices_ids=  []
        #Get invoices for each product sold
        for invoices_group in invoices_groups:
            for invoice in invoices_group:
                if invoice.invoice_payment_state == 'paid':
                    invoices_ids.append(invoice.id)

        products = []
        total_price = 0
        total_invoice = 0
        total_tax = 0
        total_bank = 0
        total_cash = 0
        global_total = 0
        #Get products
        for or_lin in order_line:
            for product in or_lin:
                if product.product_id.name != "Down payment":
                    total_price += product.price_unit 
                    total_tax += product.price_tax
                    products.append({
                                        'product':product.product_id.name_get()[0][1],
                                        'quantity':product.product_uom_qty,
                                        'price_tax':product.price_tax,
                                        'price_unit':product.price_unit
                                        
                                     
                                     })
        """
        invoices = []                             
        for invs_id in invoice_ids:
            for invoice in invs_id:
                if invoice.invoice_payment_state:
                    total_price += invoice.amount_total 
                    invoices.append({
                                        'amount_total':product.product_id.name,
                                        'quantity':product.product_uom_qty,
                                        'price_unit':product.price_unit
                                        
                                     
                                     })
        """
        payments = self.env["account.payment"].search([('invoice_ids','in',invoices_ids)])
        _logger.info("-----------------------------------"+str(payments))
        for pay in payments:
            _logger.info("-----------------------------------"+str(pay.invoice_ids))
            if pay.journal_id.type == "bank":
                total_bank += pay.amount
            if pay.journal_id.type == "cash":
                total_cash += pay.amount              
            total_invoice += pay.amount
        _logger.info("-----------------------------------"+str(invoices_ids))    
        
        return { 'products':products,
                  'total_price':total_price,
                  'price_tax':total_tax,
                  'total_invoice':total_invoice,
                  'total_cash': total_cash,
                  'total_bank': total_bank,
                  'global_total': total_cash + total_bank
                    }

    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['pos.config'].browse(data['config_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids))
        _logger.info("-----------------------------------"+str(data))
        return data

