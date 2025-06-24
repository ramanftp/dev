from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class PurchaseIndent(models.Model):
    _name = 'purchase.indent'
    _description = 'Purchase Indent'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(string='Reference', required=True, readonly=True, default='New')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today(), required=True)
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user)
    purchase_order_ids = fields.Many2many('purchase.order', string='Purchase Orders')

    # Approval Fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('technical', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    technical_approver = fields.Many2one(
        'res.users',
        string='Approver',
    )

    technical_approval_date = fields.Datetime(string='Approval Date', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)
    po_count = fields.Integer(compute="_compute_po_count", string='Contract Count')


    # Lines
    indent_lines = fields.One2many('purchase.indent.line', 'indent_id', string='Items')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)


    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Indent reference must be unique!'),
    ]

    @api.depends('indent_lines.price_subtotal')
    def _compute_total_amount(self):
        for indent in self:
            indent.total_amount = sum(line.price_subtotal for line in indent.indent_lines)

    def _compute_po_count(self):
        for rec in self:
            rec.po_count =  len(rec.purchase_order_ids)

    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.indent') or 'New'
        return super().create(vals)

    def action_submit(self):
        self.ensure_one()
        if not self.indent_lines:
            raise UserError(_("Cannot submit an indent without items"))

        self.write({
            'state': 'technical',
        })

    def action_open_rfq(self):
        self.ensure_one()
        return {
            'name': _("RFQ'S "),
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
        }

    def action_technical_approve(self):
        self.ensure_one()
        self.technical_approver = self.env.user


        self.write({
            'state': 'approved',
            'technical_approval_date': fields.Datetime.now(),
        })


    def action_technical_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Indent',
            'res_model': 'indent.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_indent_id': self.id,
                'default_is_technical': True,
                'default_approver_id': self.technical_approver.id,
            },
        }






    def action_purchase_indent_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Indent',
            'res_model': 'indent.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_indent_id': self.id,
            },
        }

    def action_create_purchase_orders(self):
        """ Create and/or modifier Purchase Orders. """
        self.ensure_one()
        self.indent_lines._check_products_vendor()

        for line in self.indent_lines:
            vendor = line.seller_id
            po_domain = [
            ('project_id', '=', self.project_id.id),
            ('partner_id', '=', vendor.id),
            ('state', '=', 'draft'),
        ]
            purchase_orders = self.env['purchase.order'].search(po_domain)

            if purchase_orders:
                # Existing RFQ found: check if we must modify an existing
                # purchase order line or create a new one.
                purchase_line = self.env['purchase.order.line'].search([
                    ('order_id', 'in', purchase_orders.ids),
                    ('product_id', '=', line.product_id.id),
                    ('product_uom', '=', line.product_id.uom_po_id.id),
                ], limit=1)
                purchase_order = self.env['purchase.order']
                if purchase_line:
                    # Compatible po line found, only update the quantity.
                    purchase_line.product_qty += line.quantity
                    purchase_order = purchase_line.order_id
                    purchase_order.project_id = self.project_id
                    self.purchase_order_ids |= purchase_order
                else:
                    # No purchase order line found, create one.
                    purchase_order = purchase_orders[0]
                    po_line_vals = self.env['purchase.order.line']._prepare_new_purchase_order_line(
                        line.product_id,
                        line.quantity,
                        line.product_id.uom_id,
                        self.env.company,
                        vendor,
                        purchase_order,
                    )
                    new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                    purchase_order.order_line = [(4, new_po_line.id)]
                    purchase_order.project_id = self.project_id
                    self.purchase_order_ids |= purchase_order

                # Add the request name on the purchase order `origin` field.
                new_origin = set([self.name])
                if purchase_order.origin:
                    missing_origin = new_origin - set(purchase_order.origin.split(', '))
                    if missing_origin:
                        purchase_order.write({'origin': purchase_order.origin + ', ' + ', '.join(missing_origin)})
                else:
                    purchase_order.write({'origin': ', '.join(new_origin)})
            else:
                # No RFQ found: create a new one.
                po_vals = line._get_purchase_order_values(vendor)
                new_purchase_order = self.env['purchase.order'].create(po_vals)
                po_line_vals = self.env['purchase.order.line']._prepare_new_purchase_order_line(
                    line.product_id,
                    line.quantity,
                    line.product_id.uom_id,
                    self.env.company,
                    vendor,
                    new_purchase_order,
                )
                new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                new_purchase_order.order_line = [(4, new_po_line.id)]
                new_purchase_order.project_id = self.project_id
                self.purchase_order_ids |= new_purchase_order


class PurchaseIndentLine(models.Model):
    _name = 'purchase.indent.line'
    _description = 'Purchase Indent Line'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id', store=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_price_subtotal', store=True)
    indent_id = fields.Many2one('purchase.indent', string='Indent', ondelete='cascade')
    seller_id = fields.Many2one('res.partner',string="Vendor")

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.price_unit = self.product_id.standard_price


    def _check_products_vendor(self):
        """ Raise an error if at least one product requires a seller. """
        product_lines_without_seller = self.filtered(lambda line: not line.seller_id)
        if product_lines_without_seller:
            product_names = product_lines_without_seller.product_id.mapped('display_name')
            raise UserError(
                _('Please select a vendor on product line or set it on product(s) %s.', ', '.join(product_names))
            )



    def _get_purchase_order_values(self, vendor):
        """ Get some values used to create a purchase order.
        Called in approval.request `action_create_purchase_orders`.

        :param vendor: a res.partner record
        :return: dict of values
        """
        self.ensure_one()
        vals = {
            'origin': self.indent_id.name,
            'partner_id': vendor.id,
            'payment_term_id': vendor.property_supplier_payment_term_id.id,
            'fiscal_position_id':self.env['account.fiscal.position']._get_fiscal_position(vendor).id,
        }
        return vals



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    @api.model
    def _prepare_new_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        partner = supplier
        uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id, rounding_method='HALF-UP')
        # _select_seller is used if the supplier have different price depending
        # the quantities ordered.
        today = fields.Date.today()
        seller = product_id.with_company(company_id)._select_seller(
            partner_id=partner,
            quantity=uom_po_qty,
            date=po.date_order and max(po.date_order.date(), today) or today,
            uom_id=product_id.uom_po_id)

        product_taxes = product_id.supplier_taxes_id.filtered(lambda x: x.company_id in company_id.parent_ids)
        taxes = po.fiscal_position_id.map_tax(product_taxes)

        price_unit = seller.price if seller else product_id.standard_price
        price_unit = self.env['account.tax']._fix_tax_included_price_company(
            price_unit, product_taxes, taxes, company_id)
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, po.currency_id, po.company_id, po.date_order or fields.Date.today())

        product_lang = product_id.with_prefetch().with_context(
            lang=partner.lang,
            partner_id=partner.id,
        )
        name = product_lang.with_context(seller_id=seller.id).display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        date_planned = self.order_id.date_planned or self._get_date_planned(seller, po=po)
        discount = seller.discount or 0.0

        return {
            'name': name,
            'product_qty': uom_po_qty,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes.ids)],
            'order_id': po.id,
            'discount': discount,
        }