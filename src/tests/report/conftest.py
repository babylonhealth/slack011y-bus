import datetime

import pytest

from src.code.model.control_panel import ControlPanel
from src.code.model.request import Request


@pytest.fixture()
def cp_daily_report():
    def __add_testing_record(data):
        schedule = data.get("schedule")
        time_zone = data.get("timezone", "UTC")
        return ControlPanel(
            id=1,
            slack_channel_name="channel1",
            slack_channel_id="BOGUS_CHANNEL_ID",
            channel_properties={
                "features": {"daily_report": {"enabled": True}},
                "_daily_report": {
                    "schedules": [
                        {
                            "local_time": schedule[0]["local_time"],
                            "last_report_datetime_utc": schedule[0]["last_report_datetime_utc"],
                        }
                    ],
                    "time_zone": time_zone,
                },
            },
        )

    return __add_testing_record


@pytest.fixture()
def daily_report_request_for_test():
    def _create_request_for_test(date, link, message=(), reaction=(), completion_datetime_utc=None):
        return Request(
            completion_datetime_utc=completion_datetime_utc,
            request_link=link,
            request_types={"message": message, "reaction": reaction},
            event_ts=date,
        )

    return _create_request_for_test


@pytest.fixture()
def x_random_records_for_testing():
    def __create_x_random_records_for_testing(number_of_records: int, date_time: datetime.datetime):
        num = 0
        while num < number_of_records:
            yield Request(
                event_ts=date_time.timestamp(),
                request_link="https://.slack.com/archives/BOGUS_CHANNEL_ID/p1651157022748229",
                request_types={"message": ["cloud-incident", "cloud-bug", "cloud-props"], "reaction": []},
            )
            num += 1

    return __create_x_random_records_for_testing
