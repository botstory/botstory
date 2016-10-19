import pytest
from . import location
from ... import matchers, story
from ...utils import answer, build_fake_session, build_fake_user, SimpleTrigger


def teardown_function(function):
    print('tear down!')
    story.stories_library.clear()


@pytest.mark.asyncio
async def test_should_trigger_on_any_location():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on(receive=location.Any())
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.location({'lat': 1, 'lng': 1}, session, user)
    assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_not_react_on_common_message():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on(receive=location.Any())
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('Hey!', session, user)

    assert not trigger.is_triggered


def test_serialize_location():
    m_old = location.Any()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, location.Any)
