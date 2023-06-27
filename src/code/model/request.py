from datetime import datetime
from typing import Any
from typing import Dict
from typing import List

from pytz import timezone
from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import and_
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import flag_modified

from src.code.db import db
from src.code.dto.dto import CompletionReactionDto
from src.code.dto.dto import NewRecordDto
from src.code.dto.dto import RequestTypeDto
from src.code.logger import create_logger
from src.code.model.block import Block
from src.code.model.custom_enums import AutocloseStatus
from src.code.model.custom_enums import RequestStatusEnum
from src.code.utils.utils import dto_to_json
from src.code.utils.utils import get_last_business_day_holidays_not_included
from src.code.utils.utils import get_timestamp_range_from_date

logger = create_logger(__name__)


class Request(db.Model):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)
    slack_channel_name = Column(String(80), nullable=False)
    slack_channel_id = Column(String(64), nullable=False)
    request_status = Column(String(64), nullable=False)
    requestor_id = Column(String(64), nullable=False)
    requestor_email = Column(String(1000))
    requestor_team_id = Column(String(64))
    event_ts = Column(Numeric(16, 6), nullable=False)
    start_work_datatime_utc = Column(DateTime)
    completion_datetime_utc = Column(DateTime)
    request_types = Column(JSON)
    completion_reactions = Column(JSON)
    form_answers = Column(JSON)
    blocks_id = Column(Integer, ForeignKey("blocks.id"))
    request_link = Column(String(255))
    autoclose_status = Column(String(64))
    thread_message = relationship("ThreadMessage", cascade="all, delete")
    blocks_table = relationship("Block", cascade="all, delete")

    def get_request_or_throw_exception(self, channel_id: str, event_ts: str) -> "Request":
        record = self.get_request(channel_id, event_ts)
        if record is None:
            raise ValueError(f"Request for {channel_id} and {event_ts} not found")
        return record

    def get_request(self, channel_id: str, event_ts: str) -> "Request":
        record = db.session.query(Request).filter_by(slack_channel_id=channel_id, event_ts=event_ts).first()
        if record:
            record.blocks = Block().get_blocks(record.blocks_id)
        return record

    def update_or_register_new_record(self, new_record: NewRecordDto):
        record = self.get_request(new_record.channel_id, new_record.event_ts)
        if not record:
            logger.info(
                "Creating new record %s for channel %s with details %s",
                new_record.event_ts,
                new_record.channel_name,
                new_record.request_link,
            )
            blocks_id = Block().create_or_update_existing_blocks(new_record.blocks)
            record = self._create_initial_record(new_record, blocks_id)
            db.session.add(record)
        else:
            logger.info(
                "Updating %s record for channel %s with details %s",
                new_record.event_ts,
                new_record.channel_name,
                new_record.request_link,
            )
            resulting_request_types = (
                new_record.request_types
                if new_record.request_types is not None
                else dto_to_json(self._get_request_types_from_message(record, new_record.request_types_from_message))
            )
            self.update_request(
                record=record,
                blocks=new_record.blocks,
                request_types=resulting_request_types,
                requestor_email=new_record.requestor_email,
            )
        db.session.commit()

    def close_request(self, channel_id: str, request_ts: str, reaction_ts: str, reaction: str):
        record = self.get_request_or_throw_exception(channel_id, request_ts)
        record.request_status = RequestStatusEnum.COMPLETED.value
        record.completion_datetime_utc = datetime.fromtimestamp(float(reaction_ts), tz=timezone("UTC"))
        self._add_complete_reaction_to_record(record, reaction)
        db.session.commit()

    def remove_request(self, channel_id: str, event_ts: str) -> None:
        channel = self.get_request_or_throw_exception(channel_id, event_ts)
        db.session.delete(channel)
        db.session.commit()

    def add_reaction_to_request_types(self, channel_id: str, request_ts: str, reaction: str):
        record = self.get_request_or_throw_exception(channel_id, request_ts)
        record.request_types = self._add_reaction_to_request_types(record, reaction)
        db.session.commit()

    def remove_completion_reaction(self, channel_id: str, request_ts: str, reaction: str):
        record = self.get_request(channel_id, request_ts)
        if record is not None:
            completion_reactions_set: set = self._remove_complete_reaction_from_record(record, reaction)
            if len(completion_reactions_set) == 0:
                record.request_status = RequestStatusEnum.WORKING.value
                record.completion_datetime_utc = None
            record.completion_reactions = dto_to_json(
                CompletionReactionDto(completion_reactions=list(completion_reactions_set))
            )
            db.session.commit()

    def remove_reaction_from_request_types(self, channel_id: str, request_ts: str, reaction: str):
        record = self.get_request(channel_id, request_ts)
        if record is not None:
            record.request_types = self._remove_reaction_from_request_types(record, reaction)
            db.session.commit()

    def _create_initial_record(self, new_record: NewRecordDto, blocks_id: int) -> "Request":  # create new record
        return Request(
            slack_channel_name=new_record.channel_name,
            slack_channel_id=new_record.channel_id,
            request_status=RequestStatusEnum.NEW_RECORD.value,
            requestor_id=new_record.requestor_id,
            requestor_email=new_record.requestor_email,
            requestor_team_id=new_record.requestor_team_id,
            event_ts=new_record.event_ts,
            request_types=dto_to_json(RequestTypeDto(message=new_record.request_types_from_message, reaction=[])),
            completion_reactions=dto_to_json(CompletionReactionDto(completion_reactions=[])),
            blocks_id=blocks_id,
            request_link=new_record.request_link,
        )

    def update_request(self, record, request_types: Dict, blocks: Dict, requestor_email: str) -> None:
        record.request_types = request_types
        record.requestor_email = requestor_email
        Block().create_or_update_existing_blocks(blocks, record.blocks_id)

    def start_work(self, record, event_ts: str) -> None:
        if record.request_status == RequestStatusEnum.NEW_RECORD.value and record.start_work_datatime_utc is None:
            record.request_status = RequestStatusEnum.WORKING.value
            record.start_work_datatime_utc = datetime.fromtimestamp(float(event_ts), tz=timezone("UTC"))
            logger.info("Current main message status has been changed to %s", RequestStatusEnum.WORKING.value)
            db.session.commit()

    def _add_reaction_to_request_types(self, record, reaction: str) -> Dict[Any, Any]:
        current_request_types = record.request_types
        current_reactions_set = set(current_request_types["reaction"])
        current_reactions_set.add(reaction)
        return dto_to_json(self._get_request_types_from_reaction(record, list(current_reactions_set)))

    def _add_complete_reaction_to_record(self, record, reaction: str):
        current_completion_marks: set = set(record.completion_reactions["completion_reactions"])
        current_completion_marks.add(reaction)
        record.completion_reactions = dto_to_json(
            CompletionReactionDto(completion_reactions=list(current_completion_marks))
        )

    def _remove_complete_reaction_from_record(self, record, reaction: str) -> set:
        current_completion_marks: set = set(record.completion_reactions["completion_reactions"])
        current_completion_marks.remove(reaction)
        return current_completion_marks

    def _remove_reaction_from_request_types(self, record, reaction) -> Dict[Any, Any]:
        current_request_types = record.request_types
        current_reactions_set = set(current_request_types["reaction"])
        current_reactions_set.remove(reaction)
        return dto_to_json(self._get_request_types_from_reaction(record, list(current_reactions_set)))

    def _get_request_types_from_message(self, record, request_types_from_message: List[str]) -> RequestTypeDto:
        return RequestTypeDto(message=request_types_from_message, reaction=record.request_types["reaction"])

    def _get_request_types_from_reaction(self, record, request_types_from_reaction: List[str]) -> RequestTypeDto:
        return RequestTypeDto(message=record.request_types["message"], reaction=request_types_from_reaction)

    def change_autoclose_status(self, channel_id: str, main_ts: str, status: AutocloseStatus):
        record = self.get_request_or_throw_exception(channel_id, main_ts)
        record.autoclose_status = status.value
        db.session.commit()

    # form functions
    def get_form_answers(self, channel_id: str, event_ts: str):
        record = self.get_request_or_throw_exception(channel_id, event_ts)
        if record is None:
            raise ValueError(f"Channel for {channel_id} and {event_ts} not found")
        return record.form_answers

    def init_form_answers(self, channel_id: str, main_ts: str) -> None:
        record = self.get_request_or_throw_exception(channel_id, main_ts)
        record.form_answers = {}
        db.session.commit()

    def save_form_answers(self, channel_id: str, main_ts: str, question_id: str, answers: list[str]) -> None:
        record = self.get_request_or_throw_exception(channel_id, main_ts)
        form_answer_loaded = record.form_answers
        form_answer_loaded[question_id] = list(answers)
        record.form_answers = form_answer_loaded
        flag_modified(record, "form_answers")
        db.session.commit()

    def remove_all_form_answers(self, channel_id: str, main_ts: str) -> None:
        self.init_form_answers(channel_id, main_ts)

    def get_last_working_day_records_sorted_by_date(self, channel_id: str, utc_now: datetime) -> list[Any]:
        last_working_data = get_last_business_day_holidays_not_included(utc_now)
        start_of_last_working_data_timestamp, end_of_last_working_data_timestamp = get_timestamp_range_from_date(
            last_working_data
        )
        return (
            Request.query.filter(
                and_(
                    Request.slack_channel_id == channel_id,
                    Request.event_ts >= start_of_last_working_data_timestamp,
                    Request.event_ts <= end_of_last_working_data_timestamp,
                )
            )
            .order_by(Request.event_ts.desc())
            .all()
        )


class ThreadMessage(db.Model):
    __tablename__ = "thread_messages"

    id = Column(Integer, primary_key=True)
    author_id = Column(String(64), nullable=False)
    event_ts = Column(Numeric(16, 6), nullable=False)
    blocks_id = Column(Integer, ForeignKey("blocks.id"))
    request_table_id = Column(Integer, ForeignKey("requests.id"))
    blocks_table = relationship("Block", cascade="all, delete")

    def add_reply(self, request: Request, event_ts: str, author_id: str, blocks: dict):
        record = self._get_reply(request.slack_channel_id, event_ts)
        if record:
            raise ValueError(
                f"Record for channel_id {request.slack_channel_id} and thread event_ts {event_ts} exists already"
            )
        else:
            logger.info("Creating new reply for channel_id %s with event_ts %s", request.slack_channel_id, event_ts)
            blocks_id = Block().create_or_update_existing_blocks(blocks)
            thread_message = ThreadMessage(
                author_id=author_id,
                event_ts=event_ts,
                blocks_id=blocks_id,
                request_table_id=request.id,
            )
            db.session.add(thread_message)
            db.session.commit()

    def update_reply(self, channel_id: str, event_ts: str, blocks: dict):
        record = self._get_reply(channel_id, event_ts)
        if not record:
            raise ValueError(f"Updating record for channel_id {channel_id} and main_ts {event_ts} has not been found")
        else:
            logger.info("Updating existing reply for channel_id %s and main_ts %s", channel_id, event_ts)
            Block().create_or_update_existing_blocks(blocks, record.blocks_id)
            db.session.commit()

    def _get_reply(self, channel_id: str, event_ts: str):
        result = (
            db.session.query(ThreadMessage)
            .join(Request)
            .filter(Request.slack_channel_id == channel_id, ThreadMessage.event_ts == event_ts)
            .first()
        )
        if result:
            result.blocks = Block().get_blocks(result.blocks_id)
        return result
