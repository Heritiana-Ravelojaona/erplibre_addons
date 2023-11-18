# Copyright 2023 TechnoLibre inc. - Mathieu Benoit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import configparser
import json
import logging
import os
import tempfile
import uuid

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

from odoo import _, api, exceptions, fields, models, tools

CODE_GENERATOR_DIRECTORY = "./addons/TechnoLibre_odoo-code-generator-template/"
CODE_GENERATOR_DEMO_NAME = "code_generator_demo"
KEY_REPLACE_CODE_GENERATOR_DEMO = 'MODULE_NAME = "%s"'
_logger = logging.getLogger(__name__)


class DevopsCgNewProject(models.Model):
    _name = "devops.cg.new_project"
    _description = "Create new project for CG project"

    @api.model
    def default_stage_id(self):
        return self.env.ref("erplibre_devops.devops_cg_new_project_stage_init")

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )

    active = fields.Boolean(default=True)

    has_error = fields.Boolean(
        help="Will be True if got error into execution of new project.",
        readonly=True,
    )

    has_warning = fields.Boolean(
        help="Will be True if got warning into execution of new project.",
        readonly=True,
    )

    stage_id = fields.Many2one(
        comodel_name="devops.cg.new_project.stage",
        string="Stage",
        default=lambda s: s.default_stage_id(),
    )

    project_type = fields.Selection(
        selection=[("self", "Self generate"), ("cg", "Code generator")]
    )

    mode_view = fields.Selection(
        selection=[
            ("normal", "Normal"),
            ("wizard_view", "Wizard"),
            ("wizard_new_view", "New"),
        ],
        default="wizard_view",
    )

    last_new_project = fields.Many2one(
        comodel_name="devops.cg.new_project",
        string="Last new project",
    )

    exec_start_date = fields.Datetime(string="Execution start date")

    exec_stop_date = fields.Datetime(string="Execution stop date")

    exec_time_duration = fields.Float(
        string="Execution time duration",
        compute="_compute_exec_time_duration",
        store=True,
    )

    execution_finish = fields.Boolean(
        readonly=True, help="Will be True when execution finish correctly."
    )

    is_pause = fields.Boolean(
        help=(
            "Is pause is True when debug is execute and set at pause to run"
            " outside."
        ),
        readonly=True,
    )

    module = fields.Char(required=True)

    directory = fields.Char(required=True)

    directory_cg = fields.Char(
        help="Specify cg generator directory, or use directory."
    )

    directory_template = fields.Char(
        help="Specify template directory, or use directory."
    )

    config = fields.Char()

    code_generator_name = fields.Char()

    template_name = fields.Char()

    odoo_config = fields.Char(default="./config.conf")

    stop_execution_if_env_not_clean = fields.Boolean(default=True)

    force = fields.Boolean()

    active_coverage = fields.Boolean(help="Will enable coverage output file.")

    keep_bd_alive = fields.Boolean()

    can_setup_ide = fields.Boolean(
        compute="_compute_can_setup_ide",
        store=True,
    )

    config_debug_uc0 = fields.Boolean(help="Debug uC0.")

    config_debug_ucA = fields.Boolean(help="Debug uCA.")

    config_debug_ucB = fields.Boolean(help="Debug uCB.")

    breakpoint_uc0_first_line_hook = fields.Boolean(
        help="Breakpoint first line hook file uc0."
    )

    breakpoint_all_write_hook_begin = fields.Boolean(
        help="Breakpoint general when write hook."
    )

    breakpoint_all_write_hook_before_model = fields.Boolean(
        help=(
            "Breakpoint general when write hook before write model/fields into"
            " hook."
        )
    )

    breakpoint_all_write_hook_model_write_field = fields.Boolean(
        help=(
            "Breakpoint general when write hook while writing model, before"
            " write field. Can use field"
            " breakpoint_all_write_hook_model_write_field_config_field_name to"
            " specify field name."
        )
    )

    breakpoint_all_write_hook_model_write_field_config_field_name = fields.Char(
        help=(
            "Associate with breakpoint_all_write_hook_model_write_field , can"
            " set field name to break."
        )
    )

    breakpoint_all_write_hook_model_write_field_config_field_att = fields.Char(
        help=(
            "Associate with breakpoint_all_write_hook_model_write_field , can"
            " set attribute field name to break."
        )
    )

    breakpoint_ucA_first_line_hook = fields.Boolean(
        help="Breakpoint first line hook file ucA."
    )

    breakpoint_ucB_first_line_hook = fields.Boolean(
        help="Breakpoint first line hook file ucB."
    )

    breakpoint_uc0_bp_cg_uc0 = fields.Boolean(
        help="Breakpoint dans la section génération de code du uC0."
    )

    breakpoint_ucA_bp_cg_ucA = fields.Boolean(
        help="Breakpoint dans la section génération de code du uCA."
    )

    breakpoint_ucA_bp_extract_view_warning = fields.Boolean(
        help="Breakpoint uCA to diagnostic warning when extract view."
    )

    breakpoint_ucB_bp_generate_view_warning = fields.Boolean(
        help="Breakpoint uCB to diagnostic warning when generate view."
    )

    breakpoint_ucB_bp_cg_ucB = fields.Boolean(
        help="Breakpoint dans la section génération de code du uCB."
    )

    breakpoint_ucB_write_code_model_field = fields.Boolean(
        help=(
            "Breakpoint dans la section génération de code du uCB - write"
            " model field module. Can use field"
            " breakpoint_ucB_write_code_model_field_config_field_name to"
            " specify field name."
        )
    )

    breakpoint_ucB_write_code_model_field_config_model_name = fields.Char(
        help=(
            "Associate with breakpoint_ucB_write_code_model_field , can set"
            " model name to break."
        )
    )

    breakpoint_ucB_write_code_model_field_config_field_name = fields.Char(
        help=(
            "Associate with breakpoint_ucB_write_code_model_field , can set"
            " field name to break."
        )
    )

    # internal_error = fields.Char(
    # compute="_compute_internal_error",
    # store=True,
    # )
    # TODO need to support related field
    # devops_exec_error_ids = fields.One2many(
    # related="devops_exec_bundle_id.devops_exec_parent_error_ids"
    # )
    cg_hooks_py = fields.Char(help="Path of hooks python file.")

    template_hooks_py = fields.Char(help="Path of template hooks python file.")

    bd_name_demo = fields.Char(help="BD name for uc0")

    bd_name_template = fields.Char(help="BD name for ucA")

    bd_name_generator = fields.Char(help="BD name for ucB")

    code_generator_demo_hooks_py = fields.Char(
        help="Path of code_generator hooks python file."
    )

    code_generator_hooks_path_relative = fields.Char(
        help="Path of code_generator hooks python file relative path."
    )

    config_path = fields.Char(
        help="Path of temporary configuration file for execution."
    )

    module_path = fields.Char(help="Path of the module.")

    template_path = fields.Char(help="Path of the template.")

    cg_path = fields.Char(help="Path of the code generator.")

    code_generator_demo_path = fields.Char(help="Path of the uc0.")

    devops_exec_bundle_id = fields.Many2one(
        comodel_name="devops.exec.bundle",
        string="Devops Exec Bundle",
    )

    devops_workspace = fields.Many2one(comodel_name="devops.workspace")

    ide_pycharm_configuration_ids = fields.One2many(
        comodel_name="devops.ide.pycharm.configuration",
        inverse_name="devops_cg_new_project_id",
        string="Pycharm configurations",
    )

    devops_exec_ids = fields.One2many(
        comodel_name="devops.exec",
        inverse_name="new_project_id",
        string="Executions",
    )

    log_error_ids = fields.One2many(
        comodel_name="devops.log.error",
        inverse_name="new_project_id",
        string="Log errors",
        readonly=True,
    )

    log_warning_ids = fields.One2many(
        comodel_name="devops.log.warning",
        inverse_name="new_project_id",
        string="Log warnings",
        readonly=True,
    )

    new_project_with_code_generator = fields.Boolean(
        default=True,
        help=(
            "Need to enable this feature if the goal is to do new_project with"
            " the code generator. Because by default, it will be installed."
            " Not working how I assume, its take 40 seconds more. Stay it at"
            " default = True."
        ),
    )

    @api.depends(
        "devops_workspace",
        "module",
        "exec_start_date",
        "exec_stop_date",
        "exec_time_duration",
    )
    def _compute_name(self):
        for rec in self:
            if not isinstance(rec.id, models.NewId):
                rec.name = f"{rec.id}: "
            else:
                rec.name = ""
            rec.name += f"{rec.devops_workspace.name} - {rec.module}"
            if rec.exec_stop_date:
                rec.name += (
                    f" - finish {rec.exec_stop_date} duration"
                    f" {rec.exec_time_duration}"
                )
            elif rec.exec_start_date:
                rec.name += f" - start {rec.exec_start_date}"

    @api.depends(
        "config_debug_uc0",
        "config_debug_ucA",
        "config_debug_ucB",
        "breakpoint_all_write_hook_begin",
        "breakpoint_all_write_hook_before_model",
        "breakpoint_all_write_hook_model_write_field",
        "breakpoint_uc0_first_line_hook",
        "breakpoint_ucA_first_line_hook",
        "breakpoint_ucB_first_line_hook",
        "breakpoint_uc0_bp_cg_uc0",
        "breakpoint_ucA_bp_cg_ucA",
        "breakpoint_ucB_bp_cg_ucB",
        "breakpoint_ucA_bp_extract_view_warning",
        "breakpoint_ucB_bp_generate_view_warning",
        "breakpoint_ucB_write_code_model_field",
    )
    def _compute_can_setup_ide(self):
        for rec in self:
            rec.can_setup_ide = (
                rec.config_debug_uc0
                + rec.config_debug_ucA
                + rec.config_debug_ucB
                + rec.breakpoint_all_write_hook_begin
                + rec.breakpoint_all_write_hook_before_model
                + rec.breakpoint_all_write_hook_model_write_field
                + rec.breakpoint_uc0_first_line_hook
                + rec.breakpoint_ucA_first_line_hook
                + rec.breakpoint_ucB_first_line_hook
                + rec.breakpoint_uc0_bp_cg_uc0
                + rec.breakpoint_ucA_bp_cg_ucA
                + rec.breakpoint_ucB_bp_cg_ucB
                + rec.breakpoint_ucA_bp_extract_view_warning
                + rec.breakpoint_ucB_bp_generate_view_warning
                + rec.breakpoint_ucB_write_code_model_field
            )

    def action_new_project_clear_pause(self, ctx=None):
        for rec in self:
            with rec.devops_workspace.devops_create_exec_bundle(
                "New project clear pause",
                devops_cg_new_project=rec.id,
                ctx=ctx,
            ) as rec_ws:
                rec.is_pause = False
                rec.config_debug_uc0 = False
                rec.config_debug_ucA = False
                rec.config_debug_ucB = False
                rec.breakpoint_all_write_hook_begin = False
                rec.breakpoint_all_write_hook_before_model = False
                rec.breakpoint_all_write_hook_model_write_field = False
                rec.breakpoint_uc0_first_line_hook = False
                rec.breakpoint_ucA_first_line_hook = False
                rec.breakpoint_ucB_first_line_hook = False
                rec.breakpoint_uc0_bp_cg_uc0 = False
                rec.breakpoint_ucA_bp_cg_ucA = False
                rec.breakpoint_ucB_bp_cg_ucB = False
                rec.breakpoint_ucA_bp_extract_view_warning = False
                rec.breakpoint_ucB_bp_generate_view_warning = False
                rec.breakpoint_ucB_write_code_model_field = False

    @api.depends("exec_start_date", "exec_stop_date")
    def _compute_exec_time_duration(self):
        for rec in self:
            if rec.exec_start_date and rec.exec_stop_date:
                rec.exec_time_duration = (
                    rec.exec_stop_date - rec.exec_start_date
                ).total_seconds()
            else:
                rec.exec_time_duration = None

    @api.multi
    def action_new_project_debug(self, ctx=None):
        for rec in self:
            with rec.devops_workspace.devops_create_exec_bundle(
                "New project debug", devops_cg_new_project=rec.id, ctx=ctx
            ) as rec_ws:
                has_debug = False
                stage_uc0 = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_uc0"
                )
                if rec.stage_id == stage_uc0:
                    rec.config_debug_uc0 = True
                    has_debug = True
                stage_uca = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_uca"
                )
                if rec.stage_id == stage_uca:
                    rec.config_debug_ucA = True
                    has_debug = True
                stage_ucb = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_ucb"
                )
                if rec.stage_id == stage_ucb:
                    rec.config_debug_ucB = True
                    has_debug = True
                if has_debug:
                    rec.with_context(rec_ws._context).action_new_project()
                else:
                    raise exceptions.Warning(
                        "Cannot support debug for this stage"
                    )

    @api.multi
    def action_new_project_setup_IDE(
        self,
        ctx=None,
        conf_add_mode=None,
        conf_add_db=None,
        conf_add_module=None,
        conf_add_config_path="config.conf",
        is_test=False,
    ):
        lst_test = []
        for rec in self:
            with rec.devops_workspace.devops_create_exec_bundle(
                "New project setup IDE", devops_cg_new_project=rec.id, ctx=ctx
            ) as rec_ws:
                if not rec.can_setup_ide and not is_test:
                    continue
                has_bp = rec_ws._context.get(
                    "new_project_with_breakpoint", True
                )

                if is_test or (has_bp and rec.breakpoint_all_write_hook_begin):
                    file = "addons/TechnoLibre_odoo-code-generator/code_generator_hook/models/code_generator_writer.py"
                    key = "if post_init_hook_feature_code_generator:"
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (
                    has_bp and rec.breakpoint_all_write_hook_before_model
                ):
                    file = "addons/TechnoLibre_odoo-code-generator/code_generator_hook/models/code_generator_writer.py"
                    key = (
                        "lst_dependency = \[a.name for a in"
                        " model_id.inherit_model_ids\]"
                    )
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (
                    has_bp and rec.breakpoint_all_write_hook_model_write_field
                ):
                    if (
                        rec.breakpoint_all_write_hook_model_write_field_config_field_name
                    ):
                        condition = f'key=="{rec.breakpoint_all_write_hook_model_write_field_config_field_name}"'
                        if (
                            rec.breakpoint_all_write_hook_model_write_field_config_field_att
                        ):
                            condition += (
                                " and"
                                f' subkey=="{rec.breakpoint_all_write_hook_model_write_field_config_field_att}"'
                            )
                    else:
                        condition = None

                    file = "addons/TechnoLibre_odoo-code-generator/code_generator_hook/models/code_generator_writer.py"
                    key = "self._write_dict_key(cw, subkey, value)"
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(
                            file=file, key=key, condition=condition
                        )
                if is_test or (has_bp and rec.breakpoint_uc0_first_line_hook):
                    file = rec.code_generator_demo_hooks_py
                    key = "env = api.Environment(cr, SUPERUSER_ID, {})"
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (has_bp and rec.breakpoint_ucA_first_line_hook):
                    file = rec.template_hooks_py
                    key = "env = api.Environment(cr, SUPERUSER_ID, {})"
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (has_bp and rec.breakpoint_ucB_first_line_hook):
                    file = rec.cg_hooks_py
                    key = "env = api.Environment(cr, SUPERUSER_ID, {})"
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (has_bp and rec.breakpoint_uc0_bp_cg_uc0):
                    file = "addons/TechnoLibre_odoo-code-generator/code_generator_hook/models/code_generator_writer.py"
                    key = 'cw.emit("new_module_name = MODULE_NAME")'
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (
                    has_bp
                    and (
                        rec.breakpoint_ucA_bp_cg_ucA
                        or rec.breakpoint_ucB_bp_cg_ucB
                    )
                ):
                    file = "addons/TechnoLibre_odoo-code-generator/code_generator/models/code_generator_writer.py"
                    key = (
                        "if module.template_model_name or"
                        " module.template_inherit_model_name:"
                    )
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (
                    has_bp and rec.breakpoint_ucA_bp_extract_view_warning
                ):
                    file = "addons/TechnoLibre_odoo-code-generator/code_generator/extractor_view.py"
                    key = "_logger.warning("
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (
                    has_bp and rec.breakpoint_ucB_bp_generate_view_warning
                ):
                    file = "addons/TechnoLibre_odoo-code-generator/code_generator/wizards/code_generator_generate_views_wizard.py"
                    key = "_logger.warning("
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(file=file, key=key)
                if is_test or (
                    has_bp and rec.breakpoint_ucB_write_code_model_field
                ):
                    lst_condition = []
                    if (
                        rec.breakpoint_ucB_write_code_model_field_config_model_name
                    ):
                        lst_condition.append(
                            f'model.model=="{rec.breakpoint_ucB_write_code_model_field_config_model_name}"'
                        )
                    if (
                        rec.breakpoint_ucB_write_code_model_field_config_field_name
                    ):
                        lst_condition.append(
                            f'f2export.name=="{rec.breakpoint_ucB_write_code_model_field_config_field_name}"'
                        )
                    if lst_condition:
                        condition = " and ".join(lst_condition)
                    else:
                        condition = None
                    file = "addons/TechnoLibre_odoo-code-generator/code_generator/models/code_generator_writer.py"
                    key = "dct_field_attr_diff = defaultdict(list)"
                    if is_test:
                        lst_test.append((file, key))
                    else:
                        rec.add_breakpoint(
                            file=file, key=key, condition=condition
                        )
                if conf_add_mode and not is_test:
                    rec_ws.ide_pycharm.add_configuration(
                        conf_add_mode=conf_add_mode,
                        conf_add_db=conf_add_db,
                        conf_add_module=conf_add_module,
                        conf_add_config_path=conf_add_config_path,
                    )
                if is_test:
                    return lst_test

    @api.multi
    def action_run_test(self, ctx=None):
        for rec in self:
            with rec.devops_workspace.devops_create_exec_bundle(
                "New project run test",
                devops_cg_new_project=rec.id,
                ctx=ctx,
            ) as rec_ws:
                rec = rec.with_context(rec_ws._context)
                lst_test = rec.action_new_project_setup_IDE(is_test=True)
                if not lst_test:
                    msg = f"List of breakpoint is empty."
                    _logger.error(msg)
                    raise exceptions.Warning(msg)
                for file, key in lst_test:
                    if not file:
                        # Ignore this breakpoint, the file doesn't exist, missing variable
                        continue
                    try:
                        lst_line = rec.get_no_line_breakpoint(
                            key, file, rec_ws
                        )
                    except Exception as e:
                        raise exceptions.Warning(e)
                    if not lst_line:
                        msg = (
                            f"Cannot find breakpoint for file {file}, key :"
                            f" {key}"
                        )
                        _logger.error(msg)
                        raise exceptions.Warning(msg)
                _logger.info("Test pass")

    @api.multi
    def action_new_project(self, ctx=None):
        for rec in self:
            with rec.devops_workspace.devops_create_exec_bundle(
                "Generate new project with CG",
                devops_cg_new_project=rec.id,
                ctx=ctx,
            ) as rec_ws:
                rec.is_pause = False
                rec.exec_start_date = fields.Datetime.now(self)
                rec.has_error = False
                rec.has_warning = False
                id_exec_bundle = self.env.context.get("devops_exec_bundle")
                exec_bundle_parent_id = self.env["devops.exec.bundle"].browse(
                    id_exec_bundle
                )
                stage_init_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_init"
                )
                stage_gen_conf_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_config"
                )
                stage_uc0_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_uc0"
                )
                stage_uca_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_uca"
                )
                stage_ucb_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_ucb"
                )
                # stage_terminate_id = self.env.ref(
                #     "erplibre_devops.devops_cg_new_project_stage_generate_terminate"
                # )

                if rec.stage_id == stage_init_id:
                    rec.action_init(rec_ws=rec_ws)

                if (
                    not exec_bundle_parent_id.devops_exec_parent_error_ids
                    and rec.stage_id == stage_gen_conf_id
                ):
                    rec.action_generate_config(rec_ws=rec_ws)
                else:
                    rec.has_error = True
                if (
                    not exec_bundle_parent_id.devops_exec_parent_error_ids
                    and rec.stage_id == stage_uc0_id
                ):
                    rec.action_generate_uc0(rec_ws=rec_ws)
                else:
                    rec.has_error = True
                if (
                    not exec_bundle_parent_id.devops_exec_parent_error_ids
                    and rec.stage_id == stage_uca_id
                ):
                    rec.action_generate_uca(rec_ws=rec_ws)
                else:
                    rec.has_error = True
                if (
                    not exec_bundle_parent_id.devops_exec_parent_error_ids
                    and rec.stage_id == stage_ucb_id
                ):
                    rec.action_generate_ucb(rec_ws=rec_ws)
                else:
                    rec.has_error = True

                rec.exec_stop_date = fields.Datetime.now(self)
                rec.execution_finish = True
                if rec.log_error_ids:
                    rec.has_error = True
                if rec.log_warning_ids:
                    rec.has_warning = True

    @api.multi
    def action_init(self, ctx=None, rec_ws=None):
        for rec in self:
            ws_param = rec_ws if rec_ws else rec.devops_workspace
            with ws_param.devops_create_exec_bundle(
                "New project generate 1.init", devops_cg_new_project=rec.id
            ) as ws:
                rec.stage_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_init"
                )
                if not ws.os_path_exists(rec.directory, to_instance=True):
                    msg_error = f"Path directory '{rec.directory}' not exist."
                    raise Exception(msg_error)

                if not rec.directory_cg:
                    rec.directory_cg = rec.directory
                if not ws.os_path_exists(rec.directory_cg, to_instance=True):
                    msg_error = (
                        f"Path cg directory '{rec.directory_cg}' not exist."
                    )
                    raise Exception(msg_error)

                if not rec.directory_template:
                    rec.directory_template = rec.directory
                if not ws.os_path_exists(
                    rec.directory_template, to_instance=True
                ):
                    msg_error = (
                        f"Path template directory '{rec.directory_template}'"
                        " not exist."
                    )
                    raise Exception(msg_error)

                if not rec.module:
                    msg_error = "Module name is missing."
                    raise Exception(msg_error)

                # Get code_generator name
                if not rec.code_generator_name:
                    rec.code_generator_name = f"code_generator_{rec.module}"

                # Get template name
                if not rec.template_name:
                    rec.template_name = f"code_generator_template_{rec.module}"

                # TODO copy directory in temp workspace file before update it
                rec.module_path = os.path.join(rec.directory, rec.module)
                is_over = rec.validate_path_ready_to_be_override(
                    rec.module, rec.directory, ws, path=rec.module_path
                )
                if not rec.force and not is_over:
                    msg_error = (
                        f"Cannot generate on module path '{rec.module_path}'"
                    )
                    raise Exception(msg_error)

                rec.cg_path = os.path.join(
                    rec.directory_cg, rec.code_generator_name
                )
                rec.cg_hooks_py = os.path.join(rec.cg_path, "hooks.py")
                if (
                    not rec.force
                    and not rec.validate_path_ready_to_be_override(
                        rec.code_generator_name,
                        rec.directory_cg,
                        ws,
                        path=rec.cg_path,
                    )
                ):
                    msg_error = f"Cannot generate on cg path '{rec.cg_path}'"
                    raise Exception(msg_error)

                rec.template_path = os.path.join(
                    rec.directory_template, rec.template_name
                )
                rec.template_hooks_py = os.path.join(
                    rec.template_path, "hooks.py"
                )
                if (
                    not rec.force
                    and not rec.validate_path_ready_to_be_override(
                        rec.template_name,
                        rec.directory_template,
                        ws,
                        path=rec.template_path,
                    )
                ):
                    msg_error = (
                        "Cannot generate on template path"
                        f" '{rec.template_path}'"
                    )
                    raise Exception(msg_error)

                # Validate code_generator_demo
                rec.code_generator_demo_path = os.path.join(
                    CODE_GENERATOR_DIRECTORY, CODE_GENERATOR_DEMO_NAME
                )
                rec.code_generator_demo_hooks_py = os.path.join(
                    rec.code_generator_demo_path, "hooks.py"
                )
                rec.code_generator_hooks_path_relative = os.path.join(
                    CODE_GENERATOR_DEMO_NAME, "hooks.py"
                )
                if not ws.os_path_exists(
                    rec.code_generator_demo_path, to_instance=True
                ):
                    msg_error = (
                        "code_generator_demo is not accessible"
                        f" '{rec.code_generator_demo_path}'"
                    )
                    raise Exception(msg_error)

                rec.stage_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_config"
                )

    @api.multi
    def action_generate_config(self, ctx=None, rec_ws=None):
        for rec in self:
            ws_param = rec_ws if rec_ws else rec.devops_workspace
            with ws_param.devops_create_exec_bundle(
                "New project generate 2.config", devops_cg_new_project=rec.id
            ) as ws:
                rec.stage_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_config"
                )

                if not (
                    rec.validate_path_ready_to_be_override(
                        CODE_GENERATOR_DEMO_NAME, CODE_GENERATOR_DIRECTORY, ws
                    )
                    and self.search_and_replace_file(
                        rec.code_generator_demo_hooks_py,
                        [
                            (
                                KEY_REPLACE_CODE_GENERATOR_DEMO
                                % CODE_GENERATOR_DEMO_NAME,
                                KEY_REPLACE_CODE_GENERATOR_DEMO
                                % rec.template_name,
                            ),
                            (
                                'value["enable_sync_template"] = False',
                                'value["enable_sync_template"] = True',
                            ),
                            (
                                "# path_module_generate ="
                                " os.path.normpath(os.path.join(os.path.dirname(__file__),"
                                " '..'))",
                                f'path_module_generate = "{rec.directory}"',
                            ),
                            (
                                '# "path_sync_code": path_module_generate,',
                                '"path_sync_code": path_module_generate,',
                            ),
                            (
                                '# value["template_module_path_generated_extension"]'
                                ' = "."',
                                'value["template_module_path_generated_extension"]'
                                f' = "{rec.directory_cg}"',
                            ),
                        ],
                    )
                ):
                    return False

                # Update configuration
                config = configparser.ConfigParser()
                config.read(rec.odoo_config)
                addons_path = config.get("options", "addons_path")
                lst_addons_path = addons_path.split(",")
                lst_directory = list(
                    {
                        rec.directory_cg,
                        rec.directory,
                        rec.directory_template,
                    }
                )
                has_change = False
                for new_addons_path in lst_directory:
                    for actual_addons_path in lst_addons_path:
                        if not actual_addons_path:
                            continue
                        # Validate if not existing and valide is different path
                        relative_actual_addons_path = os.path.relpath(
                            actual_addons_path
                        )
                        relative_new_addons_path = os.path.relpath(
                            new_addons_path
                        )
                        if (
                            relative_actual_addons_path
                            == relative_new_addons_path
                        ):
                            break
                    else:
                        lst_addons_path.insert(0, new_addons_path)
                        has_change = True
                if has_change:
                    config.set(
                        "options", "addons_path", ",".join(lst_addons_path)
                    )
                temp_file = tempfile.mktemp()
                with open(temp_file, "w") as configfile:
                    config.write(configfile)
                _logger.info(f"Create temporary config file: {temp_file}")
                rec.config_path = temp_file

                rec.stage_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_uc0"
                )

    @api.multi
    def action_generate_uc0(self, ctx=None, rec_ws=None):
        for rec in self:
            ws_param = rec_ws if rec_ws else rec.devops_workspace
            with ws_param.devops_create_exec_bundle(
                "New project generate 3.Uc0", devops_cg_new_project=rec.id
            ) as ws:
                rec.stage_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_uc0"
                )
                if not rec.bd_name_demo:
                    rec.bd_name_demo = (
                        f"new_project_code_generator_demo_{uuid.uuid4()}"[:63]
                    )

                if rec.new_project_with_code_generator:
                    cmd = (
                        "./script/database/db_restore.py --database"
                        f" {rec.bd_name_demo}"
                    )
                else:
                    cmd = (
                        "./script/database/db_restore.py --database"
                        f" {rec.bd_name_demo} --restore_image"
                        " addons_install_code_generator_basic"
                    )
                _logger.info(cmd)
                exec_id = ws.execute(cmd=cmd, to_instance=True)
                rec.has_error = bool(exec_id.devops_exec_error_ids.exists())
                if rec.has_error:
                    _logger.info("Exit new project")
                    continue

                # TODO need pause if ask? and continue if ask
                if rec.can_setup_ide:
                    _logger.info(
                        "========= Ask stop, setup pycharm and exit ========="
                    )
                    rec.is_pause = True
                    # rec.config_path is a temporary file, it will not work. Use default config instead
                    rec.action_new_project_setup_IDE(
                        conf_add_mode="install",
                        conf_add_db=rec.bd_name_demo,
                        conf_add_module="code_generator_demo",
                        # conf_add_config_path=rec.config_path,
                    )
                    continue

                _logger.info(
                    "========= GENERATE code_generator_demo ========="
                )

                if rec.active_coverage:
                    cmd = (
                        "./script/addons/coverage_install_addons_dev.sh"
                        f" {rec.bd_name_demo} code_generator_demo"
                        f" {rec.config_path}"
                    )
                else:
                    cmd = (
                        "./script/addons/install_addons_dev.sh"
                        f" {rec.bd_name_demo} code_generator_demo"
                        f" {rec.config_path}"
                    )
                exec_id = ws.with_context(
                    devops_cg_new_project=rec.id
                ).execute(cmd=cmd, to_instance=True)
                rec.has_error = bool(exec_id.devops_exec_error_ids.exists())
                if rec.has_error:
                    _logger.info("Exit new project")
                    continue

                if not self.keep_bd_alive:
                    cmd = (
                        "./.venv/bin/python3 ./odoo/odoo-bin db --drop"
                        f" --database {rec.bd_name_demo}"
                    )
                    _logger.info(cmd)
                    ws.execute(cmd=cmd, to_instance=True)

                # Revert code_generator_demo
                self.restore_git_code_generator_demo(
                    CODE_GENERATOR_DIRECTORY,
                    rec.code_generator_hooks_path_relative,
                )

                # Validate
                if not ws.os_path_exists(rec.template_path, to_instance=True):
                    raise Exception(
                        f"Module template not exists '{rec.template_path}'"
                    )
                else:
                    _logger.info(
                        f"Module template exists '{rec.template_path}'"
                    )
                if not rec.has_error:
                    rec.stage_id = self.env.ref(
                        "erplibre_devops.devops_cg_new_project_stage_generate_uca"
                    )

    @api.multi
    def action_generate_uca(self, ctx=None, rec_ws=None):
        for rec in self:
            ws_param = rec_ws if rec_ws else rec.devops_workspace
            with ws_param.devops_create_exec_bundle(
                "New project generate 4.UcA", devops_cg_new_project=rec.id
            ) as ws:
                rec.stage_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_uca"
                )
                lst_template_hooks_py_replace = []
                if rec.mode_view in ["wizard_view", "wizard_new_view"]:
                    lst_template_hooks_py_replace.append(
                        (
                            'value["enable_template_wizard_view"] = False',
                            'value["enable_template_wizard_view"] = True',
                        )
                    )
                    if rec.mode_view == "wizard_new_view":
                        lst_template_hooks_py_replace.append(
                            (
                                'value["force_generic_template_wizard_view"] ='
                                " False",
                                'value["force_generic_template_wizard_view"] ='
                                " True",
                            )
                        )

                # Add model from config
                if self.config:
                    config = json.loads(self.config)
                    config_lst_model = config.get("model")
                    str_lst_model = "; ".join(
                        [a.get("name") for a in config_lst_model]
                    )
                    old_str = 'value["template_model_name"] = ""'
                    new_str = (
                        f'value["template_model_name"] = "{str_lst_model}"'
                    )
                    lst_template_hooks_py_replace.append((old_str, new_str))

                if lst_template_hooks_py_replace:
                    self.search_and_replace_file(
                        rec.template_hooks_py,
                        lst_template_hooks_py_replace,
                    )

                # Execute all
                if not rec.bd_name_template:
                    rec.bd_name_template = (
                        f"new_project_code_generator_template_{uuid.uuid4()}"[
                            :63
                        ]
                    )

                if rec.new_project_with_code_generator:
                    cmd = (
                        "./script/database/db_restore.py --database"
                        f" {rec.bd_name_template}"
                    )
                else:
                    cmd = (
                        "./script/database/db_restore.py --database"
                        f" {rec.bd_name_template} --restore_image"
                        " addons_install_code_generator_basic"
                    )
                exec_id = ws.with_context(
                    devops_cg_new_project=rec.id
                ).execute(cmd=cmd, to_instance=True)
                rec.has_error = bool(exec_id.devops_exec_error_ids.exists())
                if rec.has_error:
                    _logger.info("Exit new project")
                    continue
                _logger.info(cmd)
                _logger.info(
                    f"========= GENERATE {rec.template_name} ========="
                )
                # TODO maybe the module exist somewhere else
                if ws.os_path_exists(rec.module_path, to_instance=True):
                    # Install module before running code generator
                    cmd = (
                        "./script/code_generator/search_class_model.py"
                        f" --quiet -d {rec.module_path} -t {rec.template_path}"
                    )
                    _logger.info(cmd)
                    exec_id = ws.with_context(
                        devops_cg_new_project=rec.id
                    ).execute(cmd=cmd, to_instance=True)
                    rec.has_error = bool(
                        exec_id.devops_exec_error_ids.exists()
                    )
                    if rec.has_error:
                        _logger.info("Exit new project")
                        continue

                    # TODO do we need to diagnostic installing module?

                    if rec.active_coverage:
                        cmd = (
                            "./script/addons/coverage_install_addons_dev.sh"
                            f" {rec.bd_name_template} {rec.module} {rec.config_path}"
                        )
                    else:
                        cmd = (
                            "./script/addons/install_addons_dev.sh"
                            f" {rec.bd_name_template} {rec.module} {rec.config_path}"
                        )
                    _logger.info(cmd)
                    exec_id = ws.with_context(
                        devops_cg_new_project=rec.id
                    ).execute(cmd=cmd, to_instance=True)
                    rec.has_error = bool(
                        exec_id.devops_exec_error_ids.exists()
                    )
                    if rec.has_error:
                        _logger.info("Exit new project")
                        continue

                # TODO need pause if ask? and continue if ask
                if rec.can_setup_ide:
                    _logger.info(
                        "========= Ask stop, setup pycharm and exit ========="
                    )
                    rec.is_pause = True
                    # rec.config_path is a temporary file, it will not work. Use default config instead
                    rec.action_new_project_setup_IDE(
                        conf_add_mode="install",
                        conf_add_db=rec.bd_name_template,
                        conf_add_module=rec.template_name,
                        # conf_add_config_path=rec.config_path,
                    )
                    continue

                if rec.active_coverage:
                    cmd = (
                        "./script/addons/coverage_install_addons_dev.sh"
                        f" {rec.bd_name_template} {rec.template_name} {rec.config_path}"
                    )
                else:
                    cmd = (
                        "./script/addons/install_addons_dev.sh"
                        f" {rec.bd_name_template}"
                        f" {rec.template_name} {rec.config_path}"
                    )
                _logger.info(cmd)
                exec_id = ws.with_context(
                    devops_cg_new_project=rec.id
                ).execute(cmd=cmd, to_instance=True)

                rec.has_error = bool(exec_id.devops_exec_error_ids.exists())

                if not self.keep_bd_alive:
                    cmd = (
                        "./.venv/bin/python3 ./odoo/odoo-bin db --drop"
                        f" --database {rec.bd_name_template}"
                    )
                    _logger.info(cmd)
                    ws.execute(cmd=cmd, to_instance=True)

                # Validate
                if not ws.os_path_exists(rec.cg_path, to_instance=True):
                    raise Exception(f"Module cg not exists '{rec.cg_path}'")
                else:
                    _logger.info(f"Module cg exists '{rec.cg_path}'")

                if not rec.has_error:
                    rec.stage_id = self.env.ref(
                        "erplibre_devops.devops_cg_new_project_stage_generate_ucb"
                    )

    @api.multi
    def action_generate_ucb(self, ctx=None, rec_ws=None):
        for rec in self:
            ws_param = rec_ws if rec_ws else rec.devops_workspace
            with ws_param.devops_create_exec_bundle(
                "New project generate 5.UcB", devops_cg_new_project=rec.id
            ) as ws:
                rec.stage_id = self.env.ref(
                    "erplibre_devops.devops_cg_new_project_stage_generate_ucb"
                )
                if not rec.bd_name_generator:
                    rec.bd_name_generator = (
                        f"new_project_code_generator_{uuid.uuid4()}"[:63]
                    )

                if rec.new_project_with_code_generator:
                    cmd = (
                        "./script/database/db_restore.py --database"
                        f" {rec.bd_name_generator}"
                    )
                else:
                    cmd = (
                        "./script/database/db_restore.py --database"
                        f" {rec.bd_name_generator} --restore_image"
                        " addons_install_code_generator_basic"
                    )
                _logger.info(cmd)
                exec_id = ws.with_context(
                    devops_cg_new_project=rec.id
                ).execute(cmd=cmd, to_instance=True)
                _logger.info(
                    f"========= GENERATE {rec.code_generator_name} ========="
                )

                rec.has_error = bool(exec_id.devops_exec_error_ids.exists())
                if rec.has_error:
                    _logger.info("Exit new project")
                    continue

                # Add field from config
                if self.config:
                    lst_update_cg = []
                    config = json.loads(self.config)
                    config_lst_model = config.get("model")
                    for model in config_lst_model:
                        model_name = model.get("name")
                        dct_field = {}
                        for a in model.get("fields"):
                            dct_value = {"ttype": a.get("type")}
                            if "relation" in a.keys():
                                dct_value["relation"] = a["relation"]
                            if "relation_field" in a.keys():
                                dct_value["relation_field"] = a[
                                    "relation_field"
                                ]
                            if "description" in a.keys():
                                dct_value["field_description"] = a[
                                    "description"
                                ]
                            dct_field[a.get("name")] = dct_value
                        if "name" not in dct_field.keys():
                            dct_field["name"] = {"ttype": "char"}
                        old_str = (
                            f'model_model = "{model_name}"\n       '
                            " code_generator_id.add_update_model(model_model)"
                        )
                        new_str = (
                            f'model_model = "{model_name}"\n        dct_field'
                            f" = {dct_field}\n       "
                            " code_generator_id.add_update_model(model_model,"
                            " dct_field=dct_field)"
                        )
                        lst_update_cg.append((old_str, new_str))

                    # Force add menu and access
                    # if rec.mode_view in ["wizard_view", "wizard_new_view"]:
                    #     lst_update_cg.append(
                    #         ('"disable_generate_menu": True,', "")
                    #     )
                    # lst_update_cg.append(
                    #     ('"disable_generate_access": True,', "")
                    # )
                    self.search_and_replace_file(
                        rec.cg_hooks_py,
                        lst_update_cg,
                    )

                # TODO need pause if ask? and continue if ask
                if rec.can_setup_ide:
                    _logger.info(
                        "========= Ask stop, setup pycharm and exit ========="
                    )
                    rec.is_pause = True
                    # rec.config_path is a temporary file, it will not work. Use default config instead
                    rec.action_new_project_setup_IDE(
                        conf_add_mode="install",
                        conf_add_db=rec.bd_name_generator,
                        conf_add_module=rec.code_generator_name,
                        # conf_add_config_path=rec.config_path,
                    )
                    continue

                if rec.active_coverage:
                    cmd = (
                        "./script/addons/coverage_install_addons_dev.sh"
                        f" {rec.bd_name_generator} {rec.code_generator_name} {rec.config_path}"
                    )
                else:
                    cmd = (
                        "./script/addons/install_addons_dev.sh"
                        f" {rec.bd_name_generator} {rec.code_generator_name} {rec.config_path}"
                    )
                _logger.info(cmd)
                exec_id = ws.with_context(
                    devops_cg_new_project=rec.id
                ).execute(
                    cmd=cmd,
                    to_instance=True,
                )

                rec.has_error = bool(exec_id.devops_exec_error_ids.exists())

                if not self.keep_bd_alive:
                    cmd = (
                        "./.venv/bin/python3 ./odoo/odoo-bin db --drop"
                        f" --database {rec.bd_name_generator}"
                    )
                    _logger.info(cmd)
                    ws.execute(cmd=cmd, to_instance=True)

                # Validate
                if not ws.os_path_exists(rec.module_path, to_instance=True):
                    raise Exception(f"Module not exists '{rec.module_path}'")
                else:
                    _logger.info(f"Module exists '{rec.module_path}'")

                if not rec.has_error:
                    rec.stage_id = rec.env.ref(
                        "erplibre_devops.devops_cg_new_project_stage_generate_terminate"
                    )

    @api.model
    def validate_path_ready_to_be_override(self, name, directory, ws, path=""):
        if not path:
            path = os.path.join(directory, name)
        if not ws.os_path_exists(path, to_instance=True):
            return True
        # Check if in git
        # TODO complete me, need to check into instance
        try:
            git_repo = Repo(directory)
        except NoSuchPathError:
            raise Exception(f"Directory not existing '{directory}'")
        except InvalidGitRepositoryError:
            raise Exception(
                f"The path '{path}' exist, but no git repo, use force to"
                " ignore it."
            )

        if self.stop_execution_if_env_not_clean:
            status = git_repo.git.status(name, porcelain=True)
            if status:
                msg = (
                    f"The directory '{path}' has git difference, use force to"
                    " ignore it."
                )
                raise Exception(msg)
        return True

    @staticmethod
    def restore_git_code_generator_demo(
        code_generator_demo_path, relative_path
    ):
        # TODO support to remote
        try:
            git_repo = Repo(code_generator_demo_path)
        except NoSuchPathError:
            raise Exception(
                f"Directory not existing '{code_generator_demo_path}'"
            )
        except InvalidGitRepositoryError:
            raise Exception(
                f"The path '{code_generator_demo_path}' exist, but no git repo"
            )

        git_repo.git.restore(relative_path)

    @api.model
    def get_no_line_breakpoint(self, key, file, ws):
        key = key.replace('"', '\\"')
        cmd = f'grep -n "{key}" {file}'
        cmd += " | awk -F: '{print $1}'"
        result = ws.execute(to_instance=True, cmd=cmd, engine="sh")
        try:
            lst_no_line = [int(a) for a in result.log_all.strip().split("\n")]
        except:
            raise Exception(
                f"Wrong output command : {cmd}\n{result.log_all.strip()}"
            )
        return lst_no_line

    @api.model
    def add_breakpoint(
        self, file=None, key=None, no_line=None, condition=None
    ):
        for rec in self:
            with rec.devops_workspace.devops_create_exec_bundle(
                "New project add breakpoint", devops_cg_new_project=rec.id
            ) as rec_ws:
                file_path = os.path.normpath(
                    os.path.join(
                        rec_ws.folder,
                        file,
                    )
                )
                lst_no_line = []
                if key:
                    lst_no_line = rec.get_no_line_breakpoint(key, file, rec_ws)
                elif no_line:
                    lst_no_line = [int(no_line)]

                if lst_no_line:
                    for i_no_line in lst_no_line:
                        rec_ws.ide_pycharm.add_breakpoint(
                            file_path, i_no_line - 1, condition=condition
                        )
                else:
                    _logger.warning(
                        "Missing no_line to method add_breakpoint. Or specify"
                        " a key to research from file."
                    )

    @staticmethod
    def search_and_replace_file(filepath, lst_search_and_replace):
        """
        lst_search_and_replace is a list of tuple, first item is search, second is replace
        """
        with open(filepath, "r") as file:
            txt = file.read()
            for search, replace in lst_search_and_replace:
                if search not in txt:
                    msg_error = f"Cannot find '{search}' in file '{filepath}'"
                    raise Exception(msg_error)
                txt = txt.replace(search, replace)
        with open(filepath, "w") as file:
            file.write(txt)
        return True

    @api.multi
    def action_kill_pycharm(self):
        self.ensure_one()
        self.devops_workspace.ide_pycharm.action_kill_pycharm()

    @api.multi
    def action_start_pycharm(self):
        self.ensure_one()
        self.devops_workspace.ide_pycharm.action_start_pycharm()
