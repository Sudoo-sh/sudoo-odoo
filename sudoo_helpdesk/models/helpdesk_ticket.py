# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
from odoo import models


class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _inherit = ["helpdesk.ticket", "sudoo.instance.mixin"]

    def _sudoo_instance_defaults(self):
        self.ensure_one()
        return {"instance_name": f"ticket-{self.id}"}
