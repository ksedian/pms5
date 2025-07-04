from flask import Blueprint

bp = Blueprint('routes_management', __name__)

from app.routes_management import routes 