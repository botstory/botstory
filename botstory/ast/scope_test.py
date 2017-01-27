import pytest
import botstory
from botstory.utils import answer, build_fake_session, build_fake_user, SimpleTrigger

story = None


def teardown_function(function):
    story.clear()


@pytest.mark.asyncio
async def test_jump_in_scope():
    global story
    story = botstory.Story()

    user = build_fake_user()
    session = build_fake_session()

    trigger_show_global_help = SimpleTrigger()
    trigger_show_local_help = SimpleTrigger()

    @story.on('?')
    def one_story():
        @story.part()
        def show_global_help(ctx):
            trigger_show_global_help.passed()

    @story.on('start job')
    def one_job():
        @story.part()
        def show_do_job(ctx):
            pass

        @story.scope()
        def job_scope():
            @story.on('?')
            def show_local_help(ctx):
                trigger_show_local_help.passed()

    await answer.pure_text('start job', session, user, story)
    await answer.pure_text('?', session, user, story)

    assert trigger_show_global_help.is_triggered is not True
    assert trigger_show_local_help.is_triggered is True
