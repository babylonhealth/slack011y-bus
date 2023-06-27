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

completion_description = """
List and modify completion reactions emoji for a channel.
"""
completion_ns = Namespace("completion_reactions", description=completion_description)

reactions = completion_ns.model(
    "CompletionReactionList",
    {
        "completion_reactions": fields.List(
            fields.String(
                title="Emoji name",
                description="Emoji names which signifes that a message thread is completed",
                example="white_check_mark",
            ),
            required=True,
        )
    },
)

enabled_and_reactions = completion_ns.model(
    "CompletionDetail",
    {
        "enabled": fields.Boolean(
            title="Feature enabling",
            description="Status of feature",
            example=False,
        ),
        "completion_reactions": fields.List(
            fields.String(
                title="Emoji name",
                description="Emoji names which signifes that a message thread is completed",
                example="white_check_mark",
            )
        ),
    },
)


@completion_ns.route("/")
class CompleteResource(Resource):
    @completion_ns.doc(description="Get completion reactions status and config")
    @completion_ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @completion_ns.response(code=404, description="Channel not found")
    def get(self, channel_id: str):
        cp = HelperResource.get_control_panel_or_404(channel_id)
        return channel_properties_schema.load(data=cp.channel_properties).get_feature_status_dict(
            "completion_reactions"
        )

    @completion_ns.doc(description="Modify completion reactions status and config")
    @completion_ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @completion_ns.response(code=404, description="Channel not found")
    @completion_ns.response(code=500, description="Internal server error")
    @completion_ns.expect(reactions, validate=True)
    def post(self, channel_id: str):
        reactions: List[str] = completion_ns.payload["completion_reactions"]
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().update_channel_property(channel_id, "_completion_reactions", reactions)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("completion_reactions")
        )


@completion_ns.route("/enable")
class CompleteEnableResource(Resource):
    @completion_ns.doc(description="Enable completion reactions")
    @completion_ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @completion_ns.response(code=404, description="Channel not found")
    @completion_ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.completion_reactions), True)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("completion_reactions")
        )


@completion_ns.route("/disable")
class CompleteDisableResource(Resource):
    @completion_ns.doc(description="Disable completion reactions")
    @completion_ns.response(code=200, description="Feature status and config", model=enabled_and_reactions)
    @completion_ns.response(code=404, description="Channel not found")
    @completion_ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.completion_reactions), False)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("completion_reactions")
        )
