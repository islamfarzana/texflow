from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TexFlowProductionOrder(models.Model):
    _name = 'texflow.production.order'
    _description = 'Garment Production Order'
    _order = 'manufacturing_date desc, id desc'

    def _get_next_po_number(self):
        """Suggest the next available Production Order number."""
        records = self.search(
            [('name', 'like', 'PO%')],
            order='id desc'
        )

        numbers = []

        for record in records:
            name = record.name or ''

            if name.startswith('PO'):
                number_part = name[2:]

                if number_part.isdigit():
                    numbers.append(int(number_part))

        next_number = max(numbers, default=0) + 1

        # Find the first unused number.
        while self.search_count([
            ('name', '=', f'PO{next_number:05d}')
        ]):
            next_number += 1

        return f'PO{next_number:05d}'

    name = fields.Char(
        string='Production Order',
        required=True,
        copy=False,
        default=_get_next_po_number,
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )

    style = fields.Char(
        string='Style',
    )

    fabric = fields.Char(
        string='Fabric',
    )

    color = fields.Char(
        string='Color',
    )

    size = fields.Char(
        string='Size',
    )

    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
    )

    manufacturing_date = fields.Date(
        string='Manufacturing Date',
        required=True,
        default=fields.Date.context_today,
    )

    assignee_ids = fields.Many2many(
        'res.users',
        'texflow_production_order_assignee_rel',
        'order_id',
        'user_id',
        string='Assignees',
        default=lambda self: self.env.user,
    )

    def _default_stage_id(self):
        """First stage (lowest sequence) becomes the default for new orders."""
        return self.env['texflow.production.stage'].search(
            [], order='sequence, id', limit=1
        )

    stage_id = fields.Many2one(
        'texflow.production.stage',
        string='Production Stage',
        default=_default_stage_id,
        group_expand='_read_group_stage_ids',
        index=True,
    )

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Always show every active stage as a Kanban column, even the
        ones that currently have zero Production Orders."""
        return stages.search([], order='sequence, id')

    quality_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        ],
        string='Quality Status',
        default='pending',
        required=True,
    )

    # -- Raw material / stock integration -----------------------------

    raw_material_id = fields.Many2one(
        'product.product',
        string='Raw Material (Fabric)',
        domain=[('type', 'in', ('consu', 'product'))],
        help='The fabric/raw material stock item consumed by this order.',
    )

    material_uom_id = fields.Many2one(
        related='raw_material_id.uom_id',
        string='UoM',
        readonly=True,
    )

    material_qty = fields.Float(
        string='Material Required',
        help='Quantity of raw material needed for this production order, '
             'in the material\'s unit of measure.',
    )

    material_available_qty = fields.Float(
        related='raw_material_id.qty_available',
        string='Available Stock',
        readonly=True,
        help='Current on-hand quantity of the selected raw material.',
    )

    material_consumed = fields.Boolean(
        string='Material Consumed',
        default=False,
        copy=False,
        readonly=True,
    )

    stock_move_id = fields.Many2one(
        'stock.move',
        string='Material Consumption Move',
        readonly=True,
        copy=False,
    )

    def action_consume_material(self):
        """Create and validate a stock move that consumes the configured
        raw material quantity from the default warehouse stock location
        into the virtual Production location."""
        self.ensure_one()

        if self.material_consumed:
            raise UserError(_('Material has already been consumed for this order.'))

        if not self.raw_material_id or not self.material_qty:
            raise UserError(_(
                'Please set a Raw Material and a Material Required '
                'quantity before consuming stock.'
            ))

        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        )

        if not warehouse:
            raise UserError(_('No warehouse found for the current company.'))

        source_location = warehouse.lot_stock_id
        dest_location = self.env.ref(
            'stock.location_production', raise_if_not_found=False
        ) or self.env['stock.location'].search(
            [('usage', '=', 'production')], limit=1
        )

        if not dest_location:
            raise UserError(_('No Production location found.'))

        move = self.env['stock.move'].sudo().create({
            'reference': self.name,
            'product_id': self.raw_material_id.id,
            'product_uom_qty': self.material_qty,
            'product_uom': self.material_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'company_id': self.env.company.id,
        })

        move._action_confirm()
        move._action_assign()

        # Mark the full requested quantity as picked so the move can be
        # validated even if stock was not fully reserved.
        if move.move_line_ids:
            for line in move.move_line_ids:
                line.quantity = line.quantity or self.material_qty
                line.picked = True
        else:
            move.quantity = self.material_qty
            move.picked = True

        move._action_done()

        self.write({
            'material_consumed': True,
            'stock_move_id': move.id,
        })