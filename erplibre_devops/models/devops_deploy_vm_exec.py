from odoo import _, api, fields, models


class DevopsDeployVmExec(models.Model):
    _name = "devops.deploy.vm.exec"
    _description = "devops_deploy_vm_exec"

    name = fields.Char()

    stage_id = fields.Many2one(
        comodel_name="devops.deploy.vm.exec.stage",
        string="Stage",
    )

    vm_id = fields.Many2one(
        comodel_name="devops.deploy.vm",
        string="Vm",
    )

    is_running = fields.Boolean()
