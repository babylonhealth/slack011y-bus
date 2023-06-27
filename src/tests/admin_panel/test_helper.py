from unittest.mock import patch

import pytest
from werkzeug.exceptions import Conflict
from werkzeug.exceptions import NotFound

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel


class TestHelperResource:
    def test_get_control_panel_or_404_return_cp(self, channel_id, cp):
        with patch.object(ControlPanel, "get_active_control_panel_details", return_value=cp):
            with patch("flask_restx.abort") as test:
                assert cp == HelperResource.get_control_panel_or_404(channel_id)
                test.assert_not_called()

    def test_get_control_panel_or_404_return_404(self, channel_id):
        with patch.object(ControlPanel, "get_active_control_panel_details", return_value=None):
            with pytest.raises(NotFound):
                HelperResource.get_control_panel_or_404(channel_id)

    def test_get_control_panel_or_409_return_409(self, channel_id, cp):
        with patch.object(ControlPanel, "get_control_panel_by_channel_id", return_value=cp):
            with pytest.raises(Conflict):
                HelperResource.get_control_panel_or_409(channel_id)

    def test_get_channel_properties_object_or_404_return_channel_properties(self, channel_id, cp):
        with patch.object(ControlPanel, "get_active_control_panel_details", return_value=cp):
            with patch("flask_restx.abort") as test:
                HelperResource.get_channel_properties_object_or_404(channel_id)
                test.assert_not_called()

    def test_get_channel_properties_object_from_cp_return_channel_properties(self, cp):
        assert HelperResource.get_channel_properties_object_from_cp(cp) is not None
