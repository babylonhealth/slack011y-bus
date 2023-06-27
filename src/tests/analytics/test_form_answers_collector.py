from unittest.mock import patch

from src.code.analytics.const.slack_request_details_collector_const import DIVIDER
from src.code.analytics.form_answers_collector_clear_form import FormQuestionCollectorClearForm
from src.code.analytics.form_answers_collector_fill_existing import FormQuestionCollectorFillExisting
from src.code.analytics.form_answers_collector_new_form import FormQuestionCollectorNewForm
from src.code.const import client
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import QuestionState
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import channel_properties_schema
from src.code.utils.slack_webclient import SlackWebclient


class TestFormAnswersCollector:
    def test_create_question_form_results_do_nothing_given_feature_is_disable(
        self, cp_with_question_form, channel_id, channel_name, form_questions
    ):
        form_question_enabled = False
        control_panel: ControlPanel = cp_with_question_form(
            form_questions=form_questions, form_question_enabling=form_question_enabled
        )
        channel_properties: ChannelProperties = channel_properties_schema.load(control_panel.channel_properties)
        with patch.object(ControlPanel, "get_channel_id_by_channel_name", return_value=channel_id):
            with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=channel_properties):
                FormQuestionCollectorNewForm().create_question_form(
                    state=QuestionState.NEW, channel_name=channel_name, ts=""
                )

    def test_create_question_form_result_do_nothing_form_was_already_initialized(
        self, cp_with_question_form, channel_id, channel_name, form_questions
    ):
        channel_properties: ChannelProperties = channel_properties_schema.load(
            cp_with_question_form(form_questions=form_questions).channel_properties
        )
        with patch.object(ControlPanel, "get_channel_id_by_channel_name", return_value="channel_id"):
            with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=channel_properties):
                with patch.object(Request, "get_form_answers", return_value={}):
                    FormQuestionCollectorNewForm().create_question_form(
                        state=QuestionState.NEW, channel_name=channel_name, ts=""
                    )

    def test_create_question_form_result_one_multi_select_form(
        self, cp_with_question_form, channel_id, channel_name, form_questions, event_ts
    ):
        expected_block = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": form_questions["form_title"]},
            },
            DIVIDER,
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": form_questions["questions"][0]["question_title"]},
                "accessory": {
                    "type": "multi_static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": form_questions["questions"][0]["options_title"],
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": form_questions["questions"][0]["options"]["default"][0],
                                "emoji": True,
                            },
                            "value": form_questions["questions"][0]["options"]["default"][0],
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": form_questions["questions"][0]["options"]["default"][1],
                                "emoji": True,
                            },
                            "value": form_questions["questions"][0]["options"]["default"][1],
                        },
                    ],
                    "action_id": form_questions["questions"][0]["action_id"],
                },
            },
            DIVIDER,
        ]
        channel_properties: ChannelProperties = channel_properties_schema.load(
            cp_with_question_form(form_questions=form_questions).channel_properties
        )

        with patch.object(ControlPanel, "get_channel_id_by_channel_name", return_value=channel_id):
            with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=channel_properties):
                with patch.object(Request, "get_form_answers", return_value=None):
                    with patch.object(
                        SlackWebclient, "send_post_message_to_thread", return_value=None
                    ) as patched_utils:
                        with patch.object(Request, "init_form_answers", return_value=None) as channel_init:
                            FormQuestionCollectorNewForm().create_question_form(
                                state=QuestionState.NEW, channel_name=channel_name, ts=str(event_ts)
                            )
                            patched_utils.assert_called_once_with(client, channel_name, str(event_ts), expected_block)
                            channel_init.assert_called_once_with(channel_id, str(event_ts))

    def test_fill_question_form_result_previous_action_button_and_one_multi_select_form(
        self, cp_with_question_form, form_questions, channel_id, channel_name
    ):
        expected_block = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": form_questions["form_title"]},
            },
            DIVIDER,
            {
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🗑️ Clear form", "emoji": True},
                    "value": "click_me_123",
                    "action_id": form_questions["questions"][0]["action_id"],
                },
                "text": {"type": "mrkdwn", "text": form_questions["questions"][0]["question_title"]},
                "type": "section",
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "text": {
                            "emoji": True,
                            "text": form_questions["questions"][0]["options"]["default"][0],
                            "type": "plain_text",
                        },
                        "type": "button",
                        "value": form_questions["questions"][0]["options"]["default"][0],
                    }
                ],
            },
            DIVIDER,
            {
                "accessory": {
                    "type": "multi_static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": form_questions["questions"][1]["options_title"],
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": form_questions["questions"][1]["options"]["option_1"][0],
                                "emoji": True,
                            },
                            "value": form_questions["questions"][1]["options"]["option_1"][0],
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": form_questions["questions"][1]["options"]["option_1"][1],
                                "emoji": True,
                            },
                            "value": form_questions["questions"][1]["options"]["option_1"][1],
                        },
                    ],
                    "action_id": form_questions["questions"][1]["action_id"],
                },
                "text": {"type": "mrkdwn", "text": form_questions["questions"][1]["question_title"]},
                "type": "section",
            },
            DIVIDER,
        ]
        actions = [
            {
                "action_id": form_questions["questions"][0]["action_id"],
                "selected_options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": form_questions["questions"][0]["options"]["default"][0],
                            "emoji": True,
                        },
                        "value": form_questions["questions"][0]["options"]["default"][0],
                    }
                ],
            }
        ]
        channel_properties: ChannelProperties = channel_properties_schema.load(
            cp_with_question_form(form_questions=form_questions).channel_properties
        )
        with patch.object(ControlPanel, "get_channel_name", return_value=channel_name):
            with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=channel_properties):
                with patch.object(Request, "get_form_answers", return_value=None):
                    with patch.object(SlackWebclient, "modify_thread_message", return_value=None) as patched_utils:
                        with patch.object(Request, "save_form_answers", return_value=None) as save_form:
                            FormQuestionCollectorFillExisting().fill_question_form(
                                state=QuestionState.WORKING,
                                channel_id=channel_id,
                                message={"ts": 11.11, "thread_ts": 12.12},
                                actions=actions,
                            )
                            patched_utils.assert_called_once_with(client, channel_id, 11.11, expected_block)
                            save_form.assert_called_once()

    def test_fill_question_form_result_db_question_and_previous_action_button_and_final_recommendation(
        self, cp_with_question_form, form_questions, channel_id, channel_name
    ):
        expected_block = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": form_questions["form_title"]},
            },
            DIVIDER,
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": form_questions["questions"][0]["question_title"]},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": form_questions["questions"][0]["options"]["default"][0],
                            "emoji": True,
                        },
                        "value": form_questions["questions"][0]["options"]["default"][0],
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": form_questions["questions"][0]["options"]["default"][1],
                            "emoji": True,
                        },
                        "value": form_questions["questions"][0]["options"]["default"][1],
                    },
                ],
            },
            DIVIDER,
            {
                "accessory": {
                    "action_id": form_questions["questions"][1]["action_id"],
                    "text": {"emoji": True, "text": "🗑️ Clear form", "type": "plain_text"},
                    "type": "button",
                    "value": "click_me_123",
                },
                "text": {"text": form_questions["questions"][1]["question_title"], "type": "mrkdwn"},
                "type": "section",
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": form_questions["questions"][1]["options"]["option_1"][0],
                            "emoji": True,
                        },
                        "value": form_questions["questions"][1]["options"]["option_1"][0],
                    }
                ],
            },
            DIVIDER,
            {
                "text": {
                    "text": "We found some recommendations for you, thank you for improving our tool",
                    "type": "mrkdwn",
                },
                "type": "section",
            },
            DIVIDER,
            {
                "text": {
                    "text": (
                        "1. "
                        + form_questions["questions"][0]["options"]["default"][0]
                        + " -> "
                        + form_questions["questions"][1]["options"]["option_1"][0]
                        + " -> \n\t - <link1|rec1> \n"
                    ),
                    "type": "mrkdwn",
                },
                "type": "section",
            },
        ]
        saved_labels = {
            form_questions["questions"][0]["action_id"]: [
                form_questions["questions"][0]["options"]["default"][0],
                form_questions["questions"][0]["options"]["default"][1],
            ]
        }
        actions = [
            {
                "action_id": form_questions["questions"][1]["action_id"],
                "selected_options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": form_questions["questions"][1]["options"]["option_1"][0],
                            "emoji": True,
                        },
                        "value": form_questions["questions"][1]["options"]["option_1"][0],
                    }
                ],
            }
        ]
        channel_properties: ChannelProperties = channel_properties_schema.load(
            cp_with_question_form(form_questions=form_questions).channel_properties
        )
        with patch.object(ControlPanel, "get_channel_name", return_value=channel_name):
            with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=channel_properties):
                with patch.object(Request, "get_form_answers", return_value=saved_labels):
                    with patch.object(SlackWebclient, "modify_thread_message", return_value=None) as patched_utils:
                        with patch.object(Request, "save_form_answers", return_value=None):
                            FormQuestionCollectorFillExisting().fill_question_form(
                                state=QuestionState.WORKING,
                                channel_id=channel_id,
                                message={"ts": 11.11, "thread_ts": 12.12},
                                actions=actions,
                            )
                            patched_utils.assert_called_once_with(client, channel_id, 11.11, expected_block)

    def test_clear_question_form_results_cleaning_form_and_showing_first_question(
        self, cp_with_question_form, channel_id, form_questions
    ):
        expected_block = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": form_questions["form_title"]},
            },
            DIVIDER,
            {
                "accessory": {
                    "type": "multi_static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": form_questions["questions"][0]["options_title"],
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": form_questions["questions"][0]["options"]["default"][0],
                                "emoji": True,
                            },
                            "value": form_questions["questions"][0]["options"]["default"][0],
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": form_questions["questions"][0]["options"]["default"][1],
                                "emoji": True,
                            },
                            "value": form_questions["questions"][0]["options"]["default"][1],
                        },
                    ],
                    "action_id": form_questions["questions"][0]["action_id"],
                },
                "text": {"type": "mrkdwn", "text": form_questions["questions"][0]["question_title"]},
                "type": "section",
            },
            DIVIDER,
        ]
        actions = [
            {
                "action_id": form_questions["questions"][0]["action_id"],
                "block_id": "9Ri",
                "text": {"type": "plain_text", "text": ":wastebasket: Clear form", "emoji": True},
                "value": "click_me_123",
                "type": "button",
                "action_ts": "1654840375.043467",
            }
        ]
        channel_properties: ChannelProperties = channel_properties_schema.load(
            cp_with_question_form(form_questions=form_questions).channel_properties
        )
        with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=channel_properties):
            with patch.object(Request, "remove_all_form_answers", return_value=None):
                with patch.object(SlackWebclient, "modify_thread_message", return_value=None) as patched_utils:
                    FormQuestionCollectorClearForm().clear_question_form(
                        channel_id=channel_id, message={"ts": 11.11, "thread_ts": 12.12}, actions=actions
                    )
                    patched_utils.assert_called_once_with(client, channel_id, 11.11, expected_block)
