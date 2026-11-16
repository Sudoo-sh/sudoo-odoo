# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
import re

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

PANEL_NAME_RE = re.compile(r"[^A-Za-z0-9 ._-]+")  # what the panel accepts in a name


class SudooInstanceCreate(models.TransientModel):
    """Ask a panel for a new instance. The choices offered follow what the administrator allows on the panel's
    record in Odoo (sudoo.server) and what the panel itself offers; action_create checks them all again."""

    _name = "sudoo.instance.create"
    _description = "New Sudoo.sh instance"

    server_id = fields.Many2one("sudoo.server", string="Panel", required=True,
                                default=lambda self: self.env["sudoo.server"].search([], limit=1))
    source = fields.Selection([("plain", "Plain Odoo"), ("repository", "From a GitHub repository")], required=True)
    repository = fields.Char(help="For example https://github.com/acme/odoo-addons")
    branch = fields.Char(default="main")
    instance_name = fields.Char(string="Name", help="Empty: the panel names it after the branch or the version.")
    version = fields.Char(string="Preferred version", help="A version name to start with, such as 20.0 (presets).")
    version_id = fields.Many2one("sudoo.server.version", string="Odoo version",
                                 domain="[('server_id', '=', server_id), ('allowed', '=', True)]")
    edition = fields.Selection([("community", "Community"), ("enterprise", "Enterprise")],
                               default="community", required=True)
    lifetime_days = fields.Integer(string="Lifetime (days)", help="0 keeps it until it is deleted by hand.")
    demo_data = fields.Boolean(string="Load demo data")
    install_modules = fields.Boolean(string="Install the repository's modules", default=True)
    res_model = fields.Char()
    res_id = fields.Many2oneReference(model_field="res_model")

    # what the form shows and hides, from the panel's record
    allow_plain = fields.Boolean(related="server_id.allow_plain")
    allow_repository = fields.Boolean(related="server_id.allow_repository")
    allow_demo_data = fields.Boolean(related="server_id.allow_demo_data")
    enterprise_possible = fields.Boolean(compute="_compute_policy")
    policy_html = fields.Html(compute="_compute_policy", sanitize=False)

    # ------------------------------------------------------------------ defaults and what is allowed

    @api.onchange("server_id")
    def _onchange_server_id(self):
        server = self.server_id
        if not server:
            return
        if not server.version_ids:
            server.sudo()._refresh_versions()
        if self.source not in self._allowed_sources():
            self.source = (self._allowed_sources() or [False])[0]
        if not self.version_id or self.version_id.server_id != server or not self.version_id.allowed:
            allowed = server.version_ids.filtered("allowed")
            self.version_id = allowed.filtered(lambda line: line.name == self.version)[:1] or allowed[:1]
        if not self.lifetime_days or (server.max_lifetime_days and self.lifetime_days > server.max_lifetime_days):
            self.lifetime_days = server.default_lifetime_days
        if not server.allow_demo_data:
            self.demo_data = False

    @api.onchange("version_id")
    def _onchange_version_id(self):
        if self.edition == "enterprise" and not self.enterprise_possible:
            self.edition = "community"

    def _allowed_sources(self):
        server = self.server_id
        return [source for source, allowed in (("plain", server.allow_plain), ("repository", server.allow_repository))
                if allowed]

    @api.depends("server_id", "version_id")
    def _compute_policy(self):
        for wizard in self:
            server = wizard.server_id
            wizard.enterprise_possible = bool(server.allow_enterprise and wizard.version_id.enterprise_available)
            wizard.policy_html = wizard._policy_html() if server else False

    def _policy_html(self):
        """What the administrator allows and what the panel still accepts, in a few lines for the form."""
        server = self.server_id
        allowed, refused = [], []
        for label, ok in ((_("Plain Odoo"), server.allow_plain), (_("GitHub repositories"), server.allow_repository),
                          (_("Enterprise"), server.allow_enterprise), (_("Demo data"), server.allow_demo_data)):
            (allowed if ok else refused).append(label)
        versions = server.version_ids.filtered("allowed").mapped("name")
        lines = [_("Allowed: %s.", ", ".join(allowed) or _("nothing"))]
        if refused:
            lines.append(_("Not allowed by your administrator: %s.", ", ".join(refused)))
        lines.append(_("Odoo versions: %s.", ", ".join(versions) or _("none allowed")))
        lines.append(_("Lifetime: at most %s days.", server.max_lifetime_days) if server.max_lifetime_days
                     else _("Lifetime: no limit; 0 keeps the instance."))
        if server.max_instances_per_user:
            mine = self.env["sudoo.instance"].search_count(self._own_open_domain())
            lines.append(_("You have %(mine)s of the %(max)s instances one person may have.",
                           mine=mine, max=server.max_instances_per_user))
        quota = self._panel_quota()
        if quota:
            lines.append(quota)
        return Markup("<br/>").join(escape(line) for line in lines)

    def _panel_quota(self):
        """The panel's own limit, when it has one (a short sentence), or "" when it cannot be read."""
        try:
            usage = self.server_id._call("GET", "/instance-quota") or {}
        except UserError:
            return ""
        if usage.get("max_instances"):
            left = max(usage["max_instances"] - usage.get("instances", 0), 0)
            return _("The panel can take %(left)s more of its %(max)s instances.", left=left, max=usage["max_instances"])
        return ""

    def _own_open_domain(self):
        return [("server_id", "=", self.server_id.id), ("user_id", "=", self.env.user.id),
                ("status", "not in", ("deleted",))]

    def _check_policy(self):
        """Refuse anything the administrator does not allow, whatever the form sent."""
        self.ensure_one()
        server = self.server_id
        if not self.env.user.has_group("sudoo_base.group_sudoo_user"):
            raise AccessError(_("You need the Sudoo.sh User access to create instances."))
        if self.source not in self._allowed_sources():
            raise UserError(_("Your administrator does not allow this kind of instance on %s.", server.name))
        if self.source == "repository" and not (self.repository or "").startswith(("https://github.com/", "git@github.com:")):
            raise UserError(_("Enter the GitHub repository's address, for example https://github.com/acme/odoo-addons."))
        if not self.version_id or self.version_id.server_id != server or not self.version_id.allowed:
            raise UserError(_("Choose one of the Odoo versions your administrator allows."))
        if self.edition == "enterprise" and not (server.allow_enterprise and self.version_id.enterprise_available):
            raise UserError(_("Enterprise is not available for Odoo %s here.", self.version_id.name))
        if self.demo_data and not server.allow_demo_data:
            raise UserError(_("Your administrator does not allow demo data."))
        if self.lifetime_days < 0 or (server.max_lifetime_days and not 0 < self.lifetime_days <= server.max_lifetime_days):
            raise UserError(_("The lifetime must be between 1 and %s days.", server.max_lifetime_days)
                            if server.max_lifetime_days else _("The lifetime cannot be negative."))
        if server.max_instances_per_user and self.env["sudoo.instance"].search_count(
                self._own_open_domain()) >= server.max_instances_per_user:
            raise UserError(_("You already have %s instances, the most one person may have. Delete one first.",
                              server.max_instances_per_user))

    # ------------------------------------------------------------------ creating

    def _panel_body(self):
        self.ensure_one()
        body = {
            "version": self.version_id.name,
            "edition": self.edition,
            "delete_after_days": self.lifetime_days,
            "demo": self.demo_data,
        }
        name = PANEL_NAME_RE.sub(" ", self.instance_name or "").strip()[:40]
        if name:
            body["name"] = name
        if self.source == "repository":
            body.update(repo=self.repository.strip(), branch=(self.branch or "main").strip(),
                        install_modules=self.install_modules)
        return body

    def action_create(self):
        self.ensure_one()
        self._check_policy()
        job = self.server_id._call("POST", "/instances", body=self._panel_body()) or {}
        # users only read instances; the record is written by the module, for the user who asked
        instance = self.env["sudoo.instance"].sudo().create({
            "name": job.get("instance") or self.instance_name or _("new instance"),
            "server_id": self.server_id.id,
            "user_id": self.env.user.id,
            "status": "creating",
            "last_job_id": job.get("id"),
            "odoo_version": self.version_id.name,
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
