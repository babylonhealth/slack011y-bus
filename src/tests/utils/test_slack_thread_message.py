#!/usr/bin/env python3
import json
import os
from unittest.mock import patch

import pytest

from src.code.model.custom_enums import MessageType
from src.code.model.request import Request
from src.code.model.request import ThreadMessage
from src.code.utils.slack_thread_message import SlackThreadMessage
from src.code.utils.slack_utils import SlackUtils

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestSlackThreadMessage:
    def test_deal_with_new_thread_message_result_saving_data_wo_errors_given_edit_thread(
        self, slack_event_types_folder, channel_id, blocks, event_ts, author
    ):
        with open(os.path.join(slack_event_types_folder, "06_adding_new_thread.json")) as file:
            with patch.object(SlackUtils, "get_channel_id", return_value=channel_id):
                with patch.object(SlackUtils, "get_data_from_event", return_value=(blocks, None, event_ts, author)):
                    with patch.object(ThreadMessage, "update_reply", return_value=event_ts) as test1:
                        with patch.object(ThreadMessage, "add_reply", return_value=None) as test2:
                            with patch.object(Request, "start_work", return_value=None) as test3:
                                SlackThreadMessage().deal_with_thread_message(json.load(file), MessageType.THREAD_EDIT)
                                test1.assert_called()
                                test2.assert_not_called()
                                test3.assert_not_called()

    def test_deal_with_new_thread_message_result_saving_data_wo_errors_given_new_thread(
        self, slack_event_types_folder, channel_id, blocks, event_ts, author
    ):
        with open(os.path.join(slack_event_types_folder, "07_editing_thread.json")) as file:
            with patch.object(SlackUtils, "get_channel_id", return_value=channel_id):
                with patch.object(SlackUtils, "get_data_from_event", return_value=(blocks, None, event_ts, author)):
                    with patch.object(SlackUtils, "get_main_ts", return_value=event_ts):
                        with patch.object(Request, "get_request_or_throw_exception", return_value=Request()):
                            with patch.object(ThreadMessage, "add_reply", return_value=None) as test1:
                                with patch.object(Request, "start_work", return_value=None) as test2:
                                    SlackThreadMessage().deal_with_thread_message(
                                        json.load(file), MessageType.THREAD_NEW
                                    )
                                    test1.assert_called()
                                    test2.assert_called()

    def test_deal_with_new_thread_message_result_throw_exception(self):
        with pytest.raises(Exception):
            SlackThreadMessage().deal_with_thread_message({}, MessageType.THREAD_NEW)
