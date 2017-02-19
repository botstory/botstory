import pytest
from . import location
from ... import matchers
from ...utils import answer, SimpleTrigger


@pytest.mark.asyncio
async def test_should_trigger_on_any_location(event_loop):
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(receive=location.Any())
        def one_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        assert not event_loop.is_closed()
        await story.start(event_loop)

        await talk.location({'lat': 1, 'lng': 1})
        assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_not_react_on_common_message():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(receive=location.Any())
        def one_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.pure_text('Hey!')

        assert not trigger.is_triggered


def test_serialize_location():
    m_old = location.Any()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, location.Any)
