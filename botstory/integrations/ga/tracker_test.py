import aiohttp
import asyncio
import pytest
from unittest import mock

from . import tracker
from ... import utils


@pytest.mark.asyncio
async def test_should_put_in_queue_story_part(mocker):
    tracker_mock = mock.Mock()
    tracker_mock.send = aiohttp.test_utils.make_mocked_coro()

    mocker.patch.object(tracker,
                        'Tracker',
                        return_value=tracker_mock,
                        )

    user = utils.build_fake_user()
    ga = tracker.GAStatistics(tracking_id='UA-XXXXX-Y')

    ga.story(user, 'one story', 'one part')

    await asyncio.sleep(0.1)

    tracker_mock.send.assert_called_once_with(
        'pageview',
        'one story/one part',
    )
