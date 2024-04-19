from odoo import _, api, fields, models


class DevopsDockerComposeTemplate(models.Model):
    _name = "devops.docker.compose.template"
    _description = "devops_docker_compose_template"

    name = fields.Char()

    docker_compose_model = fields.Selection(
        selection=[
            ("erplibre", "ERPLibre"),
            ("rocketchat", "RocketChat"),
            ("nextcloud", "Nextcloud"),
            ("localai", "LocalAI"),
        ],
        default="erplibre",
        required=True,
        help="Instance list, from project list.",
    )

    is_support_gpu = fields.Boolean(
        default=False, help="If true, show gpu_mode", readonly=True
    )

    gpu_mode = fields.Selection(
        selection=[
            ("no_gpu", "No GPU"),
            ("gpu_cuda_11", "GPU Cuda 11"),
            ("gpu_cuda_12", "GPU Cuda 12"),
        ],
        default="no_gpu",
        required=True,
        help="Choose a GPU mode.",
    )

    port_1 = fields.Integer(
        string="Port 1", help="Principal port", default=8080
    )

    port_2 = fields.Integer(string="Port 2", help="Second port")

    port_3 = fields.Integer(string="Port 3", help="Third port")

    is_generic_template = fields.Boolean()

    yaml = fields.Text(compute="_compute_yaml")

    @api.depends("docker_compose_model", "gpu_mode")
    @api.multi
    def _compute_yaml(self):
        for rec in self:
            if rec.docker_compose_model == "erplibre":
                rec.yaml = "fds"
            elif rec.docker_compose_model == "rocketchat":
                rec.yaml = "fds"
            elif rec.docker_compose_model == "nextcloud":
                rec.yaml = "fds"
            elif rec.docker_compose_model == "localai":
                if rec.gpu_mode == "gpu_cuda_11":
                    image = "localai/localai:latest-aio-gpu-nvidia-cuda-11"
                elif rec.gpu_mode == "gpu_cuda_12":
                    image = "localai/localai:latest-aio-gpu-nvidia-cuda-12"
                else:
                    image = "localai/localai:latest-aio-cpu"

                deploy = ""
                if rec.gpu_mode in ["gpu_cuda_11", "gpu_cuda_12"]:
                    deploy = """
    deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]""".strip()

                rec.yaml = f"""
version: "3.9"
services:
  api:
    image: {image}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/readyz"]
      interval: 1m
      timeout: 20m
      retries: 5
    ports:
      - {rec.port_1}:8080
    environment:
      - DEBUG=true
    volumes:
      - ./models:/build/models:cached
    {deploy}
""".strip()
            else:
                rec.yaml = False
