import json
import os
from typing import List
from unittest.mock import Mock

import pytest
from slack.web.slack_response import SlackResponse

from src.code.const import create_app
from src.code.scheduler.manager import SchedulerManager

app = create_app("src.tests.config.Config")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class MockedScheduler:
    add_job: Mock
    remove_all_jobs: Mock
    remove_job: Mock
    start: Mock
    shutdown: Mock

    def __init__(self):
        self.add_job = Mock()
        self.remove_all_jobs = Mock()
        self.remove_job = Mock()
        self.start = Mock()
        self.shutdown = Mock()
        self.app = app


class SchedulerManagerMock(SchedulerManager):
    def __init__(self):
        self.scheduler: MockedScheduler = MockedScheduler()


@pytest.fixture()
def mocked_scheduler_obj() -> SchedulerManagerMock:
    return SchedulerManagerMock()


@pytest.fixture()
def manager_mocked_obj() -> SchedulerManagerMock:
    return SchedulerManagerMock()


@pytest.fixture()
def conversations_history_response():
    def __add_history_response(file_name: str):
        with open(ROOT_DIR + "/data_for_testing/" + file_name) as data_f:
            return SlackResponse(
                client="",
                http_verb="",
                api_url="",
                req_args={},
                data=json.load(data_f),
                headers={},
                status_code=200,
                use_sync_aiohttp=True,
            )

    return __add_history_response


@pytest.fixture()
def conversations_replies_response():
    def __add_replies_response(file_name: str):
        with open(ROOT_DIR + "/data_for_testing/" + file_name) as data_f:
            return SlackResponse(
                client="",
                http_verb="",
                api_url="",
                req_args={},
                data=json.load(data_f),
                headers={},
                status_code=200,
                use_sync_aiohttp=True,
            )

    return __add_replies_response


@pytest.fixture()
def reminder_message_block() -> List:
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Hello. There has been no activity in this thread for a long time.\n"
                    "Please mark the main request as done if the case is resolved. "
                    "If not, please add a new reply to the thread."
                ),
            },
        }
    ]


@pytest.fixture()
def close_message_block() -> List:
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Hello. Because there is no activity in this thread, it has been marked as done.\n"
                    "If the case is still relevant, please create a new thread or raise a jira ticket."
                ),
            },
        }
    ]
