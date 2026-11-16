# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
import hashlib
import hmac
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from ..services.panel_client import PanelClient, PanelError


class FakeAnswer:
    def __init__(self, status, payload):
        self.status_code, self._payload, self.reason = status, payload, "Reason"

    def json(self):
        return self._payload


@tagged("post_install", "-at_install")
class TestPanelClient(TransactionCase):
    def test_signature_follows_the_panel_api(self):
        client = PanelClient("https://panel.example.com/", "sudoo_token", "secret", acting_for="jane")
        with patch("requests.request", return_value=FakeAnswer(200, {"data": []})) as sent:
            self.assertEqual(client.get("/instances", params={"limit": 5}), [])
        method, url = sent.call_args.args
        headers = sent.call_args.kwargs["headers"]
        self.assertEqual((method, url), ("GET", "https://panel.example.com/api/v1/instances?limit=5"))
        text = "\n".join((headers["X-Sudoo-Timestamp"], headers["X-Sudoo-Nonce"], "GET",
                          "/api/v1/instances?limit=5", hashlib.sha256(b"").hexdigest()))
        expected = "sha256=" + hmac.new(b"secret", text.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(headers["X-Sudoo-Signature"], expected)
        self.assertEqual(headers["Authorization"], "Bearer sudoo_token")
        self.assertEqual(headers["X-Sudoo-Acting-For"], "jane")

    def test_refusal_carries_the_panel_message(self):
        client = PanelClient("https://panel.example.com", "t", "s")
        answer = FakeAnswer(409, {"title": "Conflict", "detail": "This instance is still being created."})
        with patch("requests.request", return_value=answer), self.assertRaises(PanelError) as raised:
            client.post("/instances/x/actions/restart")
        self.assertIn("still being created", str(raised.exception))
        self.assertEqual(raised.exception.status, 409)

    def test_ready_instance_notifies_its_record(self):
        server = self.env["sudoo.server"].create({"name": "Panel", "url": "https://panel.example.com"})
        partner = self.env["res.partner"].create({"name": "Prospect"})
        instance = self.env["sudoo.instance"].create({"name": "demo", "server_id": server.id,
                                                     "res_model": "res.partner", "res_id": partner.id})
        instance._apply({"status": "online", "url": "https://demo.example.com", "odoo": {"version": "19.0"}})
        self.assertEqual(instance.status, "online")
        self.assertIn("https://demo.example.com", instance.message_ids[0].body)
