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
        required=True,
    )

    fabric = fields.Char(
        string='Fabric',
        required=True,
    )

    color = fields.Char(
        string='Color',
        required=True,
    )

    size = fields.Char(
        string='Size',
        required=True,
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

    production_status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Production Status',
        default='draft',
        required=True,
    )

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
