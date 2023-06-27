from unittest.mock import patch

from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import MessageType
from src.code.model.schemas import ChannelProperties
from src.code.utils.custom_event_adapter import CustomEventAdapter
from src.code.utils.slack_event_type import SlackEventType
from src.code.utils.slack_main_request import SlackMainRequest
from src.code.utils.slack_reaction_utils import SlackReactionUtils
from src.code.utils.slack_thread_message import SlackThreadMessage
from src.code.utils.slack_utils import SlackUtils
from src.code.utils.slack_webclient import SlackWebclient

USER_1: str = "USER_1"
USER_2: str = "USER_2"


class TestCustomEventAdapter:
    def test_message_results_not_creating_new_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_1):
                    with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=None) as test:
                        CustomEventAdapter.message({}, web_client)
                        test.assert_not_called()

    def test_message_results_remove_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value="USLACKBOT"):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_1):
                    with patch.object(SlackEventType, "get_event_type", return_value=MessageType.MAIN_REMOVE):
                        with patch.object(SlackUtils, "remove_main_message", return_value=None) as test:
                            CustomEventAdapter.message({}, web_client)
                            test.assert_called()

    def test_message_results_not_creating_new_event_given_block_slackbot_message(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_1):
                    with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=None) as test:
                        CustomEventAdapter.message({}, web_client)
                        test.assert_not_called()

    def test_message_results_new_main_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_2):
                    with patch.object(SlackUtils, "get_channel_id", return_value="channel"):
                        with patch.object(
                            ControlPanel, "get_channel_properties_by_channel_id", return_value=ChannelProperties()
                        ):
                            with patch.object(SlackEventType, "get_event_type", return_value=MessageType.MAIN_NEW):
                                with patch.object(SlackUtils, "is_main_message_event", return_value=True):
                                    with patch.object(
                                        SlackMainRequest, "deal_with_main_message", return_value=True
                                    ) as test:
                                        CustomEventAdapter.message({}, web_client)
                                        test.assert_called()

    def test_message_results_new_thread_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_2):
                    with patch.object(SlackUtils, "get_channel_id", return_value="channel"):
                        with patch.object(
                            ControlPanel, "get_channel_properties_by_channel_id", return_value=ChannelProperties()
                        ):
                            with patch.object(SlackEventType, "get_event_type", return_value=MessageType.THREAD_NEW):
                                with patch.object(SlackUtils, "is_main_message_event", return_value=False):
                                    with patch.object(
                                        SlackThreadMessage, "deal_with_thread_message", return_value=True
                                    ) as test:
                                        CustomEventAdapter.message({}, web_client)
                                        test.assert_called()

    def test_add_reaction_to_request_results_not_creating_new_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_1):
                    with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=None) as test:
                        CustomEventAdapter.add_reaction_to_request({}, web_client)
                        test.assert_not_called()

    def test_add_reaction_to_request_results_new_thread_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_2):
                    with patch.object(SlackUtils, "get_channel_id", return_value="channel"):
                        with patch.object(
                            ControlPanel, "get_channel_properties_by_channel_id", return_value=ChannelProperties()
                        ):
                            with patch.object(SlackReactionUtils, "is_reaction_on_main_message", return_value=True):
                                with patch.object(
                                    SlackReactionUtils, "add_start_work_reaction_to_request", return_value=None
                                ):
                                    with patch.object(
                                        SlackReactionUtils, "is_reaction_in_desired_collections", return_value=True
                                    ):
                                        with patch.object(
                                            SlackReactionUtils, "complete_request", return_value=None
                                        ) as test_1:
                                            with patch.object(
                                                SlackReactionUtils, "add_reaction_to_request_types", return_value=None
                                            ) as test_2:
                                                CustomEventAdapter.add_reaction_to_request({}, web_client)
                                                test_1.assert_called()
                                                test_2.assert_called()

    def test_remove_reaction_from_request_results_not_removing_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_1):
                    with patch.object(ControlPanel, "get_channel_properties_by_channel_id", return_value=None) as test:
                        CustomEventAdapter.remove_reaction_from_request({}, web_client)
                        test.assert_not_called()

    def test_remove_reaction_from_request_results_removing_event(self, web_client):
        with patch.object(SlackUtils, "get_event", return_value={}):
            with patch.object(SlackUtils, "get_user", return_value=USER_1):
                with patch.object(SlackWebclient, "get_bot_id", return_value=USER_2):
                    with patch.object(SlackUtils, "get_channel_id", return_value="channel"):
                        with patch.object(
                            ControlPanel, "get_channel_properties_by_channel_id", return_value=ChannelProperties()
                        ):
                            with patch.object(SlackReactionUtils, "is_reaction_on_main_message", return_value=True):
                                with patch.object(
                                    SlackReactionUtils, "is_reaction_in_desired_collections", return_value=True
                                ):
                                    with patch.object(
                                        SlackReactionUtils, "remove_completion_reaction", return_value=None
                                    ) as test_1:
                                        with patch.object(
                                            SlackReactionUtils, "remove_reaction_from_request_types", return_value=None
                                        ) as test_2:
                                            CustomEventAdapter.remove_reaction_from_request({}, web_client)
                                            test_1.assert_called()
                                            test_2.assert_called()
