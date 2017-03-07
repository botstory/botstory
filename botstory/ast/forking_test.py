from botstory.ast import story_context
import json
import logging
import pytest
import random

from . import forking
from .. import matchers
from ..middlewares import location, text
from ..utils import answer, SimpleTrigger

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_cases():
    trigger_location = SimpleTrigger()
    trigger_text = SimpleTrigger()
    trigger_after_switch = SimpleTrigger()

    with answer.Talk() as talk:
        say_location = talk(answer.location)
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('Hi there!')
        def one_story():
            @story.part()
            async def start(ctx):
                await story.say('Where do you go?', user=ctx['user'])
                return forking.Switch({
                    'location': location.Any(),
                    'text': text.Any(),
                })

            @story.case(match='location')
            def location_case():
                @story.part()
                def store_location(ctx):
                    trigger_location.receive(story_context.get_message_data(ctx))

            @story.case(match='text')
            def text_case():
                @story.part()
                def store_text(ctx):
                    trigger_text.receive(text.get_text(ctx)['raw'])

            @story.part()
            def after_switch(ctx):
                trigger_after_switch.passed()

        await say_pure_text('Hi there!')
        await say_location({'x': 123, 'y': 321})

        assert trigger_location.result() == {
            'location': {'x': 123, 'y': 321}
        }
        assert not trigger_text.result()
        assert trigger_after_switch.is_triggered


@pytest.mark.asyncio
async def test_sync_value():
    trigger_start = SimpleTrigger()
    trigger_heads = SimpleTrigger()
    trigger_tails = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('Flip a coin!')
        def one_story():
            @story.part()
            def start(message):
                coin = random.choice(['heads', 'tails'])
                assert not trigger_start.is_triggered
                assert not trigger_heads.is_triggered
                assert not trigger_tails.is_triggered
                trigger_start.passed()
                return forking.SwitchOnValue(coin)

            @story.case(equal_to='heads')
            def heads():
                @story.part()
                def store_heads(message):
                    assert not trigger_heads.is_triggered
                    trigger_heads.passed()

            @story.case(equal_to='tails')
            def tails():
                @story.part()
                def store_tails(message):
                    assert not trigger_tails.is_triggered
                    trigger_tails.passed()

        await say_pure_text('Flip a coin!')

        assert trigger_heads.is_triggered != trigger_tails.is_triggered


@pytest.mark.asyncio
async def test_few_switches_in_one_story():
    trigger_heads = SimpleTrigger()
    trigger_heads.receive(0)
    trigger_tails = SimpleTrigger()
    trigger_tails.receive(0)

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('Flip a coin!')
        def one_story():
            @story.part()
            def start_0(ctx):
                coin = random.choice(['heads', 'tails'])
                return forking.SwitchOnValue(coin)

            @story.case(equal_to='heads')
            def heads_0():
                @story.part()
                def store_heads(ctx):
                    trigger_heads.receive(trigger_heads.value + 1)

            @story.case(equal_to='tails')
            def tails_0():
                @story.part()
                def store_tails(ctx):
                    trigger_tails.receive(trigger_tails.value + 1)

            @story.part()
            def start_1(ctx):
                assert trigger_heads.value + trigger_tails.value == 1
                coin = random.choice(['heads', 'tails'])
                return forking.SwitchOnValue(coin)

            @story.case(equal_to='heads')
            def heads_1():
                @story.part()
                def store_heads(ctx):
                    trigger_heads.receive(trigger_heads.value + 1)

            @story.case(equal_to='tails')
            def tails_1():
                @story.part()
                def store_tails(ctx):
                    trigger_tails.receive(trigger_tails.value + 1)

        await say_pure_text('Flip a coin!')

        assert trigger_heads.value + trigger_tails.value == 2


@pytest.mark.asyncio
async def test_default_sync_value():
    trigger_1 = SimpleTrigger()
    trigger_default = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('Roll the dice!')
        def one_story_1():
            @story.part()
            def start(ctx):
                side = random.randint(1, 6)
                return forking.SwitchOnValue(side)

            @story.case(equal_to=1)
            def side_1():
                @story.part()
                def store_1(ctx):
                    trigger_1.passed()

            @story.case(default=True)
            def other_sides():
                @story.part()
                def store_other(ctx):
                    trigger_default.passed()

        await say_pure_text('Roll the dice!')

        assert trigger_1.is_triggered != trigger_default.is_triggered


@pytest.mark.asyncio
async def test_one_sync_switch_inside_of_another_sync_switch():
    visited_rooms = SimpleTrigger(0)

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('enter')
        def labyrinth():
            @story.part()
            def enter(ctx):
                turn = random.choice(['left', 'right'])
                visited_rooms.receive(visited_rooms.value + 1)
                return forking.SwitchOnValue(turn)

            @story.case(equal_to='left')
            def room_1():
                @story.part()
                def next_room_1(ctx):
                    turn = random.choice(['left', 'right'])
                    visited_rooms.receive(visited_rooms.value + 1)
                    return forking.SwitchOnValue(turn)

                @story.case(equal_to='left')
                def room_1_1():
                    @story.part()
                    def next_room_1_1(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

                @story.case(equal_to='right')
                def room_1_2():
                    @story.part()
                    def next_room_1_2(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

            @story.case(equal_to='right')
            def room_2():
                @story.part()
                def next_room_2(ctx):
                    turn = random.choice(['left', 'right'])
                    visited_rooms.receive(visited_rooms.value + 1)
                    return forking.SwitchOnValue(turn)

                @story.case(equal_to='left')
                def room_2_1():
                    @story.part()
                    def next_room_2_1(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

                @story.case(equal_to='right')
                def room_2_2():
                    @story.part()
                    def next_room_2_2(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

        await say_pure_text('enter')

        assert visited_rooms.value == 3


@pytest.mark.asyncio
async def test_one_sync_switch_inside_of_another_sync_switch_with_failed_switch():
    exit_trigger = SimpleTrigger()
    wrong_way = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('enter')
        def labyrinth():
            @story.part()
            def enter(ctx):
                return forking.SwitchOnValue('left')

            @story.case(equal_to='left')
            def room_1():
                @story.part()
                def next_room_1(ctx):
                    return forking.SwitchOnValue('left')

                @story.case(equal_to='left')
                def room_1_1():
                    @story.part()
                    def next_room_1_1(ctx):
                        return forking.Switch({
                            'no-exit': text.Match('no-exit'),
                        })

                    @story.case(match='no-exit')
                    def room_1_1_1():
                        @story.part()
                        def next_room_1_1_1(ctx):
                            wrong_way.passed()

                @story.part()
                def room_1_2(ctx):
                    exit_trigger.passed()
                    return [text.Any()]

        @story.on('right-way')
        def alt_labyrinth():
            @story.part()
            def next_room_2(ctx):
                wrong_way.passed()

        await say_pure_text('enter')
        # should fail switch next_room_1_1 and drop to room_1_2
        # and should not be cought by alt_labyrinth

        await say_pure_text('right-way')

        assert not wrong_way.is_triggered
        assert exit_trigger.is_triggered


@pytest.mark.asyncio
@pytest.mark.skip('not implemented yet')
async def test_simplify_syntax_wait_for_any_text():
    left_trigger = SimpleTrigger()
    right_trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('enter')
        def labyrinth():
            @story.part()
            def enter(ctx):
                # TODO: !!!!!!!!!!!
                return [text.Any()]

            @story.case(equal_to='left')
            def left_room():
                @story.part()
                def left_room_passed(ctx):
                    return left_trigger.passed()

            @story.case(equal_to='right')
            def right_room():
                @story.part()
                def right_room_passed(ctx):
                    return right_trigger.passed()

        await talk.pure_text('enter')
        await talk.pure_text('right')

        assert not left_trigger.is_triggered
        assert right_trigger.is_triggered


@pytest.mark.asyncio
@pytest.mark.skip('not implemented yet')
async def test_simplify_syntax_for_case_matching():
    left_trigger = SimpleTrigger()
    right_trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('enter')
        def labyrinth():
            @story.part()
            def enter(ctx):
                return [text.Any()]

            @story.case('left')
            def left_room():
                @story.part()
                def left_room_passed(ctx):
                    return left_trigger.passed()

            @story.case('right')
            def right_room():
                @story.part()
                def right_room_passed(ctx):
                    return right_trigger.passed()

        await talk.pure_text('enter')
        await talk.pure_text('right')

        assert not left_trigger.is_triggered
        assert right_trigger.is_triggered


@pytest.mark.asyncio
@pytest.mark.skip('not implemented yet')
async def test_simplify_syntax_case_matches_previous_returned_value():
    left_trigger = SimpleTrigger()
    right_trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('enter')
        def labyrinth():
            @story.part()
            def enter(ctx):
                return 'right'

            @story.case('left')
            def left_room():
                @story.part()
                def left_room_passed(ctx):
                    return left_trigger.passed()

            @story.case('right')
            def right_room():
                @story.part()
                def right_room_passed(ctx):
                    return right_trigger.passed()

        await talk.pure_text('enter')

        assert not left_trigger.is_triggered
        assert right_trigger.is_triggered


@pytest.mark.asyncio
@pytest.mark.skip('test warn message here')
async def test_warn_on_incorrect_syntax_user_forgot_add_switch_value():
    left_trigger = SimpleTrigger()
    right_trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('enter')
        def labyrinth():
            @story.part()
            def enter(ctx):
                # TODO: !!!!!!!!!!!
                # user forgot to add switch value like:
                # return 'right'
                pass

            @story.case('left')
            def left_room():
                @story.part()
                def left_room_passed(ctx):
                    return left_trigger.passed()

            @story.case('right')
            def right_room():
                @story.part()
                def right_room_passed(ctx):
                    return right_trigger.passed()

        await talk.pure_text('enter')

        assert not left_trigger.is_triggered
        assert not right_trigger.is_triggered
        # TODO: test warn message here


@pytest.mark.asyncio
async def test_one_sync_switch_inside_of_another_async_switch():
    visited_rooms = SimpleTrigger(0)

    with answer.Talk() as talk:
        story = talk.story

        @story.on('enter')
        def labyrinth():
            @story.part()
            async def enter(ctx):
                visited_rooms.receive(visited_rooms.value + 1)
                return await story.ask('Which turn to choose?', user=ctx['user'])

            @story.part()
            def parse_direction_0(ctx):
                return forking.SwitchOnValue(text.get_text(ctx)['raw'])

            @story.case(equal_to='left')
            def room_1():
                @story.part()
                async def next_room_1(ctx):
                    visited_rooms.receive(visited_rooms.value + 1)
                    return await story.ask('Which turn to choose?', user=ctx['user'])

                @story.part()
                def parse_direction_1(ctx):
                    return forking.SwitchOnValue(text.get_text(ctx)['raw'])

                @story.case(equal_to='left')
                def room_1_1():
                    @story.part()
                    def next_room_1_1(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

                @story.case(equal_to='right')
                def room_1_2():
                    @story.part()
                    def next_room_1_2(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

            @story.case(equal_to='right')
            def room_2():
                @story.part()
                async def next_room_2(ctx):
                    visited_rooms.receive(visited_rooms.value + 1)
                    return await story.ask('Which turn to choose?', user=ctx['user'])

                @story.part()
                def parse_direction_2(ctx):
                    return forking.SwitchOnValue(text.get_text(ctx)['raw'])

                @story.case(equal_to='left')
                def room_2_1():
                    @story.part()
                    def next_room_2_1(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

                @story.case(equal_to='right')
                def room_2_2():
                    @story.part()
                    def next_room_2_2(ctx):
                        visited_rooms.receive(visited_rooms.value + 1)

        await talk.pure_text('enter')
        await talk.pure_text(random.choice(['left', 'right']))
        await talk.pure_text(random.choice(['left', 'right']))

        assert visited_rooms.value == 3


@pytest.mark.asyncio
async def test_switch_inside_of_callable_inside_of_switch():
    visited_rooms = SimpleTrigger(0)
    spell_type = SimpleTrigger()
    spell_power = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.callable()
        def cast_the_magic():
            @story.part()
            async def ask_kind_of_spell(ctx):
                return await story.ask('What kind of spell do you cast?', user=ctx['user'])

            @story.part()
            def switch_by_kind_of_spell(ctx):
                return forking.SwitchOnValue(text.get_text(ctx)['raw'])

            @story.case(equal_to='fireball')
            def fireball():
                @story.part()
                async def power_of_spell(ctx):
                    spell_type.receive(text.get_text(ctx)['raw'])
                    return await story.ask('What is the power of fireball?', user=ctx['user'])

            @story.case(equal_to='lightning')
            def lightning():
                @story.part()
                async def power_of_spell(ctx):
                    spell_type.receive(text.get_text(ctx)['raw'])
                    return await story.ask('What is the power of lightning?', user=ctx['user'])

            @story.part()
            def store_power(ctx):
                spell_power.receive(text.get_text(ctx)['raw'])

        @story.on('enter')
        def dungeon():
            @story.part()
            async def ask_direction(ctx):
                return await story.ask(
                    'Where do you go?',
                    user=ctx['user']
                )

            @story.part()
            def parser_direction(ctx):
                return forking.SwitchOnValue(text.get_text(ctx)['raw'])

            @story.case(equal_to='left')
            def room_1():
                @story.part()
                async def meet_dragon(ctx):
                    return await cast_the_magic(session=ctx['session'], user=ctx['user'])

                @story.part()
                def store_end(ctx):
                    visited_rooms.receive(visited_rooms.value + 1)

            @story.case(equal_to='right')
            def room_2():
                @story.part()
                async def meet_ogr(ctx):
                    return await cast_the_magic(user=ctx['user'], session=ctx['session'])

                @story.part()
                def store_end(ctx):
                    visited_rooms.receive(visited_rooms.value + 1)

        await say_pure_text('enter')
        await say_pure_text(random.choice(['left', 'right']))
        await say_pure_text(random.choice(['fireball', 'lightning']))
        await say_pure_text(random.choice(['light', 'strong']))

        assert visited_rooms.value == 1
        assert spell_type.value in ['fireball', 'lightning']
        assert spell_power.value in ['light', 'strong']


@pytest.mark.asyncio
async def test_switch_without_right_case():
    got_help = SimpleTrigger()
    said_goodbay = SimpleTrigger()

    with answer.Talk() as talk:
        say_pure_text = talk(answer.pure_text)
        story = talk.story

        @story.on('I do not know')
        def meet_someone():
            @story.part()
            async def ask(message):
                return await story.ask(
                    'Do you need a help?',
                    user=message['user'],
                )

            @story.part()
            def parse_result(ctx):
                return forking.SwitchOnValue(text.get_text(ctx)['raw'])

            @story.case(equal_to='yes')
            def yes():
                @story.part()
                async def lets_go(message):
                    await story.say('Let\'s google together!', message['user'])
                    got_help.passed()

            @story.part()
            async def see_you(message):
                await story.say('Nice to see you!', user=message['user'])
                said_goodbay.passed()

        await say_pure_text('I do not know')
        await say_pure_text('No')

        assert not got_help.is_triggered
        assert said_goodbay.is_triggered


def test_serialize():
    m_old = forking.Switch({
        'location': location.Any(),
        'text': text.Any(),
    })
    ready_to_store = json.dumps(matchers.serialize(m_old))
    print('ready_to_store', ready_to_store)
    m_new = matchers.deserialize(json.loads(ready_to_store))

    assert isinstance(m_new, forking.Switch)
    assert isinstance(m_new.cases['location'], type(m_old.cases['location']))
    assert isinstance(m_new.cases['text'], type(m_old.cases['text']))
