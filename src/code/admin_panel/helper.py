from typing import Optional

from flask_restx import abort

from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import channel_properties_schema


class HelperResource:
    @classmethod
    def get_control_panel(cls, channel_id: str) -> Optional[ControlPanel]:
        return ControlPanel().get_control_panel_by_channel_id(channel_id)

    @classmethod
    def get_control_panel_or_404(cls, channel_id: str) -> Optional[ControlPanel]:
        cp: ControlPanel = ControlPanel().get_active_control_panel_details(channel_id)
        if not cp:
            abort(404, description=f"channel with id {channel_id} not found")
            return None
        return cp

    @classmethod
    def get_control_panel_or_409(cls, channel_id: str) -> None:
        if cls.get_control_panel(channel_id):
            abort(409, description=f"channel with id {channel_id} already exists and is active")

    @classmethod
    def get_channel_properties_object_or_404(cls, channel_id: str) -> ChannelProperties:
        return channel_properties_schema.load(cls.get_control_panel_or_404(channel_id).channel_properties)

    @classmethod
    def get_channel_properties_object_from_cp(cls, cp: ControlPanel) -> ChannelProperties:
        return channel_properties_schema.load(cp.channel_properties)
