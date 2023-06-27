#!/usr/bin/env python3
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from unittest.mock import patch

from slack import WebClient

from src.code.utils.slack_webclient import SlackWebclient

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

all_testing_jsons: Set[str] = set([f for f in os.listdir(ROOT_DIR + "/slack_event_types")])

not_thread_expected_results: List[Dict[str, Any]] = [
    {"name": "01_new_request.json", "result": True, "mock": None},
    {"name": "02_new_request_with_emoji.json", "result": True, "mock": None},
    {"name": "03_editing_main_request.json", "result": True, "mock": {}},
    {"name": "06_adding_new_thread.json", "result": False, "mock": None},
    {"name": "07_editing_thread", "result": False, "mock": None},
    {"name": "10_editing_main_request", "result": True, "mock": {}},
    {"name": "11_new_message_with_file_link.json", "result": True, "mock": None},
    {"name": "12_new_message_file_wo_block.json", "result": True, "mock": None},
    {"name": "13_editing_main_messagev2.json", "result": True, "mock": {}},
    {"name": "14_edit_main_message_with_file_link.json", "result": True, "mock": {}},
    {"name": "15_new_thread_with_file.json", "result": False, "mock": None},
]


class TestSlackWebclient:
    def test_get_requestor_info_result_requestor_info(self, web_client, requestor_id, user_info_response):
        with patch.object(WebClient, "users_info", return_value=user_info_response):
            assert SlackWebclient.get_requestor_info(web_client, requestor_id) == user_info_response

    def test_get_requestor_info_result_exception_and_empty_dict(self, web_client, requestor_id):
        assert SlackWebclient.get_requestor_info(web_client, requestor_id) == {}

    def test_get_requestor_email_result_requestor_email(self, requestor_id, user_info_response, requestor_email):
        assert SlackWebclient.get_requestor_email(user_info_response, requestor_id) == requestor_email

    def test_get_requestor_email_result_requestor_unknown_given_api_raised_exception(self, requestor_id):
        assert SlackWebclient.get_requestor_email({}, requestor_id) == "Unknown"

    def test_get_requestor_team_id_result_requestor_team_id(self, requestor_id, user_info_response, requestor_team_id):
        assert SlackWebclient.get_requestor_team_id(user_info_response, requestor_id) == requestor_team_id

    def test_get_requestor_team_id_result_requestor_unknown_given_api_raised_exception(self, requestor_id):
        assert SlackWebclient.get_requestor_team_id({}, requestor_id) == "Unknown"

    def test_send_post_message_as_main_message(self, web_client, channel_id, blocks):
        with patch.object(WebClient, "chat_postMessage", return_value=None) as test:
            SlackWebclient.send_post_message_as_main_message(web_client, channel_id, blocks)
            test.assert_called_with(channel=channel_id, blocks=blocks)

    def test_send_post_message_to_thread(self, web_client, channel_id, event_ts, blocks):
        with patch.object(WebClient, "chat_postMessage", return_value=None) as test:
            SlackWebclient.send_post_message_to_thread(web_client, channel_id, event_ts, [blocks])
            test.assert_called_with(channel=channel_id, thread_ts=event_ts, blocks=[blocks])

    def test_get_bot_id(self, web_client):
        with patch.object(WebClient, "auth_test", return_value={"user_id": "user_1"}):
            assert SlackWebclient.get_bot_id(web_client) == "user_1"
