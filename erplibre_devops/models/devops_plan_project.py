from odoo import _, api, exceptions, fields, models


class DevopsPlanProject(models.Model):
    _name = "devops.plan.project"
    _description = "devops_plan_project"

    name = fields.Char(help="Project name", required=True)

    type_repas_restaurant = fields.Char(
        help="Will generate about this type repas restaurant"
    )

    type_produit_magasin = fields.Char(
        help="Will generate about this type produit magasin"
    )

    website_max_number_one_pager = fields.Integer(default=300)

    project_type = fields.Selection(
        selection=[
            ("website_one_pager_restaurant", "Website one pager restaurant"),
            ("website_one_pager_magasin", "Website one pager magasin"),
        ],
        default="website_one_pager_restaurant",
        required=True,
        help="Will use DevOps tools to create this project type.",
    )

    @api.multi
    def execute(self):
        for rec in self:
            # with rec.workspace_id.devops_create_exec_bundle(
            #     "Execute plan project"
            # ) as rec_ws:
            message = ""
            if rec.project_type == "website_one_pager_restaurant":
                message = (
                    "Génère moi un texte de"
                    f" {rec.website_max_number_one_pager} mots sur le projet"
                    f" {rec.name} pour donner une envie au consommateur de"
                    " venir manger dans un restaurant de"
                    f" {rec.type_repas_restaurant}"
                )
            elif rec.project_type == "website_one_pager_magasin":
                message = (
                    "Génère moi un texte de"
                    f" {rec.website_max_number_one_pager} mots sur le projet"
                    f" {rec.name} pour donner une envie au consommateur de"
                    " venir acheter des produits dans un magasin de"
                    f" {rec.type_produit_magasin}"
                )
            if not message:
                raise ValueError("Need a project type.")
            # TODO il faut choisir un instance de déploiement ou en créer une, default local
            # TODO installer website
            # TODO générer du texte
            # TODO créer du contenu sur le site web
            op_value = {
                "prompt": message,
                "feature": "generate_text",
                "system_id": self.env.ref(
                    "erplibre_devops.devops_system_local"
                ).id,
                "request_url": f"http://localhost:8080",
                "temperature": 0.5,
            }
            op_id = self.env["devops.operate.localai"].create(op_value)
            op_id.execute_ia()
            home_page_id = self.env["ir.ui.view"].search(
                [
                    ("key", "=", "website.homepage"),
                    ("website_id", "!=", False),
                ],
                limit=1,
            )
            print(op_id)
            print(op_id.last_result_message)
            # arch_db = home_page_id.arch_db
            html_content = op_id.last_result_message.replace("\n", "<br />")
            # arch_db = arch_db.replace('<div id="wrap" class="oe_structure oe_empty"/>', f'<div id="wrap" class="oe_structure">{html_content}</div>')
            arch_db = f"""<t name="Homepage" t-name="website.homepage1">
    <t t-call="website.layout">
        <t t-set="pageName" t-value="'homepage'"/>
            <div id="wrap" class="oe_structure">{html_content}</div>
        </t>
    </t>"""
            home_page_id.arch_db = arch_db
