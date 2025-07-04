from flask import Blueprint

bp = Blueprint('bom_management', __name__)

from app.bom_management import routes 