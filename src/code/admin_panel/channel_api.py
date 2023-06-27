from typing import Optional

from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel

ns = Namespace("channels", description="Channels basic operations")

control_panel = ns.model("ControlPanel", {"slack_channel_id": fields.String, "slack_channel_name": fields.String})

control_panel_create = ns.model(
    "ControlPanelCreate",
    {"channel_id": fields.String("FSDDFSFS", required=True), "channel_name": fields.String("channel", required=True)},
)

channel_properties_model = ns.model("ControlPanelChannelProperties", {"key": fields.String("value")})

channels_details = ns.model(
    "ChannelsDetails",
    {
        "slack_channel_id": fields.String(
            title="Channel id",
            description="An id of the slack channel that slack bot is enabled on",
            example="FSDDFSFS",
        ),
        "slack_channel_name": fields.String(
            title="Channel name",
            description="A name of the slack channel that slack bot is enabled on",
            example="#channel",
        ),
        "channel_properties": fields.Wildcard(fields.Nested(channel_properties_model)),
    },
)


@ns.route("/")
class Channels(Resource):
    @ns.doc(description="Get all channels currently handled by slack bot")
    @ns.marshal_with(control_panel, as_list=True)
    @ns.response(code=200, description="List of channels handled by slack bot", model=control_panel, as_list=True)
    @ns.response(code=500, description="Internal server error")
    def get(self):
        return ControlPanel().get_all_active_control_panels()

    @ns.doc(description="Add a channel to slack bot")
    @ns.expect(control_panel_create, validate=True)
    @ns.response(code=200, description="Channel added", model=channels_details, as_list=True)
    @ns.response(code=409, description="Bad input")
    @ns.response(code=500, description="Internal server error")
    def post(self):
        channel_id: str = ns.payload["channel_id"]
        channel_name: str = ns.payload["channel_name"]
        cp: Optional[ControlPanel] = HelperResource.get_control_panel(channel_id)
        if cp:
            if cp.deactivation_ts is None:
                abort(409, description=f"channel with id {channel_id} already exists and is active")
            else:
                ControlPanel().activate_control_panel(cp)
        else:
            ControlPanel().add_control_panel(channel_id, channel_name)
        updated_control_panel: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        output = {
            "slack_channel_id": updated_control_panel.slack_channel_id,
            "slack_channel_name": updated_control_panel.slack_channel_name,
            "channel_properties": updated_control_panel.channel_properties,
        }
        return output, 200


@ns.route("/<string:channel_id>")
class ChannelResource(Resource):
    @ns.doc(description="Get channel details.")
    @ns.response(code=200, description="Feature status and config", model=channels_details)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def get(self, channel_id: str):
        cp = HelperResource.get_control_panel_or_404(channel_id)
        output = {
            "slack_channel_id": cp.slack_channel_id,
            "slack_channel_name": cp.slack_channel_name,
            "channel_properties": cp.channel_properties,
        }
        return output

    @ns.doc(description="Remove a channel from slack bot config")
    @ns.response(code=200, description="Channel removed from slack bot")
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=500, description="Internal server error")
    def delete(self, channel_id: str):
        cp = HelperResource.get_control_panel_or_404(channel_id)
        ControlPanel().soft_delete_control_panel(cp)
        return {"success": "The channel has been removed successfully"}
