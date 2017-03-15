import logging
import pytest
from botstory import matchers, utils
from botstory.middlewares import sticker
from botstory.utils import answer

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_match_any_sticker():
    trigger = utils.SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(sticker.Any())
        def sticker_story():
            @story.part()
            def then(ctx):
                trigger.passed()

        await talk.ask({
            'sticker_id': sticker.LIKE_STICKERS[0],
        })

        assert trigger.is_triggered


@pytest.mark.asyncio
async def test_match_fblike_sticker():
    trigger_any = utils.SimpleTrigger()
    trigger_like = utils.SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story

        @story.on(sticker.Like())
        def like_sticker_story():
            @story.part()
            def then(ctx):
                trigger_like.passed()

        @story.on(sticker.Any())
        def any_sticker_story():
            @story.part()
            def then(ctx):
                trigger_any.passed()

        await talk.ask({
            'sticker_id': sticker.LIKE_STICKERS[0],
        })

        assert trigger_like.is_triggered

        await talk.ask({
            'sticker_id': '1',
        })

        assert trigger_like.is_triggered
