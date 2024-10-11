from email.policy import default

from odoo import fields, models, api
from odoo.exceptions import UserError, AccessError
from odoo.tools.populate import compute
import logging

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    certification_count = fields.Integer(compute='_compute_certification_count', string="Certifications")
    skill_count = fields.Integer(compute='_compute_skill_count', string="Skills")

    years_of_experience = fields.Integer(compute="_compute_years_of_experience", string="Experience Year")
    certification_ids = fields.Many2many(
        'employee.certification',
        'employee_certification_rel',
        'employee_id',
        'certification_id',
        string="Certifications"
    )
    skill_ids = fields.Many2many(
        'employee.skill',
        'employee_skill_rel',
        'employee_id',
        'skill_id',
        string="Skills"
    )

    @api.depends('certification_ids')
    def _compute_certification_count(self):
        for employee in self:
            employee.certification_count = len(employee.certification_ids)

    @api.depends('skill_ids')
    def _compute_skill_count(self):
        for employee in self:
            employee.skill_count = len(employee.skill_ids)

    def action_view_certifications(self):
        self.ensure_one()
        return {
            'name': 'Certifications',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'employee.certification',
            'domain': [('employee_ids', 'in', self.id)],
            'context': {
                'default_employee_ids': [(6, 0, [self.id])],
                'create': True,
            },
            'target': 'current',
        }

    def action_view_skills(self):
        self.ensure_one()
        return {
            'name': 'Skills',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'employee.skill',
            'domain': [('employee_ids', 'in', self.id)],
            'context': {
                'default_employee_ids': [(6, 0, [self.id])],
                'create': True,
            },
            'target': 'current',
        }

    @api.depends('certification_ids', 'skill_ids')
    def _compute_years_of_experience(self):
        for employee in self:
            years_of_experience = 0
            if employee.certification_ids:
                for cert in employee.certification_ids:
                    if cert.date_received:
                        years_of_experience += (fields.Date.today().year - cert.date_received.year)
            for skill in employee.skill_ids:
                if skill.proficiency_level == 'beginner':
                    years_of_experience += 1
                    # print(self.env.ref('hr_employee.group_employee_experience_manager_advanced').id)
                elif skill.proficiency_level == 'intermediate':
                    years_of_experience += 2
                elif skill.proficiency_level == 'advanced':
                    years_of_experience += 3
                elif skill.proficiency_level == 'expert':
                    years_of_experience += 4
            employee.years_of_experience = years_of_experience

    def action_update_employee_skills(self):
        if not self.skill_ids:
            raise UserError("Please select at least one skill to update.")

        for skill in self.skill_ids:
            if skill not in self.skill_ids:
                self.skill_ids = [(4, skill.id)]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Skills updated successfully for this employee.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_update_employee_certifications(self):
        if not self.certification_ids:
            raise UserError("Please select at least one certification to update.")

        for certification in self.certification_ids:
            if certification not in self.certification_ids:
                self.certification_ids = [(4, certification.id)]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Certifications updated successfully for this employee.',
                'type': 'success',
                'sticky': False,
            }
        }

    # @api.onchange('years_of_experience', 'certification_ids', 'skill_ids')
    # def _check_manage_certification_permissions(self):
    #     for employee in self:
    #         if employee.certification_count >= 3:
    #             employee.manage_certifications = True
    #         else:
    #             employee.manage_certifications = False
    #
    # def _check_manage_skill_permissions(self):
    #     for employee in self:
    #         if employee.skill_count >= 3 and any(skill.name == 'manage' for skill in employee.skill_ids):
    #             employee.manage_skills = True
    #         else:
    #             employee.manage_skills = False

    # def unlink(self):
    #     if self.env.user.has_group('hr.group_hr_user'):
    #         raise AccessError("You do not have permission to delete employees.")
    #     return super(Employee, self).unlink()

    def action_open_skill_wizard(self):
        certifications = self.certification_ids

        if not certifications:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning!',
                    'message': 'This employee has no certifications. Cannot update skills.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        related_skills = certifications.mapped('related_skill_ids')

        if not related_skills:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning!',
                    'message': 'No skills found for the selected certifications. Cannot update skills.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        return {
            'name': 'Update Skills from Certifications',
            'type': 'ir.actions.act_window',
            'res_model': 'skill.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
                'default_certification_ids': certifications.ids,
                'default_skill_ids': related_skills.ids,
            }
        }

    def action_update_skills_automatically(self):
        certifications = self.certification_ids

        if not certifications:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning!',
                    'message': 'This employee has no certifications. Cannot update skills.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        new_skills = certifications.mapped('related_skill_ids')
        if not new_skills:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning!',
                    'message': 'No skills are linked to the certifications. Cannot update skills.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        self.skill_ids = [(6, 0, new_skills.ids)]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Skills updated successfully based on certifications.',
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        if 'certification_ids' in vals:
            self._check_skills_limits(vals.get('certification_ids'))

        return super(Employee, self).write(vals)


    @api.model
    def create(self, vals):
        if 'certification_ids' in vals:
            self._check_skills_limits(vals.get('certification_ids'))

        return super(Employee, self).create(vals)

    def _check_skills_limits(self, certification_ids):
        max_skills = 5

        for employee in self:
            new_certifications = self.env['employee.certification'].browse(certification_ids[0][2])
            new_skills = new_certifications.mapped('related_skill_ids')

            total_skills = len(employee.skill_ids | new_skills)

            if total_skills > max_skills:
                raise UserError(
                    f"Employee {employee.name} cannot have more than {max_skills} skills. Current: {total_skills}")

            employee.skill_ids = [(4, skill.id) for skill in new_skills]
