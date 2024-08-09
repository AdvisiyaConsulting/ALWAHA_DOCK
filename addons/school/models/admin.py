from odoo import api, fields, models
from odoo.exceptions import ValidationError
from validate_email_address import validate_email
from datetime import datetime, timedelta, date

import logging
_logger = logging.getLogger(__name__)


class SchoolAdmin(models.Model):
    """Defining an Admin information."""

    _name = "school.admin"
    _description = "Admin Information"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    employee_id = fields.Many2one(
        "hr.employee",
        "Employee ID",
        ondelete="cascade",
        delegate=True,
        required=True,
        help="Enter related employee",
    )


    school_id = fields.Many2one(
        "school.school", "Campus", help="Select school"
    )
    category_ids = fields.Many2many(
        "hr.employee.category",
        "admin_category_rel",
        "emp_id",
        "categ_id",
        "Tags",
        help="Select employee category",
    )
    department_id = fields.Many2one(
        "hr.department", "Department", help="Select department"
    )
    is_parent = fields.Boolean("Is Parent", help="Select this if it parent")
    stu_parent_id = fields.Many2one(
        "school.parent", "Related Parent", help="Enter student parent"
    )
    student_id = fields.Many2many(
        "student.student",
        "students_admins_parent_rel",
        "teacher_id",
        "student_id",
        "Children",
        help="Select student",
    )
    phone_numbers = fields.Char("Phone Number", help="Admin PH no")

    role = fields.Selection(
        [
            ("ceo", "CEO"),
            ("manager", "Manager"),
            ("assistant", "Assistant manager"),
            ("admin", "Administrator"),
            ("supervisor", "Supervisor"),
        ],
        "Role",
        required=True,
        help="Role of employee",
    )
    floor_id = fields.Many2one(
        'school.floor',
        'Floor',
        help="Select the floor related to this supervisor",
    )

    @api.onchange('floor_id')
    def onchange_floor_id(self):
        if self.floor_id:
            _logger.info("hiiiiiiiiiiiii %s"%str(self._origin.id))
            self.floor_id.supervisor_id = self._origin.id
    start_shift_morning = fields.Float("From",
                                      help="Enter the start time for the afternoon shift"
                                      )
    end_shift_morning = fields.Float("To",
                                    help="Enter the end time for the afternoon shift")
    start_shift_afternoon = fields.Float("From",
                                      help="Enter the start time for the afternoon shift"
                                      )
    end_shift_afternoon = fields.Float("To",
                                    help="Enter the end time for the afternoon shift")

    active_state = fields.Selection(
        [
            ("working", "Working"),
            ("not_working", "Not Working"),
        ],
        string="Employment Status",
        default="working",
        help="The current employment status of the staff:\n"
             "- Working: Currently employed\n"
             "- Not Working: No longer employed."
    )
    @api.model
    def create(self, vals):
        """Inherited create method to assign value to users for delegation"""
        group_admin = self.env['res.groups'].sudo().search(
            [("id", "=", 3)])
        group_access = self.env['res.groups'].sudo().search(
            [("id", "=", 2)])
        group_employee_admin = self.env['res.groups'].sudo().search(

            [ ("id", "=", 17)])
        group_employee_officer = self.env['res.groups'].sudo().search(
            [ ("id", "=", 16)])
        print('groop*************', group_admin)

        group_employee_officer = self.env['res.groups'].sudo().search(
            [("id", "=", 16)])
        _logger.info('groop************* %s' %str(group_admin))
        _logger.info('groop************* %s' % str(group_access))
        _logger.info('groop************* %s' % str(group_employee_officer))
        _logger.info('groop************* %s' % str(group_employee_admin))
        if 'school_id' in vals:
            school = self.env['school.school'].browse(vals['school_id'])
            if school:
                print("create if school admin", school.company_id)
                vals['company_id'] = school.company_id.id
        # Validate email format before creating a new staff
        if 'work_email' in vals and not validate_email(vals['work_email']):
            raise ValidationError("Invalid email format. Please provide a valid email address.")

        if 'role' in vals and vals['role'] in ['manager', 'ceo', 'assistant']:
            existing_admin = self.search([
                ('role', '=', vals.get('role', False)),
                ('school_id', '=', vals.get('school_id', False)),
                ('active_state', "=", "working")# Include school_id in the check
            ], limit=1)

            if existing_admin:
                raise ValidationError("%s already exists. Only one %s is allowed." %(vals['role'],vals['role']))
        vals['active_state']="working"
        admin_id = super(SchoolAdmin, self).create(vals)

        user_obj = self.env["res.users"]
        user_vals = {
            "name": admin_id.name,
            "login": admin_id.work_email,
            "email": admin_id.work_email,
        }
        ctx_vals = {
            "admin_create": True,
            "school_id": admin_id.school_id.company_id.id,
        }
        user_rec = user_obj.with_context(ctx_vals).create(user_vals)
        print("adminn rollee  create **********",admin_id.role)

        group_ids = [
            self.env.ref("base.group_user").id,
            self.env.ref("base.group_partner_manager").id,
        ]
        if admin_id.role == 'admin':
            group_ids = [
                self.env.ref("school.group_school_administration").id,
                self.env.ref("base.group_user").id,
                #self.env.ref("hr.employee_admin").id,
                self.env.ref("base.group_partner_manager").id,
                group_employee_officer.id,
                group_access.id,

            ]
        if admin_id.role=='supervisor':
            group_ids = [
                self.env.ref("school.group_school_supervisor").id,
                self.env.ref("base.group_user").id,
                self.env.ref("base.group_partner_manager").id,
            ]

        if admin_id.role=='ceo':
            group_ids = [
                self.env.ref("school.group_school_ceo").id,
                self.env.ref("school.group_school_administration").id,
                #self.env.ref("hr.employee_admin").id,
                group_admin.id,
                group_employee_admin.id,
                self.env.ref("base.group_user").id,
                self.env.ref("base.group_partner_manager").id,
            ]
        if admin_id.role == 'manager' or admin_id.role == 'assistant':
            group_ids = [
                self.env.ref("school.group_school_manager").id,
                self.env.ref("school.group_school_administration").id,
                #self.env.ref("hr.employee_admin").id,
                group_access.id,
                group_employee_admin.id,
                self.env.ref("base.group_user").id,
                self.env.ref("base.group_partner_manager").id,
            ]


        user_rec.write({
            "groups_id": [(6, 0, group_ids)]
        })
        print("*******************role group create ********************",group_ids)
        admin_id.employee_id.write({"user_id": user_rec.id})
        #        if vals.get('is_parent'):
        #            self.parent_crt(teacher_id)
        return admin_id

    def write(self, vals):
        """Inherited write method to assign groups based on parent field"""
        # if vals.get('is_parent'):
        #     self.parent_crt(self)
        group_admin = self.env['res.groups'].sudo().search(
            [("id","=",3)])
        group_access = self.env['res.groups'].sudo().search(
            [("id", "=", 2)])
        group_employee_admin=self.env['res.groups'].sudo().search(
            [ ("id", "=", 17)])
        group_employee_officer=self.env['res.groups'].sudo().search(
            [ ("id", "=", 16)])
        print('groop*************', group_admin)
        if 'school_id' in vals:
            school = self.env['school.school'].browse(vals['school_id'])
            if school:
                print("if school admin", school.company_id)
                self.company_id = school.company_id
        if 'role' in vals:
            if vals['role'] in ['manager', 'ceo', 'assistant']:
                existing_admin = self.search([
                    ('role', '=',vals['role']),
                    ('school_id', '=', self.school_id.id),
                    ('active_state', "=", "working")# Include school_id in the check
                ], limit=1)

                if existing_admin:
                    raise ValidationError("%s already exists. Only one %s is allowed." %(vals['role'],vals['role']))

            print("adminn rollee **********", vals)
            role=vals.get('role')
            group_ids = [
                self.env.ref("base.group_user").id,
                self.env.ref("base.group_partner_manager").id,
            ]
            if role == 'admin':
                group_ids = [
                    self.env.ref("school.group_school_administration").id,
                    group_access.id,
                    group_employee_officer.id,
                    self.env.ref("base.group_user").id,
                    self.env.ref("base.group_partner_manager").id,
                ]
            if role == 'supervisor':
                group_ids = [
                    self.env.ref("school.group_school_supervisor").id,
                    self.env.ref("base.group_user").id,
                    self.env.ref("base.group_partner_manager").id,
                ]
            if role == 'ceo':
                group_ids = [
                    self.env.ref("school.group_school_ceo").id,
                    self.env.ref("school.group_school_administration").id,
                    #self.env.ref("hr.employee_admin").id,
                    group_admin.id,
                    group_employee_admin.id,
                    self.env.ref("base.group_user").id,
                    self.env.ref("base.group_partner_manager").id,

                ]
            if role == 'manager' or role == 'assistant':
                group_ids = [
                    self.env.ref("school.group_school_manager").id,
                    self.env.ref("school.group_school_administration").id,
                    #self.env.ref("hr.employee_admin").id,
                    group_access.id,
                    group_employee_admin.id,
                    self.env.ref("base.group_user").id,
                    self.env.ref("base.group_partner_manager").id,
                ]


            user_rec = self.employee_id.user_id
            user_rec.write({
                "groups_id": [(6, 0, group_ids)]
            })
            print("*******************role group write ********************", group_ids)

            self.employee_id.write({"user_id": user_rec.id})
        if vals.get("student_id"):
            self.stu_parent_id.write({"student_id": vals.get("student_id")})
        if not vals.get("is_parent"):
            user_rec = self.employee_id.user_id
            parent_grp_id = self.env.ref("school.group_school_parent")
            if parent_grp_id in user_rec.groups_id:
                user_rec.write({"groups_id": [(3, parent_grp_id.id)]})

        #        if vals.get('is_parent'):
        #            self.parent_crt(teacher_id)

        if vals.get('active_state') == "not_working":
            self.employee_id.user_id.write({'active': False})

        return super(SchoolAdmin, self).write(vals)


    def button_leave(self):
        # Change the state to "not_working"
        self.write({'active_state': 'not_working'})