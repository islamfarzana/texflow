from odoo import fields, models


class TexFlowProductionStage(models.Model):
    _name = 'texflow.production.stage'
    _description = 'Production Order Stage'
    _order = 'sequence, id'

    name = fields.Char(
        string='Stage Name',
        required=True,
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )

    fold = fields.Boolean(
        string='Folded in Kanban',
        default=False,
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )