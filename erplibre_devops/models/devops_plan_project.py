from odoo import _, api, exceptions, fields, models


class DevopsPlanProject(models.Model):
    _name = "devops.plan.project"
    _inherit = ["mail.activity.mixin", "mail.thread"]
    _description = "devops_plan_project"

    name = fields.Char(
        help="Project name", required=True, track_visibility="onchange"
    )

    temperature = fields.Float(default=0.1, track_visibility="onchange")

    step = fields.Integer(default=20, track_visibility="onchange")

    type_context = fields.Char(
        help="Will generate about this type context",
        track_visibility="onchange",
    )

    website_max_number_one_pager = fields.Integer(
        default=10, track_visibility="onchange"
    )

    project_type = fields.Selection(
        selection=[
            (
                "website_one_pager_alimentation",
                "Website one pager en Alimentation",
            ),
            ("website_one_pager_sante", "Website one pager Santé"),
            ("website_one_pager_magasin", "Website one pager Magasin"),
        ],
        default="website_one_pager_alimentation",
        required=True,
        help="Will use DevOps tools to create this project type.",
        track_visibility="onchange",
    )

    society_type = fields.Selection(
        selection=[
            ("projet", "Projet"),
            ("projet entrepreneurial", "Projet entrepreneurial"),
            ("société", "Société"),
            ("industrie", "Industrie"),
            ("magasin", "Magasin"),
            ("restaurant", "Restaurant"),
            ("entreprise", "Entreprise"),
            ("société à but non lucratif", "OBNL"),
        ],
        default="projet",
        required=True,
        track_visibility="onchange",
    )

    question_one_pager_introduction = fields.Text(
        compute="_compute_question", track_visibility="onchange"
    )

    result_one_pager_introduction = fields.Text(track_visibility="onchange")

    question_one_pager_background_introduction = fields.Text(
        compute="_compute_question", track_visibility="onchange"
    )

    result_one_pager_background_introduction = fields.Char(
        track_visibility="onchange"
    )

    instance_exec_text_id = fields.Many2one(
        comodel_name="devops.instance.exec", track_visibility="onchange"
    )

    instance_exec_image_id = fields.Many2one(
        comodel_name="devops.instance.exec", track_visibility="onchange"
    )

    @api.depends(
        "name",
        "project_type",
        "website_max_number_one_pager",
        "type_context",
    )
    def _compute_question(self):
        for rec in self:
            message = ""
            message_background = ""
            if rec.project_type == "website_one_pager_alimentation":
                message = (
                    "Génère moi un texte de"
                    f" {rec.website_max_number_one_pager} mots, un"
                    f" {rec.society_type} nommé {rec.name} sur le sujet d'une"
                    f" introduction fabrique des {rec.type_context}"
                )
                message_background = (
                    f"Aliments «{rec.type_context}» d'une beauté extreme sur"
                    " une table de restaurant bien décoré."
                )
            elif rec.project_type == "website_one_pager_sante":
                message = (
                    "Génère moi un texte de"
                    f" {rec.website_max_number_one_pager} mots, un"
                    f" {rec.society_type} nommé {rec.name} sur le sujet d'une"
                    f" introduction sur la {rec.type_context} dans le contexte"
                    " du domaine de la santé."
                )
                message_background = (
                    "Présentation des produits sur les soins de santé"
                    f" «{rec.type_context}» avec des spécialistes."
                )
            elif rec.project_type == "website_one_pager_magasin":
                message = (
                    "Génère moi un texte de"
                    f" {rec.website_max_number_one_pager} mots sur le projet"
                    f" {rec.name} pour donner une envie au consommateur de"
                    " venir acheter des produits dans un magasin de"
                    f" {rec.type_context}"
                )
                message_background = (
                    f"Présentation des produits «{rec.type_context}» sur des"
                    " présentoirs de comptoir du magasin."
                )
            rec.question_one_pager_introduction = message
            rec.question_one_pager_background_introduction = message_background

    @api.multi
    def clear_result(self):
        for rec in self:
            rec.result_one_pager_introduction = ""
            rec.result_one_pager_background_introduction = ""

    @api.multi
    def execute(self):
        for rec in self:
            # with rec.workspace_id.devops_create_exec_bundle(
            #     "Execute plan project"
            # ) as rec_ws:
            # if not rec.question_one_pager_introduction:
            #     raise ValueError("Need a project type.")
            # TODO il faut choisir un instance de déploiement ou en créer une, default local
            # TODO installer website,website_snippet_all
            # TODO générer du texte
            # TODO créer du contenu sur le site web
            # TODO request_url auto_fill search existing localAI
            if not rec.result_one_pager_introduction:
                if rec.instance_exec_text_id:
                    op_value = {
                        "prompt": rec.question_one_pager_introduction,
                        "feature": "generate_text",
                        "system_id": self.env.ref(
                            "erplibre_devops.devops_system_local"
                        ).id,
                        "request_url": rec.instance_exec_text_id.url,
                        "temperature": rec.temperature,
                    }
                    op_id = self.env["devops.operate.localai"].create(op_value)
                    op_id.execute_ia()
                    rec.result_one_pager_introduction = (
                        op_id.last_result_message.replace("\n", "<br />")
                    )
                else:
                    rec.result_one_pager_introduction = rec.type_context

            if not rec.result_one_pager_background_introduction:
                if rec.instance_exec_image_id:
                    op_value = {
                        "prompt": rec.question_one_pager_background_introduction,
                        "feature": "generate_image",
                        "system_id": self.env.ref(
                            "erplibre_devops.devops_system_local"
                        ).id,
                        "request_url": rec.instance_exec_image_id.url,
                        "step": rec.step,
                        "gen_img_detail_level_id": self.env.ref(
                            "erplibre_devops.devops_gen_img_detail_02"
                        ).id,
                        "gen_img_light_ids": [
                            (
                                6,
                                0,
                                self.env.ref(
                                    "erplibre_devops.devops_gen_img_light_04"
                                ).ids,
                            )
                        ],
                    }
                    op_img_id = self.env["devops.operate.localai"].create(
                        op_value
                    )
                    op_img_id.execute_ia()
                    rec.result_one_pager_background_introduction = (
                        op_img_id.last_result_url
                    )

            if rec.result_one_pager_background_introduction:
                span_introduction_image = f"""<span class="s_parallax_bg oe_img_bg oe_custom_bg" style="background-image: url('{rec.result_one_pager_background_introduction}'); background-position: 50.00% 100.00%;"/>"""
            else:
                span_introduction_image = ""

            home_page_id = self.env["ir.ui.view"].search(
                [
                    ("key", "=", "website.homepage"),
                    ("website_id", "!=", False),
                ],
                limit=1,
            )

            extra_arch_db = ""
            if rec.project_type == "website_one_pager_alimentation":
                extra_arch_db = """
      <section class="s_full_menu">
        <div class="container-fluid">
          <h2 class="o_default_snippet_text">Menu à la carte</h2>
          <div class="row menu-container">
            <div class="col-lg-2 text-center">
              <h4 class="o_default_snippet_text">Hamburgers</h4>
              <i class="fa fa-glass fa-5x"/>
            </div>
            <div class="col-lg-10 s_full_menu_content">
              <div class="row">
                <div class="col-lg-4 text-center">
                  <img src="/web/image/website_snippet_all.image_content_13" alt="#" class="img img-fluid d-block mx-auto"/>
                </div>
                <div class="col-lg-8 s_full_menu_content_description">
                  <h4 class="o_default_snippet_text">Sandwich with Ham and Cheese<span class="slash o_default_snippet_text"><span class="price o_default_snippet_text"> | €</span> 9.00</span></h4>
                  <p class="o_default_snippet_text">Lorem ipsum dolor sit amet, consectetur adipisicing elit. Rerum incidunt, eum quae neque officiis dignissimos, veritatis amet, dolorum aperiam tempore sed. Modi rerum velit itaque ex nobis vero necessitatibus adipisci eaque cum iste nisi molestias quibusdam, voluptate odit deserunt, beatae.</p>
                </div>
              </div>
              <div class="row">
                <div class="col-lg-4 text-center">
                  <img src="/web/image/website_snippet_all.image_content_14" alt="#" class="img img-fluid d-block mx-auto"/>
                </div>
                <div class="col-lg-8 s_full_menu_content_description">
                  <h4 class="o_default_snippet_text">Honey Dijon Chicken Burger<span class="slash o_default_snippet_text"><span class="price o_default_snippet_text"> | €</span> 12.00</span></h4>
                  <p class="o_default_snippet_text">Lorem ipsum dolor sit amet, consectetur adipisicing elit. Rerum incidunt, eum quae neque officiis dignissimos, veritatis amet, dolorum aperiam tempore sed. Modi rerum velit itaque ex nobis vero necessitatibus adipisci eaque cum iste nisi molestias quibusdam, voluptate odit deserunt, beatae.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
"""

            arch_db = f"""<t name="Homepage" t-name="website.homepage1">
    <t t-call="website.layout">
    <t t-set="pageName" t-value="'homepage'"/>
    <div id="wrap" class="oe_structure oe_empty">
      <section class="s_cover parallax s_parallax_is_fixed bg-black-50 pt96 pb96 s_parallax_no_overflow_hidden" data-scroll-background-ratio="1" style="background-image: none; --darkreader-inline-bgimage: none;" data-darkreader-inline-bgimage="">
        {span_introduction_image}
        <div class="container">
          <div class="row s_nb_column_fixed">
            <div class="col-lg-12 s_title" data-name="Title">
              <h1 class="s_title_thin o_default_snippet_text" style="font-size: 62px; text-align: center;">{rec.name}</h1>
            </div>
            <div class="col-lg-12 s_text pt16 pb16" data-name="Text">
              <p class="lead o_default_snippet_text" style="text-align: center;">{rec.result_one_pager_introduction}</p>
            </div>
            <div class="col-lg-12 s_btn text-center pt16 pb16" data-name="Buttons">
              <a href="/aboutus" class="btn btn-delta rounded-circle o_default_snippet_text">À propos</a>
              <a href="/contactus" class="btn btn-primary rounded-circle o_default_snippet_text">Contactez-nous</a>
            </div>
          </div>
        </div>
      </section>
      {extra_arch_db}
    </div>
    </t>
</t>
            """
            home_page_id.arch_db = arch_db
