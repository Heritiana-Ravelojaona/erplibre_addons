from odoo import _, api, fields, models


class DevopsDeployDockerImage(models.Model):
    _name = "devops.deploy.docker.image"
    _description = "devops_deploy_docker_image"

    name = fields.Char()

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
    )
