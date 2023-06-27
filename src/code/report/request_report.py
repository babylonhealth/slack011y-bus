import datetime
import os
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import TypedDict

import pytz
from slack import WebClient

from src.code.const import DAILY_REPORT_ITEM_TEMPLATE
from src.code.const import DAILY_REPORT_TEMPLATE
from src.code.const import DAILY_REPORT_TEMPLATE_CONT
from src.code.const import SLACK_DATETIME_FMT
from src.code.dto.dto import ReportDto
from src.code.logger import create_logger
from src.code.model.control_panel import ControlPanel
from src.code.model.custom_enums import RequestStatusEnum
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import DailyReport
from src.code.model.schemas import Schedule
from src.code.model.schemas import channel_properties_schema
from src.code.utils.slack_webclient import SlackWebclient
from src.code.utils.utils import datetime_to_date_string
from src.code.utils.utils import extract_request_types
from src.code.utils.utils import get_emojis_str_from_list
from src.code.utils.utils import get_last_business_day_holidays_not_included
from src.code.utils.utils import is_business_day


class StatListHandler(TypedDict):
    start_datetime_utc: datetime.datetime
    request_link: str
    event_type: List[str]
    requestor: str


lambda_stat_list_handler: Callable[[Any], StatListHandler] = lambda x, type_dict: {
    "start_datetime_utc": datetime.datetime.fromtimestamp(x.event_ts),
    "request_link": x.request_link,
    "event_type": extract_request_types(x.request_types, type_dict),
    "requestor": x.requestor_id,
}

client = WebClient(token=os.getenv("SLACK_TOKEN", "dummy"))
logger = create_logger(__name__)


class RequestReport:
    def daily_report(self):
        utc_now = datetime.datetime.now(tz=pytz.UTC)
        logger.info("Daily report background process has been started at %s", utc_now.strftime(SLACK_DATETIME_FMT))
        if not is_business_day(utc_now):
            logger.info("Daily report prints only on business days, today is %s", utc_now.today().strftime("%A"))
            return
        for cp in ControlPanel().get_all_active_control_panels():
            if cp.channel_properties:
                channel_properties: ChannelProperties = channel_properties_schema.load(cp.channel_properties)
                if channel_properties.daily_report is not None:
                    daily_report: DailyReport = channel_properties.daily_report
                    for idx, schedule in enumerate(daily_report.schedules):
                        if self._is_time_for_creating_report(
                            schedule.last_report_datetime_utc, daily_report, schedule, utc_now
                        ):
                            logger.info(
                                "Daily report for channel % has been started at %s",
                                cp.slack_channel_name,
                                utc_now.strftime(SLACK_DATETIME_FMT),
                            )
                            self._generate_report(cp, channel_properties, utc_now, idx)

    def _is_time_for_creating_report(
        self, last_report_datetime_utc: str, daily_report: DailyReport, schedule: Schedule, utc_now
    ) -> bool:
        logger.info(
            "Daily report process started checking if is time for creating report time: %s and last report was at: %s",
            utc_now.strftime(SLACK_DATETIME_FMT),
            last_report_datetime_utc,
        )
        tz = pytz.timezone(daily_report.time_zone)
        scheduled_time = tz.localize(datetime.datetime.strptime(schedule.local_time, "%H:%M"), is_dst=None).time()
        if not last_report_datetime_utc:
            return scheduled_time <= utc_now.time()
        else:
            last_report_datetime_utc = pytz.UTC.localize(
                datetime.datetime.strptime(last_report_datetime_utc, SLACK_DATETIME_FMT)
            )
            return last_report_datetime_utc.date() < utc_now.date() and scheduled_time <= utc_now.time()

    def _generate_report(self, cp: ControlPanel, channel_properties: ChannelProperties, utc_now: datetime, idx: int):
        last_day_records = Request().get_last_working_day_records_sorted_by_date(cp.slack_channel_id, utc_now)
        blocks = self._create_daily_report(cp.slack_channel_name, channel_properties, utc_now, last_day_records)
        output_channel = channel_properties.daily_report.output_channel_name or cp.slack_channel_name
        logger.info("Daily report is sending to channel %s in %s pace/s", output_channel, str(len(blocks)))
        for block in blocks:
            SlackWebclient().send_post_message_as_main_message(client, output_channel, block)
        ControlPanel().update_last_report_datetime_utc_field(idx, cp.slack_channel_id, utc_now)

    def _create_daily_report(
        self,
        channel_name: str,
        channel_properties: ChannelProperties,
        utc_now: datetime,
        last_day_records: List[Request],
    ) -> list[(str, int)]:
        type_dict = channel_properties.types.emojis
        report_dto = self._get_report_dto(utc_now, last_day_records, type_dict)

        block_limit = 3001
        main_block = (
            DAILY_REPORT_TEMPLATE.replace("$channel_name_placeholder", channel_name)
            .replace("$last_day_date_placeholder", report_dto.last_working_date)
            .replace("$last_day_completed_count_placeholder", str(report_dto.last_day_completed))
            .replace("$last_day_open_count_placeholder", str(report_dto.last_day_open))
        )
        main_block_limit = block_limit - len(main_block)

        extra_block_limit = block_limit - len(DAILY_REPORT_TEMPLATE_CONT)

        list_of_blocks = []
        temp = ""
        temp_count = 0
        for item in report_dto.last_day_open_items:
            adding_item = f"{self._item_to_daily_template(item)}\n"
            temp_count += len(adding_item)
            if temp_count > (main_block_limit if len(list_of_blocks) == 0 else extra_block_limit):
                list_of_blocks.append(temp)
                temp_count = 0
                temp = ""
            temp += adding_item
        list_of_blocks.append(temp)

        return [
            main_block.replace("$last_day_items_placeholder", block)
            if idx == 0
            else DAILY_REPORT_TEMPLATE_CONT.replace("$last_day_items_placeholder", block)
            for idx, block in enumerate(list_of_blocks)
        ]

    def _get_report_dto(self, utc_now: datetime, last_day_records: List[Request], type_dict: Dict) -> ReportDto:
        completed_list, open_list = self._get_basic_stats(last_day_records, type_dict)
        return ReportDto(
            report_datetime=utc_now,
            last_working_date=datetime_to_date_string(
                get_last_business_day_holidays_not_included(utc_now - datetime.timedelta(days=1))
            ),
            last_day_total=len(last_day_records),
            last_day_completed=len(completed_list),
            last_day_completed_items=completed_list,
            last_day_open=len(open_list),
            last_day_open_items=open_list,
        )

    def _get_basic_stats(self, last_day_records: List[Request], type_dict: Dict) -> tuple[List[Any], List[Any]]:
        completed_list = [
            lambda_stat_list_handler(_, type_dict)
            for _ in last_day_records
            if _.request_status == RequestStatusEnum.COMPLETED.value
        ]
        open_list = [
            lambda_stat_list_handler(_, type_dict)
            for _ in last_day_records
            if _.request_status != RequestStatusEnum.COMPLETED.value
        ]
        return completed_list, open_list

    def _item_to_daily_template(self, item: Any) -> str:
        return (
            DAILY_REPORT_ITEM_TEMPLATE.replace(
                "$start_datetime_utc_placeholder", item["start_datetime_utc"].strftime(SLACK_DATETIME_FMT)
            )
            .replace("$request_link_placeholder", item["request_link"])
            .replace("$event_type_placeholder", get_emojis_str_from_list(item["event_type"]))
        )
