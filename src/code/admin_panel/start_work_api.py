from typing import List

from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields
from varname import nameof

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelPropertiesFeatures
from src.code.model.schemas import channel_properties_schema

types_description = """
List and modify start work reactions for a channel.
"""
ns = Namespace("start_reactions", description=types_description)

reactions = ns.model(
    "StartWorkReactionList",
    {
        "start_work_reactions": fields.List(
            fields.String(
                title="Emoji name",
                description="Emoji name that will indicate the start of work on a thread when used as a reaction.",
                example="eye",
            )
        )
    },
)

enabled_and_reactions = ns.model(
    "StartWorkDetail",
    {
        "enabled": fields.Boolean(
            title="Feature enabling",
            description="Status of feature",
            example=False,
        ),
        "start_work_reactions": fields.List(
            fields.String(
                title="Emoji name",
                description="Emoji name that will indicate the start of work on a thread when used as a reaction.",
                example="eye",
            )
        ),
    },
)


@ns.route("/")
class StartResource(Resource):
    @ns.doc(description="Get start work feature status and config")
    @ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def get(self, channel_id: str):
        cp = HelperResource.get_control_panel_or_404(channel_id)
        return channel_properties_schema.load(data=cp.channel_properties).get_feature_status_dict(
            "start_work_reactions"
        )

    @ns.doc(description="Modify start work reactions feature")
    @ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    @ns.expect(reactions, validate=True)
    def post(self, channel_id: str):
        reactions: List[str] = ns.payload["start_work_reactions"]
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().update_channel_property(channel_id, "_start_work_reactions", reactions)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("start_work_reactions")
        )


@ns.route("/enable")
class StartEnableResource(Resource):
    @ns.doc(description="Enable start work feature")
    @ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.start_work_reactions), True)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("start_work_reactions")
        )


@ns.route("/disable")
class StartDisableResource(Resource):
    @ns.doc(description="Disable start work feature")
    @ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.start_work_reactions), False)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("start_work_reactions")
        )
