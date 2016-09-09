from . import text
from ... import matchers, story
from ...utils import answer, build_fake_user, SimpleTrigger



def teardown_function(function):
    print('tear down!')
    story.clear()


def test_should_run_story_on_equal_message():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    answer.pure_text('hi there!', user)

    assert trigger.is_triggered


def test_should_not_run_story_on_non_equal_message():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    answer.pure_text('buy!', user)

    assert not trigger.is_triggered


def test_should_catch_any_text_message():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on(text.Any())
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    answer.pure_text('hi there!', user)

    assert trigger.is_triggered


def test_should_ignore_any_non_text_message():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on(text.Any())
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    answer.location('some where', user)

    assert not trigger.is_triggered


def test_serialize_text_any():
    m_old = text.Any()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, text.Any)
