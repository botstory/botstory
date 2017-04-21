import logging
import pytest
import random

from botstory.ast import callable, loop, story_context
from botstory.middlewares import text
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
                data = story_context.get_user_data(ctx)
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
                    'Nice to see you {}. What do you do here?'.format(story_context.get_user_data(ctx)),
                    user=ctx['user'],
                )

            @story.part()
            async def store_arguments(ctx):
                age = int(text.get_raw_text(ctx))
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
                trigger.receive(text.get_raw_text(ctx))

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
                user_side = text.get_raw_text(ctx)
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
                game_result.receive(story_context.get_user_data(ctx)['game_result'])

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
                game_result.receive(story_context.get_user_data(ctx)['game_result'])

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


@pytest.mark.asyncio
async def test_could_just_past_context_to_callable():
    session_storage = SimpleTrigger()
    user_storage = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_story():
            @story.part()
            def one_story_part(ctx):
                session_storage.receive(ctx['session']['user_id'])
                user_storage.receive(ctx['user'])

        @story.on('hi')
        def hi_story():
            @story.part()
            async def run_one_story(ctx):
                await one_story(ctx)

        await talk.pure_text('hi')

        assert session_storage.value == talk.session['user_id']
        assert user_storage.value == talk.user


# Loop & Callable Stories


@pytest.mark.asyncio
async def test_story_loop_inside_of_callable():
    inside_of_loop = SimpleTrigger()
    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_callable():
            @story.part()
            def story_init(ctx):
                pass

            @story.loop()
            def inner_loop():
                @story.on('jump')
                def jump_story():
                    @story.part()
                    def inner_job(ctx):
                        inside_of_loop.passed()

        # TODO: add wrapper for getting result context from callable to talk
        ctx = await one_callable(session=talk.session, user=talk.user,
                                 value='Hello World!')

        talk.session = ctx.message['session']

        await talk.pure_text('jump')

        assert inside_of_loop.is_passed()


@pytest.mark.asyncio
async def test_propagate_arguments_inside_of_story_loop():
    inner_job_receive = SimpleTrigger()
    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_callable():
            @story.part()
            def story_init(ctx):
                pass

            @story.loop()
            def inner_loop():
                @story.on('jump')
                def jump_story():
                    @story.part()
                    def inner_job(ctx):
                        inner_job_receive.receive(story_context.get_user_data(ctx)['value'])

        ctx = await one_callable(session=talk.session, user=talk.user,
                                 value='Hello World!')

        # TODO: add wrapper for talk
        talk.session = ctx.message['session']

        await talk.pure_text('jump')

        assert inner_job_receive.result() == 'Hello World!'


@pytest.mark.asyncio
async def test_exit_outside_of_callable_and_loop():
    exit_inside_callable_trigger = SimpleTrigger(0)
    in_progress_inside_callable_trigger = SimpleTrigger(0)
    in_progress_outside_callable_trigger = SimpleTrigger(0)
    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_callable():
            @story.part()
            def inner_init(ctx):
                pass

            @story.loop()
            def inner_loop():
                @story.on('in-progress')
                def in_progress():
                    @story.part()
                    def do_in_progress(ctx):
                        in_progress_inside_callable_trigger.inc()

                @story.on('exit')
                def exit():
                    @story.part()
                    def break_loop(ctx):
                        exit_inside_callable_trigger.inc()
                        return loop.BreakLoop()

        @story.on('start')
        def start_story():
            @story.part()
            async def call_callable(ctx):
                return await one_callable(ctx)

        @story.on('in-progress')
        def in_progress_outside_callable():
            @story.part()
            async def in_progress_outside_callable_store(ctx):
                in_progress_outside_callable_trigger.inc()

        await talk.pure_text('start')
        await talk.pure_text('in-progress')
        await talk.pure_text('exit')
        await talk.pure_text('in-progress')

        assert exit_inside_callable_trigger.result() == 1
        assert in_progress_inside_callable_trigger.result() == 1
        assert in_progress_outside_callable_trigger.result() == 1


@pytest.mark.asyncio
async def test_exit_outside_of_callable_and_loop_but_do_not_match_again():
    exit_outside_callable_trigger = SimpleTrigger(0)
    with answer.Talk() as talk:
        story = talk.story

        @story.callable()
        def one_callable():
            @story.part()
            def inner_init(ctx):
                pass

            @story.loop()
            def inner_loop():
                @story.on('in-progress')
                def in_progress():
                    @story.part()
                    def do_in_progress(ctx):
                        pass

                @story.on('exit')
                def exit():
                    @story.part()
                    def break_loop(ctx):
                        return loop.BreakLoop()

        @story.on('start')
        def start_story():
            @story.part()
            async def call_callable(ctx):
                return await one_callable(ctx)

        @story.on('exit')
        def exit_outside_callable():
            @story.part()
            async def exit_outside_callable_store(ctx):
                exit_outside_callable_trigger.inc()

        await talk.pure_text('start')
        await talk.pure_text('in-progress')
        await talk.pure_text('exit')

        assert exit_outside_callable_trigger.result() == 0
