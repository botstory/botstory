import json
import pytest
import random

from . import forking
from .. import chat, story, matchers
from ..middlewares.location import location
from ..middlewares.text import text
from ..utils import answer, build_fake_session, build_fake_user, SimpleTrigger


@pytest.fixture
def teardown_function(function):
    print('tear down!')
    story.stories_library.clear()


def test_cases():
    user = build_fake_user()
    session = build_fake_session()

    trigger_location = SimpleTrigger()
    trigger_text = SimpleTrigger()
    trigger_after_switch = SimpleTrigger()

    @story.on('Hi there!')
    def one_story():
        @story.part()
        def start(message):
            chat.say('Where do you go?', user=message['user'])
            return forking.Switch({
                'location': location.Any(),
                'text': text.Any(),
            })

        @story.case(match='location')
        def location_case():
            @story.part()
            def store_location(message):
                trigger_location.receive(message['location'])

        @story.case(match='text')
        def text_case():
            @story.part()
            def store_location(message):
                trigger_text.receive(message['text']['raw'])

        @story.part()
        def after_switch(message):
            trigger_after_switch.passed()

    answer.pure_text('Hi there!', session, user)
    answer.location({'x': 123, 'y': 321}, session, user)

    assert trigger_location.result() == {'x': 123, 'y': 321}
    assert not trigger_text.result()
    assert trigger_after_switch.is_triggered


def test_sync_value():
    user = build_fake_user()
    session = build_fake_session()
    trigger_heads = SimpleTrigger()
    trigger_tails = SimpleTrigger()

    @story.on('Flip a coin!')
    def one_story():
        @story.part()
        def start(message):
            coin = random.choice(['heads', 'tails'])
            return forking.SwitchOnValue(coin)

        @story.case(equal_to='heads')
        def heads():
            @story.part()
            def store_heads(message):
                trigger_heads.passed()

        @story.case(equal_to='tails')
        def tails():
            @story.part()
            def store_tails(message):
                trigger_tails.passed()

    answer.pure_text('Flip a coin!', session, user)

    assert trigger_heads.is_triggered != trigger_tails.is_triggered


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
