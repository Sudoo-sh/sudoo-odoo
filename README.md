<p align="center">
  <a href="https://sudoo.sh"><img src="sudoo_base/static/description/icon.png" alt="Sudoo.sh" width="80" height="80"></a>
</p>

<h1 align="center">Sudoo.sh for Odoo</h1>

<p align="center">Create and manage your <a href="https://github.com/Sudoo-sh/sudoo.sh">Sudoo.sh</a> Odoo instances
(demos, test branches, training) from inside your company's own Odoo.</p>

<p align="center">
  <a href="https://github.com/Sudoo-sh/sudoo-odoo/actions/workflows/ci.yml?query=branch%3A20.0"><img alt="CI" src="https://github.com/Sudoo-sh/sudoo-odoo/actions/workflows/ci.yml/badge.svg?branch=20.0"></a>
  <img alt="Odoo 17.0 | 18.0 | 19.0 | 20.0" src="https://img.shields.io/badge/Odoo-17.0%20%7C%2018.0%20%7C%2019.0%20%7C%2020.0-714B67">
  <a href="https://apps.odoo.com/apps/modules/20.0/sudoo_base"><img alt="Odoo Apps store" src="https://img.shields.io/badge/Odoo%20Apps-get%20it%20free-714B67"></a>
  <a href="LICENSE"><img alt="License: OPL-1" src="https://img.shields.io/badge/license-OPL--1-4A2F43"></a>
  <img alt="Price: free" src="https://img.shields.io/badge/price-free-2F6B4F">
  <img alt="Languages: English, Arabic" src="https://img.shields.io/badge/languages-English%20%7C%20%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-5E5560">
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000"></a>
  <a href="https://github.com/astral-sh/ruff"><img alt="Linted with ruff" src="https://img.shields.io/badge/lint-ruff-D7FF64"></a>
</p>

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

Install only what you need; each app installs the Instance Manager (`sudoo_base`) with it.

| App (on the store) | Technical name | Adds | Needs |
| :--- | :--- | :--- | :--- |
| [**Sudoo.sh Instance Manager**](https://apps.odoo.com/apps/modules/20.0/sudoo_base) | `sudoo_base` | Panels, what users may create, the instance list, the **New instance** wizard, Start, Pause, Restart, Back up, Extend, Delete | nothing |
| [**Sudoo.sh Helpdesk Tests**](https://apps.odoo.com/apps/modules/20.0/sudoo_helpdesk) | `sudoo_helpdesk` | A **Test instance** button on tickets | Helpdesk (Odoo Enterprise) |
| [**Sudoo.sh CRM Demos**](https://apps.odoo.com/apps/modules/20.0/sudoo_crm) | `sudoo_crm` | A **Create demo** button on opportunities | CRM |
| [**Sudoo.sh Project Tests**](https://apps.odoo.com/apps/modules/20.0/sudoo_project) | `sudoo_project` | A **Test instance** button on tasks | Project |

Every record with instances shows an **Instances** smart button, and the link is posted in its chatter when the
instance is ready. The interface is available in English and Arabic.

**Documentation:** [User manual](docs/USER_MANUAL.md) · [Developer guide](docs/DEVELOPER_GUIDE.md) · PDFs in
[docs/](docs) (user manual in English and Arabic, technical overview, completeness checklist).

## Installing

From the Odoo Apps store (free): [Instance Manager](https://apps.odoo.com/apps/modules/20.0/sudoo_base), [CRM Demos](https://apps.odoo.com/apps/modules/20.0/sudoo_crm),
[Project Tests](https://apps.odoo.com/apps/modules/20.0/sudoo_project) and [Helpdesk Tests](https://apps.odoo.com/apps/modules/20.0/sudoo_helpdesk), or
[all Sudoo.sh apps](https://apps.odoo.com/apps/modules/browse?author=Sudoo.sh). Each store page switches between
Odoo 17.0, 18.0, 19.0 and 20.0.

From this repository: put the folders of the branch matching your Odoo version (for example `20.0`) in an add-ons
path, update the apps list and install them.

```bash
git clone -b 20.0 https://github.com/Sudoo-sh/sudoo-odoo.git
```

## Connecting your panel

1. In the Sudoo.sh panel: **API tokens**, **Create token**, scope **Instances**. That scope can only list, create,
   start, pause, restart, back up, extend and delete instances: never passwords, logs, backups, accounts or
   settings. The panel shows the token and its signing secret once. (Panels older than the Instances scope only
   offer **write**; update the panel to get the narrower token.)
2. In Odoo: **Sudoo.sh → Configuration → Panels → New**. Enter the panel's address, the token and the signing
   secret, then click **Test connection**.
3. On the panel's tab **What users may create**, choose what Odoo users may create there: plain Odoo and/or
   GitHub repositories, Enterprise, demo data, which Odoo versions, the default and longest lifetime, and how many
   instances one person may have. The New instance wizard offers only that and says what is not allowed; every
   rule is checked again on **Create**.
4. Give people access in **Settings → Users**, under **Sudoo.sh**:
   - **User**: sees the company's instances, creates instances within those rules, starts, pauses, restarts and
     backs them up. Users never edit instances directly.
   - **Administrator**: also connects panels, sets the rules, extends lifetimes and deletes instances.

The token and the secret are visible to administrators only. Every request to the panel is signed, including the
Odoo user it is made for (shown in the panel's audit log and counted in its per-person limits); redirects are never
followed and the panel address must use https. The instances' Odoo passwords are never copied into Odoo.

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

## Code style

The code is formatted with black and checked with ruff (line length 120), and XML and YAML files are checked, on
every push and pull request. Run the same checks before you commit:

```bash
pip install pre-commit
pre-commit run --all-files
```

`.editorconfig` sets the basics for editors (UTF-8, LF, final newline, indent).

## Versions

One branch per Odoo version: `20.0`, `19.0`, `18.0` and `17.0`. Use the branch of the Odoo version your company
runs. The instances you create can be any version the panel offers (16.0 and later).

---

<sub>Copyright (c) 2026 Sudoo.sh. Odoo is a trademark of Odoo S.A.; Sudoo.sh is not affiliated with Odoo S.A.</sub>
