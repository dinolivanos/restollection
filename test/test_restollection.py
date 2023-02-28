"""
Tests for `restollection` module.
"""
import pytest
from restollection import restollection


class ResponseTest:
    """Dummy response class"""

    def __init__(self, status_code):
        self.status_code = status_code


class MessageTest(restollection.HttpMessage):
    def __init__(self, name):
        super().__init__(name)
        self._success = True

    def pre_request(self, context):
        context.append(f"{self.name} pre")

    def post_request(self, context):
        context.append(f"{self.name} post")
        self.response = ResponseTest(status_code=200)

    def send_request(self, context):
        pass

    def success(self):
        return self._success


class CollectionTest(restollection.HttpCollection):
    def pre_request(self, context):
        context.append(f"{self.name} pre")

    def post_request(self, context):
        context.append(f"{self.name} post")


def test_http_execute():
    context = []
    message = MessageTest("test")
    message.execute(context)

    expected = ["test pre", "test post"]
    assert context == expected


def test_http_collection():
    messages = [MessageTest(f"message{i}") for i in range(3)]

    test_collection = CollectionTest("collection", collection=messages)

    context = []
    test_collection.execute(context)

    expected = []
    expected.append("collection pre")

    for i in range(3):
        expected.append(f"message{i} pre")
        expected.append(f"message{i} post")

    expected.append("collection post")
    assert context == expected


def test_nested_collection():
    messages = [MessageTest(f"message{i}") for i in range(3)]

    test_inner_collection = CollectionTest("inner", collection=messages)
    test_outer_collection = CollectionTest("outer", collection=[test_inner_collection])

    context = []
    test_outer_collection.execute(context)

    expected = []
    expected.extend(["outer pre", "inner pre"])

    for i in range(3):
        expected.append(f"message{i} pre")
        expected.append(f"message{i} post")

    expected.extend(["inner post", "outer post"])
    assert context == expected


def test_execute_summary():
    messages = [MessageTest(f"message{i}") for i in range(3)]

    test_inner_collection = CollectionTest("inner", collection=messages)
    test_outer_collection = CollectionTest("outer", collection=[test_inner_collection])

    context = []
    test_outer_collection.execute(context)

    summary = restollection.execute_summary(test_outer_collection)
    expected_result = [
        ("1.1", 200, "message0"),
        ("1.2", 200, "message1"),
        ("1.3", 200, "message2"),
    ]
    assert summary == expected_result


@pytest.mark.webtest
def test_rest_message():
    # test simple request
    message = restollection.RequestsMessage("test", "get", "https://httpbin.org")
    message.send_request({})
    assert message.success()

    # test params and headers
    message2 = restollection.RequestsMessage(
        "test",
        "get",
        "https://httpbin.org/get",
        params={"key": "value"},
        headers={"Accept": "accept: application/json"},
    )

    message2.send_request({})
    response = message2.response.json()
    assert response["args"] == {"key": "value"}


def test_stops_on_first_failure():
    messages = [MessageTest(f"message{i}") for i in range(3)]
    messages[1]._success = False

    test_inner_collection = CollectionTest("inner", collection=messages)
    test_outer_collection = CollectionTest(
        "outer", collection=[test_inner_collection, MessageTest("OuterEnd")]
    )

    context = []
    test_outer_collection.execute(context)

    expected = []
    expected.extend(["outer pre", "inner pre"])

    for i in range(2):
        expected.append(f"message{i} pre")
        expected.append(f"message{i} post")

    expected.extend(["inner post", "outer post"])
    assert context == expected
    assert test_inner_collection.success() is False
    assert test_outer_collection.success() is False
