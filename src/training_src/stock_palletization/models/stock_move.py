from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.osv import expression


class ModelName(models.Model):
    _inherit = 'stock.move'

    def _package_create(self):
        return self.env['stock.quant.package'].create({})  # create new package/pallet

    def _prepare_move_line_package_vals(self, package, quantity):
        vals = self._prepare_move_line_vals(
            quantity=quantity)  # dibagian ini sdh termasuk lokasi tujuan berdasarkan putaway strategi
        vals['qty_done'] = vals['product_uom_qty']
        vals['result_package_id'] = package.id
        return vals

    def _create_pallet(self, quantity):
        package = self._package_create()
        vals = self._prepare_move_line_package_vals(package, quantity)
        move_line = self.env['stock.move.line']
        move_line.create(vals)

    def generate_pallet(self, qty_per_pallet, planning_qty, new_location_dest=None):
        # fungsi ini digunakan generate jumlah pallet yang diperlukan berdasarkan qty barang
        count_pallet = 0  # jumlah pallet
        qty_remaining = 0  # sisa qty

        if new_location_dest:
            self.location_dest_id = new_location_dest

        if qty_per_pallet > 0:
            # hitung jumlah pallet yang diperlukan
            count_pallet, qty_remaining = divmod(planning_qty, qty_per_pallet)

        # clear all move line
        self.mapped('move_line_ids').unlink()

        for p in range(int(count_pallet)):
            self._create_pallet(qty_per_pallet)

        if qty_remaining > 0:
            self._create_pallet(qty_remaining)

        self.write({'state': 'assigned'})
        return True

    def _get_location_capacity_remaind(self, product_id, location_id):
        # fungsi ini digunakan untuk menghitung sisa qty per location
        # available_qty adalah total qty yg msh ada di location
        unlimited = float("inf")
        stock_location_limit = self.env['stock.location.limit'].search([('product_id', '=', product_id.id),
                                                                        ('location_id', '=', location_id.id)])
        available_qty = self.env['stock.quant']._get_available_quantity(product_id, location_id)
        if stock_location_limit:
            return stock_location_limit.qty - available_qty
        else:
            return unlimited

    def get_putaway_rules(self):
        domain = [('location_src_id', '=', self.picking_id.location_dest_id.id),
                  ('action', 'in', ('push', 'pull_push'))]
        warehouse_id = self.warehouse_id or self.picking_id.picking_type_id.warehouse_id
        if not self.env.context.get('force_company',
                                    False) and self.location_dest_id.company_id == self.env.user.company_id:
            rules = self.env['procurement.group'].with_context(all_rules=True)._search_rule(self.route_ids,
                                                                                            self.product_id,
                                                                                            warehouse_id, domain)
        else:
            rules = self.sudo().env['procurement.group'].with_context(all_rules=True)._search_rule(self.route_ids,
                                                                                                   self.product_id,
                                                                                                   warehouse_id,
                                                                                                   domain)
        return rules

    def get_putaway_location(self):
        rules = self.get_putaway_rules()
        res = []
        for r in rules:
            res.append(r.location_id)
        return res

    def call_pallet_wizard(self):
        return {
            'name': 'Palletization Wizard',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pallet.wizard',
            'src_model': 'stock.move',
            'target': 'new',
            'context': {
                'display_location_capacity_info': True,
                'default_product_id': self.product_id.id,
            }
        }


class PalletWizard(models.TransientModel):
    _name = 'pallet.wizard'
    _inherit = ['multi.step.wizard.mixin']

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    qty_per_package = fields.Integer(string='Quantity Per Package',
                                     help='Maximum Quantity of the product can the package hold')
    planning_qty = fields.Integer(string='Planning Qty')
    uom_id = fields.Many2one('uom.uom', string='uom', readonly=True)
    count_of_identical_package = fields.Integer(string='Amount of Identical Package')

    location_dest_id = fields.Many2one('stock.location', string='Current Loc. dest', readonly=True)
    new_location_id = fields.Many2one('stock.location', string='New Loc. putaway')

    _loc_ids = []

    @api.onchange('product_id')
    def onchange_stock_move_id(self):
        stock_move = self.env['stock.move'].browse(self._context.get('active_id'))
        self.planning_qty = stock_move.product_uom_qty
        self.uom_id = stock_move.product_uom.id
        putaway_locations = stock_move.get_putaway_location()
        self._loc_ids = []
        for p in putaway_locations:
            self._loc_ids.append(p.id)
        self.location_dest_id = stock_move.location_dest_id.id

    @api.onchange('location_dest_id')
    def onchange_location(self):
        if len(self._loc_ids) > 0:
            self.new_location_id = self._loc_ids[0]  # set first index as default location
        result = {'domain': {
            'new_location_id': [('id', 'child_of', self._loc_ids)]}
        }
        return result

    @api.onchange('qty_per_package')
    def onchange_qty(self):
        if (self.planning_qty > 0) and (self.qty_per_package > 0):
            count_pallet, qty_remaining = divmod(self.planning_qty, self.qty_per_package)
            if qty_remaining > 0:
                count_pallet = count_pallet + 1
            self.count_of_identical_package = count_pallet

    @api.model
    def _selection_state(self):
        return [
            ('start', 'Start'),
            ('final', 'Final'),
        ]

    def state_exit_start(self):
        self._generate_pallet_and_fill_stock_move_line()
        super().state_exit_start()

    def _generate_pallet_and_fill_stock_move_line(self):
        move_line = self.env['stock.move'].browse(self._context.get('active_id'))
        planning_qty = move_line.product_uom_qty
        new_location_dest = self.new_location_id
        qty_available, qty_remaind = new_location_dest.get_location_capacity(move_line.product_id)
        if qty_remaind >= planning_qty:
            move_line.generate_pallet(self.qty_per_package, planning_qty, new_location_dest)
        else:
            raise UserError(_('please choose another location, because the destination location is not enough'))
