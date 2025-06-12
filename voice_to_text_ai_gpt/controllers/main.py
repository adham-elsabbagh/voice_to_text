from odoo.http import Controller, route, request
import base64
import whisper
import tempfile
import os
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class VoiceToTextController(Controller):
    @route('/voice_to_text/recognize', type='json', auth='user', csrf=False)
    def recognize_speech(self, audio_data):
        try:
            audio_bytes = base64.b64decode(audio_data)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name

            user_lang = request.env.user.lang or 'en_US'
            language_mapping = {
                'en_US': 'en', 'nl_NL': 'nl', 'fr_FR': 'fr', 'de_DE': 'de',
                'es_ES': 'es', 'nl_BE': 'nl',
            }
            whisper_lang = language_mapping.get(user_lang, 'en')

            _logger.info(f"User language: {user_lang}, Whisper language: {whisper_lang}")

            model = whisper.load_model("base")
            result = model.transcribe(temp_file_path, language=whisper_lang)
            transcription = result.get("text", "").strip()

            _logger.info(f"Transcription: {transcription}")
            os.unlink(temp_file_path)
            return {"status": "success", "text": transcription}
        except Exception as e:
            _logger.error(f"Error during Whisper transcription: {e}")
            return {"status": "error", "message": str(e)}

    @route('/voice_to_text/update_field', type='json', auth='user', csrf=False)
    def update_field(self, field, model, script, record_id):
        _logger.info(f"Model: {model}, Field: {field}, Record ID: {record_id}, Script: {script}")
        if not model or not field or not record_id:
            raise UserError("Invalid parameters provided.")
        record = request.env[model].browse(int(record_id))
        if not record.exists():
            raise UserError("The specified record does not exist.")
        if script:
            existing_value = record.sudo()[field] or ""
            updated_value = f"{existing_value}\n{script}".strip()
            record.sudo().write({field: updated_value})
            return {"status": "success", "message": "Field updated successfully."}
        else:
            raise UserError("No text provided to write.")
