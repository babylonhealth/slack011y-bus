from src.code.logger import create_logger

logger = create_logger(__name__)


class Emoji:
    types_dict: dict
    types_dict_alias: set
    _blocks: list
    _ts: str

    def __init__(self, event, types_dict: dict):
        self._blocks = (
            event.get("message").get("blocks", [])
            if event.get("subtype") == "message_changed"
            else event.get("blocks", [])
        )
        self._ts = event.get("event_ts")
        self.types_dict = types_dict
        self.types_dict_alias = set([value["alias"] for value in self.types_dict.values()])

    def is_cloud_emoji_selected(self) -> bool:
        for block in self._blocks:
            for element in block.get("elements", []):
                for message in element.get("elements", []):
                    if message.get("type") == "emoji" and message.get("name") in set(self.types_dict.keys()).union(
                        self.types_dict_alias
                    ):
                        logger.info("Cloud emoji in the main message has been found")
                        return True
        logger.info("Cloud emoji in the main message has not been found")
        return False

    def is_trigger_in_the_event(self, trigger_list: list[str]) -> bool:
        for block in self._blocks:
            for element in block.get("elements", []):
                for message in element.get("elements", []):
                    if message.get("type") == "emoji" and message.get("name") in trigger_list:
                        return True
        return False
