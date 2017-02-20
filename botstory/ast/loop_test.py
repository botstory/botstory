import pytest

from botstory.utils import answer, SimpleTrigger


@pytest.mark.asyncio
@pytest.mark.skip
async def test_jump_in_a_loop():
    trigger_show_global_help = SimpleTrigger()
    trigger_show_local_help = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('?')
        def global_help_story():
            @story.part()
            def show_global_help(ctx):
                trigger_show_global_help.passed()

        @story.on('start job')
        def one_job():
            @story.part()
            def show_do_job(ctx):
                pass

            @story.loop()
            def job_scope():
                @story.on('?')
                def local_help_story():
                    @story.part()
                    def show_local_help():
                        trigger_show_local_help.passed()

                @story.on('work')
                def job_story():
                    @story.part()
                    def do_some_job(ctx):
                        pass

        await talk.pure_text('start job')
        await talk.pure_text('?')

    assert trigger_show_global_help.is_triggered is not True
    assert trigger_show_local_help.is_triggered is True
