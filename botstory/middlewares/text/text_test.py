import pytest
from . import text
from ... import matchers, Story
from ...utils import answer, build_fake_session, build_fake_user, SimpleTrigger

story = None


def teardown_function(function):
    print('tear down!')
    story and story.clear()


@pytest.mark.asyncio
async def test_should_run_story_on_equal_message():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on('hi there!')
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('hi there!', session, user, story)

    assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_not_run_story_on_non_equal_message():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on('hi there!')
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('buy!', session, user, story)

    assert not trigger.is_triggered


@pytest.mark.asyncio
async def test_should_catch_any_text_message():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on(text.Any())
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('hi there!', session, user, story)

    assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_ignore_any_non_text_message():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on(text.Any())
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.location('some where', session, user, story)

    assert not trigger.is_triggered


@pytest.mark.asyncio
async def test_should_catch_equal_text_message():
    trigger_hi_there = SimpleTrigger()
    trigger_see_you = SimpleTrigger()

    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on(text.Equal('hi there!'))
    def one_story():
        @story.part()
        def then(ctx):
            trigger_hi_there.passed()

    @story.on(text.Equal('see you!'))
    def one_story():
        @story.part()
        def then(ctx):
            trigger_see_you.passed()

    await answer.pure_text('see you!', session, user, story)

    assert not trigger_hi_there.is_triggered
    assert trigger_see_you.is_triggered


def test_equal_handle_should_create_right_type():
    assert isinstance(text.Equal.handle(''), text.Equal)


@pytest.mark.asyncio
async def test_should_catch_equal_text_message_case_in_sensitive():
    trigger_hi_there = SimpleTrigger()
    trigger_see_you = SimpleTrigger()

    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on(text.EqualCaseIgnore('hi there!'))
    def one_story():
        @story.part()
        def then(ctx):
            trigger_hi_there.passed()

    @story.on(text.EqualCaseIgnore('see you!'))
    def one_story():
        @story.part()
        def then(ctx):
            trigger_see_you.passed()

    await answer.pure_text('See You!', session, user, story)

    assert not trigger_hi_there.is_triggered
    assert trigger_see_you.is_triggered


def test_equal_case_ignore_handle_should_create_right_type():
    assert isinstance(text.EqualCaseIgnore.handle(''), text.EqualCaseIgnore)


def test_serialize_text_any():
    m_old = text.Any()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, text.Any)
