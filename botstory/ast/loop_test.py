import pytest

from botstory.utils import answer, SimpleTrigger


@pytest.mark.asyncio
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
                    def show_local_help(ctx):
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


@pytest.mark.asyncio
async def test_do_not_propagate_previous_message_to_the_loop():
    trigger_hi_again = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('hi!')
        def one_job():
            @story.part()
            def show_do_job(ctx):
                pass

            @story.loop()
            def job_scope():
                @story.on('hi!')
                def hi_again():
                    @story.part()
                    def store_hi_again():
                        trigger_hi_again.passed()

                @story.on('?')
                def local_help_story():
                    @story.part()
                    def show_local_help(ctx):
                        pass

                @story.on('work')
                def job_story():
                    @story.part()
                    def do_some_job(ctx):
                        pass

        await talk.pure_text('hi!')

    assert trigger_hi_again.is_triggered is not True


@pytest.mark.asyncio
async def test_loop_inside_of_loop():
    trigger_global_action1 = SimpleTrigger()
    trigger_inner_action1 = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('action1')
        def global_action1():
            @story.part()
            def trigger_action1(ctx):
                trigger_global_action1.passed()

        @story.on('action2')
        def global_action2():
            @story.loop()
            def outer_loop():
                @story.on('action1')
                def outer_action1():
                    @story.loop()
                    def inner_loop():
                        @story.on('action1')
                        def inner_action1():
                            @story.part()
                            def inner_action1_part(ctx):
                                trigger_inner_action1.passed()

                        @story.on('action2')
                        def inner_action2():
                            @story.part()
                            def inner_action2_part(ctx):
                                pass

                @story.on('action2')
                def outer_action2():
                    @story.part()
                    def do_some_job(ctx):
                        pass

        await talk.pure_text('action2')
        await talk.pure_text('action1')
        await talk.pure_text('action1')

    assert trigger_inner_action1.is_triggered is True
    assert trigger_global_action1.is_triggered is not True
