#!/usr/bin/env python3
import copy
import math
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from src.code.analytics.const.slack_request_details_collector_const import BUTTON_FORM
from src.code.analytics.const.slack_request_details_collector_const import BUTTON_FORM_WITH_CLEAR_FORM
from src.code.analytics.const.slack_request_details_collector_const import DIVIDER
from src.code.analytics.const.slack_request_details_collector_const import MULTI_STATIC_SELECT_FORM
from src.code.analytics.const.slack_request_details_collector_const import SECTION
from src.code.logger import create_logger
from src.code.model.request import Request
from src.code.model.schemas import Question
from src.code.model.schemas import QuestionForm
from src.code.utils.utils import flat_list
from src.code.utils.utils import remove_duplicates_with_order

logger = create_logger(__name__)


class FormQuestionCollectorUtils:
    @staticmethod
    def get_multi_select_form(question_details: Question, actions: List = None) -> List[Dict]:
        option_types = ["default"] if not actions else [option["value"] for option in actions[0]["selected_options"]]
        options = remove_duplicates_with_order(
            flat_list(
                [
                    question_details.options.get(option_type, question_details.options.get("default"))
                    for option_type in option_types
                ]
            )
        )
        form = copy.deepcopy(MULTI_STATIC_SELECT_FORM)
        form["text"]["text"] = question_details.question_title
        form["accessory"]["action_id"] = question_details.action_id
        form["accessory"]["placeholder"]["text"] = question_details.options_title
        form["accessory"]["options"] = list(
            [{"text": {"type": "plain_text", "text": option, "emoji": True}, "value": option} for option in options]
        )
        return [form, DIVIDER]

    @staticmethod
    def get_buttons(question: Question, form_answers: Optional[List]) -> List[Dict]:
        if form_answers is None:
            return []
        button_form = copy.deepcopy(BUTTON_FORM)
        button_form[0]["text"]["text"] = question.question_title
        button_form[1]["elements"] = [
            {"type": "button", "text": {"type": "plain_text", "text": answer, "emoji": True}, "value": answer}
            for answer in form_answers
        ]
        button_form.append(DIVIDER)
        return button_form

    @staticmethod
    def get_buttons_from_previous_action(question: Question, actions: Optional[List[Any]]) -> tuple:
        actions = [] if actions is None else actions
        elements = []
        form_answers = []
        for action in actions:
            if action["action_id"] == question.action_id:
                for button in action["selected_options"]:
                    form_answer = button["text"]["text"]
                    form_answers.append(form_answer)
                    elements.append(
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": form_answer, "emoji": True},
                            "value": form_answer,
                        }
                    )
        if len(elements) == 0:
            return [], []
        button_form = copy.deepcopy(BUTTON_FORM_WITH_CLEAR_FORM)
        button_form[0]["text"]["text"] = question.question_title
        button_form[0]["accessory"]["action_id"] = question.action_id
        button_form[1]["elements"] = elements
        button_form.append(DIVIDER)
        return form_answers, button_form

    @classmethod
    def get_recommendations(
        cls, form_questions: QuestionForm, saved_form_answers: Optional[Dict], actions: Optional[List[Any]]
    ) -> List[Dict]:
        recommendations = copy.deepcopy(SECTION)
        actions_options: List = (
            ["default"] if not actions else [option["value"] for option in actions[0]["selected_options"]]
        )

        rec_str = ""
        rec_cnt = 1
        recommendation_dict = form_questions.recommendations
        if recommendation_dict:
            for modified_label in cls._get_modified_form_answers(form_questions, saved_form_answers, actions_options):
                try:
                    rs = cls._get_recommendation_from_dict(modified_label, recommendation_dict)
                except KeyError:
                    pass
                else:
                    rec_str += f"{rec_cnt}. "
                    for label in modified_label:
                        rec_str += label + " -> "
                    rec_str += "\n"
                    for r in rs:
                        rec_str += f"\t - <{r.get('link')}" + "|" + f"{r.get('name')}> \n"
                    rec_cnt += 1
        recommendations["text"]["text"] = rec_str

        recommendation_title = copy.deepcopy(SECTION)
        if rec_str != "":
            recommendation_title["text"][
                "text"
            ] = "We found some recommendations for you, thank you for improving our tool"
            return [recommendation_title, DIVIDER, recommendations]
        else:
            recommendation_title["text"][
                "text"
            ] = "We haven't found recommendations for you, thank you for improving our tool"
            return [recommendation_title]

    @staticmethod
    def init_form_answers(channel_id: Optional[str], main_ts: str):
        if channel_id is None:
            raise ValueError("Channel_id has not been provided")
        Request().init_form_answers(channel_id, main_ts)

    @staticmethod
    def save_form_answers(saving_form_answers: List[Dict], channel_id: Optional[str], main_ts: str) -> None:
        if channel_id is None:
            raise ValueError("Channel_id has not been provided")
        for answer in saving_form_answers:
            Request().save_form_answers(channel_id, main_ts, answer["action_id"], answer["form_answers"])

    @staticmethod
    def remove_all_form_answers(channel_id: str, main_ts: str) -> None:
        Request().remove_all_form_answers(channel_id, main_ts)

    @classmethod
    def _get_modified_form_answers(
        cls, form_questions: QuestionForm, saved_form_answers: Optional[Dict], actions_options: List
    ) -> List:
        form_answers: List = []
        pair_length: int = 1
        for question in form_questions.questions:
            if question.action_id and saved_form_answers and saved_form_answers.get(question.action_id):
                saved_form_answers_for_question: List = saved_form_answers[question.action_id]
                form_answers.append(saved_form_answers_for_question)
                pair_length *= len(saved_form_answers_for_question)
            else:
                form_answers.append(actions_options)
                pair_length *= len(actions_options)

        modified_form_answers = []
        for i in range(pair_length):
            el = []
            for idx, label in enumerate(form_answers):
                partition = int(pair_length / cls._get_quotient(idx, form_answers))
                t_idx = math.floor(i / partition) - len(label) * math.floor(i / len(label) / partition)
                el.append(label[t_idx])
            modified_form_answers.append(el)
        return modified_form_answers

    @classmethod
    def _get_quotient(cls, idx: int, form_answers: List) -> int:
        quotient = 1
        for label in form_answers[: idx + 1]:
            quotient = quotient * len(label)
        return quotient

    @classmethod
    def _get_recommendation_from_dict(cls, modified_label: List, recommendation_dict: Dict) -> Dict:
        for label in modified_label:
            recommendation_dict = recommendation_dict[label]
        return recommendation_dict["recommendations"]
