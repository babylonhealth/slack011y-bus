from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields
from varname import nameof

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel
from src.code.model.control_panel_question_form import ControlPanelQuestionForm
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import ChannelPropertiesFeatures
from src.code.model.schemas import Question
from src.code.model.schemas import QuestionForm

types_description = """
List and modify question forms for a channel.
"""
ns = Namespace("question forms", description=types_description)

form_modify = ns.model(
    "QuestionFormModify",
    {
        "form_title": fields.String(example="title"),
        "triggers": fields.List(
            fields.String(
                title="Emoji name",
                description="Emoji name which triggers the form to appear on the thread",
                example="bug",
            )
        ),
    },
    strict=True,
)

form_details = ns.model(
    "QuestionFormDetails",
    {
        "feature_enable": fields.Boolean(example=True),
        "form_title": fields.String(example="tools_and_reasons", required=True),
        "triggers": fields.List(
            fields.String(
                title="Emoji name",
                description="Emoji name which triggers the form to appear on the thread",
                example="sos",
            )
        ),
        "creation_ts": fields.Float(example=datetime.now().timestamp()),
        "questions": fields.List(
            fields.String(
                title="Question name",
                example="question_1",
            )
        ),
        "recommendations": fields.List(fields.String(title="Option name", example="option_1")),
    },
)

question_details = ns.model(
    "QuestionDetails",
    {
        "action_id": fields.String(example="action_id"),
        "question_title": fields.String(example="question_1"),
        "options_title": fields.String(example="options_1"),
        "options": fields.List(
            fields.Nested(ns.model("QuestionFormOptions", dict()), example={"default": ["option_1", "option_2"]})
        ),
    },
)

recommendation = ns.model(
    "Recommendation",
    {
        "option_1": fields.Nested(
            ns.model("Recommendation", dict()),
            example={
                "docs": {"recommendations": [{"name": "rec1", "link": "link1"}]},
                "access": {"recommendations": [{"name": "rec1", "link": "link1"}]},
            },
        )
    },
)


def get_question_or_404(cp: ChannelProperties, question_name: str) -> Optional[Question]:
    questions: List[Question] = cp.question_forms.questions
    question = next((question for question in questions if question.name == question_name), None)
    if not question:
        abort(404, description=f"Question with name {question_name} not found")
    return question


def get_recommendation(cp: ChannelProperties, recommendation_name: str) -> Optional[Dict]:
    recommendations: Dict = cp.question_forms.recommendations
    return {recommendation_name: recommendations.get(recommendation_name)}


def get_recommendation_list(cp: ChannelProperties) -> Dict:
    return cp.question_forms.recommendations


def get_form_details(cp: ChannelProperties) -> Optional[Dict]:
    question_forms: QuestionForm = cp.question_forms
    try:
        return {
            "feature_enable": cp.features.question_form.enabled,
            "form_title": question_forms.form_title,
            "triggers": question_forms.triggers,
            "questions": [q.name for q in question_forms.questions],
            "recommendations": [k for k in question_forms.recommendations.keys()],
            "creation_ts": question_forms.creation_ts,
        }
    except Exception:
        abort(404, description="Question form not found, use post method to create one")
        return None


def get_question_details(question: Question) -> Dict:
    return {
        "action_id": question.action_id,
        "question_title": question.question_title,
        "options_title": question.options_title,
        "options": question.options,
    }


def is_question_form_exist(cp: ControlPanel) -> None:
    if cp.channel_properties["_question_forms"] is None or cp.channel_properties["_question_forms"] == {}:
        abort(404, description="Question form not found")


def is_recommendation_exist(properties: ChannelProperties, recommendation_name: str) -> None:
    if not properties.question_forms.recommendations.get(recommendation_name):
        abort(404, description="Recommendation not found")


@ns.route("/")
class QuestionFormsResource(Resource):
    @ns.doc(description="Getting form details for selected form and channel")
    @ns.response(code=200, description="Data fetched successfully", model=form_details)
    @ns.response(code=404, description="Channel or form not found")
    def get(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        if cp.channel_properties.get("_question_forms") is None or cp.channel_properties.get("_question_forms") == {}:
            abort(404, description="Question form not found")
            return
        return get_form_details(HelperResource.get_channel_properties_object_from_cp(cp))

    @ns.doc(description="Creating question form")
    @ns.response(code=200, description="Creation completed", model=form_details)
    @ns.response(code=404, description="Channel not found")
    @ns.response(code=409, description="Question form exists")
    def post(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        if cp.channel_properties.get("_question_forms") is not None and cp.channel_properties["_question_forms"] != {}:
            abort(409, description="Question form already has been created, use put method for modifying")
        try:
            ControlPanelQuestionForm().create_question_form(cp)
            return get_form_details(HelperResource.get_channel_properties_object_or_404(channel_id))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")

    @ns.doc(description="Modify question form for channel")
    @ns.response(code=200, description="Modification completed", model=form_details)
    @ns.response(code=404, description="Channel not found")
    @ns.expect(form_modify, validate=True)
    def put(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        triggers = ns.payload.get("triggers")
        form_title = ns.payload.get("form_title")
        try:
            ControlPanelQuestionForm().modify_question_form(cp=cp, triggers=triggers, form_title=form_title)
            return get_form_details(HelperResource.get_channel_properties_object_or_404(channel_id))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")


@ns.route("/enable")
class QuestionFormsEnableResource(Resource):
    @ns.doc(description="Enable the close question form feature.")
    @ns.response(code=200, description="Feature status and config", model=form_details)
    @ns.response(code=404, description="Channel not found")
    def put(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        is_question_form_exist(cp)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.question_form), True)
            return get_form_details(HelperResource.get_channel_properties_object_or_404(channel_id))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")


@ns.route("/disable")
class QuestionFormsDisableResource(Resource):
    @ns.doc(description="Disable the close question form feature.")
    @ns.response(code=200, description="Feature status and config", model=form_details)
    @ns.response(code=404, description="Channel not found")
    def put(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        is_question_form_exist(cp)
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.question_form), False)
            return get_form_details(HelperResource.get_channel_properties_object_or_404(channel_id))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")


@ns.route("/questions/<string:question_name>")
class QuestionsResource(Resource):
    @ns.doc(description="Getting question details for selected channel")
    @ns.response(code=200, description="Data fetched successfully", model=question_details)
    @ns.response(code=404, description="Channel, form or question not found")
    def get(self, channel_id: str, question_name: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        is_question_form_exist(cp)
        try:
            channel_properties: ChannelProperties = HelperResource.get_channel_properties_object_or_404(channel_id)
            return get_question_details(get_question_or_404(channel_properties, question_name))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")

    @ns.doc(description="Modifying selected question for selected channel")
    @ns.response(code=200, description="Modifying selected question", model=question_details)
    @ns.response(code=404, description="Channel, form or question not found")
    @ns.expect(question_details, validate=True)
    def put(self, channel_id: str, question_name: str):
        action_id = ns.payload.get("action_id")
        question_title = ns.payload.get("question_title")
        options_title = ns.payload.get("options_title")
        options = ns.payload.get("options")
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        if cp.channel_properties["_question_forms"] is None or cp.channel_properties["_question_forms"] == {}:
            abort(404, description="Question form not found")
        try:
            question: Question = get_question_or_404(
                HelperResource.get_channel_properties_object_from_cp(cp), question_name
            )
            ControlPanelQuestionForm().modify_question(
                cp=cp,
                question=question,
                action_id=action_id,
                question_title=question_title,
                options_title=options_title,
                options=options,
            )
            updated_cp: ChannelProperties = HelperResource.get_channel_properties_object_or_404(channel_id)
            return get_question_details(get_question_or_404(updated_cp, question_name))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")


@ns.route("/recommendations")
class RecommendationsResource(Resource):
    @ns.doc(description="Getting recommendations for selected channel")
    @ns.response(code=200, description="Data fetched successfully", model=recommendation)
    @ns.response(code=404, description="Channel or form not found")
    def get(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        is_question_form_exist(cp)
        try:
            channel_properties: ChannelProperties = HelperResource.get_channel_properties_object_or_404(channel_id)
            return get_recommendation_list(channel_properties)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")

    @ns.doc(description="Adding or editing recommendation")
    @ns.response(code=200, description="Recommendation modified successfully", model=recommendation)
    @ns.response(code=404, description="Channel or recommendation not found")
    @ns.expect(recommendation, validate=True)
    def put(self, channel_id: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        is_question_form_exist(cp)
        try:
            ControlPanelQuestionForm().modify_recommendation(cp, ns.payload)
            updated_cp: ChannelProperties = HelperResource.get_channel_properties_object_or_404(channel_id)
            return get_recommendation_list(updated_cp)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")


@ns.route("/recommendations/<string:recommendation_name>")
class RecommendationResource(Resource):
    @ns.doc(description="Getting particular recommendation for selected channel")
    @ns.response(code=200, description="Data fetched successfully", model=recommendation)
    @ns.response(code=404, description="Channel or recommendation not found")
    def get(self, channel_id: str, recommendation_name: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        is_question_form_exist(cp)
        is_recommendation_exist(HelperResource.get_channel_properties_object_from_cp(cp), recommendation_name)
        try:
            channel_properties: ChannelProperties = HelperResource.get_channel_properties_object_or_404(channel_id)
            return get_recommendation(channel_properties, recommendation_name)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")

    @ns.doc(description="Deleting particular recommendation for selected channel")
    @ns.response(code=200, description="Recommendation deleted successfully", model=recommendation)
    @ns.response(code=404, description="Channel or recommendation not found")
    def delete(self, channel_id: str, recommendation_name: str):
        cp: ControlPanel = HelperResource.get_control_panel_or_404(channel_id)
        is_question_form_exist(cp)
        is_recommendation_exist(HelperResource.get_channel_properties_object_from_cp(cp), recommendation_name)
        try:
            ControlPanelQuestionForm().delete_recommendation(cp, recommendation_name)
            updated_cp: ChannelProperties = HelperResource.get_channel_properties_object_or_404(channel_id)
            return get_recommendation_list(updated_cp)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
