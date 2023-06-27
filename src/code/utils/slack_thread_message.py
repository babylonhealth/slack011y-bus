from typing import Dict

from src.code.logger import create_logger
from src.code.model.custom_enums import MessageType
from src.code.model.request import Request
from src.code.model.request import ThreadMessage
from src.code.utils.slack_utils import SlackUtils

logger = create_logger(__name__)


class SlackThreadMessage:
    # function for "message"
    @staticmethod
    def deal_with_thread_message(event: Dict, event_type: MessageType) -> None:
        try:
            channel_id: str = SlackUtils.get_channel_id(event)
            blocks, _, event_ts, author = SlackUtils.get_data_from_event(event)
            if event_type == MessageType.THREAD_EDIT:
                ThreadMessage().update_reply(event_ts=event_ts, blocks=blocks, channel_id=channel_id)
                # for now save only new message
            elif event_type in [MessageType.THREAD_NEW, MessageType.THREAD_NEW_FILE]:
                main_ts: str = SlackUtils.get_main_ts(event)
                record: Request = Request().get_request_or_throw_exception(channel_id=channel_id, event_ts=main_ts)
                ThreadMessage().add_reply(request=record, event_ts=event_ts, author_id=author, blocks=blocks)
                if SlackUtils.get_user(event) != record.requestor_id:
                    Request().start_work(record, main_ts)
        except Exception:
            logger.error("Thread message saving - error occurred for event: %s and client", event)
            raise Exception
