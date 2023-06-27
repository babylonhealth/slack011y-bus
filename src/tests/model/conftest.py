from datetime import datetime

import pytest

import src.tests.test_env  # noqa
from src.code.const import SLACK_DATETIME_FMT
from src.code.const import create_app
from src.code.db import db
from src.code.dto.dto import CompletionReactionDto
from src.code.dto.dto import RequestTypeDto
from src.code.model.block import Block
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import RequestStatusEnum
from src.code.model.request import Request
from src.code.model.request import ThreadMessage
from src.code.utils.utils import dto_to_json


@pytest.fixture
def db_setup():
    app = create_app("src.tests.config.Config")
    app.app_context().push()
    db.init_app(app)
    db.create_all()
    yield
    db.session.remove()
    db.drop_all()


@pytest.fixture
def test_record_added(channel_name, channel_id, requestor_id, event_ts, request_type_list):
    def __add_testing_record():
        channel = Request(
            slack_channel_name=channel_name,
            slack_channel_id=channel_id,
            requestor_id=requestor_id,
            request_status=RequestStatusEnum.NEW_RECORD.value,
            event_ts=event_ts,
            request_types=dto_to_json(RequestTypeDto(message=request_type_list, reaction=[])),
            completion_reactions=dto_to_json(CompletionReactionDto(completion_reactions=[])),
            form_answers={},
            blocks_id=1,
        )
        blocks = Block(id=1, blocks=None)
        db.session.add(channel)
        db.session.add(blocks)
        db.session.commit()

    return __add_testing_record


@pytest.fixture
def test_thread_added(channel_name, channel_id, requestor_id, event_ts, event_ts_thread, request_type_list):
    def __add_testing_channel_and_thread():
        request: Request = Request(
            slack_channel_name=channel_name,
            slack_channel_id=channel_id,
            requestor_id=requestor_id,
            request_status=RequestStatusEnum.NEW_RECORD.value,
            event_ts=event_ts,
            request_types=dto_to_json(RequestTypeDto(message=request_type_list, reaction=[])),
            completion_reactions=dto_to_json(CompletionReactionDto(completion_reactions=[])),
            blocks_id=1,
        )
        blocks = Block(id=1, blocks=None)
        thread_message: ThreadMessage = ThreadMessage(
            request_table_id=1,
            author_id=requestor_id,
            event_ts=event_ts_thread,
            blocks_id=2,
        )
        blocks_thread = Block(id=2, blocks=None)
        db.session.add(request)
        db.session.add(blocks)
        db.session.add(thread_message)
        db.session.add(blocks_thread)
        db.session.commit()

    return __add_testing_channel_and_thread


@pytest.fixture
def test_control_panel_added():
    def __add_testing_cp(cp: ControlPanel):
        db.session.add(cp)
        db.session.commit()

    return __add_testing_cp


@pytest.fixture
def requests_with_dates_added(channel_name, channel_id, requestor_id):
    def __add_requests_with_dates(date_list: list[str]):
        channels = db.session.query(Request).all()
        assert len(channels) == 0

        for date in date_list:
            channel = Request(
                slack_channel_name=channel_name,
                slack_channel_id=channel_id,
                requestor_id=requestor_id,
                request_status=RequestStatusEnum.NEW_RECORD.value,
                event_ts=datetime.strptime(date, SLACK_DATETIME_FMT).timestamp(),
            )
            db.session.add(channel)
            db.session.commit()
        channels = db.session.query(Request).all()
        assert len(channels) == len(date_list)

    return __add_requests_with_dates
