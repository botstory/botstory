import logging
import pytest
import random

from .. import chat, story
from ..utils import answer, build_fake_session, build_fake_user, SimpleTrigger

logger = logging.getLogger(__name__)


def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()


@pytest.mark.asyncio
async def test_begin_of_callable_story():
    trigger = SimpleTrigger()
    session = build_fake_session()

    @story.callable()
    def one_story():
        @story.part()
        def store_arguments(arg1, arg2):
            trigger.receive({
                'value1': arg1,
                'value2': arg2,
            })

    await one_story(arg1=1, arg2=2, session=session)

    assert trigger.result() == {
        'value1': 1,
        'value2': 2,
    }


@pytest.mark.asyncio
async def test_parts_of_callable_story():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.callable()
    def meet_ava_story():
        @story.part()
        async def ask_name(user):
            return await chat.ask(
                'My name is Ava. What is your name?',
                user=user,
            )

        @story.part()
        async def ask_age(message):
            trigger_1.passed()
            return await chat.ask(
                'Nice to see you {}. What do you do here?'.format(message['data']['text']['raw']),
                user=message['user'],
            )

        @story.part()
        async def store_arguments(message):
            age = int(message['data']['text']['raw'])
            if age < 30:
                res = 'You are so young! '
            else:
                res = 'Hm. Too old to die young'

            await chat.say(res, user=message['user'])
            trigger_2.passed()

    await meet_ava_story(user, session=session)

    await answer.pure_text('Eugene', session, user=user)
    await answer.pure_text('13', session, user=user)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered

@pytest.mark.asyncio
async def test_call_story_from_common_story():
    trigger = SimpleTrigger()

    session = build_fake_session()
    user = build_fake_user()

    @story.callable()
    def common_greeting():
        @story.part()
        async def ask_name(user):
            return await chat.ask(
                'Hi {}. How are you?'.format(user['name']),
                user=user,
            )

    @story.on('Hi!')
    def meet():
        @story.part()
        async def greeting(message):
            return await common_greeting(
                user=message['user'],
                session=message['session'],
            )

        @story.part()
        async def ask_location(message):
            return await chat.ask(
                'Which planet are we going to visit today?',
                user=message['user'],
            )

        @story.part()
        def parse(message):
            trigger.receive(message['data']['text']['raw'])

    await answer.pure_text('Hi!', session, user=user)
    await answer.pure_text('I\'m fine', session, user=user)
    await answer.pure_text('Venus, as usual!', session, user=user)

    assert trigger.value == 'Venus, as usual!'


@pytest.mark.asyncio
async def test_parts_of_callable_story_can_be_sync():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()

    @story.callable()
    def one_story():
        @story.part()
        def has():
            trigger_1.passed()

        @story.part()
        def so():
            trigger_2.passed()

    await one_story(session=session)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_call_story_from_another_callable():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()

    @story.callable()
    def one_story():
        @story.part()
        def so_1(session_1):
            pass

        @story.part()
        async def so_2(session_2):
            await another_story(session=session_2)

        @story.part()
        def so_3(session_3):
            trigger_2.passed()

    @story.callable()
    def another_story():
        @story.part()
        def has():
            pass

        @story.part()
        def so():
            trigger_1.passed()

    # push extra parameter with session
    # and it will propagate up to other story as well
    await one_story(session, session=session)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_async_end_of_story():
    sides = ['heads', 'tails']
    user = build_fake_user()
    session = build_fake_session()
    budget = SimpleTrigger(2)
    game_result = SimpleTrigger()

    @story.callable()
    def flip_a_coin():
        @story.part()
        async def choose_side(user):
            return await chat.ask('Please choose a side', user=user)

        @story.part()
        async def flip(message):
            user_side = message['data']['text']['raw']
            await chat.say('Thanks!', user=message['user'])
            await chat.say('And I am flipping a Coin', user=message['user'])
            coin_side = random.choice(sides)
            await chat.say('and got {}'.format(coin_side), user=message['user'])
            if coin_side == user_side:
                await chat.say('My greetings! You guessed!', user=message['user'])
                budget.receive(budget.value + 1)
            else:
                await chat.say('Sad but you loose!', user=message['user'])
                budget.receive(budget.value - 1)
            return story.SwitchOnValue(budget.value)

        @story.case(equal_to=0)
        def loose():
            @story.part()
            def end_of_story(message):
                return story.EndOfStory({
                    'game_result': 'loose'
                })

        @story.case(equal_to=5)
        def win():
            @story.part()
            def end_of_story(message):
                return story.EndOfStory({
                    'game_result': 'win'
                })

        @story.part()
        def tail_recursion(message):
            # TODO: add test for recursion
            # return flip_a_coin(message['user'], session)
            return story.EndOfStory({
                'game_result': 'in progress'
            })

    @story.on('enter to the saloon')
    def enter_to_the_saloon():
        @story.part()
        async def start_a_game(message):
            return await flip_a_coin(user, session=message['session'])

        @story.part()
        def game_over(message):
            logger.debug('game_over')
            logger.debug(message)
            game_result.receive(message['data']['game_result'])

    await answer.pure_text('enter to the saloon',
                     session=session, user=user)

    await answer.pure_text(random.choice(sides), session, user)

    assert game_result.result() in ['loose', 'win', 'in progress']


@pytest.mark.asyncio
async def test_sync_end_of_story():
    session = build_fake_session()

    part_1 = SimpleTrigger()
    part_2 = SimpleTrigger()
    part_3 = SimpleTrigger()

    @story.callable()
    def one_story():
        @story.part()
        def story_part_1():
            part_1.passed()

        @story.part()
        def story_part_2():
            part_2.passed()
            return story.EndOfStory('Break Point')

        @story.part()
        def story_part_3():
            part_3.passed()

    logger.debug('one_story')
    logger.debug(one_story)
    res = await one_story(session=session)

    assert part_1.is_triggered
    assert part_2.is_triggered
    assert not part_3.is_triggered
    assert res == 'Break Point'
