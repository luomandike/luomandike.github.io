from flask import Blueprint

passport_blueprint = Blueprint("passport_blueprint", __name__, url_prefix="/passport")


from . import views

