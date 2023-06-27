#!/usr/bin/env python3
from typing import Dict
from typing import List

from src.code.analytics.const.slack_request_details_collector_const import DIVIDER
from src.code.analytics.const.slack_request_details_collector_const import FORM_TITLE_HEADER
from src.code.analytics.form_answers_collector_utils import FormQuestionCollectorUtils
from src.code.const import client
from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import QuestionForm
from src.code.utils.slack_webclient import SlackWebclient

logger = create_logger(__name__)


class FormQuestionCollectorClearForm:
    def clear_question_form(self, channel_id: str, message: Dict, actions: List) -> None:
        try:
            channel_properties: ChannelProperties = ControlPanel().get_channel_properties_by_channel_id(
                channel_id=channel_id
            )
            form_questions: QuestionForm = channel_properties.question_forms
            if actions[0]["action_id"] in [question.action_id for question in form_questions.questions]:
                main_ts = message["thread_ts"]
                modified_question_ts = message["ts"]
                FormQuestionCollectorUtils.remove_all_form_answers(channel_id, main_ts)
                FORM_TITLE_HEADER["text"]["text"] = form_questions.form_title
                block = [FORM_TITLE_HEADER, DIVIDER]
                block.extend(FormQuestionCollectorUtils.get_multi_select_form(form_questions.questions[0]))
                SlackWebclient.modify_thread_message(client, channel_id, modified_question_ts, block)
        except Exception:
            logger.exception("There were problems while handling channel '%s'.", channel_id)
