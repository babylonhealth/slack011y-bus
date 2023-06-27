from enum import Enum


class RequestStatusEnum(Enum):
    NEW_RECORD = "INITIAL"
    WORKING = "WORKING"
    COMPLETED = "COMPLETED"


class MessageGroup(Enum):
    NEW = "NEW"
    EDIT = "EDIT"


class MessageType(Enum):
    MAIN_NEW = "MAIN_NEW"
    MAIN_NEW_FILE = "MAIN_NEW_FILE"
    MAIN_EDIT = "MAIN_EDIT"
    THREAD_EDIT = "THREAD_EDIT"
    THREAD_NEW = "THREAD_NEW"
    THREAD_NEW_FILE = "THREAD_NEW_FILE"
    REACTION_ADD = "REACTION_ADD"
    REACTION_REMOVE = "REACTION_REMOVE"
    MAIN_REMOVE = "MAIN_REMOVE"


class QuestionState(Enum):
    NEW = "NEW"
    WORKING = "WORKING"


class AutocloseStatus(Enum):
    REMINDER = "REMINDER"
    CLOSED = "CLOSED"
