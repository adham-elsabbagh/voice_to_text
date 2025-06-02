# Copyright 2023-2024 GUMBYS
# @author adham mohamed <adham.mohamed@gumbys.be>
# License 'LGPL-3' or later.{

{
    'name': 'Voice To Text',
    'version': '18.0.3.0.0',
    'category': 'Extra Tools',
    'summary': 'Record voice in odoo.',
    'description': 'Record voice and convert the voice into text.',
    'author': 'Adham Mohamed',
    'company': 'gumbys',
    'depends': ['base', 'web', 'crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'voice_to_text/static/src/xml/text_field.xml',
            'voice_to_text/static/src/js/text_field.js',
            'voice_to_text/static/src/css/voice_recognition.css',
        ],
    },
    'external_dependencies': {
        'python': ['openai', 'openai-whisper']
    },
}