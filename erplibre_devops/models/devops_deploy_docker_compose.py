import os

from odoo import _, api, fields, models


class DevopsDeployDockerCompose(models.Model):
    _name = "devops.deploy.docker.compose"
    _description = "devops_deploy_docker_compose"

    name = fields.Char(readonly=True)

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
        readonly=True,
    )

    active = fields.Boolean(default=True)

    config_file_path = fields.Char(readonly=True)

    folder_root = fields.Char(store=True, compute="_compute_folder_root")

    is_running = fields.Boolean(readonly=True, track_visibility="onchange")

    @api.depends("config_file_path")
    def _compute_folder_root(self):
        for rec in self:
            if rec.config_file_path:
                rec.folder_root = os.path.dirname(rec.config_file_path)
            else:
                rec.folder_root = False
