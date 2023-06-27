import os
from dataclasses import dataclass
from typing import Dict
from typing import Optional

import pytest

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass
class ChannelMock:
    slack_channel_name: Optional[str]
    slack_channel_id: Optional[str]
    blocks: Optional[dict]
    request_types: Optional[dict]
    request_link: Optional[str]
    event_ts: Optional[str]
    requestor_id: Optional[str]
    requestor_email: Optional[str]
    requestor_team_id: Optional[str]


@pytest.fixture()
def user_info_response(requestor_email, requestor_team_id) -> Dict:
    return {"user": {"profile": {"email": requestor_email}, "team_id": requestor_team_id}}


@pytest.fixture()
def slack_event_types_folder() -> str:
    return os.path.dirname(os.path.abspath(__file__)) + "/slack_event_types"


@pytest.fixture()
def example_channel_entry() -> ChannelMock:
    return ChannelMock(
        slack_channel_name="#test",
        slack_channel_id="BOGUS_CHANNEL_ID",
        blocks={},
        request_types={},
        request_link="https://link",
        event_ts="1212121.212121",
        requestor_id="some_id",
        requestor_email="TBD",
        requestor_team_id=None,
    )
