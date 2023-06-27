#!/usr/bin/env python3
import json
import os
from unittest.mock import patch

from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import MessageType
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.utils.slack_main_request import SlackMainRequest
from src.code.utils.slack_webclient import SlackWebclient

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestSlackMainRequest:
    def test_deal_with_main_message(self, web_client, slack_event_types_folder, channel_properties):
        with open(os.path.join(slack_event_types_folder, "01_new_request.json")) as file:
            with patch.object(ControlPanel, "get_channel_name", return_value="channel_name"):
                with patch.object(Request, "update_or_register_new_record", return_value=None):
                    with patch.object(SlackWebclient, "send_post_message_to_thread", return_value=None) as test:
                        SlackMainRequest().deal_with_main_message(
                            web_client, json.load(file), MessageType.MAIN_NEW, channel_properties
                        )
                        test.assert_called()

    def test_deal_with_main_message_emoji_type_not_enabled(self, web_client, slack_event_types_folder):
        with open(os.path.join(slack_event_types_folder, "01_new_request.json")) as file:
            with patch.object(ControlPanel, "get_channel_name", return_value="channel_name"):
                with patch.object(Request, "update_or_register_new_record", return_value=None):
                    with patch.object(SlackWebclient, "send_post_message_to_thread", return_value=None) as test:
                        channel_properties: ChannelProperties = ChannelProperties()
                        channel_properties.features.types.enabled = False
                        SlackMainRequest().deal_with_main_message(
                            web_client, json.load(file), MessageType.MAIN_NEW, channel_properties
                        )
                        test.assert_not_called()


# def test_deal_with_main_message_results_question_form_was_started(
#     self, web_client, slack_event_types_folder, channel_properties
# ):
#     with open(os.path.join(slack_event_types_folder, "02_new_request_with_emoji.json")) as file:
#         with patch.object(ControlPanel, "get_channel_name", return_value="channel_name"):
#             with patch.object(Request, "update_or_register_new_record", return_value=None):
#                 with patch.object(SlackWebclient, "send_post_message_to_thread", return_value=None) as send_post:
#                     with patch.object(
#                         FormQuestionCollector, "create_question_form", return_value=None
#                     ) as create_form:
#                         channel_properties.features.question_form.enabled = True
#                         question_form: QuestionForm = question_form_schema.load(
#                             {
#                                 "creation_ts": datetime.now().timestamp(),
#                                 "form_title": "form_title",
#                                 "triggers": ["cloud-help"],
#                                 "questions": [
#                                     {
#                                         "name": "question_1",
#                                         "question_title": "question_title_1",
#                                         "action_id": "action_id_1",
#                                         "options_title": "options_title_1",
#                                         "options": {"default": ["option_1", "option_2"]},
#                                     },
#                                     {
#                                         "name": "question_2",
#                                         "question_title": "question_title_2",
#                                         "action_id": "action_id_2",
#                                         "options_title": "options_title_2",
#                                         "options": {
#                                             "default": ["option_3", "option_4"],
#                                             "option_1": ["option_5", "option_6"],
#                                         },
#                                     },
#                                 ],
#                                 "recommendations": {
#                                     "option_1": {
#                                         "option_5": {"recommendations": [{"name": "rec1", "link": "link1"}]}
#                                     },
#                                     "option_2": {
#                                         "Documentation": {"recommendations": [{"name": "rec2", "link": "link2"}]}
#                                     },
#                                 },
#                             }
#                         )
#                         channel_properties.question_forms = question_form
#                         SlackMainRequest().deal_with_main_message(
#                             web_client, json.load(file), MessageType.MAIN_NEW, channel_properties
#                         )
#                         send_post.assert_not_called()
#                         create_form.assert_called_once()
