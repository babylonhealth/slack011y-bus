from flask import Blueprint
from flask import redirect

from src.code.const import api

swagger_redirect = Blueprint("rd_swagger", __name__)


@swagger_redirect.route("/admin/swagger")
@swagger_redirect.route("/swagger")
@swagger_redirect.route("/admin")
def rd_swagger():
    return redirect(api.base_url + "/swagger/")
