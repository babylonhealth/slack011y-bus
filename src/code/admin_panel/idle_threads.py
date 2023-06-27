from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields
from varname import nameof

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelPropertiesFeatures
from src.code.model.schemas import CloseIdleThreads
from src.code.model.schemas import channel_properties_schema
from src.code.model.schemas import close_idle_threads_schema

idle_threads_description = """
Modify how the bot handles idle message threads in a channel.
Idle threads are closed with a completion reaction, so this feature is closly coupled to completion_reactions feature.
It will not function with completion_reactions disabled.
"""
idle_threads_ns = Namespace("close_idle_threads", description=idle_threads_description)

idle_threads_dict = idle_threads_ns.model(
    "IdleThreadsDict",
    {
        "reminder_message": fields.String(
            title="Reminder message",
            description="Text that is sent to a thread when the bot deems it idle.",
            example=(
                "Hello. There has been no activity in this thread for a long time.\nPlease mark the main request as"
                " done if the case is resolved. If not, please add a new reply to the thread."
            ),
            required=True,
        ),
        "close_message": fields.String(
            title="Close message",
            description="Text that is sent to a thread when to bot closes it",
            example=(
                "Hello. Because there is no activity in this thread, it has been marked as done.\nIf the case is still"
                " relevant, please create a new thread or raise a jira ticket."
            ),
            required=True,
        ),
        "scan_limit_days": fields.Integer(
            title="Scan limit in days",
            description="How long in the past should the bot inspect channel threads and check if they are idle or not",
            example=CloseIdleThreads.scan_limit_days,
        ),
        "close_after_creation_hours": fields.Integer(
            title="Close after creation in hours",
            description="How long the thread should exist before the bot can deem it as idle (and viable for closure).",
            example=CloseIdleThreads.close_after_creation_hours,
        ),
        "reminder_grace_period_hours": fields.Integer(
            title="Reminder grace period",
            description=(
                "How many hours should pass after last thread reply until the bot sends a reminder message to a"
                " closable thread."
            ),
            example=CloseIdleThreads.reminder_grace_period_hours,
        ),
        "close_grace_period_hours": fields.Integer(
            title="Close grace period",
            description="How many hours should pass after sending a reminder message before the bot closes the thread",
            example=CloseIdleThreads.close_grace_period_hours,
        ),
    },
    skip_none=True,
    strict=True,
)

idle_threads = idle_threads_ns.model(
    "IdleThreads",
    {
        "close_idle_threads": fields.Nested(
            idle_threads_dict,
            required=True,
            title="Idle threads config",
            description="A json containing configuration details for the idle threads functionality",
        )
    },
)

enabled_and_idle_threads = idle_threads_ns.model(
    "IdleThreadsEanbled",
    {
        "enabled": fields.Boolean(
            title="Feature enabling",
            description="Status of feature",
            example=False,
        ),
        "close_idle_threads": fields.Nested(
            idle_threads_dict,
            required=True,
            title="Idle threads config",
            description="A json containing configuration details for the idle threads functionality",
        ),
    },
)


@idle_threads_ns.route("/")
class IdleThreadsResource(Resource):
    @idle_threads_ns.doc(description="Get idle threads config and status")
    @idle_threads_ns.response(code=200, description="Feature status and config", model=enabled_and_idle_threads)
    @idle_threads_ns.response(code=404, description="Channel not found")
    @idle_threads_ns.response(code=500, description="Internal server error")
    def get(self, channel_id: str):
        cp = HelperResource.get_control_panel_or_404(channel_id)
        return channel_properties_schema.load(data=cp.channel_properties).get_feature_status_dict("close_idle_threads")

    @idle_threads_ns.doc(description="Modify idle threads config")
    @idle_threads_ns.response(code=200, description="Feature status and config", model=enabled_and_idle_threads)
    @idle_threads_ns.response(code=404, description="Channel not found")
    @idle_threads_ns.response(code=500, description="Internal server error")
    @idle_threads_ns.expect(idle_threads, validate=True)
    def post(self, channel_id: str):
        idle_threads: dict = idle_threads_ns.payload["close_idle_threads"]
        idle_threads_obj: CloseIdleThreads = close_idle_threads_schema.load(data=idle_threads)
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().update_channel_property(channel_id, "_close_idle_threads", idle_threads_obj.__dict__)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("close_idle_threads")
        )


@idle_threads_ns.route("/enable")
class IdleThreadsEnableResource(Resource):
    @idle_threads_ns.doc(description="Enable the close idle threads feature.")
    @idle_threads_ns.response(code=200, description="Feature status and config", model=enabled_and_idle_threads)
    @idle_threads_ns.response(code=404, description="Channel not found")
    @idle_threads_ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.close_idle_threads), True)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("close_idle_threads")
        )


@idle_threads_ns.route("/disable")
class IdleThreadsDisableResource(Resource):
    @idle_threads_ns.doc(description="Disable the close idle threads feature.")
    @idle_threads_ns.response(code=200, description="Feature status and config", model=enabled_and_idle_threads)
    @idle_threads_ns.response(code=404, description="Channel not found")
    @idle_threads_ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        HelperResource.get_control_panel_or_404(channel_id)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.close_idle_threads), False)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return (
            ControlPanel()
            .get_channel_properties_by_channel_id(channel_id)
            .get_feature_status_dict("close_idle_threads")
        )
