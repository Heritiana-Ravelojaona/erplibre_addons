from odoo import _, api, fields, models


class DevopsCgField(models.Model):
    _name = "devops.cg.field"
    _description = "devops_cg_field"

    name = fields.Char(required=True)

    help = fields.Char()

    has_error = fields.Boolean(
        compute="_compute_has_error",
        store=True,
    )

    model_id = fields.Many2one(
        comodel_name="devops.cg.model",
        string="Model",
        ondelete="cascade",
    )

    type = fields.Selection(
        selection=[
            ("char", "char"),
            ("boolean", "boolean"),
            ("integer", "integer"),
            ("float", "float"),
            ("text", "text"),
            ("html", "html"),
            ("datetime", "datetime"),
            ("date", "date"),
            ("selection", "selection"),
            ("binary", "binary"),
            ("monetary", "monetary"),
            ("many2one", "many2one"),
            ("many2many", "many2many"),
            ("one2many", "one2many"),
        ],
        required=True,
        default="char",
    )

    related_manual = fields.Char(
        comodel_name="devops.cg.model",
        string="Related manual",
        help="Related field WIP",
    )

    # TODO rename relation to comodel_id
    # related_field_id = fields.Many2one(
    #     comodel_name="devops.cg.field",
    #     string="Related",
    #     help="Related field WIP",
    # )

    # TODO rename relation to comodel_id
    relation = fields.Many2one(
        comodel_name="devops.cg.model",
        string="Comodel",
        help="comodel - Create relation for many2one, many2many, one2many",
    )

    # TODO rename relation to comodel_name
    relation_manual = fields.Char(
        string="Comodel manual",
        help=(
            "comodel - Create relation for many2one, many2many, one2many."
            " Manual entry by pass relation field."
        ),
    )

    # TODO rename to inverse_field_id
    field_relation = fields.Many2one(
        comodel_name="devops.cg.field",
        domain="[('model_id', '=', relation)]",
        string="Inverse field",
        help="inverse_name - Need for one2many to associate with many2one.",
    )

    # TODO rename inverse_field_name
    field_relation_manual = fields.Char(
        string="Inverse field manual",
        help=(
            "inverse_name - Need for one2many to associate with many2one,"
            " manual entry."
        ),
    )

    # TODO rename to relation
    relation_ref = fields.Char(
        string="Relation ref",
        help="The relation name for many2many",
    )

    string = fields.Char(help="Label of the field")

    widget = fields.Selection(
        selection=[
            ("image", "image"),
            ("many2many_tags", "many2many_tags"),
            ("priority", "priority"),
            ("selection", "selection"),
            ("mail_followers", "mail_followers"),
            ("mail_activity", "mail_activity"),
            ("mail_thread", "mail_thread"),
        ]
    )

    # TODO remove this association
    devops_workspace_ids = fields.Many2many(
        comodel_name="devops.workspace",
        string="DevOps Workspace",
    )

    @api.depends(
        "type",
        "relation",
        "relation_manual",
        "field_relation",
        "field_relation_manual",
    )
    def _compute_has_error(self):
        for rec in self:
            # Disable all error
            rec.has_error = False
            if rec.type in ("many2many", "many2one", "one2many"):
                has_relation = rec.relation or rec.relation_manual
                has_field_relation = True
                if rec.type == "one2many":
                    has_field_relation = (
                        rec.field_relation or rec.field_relation_manual
                    )
                rec.has_error = not has_relation or not has_field_relation

    def get_dct(self):
        self.ensure_one()
        dct_field = {"ttype": self.type}
        if self.type in ["many2many", "many2one", "one2many"]:
            if self.relation:
                dct_field["relation"] = self.relation.name
            elif self.relation_manual:
                dct_field["relation"] = self.relation_manual
            # TODO support one2many with "inverse_field" and "inverse_field_manual"
            # TODO support many2many with different relation
        if self.help:
            dct_field["help"] = self.help
        if self.string:
            dct_field["field_description"] = self.string
        return dct_field
