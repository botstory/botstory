import logging
import pytest
import re
from . import text
from ... import matchers
from ...utils import answer, SimpleTrigger

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_should_run_story_on_equal_message():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('hi there!')
        def one_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.pure_text('hi there!')

        assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_not_run_story_on_non_equal_message():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('hi there!')
        def one_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.pure_text('buy!')

        assert not trigger.is_triggered


@pytest.mark.asyncio
async def test_should_catch_any_text_message():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(text.Any())
        def one_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.pure_text('hi there!')

        assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_ignore_any_non_text_message():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(text.Any())
        def one_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.location('some where')

        assert not trigger.is_triggered


def test_serialize_text_any():
    m_old = text.Any()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, text.Any)


@pytest.mark.asyncio
async def test_should_catch_equal_text_message():
    trigger_hi_there = SimpleTrigger()
    trigger_see_you = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(text.Equal('hi there!'))
        def first_story():
            @story.part()
            def then(ctx):
                trigger_hi_there.passed()

        @story.on(text.Equal('see you!'))
        def second_story():
            @story.part()
            def then(ctx):
                trigger_see_you.passed()

        await talk.pure_text('see you!')

        assert not trigger_hi_there.is_triggered
        assert trigger_see_you.is_triggered


def test_equal_handle_should_create_right_type():
    assert isinstance(text.Equal.handle(''), text.Equal)


def test_serialize_text_equal():
    m_old = text.Equal('hats off')
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, text.Equal)
    assert m_new.test_string == 'hats off'


@pytest.mark.asyncio
async def test_should_catch_equal_text_message_case_in_sensitive():
    trigger_hi_there = SimpleTrigger()
    trigger_see_you = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(text.EqualCaseIgnore('hi there!'))
        def first_story():
            @story.part()
            def then(ctx):
                trigger_hi_there.passed()

        @story.on(text.EqualCaseIgnore('see you!'))
        def second_story():
            @story.part()
            def then(ctx):
                trigger_see_you.passed()

        await talk.pure_text('See You!')

        assert not trigger_hi_there.is_triggered
        assert trigger_see_you.is_triggered


def test_serialize_text_equal_case_ignore():
    m_old = text.EqualCaseIgnore('hats off')
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, text.EqualCaseIgnore)
    assert m_new.test_string == 'hats off'


@pytest.mark.asyncio
async def test_should_catch_text_message_that_match_regex():
    trigger_buy = SimpleTrigger()
    trigger_sell = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(text.Match('buy (.*)btc'))
        def one_story():
            @story.part()
            def then(ctx):
                trigger_buy.receive(text.get_text(ctx)['matches'][0])

        @story.on(text.Match('sell (.*)btc'))
        def another_story():
            @story.part()
            def then(ctx):
                trigger_sell.receive(text.get_text(ctx)['matches'][0])

        await talk.pure_text('buy 700btc')
        await talk.pure_text('sell 600btc')

        assert trigger_buy.result() == '700'
        assert trigger_sell.result() == '600'


@pytest.mark.asyncio
async def test_should_catch_text_message_that_match_regex_with_flags():
    trigger_destination = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(text.Match('going to (.*)', re.IGNORECASE))
        def one_story():
            @story.part()
            def then(ctx):
                logger.debug('ctx')
                logger.debug(ctx)
                trigger_destination.receive(text.get_text(ctx)['matches'][0])

        await talk.pure_text('Going to Pripyat')

        assert trigger_destination.result() == 'Pripyat'


def test_serialize_text_match():
    m_old = text.Match('hello (.*)', re.IGNORECASE)
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, text.Match)
    assert m_new.matcher.match('Hello Piter!')


def test_text_qual_should_handle_text():
    assert isinstance(matchers.get_validator('just pure text'), text.Equal)
