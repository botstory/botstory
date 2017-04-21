import pytest
from . import messenger
from .. import mockhttp
from ... import utils


@pytest.mark.parametrize('greeting_text,valid', [
    ('very-long-message ' * 100, False),
    ('short-message.', True),
])
@pytest.mark.asyncio
async def test_validate_greeting_text(mocker, greeting_text, valid):
    fb = messenger.FBInterface()
    log_mock = mocker.patch('botstory.integrations.fb.messenger.logger')
    fb.http = mockhttp.MockHttpInterface()
    await fb.set_greeting_text(greeting_text)
    if valid:
        assert not log_mock.warn.called, 'should be valid'
    else:
        log_mock.warn.assert_called_with('greeting text should not exceed 160 length in characters')


@pytest.mark.parametrize('menu,invalid_message', [
    ([{
        'type': 'postback',
        'title': 'Help',
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
    }] * 2, False),

    ([{
        'type': 'postback',
        'title': 'Help',
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
    }] * 10, 'menu should not exceed 5 call to actions'),

    ([{
        'type': 'postback',
        'title': 'Help',
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
    }, {
        'type': 'postback',
        'title': 'VeryLongTitle' * 10,
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
    }], 'menu item title should not exceed 30 characters'),

    ([{
        'type': 'postback',
        'title': 'Help',
        'payload': 'VERY_LONG_PAYLOAD_' * 100
    }, {
        'type': 'postback',
        'title': 'Hello',
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
    }], 'menu item payload should not exceed 1000 characters'),
])
@pytest.mark.asyncio
async def test_validate_persistent_menu(mocker, menu, invalid_message):
    fb = messenger.FBInterface()
    log_mock = mocker.patch('botstory.integrations.fb.messenger.logger')
    fb.http = mockhttp.MockHttpInterface()
    await fb.set_persistent_menu(menu)
    if invalid_message:
        log_mock.warn.assert_called_with(invalid_message)
    else:
        assert not log_mock.warn.called, 'should be valid'


@pytest.mark.parametrize('text,options,invalid_message', [
    ('hi there!', None, False),

    ('very long message ' * 40, None, 'send message text should not exceed 640 character limit'),

    ('short message', [{
        'content_type': 'text',
        'title': 'Red',
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED',
    }] * 20, 'send message quick replies should not exceed 10 limit'),

    ('short message', [{
        'content_type': 'text',
        'title': 'Very Long ' * 10,
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED',
    }], 'send message quick replies title should not exceed 20 character limit'),

    ('short message', [{
        'content_type': 'text',
        'title': 'Short',
        'payload': 'VERY_LONG_' * 200,
    }], 'send message quick replies payload should not exceed 1000 character limit'),

    ('short message', [{
        'title': 'Short',
        'payload': 'SOME_PAYLOAD',
    }], 'send message quick replies should have content_type'),
])
@pytest.mark.asyncio
async def test_validate_send_text_message(mocker, text, options, invalid_message):
    recipient = utils.build_fake_user()
    fb = messenger.FBInterface()
    log_mock = mocker.patch('botstory.integrations.fb.messenger.logger')
    fb.http = mockhttp.MockHttpInterface()
    await fb.send_text_message(recipient, text, options)
    if invalid_message:
        log_mock.warn.assert_called_with(invalid_message)
    else:
        assert not log_mock.warn.called, 'should be valid'
