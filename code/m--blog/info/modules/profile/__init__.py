from flask import Blueprint

profile_blueprint = Blueprint("profile", __name__, url_prefix="/profile")

from . import views