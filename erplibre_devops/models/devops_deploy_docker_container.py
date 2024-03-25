from odoo import _, api, fields, models


class DevopsDeployDockerContainer(models.Model):
    _name = "devops.deploy.docker.container"
    _description = "devops_deploy_docker_container"

    name = fields.Char()

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
    )
