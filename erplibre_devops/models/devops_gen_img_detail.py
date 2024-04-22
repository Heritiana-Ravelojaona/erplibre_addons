from odoo import _, api, fields, models


class DevopsGenImgDetail(models.Model):
    _name = "devops.gen.img.detail"
    _description = "devops_gen_img_detail"
    _order = "name asc,id asc"

    name = fields.Char()
