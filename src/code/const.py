import os
from typing import Union

from flask import Blueprint
from flask import Flask
from flask_restx import Api
from slack import WebClient

from src.code.utils.utils import required_envar

DAILY_REPORT_TEMPLATE = (
    '[{"type":"header","text":'
    '{"type":"plain_text","text":"$channel_name_placeholder","emoji":true}},'
    '{"type":"section","text":{"type":"mrkdwn",'
    '"text":"*Last Day $last_day_date_placeholder*\\n '
    '*$last_day_completed_count_placeholder* completed | *$last_day_open_count_placeholder* open"}},'
    '{"type":"divider"},'
    '{"type":"section",'
    '"text":{"type":"mrkdwn","text":"*Last day open items:*\\n $last_day_items_placeholder"}}'
    "]"
)

DAILY_REPORT_TEMPLATE_CONT = (
    "["
    '{"type":"section",'
    '"text":{"type":"mrkdwn","text":"*Last day open items - continuation:*\\n $last_day_items_placeholder"}}'
    "]"
)

DAILY_REPORT_ITEM_TEMPLATE = (
    "* _$start_datetime_utc_placeholder_  |  <$request_link_placeholder|request link>  |  $event_type_placeholder"
)

SLACK_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"
SLACK_WORKSPACE_NAME = os.getenv("SLACK_WORKSPACE_NAME", "dummy")
client: WebClient = WebClient(token=required_envar("SLACK_TOKEN"))
swagger: Blueprint = Blueprint("api", __name__, url_prefix="/admin/api/v1")

api: Api = Api(
    swagger,
    version="0.1",
    title="slack011y-bus api",
    doc="/swagger/",
)


def create_app(config_object: Union[object, str]) -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object(config_object)
    return app
