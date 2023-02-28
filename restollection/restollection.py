import requests
from typing import Sequence


class HttpMessage:
    """Represents HTTP request/response messages"""

    def __init__(self, name):
        self.name = name
        self.response = None

    def pre_request(self, context):
        pass

    def post_request(self, context):
        pass

    def send_request(self, context):
        """Override this to do actual work"""
        raise NotImplementedError

    def success(self):
        """Contains the logic to determine if the request was successful or not"""
        raise NotImplementedError

    def execute(self, context):
        """Execute is the combination of the pre and post steps along with a send_request"""
        self.pre_request(context)
        self.send_request(context)
        self.post_request(context)


class HttpCollection(HttpMessage):
    """A set of HTTP messages to execute in squence

    If a message is not successfull the execute is aborted, post_request
    methods are still called

    """

    def __init__(self, name, collection: Sequence):
        self.name = name
        self.collection = collection
        self._success = None

    def send_request(self, context):
        for message in self.collection:
            message.execute(context)
            if not message.success():
                # If any message fails mark collection as failed and abort
                self._success = False
                return

        # No failures so we mark as success
        self._success = True

    def success(self):
        return self._success


class RequestsMessage(HttpMessage):
    """HttpMessage based on python requests package

    The constructors kwargs are passed onto the requests.request
    """

    def __init__(self, name, method, url, expected_status_code=200, **kwargs):
        super().__init__(name)
        self.method = method
        self.url = url
        self.exepected_status_code = expected_status_code
        self.args = kwargs

    def send_request(self, context):
        self.response = requests.request(self.method, self.url, **self.args)

    def success(self):
        """Success if we get the expected_status_code"""
        if self.response and self.response.status_code == self.exepected_status_code:
            return True


def execute_summary(collection, level=""):
    summary = []

    for i, message in enumerate(collection.collection, start=1):
        if isinstance(message, HttpCollection):
            collection_level = f"{level}.{i}" if level else f"{i}"
            collection_summary = execute_summary(message, collection_level)
            summary.extend(collection_summary)
        else:
            status_code = message.response.status_code if message.response else "None"
            message_level = f"{level}.{i}"
            message_summary = (f"{message_level}", status_code, message.name)
            summary.append(message_summary)

    return summary
