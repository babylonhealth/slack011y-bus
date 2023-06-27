import os

DB_USER = "DB_USER"
DB_PASSWD = "DB_PASSWD"
DB_HOST = "DB_HOST"
DB_DB = "DB_DB"
DB_PORT = "DB_PORT"
SLACK_WORKSPACE_NAME = "SLACK_WORKSPACE_NAME"
SLACK_TOKEN = "SLACK_TOKEN"
os.environ[DB_USER] = DB_USER
os.environ[DB_PASSWD] = DB_PASSWD
os.environ[DB_HOST] = DB_HOST
os.environ[DB_DB] = DB_DB
os.environ[DB_PORT] = DB_PORT
os.environ[SLACK_WORKSPACE_NAME] = SLACK_WORKSPACE_NAME
os.environ[SLACK_TOKEN] = SLACK_TOKEN

from src.code.config import Config  # noqa


def test_config():
    assert Config().db_user == DB_USER
    assert Config().db_password == DB_PASSWD
    assert Config().db_host == DB_HOST
    assert Config().db_database == DB_DB
    assert Config().db_port == DB_PORT
    assert Config().SLACK_WORKSPACE_NAME == SLACK_WORKSPACE_NAME
    assert Config().SLACK_TOKEN == SLACK_TOKEN
    assert Config().SQLALCHEMY_TRACK_MODIFICATIONS is True
    assert Config().SQLALCHEMY_DATABASE_URI == f"mysql+pymysql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
