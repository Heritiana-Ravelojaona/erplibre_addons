from odoo import _, api, fields, models


class DevopsDeployVm(models.Model):
    _name = "devops.deploy.vm"
    _description = "devops_deploy_vm"

    name = fields.Char()

    os = fields.Char()

    provider = fields.Char()

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
    )

    workspace_ids = fields.Many2many(
        comodel_name="devops.workspace",
        string="Workspace",
    )
