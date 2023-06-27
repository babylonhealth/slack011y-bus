from typing import Any
from typing import Dict

SECTION = {"type": "section", "text": {"type": "mrkdwn", "text": ""}}

MULTI_STATIC_SELECT_FORM = {
    "type": "section",
    "text": {"type": "mrkdwn", "text": ""},
    "accessory": {
        "type": "multi_static_select",
        "placeholder": {"type": "plain_text", "text": "Select tools", "emoji": True},
        "options": [],
        "action_id": "",
    },
}

BUTTON_FORM = [SECTION, {"type": "actions", "elements": []}]

BUTTON_FORM_WITH_CLEAR_FORM = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": ""},
        "accessory": {
            "type": "button",
            "text": {"type": "plain_text", "text": "🗑️ Clear form", "emoji": True},
            "value": "click_me_123",
            "action_id": "button-action",
        },
    },
    {"type": "actions", "elements": []},
]

DIVIDER = {"type": "divider"}

FORM_TITLE_HEADER: Dict[str, Any] = {
    "type": "header",
    "text": {"type": "plain_text", "text": "placeholder"},
}
