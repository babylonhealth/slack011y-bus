from typing import Dict
from typing import List
from typing import Optional

from src.code.analytics.form_answers_collector_new_form import FormQuestionCollectorNewForm
from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import QuestionState
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.utils.slack_utils import SlackUtils

logger = create_logger(__name__)


class SlackReactionUtils:
    @classmethod
    def is_reaction_on_main_message(cls, event: Dict) -> bool:
        if event["type"] != "reaction_added" and event["type"] != "reaction_removed":
            raise AttributeError("Event payload has no type 'reaction_added' or 'reaction_removed'")
        cls._required_reaction_json_attributes_are_not_none(event)
        event_ts: str = event["item"]["ts"]
        channel_id: str = event["item"]["channel"]
        if Request().get_request(channel_id, event_ts) is None:
            return False
        logger.info("Reaction for channel_id %s and event_ts %s is for main message", channel_id, event_ts)
        return True

    # function for "reaction_added"
    @staticmethod
    def add_start_work_reaction_to_request(event: Dict, channel_properties: ChannelProperties) -> None:
        if event.get("type") == "reaction_added":
            logger.info("Checking if reaction is part of start work reactions.")
            if event.get("reaction") in channel_properties.start_work_reactions:
                logger.info("Reaction is part of start work reactions")
                main_ts: str = SlackUtils.get_main_ts(event)
                channel_id: str = SlackUtils.get_channel_id(event)
                record: Request = Request().get_request(channel_id, main_ts)
                if record is not None:
                    if SlackUtils.get_user(event) != record.requestor_id:
                        Request().start_work(record=record, event_ts=main_ts)

    @staticmethod
    def is_reaction_in_desired_collections(event: Dict, channel_properties: ChannelProperties) -> bool:
        types_dict: dict = channel_properties.types.emojis
        types_dict_alias: list[str] = list(set([value["alias"] for value in types_dict.values()]))
        emoji_reaction: Optional[str] = event.get("reaction")
        if (
            emoji_reaction is not None
            and channel_properties.completion_reactions.count(emoji_reaction) == 0
            and emoji_reaction not in list(types_dict.keys())
            and emoji_reaction not in list(types_dict_alias)
        ):
            logger.info("Reaction: '%s' is not in desired collection", emoji_reaction)
            return False
        logger.info("Reaction: '%s' is in desired collection", emoji_reaction)
        return True

    # function for "reaction_added"
    @staticmethod
    def complete_request(event: Dict, completion_reactions: List) -> None:
        if event.get("type") == "reaction_added":
            if completion_reactions.count(event.get("reaction")) > 0:
                item: Dict = event["item"]
                Request().close_request(
                    channel_id=item["channel"],
                    request_ts=item["ts"],
                    reaction_ts=event["event_ts"],
                    reaction=event["reaction"],
                )

    # function for "reaction_added"
    @classmethod
    def add_reaction_to_request_types(cls, event: Dict, channel_properties: ChannelProperties) -> None:
        if event.get("type") == "reaction_added":
            reaction: Optional[str] = cls._get_cloud_reaction(event, channel_properties.types.emojis)
            if reaction:
                request_ts = event["item"]["ts"]
                channel_id = event["item"]["channel"]
                Request().add_reaction_to_request_types(channel_id=channel_id, request_ts=request_ts, reaction=reaction)
                if cls._is_reaction_question_form_trigger(event, channel_properties.question_forms.triggers):
                    FormQuestionCollectorNewForm().create_question_form(
                        state=QuestionState.NEW, channel_name=ControlPanel().get_channel_name(channel_id), ts=request_ts
                    )

    # function for "reaction_removed"
    @staticmethod
    def remove_completion_reaction(event: Dict, completion_reactions: List) -> None:
        if event.get("type") == "reaction_removed":
            if completion_reactions.count(event.get("reaction")) > 0:
                item = event.get("item")
                if item is not None:
                    Request().remove_completion_reaction(
                        channel_id=item.get("channel"), request_ts=item.get("ts"), reaction=event["reaction"]
                    )

    @classmethod
    def remove_reaction_from_request_types(cls, event: Dict, channel_properties: ChannelProperties) -> None:
        if event.get("type") == "reaction_removed":
            reaction = cls._get_cloud_reaction(event, channel_properties.types.emojis)
            if reaction:
                request_ts = event["item"]["ts"]
                channel_id = event["item"]["channel"]
                Request().remove_reaction_from_request_types(
                    channel_id=channel_id, request_ts=request_ts, reaction=reaction
                )

    @classmethod
    def _required_reaction_json_attributes_are_not_none(cls, event: Dict) -> None:
        if (
            event.get("type") is None
            or event.get("reaction") is None
            or event.get("item") is None
            or event.get("item", {}).get("ts") is None
            or event.get("item", {}).get("channel") is None
        ):
            raise AttributeError("Required reaction attributes not provided")
        pass

    @classmethod
    def _get_cloud_reaction(cls, event: Dict, types_dict: Dict) -> Optional[str]:
        if event.get("reaction") in list(types_dict.keys()):
            return event.get("reaction")
        else:
            list_of_aliases = [
                alias
                for alias, emoji in types_dict.items()
                if event.get("reaction") in [val["alias"] for val in types_dict.values()]
                and emoji["alias"] == event.get("reaction")
            ]
            if list_of_aliases:
                return list_of_aliases[0]
            else:
                return None

    @classmethod
    def _is_reaction_question_form_trigger(cls, event: dict, trigger_list: List[str]) -> bool:
        emoji_reaction = event.get("reaction")
        if len(trigger_list) == 0 and emoji_reaction not in list(trigger_list):
            logger.info("Reaction: '%s' is not question form trigger", emoji_reaction)
            return False
        logger.info("Reaction: '%s' is in question form trigger", emoji_reaction)
        return True
