from odoo import fields, models, api
from odoo.api import ondelete
from odoo.fields import Many2one, Boolean

class EmployeeCertifications(models.Model):
    _name = "employee.certification"
    _description = "Employee Certification"

    name = fields.Char(string="Certification Name", required=True)
    description = fields.Char(string="Certification Description")
    date_received = fields.Date(string="Date Received")
    employee_ids = fields.Many2many(
        'hr.employee',
        'employee_certification_rel',
        'certification_id',
        'employee_id',
        string="Employees"
    )
    related_skill_ids = fields.One2many(
        'employee.skill',
        'certification_id',
        string='Related Skills'
    )