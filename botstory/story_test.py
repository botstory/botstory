import asyncio
import logging
import pytest

from . import chat, story
from .integrations import mockdb, mockhttp
from .middlewares import location, text
from .utils import answer, build_fake_session, build_fake_user, SimpleTrigger

logger = logging.getLogger(__name__)


def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()


@pytest.mark.asyncio
async def test_should_run_sequence_of_parts():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    user = build_fake_user()
    session = build_fake_session()

    @story.on('hi there!')
    def one_story():
        @story.part()
        def then(message):
            trigger_1.passed()

        @story.part()
        def then(message):
            trigger_2.passed()

    await answer.pure_text('hi there!', session, user)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_should_wait_for_answer_on_ask():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.part()
        async def then(message):
            return await chat.ask('How are you?', user=message['user'])

        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('hi there!', session, user)

    assert not trigger.is_triggered

    await answer.pure_text('Great!', session, user)

    assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_prevent_other_story_to_start_until_we_waiting_for_answer():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.part()
        async def then(message):
            return await chat.ask('How are you?', user=message['user'])

        @story.part()
        def then(message):
            trigger_2.passed()

    @story.on('Great!')
    def one_story():
        @story.part()
        def then(message):
            trigger_1.passed()

    await answer.pure_text('hi there!', session, user)
    await answer.pure_text('Great!', session, user)

    assert trigger_2.is_triggered
    assert not trigger_1.is_triggered


@pytest.mark.asyncio
async def test_should_start_next_story_after_current_finished():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.part()
        async def then(message):
            return await chat.ask('How are you?', user=message['user'])

        @story.part()
        def then(message):
            pass

    @story.on('Great!')
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('hi there!', session, user)
    await answer.pure_text('Great!', session, user)
    await answer.pure_text('Great!', session, user)

    assert trigger.is_triggered


@pytest.mark.asyncio
async def test_should_match_group_of_matchers_between_parts_of_story():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.part()
        def then(message):
            return [text.Any(), location.Any()]

        @story.part()
        def then(message):
            trigger_1.passed()
            return [text.Any(), location.Any()]

        @story.part()
        def then(message):
            trigger_2.passed()

    await answer.pure_text('hi there!', session, user)
    await answer.location({'lat': 1, 'lng': 1}, session, user)
    await answer.pure_text('hi there!', session, user)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_should_match_group_of_matchers_on_story_start():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on(receive=['hi there!', location.Any()])
    def one_story():
        @story.part()
        def then(message):
            trigger.passed()

    await answer.pure_text('hi there!', session, user)
    await answer.location({'lat': 1, 'lng': 1}, session, user)

    assert trigger.triggered_times == 2


@pytest.mark.asyncio
async def test_can_combine_async_with_sync_parts():
    session = build_fake_session()
    user = build_fake_user()
    async_trigger = SimpleTrigger()
    sync_trigger = SimpleTrigger()

    @story.on('yo!')
    def one_story():
        @story.part()
        async def async_part(message):
            await asyncio.sleep(1)
            async_trigger.passed()

        @story.part()
        def sync_part(message):
            sync_trigger.passed()

    await answer.pure_text('yo!', session, user)
    assert async_trigger.is_triggered
    assert sync_trigger.is_triggered


@pytest.mark.asyncio
async def test_should_start_middlewares():
    story.use(mockdb.MockDB())
    http = story.use(mockhttp.MockHttpInterface())
    await story.start()
    http.start.assert_called_once_with()
