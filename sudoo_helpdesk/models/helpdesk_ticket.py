# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
"""Helpdesk tickets get Sudoo.sh instances through sudoo.instance.mixin."""

from odoo import models


class HelpdeskTicket(models.Model):
    """Tickets can have test instances, to reproduce a problem or check a fix."""

    _name = "helpdesk.ticket"
    _inherit = ["helpdesk.ticket", "sudoo.instance.mixin"]

    def _sudoo_instance_defaults(self):
        """Named after the ticket (ticket-<id>)."""
        self.ensure_one()
        return {"instance_name": f"ticket-{self.id}"}
