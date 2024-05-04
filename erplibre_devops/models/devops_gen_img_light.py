from odoo import _, api, fields, models


class DevopsGenImgLight(models.Model):
    _name = "devops.gen.img.light"
    _description = "devops_gen_img_light"
    _order = "name asc,id asc"

    name = fields.Char()
