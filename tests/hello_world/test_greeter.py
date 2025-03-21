import pytest
from io import StringIO
import sys

from hello_world import greeter


@pytest.fixture
def capture_stdout():
    """Capture stdout for testing console output."""
    captured_output = StringIO()
    sys.stdout = captured_output
    yield captured_output
    sys.stdout = sys.__stdout__


def test_say_hello_default(capture_stdout):
    """Test say_hello with default parameter."""
    greeter.say_hello()
    assert capture_stdout.getvalue().strip() == "Hello, friend!"


def test_say_hello_with_name(capture_stdout):
    """Test say_hello with a specific name."""
    greeter.say_hello("World")
    assert capture_stdout.getvalue().strip() == "Hello, World!"
