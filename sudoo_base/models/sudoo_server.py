# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.panel_client import PanelClient, PanelError


class SudooServer(models.Model):
    """A Sudoo.sh panel this company uses. Its API token and signing secret are visible to managers only."""

    _name = "sudoo.server"
    _description = "Sudoo.sh panel"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    url = fields.Char(string="Panel address", required=True, help="For example https://panel.example.com")
    token = fields.Char(string="API token", groups="sudoo_base.group_sudoo_manager", copy=False)
    secret = fields.Char(string="Signing secret", groups="sudoo_base.group_sudoo_manager", copy=False)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    default_version = fields.Char(string="Default Odoo version", default="19.0")
    default_lifetime_days = fields.Integer(string="Default lifetime (days)", default=14,
                                           help="0 keeps instances until they are deleted by hand.")
    instance_ids = fields.One2many("sudoo.instance", "server_id")
    instance_count = fields.Integer(compute="_compute_instance_count")

    @api.depends("instance_ids")
    def _compute_instance_count(self):
        for server in self:
            server.instance_count = len(server.instance_ids)

    # ------------------------------------------------------------------ connection

    def _client(self):
        """A signed client for this panel, acting for the current Odoo user."""
        self.ensure_one()
        server = self.sudo()  # the token is read by the module, never shown to users without the manager group
        return PanelClient(server.url, server.token, server.secret, acting_for=self.env.user.login)

    def _call(self, method, path, **kwargs):
        try:
            return self._client().request(method, path, **kwargs)
        except PanelError as error:
            raise UserError(str(error)) from error

    def action_test_connection(self):
        self.ensure_one()
        versions = self._call("GET", "/versions") or []
        names = ", ".join(v["version"] for v in versions) or _("none")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("Connected"), "message": _("Odoo versions offered: %s", names), "type": "success"},
        }

    def action_sync(self):
        self.env["sudoo.instance"]._sync_servers(self)
        return True

    def action_view_instances(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("sudoo_base.action_sudoo_instance")
        action["domain"] = [("server_id", "=", self.id)]
        return action
