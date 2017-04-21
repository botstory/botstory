import pytest

from botstory.ast import loop
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


@pytest.mark.asyncio
async def test_looping_the_loop():
    trigger_show_global_help = SimpleTrigger()
    trigger_show_local_help = SimpleTrigger(0)

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
                        trigger_show_local_help.inc()

                @story.on('work')
                def job_story():
                    @story.part()
                    def do_some_job(ctx):
                        pass

        await talk.pure_text('start job')
        await talk.pure_text('?')
        await talk.pure_text('?')
        await talk.pure_text('?')

    assert trigger_show_local_help.value == 3
    assert trigger_show_global_help.is_triggered is not True


@pytest.mark.asyncio
async def test_breaking_the_loop():
    trigger_show_global_help = SimpleTrigger()
    trigger_show_local_help = SimpleTrigger(0)

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
                        trigger_show_local_help.inc()

                @story.on('work')
                def job_story():
                    @story.part()
                    def do_some_job(ctx):
                        return loop.BreakLoop()

        await talk.pure_text('start job')
        await talk.pure_text('?')
        await talk.pure_text('work')
        await talk.pure_text('?')

    assert trigger_show_local_help.value == 1
    assert trigger_show_global_help.is_triggered is True


@pytest.mark.asyncio
async def test_breaking_the_loop_inside_of_other_loop():
    trigger_global = SimpleTrigger()
    trigger_inner = SimpleTrigger()
    trigger_outer = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on('action1')
        def global_action1():
            @story.part()
            def trigger_action1(ctx):
                pass

        @story.on('action2')  # 1
        def global_action2():
            @story.loop()
            def outer_loop():
                @story.on('action1')  # 2
                def outer_action1():
                    @story.loop()
                    def inner_loop():
                        @story.on('action1')  # 3
                        def inner_action1():
                            @story.part()
                            def inner_action1_part(ctx):
                                return loop.BreakLoop()

                        @story.on('action2')
                        def inner_action2():
                            @story.part()
                            def inner_action2_part(ctx):
                                pass

                        @story.on('action3')  # 4 (wrong)
                        def inner_action3():
                            @story.part()
                            def inner_action3_part(ctx):
                                trigger_inner.passed()

                @story.on('action2')
                def outer_action2():
                    @story.part()
                    def do_some_job(ctx):
                        pass

                @story.on('action3')  # 4 (correct)
                def outer_action3():
                    @story.part()
                    def do_some_job(ctx):
                        trigger_outer.passed()

            @story.on('action3')  # 4 (wrong)
            def global_action3():
                @story.part()
                def do_some_job(ctx):
                    trigger_global.passed()

        await talk.pure_text('action2')
        await talk.pure_text('action1')
        await talk.pure_text('action1')
        await talk.pure_text('action3')

    assert trigger_global.is_triggered is False
    assert trigger_inner.is_triggered is False
    assert trigger_outer.is_triggered is True


@pytest.mark.asyncio
async def test_prevent_message_propagation_from_outer_loop_to_an_inner_loop():
    trigger_1 = SimpleTrigger(0)
    trigger_2 = SimpleTrigger(0)
    trigger_3 = SimpleTrigger(0)

    with answer.Talk() as talk:
        story = talk.story

        @story.on('action1')  # 1
        def global_action1():
            @story.part()
            def pre_1(ctx):
                trigger_1.inc()

            @story.loop()
            def outer_loop():
                @story.on('action1')  # 2, 4
                def outer_action1():
                    @story.part()
                    def pre_2(ctx):
                        trigger_2.inc()

                    @story.loop()
                    def inner_loop():
                        @story.on('action1')  # 3
                        def inner_action1():
                            @story.part()
                            def inner_action1_part(ctx):
                                trigger_3.inc()
                                return loop.BreakLoop()

                    @story.part()
                    def pre_3(ctx):
                        pass

        await talk.pure_text('action1')
        await talk.pure_text('action1')
        await talk.pure_text('action1')
        await talk.pure_text('action1')

    assert trigger_1.value == 1
    assert trigger_2.value == 2
    assert trigger_3.value == 1


@pytest.mark.asyncio
async def test_break_loop_on_unmatched_message():
    action1_trigger = SimpleTrigger(0)
    action2_after_part_trigger = SimpleTrigger(0)

    with answer.Talk() as talk:
        story = talk.story

        @story.on('action1')
        def action1():
            @story.part()
            def action1_part(ctx):
                pass

        @story.on('action2')
        def action2():
            @story.part()
            def action2_part(ctx):
                pass

            @story.loop()
            def action2_loop():
                @story.on('action1')
                def action2_loop_action1():
                    @story.part()
                    def action2_loop_action1_part(ctx):
                        action1_trigger.inc()

                @story.on('action2')
                def action2_loop_action2():
                    @story.part()
                    def action2_loop_action2_part(ctx):
                        pass

            @story.part()
            def action2_after_part(ctx):
                action2_after_part_trigger.inc()

        await talk.pure_text('action2')
        await talk.pure_text('action1')
        await talk.pure_text('action1')
        await talk.pure_text('action3')

    assert action1_trigger.value == 2
    assert action2_after_part_trigger.value == 1


@pytest.mark.asyncio
async def test_break_loop_on_unmatched_message_and_jump_to_another_story():
    action1_trigger = SimpleTrigger(0)
    action3_trigger = SimpleTrigger(0)

    with answer.Talk() as talk:
        story = talk.story

        @story.on('action2')
        def action2():
            @story.part()
            def action2_part(ctx):
                pass

            @story.loop()
            def action2_loop():
                @story.on('action1')
                def action2_loop_action1():
                    @story.part()
                    def action2_loop_action1_part(ctx):
                        action1_trigger.inc()

                @story.on('action2')
                def action2_loop_action2():
                    @story.part()
                    def action2_loop_action2_part(ctx):
                        pass

        @story.on('action3')
        def action3():
            @story.part()
            def action3_part(ctx):
                action3_trigger.inc()

        await talk.pure_text('action2')
        await talk.pure_text('action1')
        await talk.pure_text('action1')
        await talk.pure_text('action3')

    assert action1_trigger.value == 2
    assert action3_trigger.value == 1
