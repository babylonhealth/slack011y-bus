from flask import abort
from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import fields
from varname import nameof

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import ChannelPropertiesFeatures
from src.code.model.schemas import channel_properties_schema

api_description = """
List and modify category daily report for a channel.
"""

ns = Namespace("reports", description=api_description)

schedule_dict = ns.model(
    "scheduleDict",
    {
        "local_time": fields.String(
            title="Local time", description="Time when the report will be printed", example="7:00"
        ),
        "last_report_datetime_utc": fields.String(
            title="last report date", description="Last report date", example="2022-12-12 7:00"
        ),
    },
)

report_dict = ns.model(
    "reportDict",
    {
        "schedules": fields.List(fields.Nested(schedule_dict)),
        "time_zone": fields.String(
            title="Report timezone",
            description="Report timezone if not provided, the default timezone is UTC",
            example="UTC",
        ),
        "output_channel_name": fields.String(
            title="Channel where the data will be printed",
            description=(
                "Channel where the data will be printed, "
                "if not provided, the report will be printed to the input channel"
            ),
            example="#channel",
        ),
    },
    skip_none=True,
    strict=True,
)

get_dict_json = ns.model(
    "reportDictJson",
    {
        "enabled": fields.Boolean(
            title="Feature flag", description="Controls if feature is enabled or not", example=True
        ),
        "daily_report": fields.Nested(
            report_dict, required=True, title="Daily report dict", description="Daily report"
        ),
    },
    strict=True,
)

form_modify = ns.model(
    "reportModify",
    {
        "schedules": fields.List(
            fields.String(
                title="Report localtime",
                description="Report localtime - required",
                example="7:00",
            )
        ),
        "time_zone": fields.String(
            title="Report timezone",
            description="Report timezone if not provided, the default timezone is UTC",
            example="UTC",
        ),
        "output_channel_name": fields.String(
            title="Channel where the data will be printed",
            description=(
                "Channel where the data will be printed, "
                "if not provided, the report will be printed to the input channel"
            ),
            example="#channel",
        ),
    },
)


@ns.route("/")
class TypesResource(Resource):
    @ns.doc(description="Daily report and feature status.")
    @ns.response(code=200, description="Daily report for a channel", model=get_dict_json)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def get(self, channel_id):
        channel_properties: ChannelProperties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        return channel_properties.get_feature_status_dict("daily_report"), 200

    @ns.doc(description="Modify daily report")
    @ns.response(code=200, description="Modification completed", model=get_dict_json)
    @ns.response(code=404, description="Channel not found")
    @ns.expect(form_modify, validate=True)
    def put(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        schedules = ns.payload.get("schedules")
        time_zone = ns.payload.get("time_zone")
        output_channel_name = ns.payload.get("output_channel_name")
        try:
            cp.modify_daily_report(schedules=schedules, time_zone=time_zone, output_channel_name=output_channel_name)
            channel_properties: ChannelProperties = channel_properties_schema.load(
                data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
            )
            return channel_properties.get_feature_status_dict("daily_report"), 200
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")


@ns.route("/enable")
class StartEnableResource(Resource):
    @ns.doc(description="Enable daily report feature")
    @ns.response(code=200, description="Feature status and config", model=get_dict_json)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.daily_report), True)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        channel_properties: ChannelProperties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        return channel_properties.get_feature_status_dict("daily_report"), 200


@ns.route("/disable")
class StartDisableResource(Resource):
    @ns.doc(description="Disable daily report feature")
    @ns.response(code=200, description="Feature status and config", model=get_dict_json)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.daily_report), False)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        channel_properties: ChannelProperties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        return channel_properties.get_feature_status_dict("daily_report"), 200
