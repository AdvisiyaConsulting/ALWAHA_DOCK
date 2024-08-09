from odoo import fields , models,api,tools,_
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError
# from odoo import amount_to_text


class CustodyRequest(models.Model):
    _name = 'custody.request'
    _description = 'Petty Cash Request'
    _order = 'custody_start_date desc'

    name = fields.Char('Reference',readonly=True)
    description = fields.Char(string='Description')
    user_name = fields.Many2one('school.admin', string='Custodian',required=True)
    check_date = fields.Date('Cheque Date', )
    #num2wo = fields.Char(string="Amount in word", compute='_onchange_amount', store=True)
    electronig = fields.Boolean(string='Cheque', copy=False)
    cheque_number = fields.Char('Cheque number')
    # check_count = fields.Integer(compute='_compute_check')
    # check_id = fields.Many2one('check.followup', string="Check Reference", readonly=True)
    custody_start_date = fields.Date('Start Date', default=lambda self: fields.Date.today(),track_visibility='onchange', required=True)
    custody_end_date = fields.Date('End Date',track_visibility='onchange',required=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount = fields.Monetary('Amount',required=True,track_visibility='onchange')
    sequence = fields.Integer(required=True, default=1,)
    # state = fields.Selection([('draft','Draft'),
    #                           ('post','Posted'),
    #                           ('cancel','Cancel')],default='draft', track_visibility='onchange')
    school_id = fields.Many2one(
        "school.school",
        "School",
        help="Select school",
        tracking=True,
        required=True,
    )
    company_id = fields.Many2one('res.company',string="Company")

    attachment = fields.Binary(string='Attachments / المرفقات')
    notes = fields.Text(string='Notes / ملاحظات ')
    expense_line_ids = fields.One2many(
        "expenses.line",
        "custody_id",
        "Expenses line",
    )
    @api.model
    def default_currency(self):
        return self.env.user.company_id.currency_id

    @api.model
    def default_company(self):
        return self.env.user.company_id

    @api.model
    def create(self, vals):
        code = 'custody.request.code'
        if vals.get('name', 'New') == 'New':
            message = 'PC' + self.env['ir.sequence'].next_by_code(code)
            vals['name'] = message

        if 'school_id' in vals:
                school = self.env['school.school'].browse(vals['school_id'])
                if school:
                    print("if school", self.company_id)
                    self.company_id = school.company_id
            # self.message_post(subject='Create CR', body='This is New CR Number' + str(message))
        return super(CustodyRequest, self).create(vals)

    @api.constrains('custody_start_date', 'custody_end_date')
    def _check_dates(self):
        for record in self:
            if record.custody_start_date and record.custody_end_date and record.custody_start_date > record.custody_end_date:
                raise ValidationError("End date must be greater than the start date.")

    @api.onchange("user_name")
    def onchange_date_day(self):
        """Method to get school_id from custodian"""
        for rec in self:
            print("onchange*****",rec.user_name.school_id)
            if rec.user_name:
                rec.school_id = rec.user_name.school_id
class Expenses(models.Model):
    _name = 'expenses.line'
    _description = 'Expenses'
    name = fields.Char('Reference')
    description = fields.Char(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency',)
    amount = fields.Monetary('Amount', required=True,track_visibility='onchange')
    expenses_type=fields.Selection(
        [   ("utilities", "Utilities (electricity, water, gas)"),
                     ("maintenance","Maintenance and repairs"),
                     ("educ","Educational software and licenses"),
                     ("classroom", "Classroom supplies"),
                     ("office", "Office supplies"),
                     ("communication", "Communication expenses (telephone, internet)"),
                     ("construction", "Construction or renovation costs"),
                     ("furniture", "Furniture and fixtures"),
                     ("equipment", "Equipment purchases"),
                     ("other","Other costs"),
         ],
        "Expense type",
        required=True,
    )
    document = fields.Binary(
        "Attachement", required=True, help="Attached Document"
    )
    school_id = fields.Many2one(
        "school.school",
        "School",
        help="Select school",
        tracking=True,
    )
    company_id = fields.Many2one('res.company',string="Company")

    notes = fields.Text(string='Notes / ملاحظات ')
    custody_id=fields.Many2one('custody.request', string="Petty Cash")

    @api.model
    def default_currency(self):
        return self.env.user.company_id.currency_id

    @api.model
    def _default_company(self):
        return self.env.user.company_id


    def write(self, vals):
        if 'custody_id' in vals:
            custody = self.env['custody.request'].browse(vals['custody_id'])
            current_user = self.env.user
            if custody and current_user != custody.user_name.user_id:
                raise ValidationError("لا يُسمح لك بإضافة  مصروفات لهذه العهد المالية.")
        return super(Expenses, self).write(vals)

    @api.model
    def create(self, vals):
        if 'school_id' in vals:
            school = self.env['school.school'].browse(vals['school_id'])
            if school:
                print("if school", self.company_id)
                self.company_id = school.company_id
        if 'custody_id' in vals:
            custody = self.env['custody.request'].browse(vals['custody_id'])
            current_user = self.env.user
            print("curent user",current_user,custody.user_name.user_id)
            if custody and current_user != custody.user_name.user_id:
                raise ValidationError("لا يُسمح لك بإضافة  مصروفات لهذه العهد المالية.")
        return super(Expenses, self).create(vals)

