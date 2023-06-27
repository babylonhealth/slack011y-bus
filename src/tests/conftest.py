import os
from typing import Dict
from typing import List

import pytest
from slack import WebClient

import src.tests.test_env  # noqa
from src.code.model.control_panel import ChannelProperties
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import channel_properties_schema

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def web_client() -> WebClient:
    return WebClient()


@pytest.fixture()
def channel_properties_dict() -> Dict:
    return {
        "features": {
            "types": {"enabled": True},
            "start_work_reactions": {"enabled": True},
            "completion_reactions": {"enabled": True},
            "close_idle_threads": {"enabled": True},
        },
        "_close_idle_threads": {
            "reminder_message": (
                "Hello. There has been no activity in this thread for a long time.\nPlease mark the main request as"
                " done if the case is resolved. If not, please add a new reply to the thread."
            ),
            "close_message": (
                "Hello. Because there is no activity in this thread, it has been marked as done.\nIf the case is still"
                " relevant, please create a new thread or raise a jira ticket."
            ),
        },
        "_start_work_reactions": ["eyes"],
        "_types": {
            "emojis": {
                "cloud-incident": {"emoji": "🚨", "color": "#FF85FB", "alias": "rotating_light"},
                "cloud-bug": {"emoji": "🐛", "color": "#CC66FF", "alias": "bug"},
                "cloud-props": {"emoji": "🏆", "color": "#A938FF", "alias": "trophy"},
                "cloud-think": {"emoji": "🤔", "color": "#9B29FF", "alias": "thinking_face"},
                "cloud-help": {"emoji": "🆘", "color": "#9661FF", "alias": "sos"},
                "cloud-pr": {"emoji": "", "image": "cloud-pr.png", "color": "#6B77FF", "alias": "review-please"},
                "cloud-feature": {"emoji": "✋", "color": "#619BFF", "alias": "raised_hand"},
                "cloud-random": {"emoji": "🧠", "color": "#70B8FF", "alias": "brain"},
                "cloud-clarify": {"emoji": "❓", "color": "#70DBFF", "alias": "question"},
            },
            "not_selected_response": "You haven't selected a type.",
        },
        "_completion_reactions": ["white_check_mark"],
    }


@pytest.fixture()
def channel_name() -> str:
    return "cloud"


@pytest.fixture()
def channel_id() -> str:
    return "FSFJSDJFS"


@pytest.fixture()
def event_ts() -> str:
    return "1212121.12121"


@pytest.fixture()
def event_ts_thread() -> str:
    return "333321.12121"


@pytest.fixture()
def blocks() -> Dict[str, str]:
    return dict()


@pytest.fixture()
def request_link() -> str:
    return "request_link"


@pytest.fixture()
def author() -> str:
    return "author"


@pytest.fixture()
def requestor_team_id() -> str:
    return "requestor_team_id"


@pytest.fixture()
def request_type_list() -> List[str]:
    return ["cloud-help"]


@pytest.fixture()
def requestor_email() -> str:
    return "requestor_email"


@pytest.fixture()
def requestor_id() -> str:
    return "requestor_id"


@pytest.fixture()
def channel_properties(channel_properties_dict) -> ChannelProperties:
    return channel_properties_schema.load(data=channel_properties_dict)


@pytest.fixture()
def cp(channel_name, channel_id, event_ts, channel_properties_dict):
    return ControlPanel(
        slack_channel_name=channel_name,
        slack_channel_id=channel_id,
        creation_ts=event_ts,
        channel_properties=channel_properties_dict,
        form_questions={"questions": "question1"},
    )
