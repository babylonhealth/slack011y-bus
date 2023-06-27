import json
from datetime import datetime
from datetime import timezone
from typing import List
from typing import Optional

import pytest
from varname import nameof

from src.code.const import SLACK_DATETIME_FMT
from src.code.db import db
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelPropertiesFeatures
from src.code.model.schemas import channel_properties_schema


class TestIntegrationControlPanel:
    def test_get_channel_name_results_channel_name_given_channel_property_exists(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        # given - table control_panel has one record
        control_panels = db.session.query(ControlPanel).all()
        assert len(control_panels) == 0
        test_control_panel_added(cp)

        # when getting channel name
        result = ControlPanel().get_channel_name(cp.slack_channel_id)

        # then channel name exists
        assert result == cp.slack_channel_name

    def test_get_channel_name_results_exception_given_channel_control_not_exists(self, db_setup, cp):
        # given - table control_panel has no records
        channels = db.session.query(ControlPanel).all()
        assert len(channels) == 0

        # when/then function raises exception
        with pytest.raises(ValueError, match=f"Property for {cp.slack_channel_id} not found"):
            ControlPanel().get_channel_name(cp.slack_channel_id)

    def test_get_channel_id_by_channel_name(self, db_setup, cp, test_control_panel_added):
        test_control_panel_added(cp)
        channels = db.session.query(ControlPanel).all()
        assert len(channels) == 1

        assert ControlPanel().get_channel_id_by_channel_name(cp.slack_channel_name) == cp.slack_channel_id

    def test_get_channel_id_by_channel_name_results_exception(self, db_setup, cp):
        with pytest.raises(ValueError, match=f"Channel for {cp.slack_channel_name} not found"):
            ControlPanel().get_channel_id_by_channel_name(cp.slack_channel_name)

    def test_get_channel_properties_by_channel_id(self, db_setup, cp: ControlPanel, test_control_panel_added):
        test_control_panel_added(cp)

        properties = ControlPanel().get_channel_properties_by_channel_id(cp.slack_channel_id)
        assert properties == channel_properties_schema.load(data=cp.channel_properties)

    def test_get_channel_properties_by_channel_id_validate_load(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        cp.channel_properties = {}
        test_control_panel_added(cp)
        properties = ControlPanel().get_channel_properties_by_channel_id(cp.slack_channel_id)
        assert properties == channel_properties_schema.load(data={})

    def test_get_channel_properties_by_channel_id_raise_when_none(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        cp.channel_properties = None
        test_control_panel_added(cp)
        with pytest.raises(Exception):
            ControlPanel().get_channel_properties_by_channel_id(cp.slack_channel_id)

    def test_get_all_active_control_panels(self, db_setup, cp, test_control_panel_added):
        # given - table control_panel has one record
        control_panels = db.session.query(ControlPanel).all()
        assert len(control_panels) == 0
        test_control_panel_added(cp)
        cp2 = ControlPanel(
            slack_channel_name=cp.slack_channel_name,
            slack_channel_id=cp.slack_channel_id,
            channel_properties=json.dumps({}),
            creation_ts=datetime.now(timezone.utc).timestamp(),
            deactivation_ts=datetime.now(timezone.utc).timestamp(),
        )
        test_control_panel_added(cp2)

        control_panels = db.session.query(ControlPanel).all()
        assert len(control_panels) == 2

        result = ControlPanel().get_all_active_control_panels()
        assert len(result) == 1
        assert result[0].deactivation_ts is None

    def test_get_control_panel_by_channel_id_return_none(self, db_setup, channel_id):
        assert ControlPanel().get_control_panel_by_channel_id(channel_id) is None

    def test_get_control_panel_by_channel_id_return_cp(self, db_setup, test_control_panel_added, channel_id, cp):
        test_control_panel_added(cp)
        result: ControlPanel = ControlPanel().get_control_panel_by_channel_id(channel_id)
        assert result is not None
        assert result.slack_channel_id == channel_id

    def test_activate_control_panel(self, db_setup, cp, test_control_panel_added):
        cp.deactivation_ts = datetime.now(timezone.utc).timestamp()
        test_control_panel_added(cp)

        ControlPanel().activate_control_panel(cp)

        result: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].slack_channel_name == cp.slack_channel_name
        assert result[0].slack_channel_id == cp.slack_channel_id
        assert result[0].deactivation_ts is None

    def test_add_control_panel_results_new_control_panel(self, cp: ControlPanel, db_setup):
        # given - table control_panel is empty
        control_panels = db.session.query(ControlPanel).all()
        assert len(control_panels) == 0

        # when adding new control panel
        ControlPanel().add_control_panel(cp.slack_channel_id, cp.slack_channel_name)

        # then new record was added
        result: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].slack_channel_name == cp.slack_channel_name
        assert result[0].slack_channel_id == cp.slack_channel_id

    def test_get_active_control_panel_details_return_channel_control(
        self, channel_id, cp: ControlPanel, db_setup, test_control_panel_added
    ):
        test_control_panel_added(cp)

        result: Optional[ControlPanel] = ControlPanel().get_active_control_panel_details(channel_id)
        assert result is not None
        assert result.id == 1
        assert result.slack_channel_name == cp.slack_channel_name
        assert result.slack_channel_id == cp.slack_channel_id
        assert result.deactivation_ts is None

    def test_get_active_control_panel_details_return_none(self, channel_id, db_setup):
        result: Optional[ControlPanel] = ControlPanel().get_active_control_panel_details(channel_id)
        assert result is None

    def test_soft_delete_channel(self, db_setup, cp: ControlPanel, test_control_panel_added):
        # given - table control_panel has one record
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert len(control_panels) == 1
        assert control_panels[0].deactivation_ts is None

        # when deleting control panel
        ControlPanel().soft_delete_control_panel(control_panel=control_panels[0])
        assert len(control_panels) == 1
        assert control_panels[0].deactivation_ts is not None

    # def test_get_channel_properties_by_channel_name(self, db_setup, cp: ControlPanel, test_control_panel_added):
    #     test_control_panel_added(cp)
    #     properties = ControlPanel().get_channel_properties_by_channel_name(cp.slack_channel_name)
    #     assert properties == channel_properties_schema.load(data=cp.channel_properties)

    def test_update_start_emojis_results_the_emoji_has_been_added(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        cp.channel_properties = {}
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert len(control_panels) == 1
        assert control_panels[0].channel_properties == {}

        emojis = ["eyes"]
        ControlPanel().update_channel_property(cp.slack_channel_id, "_start_work_reactions", emojis)
        updated_control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert len(updated_control_panels) == 1
        assert updated_control_panels[0].channel_properties["_start_work_reactions"] == emojis

    def test_toggle_feature(self, db_setup, cp: ControlPanel, test_control_panel_added):
        cp.channel_properties = {}
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert len(control_panels) == 1
        assert control_panels[0].channel_properties == {}

        ControlPanel().toggle_feature(
            control_panels[0].slack_channel_id, nameof(ChannelPropertiesFeatures.start_work_reactions), True
        )
        updated_control_panels = db.session.query(ControlPanel).all()
        assert len(updated_control_panels) == 1
        assert updated_control_panels[0].channel_properties["features"]["start_work_reactions"]["enabled"] is True
        assert updated_control_panels[0].channel_properties["features"]["types"]["enabled"] is False

    def test_get_modify_daily_report(self, db_setup, cp: ControlPanel, test_control_panel_added):
        cp.channel_properties["features"]["daily_report"] = {"enabled": True}
        cp.channel_properties["_daily_report"] = {
            "schedules": [
                {
                    "local_time": "7:00",
                    "last_report_datetime_utc": "2022-12-12 7:00",
                }
            ],
            "time_zone": "UTC",
        }
        test_control_panel_added(cp)
        cp.modify_daily_report(["8:00"], "UTC", "channel")

        updated_cp: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert updated_cp[0].channel_properties["_daily_report"]["schedules"][0]["last_report_datetime_utc"] == ""
        assert updated_cp[0].channel_properties["_daily_report"]["schedules"][0]["local_time"] == "8:00"
        assert updated_cp[0].channel_properties["_daily_report"]["time_zone"] == "UTC"
        assert updated_cp[0].channel_properties["_daily_report"]["output_channel_name"] == "channel"

    def test_update_last_report_datetime_utc_field(self, db_setup, cp, test_control_panel_added):
        cp.channel_properties["features"]["daily_report"] = {"enabled": True}
        cp.channel_properties["_daily_report"] = {
            "schedules": [
                {
                    "local_time": "7:00",
                    "last_report_datetime_utc": "2022-12-12 7:00",
                }
            ],
            "time_zone": "UTC",
        }
        test_control_panel_added(cp)
        utc_now = datetime.now()
        ControlPanel().update_last_report_datetime_utc_field(0, cp.slack_channel_id, utc_now)

        updated_cp: List[ControlPanel] = db.session.query(ControlPanel).all()
        assert updated_cp[0].channel_properties["_daily_report"]["schedules"][0][
            "last_report_datetime_utc"
        ] == utc_now.strftime(SLACK_DATETIME_FMT)

    def test_update_last_report_datetime_utc_field_result_exception(self, db_setup, cp, test_control_panel_added):
        test_control_panel_added(cp)
        utc_now = datetime.now()
        with pytest.raises(ValueError, match=f"Last report data for {cp.slack_channel_id} not updated properly"):
            ControlPanel().update_last_report_datetime_utc_field(0, cp.slack_channel_id, utc_now)
