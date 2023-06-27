import datetime

from slack import WebClient

import src.tests.test_env  # noqa

client: WebClient = WebClient(token="xoxb-BOGUS")


def test_get_data():
    time_filter = (datetime.datetime.now() - datetime.timedelta(days=7)).timestamp()
    a = client.conversations_history(channel="BOGUS_CHANNEL_ID", oldest=str(time_filter), inclusive=True, limit=200).data
    print(a)


def test_get_reply():
    time_filter = (datetime.datetime.now() - datetime.timedelta(days=7)).timestamp()
    a = client.conversations_replies(
        channel="BOGUS_CHANNEL_ID", ts=str(1668418711.414779), oldest=str(time_filter), inclusive=True
    ).data
    print(a)
