#!/usr/bin/env python3
import os
from typing import Dict
from typing import List
from unittest.mock import patch

import pytest

from src.code.model.request import Request
from src.code.utils.slack_reaction_utils import SlackReactionUtils

CHANNEL = "#cloud-helpbot"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["SERVICE_NAME"] = "foo"

REACTION_WITH_ALL_REQUIRED_ATTRIBUTES = {
    "type": "reaction_added",
    "reaction": "reaction",
    "item": {"channel": "channel", "ts": "ts"},
}


class TestSlackUtils:
    def test_is_reaction_on_main_message_results_false_given_type_is_wrong(self):
        data_list: List[Dict] = [{"type": "no_reaction_type"}]
        for data in data_list:
            with pytest.raises(AttributeError) as exc:
                SlackReactionUtils().is_reaction_on_main_message(data)
                assert str(exc.exception) == "Event payload has no type 'reaction_added' or 'reaction_removed'"

    def test_reaction_is_out_of_desired_collection_results_false_main_message_not_exists(self):
        with patch.object(Request, "get_request", return_value=None):
            event = {
                "type": "reaction_removed",
                "reaction": "sos",
                "item": {"type": "message", "channel": "BOGUS_CHANNEL_ID", "ts": "1650605980.394309"},
            }
            assert not SlackReactionUtils().is_reaction_on_main_message(event)

    def test_reaction_is_out_of_desired_collection_results_true_main_message_exists(self):
        with patch.object(Request, "get_request", return_value=Request()):
            event = {
                "type": "reaction_removed",
                "reaction": "sos",
                "item": {"type": "message", "channel": "BOGUS_CHANNEL_ID", "ts": "1650605980.394309"},
            }
            assert SlackReactionUtils().is_reaction_on_main_message(event)

    def test_add_start_work_reaction_to_request_results_reaction_added_and_status_changed(self, channel_properties):
        event: Dict = {
            "type": "reaction_added",
            "reaction": "eyes",
            "user": "1",
            "item": {"type": "message", "channel": "BOGUS_CHANNEL_ID", "ts": "1650605980.394309"},
        }
        origin_request_user: str = "2"
        with patch.object(Request, "get_request", return_value=Request(requestor_id=origin_request_user)):
            with patch.object(Request, "start_work") as start_work:
                SlackReactionUtils().add_start_work_reaction_to_request(event, channel_properties)
                start_work.assert_called_once()

    def test_add_start_work_reaction_to_request_results_reaction_hasnt_added_given_origin_user_cannot_start_work(
        self, channel_properties
    ):
        origin_request_user: str = "1"
        event: Dict = {
            "type": "reaction_added",
            "reaction": "eyes",
            "user": origin_request_user,
            "item": {"type": "message", "channel": "BOGUS_CHANNEL_ID", "ts": "1650605980.394309"},
        }
        with patch.object(Request, "get_request", return_value=Request(requestor_id=origin_request_user)):
            with patch.object(Request, "start_work") as start_work:
                SlackReactionUtils().add_start_work_reaction_to_request(event, channel_properties)
                start_work.assert_not_called()

    def test_reaction_is_out_of_desired_collection_results_true_given_emoji_in_desired_collection(
        self, channel_properties
    ):
        types_dict_keys = [{"reaction": key} for key in channel_properties.types.emojis.keys()]
        types_dict_values = [{"reaction": key["alias"]} for key in channel_properties.types.emojis.values()]
        data_list = [{"reaction": channel_properties.completion_reactions[0]}]
        for data in data_list + types_dict_keys + types_dict_values:
            assert SlackReactionUtils().is_reaction_in_desired_collections(data, channel_properties)

    def test_reaction_is_out_of_desired_collection_results_true_given_emoji_is_not_in_collection(
        self, channel_properties
    ):
        data_list = [{"reaction": "😀"}]
        for data in data_list:
            assert not SlackReactionUtils().is_reaction_in_desired_collections(data, channel_properties)

    def test_complete_request_results_close_request(self, channel_properties, channel_id, event_ts):
        event: Dict = {
            "type": "reaction_added",
            "reaction": channel_properties.completion_reactions[0],
            "event_ts": event_ts,
            "item": {"channel": channel_id, "ts": event_ts},
        }
        with patch.object(Request, "close_request", return_value=None) as test:
            SlackReactionUtils.complete_request(event, channel_properties.completion_reactions)
            test.assert_called_with(
                channel_id=channel_id,
                request_ts=event_ts,
                reaction_ts=event_ts,
                reaction=channel_properties.completion_reactions[0],
            )

    def test_add_reaction_to_request_types(self, channel_properties, channel_id, event_ts):
        reaction: str = list(channel_properties.types.emojis.keys())[0]
        event: Dict = {
            "type": "reaction_added",
            "reaction": reaction,
            "event_ts": event_ts,
            "item": {"channel": channel_id, "ts": event_ts},
        }
        with patch.object(Request, "add_reaction_to_request_types", return_value=None) as test:
            SlackReactionUtils.add_reaction_to_request_types(event, channel_properties)
            test.assert_called_with(channel_id=channel_id, request_ts=event_ts, reaction=reaction)

    def test_remove_completion_reaction(self, channel_properties, channel_id, event_ts):
        reaction: str = channel_properties.completion_reactions[0]
        event: Dict = {
            "type": "reaction_removed",
            "reaction": reaction,
            "event_ts": event_ts,
            "item": {"channel": channel_id, "ts": event_ts},
        }
        with patch.object(Request, "remove_completion_reaction", return_value=None) as test:
            SlackReactionUtils.remove_completion_reaction(event, channel_properties.completion_reactions)
            test.assert_called_with(channel_id=channel_id, request_ts=event_ts, reaction=reaction)

    def test_remove_reaction_from_request_types(self, channel_properties, channel_id, event_ts):
        reaction: str = list(channel_properties.types.emojis.keys())[0]
        event: Dict = {
            "type": "reaction_removed",
            "reaction": reaction,
            "event_ts": event_ts,
            "item": {"channel": channel_id, "ts": event_ts},
        }
        with patch.object(Request, "remove_reaction_from_request_types", return_value=None) as test:
            SlackReactionUtils.remove_reaction_from_request_types(event, channel_properties)
            test.assert_called_with(channel_id=channel_id, request_ts=event_ts, reaction=reaction)

    def test_reaction_json_attribute_is_none_results_true_given_attribute_is_missing(self):
        data_list: List[Dict] = [
            {},
            {"type": "no_reaction_type"},
            {"type": "no_reaction_type", "reaction": "reaction"},
            {"type": "no_reaction_type", "reaction": "reaction", "item": {}},
            {"type": "no_reaction_type", "reaction": "reaction", "item": {"ts": "ts"}},
            {"type": "no_reaction_type", "reaction": "reaction", "item": {"channel": "channel"}},
            {"type": "no_reaction_type", "item": {"ts": "ts", "channel": "channel"}},
        ]
        for data in data_list:
            with pytest.raises(AttributeError) as exc:
                SlackReactionUtils()._required_reaction_json_attributes_are_not_none(data)
                assert str(exc.exception) == "Required reaction attributes not provided'"

    def test_reaction_json_attribute_is_none_results_true_given_all_attributes_provided(self):
        assert not SlackReactionUtils._required_reaction_json_attributes_are_not_none(
            REACTION_WITH_ALL_REQUIRED_ATTRIBUTES
        )

    def test_get_cloud_reaction_results_cloud_reaction(self, channel_properties):
        # reaction no change
        event_list = [{"reaction": key} for key in channel_properties.types.emojis.keys()]

        for event in event_list:
            assert event.get("reaction") == SlackReactionUtils()._get_cloud_reaction(
                event, channel_properties.types.emojis
            )

        # reaction changed to cloud emoji alias value -> key
        for key, value in channel_properties.types.emojis.items():
            assert key == SlackReactionUtils()._get_cloud_reaction(
                {"reaction": value["alias"]}, channel_properties.types.emojis
            )
