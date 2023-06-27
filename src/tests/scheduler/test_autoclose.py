import datetime
from unittest.mock import patch

from slack import WebClient
from slack.web.slack_response import SlackResponse

from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import AutocloseStatus
from src.code.model.request import Request
from src.code.scheduler.autoclose import Autoclose
from src.code.utils.slack_webclient import SlackWebclient


class TestAutoclose:
    def test_close_idle_result_reminder_threads_without_thread(
        self, web_client, cp, conversations_history_response, reminder_message_block
    ):
        history_response: SlackResponse = conversations_history_response("request_reminder_without_thread.json")
        current_time = datetime.datetime.now()
        event_ts = (current_time - datetime.timedelta(days=2)).timestamp()
        history_response["messages"][0]["ts"] = event_ts
        history_response["messages"][0]["thread_ts"] = event_ts
        with patch.object(ControlPanel, "get_all_active_control_panels", return_value=[cp]):
            with patch.object(WebClient, "conversations_history", return_value=history_response):
                with patch.object(SlackWebclient, "send_post_message_to_thread", return_value=None) as patched_send:
                    with patch.object(Request, "change_autoclose_status", return_value=None) as patched_request:
                        Autoclose.close_idle_threads(web_client)
                        patched_send.assert_called_with(
                            web_client, cp.slack_channel_id, event_ts, reminder_message_block
                        )
                        patched_request.assert_called_with(cp.slack_channel_id, event_ts, AutocloseStatus.REMINDER)

    def test_close_idle_result_reminder_threads_with_thread(
        self, web_client, cp, conversations_history_response, conversations_replies_response, reminder_message_block
    ):
        # tuning main message
        history_response: SlackResponse = conversations_history_response("request_reminder_with_thread.json")
        current_time = datetime.datetime.now()
        event_ts = (current_time - datetime.timedelta(days=2)).timestamp()
        history_response["messages"][0]["ts"] = event_ts
        history_response["messages"][0]["thread_ts"] = event_ts
        history_response["messages"][0]["latest_reply"] = (current_time - datetime.timedelta(hours=14)).timestamp()
        # tuning reply message
        reply_response: SlackResponse = conversations_replies_response("reply_reminder.json")
        with patch.object(ControlPanel, "get_all_active_control_panels", return_value=[cp]):
            with patch.object(WebClient, "conversations_history", return_value=history_response):
                with patch.object(WebClient, "conversations_replies", return_value=reply_response):
                    with patch.object(SlackWebclient, "send_post_message_to_thread", return_value=None) as patched_send:
                        with patch.object(Request, "change_autoclose_status", return_value=None) as patched_request:
                            Autoclose.close_idle_threads(web_client)
                            patched_send.assert_called_with(
                                web_client, cp.slack_channel_id, event_ts, reminder_message_block
                            )
                            patched_request.assert_called_with(cp.slack_channel_id, event_ts, AutocloseStatus.REMINDER)

    def test_close_idle_result_closed_event(
        self, web_client, cp, conversations_history_response, conversations_replies_response, close_message_block
    ):
        history_response: SlackResponse = conversations_history_response("close_event.json")
        current_time = datetime.datetime.now()
        event_ts = (current_time - datetime.timedelta(days=2)).timestamp()
        history_response["messages"][0]["ts"] = event_ts
        history_response["messages"][0]["thread_ts"] = event_ts
        history_response["messages"][0]["latest_reply"] = (current_time - datetime.timedelta(hours=25)).timestamp()
        # tuning reply message
        reply_response: SlackResponse = conversations_replies_response("reply_close.json")
        with patch.object(ControlPanel, "get_all_active_control_panels", return_value=[cp]):
            with patch.object(WebClient, "conversations_history", return_value=history_response):
                with patch.object(WebClient, "conversations_replies", return_value=reply_response):
                    with patch.object(WebClient, "reactions_add", return_value=None) as patched_adding_reaction:
                        with patch.object(
                            SlackWebclient, "send_post_message_to_thread", return_value=None
                        ) as patched_send:
                            with patch.object(Request, "close_request", return_value=None) as patched_close:
                                with patch.object(
                                    Request, "change_autoclose_status", return_value=None
                                ) as patched_request:
                                    Autoclose.close_idle_threads(web_client)
                                    patched_adding_reaction.assert_called_with(
                                        channel=cp.slack_channel_id, name="white_check_mark", timestamp=event_ts
                                    )
                                    patched_send.assert_called_with(
                                        web_client, cp.slack_channel_id, event_ts, close_message_block
                                    )
                                    patched_close.assert_called()
                                    patched_request.assert_called_with(
                                        cp.slack_channel_id, event_ts, AutocloseStatus.CLOSED
                                    )

    def test_get_idle_thread_timestamps(self, channel_properties):
        channel_properties.close_idle_threads.scan_limit_days = 30
        cur_time = datetime.datetime.now()
        idle_thread_properties = Autoclose()._get_idle_thread_timestamps(
            channel_properties.close_idle_threads, cur_time
        )
        assert cur_time - datetime.timedelta(
            days=channel_properties.close_idle_threads.scan_limit_days
        ) == datetime.datetime.fromtimestamp(idle_thread_properties["time_filter"])
        assert datetime.datetime.fromtimestamp(idle_thread_properties["close_before"])
        assert datetime.datetime.fromtimestamp(idle_thread_properties["reminder_grace_period"])
        assert datetime.datetime.fromtimestamp(idle_thread_properties["close_grace_period"])
