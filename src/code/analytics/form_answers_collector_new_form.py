#!/usr/bin/env python3
from src.code.analytics.const.slack_request_details_collector_const import DIVIDER
from src.code.analytics.const.slack_request_details_collector_const import FORM_TITLE_HEADER
from src.code.analytics.form_answers_collector_utils import FormQuestionCollectorUtils
from src.code.const import client
from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import QuestionState
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import QuestionForm
from src.code.utils.slack_webclient import SlackWebclient

logger = create_logger(__name__)


class FormQuestionCollectorNewForm:
    def create_question_form(self, state: QuestionState, channel_name: str, ts: str) -> None:
        channel_id: str = ControlPanel().get_channel_id_by_channel_name(channel_name)
        channel_properties: ChannelProperties = ControlPanel().get_channel_properties_by_channel_id(
            channel_id=channel_id
        )
        form_questions: QuestionForm = channel_properties.question_forms
        if not channel_properties.is_active_question_form():
            return
        try:
            FORM_TITLE_HEADER["text"]["text"] = form_questions.form_title
            block = [FORM_TITLE_HEADER, DIVIDER]
            if state == QuestionState.NEW and Request().get_form_answers(channel_id, ts) is None:
                logger.info("Creating first question for channel %s", channel_name)
                block.extend(FormQuestionCollectorUtils.get_multi_select_form(form_questions.questions[0]))
                SlackWebclient.send_post_message_to_thread(client, channel_name, ts, block)
                FormQuestionCollectorUtils.init_form_answers(channel_id, ts)
        except Exception:
            if channel_name:
                logger.exception("There were problems while handling channel '%s'.", channel_name)
