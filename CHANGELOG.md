# Changelog

All notable changes to the Sudoo.sh apps for Odoo. Versions follow Odoo's scheme: `<Odoo series>.<major>.<minor>.<patch>`.

## [Unreleased]

### Changed

- Formatting setup: an `.editorconfig` for every editor, plus the existing black and ruff checks run unchanged; no
  file was reformatted. No behaviour change.

## 1.0.0 (2026-11-16)

First release, for Odoo 20.0, 19.0, 18.0 and 17.0 (`<series>.1.0.0`). Use a panel token with the **Instances** scope.

### Sudoo.sh Instance Manager (`sudoo_base`)

- Connect one or more Sudoo.sh panels with an API token and signing secret; every request is signed.
- What users may create, per panel: plain Odoo and/or GitHub repositories, Enterprise, demo data, the allowed Odoo
  versions (read from the panel), the default and longest lifetime, and instances per person.
- New instance wizard that offers only what is allowed, says what is not, shows the panel's remaining capacity, and
  checks every rule again on Create.
- Instance list and form, refreshed every minute: Open, Start, Pause, Restart, Back up; administrators extend
  lifetimes and delete.
- `sudoo.instance.mixin` with `_sudoo_instance_defaults` and `_sudoo_on_instance_ready` to add instances to any model.
- Two access levels (User, Administrator), read-only instances for users, multi-company rules.
- English and Arabic.

### Sudoo.sh CRM Demos (`sudoo_crm`), Project Tests (`sudoo_project`), Helpdesk Tests (`sudoo_helpdesk`)

- Create demo on opportunities; Test instance on tasks and tickets; Instances smart buttons; the link is posted in
  the record's chatter when the instance is ready.
- Helpdesk needs Odoo Enterprise; it was not tested on an Enterprise database.
