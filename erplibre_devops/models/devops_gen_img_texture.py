from odoo import _, api, fields, models


class DevopsGenImgTexture(models.Model):
    _name = "devops.gen.img.texture"
    _description = "devops_gen_img_texture"
    _order = "name asc,id asc"

    name = fields.Char()
