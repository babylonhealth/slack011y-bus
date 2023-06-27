import time
from datetime import datetime
from typing import List
from unittest.mock import patch

import pytest

from src.code.const import SLACK_DATETIME_FMT
from src.code.db import db
from src.code.dto.dto import NewRecordDto
from src.code.model.block import Block
from src.code.model.custom_enums import AutocloseStatus
from src.code.model.custom_enums import RequestStatusEnum
from src.code.model.request import Request
from src.code.model.request import ThreadMessage


class TestIntegrationRequest:
    def test_get_request_or_throw_exception_results_request(self, db_setup, test_record_added, channel_id, event_ts):
        test_record_added()
        request = Request().get_request_or_throw_exception(channel_id, event_ts)
        assert request.slack_channel_id == channel_id

    def test_get_request_or_throw_exception_results_exception(self, channel_id, event_ts):
        with pytest.raises(ValueError, match=f"Request for {channel_id} and {event_ts} not found"):
            with patch.object(Request, "get_request", return_value=None):
                Request().get_request_or_throw_exception(channel_id, event_ts)

    def test_request_get_main_request(self, db_setup, test_record_added, channel_id, event_ts, blocks):
        # given - table has one record
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        saved_block: List[Block] = db.session.query(Block).all()
        assert len(requests) == 1
        assert len(saved_block) == 1
        # when the existing record has been modified
        Block().create_or_update_existing_blocks(blocks, 1)
        # then - record has been updated
        updated_request: Request = Request().get_request(channel_id, event_ts)
        assert updated_request.slack_channel_id == channel_id

    def test_update_or_register_new_record_results_add_new_given_new_record(
        self,
        db_setup,
        channel_name,
        channel_id,
        requestor_id,
        requestor_email,
        requestor_team_id,
        blocks,
        request_type_list,
        event_ts,
        request_link,
    ):
        # given - table request is empty
        saved_requests: List[Request] = db.session.query(Request).all()
        assert len(saved_requests) == 0
        saved_blocks: List[Block] = db.session.query(Block).all()
        assert len(saved_blocks) == 0
        new_record: NewRecordDto = NewRecordDto(
            channel_name=channel_name,
            channel_id=channel_id,
            requestor_id=requestor_id,
            requestor_email=requestor_email,
            requestor_team_id=requestor_team_id,
            blocks=blocks,
            request_types_from_message=request_type_list,
            event_ts=event_ts,
            request_link=request_link,
        )
        # when adding new record
        Request().update_or_register_new_record(new_record)
        updated_requests: List[Request] = db.session.query(Request).all()
        # then - new records has been added
        updated_blocks: List[Block] = db.session.query(Block).all()
        assert len(updated_requests) == 1
        assert len(updated_blocks) == 1
        assert updated_requests[0].slack_channel_name == channel_name
        assert updated_requests[0].slack_channel_id == channel_id
        assert updated_requests[0].requestor_id == requestor_id
        assert updated_requests[0].blocks_id == 1
        assert updated_blocks[0].blocks == blocks
        assert updated_requests[0].request_types == {"message": request_type_list, "reaction": []}

    def test_update_or_register_new_record_results_update_record_given_record_exists(
        self,
        db_setup,
        test_record_added,
        channel_name,
        channel_id,
        requestor_id,
        requestor_email,
        requestor_team_id,
        blocks,
        event_ts,
        request_link,
    ):
        # given - table has one record
        test_record_added()
        saved_requests: List[Request] = db.session.query(Request).all()
        saved_blocks: List[Block] = db.session.query(Block).all()
        assert len(saved_requests) == 1
        assert len(saved_blocks) == 1
        # when the existing record has been modified
        request_types_from_message = ["cloud-incident", "cloud-bug"]
        Request().update_or_register_new_record(
            NewRecordDto(
                channel_name,
                channel_id,
                requestor_id,
                requestor_email,
                requestor_team_id,
                blocks,
                request_types_from_message,
                event_ts,
                request_link,
            )
        )
        # then - record has been updated
        updated_requests: List[Request] = db.session.query(Request).all()
        updated_blocks: List[Block] = db.session.query(Block).all()
        assert len(updated_requests) == 1
        assert len(updated_blocks) == 1
        assert updated_requests[0].request_types.get("message") == request_types_from_message
        assert updated_requests[0].request_types.get("reaction") == []
        assert updated_blocks[0].blocks == blocks

    def test_remove_request(self, db_setup, test_record_added, event_ts, requestor_id, blocks):
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        ThreadMessage().add_reply(requests[0], event_ts, requestor_id, blocks)
        thread_messages: List[ThreadMessage] = db.session.query(ThreadMessage).all()
        saved_blocks: List[Block] = db.session.query(Block).all()
        assert len(requests) == 1
        assert len(thread_messages) == 1
        assert len(saved_blocks) == 2

        Request().remove_request(requests[0].slack_channel_id, event_ts)
        updated_requests: List[Request] = db.session.query(Request).all()
        updated_thread_messages = db.session.query(ThreadMessage).all()
        updated_blocks = db.session.query(Block).all()
        assert len(updated_requests) == 0
        assert len(updated_thread_messages) == 0
        assert len(updated_blocks) == 0

    def test_add_reply(self, db_setup, test_record_added, event_ts, requestor_id, blocks):
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        thread_messages: List[ThreadMessage] = db.session.query(ThreadMessage).all()
        saved_block: List[Block] = db.session.query(Block).all()
        assert len(requests) == 1
        assert len(thread_messages) == 0
        assert len(saved_block) == 1
        ThreadMessage().add_reply(requests[0], event_ts, requestor_id, blocks)
        updated_thread_messages: List[ThreadMessage] = db.session.query(ThreadMessage).all()
        updated_block: List[Block] = db.session.query(Block).order_by(Block.id).all()
        assert len(updated_thread_messages) == 1
        assert len(updated_block) == 2
        assert updated_block[-1].blocks == blocks

    def test_update_reply(self, db_setup, test_thread_added, channel_id, event_ts, event_ts_thread, blocks):
        test_thread_added()
        requests: List[Request] = db.session.query(Request).all()
        thread_messages: List[ThreadMessage] = db.session.query(ThreadMessage).all()
        saved_blocks: List[Block] = db.session.query(Block).all()
        assert len(requests) == 1
        assert len(thread_messages) == 1
        assert len(saved_blocks) == 2
        assert saved_blocks[-1].blocks is None
        ThreadMessage().update_reply(channel_id, event_ts_thread, blocks)
        updated_thread_messages: List[ThreadMessage] = db.session.query(ThreadMessage).all()
        updated_blocks: List[Block] = db.session.query(Block).order_by(Block.id).all()
        assert len(updated_thread_messages) == 1
        assert len(updated_blocks) == 2
        assert updated_blocks[-1].blocks == blocks

    def test_get_reply(self, db_setup, test_thread_added):
        test_thread_added()
        requests: List[Request] = db.session.query(Request).all()
        thread_message: List[ThreadMessage] = db.session.query(ThreadMessage).all()
        blocks = db.session.query(Block).all()
        assert len(requests) == 1
        assert len(thread_message) == 1
        assert len(blocks) == 2
        assert blocks[-1].blocks is None
        result = ThreadMessage()._get_reply(requests[0].slack_channel_id, thread_message[0].event_ts)
        assert result is not None

    def test_close_request_results_closed_request_given_main_record_exists(
        self, db_setup, test_record_added, channel_id, event_ts, cp
    ):
        # given - table has one record
        test_record_added()
        requests = db.session.query(Request).all()
        assert len(requests) == 1

        reaction_ts = str(time.time())

        # when record has been closed
        Request().close_request(channel_id, event_ts, reaction_ts, cp.channel_properties["_completion_reactions"][0])

        # then - record has been changed to close status
        updated_requests = db.session.query(Request).all()
        assert len(updated_requests) == 1
        assert (
            updated_requests[0].completion_reactions["completion_reactions"]
            == cp.channel_properties["_completion_reactions"]
        )

    def test_change_status(self, db_setup, event_ts, test_record_added, channel_id):
        # given one record
        test_record_added()
        request: Request = db.session.query(Request).first()

        assert request.autoclose_status is None

        # when
        Request().change_autoclose_status(channel_id, event_ts, AutocloseStatus.CLOSED)

        # then
        updated_channel = db.session.query(Request).first()
        assert updated_channel.autoclose_status == AutocloseStatus.CLOSED.value

    def test_get_form_answers(self, db_setup, test_record_added, channel_id, event_ts):
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        assert Request().get_form_answers(channel_id, event_ts) == requests[0].form_answers

    def test_save_form_answers_results_answer_is_added_given_record_has_no_answer(
        self, db_setup, test_record_added, channel_id, channel_name, event_ts
    ):
        # given - table has one record
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        assert len(requests) == 1

        # when record has been updated with new form_answers
        Request().init_form_answers(channel_id, event_ts)
        Request().save_form_answers(channel_id, event_ts, "new_question_id", ["Tool1", "Tool2"])

        updated_requests = db.session.query(Request).all()
        assert len(updated_requests) == 1
        assert updated_requests[0].form_answers["new_question_id"] == ["Tool1", "Tool2"]

    def test_save_form_answers_results_answer_is_updated_given_record_has_answer(
        self, db_setup, test_record_added, channel_id, event_ts
    ):
        # given - table has one record
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        assert len(requests) == 1
        Request().init_form_answers(channel_id, event_ts)
        Request().save_form_answers(channel_id, event_ts, "new_question_1", ["Tool1", "Tool2"])
        changed_requests = db.session.query(Request).all()
        assert changed_requests[0].form_answers["new_question_1"] == ["Tool1", "Tool2"]

        # when record has been updated with new form_answers
        Request().save_form_answers(channel_id, event_ts, "new_question_1", ["Tool3", "Tool4"])

        updated_requests = db.session.query(Request).all()
        assert len(updated_requests) == 1
        assert updated_requests[0].form_answers["new_question_1"] == ["Tool3", "Tool4"]

    def test_save_form_answers_results_answer_is_added_given_record_has_form_answer(
        self, db_setup, test_record_added, channel_id, event_ts
    ):
        # given - table has one record
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        assert len(requests) == 1
        Request().init_form_answers(channel_id, event_ts)
        Request().save_form_answers(channel_id, event_ts, "new_question_1", ["Tool1", "Tool2"])
        changed_requests: List[Request] = db.session.query(Request).all()
        assert changed_requests[0].form_answers["new_question_1"] == ["Tool1", "Tool2"]

        # when record has been updated with new form_answers and new id
        Request().save_form_answers(channel_id, event_ts, "new_question_2", ["Tool3", "Tool4"])

        updated_requests = db.session.query(Request).all()
        assert len(updated_requests) == 1
        assert updated_requests[0].form_answers["new_question_1"] == ["Tool1", "Tool2"]
        assert updated_requests[0].form_answers["new_question_2"] == ["Tool3", "Tool4"]

    def test_remove_all_form_answers_results_form_answers_are_removed(
        self, db_setup, test_record_added, channel_id, event_ts
    ):
        # given - table has one record
        test_record_added()
        requests: List[Request] = db.session.query(Request).all()
        assert len(requests) == 1
        Request().init_form_answers(channel_id, event_ts)
        Request().save_form_answers(channel_id, event_ts, "new_question_1", ["Tool1", "Tool2"])
        requests = db.session.query(Request).all()
        assert requests[0].form_answers["new_question_1"] == ["Tool1", "Tool2"]

        # when record has been updated with new form_answers and new id
        Request().remove_all_form_answers(
            channel_id,
            event_ts,
        )

        updated_requests = db.session.query(Request).all()
        assert len(updated_requests) == 1
        assert updated_requests[0].form_answers == {}

    def test_start_work(self, db_setup, test_record_added):
        # given one record
        test_record_added()
        request = db.session.query(Request).first()

        assert request.start_work_datatime_utc is None
        assert request.request_status == RequestStatusEnum.NEW_RECORD.value

        # when
        Request().start_work(request, str(time.time()))

        # then
        updated_request = db.session.query(Request).first()

        assert updated_request.start_work_datatime_utc is not None
        assert updated_request.request_status == RequestStatusEnum.WORKING.value

    def test_remove_completion_reaction_results_reopened_request_given_main_record_exists(
        self, db_setup, test_record_added, channel_id, event_ts, cp
    ):
        # given - table has one record
        test_record_added()
        requests = db.session.query(Request).all()
        assert len(requests) == 1

        reaction_ts = time.time()

        # when record has been closed
        Request().close_request(
            channel_id, event_ts, str(reaction_ts), cp.channel_properties["_completion_reactions"][0]
        )

        changed_requests = db.session.query(Request).all()
        assert len(changed_requests) == 1
        assert (
            changed_requests[0].completion_reactions["completion_reactions"]
            == cp.channel_properties["_completion_reactions"]
        )
        assert changed_requests[0].request_status == RequestStatusEnum.COMPLETED.value
        assert changed_requests[0].completion_datetime_utc is not None

        # and remove completion
        Request().remove_completion_reaction(channel_id, event_ts, cp.channel_properties["_completion_reactions"][0])

        # then - record has been changed to open status
        updated_channels = db.session.query(Request).all()
        assert len(updated_channels) == 1
        assert updated_channels[0].completion_reactions["completion_reactions"] == []
        assert updated_channels[0].request_status == RequestStatusEnum.WORKING.value
        assert updated_channels[0].completion_datetime_utc is None

    def test_add_reaction_to_request_types_results_record_has_new_emoji_given_main_record_exists(
        self, db_setup, test_record_added, channel_id, event_ts, cp, request_type_list
    ):
        # given - table has one record
        test_record_added()
        requests = db.session.query(Request).all()
        assert len(requests) == 1
        emoji_alias_list = list(set([value["alias"] for value in cp.channel_properties["_types"]["emojis"].values()]))
        reaction = emoji_alias_list[3]
        # when record has been modified
        Request().add_reaction_to_request_types(channel_id, event_ts, reaction)

        # then - record has new reaction
        updated_requests = db.session.query(Request).all()
        assert len(updated_requests) == 1
        assert updated_requests[0].request_types.get("message") == request_type_list
        assert updated_requests[0].request_types.get("reaction") == [reaction]

    def test_remove_reaction_from_request_types_results_record_has_new_emoji_given_main_record_exists(
        self, db_setup, test_record_added, cp, channel_id, event_ts, request_type_list
    ):
        # given - table has one record
        test_record_added()
        requests = db.session.query(Request).all()
        assert len(requests) == 1
        emoji_alias_list = list(set([value["alias"] for value in cp.channel_properties["_types"]["emojis"].values()]))
        reaction = emoji_alias_list[3]
        Request().add_reaction_to_request_types(channel_id, event_ts, reaction)
        assert len(requests) == 1
        assert requests[0].request_types.get("message") == request_type_list
        assert requests[0].request_types.get("reaction") == [reaction]

        # when record has been modified
        Request().remove_reaction_from_request_types(channel_id, event_ts, reaction)

        # then - the reaction was removed from the record
        updated_requests = db.session.query(Request).all()
        assert len(updated_requests) == 1
        assert updated_requests[0].request_types.get("message") == request_type_list
        assert updated_requests[0].request_types.get("reaction") == []

    def test_get_last_working_day_records_sorted_by_date_returns_records(
        self, db_setup, channel_id, requests_with_dates_added
    ):
        utc_now = datetime.strptime("2022-04-22 12:00:21", SLACK_DATETIME_FMT)

        requests_with_dates_added(
            [
                "2022-04-21 21:34:58",
                "2022-04-21 08:00:21",
                "2022-04-22 21:34:58",
                "2022-04-20 21:34:58",
            ]
        )
        results = Request().get_last_working_day_records_sorted_by_date(channel_id, utc_now)
        dates = [datetime.fromtimestamp(float(x.event_ts)).strftime(SLACK_DATETIME_FMT) for x in results]
        assert len(results) == 2
        assert {"2022-04-21 21:34:58", "2022-04-21 08:00:21"} == set(dates)
