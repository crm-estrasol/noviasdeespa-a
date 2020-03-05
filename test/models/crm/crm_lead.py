# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)
from odoo.tools.misc import clean_context
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
class NoviasCrmLead(models.Model):
    _inherit  = "crm.lead"
    event_date = fields.Datetime('Fecha evento',tracking=True)
    sale_note = fields.Char('Nota de venta',tracking=True)
    #ON BUTTON ACTIONS
    def action_new_quotation(self):
       
        if len(self.order_ids) >= 1:
           raise Warning("Solo puedes asociar una venta.")
        action = self.env.ref("sale_crm.sale_action_quotations_new").read()[0]
        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_event_date':self.event_date.strftime("%Y-%m-%d") if self.event_date else str(datetime.now().date())
            
        }
        return action
    def action_view_sale_quotation(self):
        
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action
    def button_open_unique_quot(self):
       view_id = self.env.ref('sale.view_order_form').id
       if self.order_ids:
            view = {
                'name': ('Cotización'),
                'view_mode': 'form',
                'res_model': 'sale.order',
                'views':  [(view_id,'form')],
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.order_ids[-1].id
            }
            return view
    #ON BUTTON ACTIONS END