# See LICENSE file for full copyright and licensing details.

{
    "name": "Fees Management for Education ERP",
    "version": "15.0.1.0.0",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    "category": "School Management",
    "license": "AGPL-3",
    "complexity": "easy",
    "summary": "A Module For Fees Management In School",
    "depends": ["school"],
    "images": ["static/description/SchoolFees.png"],
    "data": [
        "security/ir.model.access.csv",
        "security/security_fees.xml",
        "data/school_fees_sequence.xml",
        "data/mail_template.xml",
        "data/data.xml",
        "views/school_fees_view.xml",
        "report/student_payslip.xml",
        "report/student_fees_register.xml",
        "report/report_view.xml",
    ],
    "assets": {
                "web.assets_backend": ["/school_fees/static/src/school_fees.scss"]
            },
    "demo": ["demo/school_fees_demo.xml"],
    "installable": True,
    "application": True,
}
