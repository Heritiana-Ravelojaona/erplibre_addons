from odoo import _, api, fields, models


class DevopsDeployDockerImage(models.Model):
    _name = "devops.deploy.docker.image"
    _description = "devops_deploy_docker_image"

    name = fields.Char(store=True, compute="_compute_name")

    system_ids = fields.Many2many(
        comodel_name="devops.system",
        relation="deploy_docker_image_system_ids_rel",
        string="Systems",
        readonly=True,
    )

    active = fields.Boolean(default=True)

    id_image = fields.Char(readonly=True)

    id_short_image = fields.Char(readonly=True)

    tag = fields.Char(readonly=True)

    size_human = fields.Char(readonly=True)

    size_virtual_human = fields.Char(readonly=True)

    created_at = fields.Char(readonly=True)

    created_since = fields.Char(readonly=True)

    repository = fields.Char(readonly=True)

    history_full = fields.Text(readonly=True)

    inspect_full = fields.Text(readonly=True)

    @api.depends("tag", "repository")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.repository}:{rec.tag}"
