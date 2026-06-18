from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import validate_routes, rules_routes, logs_routes
