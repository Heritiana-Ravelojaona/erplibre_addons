import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class DevopsDeployVm(models.Model):
    _name = "devops.deploy.vm"
    _description = "devops_deploy_vm"

    name = fields.Char()

    identifiant = fields.Char()

    os = fields.Char()

    provider = fields.Char()

    system_id = fields.Many2one(
        comodel_name="devops.system",
        string="System",
    )

    workspace_ids = fields.Many2many(
        comodel_name="devops.workspace",
        string="Workspaces",
    )

    has_vm_exec_running = fields.Boolean(
        compute="_compute_has_vm_exec_running", store=True
    )

    vm_exec_last_id = fields.Many2one(
        comodel_name="devops.deploy.vm.exec",
        string="VM last exec",
    )

    @api.depends("vm_exec_last_id", "vm_exec_last_id.is_running")
    def _compute_has_vm_exec_running(self):
        for rec in self:
            rec.has_vm_exec_running = (
                rec.vm_exec_last_id and rec.vm_exec_last_id.is_running
            )

    def action_start_vm(self):
        for rec in self:
            # TODO use default workspace from system for contexte dev
            if not rec.system_id:
                _logger.warning(
                    f"Missing system_id into devops.deploy.vm id {rec.id}"
                )
                continue
            cmd = f"vboxmanage startvm {rec.identifiant} --type gui"
            out, status = rec.system_id.execute_with_result(
                cmd, None, return_status=True
            )
            if status != 0:
                # TODO raise error execution
                _logger.error(f"Problem to start vm {rec.identifiant} : {out}")
            else:
                _logger.info(f"VM start: {out}")
                value = {
                    "vm_id": rec.id,
                    "is_running": True,
                }
                vm_exec_id = self.env["devops.deploy.vm.exec"].create(value)
                rec.vm_exec_last_id = vm_exec_id.id

    def action_stop_vm(self):
        for rec in self:
            # TODO use default workspace from system for contexte dev
            if not rec.system_id:
                _logger.warning(
                    f"Missing system_id into devops.deploy.vm id {rec.id}"
                )
                continue
            cmd = f"vboxmanage controlvm {rec.identifiant} poweroff"
            out, status = rec.system_id.execute_with_result(
                cmd, None, return_status=True
            )
            if status != 0:
                # TODO raise error execution
                # TODO validate before status before launch poweroff
                # Since note validate before status, believe it's stopped
                if rec.vm_exec_last_id:
                    rec.vm_exec_last_id.is_running = False
                _logger.error(f"Problem to stop vm {rec.identifiant} : {out}")
            else:
                _logger.info(f"VM stop: {out}")
                if rec.vm_exec_last_id:
                    rec.vm_exec_last_id.is_running = False
