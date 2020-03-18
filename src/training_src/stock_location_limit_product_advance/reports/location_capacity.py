# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.tools import formatLang


class LocationCapacity(models.Model):
    _name = 'stock.location.capacity'
    _auto = False
    _description = 'Location & Location Limit'
    _order = "location_id asc, product_id asc"

    id = fields.Integer(string="id")
    name = fields.Char(string='Location Name', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', readonly=True)
    qty = fields.Float('Limit Max', readonly=True)
    usage_capacity = fields.Float('Current Capacity', readonly=True)
    remaind_capacity = fields.Float('Remaind Capacity', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)

    @api.model_cr
    def init(self):
        # TODO: pastikan conversi satuan disini, jangan lupa
        tools.drop_view_if_exists(self.env.cr, 'stock_location_capacity_union')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW stock_location_capacity AS (
	                SELECT
	                    b.id, b.id as location_id, b.name, a.product_id, a.qty, a.usage_capacity, a.remaind_capacity, a.uom_id
                        FROM stock_location b
                        INNER JOIN  stock_location_limit a on a.location_id = b.id
            )""")

    def name_get(self):
        result = []
        for loc in self:
            name = loc.name or ''
            uom = loc.uom_id.name
            qty = loc.qty
            usage_capacity = loc.usage_capacity
            remaind_capacity = loc.remaind_capacity
            if not qty:
                qty = 0.0
                usage_capacity = 0.0
                remaind_capacity = 0.0
                uom = ''
            name += ' limit Max: ' + str(qty) + ' Available: ' + str(usage_capacity) + ' Remaind: ' + str(
                remaind_capacity) + ' ' + uom
            result.append((loc.id, name))
        return result
