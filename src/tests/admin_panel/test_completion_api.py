from typing import Dict
from unittest.mock import patch

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelProperties


class TestChannelApi:
    def test_get_completion_reactions(self, client, cp):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/completion_reactions/")
            assert response.status_code == 200

    def test_post_modify_completion_reactions_results_400_wrong_request(self, cp, client):
        completions: Dict = {"types": {}}
        response = client.post(
            f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/completion_reactions/", json=completions
        )
        assert response.status_code == 400

    def test_post_modify_completion_reactions_results_200(self, client, cp, channel_properties):
        completions: Dict = {"completion_reactions": ["white_check_mark"]}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "update_channel_property") as test_update:
                with patch.object(
                    ControlPanel, "get_channel_properties_by_channel_id", return_value=channel_properties
                ) as test_fetch:
                    with patch.object(ChannelProperties, "get_feature_status_dict", return_value={}):
                        response = client.post(
                            f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/completion_reactions/",
                            json=completions,
                        )
                        assert response.status_code == 200
                        test_update.assert_called_with(
                            cp.slack_channel_id, "_completion_reactions", ["white_check_mark"]
                        )
                        test_fetch.assert_called_with(cp.slack_channel_id)
