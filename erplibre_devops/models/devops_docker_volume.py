from odoo import _, api, fields, models


class DevopsDockerVolume(models.Model):
    _name = "devops.docker.volume"
    _description = "devops_docker_volume"

    name = fields.Char(readonly=True)

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
        readonly=True,
    )

    active = fields.Boolean(default=True)

    mountpoint = fields.Char(readonly=True)

    created_at_date = fields.Char(readonly=True)

    driver = fields.Char(readonly=True)

    compose_id = fields.Many2one(
        comodel_name="devops.docker.compose",
        string="Compose",
        readonly=True,
    )
