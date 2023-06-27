from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional


@dataclass(frozen=True)
class NewRecordDto:
    channel_name: str
    channel_id: str
    requestor_id: str
    requestor_email: str
    requestor_team_id: str
    blocks: Dict
    request_types_from_message: List
    event_ts: str
    request_link: str
    request_types: Optional[Dict] = None


@dataclass(frozen=True)
class CompletionReactionDto:
    completion_reactions: list[str]


@dataclass(frozen=True)
class RequestTypeDto:
    message: list[str]
    reaction: list[str]


@dataclass(frozen=True)
class ReportDto:
    report_datetime: datetime
    last_working_date: str
    last_day_total: int
    last_day_completed: int
    last_day_completed_items: list
    last_day_open: int
    last_day_open_items: list
