import json
from typing import Any
from typing import Dict

from src.code.logger import create_logger
from src.code.model.custom_enums import MessageGroup
from src.code.model.custom_enums import MessageType
from src.code.model.request import Request

logger = create_logger(__name__)


class SlackEventType:
    def __init__(self, event: Dict):
        self._event: Dict = event

    def get_event_type(self) -> MessageType:
        if self._event.get("type") == "message":
            # Test for new main message
            if self._event.get("subtype") is None:
                if self._event.get("thread_ts") is not None:
                    logger.info("Message type is: %s", MessageType.THREAD_NEW.value)
                    return MessageType.THREAD_NEW
                else:
                    logger.info("Message type is: %s", MessageType.MAIN_NEW.value)
                    return MessageType.MAIN_NEW

            # Test for new main file share
            if self._event.get("subtype") == "file_share":
                if self._event.get("thread_ts") is not None:
                    logger.info("Message type is: %s", MessageType.THREAD_NEW_FILE.value)
                    return MessageType.THREAD_NEW_FILE
                else:
                    logger.info("Message type is: %s", MessageType.MAIN_NEW.value)
                return MessageType.MAIN_NEW_FILE

            # Test for editing message - if true the main message exists
            if self._event.get("subtype") == "message_changed":
                record = Request().get_request(channel_id=self._event["channel"], event_ts=self._event["message"]["ts"])
                if record is not None:
                    if self._event["message"]["text"] == "This message was deleted.":
                        logger.info("Message type is: %s", MessageType.MAIN_REMOVE.value)
                        return MessageType.MAIN_REMOVE

                    else:
                        logger.info("Message type is: %s", MessageType.MAIN_EDIT.value)
                        return MessageType.MAIN_EDIT
                else:
                    logger.info("Message type is: %s", MessageType.THREAD_EDIT.value)
                    return MessageType.THREAD_EDIT
        elif self._event.get("type") == "reaction_added":
            logger.info("Message type is: %s", MessageType.REACTION_ADD.value)
            return MessageType.REACTION_ADD
        elif self._event.get("type") == "reaction_removed":
            logger.info("Message type is: %s", MessageType.REACTION_REMOVE.value)
            return MessageType.REACTION_REMOVE
        raise ValueError("Failed to find event type on event %s", json.dumps(self._event))

    def get_event_group(self) -> Any:
        if self._event.get("subtype") == "message_changed":
            return MessageGroup.EDIT.value
        return MessageGroup.NEW.value
