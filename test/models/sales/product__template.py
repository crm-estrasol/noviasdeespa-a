# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import clean_context
class NoviasProductTemplateAttribute(models.Model):
    _inherit = "product.template.attribute.value"
    def _get_combination_name(self):
        """Exclude values from single value lines or from no_variant attributes."""
        return "-".join([ptav.name for ptav in self._without_no_variant_attributes()._filter_single_value_lines()])
class NoviasProductTemplate(models.Model):
    _inherit = "product.template"
    
    def _get_pre_selected(self):
        atributos = self.env["product.attribute"].search([])     
        return [(0,0,{ 'attribute_id':atributo.id ,'value_ids':[ (4,atributo.value_ids[0].id ) ] } ) for atributo in atributos ]
    
    attribute_line_ids = fields.One2many('product.template.attribute.line', 'product_tmpl_id', 'Product Attributes', copy=True ,default=_get_pre_selected)

  
            