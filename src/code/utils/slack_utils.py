import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import MessageGroup
from src.code.model.custom_enums import MessageType
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.utils.slack_event_type import SlackEventType

logger = create_logger(__name__)


class SlackUtils:
    @staticmethod
    def get_event(payload: Dict) -> Dict:
        event = payload.get("event")
        if event is None:
            raise KeyError("Event not found in payload:", payload)
        return event

    @staticmethod
    def get_user(event: Dict[str, Dict]) -> str:
        try:
            return (
                event["message"]["user"]
                if SlackEventType(event).get_event_group() == MessageGroup.EDIT.value
                else event["user"]
            )
        except KeyError:
            raise KeyError("User not found in event:", event)

    @staticmethod
    def is_main_message_event(event_type: MessageType) -> bool:
        return (
            True
            if event_type
            in [MessageType.MAIN_NEW, MessageType.MAIN_NEW_FILE, MessageType.MAIN_EDIT, MessageType.MAIN_REMOVE]
            else False
        )

    @staticmethod
    def get_channel_id(event: Dict) -> str:
        try:
            event_type: MessageType = SlackEventType(event).get_event_type()
            if event_type in [
                MessageType.MAIN_NEW,
                MessageType.MAIN_EDIT,
                MessageType.MAIN_NEW_FILE,
                MessageType.THREAD_NEW,
                MessageType.THREAD_EDIT,
                MessageType.THREAD_NEW_FILE,
                MessageType.MAIN_REMOVE,
            ]:
                return event["channel"]
            elif event_type in [MessageType.REACTION_ADD, MessageType.REACTION_REMOVE]:
                return event["item"]["channel"]
            else:
                raise ValueError("Failed to find channel id on event %s", json.dumps(event))
        except Exception:
            raise ValueError("Failed to find channel id on event %s", json.dumps(event))

    @staticmethod
    def get_main_ts(event: Dict) -> str:
        try:
            event_type: MessageType = SlackEventType(event).get_event_type()
            if event_type in [MessageType.MAIN_NEW, MessageType.MAIN_NEW_FILE]:
                return event["ts"]
            elif event_type in [MessageType.MAIN_EDIT, MessageType.THREAD_EDIT]:
                return event["message"]["ts"]
            elif event_type in [MessageType.THREAD_NEW, MessageType.THREAD_NEW_FILE]:
                return event["thread_ts"]
            elif event_type in [MessageType.REACTION_ADD, MessageType.REACTION_REMOVE]:
                return event["item"]["ts"]
            else:
                raise ValueError("Failed to find event type on event %s", json.dumps(event))
        except Exception:
            raise ValueError("Failed to find event ts on event %s", json.dumps(event))

    @staticmethod
    def get_channel_name(channel_id: str) -> str:
        return ControlPanel().get_channel_name(channel_id)

    @classmethod
    def get_data_from_event(cls, event: Dict) -> Tuple[Any, Optional[Any], Any, Any]:
        try:
            if event.get("subtype") == "message_changed":
                message = event["message"]
                blocks, elements = cls._try_to_get_blocks_elements(message)
                return blocks, elements, message["ts"], message["user"]
            else:
                blocks, elements = cls._try_to_get_blocks_elements(event)
                return blocks, elements, event["ts"], event["user"]
        except KeyError as e:
            logger.error(f"{e}: event = {event}")
            raise

    @staticmethod
    def get_request_types_from_elements(elements: Optional[List[Dict]], channel_properties: ChannelProperties) -> List:
        if elements is None:
            return []
        if not channel_properties.features.types.enabled:
            return []
        types_dict = channel_properties.types.emojis
        if not types_dict:
            return []
        aliases = [value["alias"] for value in types_dict.values()]
        from_keys = set(
            map(
                lambda d: d["name"],
                (filter(lambda x: x["type"] == "emoji" and x["name"] in types_dict.keys(), elements)),
            )
        )

        from_values = set(
            map(
                lambda d: [emoji for emoji, propeties in types_dict.items() if propeties["alias"] == d["name"]][0],
                (filter(lambda x: x["type"] == "emoji" and x["name"] in aliases, elements)),
            )
        )

        return list(from_keys.union(from_values))

    @staticmethod
    def get_request_link(ts: str, channel_id: str, workspace_name: str) -> str:
        ts_wo_dot = ts.replace(".", "")
        return f"https://{workspace_name}.slack.com/archives/{channel_id}/p{ts_wo_dot}"

    @staticmethod
    def message_closed(message: Dict, completion_reactions: List) -> bool:
        return (
            True
            if "reactions" in message
            and list(filter(lambda reaction: reaction["name"] in completion_reactions, message["reactions"]))
            else False
        )

    @staticmethod
    def remove_main_message(event: Dict) -> None:
        Request().remove_request(channel_id=event["channel"], event_ts=event["message"]["ts"])

    @classmethod
    def _try_to_get_blocks_elements(cls, data: Dict) -> Tuple[Any, Optional[Any]]:
        blocks = data.get("blocks")
        elements = None
        if blocks is not None:
            outer_elements = blocks[0]["elements"]
            elements = outer_elements[0]["elements"]
        return blocks, elements
