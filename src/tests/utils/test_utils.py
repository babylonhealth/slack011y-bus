#!/usr/bin/env python3
import os
from datetime import datetime
from typing import List

import pytest

from src.code.dto.dto import RequestTypeDto
from src.code.utils.utils import datetime_to_date_string
from src.code.utils.utils import dto_to_json
from src.code.utils.utils import extract_request_types
from src.code.utils.utils import flat_list
from src.code.utils.utils import get_emojis_str_from_list
from src.code.utils.utils import get_last_business_day_holidays_not_included
from src.code.utils.utils import get_last_business_days_holidays_not_included
from src.code.utils.utils import is_business_day
from src.code.utils.utils import required_envar

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestUtils:
    def test_required_envar_returns_env(self):
        os.environ["TEST_1"] = "TEST_1"
        assert "TEST_1" == required_envar("TEST_1")

    def test_required_envar_returns_exception(self):
        with pytest.raises(EnvironmentError, match="envar TEST_2 is required"):
            assert "TEST_2" == required_envar("TEST_2")

    def test_extract_request_types_results_order_list_of_request_types_given_all_types_provided(
        self, channel_properties
    ):
        request_types_from_db = {
            "message": [
                "cloud-random",
                "cloud-bug",
                "cloud-props",
                "cloud-feature",
                "cloud-think",
                "cloud-help",
                "cloud-pr",
                "cloud-clarify",
                "cloud-incident",
            ],
            "reaction": [
                "cloud-random",
                "cloud-bug",
                "cloud-props",
                "cloud-feature",
                "white_check_mark",
                "cloud-pr",
                "cloud-clarify",
                "cloud-incident",
            ],
        }
        results = extract_request_types(request_types_from_db, channel_properties.types.emojis)
        assert set(channel_properties.types.emojis.keys()) == set(results)

    def test_extract_request_types_results_order_list_of_request_types_given_only_one_valid_type_provided(
        self, channel_properties
    ):
        request_types_from_db = {
            "message": [
                "cloud-random",
            ],
            "reaction": [
                "white_check_mark",
            ],
        }
        results = extract_request_types(request_types_from_db, channel_properties.types.emojis)
        assert {"cloud-random"} == set(results)

    def test_extract_request_types_results_empty_list_of_request_types_given_no_valid_types_provided(
        self, channel_properties
    ):
        request_types_from_db = {
            "message": [],
            "reaction": [
                "white_check_mark",
            ],
        }
        results = extract_request_types(request_types_from_db, channel_properties.types.emojis)
        assert 0 == len(results)

    def test_extract_request_types_results_empty_list_of_request_types_given_request_types_is_none(
        self, channel_properties
    ):
        results = extract_request_types({}, channel_properties.types.emojis)
        assert 0 == len(results)

    def test_dto_to_json(self):
        dto = RequestTypeDto(message=["message"], reaction=["reaction"])
        assert dto_to_json(dto) == {"message": ["message"], "reaction": ["reaction"]}

    def test_get_last_business_day_holidays_not_included(self):
        testing_data = [
            ("2022-05-06", "2022-05-05"),  # today Friday, last working date Thursday
            ("2022-05-08", "2022-05-06"),  # last Sunday, last working is Friday
            ("2022-05-07", "2022-05-06"),  # last Saturday, last working is Friday
        ]
        for data_time in testing_data:
            date = datetime.strptime(data_time[0], "%Y-%m-%d")
            assert datetime_to_date_string(get_last_business_day_holidays_not_included(date)) == data_time[1]

    def test_get_emojis_str_from_list(self):
        event_types: List[str] = ["cloud", "sky"]
        expected_result: str = ":cloud::sky:"
        assert get_emojis_str_from_list(event_types) == expected_result

    def test_get_last_business_days_holidays_not_included(self):
        testing_data = [
            ("2022-05-06", ("2022-04-28", "2022-04-29", "2022-05-02", "2022-05-03", "2022-05-04", "2022-05-05")),
            ("2022-05-08", ("2022-04-29", "2022-05-02", "2022-05-03", "2022-05-04", "2022-05-05", "2022-05-06")),
            ("2022-05-07", ("2022-04-29", "2022-05-02", "2022-05-03", "2022-05-04", "2022-05-05", "2022-05-06")),
        ]
        for data_time in testing_data:
            date = datetime.strptime(data_time[0], "%Y-%m-%d")
            for idx, result in enumerate(get_last_business_days_holidays_not_included(date, 6)):
                assert datetime.strptime(data_time[1][idx], "%Y-%m-%d") == result

    def test_is_business_day(self):
        testing_data = [
            ("2022-05-15", False),  # Sunday, not business day
            ("2022-05-14", False),  # Saturday, not business day
            ("2022-05-13", True),  # Friday, business day
            ("2022-05-12", True),  # Thursday, business day
            ("2022-05-11", True),  # Wednesday, business day
            ("2022-05-10", True),  # Tuesday, business day
            ("2022-05-09", True),  # Monday, business day
        ]
        for data in testing_data:
            assert data[1] == is_business_day(datetime.strptime(data[0], "%Y-%m-%d"))

    def test_flat_list(self):
        nested_list = [["a", "b"], "c"]
        assert flat_list(nested_list) == ["a", "b", "c"]
