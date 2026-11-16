# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
from odoo import models


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "sudoo.instance.mixin"]

    def _sudoo_instance_defaults(self):
        self.ensure_one()
        return {"instance_name": f"demo-{self.partner_id.name or self.name}"[:40], "demo_data": True, "source": "plain"}
