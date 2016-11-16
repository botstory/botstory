import aiohttp
import asyncio
import json
import pytest
from unittest import mock

from . import GAStatistics, tracker
from .. import fb, mockdb, mockhttp
from ... import story, utils


def setup_function():
    story.clear()


def teardown_function(function):
    story.clear()


@pytest.fixture
def tracker_mock(mocker):
    tr = mock.Mock()
    tr.send = aiohttp.test_utils.make_mocked_coro()
    mocker.patch.object(tracker, 'Tracker', return_value=tr)
    return tr


@pytest.mark.asyncio
async def test_should_put_in_queue_story_tracker(tracker_mock):
    user = utils.build_fake_user()
    ga = GAStatistics(tracking_id='UA-XXXXX-Y')

    ga.story(user, 'one story', 'one part')

    await asyncio.sleep(0.1)

    tracker_mock.send.assert_called_once_with(
        'pageview',
        'one story/one part',
    )


@pytest.mark.asyncio
async def test_should_put_in_queue_new_message_tracker(tracker_mock):
    user = utils.build_fake_user()
    ga = GAStatistics(tracking_id='UA-XXXXX-Y')

    ga.new_message(user, {'text': {'raw': 'hi!'}})

    await asyncio.sleep(0.1)

    tracker_mock.send.assert_called_once_with(
        'pageview',
        'receive: {}'.format(json.dumps({'text': {'raw': 'hi!'}})),
    )


@pytest.mark.asyncio
async def test_should_put_in_queue_new_user_tracker(tracker_mock):
    user = utils.build_fake_user()
    ga = GAStatistics(tracking_id='UA-XXXXX-Y')

    ga.new_user(user)

    await asyncio.sleep(0.1)

    tracker_mock.send.assert_called_once_with(
        'event',
        'new_user', 'start', 'new user starts chat'
    )


@pytest.mark.asyncio
async def test_should_put_in_queue_event_tracker(tracker_mock):
    user = utils.build_fake_user()
    ga = GAStatistics(tracking_id='UA-XXXXX-Y')

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

    story.use(mockdb.MockDB())
    facebook = story.use(fb.FBInterface())
    story.use(mockhttp.MockHttpInterface())
    story.use(GAStatistics(tracking_id='UA-XXXXX-Y'))
    await story.start()

    await facebook.handle({
        'object': 'page',
        'entry': [{
            'id': 'PAGE_ID',
            'time': 123456789,
            'messaging': [{
                'sender': {
                    'id': 'UNKNOWN_ID',
                },
                'recipient': {
                    'id': 'PAGE_ID'
                },
                'timestamp': 123456789,
                'message': {
                    'text': 'hi!'
                }
            }]
        }]
    })

    await asyncio.sleep(0.1)
    tracker_mock.send.assert_has_calls([
        mock.call('event',
                  'new_user', 'start', 'new user starts chat'
                  ),
        mock.call('pageview',
                  'receive: {}'.format(json.dumps({'text': {'raw': 'hi!'}})),
                  ),
        mock.call('pageview',
                  'one_story/greeting',
                  ),
    ])
