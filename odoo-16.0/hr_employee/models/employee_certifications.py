from odoo import fields, models, api
from odoo.api import ondelete
from odoo.exceptions import UserError
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

    def write(self, vals):
        if 'related_skill_ids' in vals:
            self._update_skills_in_database(vals.get('related_skill_ids'))

        return super(EmployeeCertifications, self).write(vals)


    @api.model
    def create(self, vals):
        if 'related_skill_ids' in vals:
            self._update_skills_in_database(vals.get('related_skill_ids'))

        return super(EmployeeCertifications, self).create(vals)


    def _update_skills_in_database(self, skill_ids):
        experience_required = 5
        for cert in self:
            employee = cert.employee_ids

            if employee.years_of_experience >= experience_required:
                if skill_ids and isinstance(skill_ids[0][2], list):
                    for skill_id in skill_ids[0][2]:
                        existing_skill = self.env['employee.skill'].browse(skill_id)
                        if not existing_skill.exists():
                            self.env['employee.skill'].create({'id': skill_id})
            else:
                raise UserError(
                    f"Employee {employee.name} does not have enough experience (minimum {experience_required} years).")