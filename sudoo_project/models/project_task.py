# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
"""Project tasks get Sudoo.sh instances through sudoo.instance.mixin."""

from odoo import models


class ProjectTask(models.Model):
    """Tasks can have test instances of the task's branch."""

    _name = "project.task"
    _inherit = ["project.task", "sudoo.instance.mixin"]

    def _sudoo_instance_defaults(self):
        """Named after the task (task-<id>), built from a repository."""
        self.ensure_one()
        return {"instance_name": f"task-{self.id}", "source": "repository"}
