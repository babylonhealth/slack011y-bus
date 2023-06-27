from typing import Any
from typing import Callable
from typing import Dict

import pytest

import src.tests.test_env  # noqa
from src.code.model.control_panel import ControlPanel


@pytest.fixture()
def form_questions(event_ts) -> Dict:
    return {
        "creation_ts": event_ts,
        "form_title": "form_title",
        "triggers": ["eyes"],
        "questions": [
            {
                "name": "question_1",
                "question_title": "question_title_1",
                "action_id": "action_id_1",
                "options_title": "options_title_1",
                "options": {"default": ["option_1", "option_2"]},
            },
            {
                "name": "question_2",
                "question_title": "question_title_2",
                "action_id": "action_id_2",
                "options_title": "options_title_2",
                "options": {"default": ["option_3", "option_4"], "option_1": ["option_5", "option_6"]},
            },
        ],
        "recommendations": {
            "option_1": {"option_5": {"recommendations": [{"name": "rec1", "link": "link1"}]}},
            "option_2": {"Documentation": {"recommendations": [{"name": "rec2", "link": "link2"}]}},
        },
    }


@pytest.fixture()
def cp_with_question_form(channel_name, channel_id, event_ts) -> Callable[[Dict[Any, Any], bool], Any]:
    def __get_cp(form_questions: Dict, form_question_enabling: bool = True) -> Any:
        return ControlPanel(
            slack_channel_name=channel_name,
            slack_channel_id=channel_id,
            creation_ts=event_ts,
            channel_properties={
                "features": {"question_form": {"enabled": form_question_enabling}},
                "_question_forms": form_questions,
            },
        )

    return __get_cp
