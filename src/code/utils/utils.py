import os
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


def required_envar(envkey: str) -> str:
    v = os.getenv(envkey)
    if not v:
        raise EnvironmentError("envar {0} is required".format(envkey))
    return v


def extract_request_types(request_types: Dict, types_dict: Dict) -> List[str]:
    if request_types:
        return [
            _
            for _ in types_dict.keys()
            if _ in set(request_types.get("message", {})).union(set(request_types.get("reaction", {})))
        ]
    return []


def dto_to_json(obj: Any) -> dict:
    return obj.__dict__


def datetime_to_date_string(date: datetime) -> str:
    return datetime.strftime(date, "%Y-%m-%d")


def get_emojis_str_from_list(event_types: List[str]) -> str:
    return "".join(f":{event_type}:" for event_type in event_types)


def get_last_business_days_holidays_not_included(date: datetime, days: int) -> list[datetime]:
    list_of_days: list[datetime] = []
    for day in range(days):
        checking_date = (date if not list_of_days else list_of_days[0]) - timedelta(days=1)
        if datetime.weekday(checking_date) == 5:
            checking_date = checking_date - timedelta(days=1)
        elif datetime.weekday(checking_date) == 6:
            checking_date = checking_date - timedelta(days=2)
        list_of_days.insert(0, checking_date)
    return list_of_days


def get_last_business_day_holidays_not_included(date: datetime) -> datetime:
    return get_last_business_days_holidays_not_included(date, 1)[-1]


def is_business_day(date: datetime) -> bool:
    if datetime.weekday(date) == 5 or datetime.weekday(date) == 6:
        return False
    return True


def flat_list(nested_list: Optional[List]) -> list:
    if not nested_list:
        return []
    return [x for xs in nested_list for x in xs]


def remove_duplicates_with_order(list_with_duplicates: list) -> list:
    result = []
    for x in list_with_duplicates:
        if x not in result:
            result.append(x)
    return result


def get_timestamp_range_from_dates(start_date: datetime, end_date: datetime) -> tuple[float, float]:
    start_date_timestamp = start_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    end_date_timestamp = end_date.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp()
    return start_date_timestamp, end_date_timestamp


def get_timestamp_range_from_date(date: datetime) -> tuple[float, float]:
    return get_timestamp_range_from_dates(date, date)
