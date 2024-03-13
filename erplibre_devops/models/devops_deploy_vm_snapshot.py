from odoo import _, api, fields, models


class DevopsDeployVmSnapshot(models.Model):
    _name = "devops.deploy.vm.snapshot"
    _description = "devops_deploy_vm_snapshot"

    name = fields.Char()
