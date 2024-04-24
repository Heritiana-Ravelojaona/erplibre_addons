from odoo import _, api, fields, models


class DevopsInstanceType(models.Model):
    _name = "devops.instance.type"
    _description = "devops_instance_type"

    name = fields.Char()
