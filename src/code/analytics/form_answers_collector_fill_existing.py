#!/usr/bin/env python3
import json
from typing import Dict
from typing import List

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


class FormQuestionCollectorFillExisting:
    def fill_question_form(self, state: QuestionState, channel_id: str, message: Dict, actions: List) -> None:
        channel_name = ControlPanel().get_channel_name(channel_id)
        channel_properties: ChannelProperties = ControlPanel().get_channel_properties_by_channel_id(
            channel_id=channel_id
        )
        form_questions: QuestionForm = channel_properties.question_forms
        if not channel_properties.is_active_question_form():
            return
        try:
            FORM_TITLE_HEADER["text"]["text"] = form_questions.form_title
            block = [FORM_TITLE_HEADER, DIVIDER]
            if state == QuestionState.WORKING:
                logger.info("Creating next question for channel id %s", channel_id)
                modified_question_ts = message["ts"] if message is not None else None
                main_ts = message["thread_ts"] if message is not None else None
                saved_form_answers: Dict = Request().get_form_answers(channel_id, main_ts)
                logger.info(
                    "Saved form answers: %s for channel_id %s, and ts %s ", saved_form_answers, channel_id, main_ts
                )
                saving_form_answers = []
                for question in form_questions.questions:
                    if saved_form_answers is not None and saved_form_answers.get(question.action_id) is not None:
                        logger.info("Creating buttons based on saved form answers for channel_id %s", channel_id)
                        block.extend(
                            FormQuestionCollectorUtils.get_buttons(question, saved_form_answers.get(question.action_id))
                        )
                    else:
                        (
                            form_answers,
                            previous_actions_buttons,
                        ) = FormQuestionCollectorUtils.get_buttons_from_previous_action(question, actions)
                        logger.info(
                            "Retrieved form_answers %s and previous actions buttons %s for channel_id %s",
                            form_answers,
                            previous_actions_buttons,
                            channel_id,
                        )
                        if len(previous_actions_buttons) > 0:
                            block.extend(previous_actions_buttons)
                            saving_form_answers.append({"action_id": question.action_id, "form_answers": form_answers})
                        else:
                            block.extend(FormQuestionCollectorUtils.get_multi_select_form(question, actions))
                            break
                        if question == form_questions.questions[-1]:
                            logger.info(
                                (
                                    "Creating recommendation based on saved form_answers %s and actions %s for"
                                    " channel_id %s"
                                ),
                                json.dumps(saved_form_answers),
                                json.dumps(actions),
                                channel_id,
                            )
                            block.extend(
                                FormQuestionCollectorUtils.get_recommendations(
                                    form_questions, saved_form_answers, actions
                                )
                            )
                logger.info(
                    "Block %s for sending to the thread for channel_id %s and ts %s",
                    block,
                    channel_id,
                    modified_question_ts,
                )
                SlackWebclient().modify_thread_message(client, channel_id, modified_question_ts, block)
                logger.info("Saving form_answers %s for channel_id %s", saving_form_answers, channel_id)
                FormQuestionCollectorUtils.save_form_answers(saving_form_answers, channel_id, main_ts)
        except Exception:
            if channel_name:
                logger.exception("There were problems while handling channel '%s'.", channel_name)
            if channel_id:
                logger.exception("There were problems while handling channel '%s'.", channel_id)
