from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'



    indent_ids = fields.One2many('purchase.indent', 'project_id', string='Purchase Indents')




class IndentRejectWizard(models.TransientModel):
    _name = 'indent.reject.wizard'
    _description = 'Purchase Indent Rejection Wizard'

    indent_id = fields.Many2one('purchase.indent', required=True)
    is_technical = fields.Boolean()
    reason = fields.Text(required=True)

    def action_reject_indent(self):
        self.ensure_one()
        if not self.reason:
            raise ValidationError(_("Please provide a rejection reason"))

        self.indent_id.write({
            'state': 'rejected',
            'rejection_reason': self.reason
        })
        return {'type': 'ir.actions.act_window_close'}