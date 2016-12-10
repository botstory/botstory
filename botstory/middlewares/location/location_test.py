import pytest
from . import location
from ... import matchers, Story
from ...utils import answer, build_fake_session, build_fake_user, SimpleTrigger

story = None


def teardown_function(function):
    print('tear down!')
    story and story.clear()


@pytest.mark.asyncio
async def test_should_trigger_on_any_location(event_loop):
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on(receive=location.Any())
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    assert not event_loop.is_closed()
    await story.start(event_loop)

    await answer.location({'lat': 1, 'lng': 1}, session, user, story)
    assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_not_react_on_common_message():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()

    @story.on(receive=location.Any())
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('Hey!', session, user, story)

    assert not trigger.is_triggered


def test_serialize_location():
    m_old = location.Any()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, location.Any)
