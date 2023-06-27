# import monkeypatch  # noqa  # noreorder  # isort: skip
import os
from typing import Dict

from slackeventsapi import SlackEventAdapter

from src.code.const import api
from src.code.const import client
from src.code.const import create_app
from src.code.const import swagger
from src.code.db import db
from src.code.logger import create_logger
from src.code.scheduler.manager import SchedulerManager
from src.code.utils.custom_event_adapter import CustomEventAdapter
from src.code.utils.utils import required_envar

logger = create_logger(__name__)

app = create_app("src.code.config.Config")
slack_event_adapter = SlackEventAdapter(required_envar("SIGNING_SECRET"), "/slack/events", app)
db.init_app(app)
if "SCHEDULER_LOADED" not in os.environ:
    os.environ["SCHEDULER_LOADED"] = "TRUE"
    scheduler_manager = SchedulerManager(app)
    scheduler_manager.start()


# Reacting on a new message or a thread message
@slack_event_adapter.on("message")
def message(payload: Dict) -> None:
    CustomEventAdapter.message(payload, client)


@slack_event_adapter.on("reaction_added")
def add_reaction_to_request(payload) -> None:
    CustomEventAdapter.add_reaction_to_request(payload, client)


@slack_event_adapter.on("reaction_removed")
def remove_reaction_from_request(payload) -> None:
    CustomEventAdapter.remove_reaction_from_request(payload, client)


@app.route("/health", methods=["GET", "POST"])
def health():
    return "Success", 200


@app.route("/live", methods=["GET", "POST"])
def live():
    return "Success", 200


from src.code.admin_panel.error_handling import bad_request  # noqa
from src.code.admin_panel.error_handling import conflict  # noqa
from src.code.admin_panel.error_handling import error_server  # noqa
from src.code.admin_panel.error_handling import resource_not_found  # noqa
from src.code.analytics.interactive_endpoints import blueprint as interactive_endpoints  # noqa
from src.code.view import blueprint as view  # noqa

app.register_blueprint(view)  # noqa
app.register_blueprint(interactive_endpoints)  # noqa
app.register_error_handler(400, bad_request)
app.register_error_handler(404, resource_not_found)
app.register_error_handler(409, conflict)
app.register_error_handler(500, error_server)

from src.code.admin_panel.channel_api import ns as channel_ns  # noqa
from src.code.admin_panel.completion import completion_ns  # noqa
from src.code.admin_panel.daily_report_api import ns as report_ns  # noqa
from src.code.admin_panel.idle_threads import idle_threads_ns  # noqa
from src.code.admin_panel.question_forms import ns as question_form_ns  # noqa
from src.code.admin_panel.start_work_api import ns as start_work_ns  # noqa
from src.code.admin_panel.swagger import swagger_redirect  # noqa
from src.code.admin_panel.types_api import types_ns  # noqa

api.add_namespace(channel_ns)
api.add_namespace(types_ns, path="/channels/<string:channel_id>/actions/types")
api.add_namespace(start_work_ns, path="/channels/<string:channel_id>/actions/start_reactions")
api.add_namespace(report_ns, path="/channels/<string:channel_id>/actions/reports")
api.add_namespace(question_form_ns, path="/channels/<string:channel_id>/actions/question_forms")
api.add_namespace(completion_ns, path="/channels/<string:channel_id>/actions/completion_reactions")
api.add_namespace(idle_threads_ns, path="/channels/<string:channel_id>/close_idle_threads")
app.register_blueprint(swagger)
app.register_blueprint(swagger_redirect)

if __name__ == "__main__":
    app.run(port=os.environ.get("SERVICE_PORT", 5002), debug=True)
