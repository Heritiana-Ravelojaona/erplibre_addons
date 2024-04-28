from odoo import _, api, fields, models


class DevopsInstanceExec(models.Model):
    _name = "devops.instance.exec"
    _description = "devops_instance_exec"

    name = fields.Char(compute="_compute_name", store=True)

    docker_container_ids = fields.Many2many(
        comodel_name="devops.docker.container",
        string="Docker Container",
    )

    docker_image_ids = fields.Many2many(
        comodel_name="devops.docker.image",
        string="Docker Image",
    )

    docker_network_ids = fields.Many2many(
        comodel_name="devops.docker.network",
        string="Docker Network",
    )

    docker_volume_ids = fields.Many2many(
        comodel_name="devops.docker.volume",
        string="Docker Volume",
    )

    port = fields.Integer()

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
    )

    type_ids = fields.Many2many(
        comodel_name="devops.instance.type",
        string="Types",
    )

    url = fields.Char()

    workspace_id = fields.Many2one(
        comodel_name="devops.workspace",
        string="Workspace",
    )

    @api.depends("url", "type_ids")
    def _compute_name(self):
        for rec in self:
            str_type = "|".join([a.name for a in rec.type_ids])
            rec.name = f"{str_type} {rec.url}"
