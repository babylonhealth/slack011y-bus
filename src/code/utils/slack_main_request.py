from typing import Dict

from slack import WebClient

from src.code.analytics.emoji import Emoji
from src.code.analytics.form_answers_collector_new_form import FormQuestionCollectorNewForm
from src.code.const import SLACK_WORKSPACE_NAME
from src.code.dto.dto import NewRecordDto
from src.code.logger import create_logger
from src.code.model.custom_enums import MessageType
from src.code.model.custom_enums import QuestionState
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import Types
from src.code.utils.slack_utils import SlackUtils
from src.code.utils.slack_webclient import SlackWebclient

logger = create_logger(__name__)


class SlackMainRequest:
    @classmethod
    def deal_with_main_message(
        cls, client: WebClient, event: Dict, event_type: MessageType, channel_properties: ChannelProperties
    ):
        try:
            channel_id: str = SlackUtils.get_channel_id(event)
            blocks, elements, ts, requestor_id = SlackUtils.get_data_from_event(event)
            channel_name: str = SlackUtils.get_channel_name(channel_id)
            request_link: str = SlackUtils.get_request_link(ts, channel_id, SLACK_WORKSPACE_NAME)
            requestor_info: Dict = SlackWebclient.get_requestor_info(client, requestor_id)
            new_record: NewRecordDto = NewRecordDto(
                channel_name=channel_name,
                channel_id=channel_id,
                requestor_id=requestor_id,
                requestor_email=SlackWebclient.get_requestor_email(requestor_info, requestor_id),
                requestor_team_id=SlackWebclient.get_requestor_team_id(requestor_info, requestor_id),
                blocks=blocks,
                request_types_from_message=SlackUtils.get_request_types_from_elements(elements, channel_properties),
                event_ts=ts,
                request_link=request_link,
            )
            Request().update_or_register_new_record(new_record)
            logger.info("Message for channel %s with link %s has been saved", channel_name, request_link)
            if not channel_properties.features.types.enabled:
                logger.info("Emoji feature is not enabled.")
                logger.info("Not checking if message has emoji and not sending missing emoji response.")
                return
            emoji = Emoji(event, channel_properties.types.emojis)
            if (
                not emoji.is_cloud_emoji_selected()
                and event_type != MessageType.MAIN_EDIT
                and channel_properties.types.not_selected_response
            ):
                response_blocks = cls.generate_not_selected_response(channel_properties.types)
                SlackWebclient.send_post_message_to_thread(
                    client=client, channel=channel_name, ts=ts, blocks=response_blocks
                )
            if channel_properties.features.question_form.enabled:
                if emoji.is_trigger_in_the_event(channel_properties.question_forms.triggers):
                    FormQuestionCollectorNewForm().create_question_form(
                        state=QuestionState.NEW, channel_name=channel_name, ts=ts
                    )
            else:
                logger.info("Form question feature is not enabled.")
        except Exception:
            logger.error("Main message saving - error occurred for event: %s and client", event, client)
            raise Exception

    @classmethod
    def generate_not_selected_response(cls, types: Types) -> list[dict]:
        block = [{"type": "section", "text": {"type": "mrkdwn", "text": types.not_selected_response}}]
        emoji_block: dict = {"type": "section", "text": {"type": "mrkdwn", "text": ""}}
        response_text = ""
        for emoji in types.emojis:
            response_text += (
                f"• :{emoji}: {types.emojis[emoji]['meaning'] if 'meaning' in types.emojis[emoji] else ''}\n"
            )
        emoji_block["text"]["text"] = response_text
        block.append(emoji_block)
        return block
