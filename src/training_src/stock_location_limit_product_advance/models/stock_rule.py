from odoo import models, api
from odoo.osv import expression


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _search_rule(self, route_ids, product_id, warehouse_id, domain):
        if self._context.get('all_rules', False):
            if warehouse_id:
                domain = expression.AND(
                    [['|', ('warehouse_id', '=', warehouse_id.id), ('warehouse_id', '=', False)], domain])
            Rule = self.env['stock.rule']
            res = self.env['stock.rule']
            if route_ids:
                res = Rule.search(expression.AND([[('route_id', 'in', route_ids.ids)], domain]),
                                  order='route_sequence, sequence')
            if not res:
                product_routes = product_id.route_ids | product_id.categ_id.total_route_ids
                if product_routes:
                    res = Rule.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]),
                                      order='route_sequence, sequence')
            if not res and warehouse_id:
                warehouse_routes = warehouse_id.route_ids
                if warehouse_routes:
                    res = Rule.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]),
                                      order='route_sequence, sequence')
            return res
        else:
            res = super(ProcurementGroup, self)._search_rule(route_ids, product_id, warehouse_id, domain)
            return res
