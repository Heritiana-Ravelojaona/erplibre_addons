from odoo import _, api, fields, models


class DevopsGenImgStyleArtist(models.Model):
    _name = "devops.gen.img.style_artist"
    _description = "devops_gen_img_style_artist"
    _order = "name asc,id asc"

    name = fields.Char()

    description = fields.Text()
