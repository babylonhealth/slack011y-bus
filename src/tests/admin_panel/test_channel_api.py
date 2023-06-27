import datetime
from unittest.mock import patch

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel


class TestChannelApi:
    def test_get_active_channels(self, client, cp):
        with patch.object(ControlPanel, "get_all_active_control_panels", return_value=[cp]):
            response = client.get("/admin/api/v1/channels/")
            data = response.json
            assert response.status_code == 200
            assert data[0]["slack_channel_id"] == cp.slack_channel_id
            assert data[0]["slack_channel_name"] == cp.slack_channel_name

    def test_post_return_bad_request_required_payload_not_found(self, client):
        response = client.post("/admin/api/v1/channels/")
        assert response.status_code == 400

    def test_post_return_already_exists_and_is_active(self, client, cp):
        with patch.object(HelperResource, "get_control_panel", return_value=cp):
            response = client.post(
                "/admin/api/v1/channels/",
                json={"channel_id": cp.slack_channel_id, "channel_name": cp.slack_channel_name},
            )
            assert response.status_code == 409

    def test_post_return_activate_existing_channel(self, client, cp):
        cp.deactivation_ts = datetime.datetime.now()
        with patch.object(HelperResource, "get_control_panel", return_value=cp):
            with patch.object(ControlPanel, "activate_control_panel") as activate:
                with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp) as updated_cp:
                    response = client.post(
                        "/admin/api/v1/channels/",
                        json={"channel_id": cp.slack_channel_id, "channel_name": cp.slack_channel_name},
                    )
                    assert response.status_code == 200
                    activate.assert_called()
                    updated_cp.assert_called()

    def test_post_return_add_new_channel(self, client, cp):
        with patch.object(HelperResource, "get_control_panel", return_value=None):
            with patch.object(ControlPanel, "add_control_panel") as add_channel:
                with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp) as updated_cp:
                    response = client.post(
                        "/admin/api/v1/channels/",
                        json={"channel_id": cp.slack_channel_id, "channel_name": cp.slack_channel_name},
                    )
                    assert response.status_code == 200
                    add_channel.assert_called()
                    updated_cp.assert_called()

    def test_get_channel_return_channel(self, client, cp):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get("/admin/api/v1/channels/channel_id")
            assert response.status_code == 200
            data = response.json
            assert data["slack_channel_id"] == cp.slack_channel_id
            assert data["slack_channel_name"] == cp.slack_channel_name
            assert data["channel_properties"] == cp.channel_properties

    def test_delete_channel(self, client, cp):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "soft_delete_control_panel", return_value=None):
                response = client.delete("/admin/api/v1/channels/channel_id")
                assert response.status_code == 200
                assert response.json == {"success": "The channel has been removed successfully"}
