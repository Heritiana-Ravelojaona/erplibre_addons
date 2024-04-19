# Copyright 2023 TechnoLibre inc. - Mathieu Benoit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "ERPLibre DevOps",
    "category": "Tools",
    "summary": "ERPLibre DevOps manage workspace to create new ERPLibre",
    "version": "12.0.1.0.0",
    "author": "Mathieu Benoit",
    "license": "AGPL-3",
    "website": "https://erplibre.ca",
    "application": True,
    "depends": [
        "code_generator",
        "code_generator_cron",
        "code_generator_db_servers",
        "code_generator_geoengine",
        "code_generator_hook",
        "code_generator_portal",
        "code_generator_theme_website",
        "code_generator_website_leaflet",
        "code_generator_website_snippet",
        "mail",
        "multi_step_wizard",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/devops_plan_action_wizard.xml",
        "data/mail_message_subtype.xml",
        "data/erplibre_config_path_home.xml",
        "data/devops_cg_module.xml",
        "data/devops_cg_new_project_stage.xml",
        "data/devops_cg_test_case.xml",
        "data/devops_test_plan.xml",
        "data/devops_test_case.xml",
        "data/devops_docker_compose_template.xml",
        "data/devops_ide_breakpoint.xml",
        "data/devops_system.xml",
        "data/devops_workspace.xml",
        "data/erplibre_mode_env.xml",
        "data/erplibre_mode_exec.xml",
        "data/erplibre_mode_source.xml",
        "data/erplibre_mode_version_base.xml",
        "data/erplibre_mode_version_erplibre.xml",
        "data/erplibre_mode.xml",
        "data/ir_cron.xml",
        "views/devops_cg.xml",
        "views/devops_cg_field.xml",
        "views/devops_cg_model.xml",
        "views/devops_cg_module.xml",
        "views/devops_cg_new_project.xml",
        "views/devops_cg_new_project_stage.xml",
        "views/devops_cg_test_case.xml",
        "views/devops_code_todo.xml",
        "views/devops_db_image.xml",
        "views/devops_deploy_vm.xml",
        "views/devops_deploy_vm_exec.xml",
        "views/devops_deploy_vm_exec_stage.xml",
        "views/devops_deploy_vm_snapshot.xml",
        "views/devops_docker_container.xml",
        "views/devops_docker_volume.xml",
        "views/devops_docker_compose.xml",
        "views/devops_docker_compose_template.xml",
        "views/devops_docker_image.xml",
        "views/devops_docker_network.xml",
        "views/devops_exec.xml",
        "views/devops_exec_bundle.xml",
        "views/devops_exec_error.xml",
        "views/devops_ide_breakpoint.xml",
        "views/devops_ide_pycharm.xml",
        "views/devops_log_makefile_target.xml",
        "views/devops_operate_localai.xml",
        "views/devops_plan_cg.xml",
        "views/devops_system.xml",
        "views/res_config_settings.xml",
        "views/devops_test_case.xml",
        "views/devops_test_case_exec.xml",
        "views/devops_test_plan.xml",
        "views/devops_test_plan_exec.xml",
        "views/devops_test_result.xml",
        "views/devops_workspace.xml",
        "views/devops_workspace_docker.xml",
        "views/devops_workspace_terminal.xml",
        "views/erplibre_config_path_home.xml",
        "views/erplibre_mode.xml",
        "views/erplibre_mode_env.xml",
        "views/erplibre_mode_exec.xml",
        "views/erplibre_mode_source.xml",
        "views/erplibre_mode_version_base.xml",
        "views/erplibre_mode_version_erplibre.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
