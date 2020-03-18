from odoo import fields, models, api


class Principal(models.Model):
    _name = 'principal'
    _description = 'Principal Master'

    def create_vendor(self):
        retval = None
        # action_pointer = self.env.ref('base.view_partner_form')
        new_view_id = self.env.ref('base.view_partner_form').id
        new_context = self._context.copy()
        other_context = self.env.ref('base.view_partner_form').with_context()
        new_context.update({'default_name':self.code + '-' })
        retval = {
            'name': 'Supplier',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(new_view_id,'form')],
            'res_model': 'res.partner',
            'view_id': new_view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': new_context,
        }
        return retval

    def call_supplier_only_action(self):
        retval = None
        action_pointer = self.env.ref('base.action_partner_supplier_form')
        result_data = action_pointer.read()[0]
        # result_data['domain'] = [('name','ilike','v')]
        result_data['domain'] = [('name','ilike',self.code)]
        result_data['context'] = {
            'search_default_supplier': 1,
            'default_customer': True
        }
        retval = result_data
        return retval

    def _get_address(self):
        counter = 0
        for data in self:
            if not data.address:
                data.address = 'Jalan Tamansari 10' + '-' + str(counter)
            counter = counter + 1

    #     # retval = 'Jalan Tamansari 10'
    #     # return retval

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    address = fields.Char(string='Address',
                          compute=_get_address
                          )
    active = fields.Boolean(string='Active')
