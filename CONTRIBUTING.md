# Contributing

Thank you for helping. These modules are **proprietary software of Sudoo.sh**, published openly so that anyone can
read them, report problems and propose improvements. Only Sudoo.sh publishes them.

## Contents

1. [What you may do](#what-you-may-do)
2. [Reporting a problem](#reporting-a-problem)
3. [Proposing a change](#proposing-a-change)
4. [Code rules](#code-rules)
5. [Your contribution's licence](#your-contributions-licence)

## What you may do

| | |
| :--- | :--- |
| Install and use the modules, for free, also in a company | yes |
| Write your own modules that depend on them and extend them | yes |
| Fork this repository on GitHub to open a pull request | yes |
| Publish, redistribute or sell copies, changed or not (another store, another repository, a customer's server) | no |

## Reporting a problem

Open an issue with the Odoo version, the app (`sudoo_base`, `sudoo_crm`...), what you did, what you expected and
what happened. Security problems: never in an issue; follow the
[security policy](https://github.com/Sudoo-sh/.github/blob/main/SECURITY.md).

## Proposing a change

1. Open an issue first for anything bigger than a small fix, so we agree on the approach.
2. Branch from the version branch you change (`20.0`, `19.0`, ...), named `fix/...` or `feat/...`.
3. Keep one subject per pull request, with tests for new behaviour.
4. Sign off every commit (`git commit -s`): it states that you wrote the change and may contribute it.
5. Open the pull request against that version branch. A maintainer reviews it; once merged, Sudoo.sh ports it to
   the other version branches.

## Code rules

- **Small modules.** `sudoo_base` holds only what every app needs: panels, instances, the wizard, the mixin,
  security. Anything tied to another Odoo app goes into its own module (`sudoo_<app>`).
- **One place talks to the panel:** `sudoo_base/services/panel_client.py`. Models call `server._call(...)`, never
  `requests` directly.
- **One file per model**, named after it; views in `views/`, wizards in `wizard/`, access in `security/`.
- **Extend through the mixin** (`sudoo.instance.mixin`) and its hooks; do not copy its code into another module.
- Every file starts with the header
  `# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.`
  (XML: the same text in a comment).
- Follow Odoo's guidelines: `invisible="..."` expressions (no `attrs`), translatable strings with `_()`, no SQL
  where the ORM does it, access rules for every new model.
- Tests: `odoo -d test -i <module> --test-enable --test-tags /<module> --stop-after-init` must pass.
- Plain, direct wording in labels and messages; say what the user can do.

## Your contribution's licence

By submitting a contribution you confirm that you wrote it (or may contribute it), and you grant Sudoo.sh a
perpetual, worldwide, non-exclusive, royalty-free, irrevocable licence to use, change, publish and license it as
part of these modules under any terms. You keep the copyright of your own work.
