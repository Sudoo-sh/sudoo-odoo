# Part of Sudoo.sh. Proprietary: see the LICENSE file for full copyright and licensing details.
{
    "name": "Sudoo.sh Instance Manager",
    "summary": "Create, start, pause, back up and delete Odoo demo, test and training instances on your "
    "Sudoo.sh server, from inside Odoo",
    "version": "17.0.1.0.0",
    "category": "Productivity",
    "author": "Sudoo.sh",
    "website": "https://sudoo.sh",
    "license": "OPL-1",
    "support": "support@sudoo.sh",
    "maintainer": "Sudoo.sh",
    "depends": ["base", "mail"],
    "data": [
        "security/sudoo_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/sudoo_instance_views.xml",
        "views/sudoo_server_views.xml",
        "wizard/sudoo_instance_create_views.xml",
        "views/menus.xml",
    ],
    "images": ["static/description/banner.png"],
    "application": True,
    "installable": True,
}
