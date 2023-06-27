import pytest
from flask import Blueprint
from flask import Flask
from flask.testing import FlaskClient
from flask_restx import Api

from src.code.admin_panel.channel_api import ns as channel_ns  # noqa
from src.code.admin_panel.completion import completion_ns  # noqa
from src.code.admin_panel.idle_threads import idle_threads_ns  # noqa
from src.code.admin_panel.question_forms import ns as question_form_ns  # noqa
from src.code.admin_panel.start_work_api import ns as start_work_ns  # noqa
from src.code.admin_panel.types_api import types_ns  # noqa


@pytest.fixture()
def client() -> FlaskClient:
    app: Flask = Flask(__name__)
    app.config.from_object("src.tests.config.Config")
    swagger: Blueprint = Blueprint("api", __name__, url_prefix="/admin/api/v1")
    api: Api = Api(swagger)
    api.add_namespace(channel_ns)
    api.add_namespace(types_ns, path="/channels/<string:channel_id>/actions/types")
    api.add_namespace(start_work_ns, path="/channels/<string:channel_id>/actions/start_reactions")
    api.add_namespace(question_form_ns, path="/channels/<string:channel_id>/actions/question_forms")
    api.add_namespace(completion_ns, path="/channels/<string:channel_id>/actions/completion_reactions")
    api.add_namespace(idle_threads_ns, path="/channels/<string:channel_id>/close_idle_threads")
    app.register_blueprint(swagger)
    return app.test_client()


@pytest.fixture()
def question_forms():
    return {
        "creation_ts": 11.11,
        "form_title": "title",
        "triggers": [],
        "questions": [
            {
                "name": "question_1",
                "question_title": "title",
                "action_id": "action",
                "options_title": "options",
                "options": {},
            }
        ],
        "recommendations": {},
    }
