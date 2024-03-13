from odoo import _, api, fields, models


class DevopsDeployVmExecStage(models.Model):
    _name = "devops.deploy.vm.exec.stage"
    _description = "devops_deploy_vm_exec_stage"

    name = fields.Char()
