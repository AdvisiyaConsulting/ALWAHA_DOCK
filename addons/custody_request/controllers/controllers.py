# -*- coding: utf-8 -*-
# from odoo import http


# class CustodyRequest(http.Controller):
#     @http.route('/custody_request/custody_request', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custody_request/custody_request/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custody_request.listing', {
#             'root': '/custody_request/custody_request',
#             'objects': http.request.env['custody_request.custody_request'].search([]),
#         })

#     @http.route('/custody_request/custody_request/objects/<model("custody_request.custody_request"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custody_request.object', {
#             'object': obj
#         })
