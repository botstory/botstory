import json
import logging
import pytest
import random

logger = logging.getLogger(__name__)

from . import forking
from .. import chat, story, matchers
from ..middlewares import location, text
from ..utils import answer, build_fake_session, build_fake_user, SimpleTrigger


def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()


@pytest.mark.asyncio
async def test_cases():
    user = build_fake_user()
    session = build_fake_session()

    trigger_location = SimpleTrigger()
    trigger_text = SimpleTrigger()
    trigger_after_switch = SimpleTrigger()

    @story.on('Hi there!')
    def one_story():
        @story.part()
        async def start(message):
            await chat.say('Where do you go?', user=message['user'])
            return forking.Switch({
                'location': location.Any(),
                'text': text.Any(),
            })

        @story.case(match='location')
        def location_case():
            @story.part()
            def store_location(message):
                trigger_location.receive(message['data']['location'])

        @story.case(match='text')
        def text_case():
            @story.part()
            def store_location(message):
                trigger_text.receive(message['data']['text']['raw'])

        @story.part()
        def after_switch(message):
            trigger_after_switch.passed()

    await answer.pure_text('Hi there!', session, user)
    await answer.location({'x': 123, 'y': 321}, session, user)

    assert trigger_location.result() == {'x': 123, 'y': 321}
    assert not trigger_text.result()
    assert trigger_after_switch.is_triggered


@pytest.mark.asyncio
async def test_sync_value():
    user = build_fake_user()
    session = build_fake_session()
    trigger_start = SimpleTrigger()
    trigger_heads = SimpleTrigger()
    trigger_tails = SimpleTrigger()

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

    await answer.pure_text('Flip a coin!', session, user)

    assert trigger_heads.is_triggered != trigger_tails.is_triggered


@pytest.mark.asyncio
async def test_few_switches_in_one_story():
    user = build_fake_user()
    session = build_fake_session()
    trigger_heads = SimpleTrigger()
    trigger_heads.receive(0)
    trigger_tails = SimpleTrigger()
    trigger_tails.receive(0)

    @story.on('Flip a coin!')
    def one_story():
        @story.part()
        def start(message):
            coin = random.choice(['heads', 'tails'])
            return forking.SwitchOnValue(coin)

        @story.case(equal_to='heads')
        def heads_0():
            @story.part()
            def store_heads(message):
                trigger_heads.receive(trigger_heads.value + 1)

        @story.case(equal_to='tails')
        def tails_0():
            @story.part()
            def store_tails(message):
                trigger_tails.receive(trigger_tails.value + 1)

        @story.part()
        def start(message):
            assert trigger_heads.value + trigger_tails.value == 1
            coin = random.choice(['heads', 'tails'])
            return forking.SwitchOnValue(coin)

        @story.case(equal_to='heads')
        def heads_1():
            @story.part()
            def store_heads(message):
                trigger_heads.receive(trigger_heads.value + 1)

        @story.case(equal_to='tails')
        def tails_1():
            @story.part()
            def store_tails(message):
                trigger_tails.receive(trigger_tails.value + 1)

    await answer.pure_text('Flip a coin!', session, user)

    assert trigger_heads.value + trigger_tails.value == 2


@pytest.mark.asyncio
async def test_default_sync_value():
    user = build_fake_user()
    session = build_fake_session()
    trigger_1 = SimpleTrigger()
    trigger_default = SimpleTrigger()

    @story.on('Roll the dice!')
    def one_story_1():
        @story.part()
        def start(message):
            side = random.randint(1, 6)
            return forking.SwitchOnValue(side)

        @story.case(equal_to=1)
        def side_1():
            @story.part()
            def store_1(message):
                trigger_1.passed()

        @story.case(default=True)
        def other_sides():
            @story.part()
            def store_other(message):
                trigger_default.passed()

    await answer.pure_text('Roll the dice!', session, user)

    assert trigger_1.is_triggered != trigger_default.is_triggered


@pytest.mark.asyncio
async def test_one_sync_switch_inside_of_another_sync_switch():
    user = build_fake_user()
    session = build_fake_session()
    visited_rooms = SimpleTrigger(0)

    @story.on('enter')
    def labyrinth():
        @story.part()
        def enter(message):
            turn = random.choice(['left', 'right'])
            visited_rooms.receive(visited_rooms.value + 1)
            return forking.SwitchOnValue(turn)

        @story.case(equal_to='left')
        def room_1():
            @story.part()
            def next_room_1(message):
                turn = random.choice(['left', 'right'])
                visited_rooms.receive(visited_rooms.value + 1)
                return forking.SwitchOnValue(turn)

            @story.case(equal_to='left')
            def room_1_1():
                @story.part()
                def next_room_1_1(message):
                    visited_rooms.receive(visited_rooms.value + 1)

            @story.case(equal_to='right')
            def room_1_2():
                @story.part()
                def next_room_1_2(message):
                    visited_rooms.receive(visited_rooms.value + 1)

        @story.case(equal_to='right')
        def room_2():
            @story.part()
            def next_room_2(message):
                turn = random.choice(['left', 'right'])
                visited_rooms.receive(visited_rooms.value + 1)
                return forking.SwitchOnValue(turn)

            @story.case(equal_to='left')
            def room_2_1():
                @story.part()
                def next_room_2_1(message):
                    visited_rooms.receive(visited_rooms.value + 1)

            @story.case(equal_to='right')
            def room_2_2():
                @story.part()
                def next_room_2_2(message):
                    visited_rooms.receive(visited_rooms.value + 1)

    await answer.pure_text('enter', session, user)

    assert visited_rooms.value == 3


@pytest.mark.asyncio
async def test_one_sync_switch_inside_of_another_async_switch():
    user = build_fake_user()
    session = build_fake_session()
    visited_rooms = SimpleTrigger(0)

    @story.on('enter')
    def labyrinth():
        @story.part()
        async def enter(message):
            visited_rooms.receive(visited_rooms.value + 1)
            return await chat.ask('Which turn to choose?', user=message['user'])

        @story.part()
        def parse_direction_0(message):
            return forking.SwitchOnValue(message['data']['text']['raw'])

        @story.case(equal_to='left')
        def room_1():
            @story.part()
            async def next_room_1(message):
                visited_rooms.receive(visited_rooms.value + 1)
                return await chat.ask('Which turn to choose?', user=message['user'])

            @story.part()
            def parse_direction_1(message):
                return forking.SwitchOnValue(message['data']['text']['raw'])

            @story.case(equal_to='left')
            def room_1_1():
                @story.part()
                def next_room_1_1(message):
                    visited_rooms.receive(visited_rooms.value + 1)

            @story.case(equal_to='right')
            def room_1_2():
                @story.part()
                def next_room_1_2(message):
                    visited_rooms.receive(visited_rooms.value + 1)

        @story.case(equal_to='right')
        def room_2():
            @story.part()
            async def next_room_2(message):
                visited_rooms.receive(visited_rooms.value + 1)
                return await chat.ask('Which turn to choose?', user=message['user'])

            @story.part()
            def parse_direction_2(message):
                return forking.SwitchOnValue(message['data']['text']['raw'])

            @story.case(equal_to='left')
            def room_2_1():
                @story.part()
                def next_room_2_1(message):
                    visited_rooms.receive(visited_rooms.value + 1)

            @story.case(equal_to='right')
            def room_2_2():
                @story.part()
                def next_room_2_2(message):
                    visited_rooms.receive(visited_rooms.value + 1)

    await answer.pure_text('enter', session, user)
    await answer.pure_text(random.choice(['left', 'right']), session, user)
    await answer.pure_text(random.choice(['left', 'right']), session, user)

    assert visited_rooms.value == 3


@pytest.mark.asyncio
async def test_switch_inside_of_callable_inside_of_switch():
    user = build_fake_user()
    session = build_fake_session()

    visited_rooms = SimpleTrigger(0)
    spell_type = SimpleTrigger()
    spell_power = SimpleTrigger()

    @story.callable()
    def cast_the_magic():
        @story.part()
        async def ask_kind_of_spell(user):
            return await chat.ask('What kind of spell do you cast?', user=user)

        @story.part()
        def switch_by_kind_of_spell(message):
            return forking.SwitchOnValue(message['data']['text']['raw'])

        @story.case(equal_to='fireball')
        def fireball():
            @story.part()
            async def power_of_spell(message):
                spell_type.receive(message['data']['text']['raw'])
                return await chat.ask('What is the power of fireball?', user=message['user'])

        @story.case(equal_to='lightning')
        def lightning():
            @story.part()
            async def power_of_spell(message):
                spell_type.receive(message['data']['text']['raw'])
                return await chat.ask('What is the power of lightning?', user=message['user'])

        @story.part()
        def store_power(message):
            spell_power.receive(message['data']['text']['raw'])

    @story.on('enter')
    def dungeon():
        @story.part()
        async def ask_direction(message):
            return await chat.ask(
                'Where do you go?',
                user=message['user']
            )

        @story.part()
        def parser_direction(message):
            return forking.SwitchOnValue(message['data']['text']['raw'])

        @story.case(equal_to='left')
        def room_1():
            @story.part()
            async def meet_dragon(message):
                return await cast_the_magic(message['user'], session=session)

            @story.part()
            def store_end(message):
                visited_rooms.receive(visited_rooms.value + 1)

        @story.case(equal_to='right')
        def room_2():
            @story.part()
            async def meet_ogr(message):
                return await cast_the_magic(message['user'], session=session)

            @story.part()
            def store_end(message):
                visited_rooms.receive(visited_rooms.value + 1)

    await answer.pure_text('enter', session, user)
    await answer.pure_text(random.choice(['left', 'right']), session, user)
    await answer.pure_text(random.choice(['fireball', 'lightning']), session, user)
    await answer.pure_text(random.choice(['light', 'strong']), session, user)

    assert visited_rooms.value == 1
    assert spell_type.value in ['fireball', 'lightning']
    assert spell_power.value in ['light', 'strong']


@pytest.mark.asyncio
async def test_switch_without_right_case():
    user = build_fake_user()
    session = build_fake_session()

    get_help = SimpleTrigger()
    say_goodbay = SimpleTrigger()

    @story.on('I do not know')
    def meet_someone():
        @story.part()
        async def ask(message):
            return await chat.ask(
                'Do you need a help?',
                user=message['user'],
            )

        @story.part()
        def parse_result(message):
            return forking.SwitchOnValue(message['data']['text']['raw'])

        @story.case(equal_to='yes')
        def yes():
            @story.part()
            async def lets_go(message):
                await chat.say('Let\'s google together!', message['user'])
                get_help.passed()

        @story.part()
        async def see_you(message):
            await chat.say('Nice to see you!', user=message['user'])
            say_goodbay.passed()

    await answer.pure_text('I do not know', session, user)
    await answer.pure_text('No', session, user)

    assert not get_help.is_triggered
    assert say_goodbay.is_triggered


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
