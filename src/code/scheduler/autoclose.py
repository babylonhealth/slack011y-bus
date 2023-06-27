import datetime
import time
from typing import Dict
from typing import List

from slack import WebClient
from slack.errors import SlackApiError

from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import AutocloseStatus
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import CloseIdleThreads
from src.code.model.schemas import channel_properties_schema
from src.code.utils.slack_utils import SlackUtils
from src.code.utils.slack_webclient import SlackWebclient

logger = create_logger(__name__)


class Autoclose:
    @classmethod
    def close_idle_threads(cls, client: WebClient) -> None:
        logger.info("Starting scan of idle threads.")
        current_time = datetime.datetime.now()
        for entry in ControlPanel().get_all_active_control_panels():
            try:
                logger.info(
                    "Checking channel '%s', channel_id '%s', for idle threads",
                    entry.slack_channel_name,
                    entry.slack_channel_id,
                )
                message = None
                cls._analyse_channel(current_time, client, entry)
            except Exception:
                logger.exception("There were problems while handling channel '%s'.", entry.slack_channel_name)
                logger.error("checked message: %s", str(message) if message else "None")
                logger.error("The channel was skipped.")
        logger.info("Ending scan of idle threads")

    @classmethod
    def _analyse_channel(cls, current_time, client, entry):
        channel_properties: ChannelProperties = channel_properties_schema.load(data=entry.channel_properties)
        if all([channel_properties.completion_reactions, channel_properties.close_idle_threads]):
            idle_thread_timestamps = cls._get_idle_thread_timestamps(
                channel_properties.close_idle_threads, current_time
            )
            messages: List = cls._get_all_messages_from_channel(
                client, channel_id=entry.slack_channel_id, time_filter=idle_thread_timestamps["time_filter"]
            )
            logger.info("%s of items for analyzing", str(len(messages)))
            for message in messages:
                if "thread_ts" in message and message["ts"] == message["thread_ts"] and "bot_id" not in message:
                    if SlackUtils.message_closed(message, completion_reactions=channel_properties.completion_reactions):
                        continue
                    logger.debug("Message ts: %s", str(message["ts"]))
                    logger.debug("Idle thread timestamps close_before: %s", str(idle_thread_timestamps["close_before"]))
                    if float(message["ts"]) < idle_thread_timestamps["close_before"]:
                        logger.debug("Unclosed message ts: %s", str(message["ts"]))
                        if "latest_reply" not in message:  # message is not a thread or is main message of thread
                            logger.debug("Latest_reply not in message for ts: %s", str(message["ts"]))
                            cls._close_thread_message(
                                client, entry, message, channel_properties.close_idle_threads.reminder_message
                            )
                        else:
                            cls._proceed_with_latest_reply(
                                entry, client, message, channel_properties, idle_thread_timestamps
                            )
        else:
            logger.info("Channel has close_idle_threads or completion_reactions disabled. Skipping.")

    @classmethod
    def _proceed_with_latest_reply(
        cls,
        entry: ControlPanel,
        client: WebClient,
        message: Dict,
        channel_properties: ChannelProperties,
        idle_thread_timestamps: Dict,
    ):
        latest_reply = cls._get_latest_reply(message["ts"], message["latest_reply"], entry.slack_channel_id, client)
        user = latest_reply["user"] if "user" in latest_reply else latest_reply["bot_id"]
        latest_reply_float = float(message["latest_reply"])
        logger.debug(
            "Latest_reply in message for ts: %s, for user: %s, latest_reply_float: %s, reminder_grace_period: %s",
            str(message["ts"]),
            user,
            str(latest_reply_float),
            idle_thread_timestamps["reminder_grace_period"],
        )
        if (
            channel_properties.close_idle_threads.reminder_message != latest_reply["blocks"][0]["text"]["text"]
            and latest_reply_float < idle_thread_timestamps["reminder_grace_period"]
        ):
            cls._close_thread_message(client, entry, message, channel_properties.close_idle_threads.reminder_message)
        elif (
            # This should be improved
            channel_properties.close_idle_threads.reminder_message == latest_reply["blocks"][0]["text"]["text"]
            and latest_reply_float < idle_thread_timestamps["close_grace_period"]
        ):
            cls._close_thread(
                message["ts"],
                entry.slack_channel_id,
                client,
                channel_properties.completion_reactions,
                [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": channel_properties.close_idle_threads.close_message},
                    }
                ],
            )

    @classmethod
    def _get_idle_thread_timestamps(
        cls, close_idle_threads_conf: CloseIdleThreads, point_in_time: datetime.datetime
    ) -> Dict:
        idle_thread_timestamps = {}
        logger.debug(
            (
                "scan_limit_days '%d', close_after_hours '%d', reminder_grace_period_hours '%d',"
                " close_grace_period_hours '%d'"
            ),
            close_idle_threads_conf.scan_limit_days,
            close_idle_threads_conf.close_after_creation_hours,
            close_idle_threads_conf.reminder_grace_period_hours,
            close_idle_threads_conf.close_grace_period_hours,
        )
        idle_thread_timestamps["time_filter"] = (
            point_in_time - datetime.timedelta(days=close_idle_threads_conf.scan_limit_days)
        ).timestamp()
        idle_thread_timestamps["close_before"] = (
            point_in_time - datetime.timedelta(hours=close_idle_threads_conf.close_after_creation_hours)
        ).timestamp()
        idle_thread_timestamps["reminder_grace_period"] = (
            point_in_time - datetime.timedelta(hours=close_idle_threads_conf.reminder_grace_period_hours)
        ).timestamp()
        idle_thread_timestamps["close_grace_period"] = (
            point_in_time - datetime.timedelta(hours=close_idle_threads_conf.close_grace_period_hours)
        ).timestamp()
        logger.debug(
            "time_filter '%d', close_before '%d', reminder_grace_period '%d', close_grace_period '%d'",
            idle_thread_timestamps["time_filter"],
            idle_thread_timestamps["close_before"],
            idle_thread_timestamps["reminder_grace_period"],
            idle_thread_timestamps["close_grace_period"],
        )
        logger.debug("Converted from timestamps:")
        logger.debug(
            "time_filter '%s', close_before '%s', reminder_grace_period '%s', close_grace_period '%s'",
            str(datetime.datetime.fromtimestamp(idle_thread_timestamps["time_filter"])),
            str(datetime.datetime.fromtimestamp(idle_thread_timestamps["close_before"])),
            str(datetime.datetime.fromtimestamp(idle_thread_timestamps["reminder_grace_period"])),
            str(datetime.datetime.fromtimestamp(idle_thread_timestamps["close_grace_period"])),
        )
        return idle_thread_timestamps

    @classmethod
    def _close_thread(
        cls,
        ts: str,
        channel: str,
        client: WebClient,
        completion_reactions: List,
        close_message_slack_blocks: List[dict],
    ):
        logger.info("Closing thread %s", ts)
        client.reactions_add(channel=channel, name=completion_reactions[0], timestamp=ts)
        SlackWebclient.send_post_message_to_thread(client, channel, ts, close_message_slack_blocks)
        try:
            Request().close_request(
                channel_id=channel,
                request_ts=ts,
                reaction_ts=str(datetime.datetime.now().timestamp()),
                reaction=completion_reactions[0],
            )
            cls._send_close_message_flag_to_db(channel, ts)
        except Exception:
            logger.exception("Cannot add reaction to request in database")
        time.sleep(1)

    @classmethod
    def _get_all_messages_from_channel(cls, client: WebClient, channel_id: str, time_filter: float) -> List:
        time_filter_for_debug = str(datetime.datetime.fromtimestamp(time_filter))
        logger.debug("Grabbing messages for channel_id %s, time_filter %s", channel_id, time_filter_for_debug)
        try:
            page = client.conversations_history(
                channel=channel_id, oldest=str(time_filter), inclusive=True, limit=200
            ).data
            result: List = page["messages"]
            while page["has_more"]:
                logger.debug(
                    "Grabbing more messages for channel_id %s, time_filter %s, cursor %s",
                    channel_id,
                    time_filter_for_debug,
                    page["response_metadata"]["next_cursor"],
                )
                page = client.conversations_history(
                    channel=channel_id,
                    oldest=str(time_filter),
                    inclusive=True,
                    limit=200,
                    cursor=page["response_metadata"]["next_cursor"],
                ).data
                result.extend(page["messages"])
            return result
        except SlackApiError:
            logger.error("Error grabbing messages from channel %s", channel_id)
            raise

    @classmethod
    def _close_thread_message(cls, client: WebClient, entry: ControlPanel, message: Dict, message_string: str) -> None:
        logger.info("Sending reminder to main message %s", message["ts"])
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": message_string}}]
        SlackWebclient.send_post_message_to_thread(client, entry.slack_channel_id, message["ts"], blocks)
        cls._send_reminder_message_flag_to_db(entry.slack_channel_id, message["ts"])
        time.sleep(1)

    @classmethod
    def _get_latest_reply(cls, parent_ts: str, ts: str, channel: str, client: WebClient) -> Dict:
        try:
            # Slack always returns the main message as first message
            # Replies are sent later
            return (
                client.conversations_replies(channel=channel, ts=str(parent_ts), oldest=str(ts), inclusive=True)
                .data["messages"]
                .pop()
            )
        except SlackApiError:
            logger.error("Error grabbing reply %s from channel %s for thread %s", ts, channel, parent_ts)
            raise

    @classmethod
    def _send_reminder_message_flag_to_db(cls, channel_id: str, ts: str):
        Request().change_autoclose_status(channel_id, ts, AutocloseStatus.REMINDER)

    @classmethod
    def _send_close_message_flag_to_db(cls, channel_id: str, ts: str):
        Request().change_autoclose_status(channel_id, ts, AutocloseStatus.CLOSED)
