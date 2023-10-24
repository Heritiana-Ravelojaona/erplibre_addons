# Copyright 2023 TechnoLibre inc. - Mathieu Benoit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
import os
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta

import requests

from odoo import _, api, exceptions, fields, models, tools

_logger = logging.getLogger(__name__)


class ItWorkspace(models.Model):
    _name = "it.workspace"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "ERPLibre IT Workspace"

    name = fields.Char(
        compute="_compute_name",
        store=True,
        help="Summary of this it_workspace process",
    )

    it_exec_ids = fields.One2many(
        comodel_name="it.exec",
        inverse_name="it_workspace",
        string="Executions",
    )

    it_exec_bundle_ids = fields.One2many(
        comodel_name="it.exec.bundle",
        inverse_name="it_workspace",
        string="Executions bundle",
    )

    it_exec_error_ids = fields.One2many(
        comodel_name="it.exec.error",
        inverse_name="it_workspace",
        string="Executions error",
    )

    it_workspace_format = fields.Selection(
        selection=[
            ("zip", "zip (includes filestore)"),
            ("dump", "pg_dump custom format (without filestore)"),
        ],
        default="zip",
        help="Choose the format for this it_workspace.",
    )

    log_workspace = fields.Text()

    need_debugger_cg_erplibre_it = fields.Boolean(
        help="CG erplibre_it got error, detect can use the debugger"
    )

    show_error_chatter = fields.Boolean(help="Show error to chatter")

    path_code_generator_to_generate = fields.Char(default="addons/addons")

    path_working_erplibre = fields.Char(default="/ERPLibre")

    is_installed = fields.Boolean(
        help="Need to install environnement before execute it."
    )

    is_debug_log = fields.Boolean(help="Will print cmd to debug.")

    is_running = fields.Boolean(
        readonly=True,
        default=False,
    )

    folder = fields.Char(
        required=True,
        default=lambda self: self._default_folder(),
        help="Absolute path for storing the it_workspaces",
    )

    system_id = fields.Many2one(
        comodel_name="it.system",
        string="System",
        required=True,
        default=lambda self: self.env.ref(
            "erplibre_it.it_system_local", raise_if_not_found=False
        ),
    )

    ide_pycharm = fields.Many2one(comodel_name="it.ide.pycharm")

    # TODO backup button and restore button

    port_http = fields.Integer(
        string="port http",
        default=8069,
        help="The port of http odoo.",
    )

    is_self_instance = fields.Boolean(
        help="Is the instance who run this database"
    )

    port_longpolling = fields.Integer(
        string="port longpolling",
        default=8071,
        help="The port of longpolling odoo.",
    )

    db_name = fields.Char(
        string="DB instance name",
        default="test",
    )

    is_me = fields.Char(
        string="Self instance",
        help="Add more automatisation about manage itself.",
    )

    db_is_restored = fields.Boolean(
        readonly=True, help="When false, it's because actually restoring a DB."
    )

    url_instance = fields.Char(
        compute="_compute_url_instance",
        store=True,
    )

    url_instance_database_manager = fields.Char(
        compute="_compute_url_instance",
        store=True,
    )

    it_code_generator_ids = fields.Many2many(
        comodel_name="it.code_generator",
        inverse_name="it_workspace_id",
        string="Project",
    )

    it_code_generator_module_ids = fields.Many2many(
        comodel_name="it.code_generator.module",
        # related="it_code_generator_ids.module_ids",
        string="Module",
        readonly=False,
    )

    it_code_generator_model_ids = fields.Many2many(
        # related="it_code_generator_module_ids.model_ids",
        comodel_name="it.code_generator.module.model",
        string="Model",
        readonly=False,
    )

    it_code_generator_field_ids = fields.Many2many(
        # related="it_code_generator_model_ids.field_ids",
        comodel_name="it.code_generator.module.model.field",
        string="Field",
        readonly=False,
    )

    # it_code_generator_finish_compute = fields.Boolean(
    #     store=True, compute="_compute_it_code_generator_finish_compute"
    # )

    it_code_generator_tree_addons = fields.Text(
        string="Tree addons",
        help="Will show generated files from code generator or humain",
    )

    it_code_generator_diff = fields.Text(
        string="Diff addons",
        help="Will show diff git",
    )

    it_code_generator_status = fields.Text(
        string="Status addons",
        help="Will show status git",
    )

    it_code_generator_stat = fields.Text(
        string="Stat addons",
        help="Will show statistique code",
    )

    it_code_generator_log_addons = fields.Text(
        string="Log code generator",
        help="Will show code generator log, last execution",
    )

    it_cg_erplibre_it_log = fields.Text(
        string="Log CG erplibre_it new_project",
        help=(
            "Will show code generator log for new project erplibr_it, last"
            " execution"
        ),
        readonly=True,
    )

    it_cg_erplibre_it_error_log = fields.Text(
        string="Error CG erplibre_it new_project",
        help=(
            "Will show code generator error for new project erplibr_it, last"
            " execution"
        ),
        readonly=True,
    )

    time_exec_action_code_generator_generate_all = fields.Char(
        readonly=True,
        help="Execution time of method action_code_generator_generate_all",
    )

    time_exec_action_cg_erplibre_it = fields.Char(
        readonly=True,
        help="Execution time of method action_cg_erplibre_it",
    )

    mode_source = fields.Selection(
        selection=[("docker", "Docker"), ("git", "Git")],
        required=True,
        default="docker",
    )

    mode_exec = fields.Selection(
        selection=[
            ("docker", "Docker"),
            ("terminal", "Gnome-terminal"),
            # ("systemd", "SystemD"),
        ],
        default="docker",
        required=True,
    )

    mode_environnement = fields.Selection(
        selection=[
            ("dev", "Dev"),
            ("test", "Test"),
            ("prod", "Prod"),
            ("stage", "Stage"),
        ],
        required=True,
        default="test",
        help=(
            "Dev to improve, test to test, prod ready for production, stage to"
            " use a dev and replace a prod"
        ),
    )

    is_conflict_mode_exec = fields.Boolean(
        compute="_compute_is_conflict_mode_exec",
        store=True,
    )

    mode_version_erplibre = fields.Selection(
        selection=[
            ("1.5.0", "1.5.0"),
            ("master", "Master"),
            ("develop", "Develop"),
        ],
        required=True,
        default="1.5.0",
        help=(
            "Dev to improve, test to test, prod ready for production, stage to"
            " use a dev and replace a prod"
        ),
    )

    mode_version_base = fields.Selection(
        selection=[("12.0", "12.0"), ("14.0", "14.0")],
        required=True,
        default="12.0",
        help="Support base version communautaire",
    )

    git_branch = fields.Char("Git branch")

    git_url = fields.Char(
        "Git URL", default="https://github.com/ERPLibre/ERPLibre"
    )

    time_exec_action_clear_all_generated_module = fields.Char(
        readonly=True,
        help="Execution time of method action_clear_all_generated_module",
    )

    time_exec_action_install_all_generated_module = fields.Char(
        readonly=True,
        help="Execution time of method action_install_all_generated_module",
    )

    time_exec_action_install_all_uca_generated_module = fields.Char(
        readonly=True,
        help=(
            "Execution time of method action_install_all_uca_generated_module"
        ),
    )

    time_exec_action_install_all_ucb_generated_module = fields.Char(
        readonly=True,
        help=(
            "Execution time of method action_install_all_ucb_generated_module"
        ),
    )

    time_exec_action_install_and_generate_all_generated_module = fields.Char(
        readonly=True,
        help=(
            "Execution time of method"
            " action_install_and_generate_all_generated_module"
        ),
    )

    time_exec_action_refresh_meta_cg_generated_module = fields.Char(
        readonly=True,
        help=(
            "Execution time of method action_refresh_meta_cg_generated_module"
        ),
    )

    time_exec_action_git_commit_all_generated_module = fields.Char(
        readonly=True,
        help="Execution time of method action_git_commit_all_generated_module",
    )

    workspace_docker_id = fields.Many2one(
        comodel_name="it.workspace.docker",
        string="Workspace Docker",
    )

    test_ids = fields.Many2many(
        comodel_name="it.test",
        string="Tests",
    )

    workspace_terminal_id = fields.Many2one(
        comodel_name="it.workspace.terminal",
        string="Workspace Terminal",
    )

    has_error_restore_db = fields.Boolean()

    last_new_project_self = fields.Many2one(
        comodel_name="it.cg.new_project",
        string="Last new project self",
    )

    last_new_project_cg = fields.Many2one(
        comodel_name="it.cg.new_project",
        string="Last new project cg",
    )

    def _default_image_db_selection(self):
        return self.env["it.db.image"].search(
            [("name", "like", "erplibre_base")], limit=1
        )

    image_db_selection = fields.Many2one(
        comodel_name="it.db.image", default=_default_image_db_selection
    )

    @api.model
    def _default_folder(self):
        return os.getcwd()

    @api.multi
    @api.depends(
        "mode_source",
        "mode_exec",
        "mode_environnement",
        "mode_version_erplibre",
        "mode_version_base",
        "folder",
        "port_http",
    )
    def _compute_name(self):
        for rec in self:
            if not isinstance(rec.id, models.NewId):
                rec.name = f"{rec.id}: "
            else:
                rec.name = ""
            rec.name += (
                f"{rec.mode_source} - {rec.mode_exec} -"
                f" {rec.mode_environnement} - {rec.mode_version_erplibre} -"
                f" {rec.mode_version_base} - {rec.folder} - {rec.port_http}"
            )

    @api.multi
    @api.depends("mode_source", "mode_exec")
    def _compute_is_conflict_mode_exec(self):
        for rec in self:
            rec.is_conflict_mode_exec = (
                rec.mode_source == "docker" and rec.mode_exec != "docker"
            )

    @api.multi
    @api.depends("system_id.ssh_host", "system_id.method", "port_http")
    def _compute_url_instance(self):
        for rec in self:
            # TODO create configuration
            # localhost = "127.0.0.1"
            localhost = "localhost"
            url_host = (
                rec.system_id.ssh_host
                if rec.system_id.method == "ssh"
                else localhost
            )
            rec.url_instance = f"http://{url_host}:{rec.port_http}"
            rec.url_instance_database_manager = (
                f"{rec.url_instance}/web/database/manager"
            )

    @api.multi
    @api.depends("folder", "system_id")
    def _compute_is_installed(self):
        for rec in self:
            # TODO validate installation is done before
            rec.is_installed = False

    @api.multi
    def action_cg_erplibre_it(self):
        for rec in self:
            start = datetime.now()
            rec.it_cg_erplibre_it_error_log = False
            rec.need_debugger_cg_erplibre_it = False
            addons_path = "./addons/ERPLibre_erplibre_addons"
            module_name = "erplibre_it"

            # Disable all others
            new_project_ids_disable = self.env["it.cg.new_project"].search(
                [
                    ("it_workspace", "=", rec.id),
                    ("project_type", "=", "self"),
                ]
            )
            new_project_ids_disable.write({"active": False})

            new_project_id = self.env["it.cg.new_project"].create(
                {
                    "module": module_name,
                    "directory": addons_path,
                    "it_workspace": rec.id,
                    "project_type": "self",
                }
            )
            if rec.last_new_project_self:
                new_project_id.last_new_project = rec.last_new_project_self.id
            rec.last_new_project_self = new_project_id.id
            new_project_id.action_new_project()
            # result = rec.execute(
            #     cmd=f"cd {rec.folder};./script/code_generator/new_project.py"
            #     f" -d {addons_path} -m {module_name}",
            # )
            result = ""
            rec.it_cg_erplibre_it_log = result
            index_error = result.rfind("odoo.exceptions.ValidationError")
            if index_error >= 0:
                rec.it_cg_erplibre_it_error_log = result[
                    index_error : result.find("\n", index_error)
                ]
                rec.need_debugger_cg_erplibre_it = True

            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_cg_erplibre_it = f"{td:.03f}s"

    @api.multi
    def action_cg_setup_pycharm_debug(self):
        for rec in self:
            if not rec.ide_pycharm:
                rec.ide_pycharm = self.env["it.ide.pycharm"].create(
                    {"it_workspace": rec.id}
                )
            rec.ide_pycharm.action_cg_setup_pycharm_debug()

    @api.multi
    def action_open_terminal_path_erplibre_it(self):
        for rec in self:
            folder_path = os.path.join(
                rec.folder, "addons", "ERPLibre_erplibre_addons"
            )
            rec.execute(folder=folder_path, force_open_terminal=True)

    @api.multi
    def action_code_generator_generate_all(self):
        for rec in self:
            start = datetime.now()
            # TODO add try catch, add breakpoint, rerun loop. Careful when lose context
            # Start with local storage
            # Increase speed
            # TODO keep old configuration of config.conf and not overwrite all
            # rec.execute(cmd=f"cd {rec.path_working_erplibre};make config_gen_code_generator", to_instance=True)
            if rec.it_code_generator_ids and rec.mode_exec in ["docker"]:
                rec.workspace_docker_id.docker_config_gen_cg = True
                rec.action_reboot()
                rec.workspace_docker_id.docker_config_gen_cg = False
            for rec_cg in rec.it_code_generator_ids:
                for module_id in rec_cg.module_ids:
                    # Support only 1, but can run in parallel multiple if no dependencies between
                    module_name = module_id.name
                    lst_model = []
                    dct_model_conf = {"model": lst_model}
                    for model_id in module_id.model_ids:
                        lst_field = []
                        lst_model.append(
                            {"name": model_id.name, "fields": lst_field}
                        )
                        for field_id in model_id.field_ids:
                            dct_value_field = {
                                "name": field_id.name,
                                "help": field_id.help,
                                "type": field_id.type,
                            }
                            if field_id.type in [
                                "many2one",
                                "many2many",
                                "one2many",
                            ]:
                                dct_value_field["relation"] = (
                                    field_id.relation.name
                                    if field_id.relation
                                    else field_id.relation_manual
                                )
                                if not dct_value_field["relation"]:
                                    msg_err = (
                                        f"Model '{model_id.name}', field"
                                        f" '{field_id.name}' need a"
                                        " relation because type is"
                                        f" '{field_id.type}'"
                                    )
                                    raise exceptions.Warning(msg_err)
                            if field_id.type in [
                                "one2many",
                            ]:
                                dct_value_field["relation_field"] = (
                                    field_id.field_relation.name
                                    if field_id.field_relation
                                    else field_id.field_relation_manual
                                )
                                if not dct_value_field["relation_field"]:
                                    msg_err = (
                                        f"Model '{model_id.name}', field"
                                        f" '{field_id.name}' need a"
                                        " relation field because type is"
                                        f" '{field_id.type}'"
                                    )
                                    raise exceptions.Warning(msg_err)
                            if field_id.widget:
                                dct_value_field = field_id.widget
                            lst_field.append(dct_value_field)
                    if rec_cg.force_clean_before_generate:
                        rec.workspace_code_remove_module(module_id)
                    model_conf = (
                        json.dumps(dct_model_conf)
                        # .replace('"', '\\"')
                        # .replace("'", "")
                    )
                    dct_new_project = {
                        "module": module_name,
                        "directory": rec.path_code_generator_to_generate,
                        "keep_bd_alive": True,
                        "it_workspace": rec.id,
                        "project_type": "cg",
                    }
                    # extra_arg = ""
                    if model_conf:
                        dct_new_project["config"] = model_conf
                        # extra_arg = f" --config '{model_conf}'"

                    # Disable all others
                    new_project_ids_disable = self.env[
                        "it.cg.new_project"
                    ].search(
                        [
                            ("it_workspace", "=", rec.id),
                            ("project_type", "=", "cg"),
                        ]
                    )
                    new_project_ids_disable.write({"active": False})

                    new_project_id = self.env["it.cg.new_project"].create(
                        dct_new_project
                    )
                    if rec.last_new_project_cg:
                        new_project_id.last_new_project = (
                            rec.last_new_project_cg.id
                        )
                    rec.last_new_project_cg = new_project_id.id
                    new_project_id.action_new_project()
                    # cmd = (
                    #     f"cd {rec.path_working_erplibre};./script/code_generator/new_project.py"
                    #     f" --keep_bd_alive -m {module_name} -d"
                    #     f" {rec.path_code_generator_to_generate}{extra_arg}"
                    # )
                    # result = rec.execute(cmd=cmd, to_instance=True)
                    # rec.it_code_generator_log_addons = result
            if rec.it_code_generator_ids and rec.mode_exec in ["docker"]:
                rec.action_reboot()
            # rec.execute(cmd=f"cd {rec.path_working_erplibre};make config_gen_all", to_instance=True)
            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_code_generator_generate_all = f"{td:.03f}s"

    @api.multi
    def action_clear_all_generated_module(self):
        for rec in self:
            start = datetime.now()
            for cg in rec.it_code_generator_ids:
                for module_id in cg.module_ids:
                    rec.workspace_code_remove_module(module_id)
            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_clear_all_generated_module = f"{td:.03f}s"
        self.action_check()

    @api.multi
    def workspace_code_remove_module(self, module_id):
        for rec in self:
            path_to_remove = (
                f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate}"
            )
            rec.workspace_remove_module(module_id.name, path_to_remove)

    @api.multi
    def workspace_CG_remove_module(self):
        for rec in self:
            # TODO is it necessary to hardcode it? Why not merge with code section?
            path_to_remove = (
                f"cd {rec.path_working_erplibre}/addons/ERPLibre_erplibre_addons"
            )
            rec.workspace_remove_module(
                "erplibre_it", path_to_remove, remove_module=False
            )

    @api.multi
    def workspace_remove_module(
        self, module_name, path_to_remove, remove_module=True
    ):
        for rec in self:
            if remove_module:
                rec.execute(
                    cmd=f"{path_to_remove};rm -rf ./{module_name};",
                    to_instance=True,
                )
            rec.execute(
                cmd=(
                    f"{path_to_remove};rm"
                    f" -rf ./code_generator_template_{module_name};"
                ),
                to_instance=True,
            )
            rec.execute(
                cmd=f"{path_to_remove};rm -rf ./code_generator_{module_name};",
                to_instance=True,
            )

    @api.multi
    def action_git_commit_all_generated_module(self):
        for rec in self:
            start = datetime.now()
            # for cg in rec.it_code_generator_ids:
            # Validate git directory exist
            exec_id = rec.execute(
                cmd=(
                    f"ls {rec.path_working_erplibre}/{rec.path_code_generator_to_generate}/.git"
                ),
                to_instance=True,
            )
            result = exec_id.log_all
            if "No such file or directory" in result:
                # Suppose git not exist
                # This is not good if .git directory is in parent directory
                rec.execute(
                    cmd=(
                        f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate};git"
                        " init;echo '*.pyc' > .gitignore;git add"
                        " .gitignore;git commit -m 'first commit'"
                    ),
                    to_instance=True,
                )
                rec.execute(
                    cmd=(
                        f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate};git"
                        " init"
                    ),
                    to_instance=True,
                )

            exec_id = rec.execute(
                cmd=(
                    f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate};git"
                    " status -s"
                ),
                to_instance=True,
            )
            result = exec_id.log_all
            if result:
                # TODO show result to log
                # Force add file and commit
                rec.execute(
                    cmd=(
                        f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate};git"
                        " add ."
                    ),
                    to_instance=True,
                )
                rec.execute(
                    cmd=(
                        f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate};git"
                        " commit -m 'Commit by RobotLibre'"
                    ),
                    to_instance=True,
                )
            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_git_commit_all_generated_module = (
                f"{td:.03f}s"
            )

    @api.multi
    def action_refresh_meta_cg_generated_module(self):
        for rec in self:
            start = datetime.now()
            diff = ""
            status = ""
            stat = ""
            exec_id = rec.execute(
                cmd=(
                    f"ls {rec.path_working_erplibre}/{rec.path_code_generator_to_generate}/.git"
                ),
                to_instance=True,
            )
            result = exec_id.log_all
            if result:
                # Create diff
                exec_id = rec.execute(
                    cmd=(
                        f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate};git"
                        " diff"
                    ),
                    to_instance=True,
                )
                diff += exec_id.log_all
                # Create status
                exec_id = rec.execute(
                    cmd=(
                        f"cd {rec.path_working_erplibre}/{rec.path_code_generator_to_generate};git"
                        " status"
                    ),
                    to_instance=True,
                )
                status += exec_id.log_all
                for cg in rec.it_code_generator_ids:
                    # Create statistic
                    for module_id in cg.module_ids:
                        exec_id = rec.execute(
                            cmd=(
                                f"cd {rec.path_working_erplibre};./script/statistic/code_count.sh"
                                f" ./{rec.path_code_generator_to_generate}/{module_id.name};"
                            ),
                            to_instance=True,
                        )
                        result = exec_id.log_all
                        if result:
                            stat += f"./{rec.path_code_generator_to_generate}/{module_id.name}"
                            stat += result

                        exec_id = rec.execute(
                            cmd=(
                                f"cd {rec.path_working_erplibre};./script/statistic/code_count.sh"
                                f" ./{rec.path_code_generator_to_generate}/code_generator_template_{module_id.name};"
                            ),
                            to_instance=True,
                        )
                        result = exec_id.log_all
                        if result:
                            stat += f"./{rec.path_code_generator_to_generate}/code_generator_template_{module_id.name}"
                            stat += result

                        exec_id = rec.execute(
                            cmd=(
                                f"cd {rec.path_working_erplibre};./script/statistic/code_count.sh"
                                f" ./{rec.path_code_generator_to_generate}/code_generator_{module_id.name};"
                            ),
                            to_instance=True,
                        )
                        result = exec_id.log_all
                        if result:
                            stat += f"./{rec.path_code_generator_to_generate}/code_generator_{module_id.name}"
                            stat += result

                        # Autofix attached field to workspace
                        if rec not in module_id.it_workspace_ids:
                            module_id.it_workspace_ids = [(4, rec.id)]
                        for model_id in module_id.model_ids:
                            if rec not in model_id.it_workspace_ids:
                                model_id.it_workspace_ids = [(4, rec.id)]
                            for field_id in model_id.field_ids:
                                if rec not in field_id.it_workspace_ids:
                                    field_id.it_workspace_ids = [(4, rec.id)]

            rec.it_code_generator_diff = diff
            rec.it_code_generator_status = status
            rec.it_code_generator_stat = stat
            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_refresh_meta_cg_generated_module = (
                f"{td:.03f}s"
            )

    @api.multi
    def write(self, values):
        cg_before_ids_i = self.it_code_generator_ids.ids

        status = super().write(values)
        if "it_code_generator_ids" in values.keys():
            # Update all the list of code generator, associate to this workspace
            for rec in self:
                cg_missing_ids_i = list(
                    set(cg_before_ids_i).difference(
                        set(rec.it_code_generator_ids.ids)
                    )
                )
                cg_missing_ids = self.env["it.code_generator"].browse(
                    cg_missing_ids_i
                )
                for cg_id in cg_missing_ids:
                    for module_id in cg_id.module_ids:
                        if rec in module_id.it_workspace_ids:
                            module_id.it_workspace_ids = [(3, rec.id)]
                        for model_id in module_id.model_ids:
                            if rec in model_id.it_workspace_ids:
                                model_id.it_workspace_ids = [(3, rec.id)]
                            for field_id in model_id.field_ids:
                                if rec in field_id.it_workspace_ids:
                                    field_id.it_workspace_ids = [(3, rec.id)]
                cg_adding_ids_i = list(
                    set(rec.it_code_generator_ids.ids).difference(
                        set(cg_before_ids_i)
                    )
                )
                cg_adding_ids = self.env["it.code_generator"].browse(
                    cg_adding_ids_i
                )
                for cg_id in cg_adding_ids:
                    for module_id in cg_id.module_ids:
                        if rec not in module_id.it_workspace_ids:
                            module_id.it_workspace_ids = [(4, rec.id)]
                        for model_id in module_id.model_ids:
                            if rec not in model_id.it_workspace_ids:
                                model_id.it_workspace_ids = [(4, rec.id)]
                            for field_id in model_id.field_ids:
                                if rec not in field_id.it_workspace_ids:
                                    field_id.it_workspace_ids = [(4, rec.id)]
        return status

    @api.multi
    def action_install_all_generated_module(self):
        for rec in self:
            start = datetime.now()
            module_list = ",".join(
                [
                    m.name
                    for cg in rec.it_code_generator_ids
                    for m in cg.module_ids
                ]
            )
            if rec.mode_exec in ["docker"]:
                last_cmd = rec.workspace_docker_id.docker_cmd_extra
                rec.workspace_docker_id.docker_cmd_extra = (
                    f"-d {rec.db_name} -i {module_list} -u {module_list}"
                )
                # TODO option install continuous or stop execution.
                # TODO Use install continuous in production, else stop execution for dev
                # TODO actually, it's continuous
                # TODO maybe add an auto-update when detect installation finish
                rec.action_reboot()
                rec.workspace_docker_id.docker_cmd_extra = last_cmd
            elif rec.mode_exec in ["terminal"]:
                rec.execute(
                    "./script/addons/install_addons.sh"
                    f" {rec.db_name} {module_list}"
                )
                rec.action_reboot()
            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_install_all_generated_module = f"{td:.03f}s"
        self.action_check()

    @api.multi
    def action_install_all_uca_generated_module(self):
        for rec in self:
            start = datetime.now()
            module_list = ",".join(
                [
                    f"code_generator_template_{m.name},{m.name}"
                    for cg in rec.it_code_generator_ids
                    for m in cg.module_ids
                ]
            )
            rec.execute(
                cmd=(
                    f"cd {rec.path_working_erplibre};./script/database/db_restore.py"
                    " --database cg_uca"
                ),
                to_instance=True,
            )
            rec.execute(
                cmd=(
                    f"cd {rec.path_working_erplibre};./script/addons/install_addons_dev.sh"
                    f" cg_uca {module_list}"
                ),
                to_instance=True,
            )

            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_install_all_uca_generated_module = (
                f"{td:.03f}s"
            )
        self.action_check()

    @api.multi
    def action_install_all_ucb_generated_module(self):
        for rec in self:
            start = datetime.now()
            module_list = ",".join(
                [
                    f"code_generator_{m.name}"
                    for cg in rec.it_code_generator_ids
                    for m in cg.module_ids
                ]
            )
            rec.execute(
                cmd=(
                    f"cd {rec.path_working_erplibre};./script/database/db_restore.py"
                    " --database cg_ucb"
                ),
                to_instance=True,
            )
            rec.execute(
                cmd=(
                    f"cd {rec.path_working_erplibre};./script/addons/install_addons_dev.sh"
                    f" cg_ucb {module_list}"
                ),
                to_instance=True,
            )

            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_install_all_ucb_generated_module = (
                f"{td:.03f}s"
            )
        self.action_check()

    @api.multi
    def action_install_and_generate_all_generated_module(self):
        for rec in self:
            start = datetime.now()
            rec.action_code_generator_generate_all()
            rec.action_git_commit_all_generated_module()
            rec.action_refresh_meta_cg_generated_module()
            rec.action_install_all_generated_module()
            end = datetime.now()
            td = (end - start).total_seconds()
            rec.time_exec_action_install_and_generate_all_generated_module = (
                f"{td:.03f}s"
            )

    @api.multi
    def action_open_terminal(self):
        for rec in self:
            rec.execute(force_open_terminal=True)

    @api.multi
    def action_open_terminal_addons(self):
        for rec in self:
            cmd = (
                f"cd {os.path.join(rec.path_working_erplibre, rec.path_code_generator_to_generate)};ls -l"
            )
            if rec.is_debug_log:
                _logger.info(cmd)
            rec.execute(
                cmd=cmd,
                force_open_terminal=True,
                docker=bool(rec.mode_exec in ["docker"]),
            )

    @api.multi
    def action_open_terminal_tig(self):
        # TODO move to model code_generator ?
        for rec in self:
            is_docker = False
            if rec.mode_exec in ["docker"]:
                is_docker = True
                exec_id = rec.execute(cmd="which tig", to_instance=True)
                result = exec_id.log_all
                if not result:
                    # TODO support OS and not only docker
                    self.workspace_docker_id.action_docker_install_dev_soft()
            dir_to_check = os.path.join(
                rec.path_working_erplibre,
                rec.path_code_generator_to_generate,
                ".git",
            )
            exec_id = rec.execute(cmd=f"ls {dir_to_check}")
            status_ls = exec_id.log_all
            if "No such file or directory" in status_ls:
                raise Warning(
                    "Cannot open command 'tig', cannot find directory"
                    f" '{dir_to_check}'."
                )
            cmd = (
                f"cd {rec.path_working_erplibre};cd"
                f" ./{rec.path_code_generator_to_generate};tig"
            )
            if rec.is_debug_log:
                _logger.info(cmd)
            rec.execute(cmd=cmd, force_open_terminal=True, docker=is_docker)

    @api.model
    def action_check_all(self):
        """Run all scheduled check."""
        return self.search([]).action_check()

    @api.multi
    def action_check(self):
        for rec_o in self:
            # Track exception because it's run from cron
            with rec_o.it_create_exec_bundle("Check all") as rec:
                # rec.docker_initiate_succeed = not rec.docker_initiate_succeed
                exec_id = rec.execute(cmd=f"ls {rec.folder}")
                lst_file = exec_id.log_all.strip().split("\n")
                if any(
                    [
                        "No such file or directory" in str_file
                        for str_file in lst_file
                    ]
                ):
                    rec.is_installed = False
                if rec.mode_exec in ["docker"]:
                    rec.is_running = rec.workspace_docker_id.docker_is_running
                    rec.workspace_docker_id.action_check()
                elif rec.mode_exec in ["terminal"]:
                    # TODO missing detect is running
                    rec.workspace_terminal_id.action_check()
                else:
                    _logger.warning(
                        "Support other mode_exec to detect is_running"
                        f" '{rec.mode_exec}'"
                    )

                rec.action_check_tree_addons()

    @api.multi
    def action_install_me_workspace(self):
        for rec in self:
            # Set same BD of this instance
            rec.db_name = self.env.cr.dbname
            # Detect the mode exec of this instance
            exec_id = rec.execute(cmd=f"ls {rec.folder}/.git")
            status_ls = exec_id.log_all
            if "No such file or directory" not in status_ls:
                rec.mode_source = "git"
                rec.mode_exec = "terminal"
            self.action_install_workspace()
        self.is_me = True
        self.port_http = 8069
        self.port_longpolling = 8072

    @api.multi
    def action_check_tree_addons(self):
        for rec_o in self:
            with rec_o.it_create_exec_bundle("Check tree addons") as rec:
                exec_id = rec.execute(
                    cmd=f"cd {rec.path_working_erplibre};tree",
                    to_instance=True,
                )
                rec.it_code_generator_tree_addons = exec_id.log_all


    @api.multi
    def action_restore_db_image(self):
        for rec in self:
            rec.has_error_restore_db = False
            if rec.mode_exec in ["terminal"]:
                image = ""
                if rec.image_db_selection:
                    image = f" --image {rec.image_db_selection.name}"
                cmd = (
                    f"cd {rec.path_working_erplibre};"
                    "./script/database/db_restore.py --database"
                    f" {rec.db_name}{image};"
                )
                exec_id = rec.execute(cmd=cmd)
                rec.log_workspace = f"\n{exec_id.log_all}"
            elif rec.mode_exec in ["docker"]:
                # maybe send by network REST web/database/restore
                url_list = f"{rec.url_instance}/web/database/list"
                url_restore = f"{rec.url_instance}/web/database/restore"
                url_drop = f"{rec.url_instance}/web/database/drop"
                if not rec.image_db_selection:
                    # TODO create stage, need a stage ready to restore
                    raise exceptions.Warning(
                        _("Error, need field db_selection")
                    )
                rec.db_is_restored = False
                backup_file_path = rec.image_db_selection.path
                session = requests.Session()
                response = requests.get(
                    url_list,
                    data=json.dumps({}),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                if response.status_code == 200:
                    database_list = response.json()
                    print(database_list)
                else:
                    # TODO remove print
                    print("une erreur")
                    continue

                # Delete first
                # TODO cannot delete database if '-d database' argument -d is set
                result_db_list = database_list.get("result")
                if rec.db_name in result_db_list:
                    print(result_db_list)
                    files = {
                        "master_pwd": (None, "admin"),
                        "name": (None, rec.db_name),
                    }
                    response = session.post(url_drop, files=files)
                    if response.status_code == 200:
                        print("Le drop a été envoyé avec succès.")
                    else:
                        rec.workspace_docker_id.docker_cmd_extra = ""
                        # TODO detect "-d" in execution instead of force action_reboot
                        rec.action_reboot()
                        next_second = 5
                        print(
                            "Une erreur s'est produite lors du drop, code"
                            f" '{response.status_code}'. Retry in"
                            f" {next_second} seconds"
                        )
                        # Strange, retry for test
                        time.sleep(next_second)
                        # response = requests.get(
                        #     url_list,
                        #     data=json.dumps({}),
                        #     headers={
                        #         "Content-Type": "application/json",
                        #         "Accept": "application/json",
                        #     },
                        # )
                        response = session.post(url_drop, files=files)
                        if response.status_code == 200:
                            # database_list = response.json()
                            # print(database_list)
                            print(
                                "Seconde essaie, le drop a été envoyé avec"
                                " succès."
                            )
                        else:
                            print(
                                "Seconde essaie, une erreur s'est produite"
                                " lors du drop, code"
                                f" '{response.status_code}'."
                            )
                            rec.has_error_restore_db = True
                    if not rec.has_error_restore_db:
                        response = requests.get(
                            url_list,
                            data=json.dumps({}),
                            headers={
                                "Content-Type": "application/json",
                                "Accept": "application/json",
                            },
                        )
                        if response.status_code == 200:
                            database_list = response.json()
                            print(database_list)

                if not rec.has_error_restore_db:
                    with open(backup_file_path, "rb") as backup_file:
                        files = {
                            "backup_file": (
                                backup_file.name,
                                backup_file,
                                "application/octet-stream",
                            ),
                            "master_pwd": (None, "admin"),
                            "name": (None, rec.db_name),
                        }
                        response = session.post(url_restore, files=files)
                    if response.status_code == 200:
                        print(
                            "Le fichier de restauration a été envoyé avec"
                            " succès."
                        )
                        rec.db_is_restored = True
                    else:
                        print(
                            "Une erreur s'est produite lors de l'envoi du"
                            " fichier de restauration."
                        )

                # f = {'file data': open(f'./image_db{rec.path_working_erplibre}_base.zip', 'rb')}
                # res = requests.post(url_restore, files=f)
                # print(res.text)

    @api.multi
    def check_it_workspace_docker(self):
        for rec in self:
            if rec.mode_exec in ["docker"]:
                if not rec.workspace_docker_id:
                    rec.workspace_docker_id = self.env[
                        "it.workspace.docker"
                    ].create({"workspace_id": rec.id})
            elif rec.mode_exec in ["terminal"]:
                if not rec.workspace_terminal_id:
                    rec.workspace_terminal_id = self.env[
                        "it.workspace.terminal"
                    ].create({"workspace_id": rec.id})
            else:
                raise Warning(f"Cannot support '{rec.mode_exec}'")

    @api.multi
    def action_start(self):
        # Not work sleep 0 with gnome_terminal
        # need enough second to write to database
        sleep_kill = 2
        self.check_it_workspace_docker()
        for rec in self:
            exec_id = rec.execute(f"lsof -i TCP:{rec.port_http} | grep python")
            out_server_exist = exec_id.log_all
            if rec.mode_exec in ["docker"]:
                rec.workspace_docker_id.action_start_docker_compose()
            elif rec.mode_exec in ["terminal"]:
                # TODO support is_me with docker
                prefix = ""
                if rec.is_me and out_server_exist:
                    prefix = f"sleep {sleep_kill * 2};"
                rec.execute(
                    cmd=(
                        f"{prefix}./run.sh -d"
                        f" {rec.db_name} --http-port={rec.port_http} --longpolling-port={rec.port_longpolling}"
                    ),
                    force_open_terminal=True,
                )
            if out_server_exist:
                # TODO this cause problem, cannot save all information
                # kill me if I exist
                # kill first application with python3 with this port
                # Ignore the browser with the same page, that's why need grep
                # The first number is the 3 from python3, so take second number
                # Force to kill, because execution is running, a simple sigint will not work. Cannot write this request
                if out_server_exist.startswith("python3 "):
                    cmd = (
                        f"sleep {sleep_kill};kill -9 $(lsof -i"
                        f" TCP:{rec.port_http} | grep python3 | grep -oE"
                        " '[0-9]+' | sed -n '2p');exit"
                    )
                    rec.execute(cmd=cmd, force_open_terminal=True)
                elif out_server_exist.startswith("python "):
                    cmd = (
                        f"sleep {sleep_kill};kill -9 $(lsof -i"
                        f" TCP:{rec.port_http} | grep python | grep -oE"
                        " '[0-9]+' | head -n1);exit"
                    )
                    rec.execute(cmd=cmd, force_open_terminal=True)
                else:
                    _logger.warning(
                        f"What is the software for the port {rec.port_http} :"
                        f" {out_server_exist}"
                    )

            rec.action_check()

    @api.multi
    def action_stop(self):
        self.check_it_workspace_docker()
        for rec in self:
            if rec.mode_exec in ["docker"]:
                rec.workspace_docker_id.action_stop_docker_compose()
            elif rec.mode_exec in ["terminal"]:
                # TODO support it
                pass
            rec.action_check()

    @api.multi
    def action_reboot(self):
        self.action_stop()
        self.action_start()

    @api.multi
    @api.depends(
        "mode_source",
        "mode_exec",
        "mode_environnement",
        "mode_version_erplibre",
        "mode_version_base",
    )
    def action_install_workspace(self):
        for rec in self:
            exec_id = rec.execute(cmd=f"ls {rec.folder}")
            lst_file = exec_id.log_all.strip().split("\n")
            if rec.mode_source in ["docker"]:
                if "docker-compose.yml" in lst_file:
                    # TODO try to reuse
                    _logger.info("detect docker-compose.yml, please read it")
                rec.action_pre_install_workspace()
                rec.path_working_erplibre = "/ERPLibre"
            elif rec.mode_source in ["git"]:
                if rec.mode_exec in ["docker"]:
                    rec.path_working_erplibre = "/ERPLibre"
                else:
                    rec.path_working_erplibre = rec.folder
                branch_str = ""
                if rec.mode_version_erplibre:
                    if rec.mode_version_erplibre[0].isnumeric():
                        branch_str = f" -b v{rec.mode_version_erplibre}"
                    else:
                        branch_str = f" -b {rec.mode_version_erplibre}"

                # TODO bug if file has same key
                # if any(["ls:cannot access " in str_file for str_file in lst_file]):
                if any(
                    [
                        "No such file or directory" in str_file
                        for str_file in lst_file
                    ]
                ):
                    # self.action_pre_install_workspace(
                    #     ignore_last_directory=True
                    # )
                    exec_id = rec.execute(
                        cmd=f"git clone {rec.git_url}{branch_str} {rec.folder}"
                    )
                    rec.log_workspace = exec_id.log_all
                    exec_id = rec.execute(
                        cmd=(
                            f"cd {rec.folder};./script/install/install_locally_dev.sh"
                        )
                    )
                    rec.log_workspace += exec_id.log_all
                    # TODO fix this bug, but activate into install script
                    # TODO bug only for local, ssh is good
                    # Bug poetry thinks it's installed, so force it
                    # result = rec.system_id.execute_with_result(
                    #     f"cd {rec.folder};source"
                    #     " ./.venv/bin/activate;poetry install"
                    # )
                    # rec.log_workspace += result
                    rec.execute(
                        cmd=(
                            'bash -c "source ./.venv/bin/activate;poetry'
                            ' install"'
                        ),
                        force_open_terminal=True,
                    )
                else:
                    # TODO try te reuse
                    _logger.info("Git project already exist")

                # lst_file = rec.execute(cmd=f"ls {rec.folder}").log_all.strip().split("\n")
                # if "docker-compose.yml" in lst_file:
                # if rec.mode_environnement in ["prod", "test"]:
                #     result = rec.system_id.execute_with_result(
                #         f"git clone https://github.com{rec.path_working_erplibre}{rec.path_working_erplibre}"
                #         f"{branch_str}"
                #     )
                # else:
            rec.action_network_change_port_random()
            rec.is_installed = True

    @api.multi
    def execute(
        self,
        cmd="",
        folder="",
        force_open_terminal=False,
        force_docker=False,
        add_stdin_log=False,
        add_stderr_log=True,
        # get_stderr=False,
        # get_status=False,
        to_instance=False,
        engine="bash",
        docker=False,
    ):
        # TODO search into context if need to parallel or serial
        """TODO need to return out, err, status"""
        lst_result = []
        first_log_debug = True
        out = False
        # out = ""
        # err = ""
        # status = False
        if to_instance:
            self.check_it_workspace_docker()
        for rec in self:
            rec_force_docker = force_docker
            if to_instance:
                if rec.mode_exec in ["docker"]:
                    rec_force_docker = True

            if rec.is_debug_log and cmd:
                if first_log_debug:
                    _logger.info(cmd)
                    first_log_debug = False

            force_folder = folder if folder else rec.folder
            it_exec_value = {
                "it_workspace": rec.id,
                "cmd": cmd,
                "folder": force_folder,
            }
            it_exec_bundle = self.env.context.get("it_exec_bundle")
            if it_exec_bundle:
                it_exec_value["it_exec_bundle_id"] = it_exec_bundle
            it_exec = self.env["it.exec"].create(it_exec_value)
            lst_result.append(it_exec)
            if force_open_terminal:
                rec_force_docker = rec_force_docker or docker
                rec.system_id.execute_gnome_terminal(
                    force_folder,
                    cmd=cmd,
                    docker=rec_force_docker,
                )
            elif rec_force_docker:
                out = rec.system_id.exec_docker(cmd, force_folder)
            else:
                out = rec.system_id.execute_with_result(
                    cmd,
                    add_stdin_log=add_stdin_log,
                    add_stderr_log=add_stderr_log,
                    engine=engine,
                )

            it_exec.exec_stop_date = fields.Datetime.now()
            if out is not False:
                it_exec.log_stdout = out

        #
        # if get_stderr:
        #     if get_status:
        #         return out, err, status
        #     return out, err
        # elif get_status:
        #     return out, status
        # return out
        if len(self) == 1:
            return lst_result[0]
        return self.env["it.exec"].browse([a.id for a in lst_result])

    @api.multi
    def action_poetry_install(self):
        self.execute(
            cmd='bash -c "source ./.venv/bin/activate;poetry install"'
        )

    @api.multi
    def action_pre_install_workspace(self, ignore_last_directory=False):
        for rec in self:
            # folder = (
            #     rec.folder
            #     if not ignore_last_directory
            #     else os.path.basename(rec.folder)
            # )
            # Directory must exist
            # TODO make test to validate if remove next line, permission root the project /tmp/project/addons root
            addons_path = os.path.join(rec.folder, "addons", "addons")
            rec.execute(f"mkdir -p '{addons_path}'")

    @api.multi
    @api.model
    def action_network_change_port_default(
        self, ctx=None, default_port_http=8069, default_port_longpolling=8072
    ):
        for rec in self:
            rec.port_http = default_port_http
            rec.port_longpolling = default_port_longpolling

    @api.multi
    def action_network_change_port_random(
        self, ctx=None, min_port=10000, max_port=20000
    ):
        # Choose 2 sequence
        for rec in self:
            # port_1
            while rec.check_port_is_open(
                rec, rec.system_id.iterator_port_generator
            ):
                rec.system_id.iterator_port_generator += 1
            rec.port_http = rec.system_id.iterator_port_generator
            rec.system_id.iterator_port_generator += 1
            # port_2
            while rec.check_port_is_open(
                rec, rec.system_id.iterator_port_generator
            ):
                rec.system_id.iterator_port_generator += 1
            rec.port_longpolling = rec.system_id.iterator_port_generator
            rec.system_id.iterator_port_generator += 1
            if rec.system_id.iterator_port_generator >= max_port:
                rec.system_id.iterator_port_generator = min_port

    @staticmethod
    def check_port_is_open(rec, port):
        # TODO move to it_network
        # TODO use lsof instead of this script
        script = f"""import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("127.0.0.1",{port}))
if result == 0:
   print("Port is open")
else:
   print("Port is not open")
sock.close()
        """
        if rec.system_id.debug_command:
            _logger.info(script)
        exec_id = rec.execute(
            cmd=script,
            engine="python",
        )
        return exec_id.log_all == "Port is open"

    @api.multi
    @contextmanager
    def it_workspace_log(self):
        # TODO adapt for erplibre_it
        """Log a it_workspace result."""
        try:
            _logger.info("Starting database it_workspace: %s", self.name)
            yield
        except Exception:
            _logger.exception("Database it_workspace failed: %s", self.name)
            escaped_tb = tools.html_escape(traceback.format_exc())
            self.message_post(  # pylint: disable=translation-required
                body="<p>%s</p><pre>%s</pre>"
                % (_("Database it_workspace failed."), escaped_tb),
                subtype=self.env.ref(
                    "erplibre_it.mail_message_subtype_failure"
                ),
            )
        else:
            _logger.info("Database it_workspace succeeded: %s", self.name)
            self.message_post(body=_("Database it_workspace succeeded."))

    @api.multi
    @contextmanager
    def it_create_exec_bundle(
        self, description, ignore_parent=False, succeed_msg=False
    ):
        self.ensure_one()
        value_bundle = {"it_workspace": self.id, "description": description}
        if not ignore_parent:
            it_exec_bundle_parent = self.env.context.get("it_exec_bundle")
            if it_exec_bundle_parent:
                value_bundle["parent_id"] = it_exec_bundle_parent
        it_exec_bundle_id = self.env["it.exec.bundle"].create(value_bundle)
        rec = self.with_context(it_exec_bundle=it_exec_bundle_id.id)
        try:
            yield rec
        except Warning as e:
            raise e
        except Exception as e:
            _logger.exception(
                f"'{description}' it.exec.bundle id '{it_exec_bundle_id.id}'"
                " failed"
            )
            escaped_tb = tools.html_escape(traceback.format_exc())
            error_value = {
                "description": description,
                "escaped_tb": escaped_tb,
                "it_workspace": rec.id,
                "it_exec_bundle_ids": it_exec_bundle_id.id,
            }
            partner_ids = [
                (
                    6,
                    0,
                    [
                        a.partner_id.id
                        for a in rec.message_follower_ids
                        if a.partner_id
                    ],
                )
            ]
            if partner_ids:
                error_value["partner_ids"] = partner_ids
            channel_ids = [
                (
                    6,
                    0,
                    [
                        a.channel_id.id
                        for a in rec.message_follower_ids
                        if a.channel_id
                    ],
                )
            ]
            if channel_ids:
                error_value["channel_ids"] = channel_ids
            # this is not true, cannot associate exec_id to this error
            # exec_id = it_exec_bundle_id.get_last_exec()
            # if exec_id:
            #     error_value["it_exec_ids"] = exec_id.id
            self.env["it.exec.error"].create(error_value)
            if rec.show_error_chatter:
                self.message_post(  # pylint: disable=translation-required
                    body="<p>%s</p><pre>%s</pre>"
                    % (
                        _("it.workspace '%s' failed.") % description,
                        escaped_tb,
                    ),
                    subtype=self.env.ref(
                        "erplibre_it.mail_message_subtype_failure"
                    ),
                    author_id=self.env.ref("base.user_root").partner_id.id,
                    partner_ids=partner_ids,
                    channel_ids=channel_ids,
                )
        else:
            if succeed_msg:
                _logger.info(
                    "it_workspace succeeded '%s': %s", self.name, description
                )

                partner_ids = [
                    (
                        6,
                        0,
                        [
                            a.partner_id.id
                            for a in rec.message_follower_ids
                            if a.partner_id
                        ],
                    )
                ]
                channel_ids = [
                    (
                        6,
                        0,
                        [
                            a.channel_id.id
                            for a in rec.message_follower_ids
                            if a.channel_id
                        ],
                    )
                ]

                self.message_post(
                    body=_("it_workspace succeeded '%s': %s")
                    % (self.name, description),
                    subtype=self.env.ref(
                        "erplibre_it.mail_message_subtype_success"
                    ),
                    author_id=self.env.ref("base.user_root").partner_id.id,
                    partner_ids=partner_ids,
                    channel_ids=channel_ids,
                )
        finally:
            # Finish bundle
            it_exec_bundle_id.exec_stop_date = fields.Datetime.now()
