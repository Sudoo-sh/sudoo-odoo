# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
"""CRM opportunities get Sudoo.sh instances through sudoo.instance.mixin."""

from odoo import models


class CrmLead(models.Model):
    """Opportunities can have demo instances."""

    _name = "crm.lead"
    _inherit = ["crm.lead", "sudoo.instance.mixin"]

    def _sudoo_instance_defaults(self):
        """A plain Odoo demo with demo data, named after the customer (or the opportunity)."""
        self.ensure_one()
        return {"instance_name": f"demo-{self.partner_id.name or self.name}"[:40], "demo_data": True, "source": "plain"}
