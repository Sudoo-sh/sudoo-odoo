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
import re
import secrets
import time
from urllib.parse import quote, urlencode, urlsplit

import requests

API_PREFIX = "/api/v1"
TIMEOUT_SECONDS = 20
MAX_ANSWER_BYTES = 2 * 1024 * 1024  # the largest answer (500 instances) is far smaller
INSTANCE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")  # the panel's own rule for instance names
ACTING_FOR_RE = re.compile(r"[^A-Za-z0-9._@+-]")  # what the panel accepts in X-Sudoo-Acting-For


def instance_path(name):
    """/instances/<name>, refusing anything that is not an instance name (it becomes part of the address)."""
    if not INSTANCE_NAME_RE.match(name or ""):
        raise PanelError("This is not a valid instance name.", kind="bad_name")
    return f"/instances/{quote(name)}"


class PanelError(Exception):
    """The panel refused a request or could not be reached. `kind` names the problem and `values` fill its message;
    sudoo.server._panel_message turns them into the user's language. str() is the English message."""

    def __init__(self, message, status=None, kind=None, **values):
        super().__init__(message)
        self.status = status
        self.kind = kind
        self.values = values


class PanelClient:
    """A signed connection to one panel: PanelClient(url, token, secret).get("/instances")."""

    def __init__(self, url, token, secret, acting_for=None):
        self.url = (url or "").rstrip("/")
        self.token = token or ""
        self.secret = secret or ""
        # the Odoo user behind the call: signed, shown in the panel's audit log and counted in its per-person limits
        self.acting_for = ACTING_FOR_RE.sub("", acting_for or "")[:120] or None

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
            raise PanelError("The panel's address, API token and signing secret are all needed.", kind="incomplete")
        full_path = API_PREFIX + path + (("?" + urlencode(params)) if params else "")
        raw = json.dumps(body, separators=(",", ":")).encode() if body is not None else b""
        headers = self._signed_headers(method, full_path, raw)
        if body is not None:
            headers["Content-Type"] = "application/json"
        host = urlsplit(self.url).netloc
        try:
            # never follow a redirect: the signed request is meant for this panel only
            answer = requests.request(method, self.url + full_path, data=raw or None, headers=headers,
                                      timeout=TIMEOUT_SECONDS, allow_redirects=False, stream=True)
            content = answer.raw.read(MAX_ANSWER_BYTES + 1, decode_content=True) if answer.raw else b""
        except requests.RequestException as error:
            raise PanelError(f"The panel at {host} could not be reached ({error.__class__.__name__}).", kind="unreachable",
                             host=host, reason=error.__class__.__name__) from error
        if len(content) > MAX_ANSWER_BYTES:
            raise PanelError(f"The panel at {host} sent an answer that is too large.", kind="too_large", host=host)
        if 300 <= answer.status_code < 400:
            raise PanelError(f"The panel at {host} answered with a redirect. Check the panel address.", kind="redirect",
                             host=host)
        if answer.status_code == 204:
            return None
        payload = self._json(content)
        if answer.status_code >= 400:
            detail = payload.get("detail") or payload.get("title") or answer.reason
            raise PanelError(f"The panel refused this: {detail}", answer.status_code, kind="refused", detail=detail)
        return payload.get("data")

    # ------------------------------------------------------------------ signing

    def _signed_headers(self, method, full_path, raw):
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(24)
        lines = [timestamp, nonce, method.upper(), full_path, hashlib.sha256(raw).hexdigest()]
        if self.acting_for:
            lines.append(self.acting_for)  # signed too, so nobody can change who the call is made for
        text = "\n".join(lines)
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
    def _json(content):
        try:
            payload = json.loads(content or b"{}")
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}
