# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, new_test_user, tagged

from ..services.panel_client import PanelClient


def fake_panel(method, path, params=None, body=None):
    """What a panel answers, without a network."""
    if path == "/versions":
        return [{"version": "20.0", "enterprise": True}, {"version": "19.0", "enterprise": False}]
    if path == "/instance-quota":
        return {"instances": 3, "max_instances": 10}
    if method == "POST" and path == "/instances":
        fake_panel.sent = body
        return {"id": "job1", "instance": "sales-demo"}
    return {}


@tagged("post_install", "-at_install")
class TestAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))  # messages are checked in English
        cls.server = cls.env["sudoo.server"].create({
            "name": "Panel", "url": "https://panel.example.com", "token": "t", "secret": "s",
            "allow_repository": False, "allow_demo_data": False, "max_lifetime_days": 30, "default_lifetime_days": 7,
            "max_instances_per_user": 1,
        })
        with patch.object(PanelClient, "request", side_effect=lambda self, *a, **k: fake_panel(*a, **k), autospec=True):
            cls.server._refresh_versions()
        cls.server.version_ids.filtered(lambda line: line.name == "19.0").allowed = False
        cls.user = new_test_user(cls.env, login="seller", groups="sudoo_base.group_sudoo_user", lang="en_US")
        cls.outsider = new_test_user(cls.env, login="outsider", groups="base.group_user", lang="en_US")

    def wizard(self, user=None, **values):
        env = self.env(user=user or self.user)
        form = Form(env["sudoo.instance.create"])
        for key, value in values.items():
            setattr(form, key, value)
        return form

    def run_create(self, wizard):
        with patch.object(PanelClient, "request", side_effect=lambda self, *a, **k: fake_panel(*a, **k), autospec=True):
            return wizard.action_create()

    def test_form_offers_only_what_is_allowed(self):
        with patch.object(PanelClient, "request", side_effect=lambda self, *a, **k: fake_panel(*a, **k), autospec=True):
            form = self.wizard()
            self.assertEqual(form.source, "plain")
            self.assertEqual(form.version_id.name, "20.0")
            self.assertEqual(form.lifetime_days, 7)
            self.assertTrue(form.enterprise_possible)
            self.assertIn("Not allowed by your administrator", form.policy_html)
            self.assertIn("7 more of its 10", form.policy_html)
            wizard = form.save()
        self.run_create(wizard)
        self.assertEqual(fake_panel.sent["version"], "20.0")
        instance = self.env["sudoo.instance"].search([("name", "=", "sales-demo")])
        self.assertEqual(instance.user_id, self.user)

    def test_refuses_what_the_administrator_does_not_allow(self):
        with patch.object(PanelClient, "request", side_effect=lambda self, *a, **k: fake_panel(*a, **k), autospec=True):
            wizard = self.wizard().save()
        for values, message in (
            ({"source": "repository", "repository": "https://github.com/acme/x"}, "does not allow this kind"),
            ({"demo_data": True}, "does not allow demo data"),
            ({"lifetime_days": 0}, "between 1 and 30"),
            ({"lifetime_days": 31}, "between 1 and 30"),
            ({"version_id": self.server.version_ids.filtered(lambda l: l.name == "19.0").id}, "versions your administrator allows"),
        ):
            with self.subTest(values=values):
                attempt = wizard
                attempt.write(values)
                with self.assertRaisesRegex(UserError, message):
                    self.run_create(attempt)
                attempt.write({"source": "plain", "demo_data": False, "lifetime_days": 7,
                               "version_id": self.server.version_ids.filtered(lambda l: l.name == "20.0").id})

    def test_one_instance_per_person(self):
        with patch.object(PanelClient, "request", side_effect=lambda self, *a, **k: fake_panel(*a, **k), autospec=True):
            first = self.wizard().save()
            second = self.wizard().save()
        self.run_create(first)
        with self.assertRaisesRegex(UserError, "the most one person may have"):
            self.run_create(second)

    def test_users_only_read_instances_and_secrets_stay_hidden(self):
        instance = self.env["sudoo.instance"].create({"name": "x", "server_id": self.server.id})
        with self.assertRaises(AccessError):
            instance.with_user(self.user).write({"url": "javascript:alert(1)"})
        with self.assertRaises(AccessError):
            instance.with_user(self.user).action_delete()
        with self.assertRaises(AccessError):
            self.server.with_user(self.user).read(["token"])
        with self.assertRaises(AccessError):
            self.env["sudoo.instance"].with_user(self.outsider).search([])

    def test_panel_address_must_be_https(self):
        with self.assertRaises(ValidationError):
            self.env["sudoo.server"].create({"name": "Bad", "url": "http://panel.example.com"})
        self.env["sudoo.server"].create({"name": "Local", "url": "http://localhost:9000"})

    def test_links_other_than_http_are_dropped(self):
        instance = self.env["sudoo.instance"].create({"name": "y", "server_id": self.server.id, "status": "unknown"})
        instance._apply({"status": "online", "url": "javascript:alert(1)"})
        self.assertFalse(instance.url)
