from typing import Dict

from slack import WebClient

from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import MessageType
from src.code.model.schemas import ChannelProperties
from src.code.utils.slack_event_type import SlackEventType
from src.code.utils.slack_main_request import SlackMainRequest
from src.code.utils.slack_reaction_utils import SlackReactionUtils
from src.code.utils.slack_thread_message import SlackThreadMessage
from src.code.utils.slack_utils import SlackUtils
from src.code.utils.slack_webclient import SlackWebclient

logger = create_logger(__name__)


class CustomEventAdapter:
    @staticmethod
    def message(payload: Dict, client: WebClient):
        event: Dict = SlackUtils.get_event(payload)
        user: str = SlackUtils.get_user(event)
        if user in [SlackWebclient.get_bot_id(client)]:
            return
        elif user in ["USLACKBOT"]:
            if SlackEventType(event).get_event_type() == MessageType.MAIN_REMOVE:
                SlackUtils.remove_main_message(event)
            return
        channel_properties: ChannelProperties = ControlPanel().get_channel_properties_by_channel_id(
            SlackUtils.get_channel_id(event)
        )
        logger.info("%s user is creating new message group: %s", user, SlackEventType(event).get_event_group())
        event_type: MessageType = SlackEventType(event).get_event_type()
        if SlackUtils.is_main_message_event(event_type):
            SlackMainRequest().deal_with_main_message(
                client=client, event=event, event_type=event_type, channel_properties=channel_properties
            )
        else:
            SlackThreadMessage.deal_with_thread_message(event=event, event_type=event_type)

    @staticmethod
    def add_reaction_to_request(payload: Dict, client: WebClient):
        event = payload.get("event", {})
        user = SlackUtils.get_user(event)
        if user in {SlackWebclient.get_bot_id(client), "USLACKBOT"}:
            return
        channel_properties = ControlPanel().get_channel_properties_by_channel_id(SlackUtils.get_channel_id(event))
        logger.info("%s user is adding new reaction", event.get("user"))
        if SlackReactionUtils.is_reaction_on_main_message(event):
            SlackReactionUtils.add_start_work_reaction_to_request(event, channel_properties)
            if SlackReactionUtils.is_reaction_in_desired_collections(event, channel_properties):
                SlackReactionUtils.complete_request(event, channel_properties.completion_reactions)
                SlackReactionUtils.add_reaction_to_request_types(event, channel_properties)

    @staticmethod
    def remove_reaction_from_request(payload: Dict, client: WebClient):
        event = payload.get("event", {})
        user = SlackUtils.get_user(event)
        if user in {SlackWebclient.get_bot_id(client), "USLACKBOT"}:
            return
        channel_properties = ControlPanel().get_channel_properties_by_channel_id(SlackUtils.get_channel_id(event))
        if SlackReactionUtils.is_reaction_in_desired_collections(
            event, channel_properties
        ) and SlackReactionUtils.is_reaction_on_main_message(event):
            SlackReactionUtils.remove_completion_reaction(event, channel_properties.completion_reactions)
            SlackReactionUtils.remove_reaction_from_request_types(event, channel_properties)
