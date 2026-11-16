# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
from odoo import models


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "sudoo.instance.mixin"]

    def _sudoo_instance_defaults(self):
        self.ensure_one()
        return {"instance_name": f"task-{self.id}", "source": "repository"}
