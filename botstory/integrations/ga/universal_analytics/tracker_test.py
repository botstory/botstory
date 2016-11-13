#!/usr/bin/python
# -*- encoding: utf-8 -*-
###############################################################################
# Test and example kit for Universal Analytics for Python
# Copyright (c) 2013, Analytics Pros
#
# This project is free software, distributed under the BSD license.
# Analytics Pros offers consulting and integration services if your firm needs
# assistance in strategy, implementation, or auditing existing work.
###############################################################################

import pytest
import urllib

from .tracker import Tracker
from . import fake_analytics


def url_quote(value, safe_chars=''):
    return urllib.parse.quote(value, safe_chars)


@pytest.fixture
def tracker():
    return Tracker('UA-XXXXX-Y', use_post=True)


def test_tracker_options_basic(tracker):
    assert 'UA-XXXXX-Y' == tracker.params['tid']


def test_persistent_campaign_settings(tracker):
    # Apply campaign settings
    tracker.set('campaignName', 'testing-campaign')
    tracker.set('campaignMedium', 'testing-medium')
    tracker['campaignSource'] = 'test-source'

    tracker.params['cn'] = 'testing-campaign'
    tracker.params['cm'] = 'testing-medium'
    tracker.params['cs'] = 'test-source'


@pytest.mark.asyncio
async def test_send_pageview(tracker, event_loop):
    async with fake_analytics.FakeAnalytics(event_loop) as server:
        async with server.session() as session:
            tracker.http._session = session

            await tracker.send('pageview', '/test')

            assert len(server.history) == 1
            text = await server.history[-1]['request'].text()
            assert 't=pageview' in text
            assert 'dp={0}'.format(url_quote('/test')) in text


@pytest.mark.asyncio
async def test_send_interactive_event(tracker, event_loop):
    async with fake_analytics.FakeAnalytics(event_loop) as server:
        async with server.session() as session:
            tracker.http._session = session

            await tracker.send('event', 'mycat', 'myact', 'mylbl', {'noninteraction': 1, 'page': '/1'})

            assert len(server.history) == 1
            text = await server.history[-1]['request'].text()
            assert 't=event' in text
            assert 'ec=mycat' in text
            assert 'ea=myact' in text
            assert 'el=mylbl' in text
            assert 'ni=1' in text
            assert 'dp={0}'.format(url_quote('/1')) in text


# def testSendUnicodeEvent(self):
#         # Send unicode data:
#         # As unicode
#         self.tracker.send('event', u'câtēgøry', u'åctîõn', u'låbęl', u'válüē')
#         # As str
#         self.tracker.send('event', 'câtēgøry', 'åctîõn', 'låbęl', 'válüē')
#
#         # TODO  write assertions for these...
#         # The output buffer should show both representations in UTF-8 for compatibility
#

@pytest.mark.asyncio
async def test_send_social_hit(tracker, event_loop):
    async with fake_analytics.FakeAnalytics(event_loop) as server:
        async with server.session() as session:
            tracker.http._session = session

            # Send a social hit
            await tracker.send('social', 'facebook', 'share', '/test#social')
            text = await server.history[-1]['request'].text()
            assert 't=social' in text
            assert 'sn=facebook' in text
            assert 'sa=share' in text
            assert 'st={0}'.format(url_quote('/test#social')) in text


@pytest.mark.asyncio
async def test_send_transaction(tracker, event_loop):
    async with fake_analytics.FakeAnalytics(event_loop) as server:
        async with server.session() as session:
            tracker.http._session = session

            # Dispatch the item hit first (though this is somewhat unusual)
            await tracker.send('item', {
                'transactionId': '12345abc',
                'itemName': 'pizza',
                'itemCode': 'abc',
                'itemCategory': 'hawaiian',
                'itemQ7uantity': 1
            }, hitage=200)

            # Then the transaction hit...
            await tracker.send('transaction', {
                'transactionId': '12345abc',
                'transactionAffiliation': 'phone order',
                'transactionRevenue': 28.00,
                'transactionTax': 3.00,
                'transactionShipping': 0.45,
                'transactionCurrency': 'USD'
            }, hitage=7200)

            # TODO: asserts


@pytest.mark.asyncio
async def test_send_transaction(tracker, event_loop):
    async with fake_analytics.FakeAnalytics(event_loop) as server:
        async with server.session() as session:
            tracker.http._session = session

            # A few more hits for good measure, testing real-time support for time offset
            await tracker.send('pageview', '/test', {'campaignName': 'testing2'}, hitage=60 * 5)  # 5 minutes ago
            await tracker.send('pageview', '/test', {'campaignName': 'testing3'}, hitage=60 * 20)  # 20 minutes ago

            # TODO: asserts
