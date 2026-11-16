# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
import re

from odoo import _, api, fields, models


class SudooInstanceCreate(models.TransientModel):
    """Ask a panel for a new instance: from a GitHub repository and branch, or plain Odoo."""

    _name = "sudoo.instance.create"
    _description = "New Sudoo.sh instance"

    server_id = fields.Many2one("sudoo.server", string="Panel", required=True,
                                default=lambda self: self.env["sudoo.server"].search([], limit=1))
    source = fields.Selection([("repository", "From a GitHub repository"), ("plain", "Plain Odoo")],
                              default="plain", required=True)
    repository = fields.Char(help="For example https://github.com/acme/odoo-addons")
    branch = fields.Char(default="main")
    instance_name = fields.Char(string="Name", help="Empty: the panel names it after the branch or the version.")
    version = fields.Char(string="Odoo version", required=True)
    edition = fields.Selection([("community", "Community"), ("enterprise", "Enterprise")],
                               default="community", required=True)
    lifetime_days = fields.Integer(string="Lifetime (days)", help="0 keeps it until it is deleted by hand.")
    demo_data = fields.Boolean(string="Load demo data")
    install_modules = fields.Boolean(string="Install the repository's modules", default=True)
    res_model = fields.Char()
    res_id = fields.Many2oneReference(model_field="res_model")

    @api.onchange("server_id")
    def _onchange_server_id(self):
        if self.server_id:
            self.version = self.version or self.server_id.default_version
            if not self.lifetime_days:
                self.lifetime_days = self.server_id.default_lifetime_days

    def _panel_body(self):
        self.ensure_one()
        body = {
            "version": self.version,
            "edition": self.edition,
            "delete_after_days": self.lifetime_days,
            "demo": self.demo_data,
        }
        name = re.sub(r"[^A-Za-z0-9 ._-]+", " ", self.instance_name or "").strip()[:40]  # what the panel accepts
        if name:
            body["name"] = name
        if self.source == "repository":
            body.update(repo=self.repository or "", branch=self.branch or "main", install_modules=self.install_modules)
        return body

    def action_create(self):
        self.ensure_one()
        job = self.server_id._call("POST", "/instances", body=self._panel_body()) or {}
        instance = self.env["sudoo.instance"].create({
            "name": job.get("instance") or self.instance_name or _("new instance"),
            "server_id": self.server_id.id,
            "status": "creating",
            "last_job_id": job.get("id"),
            "odoo_version": self.version,
            "edition": self.edition,
            "source": self.source,
            "repository": self.repository if self.source == "repository" else False,
            "branch": self.branch if self.source == "repository" else False,
            "lifetime_days": self.lifetime_days,
            "res_model": self.res_model or False,
            "res_id": self.res_id or False,
        })
        instance.message_post(body=_("Creation requested by %s. The link appears here when it is ready.",
                                     self.env.user.name))
        return {"type": "ir.actions.act_window", "res_model": "sudoo.instance", "res_id": instance.id,
                "view_mode": "form", "target": "current"}
