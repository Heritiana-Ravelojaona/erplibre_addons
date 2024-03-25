from odoo import _, api, fields, models


class DevopsDeployDockerCompose(models.Model):
    _name = "devops.deploy.docker.compose"
    _description = "devops_deploy_docker_compose"

    name = fields.Char()

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
    )
