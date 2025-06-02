# Copyright 2023-2024 GUMBYS
# @author adham mohamed <adham.mohamed@gumbys.be>
# License 'LGPL-3' or later.

from datetime import datetime
from odoo import api, fields, models, _
import openai
from collections import defaultdict
import logging
_logger = logging.getLogger(__name__)

class MailActivity(models.Model):
    _inherit = "mail.activity"

    voice_to_text = fields.Text(string="Voice to Text")
    voice_to_text_id = fields.Many2one(
        comodel_name="crm.voice.text",
        string="Voice to Text"
    )
    is_done = fields.Boolean(string="Is Done", default=False, readonly=True)

    def action_log_voice_note(self):
        """ Action to log the voice-to-text result using OpenAI ChatGPT """
        if not self.voice_to_text_id:
            return

        # Prepare the prompt, including the voice_to_text field
        title = self.voice_to_text_id.title
        description = self.voice_to_text_id.description  # Already includes instructions
        voice_to_text = self.voice_to_text or ""
        prompt = f"Title: {title}\nDescription: {description}\nText: {voice_to_text}"

        # Retrieve the OpenAI API key from system parameters
        api_key = self.env['ir.config_parameter'].sudo().get_param('openai.api_key')
        if not api_key:
            _logger.error("OpenAI API key not found in system parameters.")
            return

        # Set the API key for the OpenAI library
        openai.api_key = api_key

        try:
            # Call the OpenAI ChatGPT API with the latest model (gpt-4)
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Use the newest and most accurate model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100  # Adjust as needed
            )

            # Extract the generated text from the response
            chatgpt_response = response.choices[0].message["content"].strip()
            _logger.info(f"OpenAI ChatGPT Response: {chatgpt_response}")

            # Get the current date and time
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update the description field with the generated response, including date and time
            self.note = (self.note or "") + f"\n[{current_datetime}][{self.env.user.name}] {chatgpt_response}"

            # Log the result in the chatter
        except Exception as e:
            _logger.error(f"Error during OpenAI ChatGPT processing: {e}")


    def _action_done(self, feedback=False, attachment_ids=None):
        """ Private implementation of marking activity as done: posting a message, deleting activity
            (since done), and eventually create the automatical next activity (depending on config).
            :param feedback: optional feedback from user when marking activity as done
            :param attachment_ids: list of ir.attachment ids to attach to the posted mail.message
            :returns (messages, activities) where
                - messages is a recordset of posted mail.message
                - activities is a recordset of mail.activity of forced automically created activities
        """
        # marking as 'done'
        messages = self.env['mail.message']
        next_activities_values = []


        # Search for all attachments linked to the activities we are about to unlink. This way, we
        # can link them to the message posted and prevent their deletion.
        attachments = self.env['ir.attachment'].search_read([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['id', 'res_id'])

        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment['res_id']
            activity_attachments[activity_id].append(attachment['id'])

        for model, activity_data in self._classify_by_model().items():
            # Allow user without access to the record to "mark as done" activities assigned to them. At the end of the
            # method, the activity is unlinked or archived which ensure the user has enough right on the activities.
            records_sudo = self.env[model].sudo().browse(activity_data['record_ids'])
            for record_sudo, activity in zip(records_sudo, activity_data['activities']):
                # extract value to generate next activities
                if activity.chaining_type == 'trigger':
                    vals = activity.with_context(activity_previous_deadline=activity.date_deadline)._prepare_next_activity_values()
                    next_activities_values.append(vals)

                # post message on activity, before deleting it
                activity_message = record_sudo.message_post_with_source(
                    'mail.message_activity_done',
                    attachment_ids=attachment_ids,
                    author_id=self.env.user.partner_id.id,
                    render_values={
                        'activity': activity,
                        'feedback': feedback,
                        'display_assignee': activity.user_id != self.env.user
                    },
                    mail_activity_type_id=activity.activity_type_id.id,
                    subtype_xmlid='mail.mt_activities',
                )
                if activity.activity_type_id.keep_done:
                    attachment_ids = (attachment_ids or []) + activity_attachments.get(activity.id, [])
                    if attachment_ids:
                        activity.attachment_ids = attachment_ids

                # Moving the attachments in the message
                # TODO: Fix void res_id on attachment when you create an activity with an image
                # directly, see route /web_editor/attachment/add
                if activity_attachments[activity.id]:
                    message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity.id])
                    if message_attachments:
                        message_attachments.write({
                            'res_id': activity_message.id,
                            'res_model': activity_message._name,
                        })
                        activity_message.attachment_ids = message_attachments
                messages += activity_message

        next_activities = self.env['mail.activity']
        if next_activities_values:
            next_activities = self.env['mail.activity'].create(next_activities_values)
        self.is_done = True

        return messages, next_activities


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    category = fields.Selection(selection_add=[('meeting', 'Meeting'),
                                               ('teams_call', 'Teams Call'),
                                               ('physical_visit', 'Physical Visit'),
                                               ('email', 'Email'),
                                               ('todo', 'To-Do')
                                               ])


class CrmLead(models.Model):
    _inherit = "crm.lead"

    voice_to_text = fields.Text(string="Voice to Text")
    voice_to_text_id = fields.Many2one(
        comodel_name="crm.voice.text",
        string="Voice to Text"
    )
    activity_ids = fields.One2many(
        comodel_name='mail.activity',
        inverse_name='res_id',
        domain=lambda self: [('res_model', '=', self._name)],
        string='Activities'
    )

    activity_count_email = fields.Integer(
        string='Email Activities', compute='_compute_activity_counts'
    )
    activity_count_call = fields.Integer(
        string='Call Activities', compute='_compute_activity_counts'
    )
    activity_count_meeting = fields.Integer(
        string='Meeting Activities', compute='_compute_activity_counts'
    )
    activity_count_todo = fields.Integer(
        string='ToDo Activities', compute='_compute_activity_counts'
    )

    done_calls_count = fields.Integer(compute='_compute_done_activities_count', string='Done Calls')
    done_teams_calls_count = fields.Integer(compute='_compute_done_activities_count', string='Done Teams Calls')
    done_physical_visits_count = fields.Integer(compute='_compute_done_activities_count', string='Done Physical Visits')
    done_emails_count = fields.Integer(compute='_compute_done_activities_count', string='Done Emails')

    @api.depends('activity_ids')
    def _compute_done_activities_count(self):
        for record in self:
            # Filter activities where 'is_done' is True
            activities = record.activity_ids.filtered(lambda a: a.is_done and a.activity_type_id.category)
            record.done_calls_count = len(activities.filtered(lambda a: a.activity_type_id.category == 'phonecall'))
            record.done_teams_calls_count = len(activities.filtered(lambda a: a.activity_type_id.category == 'teams_call'))
            record.done_physical_visits_count = len(activities.filtered(lambda a: a.activity_type_id.category == 'physical_visit'))
            record.done_emails_count = len(activities.filtered(lambda a: a.activity_type_id.category == 'email'))

    @api.depends('activity_ids')
    def _compute_activity_counts(self):
        for lead in self:
            activities = lead.activity_ids
            lead.activity_count_email = len(
                activities.filtered(lambda a: a.activity_type_id.category == 'email'))
            lead.activity_count_call = len(
                activities.filtered(lambda a: a.activity_type_id.category == 'phonecall'))
            lead.activity_count_meeting = len(
                activities.filtered(lambda a: a.activity_type_id.category == 'meeting'))
            lead.activity_count_todo = len(
                activities.filtered(lambda a: a.activity_type_id.category == 'todo'))
    def action_log_voice_note(self):
        """ Action to log the voice-to-text result using OpenAI ChatGPT """
        if not self.voice_to_text_id:
            self.message_post(body="No voice-to-text record selected.")
            return

        # Prepare the prompt, including the voice_to_text field
        title = self.voice_to_text_id.title
        description = self.voice_to_text_id.description  # Already includes instructions
        voice_to_text = self.voice_to_text or ""
        prompt = f"Title: {title}\nDescription: {description}\nText: {voice_to_text}"

        # Retrieve the OpenAI API key from system parameters
        api_key = self.env['ir.config_parameter'].sudo().get_param('openai.api_key')
        if not api_key:
            _logger.error("OpenAI API key not found in system parameters.")
            self.message_post(body="OpenAI API key is missing. Please configure it in system parameters.")
            return

        # Set the API key for the OpenAI library
        openai.api_key = api_key

        try:
            # Call the OpenAI ChatGPT API with the latest model (gpt-4)
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Use the newest and most accurate model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100  # Adjust as needed
            )

            # Extract the generated text from the response
            chatgpt_response = response.choices[0].message["content"].strip()
            _logger.info(f"OpenAI ChatGPT Response: {chatgpt_response}")

            # Get the current date and time
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update the description field with the generated response, including date and time
            self.description = (self.description or "") + f"\n[{current_datetime}][{self.env.user.name}] {chatgpt_response}"

            # Log the result in the chatter
            self.message_post(body="Voice-to-text note added to description.")
        except Exception as e:
            _logger.error(f"Error during OpenAI ChatGPT processing: {e}")
            self.message_post(body="Error during OpenAI ChatGPT processing.")


class CrmVoiceText(models.Model):
    _name = "crm.voice.text"
    _description = "CRM Voice to Text Record"
    _rec_name = 'title'

    title = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")