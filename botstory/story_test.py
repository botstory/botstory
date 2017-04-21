import asyncio
import logging
import pytest
from unittest.mock import call

from . import di
from .integrations import mockdb, mockhttp
from .middlewares import location, text
from .utils import answer, SimpleTrigger

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_should_run_sequence_of_parts():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('hi there!')
        def one_story():
            @story.part()
            def then(ctx):
                trigger_1.passed()

            @story.part()
            def then(ctx):
                trigger_2.passed()

        await talk.pure_text('hi there!')

        assert trigger_1.is_triggered
        assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_should_wait_for_answer_on_ask():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('hi there!')
        def one_story():
            @story.part()
            async def then(message):
                return await story.ask('How are you?', user=message['user'])

            @story.part()
            def then(message):
                trigger.passed()

        await say_pure_text('hi there!')

        assert not trigger.is_triggered

        await say_pure_text('Great!')

        assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_prevent_other_story_to_start_until_we_waiting_for_answer():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('hi there!')
        def first_story():
            @story.part()
            async def then_ask(ctx):
                return await story.ask('How are you?', user=ctx['user'])

            @story.part()
            async def then_trigger_2(ctx):
                trigger_2.passed()

        @story.on('Great!')
        def second_story():
            @story.part()
            def then_trigger_1(ctx):
                trigger_1.passed()

        await say_pure_text('hi there!')
        await say_pure_text('Great!')

        assert trigger_2.is_triggered
        assert not trigger_1.is_triggered


@pytest.mark.asyncio
async def test_should_start_next_story_after_current_finished():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('hi there!')
        def first_story():
            @story.part()
            async def then(ctx):
                return await story.ask('How are you?', user=ctx['user'])

            @story.part()
            def then(ctx):
                pass

        @story.on('Great!')
        def second_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.pure_text('hi there!')
        await talk.pure_text('Great!')
        await talk.pure_text('Great!')

        assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_match_group_of_matchers_between_parts_of_story():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()

    with answer.Talk() as talk:
        say_location = talk(answer.location)
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('hi there!')
        def one_story():
            @story.part()
            def then(ctx):
                return [text.Any(), location.Any()]

            @story.part()
            def then(ctx):
                trigger_1.passed()
                return [text.Any(), location.Any()]

            @story.part()
            def then(ctx):
                trigger_2.passed()

        await say_pure_text('hi there!')
        await say_location({'lat': 1, 'lng': 1})
        await say_pure_text('hi there!')

        assert trigger_1.is_triggered
        assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_should_match_group_of_matchers_on_story_start():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(receive=['hi there!', location.Any()])
        def one_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.pure_text('hi there!')
        await talk.location({'lat': 1, 'lng': 1})

        assert trigger.triggered_times == 2


@pytest.mark.asyncio
async def test_can_combine_async_with_sync_parts():
    async_trigger = SimpleTrigger()
    sync_trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('yo!')
        def one_story():
            @story.part()
            async def async_part(ctx):
                await asyncio.sleep(1)
                async_trigger.passed()

            @story.part()
            def sync_part(ctx):
                sync_trigger.passed()

        await talk.pure_text('yo!')
        assert async_trigger.is_triggered
        assert sync_trigger.is_triggered


@pytest.mark.asyncio
async def test_should_drop_session_once_found_that_it_does_not_match_current_story_structure():
    trigger = SimpleTrigger()
    another_trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('one')
        def one_story():
            @story.part()
            def async_part(ctx):
                return text.Any()

            @story.part()
            def sync_part(ctx):
                trigger.passed()

        @story.on('two')
        def another_story():
            @story.part()
            def sync_part(ctx):
                another_trigger.passed()

        await talk.pure_text('one')
        # now session differs from story struct
        talk.session['stack'][-1]['topic'] += '_'
        await talk.pure_text('two')
        assert not trigger.is_triggered
        assert another_trigger.is_triggered


@pytest.mark.asyncio
async def test_should_start_middlewares():
    with answer.Talk() as talk:
        story = talk.story
        story.use(mockdb.MockDB())
        http = story.use(mockhttp.MockHttpInterface())
        await story.start()
        http.start.assert_called_once_with()


@pytest.mark.asyncio
async def test_setup_should_config_facebook_options():
    with answer.Talk() as talk:
        story = talk.story
        db = story.use(mockdb.MockDB())
        http = story.use(mockhttp.MockHttpInterface())

        await story.setup()

        db.setup.assert_called_once_with()
        http.setup.assert_called_once_with()


@pytest.mark.asyncio
async def test_should_run_before_start_start_and_then_after_start(mocker):
    with di.child_scope():
        with answer.Talk() as talk:
            story = talk.story

            @di.desc()
            class MockExtension:
                handler = mocker.stub()

                async def before_start(self):
                    self.handler('before_start')

                async def start(self):
                    self.handler('start')

                async def after_start(self):
                    self.handler('after_start')

            ext = story.use(MockExtension())
            await story.start()
            ext.handler.assert_has_calls([
                call('before_start'),
                call('start'),
                call('after_start'),
            ])
