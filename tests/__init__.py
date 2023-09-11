import pytest


class FakeResource:

    def __init__(self):
        self.buffer = []

    def write(self, message):
        self.buffer.append(message)

    def query(self, message):
        self.buffer.append(message)
        return self.buffer.pop(0)

    def clear(self):
        ...


@pytest.fixture
def res():
    return FakeResource()
