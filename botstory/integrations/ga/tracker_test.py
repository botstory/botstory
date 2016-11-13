import aiohttp
import asyncio
import pytest
from unittest import mock

from . import tracker
from ... import story, chat, utils


@pytest.fixture
def tracker_mock(mocker):
    tr = mock.Mock()
    tr.send = aiohttp.test_utils.make_mocked_coro()
    mocker.patch.object(tracker, 'Tracker', return_value=tr)
    return tr


@pytest.mark.asyncio
async def test_should_put_in_queue_story_tracker(tracker_mock):
    user = utils.build_fake_user()
    ga = tracker.GAStatistics(tracking_id='UA-XXXXX-Y')

    ga.story(user, 'one story', 'one part')

    await asyncio.sleep(0.1)

    tracker_mock.send.assert_called_once_with(
        'pageview',
        'one story/one part',
    )


@pytest.mark.asyncio
async def test_should_put_in_queue_event_tracker(tracker_mock):
    user = utils.build_fake_user()
    ga = tracker.GAStatistics(tracking_id='UA-XXXXX-Y')

    ga.event(user, 'category', 'action', 'label', 10)

    await asyncio.sleep(0.1)

    tracker_mock.send.assert_called_once_with(
        'event',
        'category', 'action', 'label', 10,
    )


# integration testing

@pytest.mark.asyncio
async def test_should_track_story(tracker_mock):
    @story.on('hi!')
    def one_story():
        @story.part()
        def greeting(message):
            pass

    story.use(tracker.GAStatistics(tracking_id='UA-XXXXX-Y'))
    await story.start()
    user = utils.build_fake_user()
    await chat.say('hi!', user=user)

    await asyncio.sleep(0.1)

    tracker_mock.send.assert_called_once_with(
        'pageview',
        'one_story/greeting',
    )
