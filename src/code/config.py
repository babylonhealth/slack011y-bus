from src.code.utils.utils import required_envar


class Config:
    db_user = required_envar("DB_USER")
    db_password = required_envar("DB_PASSWD")
    db_host = required_envar("DB_HOST")
    db_database = required_envar("DB_DB")
    db_port = required_envar("DB_PORT")
    SLACK_WORKSPACE_NAME = required_envar("SLACK_WORKSPACE_NAME")
    SLACK_TOKEN = required_envar("SLACK_TOKEN")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
