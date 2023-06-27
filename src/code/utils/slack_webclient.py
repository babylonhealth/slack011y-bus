from typing import Dict
from typing import List

from slack import WebClient
from slack.errors import SlackApiError

from src.code.logger import create_logger

logger = create_logger(__name__)


class SlackWebclient:
    @classmethod
    def get_requestor_info(cls, client: WebClient, requestor_id: str):
        try:
            requestor_info = client.users_info(user=requestor_id)
            logger.debug("Requestor info %s for requestor id %s", requestor_info, requestor_id)
            return requestor_info
        except SlackApiError as e:
            logger.error("Failed to get user info for requestor id %s:" + str(e), requestor_id)
            return {}

    @classmethod
    def get_requestor_email(cls, requestor_info: Dict, requestor_id: str) -> str:
        try:
            return requestor_info["user"]["profile"]["email"]
        except (AttributeError, KeyError):
            logger.error("Email for requestor id %s has not found", requestor_id)
            return "Unknown"

    @classmethod
    def get_requestor_team_id(cls, requestor_info: Dict, requestor_id: str) -> str:
        try:
            return requestor_info["user"]["team_id"]
        except (AttributeError, KeyError):
            logger.error("Email for requestor id %s has not found", requestor_id)
            return "Unknown"

    @staticmethod
    def send_post_message_as_main_message(client: WebClient, channel: str, blocks: dict) -> None:
        client.chat_postMessage(channel=channel, blocks=blocks)
        logger.info("Main message to channel %s has been sent successfully", channel)

    @classmethod
    def send_post_message_to_thread(cls, client: WebClient, channel: str, ts: str, blocks: List[Dict]) -> None:
        client.chat_postMessage(channel=channel, thread_ts=ts, blocks=blocks)
        logger.info("Thread message to channel %s and ts %s has been sent successfully", channel, ts)

    @staticmethod
    def modify_thread_message(client: WebClient, channel: str, ts: str, blocks: List[Dict]) -> None:
        client.chat_update(channel=channel, ts=ts, blocks=blocks)

    @classmethod
    def get_bot_id(cls, client: WebClient) -> str:
        return client.auth_test()["user_id"]
