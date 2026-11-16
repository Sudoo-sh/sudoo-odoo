# Module Completeness Checklist: Sudoo.sh for Odoo

_Sudoo.sh for Odoo · 4 modules (sudoo_base, sudoo_crm, sudoo_project, sudoo_helpdesk) · Odoo 20.0 · branch 20.0 at commit 176d13e · checked 16 November 2026_

This is the Module Completeness Checklist ("The Anatomy of a Complete Odoo Module", 20 areas) filled in for the Sudoo.sh apps for Odoo 20.0. Every item is marked **Included**, **Not applicable** or **Deferred**, and every deferred item says why. Items that need a running Odoo were run: a fresh install with the tests, an upgrade, an uninstall and reinstall, and the Arabic interface. The apps are also published for Odoo 17.0, 18.0 and 19.0 (branches of the same name); this documentation describes 20.0. Two things were **not** run and are said so wherever they matter: the Helpdesk app (it needs Odoo Enterprise) and a live Sudoo.sh panel (the tests use a patched panel client, the screenshots a stand-in panel with sample data).

**105 items:** 88 included · 13 not applicable · 4 deferred with a reason.

## Summary

| | |
| :--- | :--- |
| **Automated tests** | Official Odoo images, fresh database with sudoo_base, sudoo_crm and sudoo_project, once in English and once in a database created in Arabic (ar_001), 16 Nov 2026: 20.0: 12 tests; 19.0, 18.0 and 17.0: 10 tests each; 0 failed, 0 errors every time (the test runner's totals). sudoo_crm and sudoo_project have no tests of their own. |
| **Code style** | pre-commit with black, ruff and XML/YAML checks (pyproject.toml, .pre-commit-config.yaml); a CI job on GitHub runs it next to the install-and-test job. |
| **Install / upgrade / uninstall** | 20.0: fresh install clean; upgrade (-u) of an installed database clean, and a changed sync interval kept; uninstall of the three apps left no sudoo table, model or column, and the reinstall was clean. |
| **Arabic** | ar.po for all four modules, 193 terms, all translated (none fuzzy); loaded into Odoo 20.0, the instance list checked right to left and two panel connection errors shown in Arabic; tests pass in an Arabic database on every branch. |
| **Closed on 16 Nov 2026** | Done since the previous version: the smart button icon on Odoo 20, translatable panel errors, a sync schedule kept through upgrades (areas 4, 6, 8), the other version branches verified (area 20) and code style checked in CI (area 19). |
| **Not verified** | sudoo_helpdesk on an Enterprise database; any call against a real Sudoo.sh panel. |

## Deferred items

| Area | Item | Reason |
| :--- | :--- | :--- |
| Tests (non-negotiable) | Tests for the app modules | sudoo_crm and sudoo_project have no own tests (defaults and buttons only); the mixin is covered in sudoo_base. Add a test per app. |
| Tests (non-negotiable) | Tested against a live panel | Not done yet; needs a test panel with an API token. |
| Tests (non-negotiable) | Helpdesk tested | Needs an Enterprise database; not available here. |
| Data and architecture | Scale | The sync reads up to 500 instances per panel each minute; not measured on a large panel yet. |

## 1. Manifest and identity

| Item | Status | Where / why |
| :--- | :--- | :--- |
| name: human-readable English, no version or client name | Included | Sudoo.sh Instance Manager, CRM Demos, Project Tests, Helpdesk Tests. |
| summary: one line | Included | One line in every manifest. |
| description (or static/description/index.html) | Included | index.html for all four apps (store page with tabs). |
| version 20.0.x.y.z | Included | 20.0.1.0.0 in all four. |
| category: an existing one | Included | Productivity (base), Sales/CRM, Services/Project, Services/Helpdesk. |
| author / maintainer | Included | Sudoo.sh, with support address. |
| website resolvable and correct | Included | https://sudoo.sh. |
| license consciously chosen | Included | OPL-1, with LICENSE and COPYRIGHT at the repository root. |
| application explicit; installable True | Included | sudoo_base is the application; the other three are add-ons; all installable. |
| auto_install only for genuine bridges | Not applicable | No module installs itself; each app is chosen explicitly. |
| depends minimal and justified | Included | base, mail for sudoo_base; sudoo_base plus crm, project or helpdesk for the apps. |
| external_dependencies declared | Not applicable | Only requests, which ships with Odoo. |
| data ordered so referenced records load first | Included | Security, access, cron, views, wizard, menus; fresh install clean. |
| demo separated from structural data | Not applicable | The modules ship no demo data (they need a real panel). |
| assets declared in the manifest | Not applicable | No JavaScript or SCSS assets. |
| hooks where install/uninstall needs logic | Not applicable | None needed; uninstall verified clean. |
| images banner | Included | static/description/banner.png in all four (2:1). |
| price / currency | Included | Free: no price in the manifests. |

## 2. Repository and directory hygiene

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Conventional layout | Included | models/, views/, security/, wizard/, services/, data/, tests/, i18n/, static/. |
| __init__.py at every level | Included | Present; install proves the import order. |
| LICENSE present | Included | LICENSE and COPYRIGHT at the repository root (OPL-1). |
| README.md | Included | Repository README with apps, install, connection, use, extension, versions. |
| .gitignore | Included | Present at the root. |
| No compiled artefacts, backups or client data | Included | None in git; screenshots use sample data only. |

## 3. Models layer

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Models named after the business object | Included | sudoo.server, sudoo.server.version, sudoo.instance, sudoo.instance.create, sudoo.instance.mixin. |
| _description on every model | Included | All five. |
| _order where it matters | Included | Panels by sequence, versions by name, instances newest first. |
| _inherit chosen deliberately | Included | The apps extend crm.lead, project.task, helpdesk.ticket with the mixin; no _inherits. |
| Explicit labels and help on non-obvious fields | Included | Lifetimes, limits, token, secret, wizard fields carry help. |
| required / readonly / copy / tracking set consciously | Included | Instance fields read-only, token/secret copy=False, name and status tracked. |
| ondelete on Many2one | Included | Versions and instances cascade with their panel. |
| Constraints for rules, models.Constraint for uniqueness | Included | https rule and limits as constrains; unique version per panel and instance name per panel. |
| No hard-coded ids or currency | Included | None. |
| Logging through getLogger | Included | The sync logs unreachable panels as warnings. |

## 4. Structural data

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Stable external ids | Included | group_sudoo_user, group_sudoo_manager, ir_cron_sudoo_sync, actions and menus. |
| Crons with realistic intervals | Included | "Sudoo.sh: read instances from the panels" every minute. |
| noupdate on client-modifiable records | Included | data/ir_cron.xml is noupdate (595752f): an interval changed to 5 minutes was kept through -u on 16 Nov 2026. |
| Sequences, mail templates, stages | Not applicable | Not needed. |

## 5. Demo data

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Only in the demo key | Not applicable | No demo data: an instance only means something on a real panel. |
| Generated by a committed script at volume | Not applicable | Same reason. |

## 6. Views and user interface

| Item | Status | Where / why |
| :--- | :--- | :--- |
| List, form and search for user-facing models | Included | Instances (list, form, search) and panels (list, form). |
| Search with filters and group-bys | Included | Mine, Not deleted (default), group by Status and Odoo version. |
| Statusbar, smart buttons | Included | Instance status bar; Instances smart buttons on panel, opportunity, task, ticket; Linked record. |
| Conditional invisible | Included | Buttons follow the status; wizard fields follow what the panel allows. |
| Empty-state messages and actions with help | Included | Instances action has an empty-state help. |
| Resilient xpath inheritance | Included | //header and //div[@name='button_box']. |
| Smart button icon renders | Included | Instances smart buttons use icon deployed_code (595752f); it renders on Odoo 20 in the opportunity, task and panel screenshots taken 16 Nov 2026. |
| RTL layout verified for Arabic | Included | Instance list checked in Arabic, right to left (screenshot instances_ar.png). |

## 7. Security (non-negotiable)

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Groups with a privilege | Included | User and Administrator under the privilege Sudoo.sh. |
| ACL for every model, transient included | Included | security/ir.access.csv: 7 lines, wizard included. |
| Record rules, multi-company | Included | Company rules on panels, versions and instances. |
| Field-level groups for sensitive fields | Included | Token and signing secret: administrators only. |
| Least-privilege credentials | Included | Setup asks for an Instances-scope panel token; panels without that scope only offer write (acts as panel Administrator), which the manual says plainly. |
| Menus tied to groups | Included | App menu for Users; Configuration for Administrators. |
| sudo() sparing, each use justified | Included | Signing, the module's own writes after checks, the sync; each commented. |
| Server-side checks, not only the form | Included | _check_policy on Create; Administrator check on extend and delete. |
| Tested as a restricted user | Included | test_access: user cannot write instances, delete, or read the token; outsider sees nothing. |

## 8. Translation

| Item | Status | Where / why |
| :--- | :--- | :--- |
| .pot generated and committed | Included | One .pot per module. |
| .po per target language, 100 % | Included | ar.po in all four, 193 terms, all translated. |
| Every user-facing string wrapped | Included | Panel connection errors go through sudoo.server._panel_message and are in ar.po (595752f); checked in Arabic on Odoo 20.0, 16 Nov 2026. |
| Verified in the running interface | Included | Arabic loaded into Odoo 20.0, instance list checked. |

## 9. Reports and documents

| Item | Status | Where / why |
| :--- | :--- | :--- |
| QWeb reports | Not applicable | Nothing to print. |

## 10. Wizards and user actions

| Item | Status | Where / why |
| :--- | :--- | :--- |
| TransientModel for input gathering | Included | sudoo.instance.create. |
| Confirmation before destructive actions | Included | Delete asks for confirmation; the panel backs up first. |
| Feedback on long actions | Included | Status Working and a chatter line; the link is posted when ready. |
| Idempotent actions | Included | The sync updates by name; ready notification sent once (creating to ready). |

## 11. Settings integration

| Item | Status | Where / why |
| :--- | :--- | :--- |
| res.config.settings where there are options | Not applicable | Options live on each panel record (several panels per database). |

## 12. Front-end assets

| Item | Status | Where / why |
| :--- | :--- | :--- |
| OWL / SCSS / bundles | Not applicable | No front-end code. |

## 13. Controllers and portal

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Controllers | Not applicable | No routes exposed; Odoo only calls the panel. |
| Outgoing calls hardened | Included | Signed, 20 s timeout, no redirects, 2 MB cap, instance names checked, https only. |

## 14. Tests (non-negotiable)

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Tests under tests/, discovered by convention | Included | sudoo_base/tests: test_access.py, test_panel_client.py. |
| Tagged for the right phase | Included | post_install, -at_install. |
| Core rules covered | Included | Signature, policy, per-person limit, refusals, redirect and size limits, ready notification. |
| Security covered as a restricted user | Included | test_users_only_read_instances_and_secrets_stay_hidden. |
| No network in tests | Included | PanelClient.request is patched. |
| Tests for the app modules | Deferred | sudoo_crm and sudoo_project have no own tests (defaults and buttons only); the mixin is covered in sudoo_base. Add a test per app. |
| Tested against a live panel | Deferred | Not done yet; needs a test panel with an API token. |
| Helpdesk tested | Deferred | Needs an Enterprise database; not available here. |

## 15. Install, upgrade, uninstall

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Verified on fresh install | Included | 16 Nov 2026, on 20.0, 19.0, 18.0 and 17.0, in English and Arabic databases. |
| Verified on upgrade | Included | 20.0: -u on a database installed from earlier code (adds a field): clean; -u at 595752f kept a changed cron interval. |
| Verified on uninstall + reinstall | Included | No sudoo table, model or column left; reinstall clean. |
| migrations/ | Not applicable | First release, nothing to migrate. |

## 16. Documentation

| Item | Status | Where / why |
| :--- | :--- | :--- |
| README.md | Included | Repository README. |
| static/description/index.html | Included | All four apps. |
| Designed icon.png | Included | All four. |
| Screenshots | Included | 7 screenshots of the real screens (sample data) in static/description/screenshots. |
| User guide in every delivery language | Included | User Manual in English and Arabic (PDF), USER_MANUAL.md. |
| Developer documentation | Included | DEVELOPER_GUIDE.md and the Technical Overview. |
| CHANGELOG.md | Included | Present (1.0.0). |

## 17. Licensing and legal

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Manifest license matches the instrument | Included | OPL-1 in manifests and LICENSE. |
| Copyright headers | Included | Every Python and XML file. |
| Terms for extensions stated | Included | README and Developer Guide: own modules may use any licence, no copied code. |

## 18. Data and architecture

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Multi-company decided | Included | Panels belong to a company; instances follow their panel. |
| Time zones | Included | Panel times converted to UTC before storing. |
| Concurrency | Included | No global state; the per-person limit is checked on Create. |
| Scale | Deferred | The sync reads up to 500 instances per panel each minute; not measured on a large panel yet. |

## 19. Code quality

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Odoo naming, no dead code, no debug leftovers | Included | Reviewed while writing these documents; ruff checks unused imports and common mistakes. |
| Code style checked automatically | Included | black and ruff (pyproject.toml) plus XML and YAML checks, run by pre-commit locally and by a CI job on GitHub. |
| No secrets in code | Included | Token and secret are entered on the panel record. |
| Readable commit history | Included | Commits describe the change. |

## 20. Delivery and operations

| Item | Status | Where / why |
| :--- | :--- | :--- |
| Verified on a clean database | Included | Fresh install and tests, 16 Nov 2026. |
| Deployment note | Included | README "Connecting your panel" and chapter 2 of the User Manual. |
| Known limitations communicated | Included | "What to keep in mind" in the manual and section 7 of the overview. |
| Continuous integration | Included | GitHub Actions: an install-and-test job and a code-style job. |
| Other version branches verified | Included | 19.0, 18.0 and 17.0 (official images, 16 Nov 2026): each installs sudoo_base, sudoo_crm and sudoo_project with 10 tests, 0 failed, 0 errors, in an English database and in one created in Arabic (ar_001); 20.0 the same with 12 tests. |

---

Source: the Module Completeness Checklist ("The Anatomy of a Complete Odoo Module"), 20 areas. Screens and runs used sample data only.
