# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
"""The panel client: request signing, refused redirects and large answers, the panel's error messages,
and the ready notification. requests.request is patched, so no network is used.
"""

import hashlib
import hmac
import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from ..services.panel_client import PanelClient, PanelError, instance_path


class FakeRaw:
    """Stands in for the raw stream of a requests answer."""

    def __init__(self, content):
        """Keep the bytes the stream returns."""
        self.content = content

    def read(self, size, decode_content=True):
        """At most `size` bytes, like urllib3's read."""
        return self.content[:size]


class FakeAnswer:
    """Stands in for a requests answer with a status and a JSON (or raw) body."""

    def __init__(self, status, payload, content=None):
        """Answer `status` with `payload` as JSON, or `content` as is."""
        self.status_code, self.reason = status, "Reason"
        self.raw = FakeRaw(content if content is not None else json.dumps(payload).encode())


@tagged("post_install", "-at_install")
class TestPanelClient(TransactionCase):
    """The panel client and the ready notification, without a network."""

    def test_signature_follows_the_panel_api(self):
        """The URL, bearer token, acting-for header and HMAC signature match the panel API's rules."""
        client = PanelClient("https://panel.example.com/", "sudoo_token", "secret", acting_for="jane")
        with patch("requests.request", return_value=FakeAnswer(200, {"data": []})) as sent:
            self.assertEqual(client.get("/instances", params={"limit": 5}), [])
        method, url = sent.call_args.args
        headers = sent.call_args.kwargs["headers"]
        self.assertEqual((method, url), ("GET", "https://panel.example.com/api/v1/instances?limit=5"))
        text = "\n".join(
            (
                headers["X-Sudoo-Timestamp"],
                headers["X-Sudoo-Nonce"],
                "GET",
                "/api/v1/instances?limit=5",
                hashlib.sha256(b"").hexdigest(),
                "jane",
            )
        )
        expected = "sha256=" + hmac.new(b"secret", text.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(headers["X-Sudoo-Signature"], expected)
        self.assertEqual(headers["Authorization"], "Bearer sudoo_token")
        self.assertEqual(headers["X-Sudoo-Acting-For"], "jane")

    def test_redirects_large_answers_and_bad_names_are_refused(self):
        """Redirects and oversized answers raise PanelError, redirects are never followed, and bad instance names
        never reach the address.
        """
        client = PanelClient("https://panel.example.com", "t", "s", acting_for="Jane Doe <x>")
        self.assertEqual(client.acting_for, "JaneDoex")
        with (
            patch("requests.request", return_value=FakeAnswer(302, {})),
            self.assertRaisesRegex(PanelError, "redirect"),
        ):
            client.get("/versions")
        with (
            patch("requests.request", return_value=FakeAnswer(200, None, b"x" * (3 * 1024 * 1024))),
            self.assertRaisesRegex(PanelError, "too large"),
        ):
            client.get("/instances")
        with patch("requests.request", return_value=FakeAnswer(200, {"data": []})) as sent:
            client.get("/versions")
        self.assertFalse(sent.call_args.kwargs["allow_redirects"])
        for bad in ("../tokens", "a/b", "", "UPPER", "x" * 40):
            with self.assertRaises(PanelError):
                instance_path(bad)

    def test_refusal_carries_the_panel_message(self):
        """A 4xx answer raises PanelError with the panel's detail."""
        client = PanelClient("https://panel.example.com", "t", "s")
        answer = FakeAnswer(409, {"title": "Conflict", "detail": "This instance is still being created."})
        with patch("requests.request", return_value=answer), self.assertRaises(PanelError) as raised:
            client.post("/instances/x/actions/restart")
        self.assertIn("still being created", str(raised.exception))
        self.assertEqual(raised.exception.status, 409)

    def test_ready_instance_notifies_its_record(self):
        """When a creating instance comes online, its link is posted on the instance."""
        server = self.env["sudoo.server"].create({"name": "Panel", "url": "https://panel.example.com"})
        partner = self.env["res.partner"].create({"name": "Prospect"})
        instance = self.env["sudoo.instance"].create(
            {"name": "demo", "server_id": server.id, "res_model": "res.partner", "res_id": partner.id}
        )
        instance._apply({"status": "online", "url": "https://demo.example.com", "odoo": {"version": "19.0"}})
        self.assertEqual(instance.status, "online")
        self.assertIn("https://demo.example.com", instance.message_ids[0].body)
