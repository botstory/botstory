from . import story
from .utils import match_pure_text, SimpleTrigger


def teardown_function(function):
    print('tear down!')
    story.clear()


def test_should_run_sequence_of_parts():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            trigger_1.passed()

        @story.then()
        def then(message):
            trigger_2.passed()

    match_pure_text('hi there!')

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered
