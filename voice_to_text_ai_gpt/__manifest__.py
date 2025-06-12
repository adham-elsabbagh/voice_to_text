{
    'name': 'Voice To Text GPT Connector',
    'version': '18.0.3.0.0',
    'category': 'Extra Tools',
    'summary': 'Convert voice recordings to text using AI-powered transcription in Odoo CRM.',
    'license': 'LGPL-3',
    'description': '''
        Voice To Text GPT Connector

        Transform your voice into text seamlessly within Odoo using advanced AI technology.

        Key Features:
        • Real-time voice recording with visual feedback
        • Automatic speech-to-text conversion using OpenAI Whisper
        • Multi-language support (EN, NL, FR, DE, ES)
        • AI-powered note enhancement with ChatGPT integration
        • Seamless CRM Lead and Activity integration
        • Custom activity tracking and statistics
        • Responsive web interface with modern UI
        • Configurable prompts for AI processing

        Perfect for:
        • Quick note-taking during customer calls
        • Voice memos for follow-up activities
        • Hands-free data entry in CRM
        • Meeting notes and action items
        • Mobile-friendly voice input
        • Accessibility for users with typing difficulties

        Requirements:
        • OpenAI API key for GPT and Whisper services
        • Modern browser with microphone access
        • Internet connection for AI processing
    ''',
    'author': 'Adham',
    'maintainer': 'Adham',
    'depends': ['base', 'web', 'crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'voice_to_text_ai_gpt/static/src/xml/text_field.xml',
            'voice_to_text_ai_gpt/static/src/js/text_field.js',
            'voice_to_text_ai_gpt/static/src/css/voice_recognition.css',
        ],
    },
    'external_dependencies': {
        'python': ['openai', 'openai-whisper']
    },
    'icon': 'voice_to_text_ai_gpt/static/description/icon.png',
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 9.99,
    'currency': 'EUR',
    'support': 'adham.mohamed@example.com',
    'live_test_url': 'https://demo.odoo.com',
}