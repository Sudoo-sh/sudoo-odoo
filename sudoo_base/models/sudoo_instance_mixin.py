# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
"""sudoo.instance.mixin: what any model inherits to get a New instance button and an Instances smart button."""

from odoo import _, fields, models


class SudooInstanceMixin(models.AbstractModel):
    """Give any model Sudoo.sh instances: inherit this mixin, then add the buttons to its form.

        class HelpdeskTicket(models.Model):
            _name = "helpdesk.ticket"
            _inherit = ["helpdesk.ticket", "sudoo.instance.mixin"]

            def _sudoo_instance_defaults(self):
                return {"instance_name": f"ticket-{self.id}"}

    Form buttons: `action_sudoo_create_instance` (opens the create wizard for this record) and a
    smart button on `action_sudoo_view_instances` showing `sudoo_instance_count`.
    """

    _name = "sudoo.instance.mixin"
    _description = "Records that can have Sudoo.sh instances"

    sudoo_instance_ids = fields.One2many(
        "sudoo.instance", compute="_compute_sudoo_instances", string="Sudoo.sh instances"
    )
    sudoo_instance_count = fields.Integer(compute="_compute_sudoo_instances", string="Instances")

    def _compute_sudoo_instances(self):
        """The instances made for each record, found by res_model/res_id in one search for the whole batch."""
        found = self.env["sudoo.instance"].search([("res_model", "=", self._name), ("res_id", "in", self.ids)])
        for record in self:
            mine = found.filtered(lambda instance, record_id=record.id: instance.res_id == record_id)
            record.sudoo_instance_ids = mine
            record.sudoo_instance_count = len(mine)

    # ------------------------------------------------------------------ hooks to override

    def _sudoo_instance_defaults(self):
        """Values the create wizard starts with for this record (any wizard field: instance_name,
        source, repository, branch, version, edition, lifetime_days, demo_data). Override it."""
        self.ensure_one()
        return {}

    def _sudoo_on_instance_ready(self, instance):
        """Called once when an instance made for this record is ready. By default the link is posted
        in the record's chatter when it has one. Override it to e-mail a customer, move a stage..."""
        self.ensure_one()
        if hasattr(self, "message_post"):
            self.message_post(
                body=_("The Sudoo.sh instance %(name)s is ready: %(url)s", name=instance.name, url=instance.url or "-")
            )

    # ------------------------------------------------------------------ buttons

    def action_sudoo_create_instance(self):
        """Button: open the New instance wizard for this record.

        The wizard starts with _sudoo_instance_defaults() and remembers the record, so the instance is linked
        to it and the record is told when it is ready.
        """
        self.ensure_one()
        context = {f"default_{key}": value for key, value in self._sudoo_instance_defaults().items()}
        context.update(default_res_model=self._name, default_res_id=self.id)
        return {
            "type": "ir.actions.act_window",
            "name": _("New instance"),
            "res_model": "sudoo.instance.create",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    def action_sudoo_view_instances(self):
        """Smart button: the instance list, filtered to this record's instances."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("sudoo_base.action_sudoo_instance")
        action["domain"] = [("res_model", "=", self._name), ("res_id", "=", self.id)]
        action["context"] = {"create": False}
        return action
