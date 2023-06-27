from typing import Dict
from unittest.mock import patch

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel


class TestTypesApi:
    def test_get_type_for_selected_channel(self, client, cp: ControlPanel):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/")
            assert response.status_code == 200

    def test_put_results_400_types_in_request_not_found(self, client, cp: ControlPanel):
        types: Dict = {"types": {}}
        response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
        assert response.status_code == 400

    def test_put_results_409_emoji_already_exists(self, client, cp: ControlPanel):
        # adding types
        types: Dict = {
            "types": {
                "emojis": {
                    "additionalProp1": {
                        "emoji": "U+1F198",
                        "alias": "sos",
                        "image": "cloud-pr.png",
                        "color": "#619BFF",
                        "meaning": "Need help",
                    }
                }
            }
        }
        # existing types
        cp.channel_properties["_types"] = {
            "emojis": {
                "additionalProp1": {
                    "emoji": "U+1F198",
                    "alias": "sos",
                    "image": "cloud-pr.png",
                    "color": "#619BFF",
                    "meaning": "Need help",
                }
            }
        }
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
            assert response.status_code == 409

    def test_put_update_channel_types(self, client, cp: ControlPanel):
        # adding types
        types: Dict = {
            "types": {
                "emojis": {
                    "additionalProp2": {
                        "emoji": "U+1F198",
                        "alias": "sos",
                        "image": "cloud-pr.png",
                        "color": "#619BFF",
                        "meaning": "Need help",
                    }
                }
            }
        }
        # existing types
        cp.channel_properties["_types"] = {
            "emojis": {
                "additionalProp1": {
                    "emoji": "U+1F198",
                    "alias": "sos",
                    "image": "cloud-pr.png",
                    "color": "#619BFF",
                    "meaning": "Need help",
                }
            }
        }
        # expected agrument
        expected_argument = {
            "not_selected_response": "",
            "emojis": {
                "additionalProp1": {
                    "emoji": "U+1F198",
                    "alias": "sos",
                    "image": "cloud-pr.png",
                    "color": "#619BFF",
                    "meaning": "Need help",
                },
                "additionalProp2": {
                    "alias": "sos",
                    "color": "#619BFF",
                    "emoji": "U+1F198",
                    "image": "cloud-pr.png",
                    "meaning": "Need help",
                },
            },
        }
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "update_channel_property", return_value=None) as update:
                response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
                update.assert_called_with(cp.slack_channel_id, "_types", expected_argument)
                assert response.status_code == 200

    def test_put_500_during_updating(self, client, cp: ControlPanel):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.put(
                f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json={"types": {"emojis": {}}}
            )
            assert response.status_code == 500

    def test_delete_results_400_payload_not_found(self, client, cp: ControlPanel):
        types: Dict = {"wrong_payload": {}}
        response = client.delete(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
        assert response.status_code == 400

    def test_delete_results_404_emoji_not_found(self, client, cp: ControlPanel):
        # deleting type
        types: Dict = {"emoji_to_delete": ["additionalProp1"]}
        # type does not exist
        cp.channel_properties["_types"] = {"emojis": {}}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.delete(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
            assert response.status_code == 404

    def test_delete_result_type_has_been_deleted(self, client, cp: ControlPanel):
        # deleting type
        types: Dict = {"emoji_to_delete": ["additionalProp1"]}
        # type which will be deleted
        cp.channel_properties["_types"] = {"emojis": {"additionalProp1": {}}}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "update_channel_property", return_value=None):
                response = client.delete(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
                assert response.status_code == 200

    def test_delete_500_during_updating(self, client, cp: ControlPanel):
        # deleting type
        types: Dict = {"emoji_to_delete": ["additionalProp1"]}
        # type which will be deleted
        cp.channel_properties["_types"] = {"emojis": {"additionalProp1": {}}}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.delete(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
            assert response.status_code == 500

    def test_post_results_400_payload_not_found(self, client, cp: ControlPanel):
        types: Dict = {"wrong_payload": {}}
        response = client.post(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
        assert response.status_code == 400

    def test_post_results_replace_existing_type(self, client, cp: ControlPanel):
        # adding types
        types: Dict = {
            "types": {
                "not_selected_response": "You haven't selected a type for your message.",
                "emojis": {
                    "additionalProp1": {
                        "emoji": "U+1F198",
                        "alias": "sos",
                        "image": "cloud-pr.png",
                        "color": "#619BFF",
                        "meaning": "Need help",
                    }
                },
            }
        }
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "update_channel_property", return_value=None) as update:
                response = client.post(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
                update.assert_called_with(cp.slack_channel_id, "_types", types["types"])
                assert response.status_code == 200

    def test_post_results_500(self, client, cp: ControlPanel):
        # adding types
        types: Dict = {
            "types": {
                "not_selected_response": "You haven't selected a type for your message.",
                "emojis": {
                    "additionalProp1": {
                        "emoji": "U+1F198",
                        "alias": "sos",
                        "image": "cloud-pr.png",
                        "color": "#619BFF",
                        "meaning": "Need help",
                    }
                },
            }
        }
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.post(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/", json=types)
            assert response.status_code == 500

    def test_post_no_type_selected_results_400_wrong_payload(self, client, cp: ControlPanel):
        types: Dict = {"wrong_payload": {}}
        response = client.post(
            f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/no_type_selected", json=types
        )
        assert response.status_code == 400

    def test_post_no_type_selected_results_replace_existing_type(self, client, cp: ControlPanel):
        # adding types
        types: Dict = {"not_selected_response": "You haven't selected a type for your message."}

        cp.channel_properties["_types"] = {"emojis": {}}
        expected_argument = {"emojis": {}, "not_selected_response": "You haven't selected a type for your message."}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "update_channel_property", return_value=None) as update:
                response = client.post(
                    f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/no_type_selected", json=types
                )
                update.assert_called_with(cp.slack_channel_id, "_types", expected_argument)
                assert response.status_code == 200

    def test_post_no_type_selected_results_500(self, client, cp: ControlPanel):
        # adding types
        types: Dict = {"not_selected_response": "You haven't selected a type for your message."}

        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.post(
                f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/no_type_selected", json=types
            )
            assert response.status_code == 500

    def test_delete_no_type_selected_results_deleted_successfully(self, client, cp: ControlPanel):
        cp.channel_properties["_types"] = {"emojis": {}}
        expected_argument = {"not_selected_response": "", "emojis": {}}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "update_channel_property", return_value=None) as update:
                response = client.delete(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/no_type_selected")
                update.assert_called_with(cp.slack_channel_id, "_types", expected_argument)
                assert response.status_code == 200

    def test_delete_no_type_selected_results_500(self, client, cp: ControlPanel):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.delete(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/no_type_selected")
            assert response.status_code == 500

    def test_enable_results_enabled_successfully(self, client, cp: ControlPanel):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "toggle_feature", return_value=None) as update:
                response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/enable")
                update.assert_called_with(cp.slack_channel_id, "types", True)
                assert response.status_code == 200

    def test_enable_results_500(self, client, cp: ControlPanel):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/enable")
            assert response.status_code == 500

    def test_disable_results_disabled_successfully(self, client, cp: ControlPanel):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanel, "toggle_feature", return_value=None) as update:
                response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/disable")
                update.assert_called_with(cp.slack_channel_id, "types", False)
                assert response.status_code == 200

    def test_disable_results_500(self, client, cp: ControlPanel):
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/types/disable")
            assert response.status_code == 500
