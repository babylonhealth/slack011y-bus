import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pytz

from src.code.const import DAILY_REPORT_TEMPLATE
from src.code.const import SLACK_DATETIME_FMT
from src.code.model.control_panel import ControlPanel
from src.code.model.request import Request
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import channel_properties_schema
from src.code.report.request_report import RequestReport
from src.code.utils.slack_webclient import SlackWebclient
from src.code.utils.utils import datetime_to_date_string
from src.code.utils.utils import get_last_business_day_holidays_not_included


class TestChannelReport:
    def test_daily_report_results_report_given_last_report_date_is_empty(self, cp_daily_report: ControlPanel):
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime(2022, 5, 13, 8, 0, 0, tzinfo=pytz.UTC)
        testing_data = [
            {
                "schedule": [
                    {"local_time": "8:00", "last_report_datetime_utc": ""},
                    {"local_time": "20:00", "last_report_datetime_utc": ""},
                ],
                "count_of_reports_created": 1,
            },
            {
                "schedule": [
                    {"local_time": "7:00", "last_report_datetime_utc": ""},
                    {"local_time": "20:00", "last_report_datetime_utc": ""},
                ],
                "count_of_reports_created": 1,
            },
            {
                "schedule": [
                    {"local_time": "9:00", "last_report_datetime_utc": ""},
                    {"local_time": "20:00", "last_report_datetime_utc": ""},
                ],
                "count_of_reports_created": 0,
            },
            {
                "schedule": [
                    {"local_time": "7:00", "last_report_datetime_utc": "2022-05-13 7:00:00"},
                    {"local_time": "20:00", "last_report_datetime_utc": "2022-05-12 20:00:00"},
                ],
                "count_of_reports_created": 0,
            },
            {
                "schedule": [
                    {"local_time": "7:00", "last_report_datetime_utc": "2022-05-12 7:00:00"},
                    {"local_time": "20:00", "last_report_datetime_utc": "2022-05-12 20:00:00"},
                ],
                "count_of_reports_created": 1,
            },
        ]
        with patch("datetime.datetime", new=datetime_mock):
            for data in testing_data:
                cp: ControlPanel = cp_daily_report(data)
                with patch.object(ControlPanel, "get_all_active_control_panels", return_value=[cp]):
                    with patch.object(Request, "get_last_working_day_records_sorted_by_date", return_value=[]):
                        with patch.object(SlackWebclient, "send_post_message_as_main_message", return_value=None):
                            with patch.object(
                                ControlPanel, "update_last_report_datetime_utc_field", return_value=None
                            ) as mock:
                                RequestReport().daily_report()
                    assert data["count_of_reports_created"] == mock.call_count

    def test_generate_report_check_results_sending_post_to_specific_channel(self, cp_daily_report):
        data_1 = {
            "schedule": [
                {"local_time": "7:00", "last_report_datetime_utc": "2022-12-12 7:00"},
                {"local_time": "20:00", "last_report_datetime_utc": ""},
            ]
        }
        data_2 = {
            "schedule": [
                {"local_time": "7:00", "last_report_datetime_utc": "2022-12-12 7:00"},
                {"local_time": "20:00", "last_report_datetime_utc": ""},
            ]
        }
        cp_1: ControlPanel = cp_daily_report(data_1)
        cp_2: ControlPanel = cp_daily_report(data_2)
        for cp in ((cp_1, 1, "#cloud"), (cp_2, 1, "channel1")):
            with patch.object(Request, "get_last_working_day_records_sorted_by_date", return_value=[]):
                with patch.object(SlackWebclient, "send_post_message_as_main_message", return_value=None) as mock:
                    with patch.object(ControlPanel, "update_last_report_datetime_utc_field", return_value=None):
                        channel_properties: ChannelProperties = channel_properties_schema.load(cp[0].channel_properties)
                        channel_properties.daily_report.output_channel_name = cp[2]
                        RequestReport()._generate_report(cp[0], channel_properties, datetime.datetime.utcnow(), 0)
                        assert cp[1] == mock.call_count
                        assert cp[2] == mock.call_args[0][1]

    def test_create_daily_report_results_json_report(
        self, cp_daily_report: ControlPanel, daily_report_request_for_test
    ):
        utc_now = datetime.datetime.utcnow()
        data_for_testing = [
            {
                "link": "link1",
                "message": ["cloud-pr"],
                "reaction": ["white_check_mark"],
                "completion_datetime_utc": None,
            },
            {"link": "link2", "message": ["cloud-pr"], "reaction": ["cloud-help"], "completion_datetime_utc": utc_now},
        ]
        last_day_records = [
            daily_report_request_for_test(
                utc_now.timestamp(), _["link"], _["message"], _["reaction"], _["completion_datetime_utc"]
            )
            for _ in data_for_testing
        ]
        data = {
            "schedule": [
                {"local_time": "7:00", "last_report_datetime_utc": "2022-12-12 7:00"},
                {"local_time": "20:00", "last_report_datetime_utc": ""},
            ]
        }
        cp: ControlPanel = cp_daily_report(data)
        channel_properties: ChannelProperties = channel_properties_schema.load(cp.channel_properties)
        report = RequestReport()._create_daily_report(
            cp.slack_channel_name, channel_properties, utc_now, last_day_records
        )

        last_working_date = datetime_to_date_string(
            get_last_business_day_holidays_not_included(utc_now - datetime.timedelta(days=1))
        )
        expected_report = DAILY_REPORT_TEMPLATE.replace("$channel_name_placeholder", cp.slack_channel_name)
        expected_report = expected_report.replace("$last_day_date_placeholder", last_working_date)
        expected_report = expected_report.replace("$last_day_completed_count_placeholder", "0")
        expected_report = expected_report.replace("$last_day_open_count_placeholder", "2")
        expected_report = expected_report.replace(
            "$last_day_items_placeholder",
            "* _"
            + utc_now.strftime(SLACK_DATETIME_FMT)
            + "_  |  <link1|request link>  |  \n* _"
            + utc_now.strftime(SLACK_DATETIME_FMT)
            + "_  |  <link2|request link>  |  \n",
        )
        assert len(report) == 1
        assert expected_report == report[0]

    def test_create_daily_report_results_json_in_2_peaces_block_bigger_then_3001(
        self, cp_daily_report, channel_properties, x_random_records_for_testing
    ):
        utc_now = datetime.datetime.utcnow()
        data = {
            "schedule": [
                {"local_time": "7:00", "last_report_datetime_utc": "2022-12-12 7:00"},
                {"local_time": "20:00", "last_report_datetime_utc": ""},
            ]
        }
        cp: ControlPanel = cp_daily_report(data)
        last_day_records = x_random_records_for_testing(25, utc_now)
        result = RequestReport()._create_daily_report(
            cp.slack_channel_name, channel_properties, utc_now, list(last_day_records)
        )
        assert len(result) == 2
