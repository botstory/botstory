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
            'data': None,
            'stack': [{
                'data': None,
                'step': 2,
                'topic': 'one_story',
            }],
        },
        'user': None,
    })

    ctx_after = await story_context.reducers.execute(ctx_before)
    assert ctx_after is not ctx_before
    assert ctx_after.waiting_for is not ctx_before.waiting_for
    assert ctx_after.message is not ctx_before.message
    assert ctx_after.get_user_data() is not ctx_before.get_user_data()


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

    story_part = next(story_line)
    while True:
        try:
            assert story_part != ctx_before
            assert story_part.message is not ctx_before.message
            assert story_part.message['session'] is not ctx_before.message['session']
            assert story_part.message['session']['stack'] is not ctx_before.message['session']['stack']
            assert story_part.message['session']['stack'][-1] is not ctx_before.message['session']['stack'][-1]
            story_line.send(story_part)
        except StopIteration:
            break


def test_iterate_storyline_send_ctx_back(build_mock_context):
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
    ctx_after = next(story_line)
    ctx_before = ctx_after
    ctx_before.message['session']['stack'][-1]['data'] = 'hello world!'

    ctx_after = story_line.send(ctx_before)
    assert ctx_before.message['session']['stack'][-1]['data'] == \
           ctx_after.message['session']['stack'][-1]['data']
    compare_ctx(ctx_before, ctx_after)
    ctx_before = ctx_after

    ctx_after = story_line.send(ctx_before)
    compare_ctx(ctx_before, ctx_after)
    with pytest.raises(StopIteration):
        story_line.send(ctx_before)


def compare_ctx(ctx1, ctx2):
    assert ctx1 != ctx2
    assert ctx1.message != ctx2.message


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
