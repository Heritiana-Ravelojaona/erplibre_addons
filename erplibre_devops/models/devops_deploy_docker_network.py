from odoo import _, api, fields, models


class DevopsDeployDockerNetwork(models.Model):
    _name = "devops.deploy.docker.network"
    _description = "devops_deploy_docker_network"

    name = fields.Char()

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
    )
