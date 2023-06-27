import os

from flask import Blueprint
from flask import render_template

from src.code.logger import create_logger

logger = create_logger(__name__)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


blueprint = Blueprint("slack_bot_app", __name__)


@blueprint.route("/")
def home():
    return render_template("base_page.html")
