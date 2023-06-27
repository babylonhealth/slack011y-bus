import logging
from datetime import datetime
from datetime import timezone
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import and_
from sqlalchemy.orm.attributes import flag_modified

from src.code.const import SLACK_DATETIME_FMT
from src.code.db import db
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import channel_properties_schema

logger = logging.getLogger(__name__)


class ControlPanel(db.Model):
    __tablename__ = "control_panels"

    id = Column(Integer, primary_key=True)
    slack_channel_name = Column(String(80), nullable=False)
    slack_channel_id = Column(String(64), nullable=False)
    channel_properties = Column(JSON)
    label_questions = Column(String(1000))
    form_questions = Column(JSON)
    creation_ts = Column(Numeric(16, 6), nullable=False)
    deactivation_ts = Column(Numeric(16, 6))

    def get_channel_properties_by_channel_id(self, channel_id: str) -> ChannelProperties:
        channel = self._get_control_panel_by_channel_id_or_throw_exception(channel_id)
        return channel_properties_schema.load(data=channel.channel_properties)

    def get_channel_name(self, channel_id: str) -> str:
        control_panel = self._get_control_panel_by_channel_id_or_throw_exception(channel_id)
        return control_panel.slack_channel_name

    def get_channel_id_by_channel_name(self, channel_name: str) -> str:
        control_panel = (
            db.session.query(ControlPanel).filter(ControlPanel.slack_channel_name.like(f"%{channel_name}")).first()
        )
        if control_panel is None:
            raise ValueError(f"Channel for {channel_name} not found")
        return control_panel.slack_channel_id

    def _get_control_panel_by_channel_id_or_throw_exception(self, channel_id: Optional[str]) -> "ControlPanel":
        control_panel = db.session.query(ControlPanel).filter_by(slack_channel_id=channel_id).first()
        if control_panel is None:
            raise ValueError(f"Property for {channel_id} not found")
        return control_panel

    # api
    def get_all_active_control_panels(self) -> List["ControlPanel"]:
        return db.session.query(ControlPanel).filter(ControlPanel.deactivation_ts == None).all()  # noqa: E711

    def get_control_panel_by_channel_id(self, channel_id: Optional[str]) -> "ControlPanel":
        return db.session.query(ControlPanel).filter_by(slack_channel_id=channel_id).first()

    def activate_control_panel(self, control_panel: "ControlPanel") -> None:
        control_panel.deactivation_ts = None
        db.session.commit()

    def add_control_panel(self, channel_id: str, channel_name: str) -> None:
        db.session.add(
            ControlPanel(
                slack_channel_name=channel_name,
                slack_channel_id=channel_id,
                creation_ts=datetime.now(timezone.utc).timestamp(),
                channel_properties=channel_properties_schema.dump(channel_properties_schema.load({})),
            )
        )
        db.session.commit()

    def get_active_control_panel_details(self, channel_id: str) -> Optional["ControlPanel"]:
        channel = (
            db.session.query(ControlPanel)
            .filter(
                and_(ControlPanel.slack_channel_id == channel_id, ControlPanel.deactivation_ts == None)  # noqa: E711
            )
            .first()
        )
        if not channel:
            return None
        return channel

    def soft_delete_control_panel(self, control_panel: "ControlPanel") -> None:
        control_panel.deactivation_ts = datetime.now(timezone.utc).timestamp()
        db.session.commit()

    def update_channel_property(self, channel_id: str, property: str, feature_properties: Union[Dict, List]):
        cp = self._get_control_panel_by_channel_id_or_throw_exception(channel_id)
        cp.channel_properties = channel_properties_schema.dump(
            channel_properties_schema.load(data=cp.channel_properties)
        )
        cp.channel_properties[property] = feature_properties
        flag_modified(cp, "channel_properties")
        db.session.commit()

    def toggle_feature(self, channel_id: str, feature: str, toggle: bool) -> None:
        cp = self._get_control_panel_by_channel_id_or_throw_exception(channel_id)
        cp.channel_properties = channel_properties_schema.dump(
            channel_properties_schema.load(data=cp.channel_properties)
        )
        cp.channel_properties["features"][feature]["enabled"] = toggle
        flag_modified(cp, "channel_properties")
        db.session.commit()

    def modify_daily_report(self, schedules: List[str], time_zone: str, output_channel_name: str) -> None:
        channel_properties: ChannelProperties = channel_properties_schema.load(self.channel_properties)
        if channel_properties.features.daily_report.enabled:
            channel_properties.daily_report.output_channel_name = output_channel_name
            channel_properties.daily_report.time_zone = time_zone
            channel_properties.daily_report.schedules = [
                {"local_time": x, "last_report_datetime_utc": ""} for x in schedules
            ]
            self.channel_properties = channel_properties_schema.dump(channel_properties)
            flag_modified(self, "channel_properties")
            db.session.commit()

    def update_last_report_datetime_utc_field(self, index: int, channel_id: str, utc_now: datetime):
        control_panel: ControlPanel = self._get_control_panel_by_channel_id_or_throw_exception(channel_id)
        channel_properties: ChannelProperties = channel_properties_schema.load(control_panel.channel_properties)
        if channel_properties.features.daily_report.enabled and len(channel_properties.daily_report.schedules) > 0:
            channel_properties.daily_report.schedules[index].last_report_datetime_utc = utc_now.strftime(
                SLACK_DATETIME_FMT
            )
            control_panel.channel_properties = channel_properties_schema.dump(channel_properties)
            flag_modified(control_panel, "channel_properties")
            db.session.commit()
        else:
            raise ValueError(f"Last report data for {channel_id} not updated properly")
