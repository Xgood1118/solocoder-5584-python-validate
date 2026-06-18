from flask import Flask
from .config import Config
from .api import api_bp
from .i18n import init_i18n
from .rules import init_rules_storage
from .logs import init_logs_storage


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_i18n(app)
    init_rules_storage(app)
    init_logs_storage(app)

    app.register_blueprint(api_bp, url_prefix='/api/v1')

    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'service': 'validation-framework'}

    return app
