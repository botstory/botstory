from botstory import Story
from botstory.ast import callable, forking, story_context
from botstory.middlewares import location, text
import pytest


@pytest.fixture
def build_mock_context():
    def factory(msg):
        story = Story()

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
                    return text.Equal('hello!')

            @story.case(match='text')
            def text_case():
                @story.part()
                def store_location(ctx):
                    pass

            @story.part()
            def after_switch(ctx):
                return callable.EndOfStory('the end')

        return story_context.StoryContext(msg, story.stories_library)

    return factory


@pytest.mark.asyncio
async def test_execute_immutability(build_mock_context):
    ctx_before = build_mock_context({
        'session': {
            'stack': [{
                'data': None,
                'step': 0,
                'topic': 'one_story',
            }, {
                'data': None,
                'step': 0,
                'topic': 'location_case',
            }],
        },
        'user': None,
        'data': None,
    })

    ctx_after = await story_context.reducers.execute(ctx_before)
    assert ctx_after is not ctx_before
    assert ctx_after.waiting_for is not ctx_before.waiting_for
    assert ctx_after.message is not ctx_before.message
    assert ctx_after.message['session'] is not ctx_before.message['session']
    assert ctx_after.message['session']['stack'] is not ctx_before.message['session']['stack']
    assert ctx_after.message['session']['stack'][-1] is not ctx_before.message['session']['stack'][-1]


@pytest.mark.asyncio
async def test_execute_immutability_with_end_of_story(build_mock_context):
    ctx_before = build_mock_context({
        'session': {
            'stack': [{
                'data': None,
                'step': 2,
                'topic': 'one_story',
            }],
        },
        'user': None,
        'data': None,
    })

    ctx_after = await story_context.reducers.execute(ctx_before)
    assert ctx_after is not ctx_before
    assert ctx_after.waiting_for is not ctx_before.waiting_for
    assert ctx_after.message is not ctx_before.message
    assert ctx_after.message['data'] is not ctx_before.message['data']


def test_iterate_storyline_immutability(build_mock_context):
    ctx_before = build_mock_context({
        'session': {
            'stack': [{
                'data': None,
                'step': 0,
                'topic': 'one_story',
            }],
        },
        'user': None,
        'data': None,
    })

    story_line = story_context.reducers.iterate_storyline(ctx_before)
    assert story_line is not []
    for story_part in story_line:
        assert story_part != ctx_before
        assert story_part.message is not ctx_before.message
        assert story_part.message['session'] is not ctx_before.message['session']
        assert story_part.message['session']['stack'] is not ctx_before.message['session']['stack']
        assert story_part.message['session']['stack'][-1] is not ctx_before.message['session']['stack'][-1]


def test_scope_out_immutability(build_mock_context):
    ctx_before = build_mock_context({
        'session': {
            'stack': [{
                'data': None,
                'step': 2,
                'topic': 'one_story',
            }],
        },
        'user': None,
        'data': None,
    })
    ctx_after = story_context.reducers.scope_out(ctx_before)
    assert ctx_after != ctx_before


def test_scope_in_immutability(build_mock_context):
    ctx_before = build_mock_context({
        'session': {
            'stack': [{
                'data': None,
                'step': 1,
                'topic': 'one_story',
            }, ],
        },
        'user': None,
        'data': None,
    })
    ctx_after = story_context.reducers.scope_in(ctx_before)
    assert ctx_after != ctx_before
    assert ctx_after.stack() != ctx_before.stack()