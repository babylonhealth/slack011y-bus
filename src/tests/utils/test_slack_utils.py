#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from unittest.mock import patch

import pytest

from src.code.model.custom_enums import MessageType
from src.code.model.request import Request
from src.code.utils.slack_event_type import SlackEventType
from src.code.utils.slack_utils import SlackUtils

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

all_testing_jsons: Set[str] = set([f for f in os.listdir(ROOT_DIR + "/slack_event_types")])

channel_id_expected_results: List[Dict] = [
    {"name": "01_new_request.json", "mock": None},
    {"name": "02_new_request_with_emoji.json", "mock": None},
    {"name": "03_editing_main_request.json", "mock": {}},
    {"name": "04_adding_reaction_to_main.json", "mock": None},
    {"name": "05_removing_reaction_from_main.json", "mock": None},
    {"name": "06_adding_new_thread.json", "mock": None},
    {"name": "07_editing_thread.json", "mock": {}},
    {"name": "08_adding_reaction_to_thread.json", "mock": None},
    {"name": "09_removing_reaction_from_thread.json", "mock": None},
    {"name": "10_editing_main_request.json", "mock": {}},
    {"name": "11_new_message_with_file_link.json", "mock": None},
    {"name": "12_new_message_file_wo_block.json", "mock": None},
    {"name": "13_editing_main_messagev2.json", "mock": {}},
    {"name": "14_edit_main_message_with_file_link.json", "mock": {}},
    {"name": "15_new_thread_with_file.json", "mock": None},
]

not_thread_expected_results: List[Dict[str, Any]] = [
    {"name": "01_new_request.json", "result": True, "mock": None},
    {"name": "02_new_request_with_emoji.json", "result": True, "mock": None},
    {"name": "03_editing_main_request.json", "result": True, "mock": {}},
    {"name": "06_adding_new_thread.json", "result": False, "mock": None},
    {"name": "07_editing_thread.json", "result": False, "mock": None},
    {"name": "10_editing_main_request.json", "result": True, "mock": {}},
    {"name": "11_new_message_with_file_link.json", "result": True, "mock": None},
    {"name": "12_new_message_file_wo_block.json", "result": True, "mock": None},
    {"name": "13_editing_main_messagev2.json", "result": True, "mock": {}},
    {"name": "14_edit_main_message_with_file_link.json", "result": True, "mock": {}},
    {"name": "15_new_thread_with_file.json", "result": False, "mock": None},
    {"name": "16_message_deleted.json", "result": False, "mock": None},
]


class TestSlackUtils:
    def test_get_event_results_event(self):
        payload: Dict = {"event": {}}
        assert SlackUtils.get_event(payload) == {}

    def test_get_event_results_exception_given_event_not_found_in_payload(self):
        with pytest.raises(KeyError, match="('Event not found in payload:', {})"):
            SlackUtils.get_event({})

    @pytest.mark.parametrize("filename", all_testing_jsons)
    def test_get_user_results_user_given_user_provided_in_the_event(self, filename, slack_event_types_folder):
        with open(os.path.join(slack_event_types_folder, filename)) as file:
            assert SlackUtils.get_user(json.load(file)) is not None

    def test_get_user_results_exception_given_user_not_found_in_payload(self):
        with pytest.raises(KeyError, match="('User not found in event:', {})"):
            SlackUtils.get_user({})

    @pytest.mark.parametrize("item", channel_id_expected_results)
    def test_get_channel_id_results_channel_id(self, item, slack_event_types_folder):
        with open(os.path.join(slack_event_types_folder, item["name"])) as file:
            with patch.object(Request, "get_request", return_value=item["mock"]):
                assert SlackUtils.get_channel_id(json.load(file)) is not None

    def test_get_channel_id_results_throw_exception_given_channel_id_not_provided(self):
        with pytest.raises(ValueError, match="('Failed to find channel id on event %s', '{}')"):
            with patch.object(SlackEventType, "get_event_type", return_value=MessageType.MAIN_NEW):
                SlackUtils.get_channel_id({})

    @pytest.mark.parametrize("item", channel_id_expected_results)
    def test_get_main_ts_results_return_main_ts(self, item, slack_event_types_folder):
        with open(os.path.join(slack_event_types_folder, item["name"])) as file:
            with patch.object(Request, "get_request", return_value=item["mock"]):
                assert SlackUtils.get_main_ts(json.load(file)) is not None

    def test_get_main_ts_results_results_throw_exception_given_main_ts_not_provided(self):
        with pytest.raises(ValueError, match="('Failed to find event ts on event %s', '{}')"):
            with patch.object(SlackEventType, "get_event_type", return_value=MessageType.MAIN_NEW):
                SlackUtils.get_main_ts({})

    @pytest.mark.parametrize(
        "item",
        {
            (MessageType.MAIN_NEW, True),
            (MessageType.MAIN_EDIT, True),
            (MessageType.MAIN_NEW_FILE, True),
            (MessageType.THREAD_EDIT, False),
            (MessageType.THREAD_NEW, False),
            (MessageType.THREAD_NEW_FILE, False),
        },
    )
    def test_is_main_message(self, item):
        assert item[1] == SlackUtils.is_main_message_event(item[0])

    def test_get_data_from_new_message_results_exception_given_message_has_no_blocks_section(self):
        with pytest.raises(KeyError):
            SlackUtils.get_data_from_event({})

    def test_get_data_from_new_message_results_requested_data_given_message_has_blocks_section(self):
        org_ts = "1648451272.633599"
        user = "BOGUS_USER_ID6"
        channel = "channel"
        emoji = {"type": "emoji", "name": "rotating_light"}
        text = {"type": "text", "text": "This text needs to be extracted"}
        inner_elements: Dict = {"elements": [emoji, text]}
        outer_elements: Dict = {"elements": [inner_elements]}
        event: Dict = {"blocks": [outer_elements], "ts": org_ts, "user": user, "channel": channel}

        blocks, elements, ts, requestor = SlackUtils.get_data_from_event(event)
        assert blocks == [outer_elements]
        assert elements == inner_elements.get("elements")
        assert ts == org_ts
        assert requestor == user

    @pytest.mark.parametrize(
        "filename",
        {
            "01_new_request.json",
            "02_new_request_with_emoji.json",
            "06_adding_new_thread.json",
            "11_new_message_with_file_link.json",
            "12_new_message_file_wo_block.json",
            "15_new_thread_with_file.json",
        },
    )
    def test_get_data_from_new_message_results_extracts_block_section_given_different_type_of_requests(
        self, filename, slack_event_types_folder
    ):
        with open(os.path.join(slack_event_types_folder, filename)) as file:
            block, elements, ts, author = SlackUtils.get_data_from_event(json.load(file))
            assert ts
            assert author
            if filename in {"12_new_message_file_wo_block.json", "15_new_thread_with_file.json"}:
                assert block is None
                assert elements is None
            else:
                assert block
                assert elements

    def test_get_request_types_from_elements_results_list_given_elements_and_keys_from_types_dict(
        self, channel_properties
    ):
        elements = [
            {"type": "emoji", "name": "cloud-incident"},
            {"type": "text", "text": "This text needs to be extracted"},
            {"type": "emoji", "name": "cloud-incident"},
            {"type": "emoji", "name": "cloud-pr"},
            {"type": "emoji", "name": "cloud-props"},
            {"type": "emoji", "name": "cloud-think"},
            {"type": "emoji", "name": "cloud-help"},
            {"type": "emoji", "name": "cloud-feature"},
            {"type": "emoji", "name": "cloud-random"},
            {"type": "emoji", "name": "cloud-clarify"},
            {"type": "emoji", "name": "cloud-bug"},
        ]

        expected_result = {
            "cloud-incident",
            "cloud-pr",
            "cloud-props",
            "cloud-think",
            "cloud-help",
            "cloud-feature",
            "cloud-bug",
            "cloud-random",
            "cloud-clarify",
        }
        assert set(SlackUtils.get_request_types_from_elements(elements, channel_properties)) == expected_result

    def test_get_request_link_results_request_link_given_all_data_provided(self):
        ts = "11212121.12121"
        channel = "channel"
        workspace_name = "workspace"
        expected_result = "https://workspace.slack.com/archives/channel/p1121212112121"
        assert SlackUtils.get_request_link(ts, channel, workspace_name) == expected_result

    @pytest.mark.parametrize(
        "filename",
        {
            "01_message_closed.json",
            "02_message_closed.json",
        },
    )
    def test_message_closed_result_close_example(self, filename, channel_properties):
        test_directory = Path(ROOT_DIR + "/test_message_closed")
        with open(test_directory / filename, "r") as test_message_file:
            assert SlackUtils.message_closed(json.load(test_message_file), channel_properties.completion_reactions)

    @pytest.mark.parametrize(
        "filename",
        {
            "03_message_opened.json",
            "04_message_opened.json",
            "05_message_opened.json",
        },
    )
    def test_message_closed_result_still_open_example(self, filename, channel_properties):
        test_directory = Path(ROOT_DIR + "/test_message_closed")
        with open(test_directory / filename, "r") as test_message_file:
            assert (
                SlackUtils.message_closed(json.load(test_message_file), channel_properties.completion_reactions)
                is False
            )

    def test_remove_main_message(self, channel_id, event_ts):
        event: Dict = {"channel": channel_id, "message": {"ts": event_ts}}
        with patch.object(Request, "remove_request", return_value=None) as test:
            SlackUtils.remove_main_message(event)
            test.assert_called_with(channel_id=channel_id, event_ts=event_ts)
