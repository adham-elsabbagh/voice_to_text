# CRM Voice to Text & Analytics Enhancements

## Overview

This Odoo module enhances the `crm.lead` functionality by:
- Adding voice-to-text transcription and logging using a microphone interface.
- Integrating OpenAI GPT-4 for processing and summarizing transcriptions.
- Tracking various activity types (calls, meetings, emails, physical visits, Teams calls).
- Extending the graph view with custom KPIs such as completed calls and meetings.

## Features

### 🎙️ Voice to Text
- Users can record voice notes directly into a text field.
- Transcription is handled via a custom `/voice_to_text/recognize` RPC endpoint.
- Results are optionally processed by OpenAI's ChatGPT for summarization.

### 📊 Activity KPIs
The module adds computed fields for activity analytics:
- `done_calls_count`
- `done_teams_calls_count`
- `done_physical_visits_count`
- `done_emails_count`

These are also displayed in the graph view for easy tracking.

## Installation

1. Place the module in your custom addons directory.
2. Ensure the required dependencies are installed:
   - Python packages: `openai`
3. Add your OpenAI API key in **Settings → Technical → Parameters → System Parameters**:
   - `Key`: `openai.api_key`
   - `Value`: `<your_openai_api_key>`

4. Update your Odoo manifest and restart the server:
   ```bash
   ./odoo-bin -u your_module_name -d your_database
