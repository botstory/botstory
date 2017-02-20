import logging
import pytest
import random

from botstory.ast import callable
from .. import EndOfStory, SwitchOnValue
from ..utils import answer, SimpleTrigger

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_begin_of_callable_story():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_story():
            @story.part()
            def store_arguments(ctx):
                data = ctx['data']
                trigger.receive({
                    'value1': data['arg1'],
                    'value2': data['arg2'],
                })

        await one_story(arg1=1, arg2=2, session=talk.session, user=talk.user)

        assert trigger.result() == {
            'value1': 1,
            'value2': 2,
        }


@pytest.mark.asyncio
async def test_parts_of_callable_story():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def meet_ava_story():
            @story.part()
            async def ask_name(ctx):
                return await story.ask(
                    'My name is Ava. What is your name?',
                    user=ctx['user'],
                )

            @story.part()
            async def ask_age(ctx):
                trigger_1.passed()
                return await story.ask(
                    'Nice to see you {}. What do you do here?'.format(ctx['data']['text']['raw']),
                    user=ctx['user'],
                )

            @story.part()
            async def store_arguments(ctx):
                age = int(ctx['data']['text']['raw'])
                if age < 30:
                    res = 'You are so young! '
                else:
                    res = 'Hm. Too old to die young'

                await story.say(res, user=ctx['user'])
                trigger_2.passed()

        ctx = await meet_ava_story(session=talk.session, user=talk.user)
        talk.init_by_ctx(ctx)

        await talk.pure_text('Eugene')
        await talk.pure_text('13')

        assert trigger_1.is_triggered
        assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_call_story_from_common_story():
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.callable()
        def common_greeting():
            @story.part()
            async def ask_name(ctx):
                return await story.ask(
                    'Hi {}. How are you?'.format(ctx['user']['name']),
                    user=ctx['user'],
                )

        @story.on('Hi!')
        def meet():
            @story.part()
            async def greeting(ctx):
                return await common_greeting(
                    user=ctx['user'],
                    session=ctx['session'],
                )

            @story.part()
            async def ask_location(ctx):
                return await story.ask(
                    'Which planet are we going to visit today?',
                    user=ctx['user'],
                )

            @story.part()
            def parse(ctx):
                trigger.receive(ctx['data']['text']['raw'])

        await say_pure_text('Hi!')
        await say_pure_text('I\'m fine')
        await say_pure_text('Venus, as usual!')

        assert trigger.value == 'Venus, as usual!'


@pytest.mark.asyncio
async def test_parts_of_callable_story_can_be_sync():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_story():
            @story.part()
            def has(ctx):
                trigger_1.passed()

            @story.part()
            def so(ctx):
                trigger_2.passed()

        await one_story(session=talk.session, user=talk.user)

        assert trigger_1.is_triggered
        assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_call_story_from_another_callable():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_story():
            @story.part()
            def so_1(ctx):
                pass

            @story.part()
            async def so_2(ctx):
                await another_story(session=ctx['session'], user=ctx['user'])

            @story.part()
            def so_3(ctx):
                trigger_2.passed()

        @story.callable()
        def another_story():
            @story.part()
            def has(cxt):
                pass

            @story.part()
            def so(ctx):
                trigger_1.passed()
                return callable.EndOfStory()

        # push extra parameter with session
        # and it will propagate up to other story as well
        logger.debug('[!] before await one_story')
        await one_story(session=talk.session, user=talk.user)

        assert trigger_1.is_triggered
        assert trigger_2.is_triggered


@pytest.mark.asyncio
async def test_async_end_of_story_with_switch():
    sides = ['heads', 'tails']
    budget = SimpleTrigger(2)
    game_result = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def flip_a_coin():
            @story.part()
            async def choose_side(ctx):
                return await story.ask('Please choose a side', user=ctx['user'])

            @story.part()
            async def flip(ctx):
                user_side = ctx['data']['text']['raw']
                await story.say('Thanks!', user=ctx['user'])
                await story.say('And I am flipping a Coin', user=ctx['user'])
                coin_side = random.choice(sides)
                await story.say('and got {}'.format(coin_side), user=ctx['user'])
                if coin_side == user_side:
                    await story.say('My greetings! You guessed!', user=ctx['user'])
                    budget.receive(budget.value + 1)
                else:
                    await story.say('Sad but you loose!', user=ctx['user'])
                    budget.receive(budget.value - 1)
                return SwitchOnValue(budget.value)

            @story.case(equal_to=0)
            def loose():
                @story.part()
                def end_of_story(ctx):
                    return EndOfStory({
                        'game_result': 'loose'
                    })

            @story.case(equal_to=5)
            def win():
                @story.part()
                def end_of_story(ctx):
                    return EndOfStory({
                        'game_result': 'win'
                    })

            @story.part()
            def tail_recursion(ctx):
                # TODO: add test for recursion
                # return flip_a_coin(message['user'], session)
                return EndOfStory({
                    'game_result': 'in progress'
                })

        @story.on('enter to the saloon')
        def enter_to_the_saloon():
            @story.part()
            async def start_a_game(ctx):
                return await flip_a_coin(user=ctx['user'], session=ctx['session'])

            @story.part()
            def game_over(ctx):
                logger.debug('game_over')
                logger.debug(ctx)
                game_result.receive(ctx['data']['game_result'])

        await talk.pure_text('enter to the saloon')

        await talk.pure_text(random.choice(sides))

        assert game_result.result() in ['loose', 'win', 'in progress']


@pytest.mark.asyncio
@pytest.mark.skip('recursion')
async def test_async_end_of_story():
    game_result = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def flip_a_coin():
            @story.part()
            def tail_recursion(ctx):
                # TODO: add test for recursion
                # return flip_a_coin(message['user'], session)
                return EndOfStory({
                    'game_result': 'in progress'
                })

        @story.on('enter to the saloon')
        def enter_to_the_saloon():
            @story.part()
            async def start_a_game(ctx):
                return await flip_a_coin(session=ctx['session'], user=ctx['user'], )

            @story.part()
            def game_over(ctx):
                logger.debug('game_over')
                logger.debug(ctx)
                game_result.receive(ctx['data']['game_result'])

        await talk.pure_text('enter to the saloon')

        assert game_result.result() in ['loose', 'win', 'in progress']


@pytest.mark.asyncio
async def test_sync_end_of_story():
    part_1 = SimpleTrigger()
    part_2 = SimpleTrigger()
    part_3 = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_story():
            @story.part()
            def story_part_1(ctx):
                part_1.passed()

            @story.part()
            def story_part_2(ctx):
                part_2.passed()
                return EndOfStory('Break Point')

            @story.part()
            def story_part_3(ctx):
                part_3.passed()

        res = await one_story(session=talk.session, user=talk.user)

        assert part_1.is_triggered
        assert part_2.is_triggered
        assert not part_3.is_triggered
        assert res == 'Break Point'
