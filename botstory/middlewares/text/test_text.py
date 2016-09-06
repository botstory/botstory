from ... import story
from ...utils import match_pure_text, SimpleTrigger


def teardown_function(function):
    print('tear down!')
    story.clear()


def test_should_run_story_on_equal_message():
    trigger = SimpleTrigger()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    match_pure_text('hi there!')

    assert trigger.is_triggered


def test_should_not_run_story_on_non_equal_message():
    trigger = SimpleTrigger()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    match_pure_text('buy!')

    assert not trigger.is_triggered
