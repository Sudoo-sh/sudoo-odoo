# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
"""Sudoo.sh panels (sudoo.server) and the Odoo versions they offer (sudoo.server.version).

A panel record holds the address, the API token and the signing secret, and the rules for what this
company's users may create there. Models call the panel only through SudooServer._call.
"""

from urllib.parse import urlsplit

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.panel_client import PanelClient, PanelError

LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


class SudooServer(models.Model):
    """A Sudoo.sh panel this company uses, and what its Odoo users may create on it.

    The API token and the signing secret are readable by Sudoo.sh administrators only; the module reads them with
    sudo() to sign requests and never shows them to anyone else."""

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
    acting_for_unsupported = fields.Boolean(
        readonly=True,
        copy=False,
        help="Set by the module when the panel is " "older than the signed X-Sudoo-Acting-For header.",
    )
    instance_ids = fields.One2many("sudoo.instance", "server_id")
    instance_count = fields.Integer(compute="_compute_instance_count")

    # what the administrator allows Odoo users to create on this panel
    version_ids = fields.One2many("sudoo.server.version", "server_id", string="Odoo versions")
    allow_plain = fields.Boolean(string="Plain Odoo", default=True)
    allow_repository = fields.Boolean(string="From a GitHub repository", default=True)
    allow_enterprise = fields.Boolean(
        string="Enterprise edition", default=True, help="Only for versions where the panel has Enterprise."
    )
    allow_demo_data = fields.Boolean(string="Demo data", default=True)
    default_lifetime_days = fields.Integer(string="Default lifetime (days)", default=14)
    max_lifetime_days = fields.Integer(
        string="Longest lifetime (days)",
        default=90,
        help="0: no limit, and instances may be kept until deleted by hand.",
    )
    max_instances_per_user = fields.Integer(
        string="Instances per person",
        default=0,
        help="How many instances one Odoo user may have at a time; 0: no limit. " "The panel's own limits apply too.",
    )

    @api.depends("instance_ids")
    def _compute_instance_count(self):
        """How many instance records each panel has, for the smart button."""
        for server in self:
            server.instance_count = len(server.instance_ids)

    @api.onchange("url", "token", "secret")
    def _onchange_credentials(self):
        """Clear acting_for_unsupported when the address, token or secret change."""
        self.acting_for_unsupported = False  # a new panel or token: try the signed acting-for line again

    @api.constrains("url")
    def _check_url(self):
        """Refuse a panel address that is not https:// (http:// is accepted for localhost only), so tokens and
        signatures never travel in clear text. Raises ValidationError.
        """
        for server in self:
            parts = urlsplit(server.url or "")
            local = parts.hostname in LOCAL_HOSTS
            if not parts.hostname or parts.scheme not in ("https", "http") or (parts.scheme == "http" and not local):
                raise ValidationError(_("The panel address must start with https:// (http:// only for localhost)."))

    @api.constrains("default_lifetime_days", "max_lifetime_days", "max_instances_per_user")
    def _check_limits(self):
        """Refuse negative limits, and a default lifetime outside 1..longest lifetime. Raises ValidationError."""
        for server in self:
            if min(server.default_lifetime_days, server.max_lifetime_days, server.max_instances_per_user) < 0:
                raise ValidationError(_("Lifetimes and limits cannot be negative."))
            if server.max_lifetime_days and not 0 < server.default_lifetime_days <= server.max_lifetime_days:
                raise ValidationError(_("The default lifetime must be between 1 day and the longest lifetime."))

    # ------------------------------------------------------------------ connection

    def _client(self):
        """A signed client for this panel, acting for the current Odoo user (unless the panel is too old for it)."""
        self.ensure_one()
        server = self.sudo()
        acting_for = None if server.acting_for_unsupported else self.env.user.login
        return PanelClient(server.url, server.token, server.secret, acting_for=acting_for)

    def _call(self, method, path, **kwargs):
        """Send one signed request to this panel and return the answer's data (None for 204).

        If the panel refuses the signed X-Sudoo-Acting-For line with 401, the request is sent once more
        without it and acting_for_unsupported is set, so later calls skip it (panels from before that line).
        Raises UserError, in the user's language, for any PanelError.
        """
        try:
            try:
                return self._client().request(method, path, **kwargs)
            except PanelError as error:
                if error.status != 401 or self.sudo().acting_for_unsupported:
                    raise
                # a panel from before the signed acting-for line refuses the signature: once without it, and remember
                answer = PanelClient(self.sudo().url, self.sudo().token, self.sudo().secret).request(
                    method, path, **kwargs
                )
                self.sudo().acting_for_unsupported = True
                return answer
        except PanelError as error:
            raise UserError(self._panel_message(error)) from error

    def _panel_message(self, error):
        """A PanelError in the user's language (the panel's own detail stays as the panel wrote it)."""
        messages = {
            "bad_name": _("This is not a valid instance name."),
            "incomplete": _("The panel's address, API token and signing secret are all needed."),
            "unreachable": _("The panel at %(host)s could not be reached (%(reason)s)."),
            "too_large": _("The panel at %(host)s sent an answer that is too large."),
            "redirect": _("The panel at %(host)s answered with a redirect. Check the panel address."),
            "refused": _("The panel refused this: %(detail)s"),
        }
        template = messages.get(error.kind)
        return template % error.values if template else str(error)

    def _refresh_versions(self):
        """Read the Odoo versions the panel offers: new ones are added (allowed), gone ones removed."""
        for server in self:
            offered = {v["version"]: bool(v.get("enterprise")) for v in server._call("GET", "/versions") or []}
            lines = server.sudo().version_ids
            for line in lines:
                if line.name in offered:
                    line.enterprise_available = offered.pop(line.name)
                else:
                    line.unlink()
            for version, enterprise in offered.items():
                lines.create({"server_id": server.id, "name": version, "enterprise_available": enterprise})

    def action_test_connection(self):
        """Button: read the panel's Odoo versions and show them in a notification. Raises UserError on failure."""
        self.ensure_one()
        self._refresh_versions()
        names = ", ".join(self.version_ids.mapped("name")) or _("none")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("Connected"), "message": _("Odoo versions offered: %s", names), "type": "success"},
        }

    def action_sync(self):
        """Button: refresh the offered versions and sync the instance list now."""
        self._refresh_versions()
        self.env["sudoo.instance"]._sync_servers(self)
        return True

    def action_view_instances(self):
        """Smart button: the instance list, filtered to this panel."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("sudoo_base.action_sudoo_instance")
        action["domain"] = [("server_id", "=", self.id)]
        return action


class SudooServerVersion(models.Model):
    """An Odoo version a panel offers, and whether this company's users may create instances of it."""

    _name = "sudoo.server.version"
    _description = "Odoo version offered by a Sudoo.sh panel"
    _order = "server_id, name desc"

    name = fields.Char(string="Version", required=True, readonly=True)
    server_id = fields.Many2one("sudoo.server", required=True, ondelete="cascade", index=True)
    enterprise_available = fields.Boolean(string="Enterprise on the panel", readonly=True)
    allowed = fields.Boolean(default=True)

    _version_unique = models.Constraint("unique(server_id, name)", "Each version is listed once per panel.")
