from flask import request, g
from .messages import MESSAGES


def get_language():
    if 'language' in g:
        return g.language
    
    accept_language = request.headers.get('Accept-Language', 'zh')
    lang = accept_language.split(',')[0].strip()
    
    if lang.startswith('zh'):
        g.language = 'zh'
    elif lang.startswith('en'):
        g.language = 'en'
    else:
        g.language = 'zh'
    
    return g.language


def get_message(key, **kwargs):
    lang = get_language()
    template = MESSAGES.get(lang, {}).get(key, MESSAGES['zh'].get(key, key))
    
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def init_i18n(app):
    app.before_request(lambda: setattr(g, 'language', get_language()))
