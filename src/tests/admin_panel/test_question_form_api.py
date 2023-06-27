from unittest.mock import patch

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel
from src.code.model.control_panel_question_form import ControlPanelQuestionForm


class TestChannelApi:
    def test_get_question_forms(self, client, cp, question_forms):
        cp.channel_properties["_question_forms"] = question_forms
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/")
            assert response.status_code == 200

    def test_get_question_forms_results_404(self, client, cp, question_forms):
        cp.channel_properties["_question_forms"] = {}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/")
            assert response.status_code == 404

    def test_post_results_409_question_form_exists(self, client, cp: ControlPanel, question_forms):
        cp.channel_properties["_question_forms"] = question_forms
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.post(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/")
            assert response.status_code == 409

    def test_post_results_create_form(self, client, cp: ControlPanel):
        cp.channel_properties["_question_forms"] = {}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanelQuestionForm, "create_question_form", return_value=None):
                response = client.post(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/")
                assert response.status_code == 200

    def test_post_results_500(self, client, cp: ControlPanel):
        cp.channel_properties["_question_forms"] = {}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.post(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/")
            assert response.status_code == 500

    def test_put_modify_form_results_400_wrong_input(self, client, cp: ControlPanel, question_forms):
        response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/")
        assert response.status_code == 400

    def test_put_modify_form_results_200(self, client, cp: ControlPanel, question_forms):
        input_api = {"form_title": "title", "triggers": ["emoji"]}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanelQuestionForm, "modify_question_form", return_value=None) as modify:
                response = client.put(
                    f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/", json=input_api
                )
                modify.assert_called_with(cp=cp, triggers=["emoji"], form_title="title")
            assert response.status_code == 200

    def test_put_modify_form_results_500(self, client, cp: ControlPanel, question_forms):
        input_api = {"form_title": "title", "triggers": ["emoji"]}
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.put(
                f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/", json=input_api
            )
            assert response.status_code == 500

    def test_get_questions(self, client, cp, question_forms):
        cp.channel_properties["_question_forms"] = question_forms
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get(
                f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/"
                f"questions/{question_forms['questions'][0]['name']}"
            )
            assert response.status_code == 200

    def test_put_modify_questions_results_400(self, client, cp, question_forms):
        response = client.put(
            f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/"
            f"questions/{question_forms['questions'][0]['name']}"
        )
        assert response.status_code == 400

    def test_put_modify_questions_results_200(self, client, cp, question_forms):
        input_api = {
            "action_id": "action_id",
            "question_title": "question_1",
            "options_title": "options_1",
            "options": [{"default": ["option_1", "option_2"]}],
        }
        cp.channel_properties["_question_forms"] = question_forms
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanelQuestionForm, "modify_question", return_value=None) as modify:
                response = client.put(
                    (
                        f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/"
                        f"questions/{question_forms['questions'][0]['name']}"
                    ),
                    json=input_api,
                )
                modify.assert_called()
                assert response.status_code == 200

    def test_get_recommendations_results_500(self, client, cp, question_forms):
        cp.channel_properties["_question_forms"] = question_forms
        response = client.get(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/recommendations")
        assert response.status_code == 500

    def test_get_recommendations_results_200(self, client, cp, question_forms):
        cp.channel_properties["_question_forms"] = question_forms
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get(
                f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/recommendations"
            )
            assert response.status_code == 200

    def test_modify_recommendations_results_400_wrong_input(self, client, cp, question_forms):
        cp.channel_properties["_question_forms"] = question_forms
        response = client.put(f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/recommendations")
        assert response.status_code == 400

    def test_modify_recommendations_results_200(self, client, cp, question_forms):
        cp.channel_properties["_question_forms"] = question_forms
        input_api = {
            "option_1": {
                "docs": {"recommendations": [{"name": "rec1", "link": "link1"}]},
                "access": {"recommendations": [{"name": "rec1", "link": "link1"}]},
            }
        }
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanelQuestionForm, "modify_recommendation", return_value=None):
                response = client.put(
                    f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/recommendations",
                    json=input_api,
                )
                assert response.status_code == 200

    def test_get_specific_recommendations_results_200(self, client, cp, question_forms):
        question_forms["recommendations"] = {
            "option_1": {
                "docs": {"recommendations": [{"name": "rec1", "link": "link1"}]},
                "access": {"recommendations": [{"name": "rec1", "link": "link1"}]},
            }
        }
        cp.channel_properties["_question_forms"] = question_forms
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            response = client.get(
                f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/recommendations/option_1"
            )
            assert response.status_code == 200

    def test_modify_specific_recommendations_results_200(self, client, cp, question_forms):
        question_forms["recommendations"] = {
            "option_1": {
                "docs": {"recommendations": [{"name": "rec1", "link": "link1"}]},
                "access": {"recommendations": [{"name": "rec1", "link": "link1"}]},
            }
        }
        cp.channel_properties["_question_forms"] = question_forms
        with patch.object(HelperResource, "get_control_panel_or_404", return_value=cp):
            with patch.object(ControlPanelQuestionForm, "delete_recommendation", return_value=None):
                response = client.delete(
                    f"/admin/api/v1/channels/{cp.slack_channel_id}/actions/question_forms/recommendations/option_1"
                )
                assert response.status_code == 200
