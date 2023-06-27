from typing import Dict
from typing import List

from src.code.db import db
from src.code.model.control_panel import ControlPanel
from src.code.model.control_panel_question_form import ControlPanelQuestionForm
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import Question
from src.code.model.schemas import QuestionForm
from src.code.model.schemas import channel_properties_schema


class TestIntegrationControlPanelQuestionForm:
    def test_modify_question_form_results_new_form(self, db_setup, cp: ControlPanel, test_control_panel_added):
        control_panels = db.session.query(ControlPanel).all()
        assert len(control_panels) == 0

        cp.channel_properties = {}
        test_control_panel_added(cp)
        control_panels = db.session.query(ControlPanel).all()
        assert len(control_panels) == 1
        channel_properties: ChannelProperties = channel_properties_schema.load(control_panels[0].channel_properties)
        assert channel_properties.question_forms is not None

        ControlPanelQuestionForm().create_question_form(cp=control_panels[0])
        updated_control_panels = db.session.query(ControlPanel).all()
        updated_properties: ChannelProperties = channel_properties_schema.load(
            updated_control_panels[0].channel_properties
        )
        assert len(updated_control_panels) == 1
        updated_form: QuestionForm = updated_properties.question_forms
        assert updated_form.creation_ts is not None
        assert updated_form.triggers == []
        assert len(updated_form.questions) == 2
        assert updated_form.recommendations == {}

    def test_modify_question_form_results_whole_form_is_updated(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        empty_cp = db.session.query(ControlPanel).all()
        assert len(empty_cp) == 0

        cp.channel_properties = {
            "_question_forms": {
                "creation_ts": 11.11,
                "triggers": [],
                "questions": [],
                "recommendations": {},
            }
        }
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        channel_properties: ChannelProperties = channel_properties_schema.load(control_panels[0].channel_properties)
        assert len(control_panels) == 1
        form: QuestionForm = channel_properties.question_forms
        assert form.creation_ts == 11.11
        assert form.triggers == []
        assert len(form.questions) == 0
        assert form.recommendations == {}

        ControlPanelQuestionForm().modify_question_form(cp=control_panels[0], triggers=["eyes"], questions=[])

        updated_control_panels = db.session.query(ControlPanel).all()
        updated_properties: ChannelProperties = channel_properties_schema.load(
            updated_control_panels[0].channel_properties
        )
        assert len(updated_control_panels) == 1
        updated_form: QuestionForm = updated_properties.question_forms
        assert updated_form.creation_ts == 11.11
        assert updated_form.triggers == ["eyes"]
        assert len(updated_form.questions) == 0
        assert updated_form.recommendations == {}

    def test_modify_question_form_results_nothing_is_updated(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        empty_cp = db.session.query(ControlPanel).all()
        assert len(empty_cp) == 0

        cp.channel_properties = {
            "_question_forms": {
                "creation_ts": 11.11,
                "triggers": [],
                "questions": [],
                "recommendations": {},
            }
        }
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        channel_properties: ChannelProperties = channel_properties_schema.load(control_panels[0].channel_properties)
        assert len(control_panels) == 1
        form: QuestionForm = channel_properties.question_forms
        assert form.creation_ts == 11.11
        assert form.triggers == []
        assert len(form.questions) == 0
        assert form.recommendations == {}

        ControlPanelQuestionForm().modify_question_form(cp=control_panels[0], triggers=None, questions=None)

        updated_control_panels = db.session.query(ControlPanel).all()
        updated_properties: ChannelProperties = channel_properties_schema.load(
            updated_control_panels[0].channel_properties
        )
        assert len(updated_control_panels) == 1
        updated_form: QuestionForm = updated_properties.question_forms
        assert updated_form.creation_ts == 11.11
        assert updated_form.triggers == []

    def test_modify_question_results_question_has_been_updated(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        empty_cp = db.session.query(ControlPanel).all()
        assert len(empty_cp) == 0

        cp.channel_properties = {
            "_question_forms": {
                "creation_ts": 11.11,
                "triggers": [],
                "questions": [{"name": "question_1"}],
                "recommendations": {},
            }
        }
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()

        question: Question = Question("question_1")
        ControlPanelQuestionForm().modify_question(
            control_panels[0],
            question,
            "action",
            "question_title",
            "options_title",
            {"default": ["option_1", "option_2"]},
        )

        updated_control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        updated_properties: ChannelProperties = channel_properties_schema.load(
            updated_control_panels[0].channel_properties
        )
        updated_form: QuestionForm = updated_properties.question_forms
        assert len(updated_form.questions) == 1
        assert updated_form.recommendations == {}
        assert updated_form.questions[0].question_title == "question_title"
        assert updated_form.questions[0].action_id == "action"
        assert updated_form.questions[0].options_title == "options_title"
        assert updated_form.questions[0].options == {"default": ["option_1", "option_2"]}

    def test_modify_recommendation_results_new_recommendation_was_added(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        empty_cp = db.session.query(ControlPanel).all()
        assert len(empty_cp) == 0
        recommendation: Dict = {"Recommendation_1": {}}

        cp.channel_properties = {
            "_question_forms": {
                "creation_ts": 11.11,
                "triggers": [],
                "questions": [{"name": "question_1"}],
                "recommendations": recommendation,
            }
        }
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()

        adding_recommendation = {
            "Recommendation_2": {"Documentation": {"recommendations": [{"name": "rec1", "link": "link1"}]}}
        }

        ControlPanelQuestionForm().modify_recommendation(control_panels[0], adding_recommendation)
        updated_control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        updated_properties: ChannelProperties = channel_properties_schema.load(
            updated_control_panels[0].channel_properties
        )

        recommendation["Recommendation_2"] = adding_recommendation["Recommendation_2"]
        assert updated_properties.question_forms.recommendations == recommendation

    def test_modify_recommendations_results_recommendation_was_modified(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        empty_cp = db.session.query(ControlPanel).all()
        assert len(empty_cp) == 0
        recommendation: Dict = {"Recommendation_1": {}}

        cp.channel_properties = {
            "_question_forms": {
                "creation_ts": 11.11,
                "triggers": [],
                "questions": [{"name": "question_1"}],
                "recommendations": recommendation,
            }
        }
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()

        adding_recommendation = {
            "Recommendation_1": {"Documentation": {"recommendations": [{"name": "rec1", "link": "link1"}]}}
        }

        ControlPanelQuestionForm().modify_recommendation(control_panels[0], adding_recommendation)
        updated_control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        updated_properties: ChannelProperties = channel_properties_schema.load(
            updated_control_panels[0].channel_properties
        )
        assert updated_properties.question_forms.recommendations == adding_recommendation

    def test_delete_recommendations_results_recommendation_was_deleted(
        self, db_setup, cp: ControlPanel, test_control_panel_added
    ):
        empty_cp = db.session.query(ControlPanel).all()
        assert len(empty_cp) == 0
        recommendation_name: str = "Recommendation_1"
        recommendation: Dict = {recommendation_name: {}}

        cp.channel_properties = {
            "_question_forms": {
                "creation_ts": 11.11,
                "triggers": [],
                "questions": [{"name": "question_1"}],
                "recommendations": recommendation,
            }
        }
        test_control_panel_added(cp)
        control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        channel_properties: ChannelProperties = channel_properties_schema.load(control_panels[0].channel_properties)

        assert channel_properties.question_forms.recommendations == recommendation

        ControlPanelQuestionForm().delete_recommendation(control_panels[0], recommendation_name)
        updated_control_panels: List[ControlPanel] = db.session.query(ControlPanel).all()
        updated_properties: ChannelProperties = channel_properties_schema.load(
            updated_control_panels[0].channel_properties
        )
        assert updated_properties.question_forms.recommendations == {}
