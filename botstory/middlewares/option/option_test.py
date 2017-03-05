from botstory.middlewares import option
import logging
import pytest
from . import option
from ... import matchers
from ...utils import answer, SimpleTrigger

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_should_ask_with_options():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('How are you?')
        def one_story():
            @story.part()
            async def ask(ctx):
                return await story.ask(
                    'I feel fine. How about you?',
                    options=[{
                        'title': 'Good!',
                        'payload': {'health': 1},
                    }, {
                        'title': 'Ugly!',
                        'payload': {'health': -1},
                    }, {
                        'title': 'As usual',
                        'payload': {'health': 0},
                    }],
                    user=ctx['user'],
                )

            @story.part()
            def get_health(ctx):
                trigger.receive(option.get_option(ctx))

        await talk.pure_text('How are you?')
        await talk.option({'health': 1})
        assert trigger.result() == {'health': 1}


@pytest.mark.asyncio
async def test_validate_option():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(receive=option.Any())
        def one_story():
            @story.part()
            def store_option(ctx):
                trigger.passed()

        await talk.option({'engine': 'start'})
        assert trigger.is_triggered


@pytest.mark.asyncio
async def test_discard_not_valid_text_message():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(receive=option.Any())
        def one_story():
            @story.part()
            def store_option(ctx):
                trigger.passed()

        await talk.pure_text('Start engine!')
        assert not trigger.is_triggered


def test_serialize_option_match():
    m_old = option.Match('yellow')
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, option.Match)
    assert m_new.option == m_old.option


@pytest.mark.asyncio
async def test_validate_only_option():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(receive=option.Match('green'))
        def one_story():
            @story.part()
            def store_option(ctx):
                trigger.passed()

        await talk.option('green')
        assert trigger.is_triggered


def test_serialize_on_start_option():
    m_old = option.OnStart()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, option.OnStart)
