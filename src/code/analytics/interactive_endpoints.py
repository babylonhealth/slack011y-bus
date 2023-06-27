import json
import os

from flask import Blueprint
from flask import make_response
from flask import request

from src.code.analytics.form_answers_collector_clear_form import FormQuestionCollectorClearForm
from src.code.analytics.form_answers_collector_fill_existing import FormQuestionCollectorFillExisting
from src.code.logger import create_logger
from src.code.model.custom_enums import QuestionState

logger = create_logger(__name__)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

blueprint = Blueprint("interactive_endpoints", __name__)


@blueprint.route("/slack/interactive-endpoints", methods=["POST"])
def interactive_endpoints():
    payload = json.loads(request.form.get("payload", {}))
    channel_id = payload["channel"]["id"]
    actions = payload["actions"]
    if actions[0]["type"] == "multi_static_select":
        FormQuestionCollectorFillExisting().fill_question_form(
            state=QuestionState.WORKING, channel_id=channel_id, message=payload["message"], actions=actions
        )
    if actions[0]["type"] == "button":
        FormQuestionCollectorClearForm().clear_question_form(
            channel_id=channel_id, message=payload["message"], actions=actions
        )
    return make_response()
