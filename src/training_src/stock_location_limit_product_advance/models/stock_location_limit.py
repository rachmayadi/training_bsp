from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from odoo.osv import expression


class StockLocationLimit(models.Model):
    _inherit = 'stock.location.limit'

    stock_quant_ids = fields.One2many('stock.quant', 'product_id', help='Technical: used to compute quantities.')
    usage_capacity = fields.Float('Usage Capacity', compute='_campute_capacity', digits=dp.get_precision('Product Quantity'), store=True)
    remaind_capacity = fields.Float('Remaind Capacity', compute='_campute_capacity', digits=dp.get_precision('Product Quantity'), store=True)

    # TODO: Tambahkan conversi qty antara uom di lokasi penyimpanan dengan uom di stock.quant
    @api.depends('stock_quant_ids.quantity', 'stock_quant_ids.reserved_quantity')
    def _campute_capacity(self):
        for loc in self:
            available_qty = self.env['stock.quant']._get_available_quantity(loc.product_id, loc.location_id)
            loc.usage_capacity = available_qty
            if loc.qty > loc.usage_capacity:
                remaind_qty = loc.qty - loc.usage_capacity
                loc.remaind_capacity = remaind_qty
            elif available_qty > loc.qty:
                loc.remaind_capacity = 0
            else:
                loc.remaind_capacity = loc.qty


class StockLocation(models.Model):
    _inherit = 'stock.location'

    location_capacity_id = fields.Many2one(
        comodel_name='stock.location.capacity',
        string='Location Capacity'
    )

    def get_location_capacity(self, product):
        ''' return usage_capacity and remaind_capacity'''
        unlimited = float("inf")
        last_capacity = self.limit_ids.filtered(lambda l: l.product_id == product)
        if last_capacity:
            return last_capacity.usage_capacity, last_capacity.remaind_capacity,
        else:
            return 0, unlimited

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        res = super(StockLocation, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
        # tampilkan sisa kapasitas lokasi penyimpanan barang
        if self.env.context.get('display_location_capacity_info'):
            new_res = []
            domain = [
                ('product_id', '=', self.env.context.get(
                    'default_product_id', False)),
                ('location_id.usage', '=', 'internal')
            ]
            loc_capacitys = self.env['stock.location.limit'].search(domain, order='location_id')
            idx = 0
            for elm in res:
                found = False
                for capacity in loc_capacitys:
                    if elm[0] == capacity.location_id.id:
                        new_res.insert(idx, (elm[0], elm[1]))
                        found = True
                        break
                if not found:
                    new_res.insert(idx, (elm[0], elm[1]))
                idx += 1
            res = new_res
        return res

    @api.multi
    def name_get(self):
        res = super(StockLocation, self).name_get()
        # tampilkan sisa kapasitas lokasi penyimpanan barang
        if self.env.context.get('display_location_capacity_info'):
            new_res = []
            domain = [
                ('product_id', '=', self.env.context.get(
                    'default_product_id', False)),
                ('location_id', 'in', self.ids)
            ]
            loc_capacitys = self.env['stock.location.limit'].search(domain, order='location_id')
            idx = 0
            for elm in res:
                found = False
                # FIXME: Loop ini ganti kembali, potensial lemott
                for capacity in loc_capacitys:
                    if elm[0] == capacity.location_id.id:
                        new_res.insert(idx, (elm[0], elm[1] + ' limit Max: ' + str(capacity.qty) + ' Usage: ' + str(capacity.usage_capacity) + ' Remaind: ' + str(capacity.remaind_capacity) + ' ' + capacity.uom_id.name))
                        found = True
                        break
                if not found:
                    new_res.insert(idx, (elm[0], elm[1]))
                idx += 1
            res = new_res
        return res

    # @api.multi
    # def name_get(self):
    #     res = super(StockLocation, self).name_get()
    #     if self.env.context.get('stock_location_capacity'):
    #         new_res = []
    #         ordered_name_loc_list = []
    #         domain = [
    #             ('product_id', '=', self.env.context.get(
    #                 'default_product_id', False)),
    #             ('location_id', 'in', self.ids)
    #         ]
    #         quants = self.env['stock.quant'].with_context(
    #             stock_location_capacity=False).read_group(
    #             domain, ['location_id', 'quantity'], 'location_id',
    #             orderby='qty desc')
    #         for quant in quants:
    #             full_name_loc = (
    #                 quant['location_id'][0],
    #                 quant['location_id'][1] + ' (%s)' % quant['quantity'])
    #             ordered_name_loc_list.append(full_name_loc)
    #             if quant['location_id'] in res:
    #                 res.remove(quant['location_id'])
    #         for elm in res:
    #             new_res.append((elm[0], elm[1] + ' (0)'))
    #         res = ordered_name_loc_list + new_res
    #     return res

    # @api.multi
    # def name_get(self):
    #     res = super(StockLocation, self).name_get()
    #     if self.env.context.get('stock_change_product_quantity'):
    #         new_res = []
    #         ordered_name_loc_list = []
    #         domain = [
    #             ('product_id', '=', self.env.context.get(
    #                 'default_product_id', False)),
    #             ('location_id', 'in', self.ids)
    #         ]
    #         if self.env.context.get('default_lot_id'):
    #             domain += [('lot_id', '=', self.env.context.get(
    #                 'default_lot_id'))]
    #         quants = self.env['stock.quant'].with_context(
    #             stock_change_product_quantity=False).read_group(
    #                 domain, ['location_id', 'quantity'], 'location_id',
    #                 orderby='qty desc')
    #         for quant in quants:
    #             full_name_loc = (
    #                 quant['location_id'][0],
    #                 quant['location_id'][1] + ' (%s)' % quant['quantity'])
    #             ordered_name_loc_list.append(full_name_loc)
    #             if quant['location_id'] in res:
    #                 res.remove(quant['location_id'])
    #         for elm in res:
    #             new_res.append((elm[0], elm[1] + ' (0)'))
    #         res = ordered_name_loc_list + new_res
    #     return res
