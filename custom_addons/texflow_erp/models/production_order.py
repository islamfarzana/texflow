from odoo import api, fields, models


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