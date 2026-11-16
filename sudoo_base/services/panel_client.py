# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
"""The only place that talks to a Sudoo.sh panel.

Every request is signed as the panel's API expects (docs/PANEL_API.md, "Signing a request"):
an API token, a timestamp, a one-time nonce and an HMAC-SHA256 signature over the method,
the path and the body. Answers are {"data": ..., "meta": ...}; errors are problem details
({"title", "detail"}), turned into PanelError with the panel's own message.
"""

import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import urlencode, urlsplit

import requests

API_PREFIX = "/api/v1"
TIMEOUT_SECONDS = 20


class PanelError(Exception):
    """The panel refused a request or could not be reached. The message is meant for users."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class PanelClient:
    """A signed connection to one panel: PanelClient(url, token, secret).get("/instances")."""

    def __init__(self, url, token, secret, acting_for=None):
        self.url = (url or "").rstrip("/")
        self.token = token or ""
        self.secret = secret or ""
        self.acting_for = acting_for  # the Odoo user behind the call, for the panel's audit log

    # ------------------------------------------------------------------ requests

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def post(self, path, body=None):
        return self.request("POST", path, body=body or {})

    def patch(self, path, body):
        return self.request("PATCH", path, body=body)

    def delete(self, path, body=None):
        return self.request("DELETE", path, body=body)

    def request(self, method, path, params=None, body=None):
        """Send a signed request to API_PREFIX + path; returns the answer's "data" (None for 204)."""
        if not (self.url and self.token and self.secret):
            raise PanelError("The panel's address, API token and signing secret are all needed.")
        full_path = API_PREFIX + path + (("?" + urlencode(params)) if params else "")
        raw = json.dumps(body, separators=(",", ":")).encode() if body is not None else b""
        headers = self._signed_headers(method, full_path, raw)
        if body is not None:
            headers["Content-Type"] = "application/json"
        try:
            answer = requests.request(method, self.url + full_path, data=raw or None, headers=headers,
                                      timeout=TIMEOUT_SECONDS)
        except requests.RequestException as error:
            raise PanelError(f"The panel at {urlsplit(self.url).netloc} could not be reached ({error.__class__.__name__}).") from error
        if answer.status_code == 204:
            return None
        payload = self._json(answer)
        if answer.status_code >= 400:
            detail = payload.get("detail") or payload.get("title") or answer.reason
            raise PanelError(f"The panel refused this: {detail}", answer.status_code)
        return payload.get("data")

    # ------------------------------------------------------------------ signing

    def _signed_headers(self, method, full_path, raw):
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(24)
        text = "\n".join((timestamp, nonce, method.upper(), full_path, hashlib.sha256(raw).hexdigest()))
        signature = hmac.new(self.secret.encode(), text.encode(), hashlib.sha256).hexdigest()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Sudoo-Timestamp": timestamp,
            "X-Sudoo-Nonce": nonce,
            "X-Sudoo-Signature": f"sha256={signature}",
            "Accept": "application/json",
        }
        if self.acting_for:
            headers["X-Sudoo-Acting-For"] = self.acting_for
        return headers

    @staticmethod
    def _json(answer):
        try:
            payload = answer.json()
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}
