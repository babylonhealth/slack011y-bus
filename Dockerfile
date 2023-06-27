ARG APP_NAME=slacky011y_bus

FROM python:3.9-slim-buster AS REQ

ADD ./pyproject.toml /opt/$APP_NAME/pyproject.toml

WORKDIR /opt/$APP_NAME

RUN pip install poetry

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root -n -v 

FROM python:3.9-slim-buster

COPY --from=REQ /usr/local/ /usr/local/

WORKDIR /opt/$APP_NAME

ADD . /opt/$APP_NAME

EXPOSE 8000

CMD ["bash", "run.sh", "--gunicorn"]
