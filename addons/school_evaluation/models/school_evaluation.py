# See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import datetime, timedelta, date

import logging
_logger = logging.getLogger(__name__)

class SchoolEvaluation(models.Model):
    """Defining School Evaluation."""

    _name = "school.evaluation"
    _description = "School Evaluation details"
    _rec_name = "type"



    def action_check_evaluation(self):
        # Get the current date
        current_date = datetime.now()
        # Calculate the date one month ago
        one_month_ago = current_date - timedelta(days=30)  # Assuming 30 days = 1 month
        teachers=self.env['school.teacher'].sudo().search([])
        for teacher in teachers:
                standard_teachers = []
                for standard_teacher in teacher.standard_id:
                    standard_teachers.append(standard_teacher.id)
                students=self.env['student.student'].sudo().search([("standard_id.id","in",standard_teachers)])
                students_not_evaluation=""
                for student in students:

                    evaluations = self.env['school.evaluation'].sudo().search([("type", "=", "student"),
                                                                               ("teacher_id.id", "=", teacher.id),
                                                                               ("student_id.id","=",student.id)])
                    _logger.info("school.evaluation %s" % str(evaluations))
                    if not evaluations:
                            students_not_evaluation= students_not_evaluation + str(student.name) + ", "
                            _logger.info("this student havent evaluation %s"%str(student))
                            _logger.info("for teacher %s"%str(teacher))

                if students_not_evaluation != "":
                    base_url = str(self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
                    url=base_url+"/web#id="+str(teacher.id)+"2&cids=5&menu_id=380&action=593&model=school.teacher&view_type=form"
                    _logger.info("studenttt  %s" %str(url))
                    # student_name=str(rec.name+' ' + rec.middle + ' ' + rec.last)
                    users = []
                    activity_type_id = self.env.ref('mail.mail_activity_data_todo')
                    activity_obj = self.env['mail.activity']
                    note= "We kindly request that you review the status of this admission register: %s." % str(
                         students_not_evaluation)
                    # #student_name = str(rec.student_payslip_id.student_id.name)+" "+str(rec.student_payslip_id.student_id.middle)+" "+str(rec.student_payslip_id.student_id.last)
                    # exist_activity=activity_obj.sudo().search([('res_model_id',"=",self.env['ir.model'].sudo()._get('student.student').id),
                    #                                             ('note',"like",note)])
                    # _logger.info("exist activity %s" %str(exist_activity))
                    # if exist_activity:
                    users += self.env.ref('school.group_school_administration').sudo().users
                    for user in users:

                            body = (
                                    """
                                <div dir="rtl" >
                                    <p>عزيزي """
                                    + str(user.display_name)
                                    + """,
                                                        <br/><br/>
                                                 المعلم 
                                                 """ +  """
                                                           <a href=""" + str(url) + """ style="color: red;" >""" + str(
                                teacher.name) + """</a><br/> <br/>"""  +
                                    """
                                                  لم يقم بإعداد تقييم الطلاب : """

                                    + """ <br> """ + str(students_not_evaluation)
                                                         + """
                                                        <br></br>
                                                    شكرًا.
                                                    </div>
                                                    """
                            )

                            email_values={
                                    "email_from": self.env.user.email or "",
                                    "email_to": user.email,
                                    "subject": "Missing Evaluation",
                                    "body_html": body,
                                }
                            # send email
                            _logger.info("user id ********** %s" %str(user.id))
                            #self.send_email_with_template(user, "Missing Evaluation", email_values)
                            self.send_email(user.email, "Missing Evaluation", body)

    def send_email_with_template(self, user, template_name, email_values):

        template = (self.env["mail.template"].with_context(lang=user.lang)
                    .sudo()
                    .search([("name", "ilike", template_name)], limit=1)
                    )
        _logger.info("before if templatee**************** %s" % str(template))

        if template:

            template.send_mail(user.id, force_send=True, email_values=email_values)
            return True
        else:
            return False

    def send_email(self, recipient_email, subject, body):
            IrMailServer = self.env['ir.mail_server']
            mail_server = IrMailServer.search([], limit=1)
            if mail_server:
                mail_values = {
                    'subject': subject,
                    'email_to': recipient_email,
                    'email_from': self.env.user.company_id.email,
                    'body_html': body,
                    'body': body,
                }
                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.send()
                return True
            else:
                return False
    @api.depends("eval_line_ids")
    def _compute_total_points(self):
        """Method to compute evaluation points"""
        for rec in self:
            if rec.eval_line_ids:
                rec.total = sum(
                    line.point_id.rating
                    for line in rec.eval_line_ids
                    if line.point_id.rating
                )

    student_id = fields.Many2one(
        "student.student", "Student Name", help="Select Student"
    )

    @api.constrains("student_id")
    def check_date(self):
        """Method to check constraint of student evaluation"""
        for line in self:

            if line.student_id:
                student_id = line.student_id
                standard = self.env['school.standard'].sudo().search([('id',"=",student_id.standard_id.id)])
                teacher_find=False
                if standard:
                    print("student*********",line.teacher_id)
                    for teacher in standard.teacher_ids:
                        if line.teacher_id == teacher:
                            teacher_find = True

                    if not teacher_find:
                        raise ValidationError(
                            _(
                                "You can't evaluate a student who is not in your class !"
                            )
                        )

    teacher_id = fields.Many2one(
        "school.teacher", "Teacher", help="Select teacher"
    )
    type = fields.Selection(
        [("student", "Student"), ("faculty", "Faculty")],
        "User Type",
        required=True,
        help="Type of evaluation",
    )
    date = fields.Date(
        "Evaluation Date",
        required=True,
        help="Evaluation Date",
        default=fields.Date.context_today,
    )
    eval_line_ids = fields.One2many(
        "school.evaluation.line",
        "eval_id",
        "Questionnaire",
        help="Enter evaluation details",
    )
    total = fields.Float(
        "Total Points",
        compute="_compute_total_points",
        help="Total Points Obtained",
        store=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("start", "In Progress"),
            ("finished", "Finish"),
            ("cancelled", "Cancel"),
        ],
        "State",
        readonly=True,
        default="draft",
        help="State of evaluation line",
    )
    username = fields.Many2one(
        "res.users",
        "User",
        readonly=True,
        default=lambda self: self.env.user,
        help="Related user",
    )
    active = fields.Boolean(
        "Active", default=True, help="Activate/Deactivate record"
    )

    @api.model
    def default_get(self, fields):
        """Override method to get default value of teacher"""
        res = super(SchoolEvaluation, self).default_get(fields)
        if res.get("type") == "student":
            hr_emp_rec = self.env["school.teacher"].search(
                [("user_id", "=", self._uid)]
            )
            res.update({"teacher_id": hr_emp_rec.id})
        return res

    @api.model
    def fields_view_get(
        self, view_id=None, viewtype="form", toolbar=False, submenu=False
    ):
        """Inherited this method to hide the create,edit button from list"""
        res = super(SchoolEvaluation, self).fields_view_get(
            view_id=view_id,
            view_type=viewtype,
            toolbar=toolbar,
            submenu=submenu,
        )
        teacher_group = self.env.user.has_group("school.group_school_teacher")
        doc = etree.XML(res["arch"])
        if teacher_group:
            if viewtype == "tree":
                nodes = doc.xpath("//tree[@name='teacher_evaluation']")
                for node in nodes:
                    node.set("create", "false")
                    node.set("edit", "false")
                res["arch"] = etree.tostring(doc)
            if viewtype == "form":
                nodes = doc.xpath("//form[@name='teacher_evaluation']")
                for node in nodes:
                    node.set("create", "false")
                    node.set("edit", "false")
                res["arch"] = etree.tostring(doc)
        return res

    def get_record(self):
        """Method to get the evaluation questions"""
        eval_temp_obj = self.env["school.evaluation.template"]
        for rec in self:
            eval_list = []
            for eval_temp in eval_temp_obj.search([("type", "=", rec.type)]):
                eval_list.append((0, 0, {"stu_eval_id": eval_temp.id}))
            if rec.eval_line_ids:
                rec.write({"eval_line_ids": [(5, 0, 0)]})
            rec.write({"eval_line_ids": eval_list})
        return True

    def set_start(self):
        """change state to start"""
        for rec in self:
            if not rec.eval_line_ids:
                raise ValidationError(
                    _(
                        """Please Get the Questions First!
To Get the Questions please click on "Get Questions" Button!"""
                    )
                )
        self.state = "start"

    def set_finish(self):
        """Change state to finished"""
        for rec in self:
            if [
                line.id
                for line in rec.eval_line_ids
                if (not line.point_id or not line.rating)
            ]:
                raise ValidationError(
                    _(
                        """You can't mark the evaluation as Finished untill
the Rating/Remarks are not added for all the Questions!"""
                    )
                )
        self.state = "finished"

    def set_cancel(self):
        """Change state to cancelled"""
        self.state = "cancelled"

    def set_draft(self):
        """Changes state to draft"""
        self.state = "draft"

    def unlink(self):
        """Inherited unlink method to check state at record deletion"""
        for rec in self:
            if rec.state in ["start", "finished"]:
                raise ValidationError(
                    _("""You can delete record in unconfirmed state only!""")
                )
        return super(SchoolEvaluation, self).unlink()


class StudentEvaluationLine(models.Model):
    """Defining School Evaluation Line."""

    _name = "school.evaluation.line"
    _description = "School Evaluation Line Details"

    eval_id = fields.Many2one(
        "school.evaluation", "Evaluation id", help="Select school evaluation"
    )
    stu_eval_id = fields.Many2one(
        "school.evaluation.template",
        "Question",
        help="Select evaluation question",
    )
    point_id = fields.Many2one(
        "rating.rating",
        "Rating",
        domain="[('template_id', '=', stu_eval_id)]",
        help="Evaluation point",
    )
    rating = fields.Char("Remarks", help="Enter remark")

    # attachment = fields.Binary(
    #     "Attachment", help="Evaluation attachment"
    # )

    _sql_constraints = [
        (
            "number_uniq",
            "unique(eval_id, stu_eval_id)",
            "Questions already exist!",
        )
    ]

    @api.onchange("point_id")
    def onchange_point(self):
        """Method to get rating point based on rating"""
        self.rating = False
        if self.point_id:
            self.rating = self.point_id.feedback


class SchoolEvaluationTemplate(models.Model):
    """Defining School Evaluation Template."""

    _name = "school.evaluation.template"
    _description = "School Evaluation Template Details"
    _rec_name = "desc"

    desc = fields.Char("Description", required=True, help="Description")
    type = fields.Selection(
        [("faculty", "Faculty"), ("student", "Student")],
        "User Type",
        required=True,
        default="faculty",
        help="Type of Evaluation",
    )
    rating_line = fields.One2many(
        "rating.rating", "template_id", "Rating", help="Rating"
    )


class RatingRating(models.Model):
    """Defining Rating."""

    _inherit = "rating.rating"
    _description = "Rating"

    template_id = fields.Many2one(
        "school.evaluation.template", "Stud", help="Ratings"
    )

    @api.model
    def create(self, vals):
        """Set Document model name for rating."""
        res_model_rec = self.env["ir.model"].search(
            [("model", "=", "school.evaluation.template")]
        )
        vals.update({"res_model_id": res_model_rec.id})
        res = super(RatingRating, self).create(vals)
        return res

    @api.depends("res_model", "res_id")
    def _compute_res_name(self):
        """Override this method to set the alternate rec_name as rating"""
        # cannot change the rec_name of session since
        #                    it is use to create the bus channel
        # so, need to override this method to set the same
        #                           alternative rec_name as rating
        for rate in self:
            if rate.res_model == "school.evaluation.template":
                rate.res_name = rate.rating
            else:
                super(RatingRating, self)._compute_res_name()


class StudentExtend(models.Model):
    _inherit = "student.student"

    def set_alumni(self):
        """Override method to set active false student evaluation when
        student is set to alumni"""
        student_eval_obj = self.env["school.evaluation"]
        for rec in self:
            student_eval_rec = student_eval_obj.search(
                [("type", "=", "student"), ("student_id", "=", rec.id)]
            )
            if student_eval_rec:
                student_eval_rec.active = False
        return super(StudentExtend, self).set_alumni()
