from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List

from marshmallow_dataclass import class_schema

from src.code.logger import create_logger

logger = create_logger(__name__)


@dataclass
class ChannelPropertiesFeature:
    enabled: bool = field(default=False)


@dataclass
class ChannelPropertiesFeatures:
    types: ChannelPropertiesFeature = field(default=ChannelPropertiesFeature())
    start_work_reactions: ChannelPropertiesFeature = field(default=ChannelPropertiesFeature())
    question_form: ChannelPropertiesFeature = field(default=ChannelPropertiesFeature())
    completion_reactions: ChannelPropertiesFeature = field(default=ChannelPropertiesFeature())
    close_idle_threads: ChannelPropertiesFeature = field(default=ChannelPropertiesFeature())
    daily_report: ChannelPropertiesFeature = field(default=ChannelPropertiesFeature())


@dataclass
class CloseIdleThreads:
    reminder_message: str
    close_message: str
    scan_limit_days: int = field(default=7)
    close_after_creation_hours: int = field(default=24)
    reminder_grace_period_hours: int = field(default=12)
    close_grace_period_hours: int = field(default=24)


@dataclass()
class Question:
    name: str
    question_title: str = field(default="")
    action_id: str = field(default="")
    options_title: str = field(default="")
    options: Dict[str, list] = field(default_factory=lambda: {})


@dataclass
class QuestionForm:
    creation_ts: float = field(default=0)
    form_title: str = field(default="title")
    triggers: List[str] = field(default_factory=lambda: [])
    questions: List[Question] = field(default_factory=lambda: [])
    recommendations: Dict[str, dict] = field(default_factory=lambda: {})


@dataclass
class Types:
    emojis: Dict[str, dict] = field(default_factory=lambda: {})
    not_selected_response: str = field(default="")


@dataclass
class Schedule:
    last_report_datetime_utc: str
    local_time: str = field(default="7:00")


@dataclass
class DailyReport:
    output_channel_name: str = field(default="")
    schedules: List[Schedule] = field(default_factory=lambda: [])
    time_zone: str = field(default="UTC")


@dataclass
class ChannelProperties:
    features: ChannelPropertiesFeatures = field(default=ChannelPropertiesFeatures())
    _types: Types = field(default=Types())
    _start_work_reactions: List[str] = field(default_factory=lambda: [])
    _question_forms: QuestionForm = field(default=QuestionForm())
    _completion_reactions: List[str] = field(default_factory=lambda: [])
    _close_idle_threads: CloseIdleThreads = field(default=CloseIdleThreads(reminder_message="", close_message=""))
    _daily_report: DailyReport = field(default=DailyReport())

    @property
    def types(self):
        if self.features.types.enabled:
            return self._types
        else:
            logger.info("Feature 'types' is not enabled.")
            return Types()

    @types.setter
    def types(self, types_dict):
        self._types = types_dict

    @property
    def daily_report(self):
        if self.features.daily_report.enabled:
            return self._daily_report
        else:
            logger.info("Feature 'daily_report' is not enabled.")
            return None

    @daily_report.setter
    def daily_report(self, daily_report):
        self._daily_report = daily_report

    @property
    def start_work_reactions(self):
        if self.features.start_work_reactions.enabled:
            return self._start_work_reactions
        else:
            logger.info("Feature 'start_work_reactions' is not enabled.")
            return []

    @start_work_reactions.setter
    def start_work_reactions(self, reactions):
        self._start_work_reactions = reactions

    @property
    def question_forms(self):
        return self._question_forms

    @question_forms.setter
    def question_forms(self, forms):
        self._question_forms = forms

    def is_active_question_form(self) -> bool:
        if self.features.question_form.enabled and self.question_forms and len(self._question_forms.questions) > 0:
            return True
        return False

    @property
    def completion_reactions(self):
        if self.features.completion_reactions.enabled:
            return self._completion_reactions
        else:
            logger.info("Feature 'completion_reactions' is not enabled.")
            return []

    @completion_reactions.setter
    def completion_reactions(self, reactions):
        self._completion_reactions = reactions

    @property
    def close_idle_threads(self):
        if self.features.close_idle_threads.enabled:
            return self._close_idle_threads
        else:
            logger.info("Feature 'close_idle_threads' is not enabled.")
            return None

    @close_idle_threads.setter
    def close_idle_threads(self, close_idle_threads):
        self._close_idle_threads = close_idle_threads

    def get_feature_status_dict(self, feature_name: str) -> dict:
        self_full_dict = channel_properties_schema.dump(self)
        if feature_name not in self_full_dict["features"]:
            raise KeyError(f"Feature `{feature_name}` does not exist.")
        return {
            "enabled": self_full_dict["features"][feature_name]["enabled"],
            feature_name: self_full_dict[f"_{feature_name}"],
        }


channel_properties_schema = class_schema(ChannelProperties)()
question_form_schema = class_schema(QuestionForm)()
question_schema = class_schema(Question)()
types_schema = class_schema(Types)()
close_idle_threads_schema = class_schema(CloseIdleThreads)()
daily_report_schema = class_schema(DailyReport)()
