from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import Question
from src.code.model.schemas import channel_properties_schema


class TestSchemas:
    def test_is_active_question_form_empty_question_form(self, cp):
        channel_properties: ChannelProperties = channel_properties_schema.load(cp.channel_properties)
        channel_properties.features.question_form.enabled = True
        channel_properties.question_forms.questions = []
        assert channel_properties.is_active_question_form() is False

    def test_is_active_question_form_not_enabled(self, cp):
        channel_properties: ChannelProperties = channel_properties_schema.load(cp.channel_properties)
        channel_properties.features.question_form.enabled = False
        channel_properties.question_forms.questions = [Question("question1")]
        assert channel_properties.is_active_question_form() is False
