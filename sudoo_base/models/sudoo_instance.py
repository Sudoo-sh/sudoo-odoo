# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime, timezone

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from ..services.panel_client import INSTANCE_NAME_RE, PanelError, instance_path

_logger = logging.getLogger(__name__)

STATUSES = [
    ("creating", "Creating"),
    ("starting", "Starting"),
    ("online", "Online"),
    ("busy", "Working"),
    ("paused", "Paused"),
    ("switched_off", "Switched off"),
    ("stopped", "Stopped"),
    ("unknown", "Unknown"),
    ("deleted", "Deleted"),
]
READY = ("online", "paused")  # a creation has finished once the instance reaches one of these


def _utc(text):
    """An ISO time from the panel ("2026-11-16T09:30:00Z") as the naive UTC datetime Odoo stores."""
    if not text:
        return False
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)


class SudooInstance(models.Model):
    """An Odoo instance on a Sudoo.sh panel, kept in step with the panel by a scheduled action."""

    _name = "sudoo.instance"
    _description = "Sudoo.sh instance"
    _inherit = ["mail.thread"]
    _order = "create_date desc, id desc"
    _mail_post_access = "read"  # users only read instances; the module writes them (see _write_as_module)

    name = fields.Char(required=True, readonly=True, tracking=True)
    server_id = fields.Many2one("sudoo.server", required=True, readonly=True, ondelete="cascade")
    company_id = fields.Many2one(related="server_id.company_id", store=True)
    status = fields.Selection(STATUSES, default="creating", readonly=True, tracking=True)
    url = fields.Char(string="Link", readonly=True)
    odoo_version = fields.Char(readonly=True)
    edition = fields.Selection([("community", "Community"), ("enterprise", "Enterprise")], readonly=True)
    source = fields.Selection([("repository", "Repository"), ("plain", "Plain Odoo")], readonly=True)
    repository = fields.Char(readonly=True)
    branch = fields.Char(readonly=True)
    lifetime_days = fields.Integer(readonly=True, help="Deleted automatically this many days after its creation "
                                                       "(a backup is kept); 0 keeps it.")
    panel_created_at = fields.Datetime(string="Created on the panel", readonly=True)
    panel_created_by = fields.Char(readonly=True)
    user_id = fields.Many2one("res.users", string="Requested by", readonly=True, default=lambda self: self.env.user)
    last_job_id = fields.Char(readonly=True)
    # the record the instance was made for (a ticket, an opportunity, a task...), see sudoo.instance.mixin
    res_model = fields.Char(readonly=True, index=True)
    res_id = fields.Many2oneReference(model_field="res_model", readonly=True, index=True)

    _sql_constraints = [
        ("name_server_unique", "unique(server_id, name)", "An instance name is unique per panel."),
    ]

    # ------------------------------------------------------------------ panel calls

    def _path(self):
        self.ensure_one()
        try:
            return instance_path(self.name)
        except PanelError as error:
            raise UserError(str(error)) from error

    def _write_as_module(self, values):
        """Users may only read instances (security/ir.model.access.csv): what changes, the module writes, after the
        checks in the action that asked for it."""
        return self.sudo().write(values)

    def _run(self, action, title, body=None):
        self.check_access_rights("read")
        self.check_access_rule("read")
        for instance in self:
            job = instance.server_id._call("POST", f"{instance._path()}/actions/{action}", body=body or {})
            instance._write_as_module({"status": "busy", "last_job_id": (job or {}).get("id")})
            instance.message_post(body=_("%(title)s requested by %(user)s.", title=title, user=self.env.user.name))
        return True

    def action_open(self):
        self.ensure_one()
        if not (self.url or "").startswith(("https://", "http://")):
            raise UserError(_("This instance has no link yet."))
        return {"type": "ir.actions.act_url", "url": self.url, "target": "new"}

    def action_start(self):
        return self._run("start", _("Start"))

    def action_pause(self):
        return self._run("pause", _("Pause"))

    def action_restart(self):
        return self._run("restart", _("Restart"))

    def action_backup(self):
        return self._run("backup", _("Back up"))

    def _check_manager(self):
        if not self.env.user.has_group("sudoo_base.group_sudoo_manager"):
            raise AccessError(_("Only Sudoo.sh administrators can do this."))

    def action_extend(self):
        """Keep the instance one default lifetime longer."""
        self._check_manager()
        for instance in self:
            server = instance.server_id
            days = instance.lifetime_days + (server.default_lifetime_days or 14)
            if server.max_lifetime_days:
                days = min(days, server.max_lifetime_days)
            data = instance.server_id._call("PATCH", instance._path(), body={"delete_after_days": days})
            instance._apply(data or {})
            instance.message_post(body=_("Lifetime extended to %s days.", days))
        return True

    def action_delete(self):
        self._check_manager()
        for instance in self:
            instance.server_id._call("DELETE", instance._path(), body={"confirm": instance.name})
            instance._write_as_module({"status": "busy"})
            instance.message_post(body=_("Deletion requested by %s; a backup is taken first.", self.env.user.name))
        return True

    def action_open_record(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": self.res_model, "res_id": self.res_id,
                "view_mode": "form", "target": "current"}

    # ------------------------------------------------------------------ keeping in step with the panel

    def _apply(self, data):
        """Copy what the panel says about the instance onto the record."""
        self.ensure_one()
        odoo, git, settings = data.get("odoo") or {}, data.get("git") or {}, data.get("settings") or {}
        values = {
            "status": data.get("status") if data.get("status") in dict(STATUSES) else "unknown",
            "url": data.get("url") if str(data.get("url") or "").startswith(("https://", "http://")) else False,
            "odoo_version": odoo.get("version") or False,
            "edition": odoo.get("edition") or False,
            "source": data.get("source") or False,
            "repository": git.get("repository") or False,
            "branch": git.get("branch") or False,
            "lifetime_days": settings.get("delete_after_days") or 0,
            "panel_created_at": _utc(data.get("created_at")),
            "panel_created_by": data.get("created_by") or False,
        }
        was_creating = self.status == "creating"
        self._write_as_module({key: value for key, value in values.items() if self[key] != value})
        if was_creating and self.status in READY:
            self._notify_ready()

    def _notify_ready(self):
        """Tell the record the instance was made for (sudoo.instance.mixin) that it is ready."""
        self.ensure_one()
        self.message_post(body=_("Ready: %s", self.url or self.name))
        if self.res_model and self.res_id and self.res_model in self.env:
            record = self.env[self.res_model].browse(self.res_id).exists()
            if record and hasattr(record, "_sudoo_on_instance_ready"):
                record._sudoo_on_instance_ready(self)

    @api.model
    def _sync_servers(self, servers):
        for server in servers:
            listed = server._call("GET", "/instances", params={"limit": 500}) or []
            known = {instance.name: instance for instance in self.with_context(active_test=False).search(
                [("server_id", "=", server.id)])}
            for data in listed:
                if not isinstance(data, dict) or not INSTANCE_NAME_RE.match(str(data.get("name") or "")):
                    continue  # never store what is not an instance of the panel
                instance = known.pop(data["name"], None) or self.sudo().create({"name": data["name"], "server_id": server.id,
                                                                          "user_id": False, "status": "unknown"})
                instance._apply(data)
            for gone in known.values():
                if gone.status != "deleted":
                    gone._write_as_module({"status": "deleted", "url": False})

    @api.model
    def _cron_sync(self):
        for server in self.env["sudoo.server"].search([]):
            try:
                self._sync_servers(server)
            except (PanelError, UserError) as error:
                _logger.warning("Sudoo.sh: could not read the instances of %s: %s", server.name, error)
