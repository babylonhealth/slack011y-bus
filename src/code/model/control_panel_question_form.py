import logging
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from src.code.db import db
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import Question
from src.code.model.schemas import QuestionForm
from src.code.model.schemas import channel_properties_schema
from src.code.model.schemas import question_form_schema

logger = logging.getLogger(__name__)


class ControlPanelQuestionForm:
    def create_question_form(self, cp: ControlPanel):
        properties: ChannelProperties = channel_properties_schema.load(data=cp.channel_properties)
        form: QuestionForm = QuestionForm(
            form_title="",
            triggers=[],
            creation_ts=datetime.now(timezone.utc).timestamp(),
            questions=[
                Question(
                    name="question_1",
                    question_title="question_title_1",
                    action_id="action_id_1",
                    options_title="options_title_1",
                    options={"default": ["option_1", "option_2"]},
                ),
                Question(
                    name="question_2",
                    question_title="question_title_2",
                    action_id="action_id_2",
                    options_title="options_title_2",
                    options={"default": ["option_1", "option_2"]},
                ),
            ],
            recommendations={},
        )
        properties.question_forms = question_form_schema.dump(form)
        cp.channel_properties = channel_properties_schema.dump(properties)
        db.session.commit()

    def modify_question_form(
        self,
        cp: ControlPanel,
        form_title: Optional[str] = None,
        triggers: Optional[List[str]] = None,
        questions: Optional[List] = None,
    ) -> None:
        properties: ChannelProperties = channel_properties_schema.load(data=cp.channel_properties)
        form: QuestionForm = QuestionForm(
            form_title=properties.question_forms.form_title if form_title is None else form_title,
            triggers=properties.question_forms.triggers if triggers is None else triggers,
            creation_ts=properties.question_forms.creation_ts,
            questions=properties.question_forms.questions if questions is None else questions,
            recommendations=properties.question_forms.recommendations,
        )
        properties.question_forms = question_form_schema.dump(form)
        cp.channel_properties = channel_properties_schema.dump(properties)
        db.session.commit()

    def modify_question(
        self,
        cp: ControlPanel,
        question: Question,
        action_id: str,
        question_title: str,
        options_title: str,
        options: Dict[str, Any],
    ) -> None:
        question.action_id = action_id
        question.question_title = question_title
        question.options_title = options_title
        question.options = options

        # fetching properties and form
        properties: ChannelProperties = channel_properties_schema.load(data=cp.channel_properties)

        # modifying question in the form
        fetched_questions: List[Question] = properties.question_forms.questions

        modify_question_index = next(ind for ind, q in enumerate(fetched_questions) if q.name == question.name)
        fetched_questions[modify_question_index] = question
        cp.channel_properties = channel_properties_schema.dump(properties)
        db.session.commit()

    def modify_recommendation(self, cp: ControlPanel, recommendation: Dict) -> None:
        # fetching properties and form
        properties: ChannelProperties = channel_properties_schema.load(data=cp.channel_properties)
        fetched_recommendations: Dict = properties.question_forms.recommendations

        # updating recommendations
        recommendation_key = list(recommendation.keys())[0]
        fetched_recommendations[recommendation_key] = recommendation[recommendation_key]
        cp.channel_properties = channel_properties_schema.dump(properties)
        db.session.commit()

    def delete_recommendation(self, cp: ControlPanel, recommendation_name: str) -> None:
        # fetching properties and form
        properties: ChannelProperties = channel_properties_schema.load(data=cp.channel_properties)
        fetched_recommendations: Dict = properties.question_forms.recommendations

        # updating recommendations
        del fetched_recommendations[recommendation_name]
        cp.channel_properties = channel_properties_schema.dump(properties)
        db.session.commit()
