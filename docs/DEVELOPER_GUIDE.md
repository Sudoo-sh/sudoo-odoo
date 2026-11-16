# Sudoo.sh for Odoo: Developer Guide

**Audience:** Odoo developers who want Sudoo.sh instances on their own models, or who maintain these modules.

**Covers:** `sudoo_base` on Odoo 20.0: the mixin and its hooks, the buttons, calling the panel, access rules, tests,
code style and licensing. The apps are also published for Odoo 17.0, 18.0 and 19.0 (branches of the same name); this
documentation describes 20.0.

## Contents

1. [How it fits together](#1-how-it-fits-together)
2. [Depend on sudoo_base and inherit the mixin](#2-depend-on-sudoo_base-and-inherit-the-mixin)
3. [Preset the New instance window: `_sudoo_instance_defaults`](#3-preset-the-new-instance-window-_sudoo_instance_defaults)
4. [React when the instance is ready: `_sudoo_on_instance_ready`](#4-react-when-the-instance-is-ready-_sudoo_on_instance_ready)
5. [Add the buttons to your form](#5-add-the-buttons-to-your-form)
6. [Call the panel through `server._call`, never directly](#6-call-the-panel-through-server_call-never-directly)
7. [Access rules for your own models](#7-access-rules-for-your-own-models)
8. [Test with a patched panel client](#8-test-with-a-patched-panel-client)
9. [Licensing](#9-licensing)

## 1. How it fits together

`sudoo_base` owns everything that talks to a Sudoo.sh panel:

| Piece | What it is |
| :--- | :--- |
| `sudoo.server` | A panel: address, API token, signing secret, and what users may create there |
| `sudoo.server.version` | An Odoo version the panel offers, and whether users may create it |
| `sudoo.instance` | An instance on a panel, kept in step every minute by a scheduled action; it has a chatter |
| `sudoo.instance.create` | The New instance window; it checks every rule again on **Create** |
| `sudoo.instance.mixin` | What your model inherits to get instances |
| `services/panel_client.py` | The only code that sends requests: signed, no redirects, size-capped |

An instance remembers the record it was made for in `res_model` and `res_id`. The CRM, Project and Helpdesk apps are
built exactly the way this guide describes; read `sudoo_crm` as the shortest example.

## 2. Depend on sudoo_base and inherit the mixin

Add `sudoo_base` to your manifest's `depends`, then inherit the mixin next to your model:

```python
from odoo import models


class Course(models.Model):
    _name = "school.course"
    _inherit = ["school.course", "sudoo.instance.mixin"]
```

The mixin adds two computed fields, `sudoo_instance_ids` and `sudoo_instance_count`, and two button methods,
`action_sudoo_create_instance` and `action_sudoo_view_instances`. It stores nothing on your table.

## 3. Preset the New instance window: `_sudoo_instance_defaults`

Return the values the window should start with for this record. Any of these keys may be set:

| Key | Meaning |
| :--- | :--- |
| `instance_name` | The name to ask the panel for (empty: the panel names it after the branch or version) |
| `source` | `plain` or `repository` |
| `repository` | A GitHub address, `https://github.com/...` or `git@github.com:...` |
| `branch` | The branch to run (default `main`) |
| `version` | A preferred Odoo version name, such as `20.0`; it is used when the administrator allows it |
| `edition` | `community` or `enterprise` |
| `lifetime_days` | Days before the panel deletes it; above the panel's longest lifetime, the default lifetime is used instead |
| `demo_data` | Load Odoo's demo data (only when the administrator allows it) |
| `install_modules` | Install the repository's modules (repository source only) |

```python
    def _sudoo_instance_defaults(self):
        self.ensure_one()
        return {"instance_name": f"course-{self.id}", "lifetime_days": 30, "demo_data": True}
```

These are only starting values. The window still offers only what the panel record allows, and the user can change
them before clicking **Create**.

## 4. React when the instance is ready: `_sudoo_on_instance_ready`

It is called once, when an instance made for your record goes from Creating to Online or Paused. By default it posts
the link in the record's chatter (when the record has one). Call `super()` to keep that, then add your own step:

```python
    def _sudoo_on_instance_ready(self, instance):
        super()._sudoo_on_instance_ready(instance)
        self.activity_schedule("mail.mail_activity_data_todo", summary="Training instance ready",
                               note=instance.url, user_id=self.user_id.id)
```

It usually runs inside the scheduled sync, not in a user's request. Keep it short and never let it raise for ordinary data: a raise
would stop the sync of that panel for that minute.

## 5. Add the buttons to your form

Inherit your form view and add the header button and the smart button with xpath. Show them to Sudoo.sh users only:

```xml
<record id="school_course_view_form_sudoo" model="ir.ui.view">
    <field name="name">school.course.form.sudoo</field>
    <field name="model">school.course</field>
    <field name="inherit_id" ref="school.course_view_form"/>
    <field name="arch" type="xml">
        <xpath expr="//header" position="inside">
            <button name="action_sudoo_create_instance" type="object" string="Training instance"
                    groups="sudoo_base.group_sudoo_user"/>
        </xpath>
        <xpath expr="//div[@name='button_box']" position="inside">
            <button name="action_sudoo_view_instances" type="object" class="oe_stat_button" icon="deployed_code"
                    groups="sudoo_base.group_sudoo_user" invisible="sudoo_instance_count == 0">
                <field name="sudoo_instance_count" widget="statinfo" string="Instances"/>
            </button>
        </xpath>
    </field>
</record>
```

If your form has no `header` or `button_box`, add them first.

## 6. Call the panel through `server._call`, never directly

Never use `requests` (or any other HTTP library) to reach a panel. Use the panel record:

```python
server = self.env["sudoo.server"].search([], limit=1)
quota = server._call("GET", "/instance-quota")
```

`_call(method, path, params=None, body=None)` signs the request with the panel's token and secret, sends the Odoo
user it is made for, refuses redirects and oversized answers, and turns every refusal into a `UserError` in the
user's language (`_panel_message`), keeping the panel's own detail. Build instance paths with `instance._path()` (it refuses anything that is not a valid instance
name), and change instance records through the module, the way `sudoo.instance` does (`_write_as_module`), after
your own checks. Users only have read access to instances.

## 7. Access rules for your own models

- Give every new model an access line in your module's `security/ir.access.csv`, for `sudoo_base.group_sudoo_user`
  and `sudoo_base.group_sudoo_manager` as fits, and transient models too.
- Keep administrator-only actions (extending, deleting, anything that spends the panel's resources beyond the
  rules) behind a check in Python, not only `groups=` on a button: see `sudoo.instance._check_manager`.
- If your model has `company_id`, add a company record rule like the ones in `sudoo_base/security/ir.access.csv`.
- Never read `token` or `secret` yourself; they are restricted to Sudoo.sh administrators, and `_call` reads them
  with `sudo()` only to sign.

## 8. Test with a patched panel client

Tests must not reach the network. Patch `PanelClient.request` with a function that answers like a panel, the way
`sudoo_base/tests/test_access.py` does:

```python
from unittest.mock import patch

from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.sudoo_base.services.panel_client import PanelClient


def fake_panel(method, path, params=None, body=None):
    if path == "/versions":
        return [{"version": "20.0", "enterprise": True}]
    if path == "/instance-quota":
        return {"instances": 1, "max_instances": 10}
    if method == "POST" and path == "/instances":
        return {"id": "job1", "instance": "course-1"}
    return {}


@tagged("post_install", "-at_install")
class TestCourseInstances(TransactionCase):
    def test_button_presets_the_window(self):
        with patch.object(PanelClient, "request", side_effect=lambda self, *a, **k: fake_panel(*a, **k),
                          autospec=True):
            ...
```

Test as a restricted user (`new_test_user(..., groups="sudoo_base.group_sudoo_user")`) as well as an administrator,
and run your tests with `--test-enable --test-tags /your_module`.

Tests that compare messages should run in English whatever the database language: give the test environment and
test users `lang="en_US"`, as `sudoo_base/tests/test_access.py` does.

Before you push, run `pre-commit run --all-files`: it applies black and ruff (settings in `pyproject.toml`) and checks
XML and YAML files. CI on GitHub runs the same hooks, and installs the apps and runs their tests.

## 9. Licensing

These modules are proprietary software of Sudoo.sh, free to use, under the Odoo Proprietary License v1.0 (OPL-1).
You may build your own modules on top of them and give your module any licence you like (LGPL, MIT or proprietary),
as long as it depends on these modules and does not copy code from them. Improvements to these modules are welcome
as pull requests (see `CONTRIBUTING.md`).

---

<sub>Sudoo.sh for Odoo · Proprietary software of Sudoo.sh, free to use. Odoo is a trademark of Odoo S.A.; Sudoo.sh is
not affiliated with Odoo S.A.</sub>
