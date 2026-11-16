<p align="center">
  <a href="https://sudoo.sh"><img src="sudoo_base/static/description/icon.png" alt="Sudoo.sh" width="80" height="80"></a>
</p>

<h1 align="center">Sudoo.sh for Odoo</h1>

<p align="center">Create and manage your <a href="https://github.com/Sudoo-sh/sudoo.sh">Sudoo.sh</a> Odoo instances
(demos, test branches, training) from inside your company's own Odoo.</p>

> [!NOTE]
> **Proprietary software of Sudoo.sh, free to use.** Licensed under the Odoo Proprietary License v1.0
> ([LICENSE](LICENSE), [COPYRIGHT](COPYRIGHT)). You may install and use these modules and build your own modules
> on top of them. You may not publish, redistribute or sell copies of them, changed or not. Improvements are
> welcome as pull requests: see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contents

1. [The apps](#the-apps)
2. [Installing](#installing)
3. [Connecting your panel](#connecting-your-panel)
4. [Using it](#using-it)
5. [Adding instances to your own models](#adding-instances-to-your-own-models)
6. [Versions](#versions)

## The apps

Install only what you need; each app installs `Sudoo.sh` (the base) with it.

| App | Technical name | Adds | Needs |
| :--- | :--- | :--- | :--- |
| **Sudoo.sh** | `sudoo_base` | Panels, the instance list, the **New instance** wizard, Start, Pause, Restart, Back up, Extend, Delete | nothing |
| **Sudoo.sh for Helpdesk** | `sudoo_helpdesk` | A **Test instance** button on tickets | Helpdesk (Odoo Enterprise) |
| **Sudoo.sh for CRM** | `sudoo_crm` | A **Create demo** button on opportunities | CRM |
| **Sudoo.sh for Project** | `sudoo_project` | A **Test instance** button on tasks | Project |

Every record with instances shows an **Instances** smart button, and the link is posted in its chatter when the
instance is ready.

## Installing

From the Odoo Apps store: search for **Sudoo.sh** and install the apps you want.

From this repository: put the folders of the branch matching your Odoo version (for example `19.0`) in an add-ons
path, update the apps list and install them.

```bash
git clone -b 19.0 https://github.com/Sudoo-sh/sudoo-odoo.git
```

## Connecting your panel

1. In the Sudoo.sh panel: **API tokens**, **Create token**, scope **write**. The panel shows the token and its
   signing secret once.
2. In Odoo: **Sudoo.sh → Configuration → Panels → New**. Enter the panel's address, the token and the signing
   secret, then click **Test connection**.
3. Give people access in **Settings → Users**, under **Sudoo.sh**:
   - **User**: sees the company's instances, creates instances, starts, pauses, restarts and backs them up.
   - **Administrator**: also connects panels, extends lifetimes and deletes instances.

The token and the secret are visible to administrators only. Odoo's admin passwords of the instances are never
copied into Odoo.

## Using it

- **Sudoo.sh → New instance**: plain Odoo, or a branch of a GitHub repository; version, edition, lifetime.
- **Sudoo.sh → Instances**: every instance of your panels, refreshed every minute, with Open, Start, Pause,
  Restart, Back up, Extend lifetime and Delete (a backup is always taken first).
- With the other apps: **Test instance** on a ticket or task, **Create demo** on an opportunity. The new instance
  is linked to that record.

## Adding instances to your own models

Any model can get instances in a few lines. Depend on `sudoo_base`, inherit the mixin and add the buttons:

```python
from odoo import models


class Course(models.Model):
    _name = "school.course"
    _inherit = ["school.course", "sudoo.instance.mixin"]

    def _sudoo_instance_defaults(self):
        """What the New instance wizard starts with for this record."""
        return {"instance_name": f"course-{self.id}", "lifetime_days": 30, "demo_data": True}

    def _sudoo_on_instance_ready(self, instance):
        """Called once when the instance is ready; by default the link is posted in the chatter."""
        super()._sudoo_on_instance_ready(instance)
```

```xml
<xpath expr="//header" position="inside">
    <button name="action_sudoo_create_instance" type="object" string="Training instance"
            groups="sudoo_base.group_sudoo_user"/>
</xpath>
<xpath expr="//div[@name='button_box']" position="inside">
    <button name="action_sudoo_view_instances" type="object" class="oe_stat_button" icon="fa-server"
            invisible="sudoo_instance_count == 0">
        <field name="sudoo_instance_count" widget="statinfo" string="Instances"/>
    </button>
</xpath>
```

Wizard fields you can preset: `instance_name`, `source` (`plain` or `repository`), `repository`, `branch`,
`version`, `edition`, `lifetime_days`, `demo_data`, `install_modules`. The Helpdesk, CRM and Project apps are
built exactly this way; read them as examples.

Your own module may use any licence compatible with the Odoo Proprietary License (LGPL, MIT or proprietary), as
long as it does not copy code from these modules.

## Versions

One branch per Odoo version: `19.0` (first), then `20.0`, `18.0` and `17.0`. The panel itself runs Odoo 16.0 and
later.

---

<sub>Copyright (c) 2026 Sudoo.sh. Odoo is a trademark of Odoo S.A.; Sudoo.sh is not affiliated with Odoo S.A.</sub>
