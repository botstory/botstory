import logging
from unittest import mock
import pytest

from . import messenger
from .. import commonhttp, mockdb, mockhttp
from ... import chat, story, utils
from ...middlewares import any, option

logger = logging.getLogger(__name__)


def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()
    chat.interfaces = {}


@pytest.mark.asyncio
async def test_send_text_message():
    user = utils.build_fake_user()

    interface = story.use(messenger.FBInterface(page_access_token='qwerty'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await interface.send_text_message(
        recipient=user, text='hi!', options=None
    )

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/messages/',
        params={
            'access_token': 'qwerty',
        },
        json={
            'message': {
                'text': 'hi!',
            },
            'recipient': {
                'id': user['facebook_user_id'],
            },
        }
    )


@pytest.mark.asyncio
async def test_integration():
    user = utils.build_fake_user()

    story.use(messenger.FBInterface(page_access_token='qwerty'))
    story.use(mockdb.MockDB())
    mock_http = story.use(mockhttp.MockHttpInterface())

    await chat.say('hi there!', user=user)

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/messages/',
        params={
            'access_token': 'qwerty',
        },
        json={
            'message': {
                'text': 'hi there!',
            },
            'recipient': {
                'id': user['facebook_user_id'],
            },
        }
    )


@pytest.mark.asyncio
async def test_options():
    user = utils.build_fake_user()

    story.use(messenger.FBInterface(page_access_token='qwerty'))
    story.use(mockdb.MockDB())
    mock_http = story.use(mockhttp.MockHttpInterface())

    await chat.ask(
        'Which color do you like?',
        options=[{
            'title': 'Red',
            'payload': 0xff0000,
        }, {
            'title': 'Green',
            'payload': 0x00ff00,
        }, {
            'title': 'Blue',
            'payload': 0x0000ff,
        }],
        user=user)

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/messages/',
        params={
            'access_token': 'qwerty',
        },
        json={
            'message': {
                'text': 'Which color do you like?',
                'quick_replies': [
                    {
                        'content_type': 'text',
                        'title': 'Red',
                        'payload': 0xff0000,
                    },
                    {
                        'content_type': 'text',
                        'title': 'Green',
                        'payload': 0x00ff00,
                    },
                    {
                        'content_type': 'text',
                        'title': 'Blue',
                        'payload': 0x0000ff,
                    },
                ],
            },
            'recipient': {
                'id': user['facebook_user_id'],
            },
        }
    )


@pytest.mark.asyncio
async def test_setup_webhook():
    fb_interface = story.use(messenger.FBInterface(
        webhook_url='/webhook',
        webhook_token='some-token',
    ))
    mock_http = story.use(mockhttp.MockHttpInterface())

    mock_http.webhook.assert_called_with(
        '/webhook',
        fb_interface.handle,
        'some-token',
    )


@pytest.mark.asyncio
async def test_should_request_user_data_once_we_do_not_know_current_user():
    fb_interface = story.use(messenger.FBInterface(
        page_access_token='qwerty',
        webhook_url='/webhook',
        webhook_token='some-token',
    ))
    http = story.use(mockhttp.MockHttpInterface(get={
        'first_name': 'Peter',
        'last_name': 'Chang',
        'profile_pic': 'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xpf1/v/t1.0-1/p200x200/13055603_10105219398495383_8237637584159975445_n.jpg?oh=1d241d4b6d4dac50eaf9bb73288ea192&oe=57AF5C03&__gda__=1470213755_ab17c8c8e3a0a447fed3f272fa2179ce',
        'locale': 'en_US',
        'timezone': -7,
        'gender': 'male'
    }))
    story.use(mockdb.MockDB())

    await fb_interface.handle({
        'object': 'page',
        'entry': [{
            'id': 'PAGE_ID',
            'time': 1473204787206,
            'messaging': [
                {
                    'sender': {
                        'id': 'USER_ID'
                    },
                    'recipient': {
                        'id': 'PAGE_ID'
                    },
                    'timestamp': 1458692752478,
                    'message': {
                        'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                        'seq': 73,
                        'text': 'hello, world!'
                    }
                }
            ]
        }]
    })

    http.get.assert_called_with(
        'https://graph.facebook.com/v2.6/USER_ID',
        params={
            'access_token': 'qwerty',
        },
    )


@pytest.mark.asyncio
async def test_should_request_user_data_and_fail():
    fb_interface = story.use(messenger.FBInterface(
        page_access_token='qwerty',
        webhook_url='/webhook',
        webhook_token='some-token',
    ))
    story.use(mockhttp.MockHttpInterface(
        get_raise=commonhttp.errors.HttpRequestError()))
    db = story.use(mockdb.MockDB())

    await fb_interface.handle({
        'object': 'page',
        'entry': [{
            'id': 'PAGE_ID',
            'time': 1473204787206,
            'messaging': [
                {
                    'sender': {
                        'id': 'USER_ID'
                    },
                    'recipient': {
                        'id': 'PAGE_ID'
                    },
                    'timestamp': 1458692752478,
                    'message': {
                        'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                        'seq': 73,
                        'text': 'hello, world!'
                    }
                }
            ]
        }]
    })

    assert (await db.get_user(facebook_user_id='USER_ID')).no_fb_profile is True


@pytest.mark.asyncio
async def test_webhook_handler_should_return_ok_status_if_http_fail():
    fb_interface = story.use(messenger.FBInterface(
        page_access_token='qwerty',
        webhook_url='/webhook',
        webhook_token='some-token',
    ))
    story.use(mockhttp.MockHttpInterface(get_raise=commonhttp.errors.HttpRequestError()))
    story.use(mockdb.MockDB())

    res = await fb_interface.handle({
        'object': 'page',
        'entry': [{
            'id': 'PAGE_ID',
            'time': 1473204787206,
            'messaging': [
                {
                    'sender': {
                        'id': 'USER_ID'
                    },
                    'recipient': {
                        'id': 'PAGE_ID'
                    },
                    'timestamp': 1458692752478,
                    'message': {
                        'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                        'seq': 73,
                        'text': 'hello, world!'
                    }
                }
            ]
        }]
    })

    assert res['status'] == 200


@pytest.mark.asyncio
async def test_webhook_handler_should_return_ok_status_in_any_case():
    fb_interface = messenger.FBInterface()
    with mock.patch('botstory.integrations.fb.messenger.logger') as mock_logger:
        res = await fb_interface.handle({
            'object': 'page',
            'entry': [{
                'id': 'PAGE_ID',
                'time': 1473204787206,
                'messaging': [
                    {
                        'sender': {
                            'id': 'USER_ID'
                        },
                        'recipient': {
                            'id': 'PAGE_ID'
                        },
                        'timestamp': 1458692752478,
                        'message': {
                            'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                            'seq': 73,
                            'text': 'hello, world!'
                        }
                    }
                ]
            }]
        })

        assert mock_logger.debug.calledWith()

    assert res['status'] == 200


# integration

@pytest.fixture
def build_fb_interface():
    async def builder():
        user = utils.build_fake_user()
        session = utils.build_fake_session()

        storage = story.use(mockdb.MockDB())
        fb = story.use(messenger.FBInterface(page_access_token='qwerty'))

        await storage.set_session(session)
        await storage.set_user(user)

        return fb

    return builder


@pytest.mark.asyncio
async def test_handler_raw_text(build_fb_interface):
    fb_interface = await build_fb_interface()

    correct_trigger = utils.SimpleTrigger()
    incorrect_trigger = utils.SimpleTrigger()

    @story.on('hello, world!')
    def correct_story():
        @story.part()
        def store_result(message):
            correct_trigger.receive(message)

    @story.on('Goodbye, world!')
    def incorrect_story():
        @story.part()
        def store_result(message):
            incorrect_trigger.receive(message)

    await fb_interface.handle({
        'object': 'page',
        'entry': [{
            'id': 'PAGE_ID',
            'time': 1473204787206,
            'messaging': [
                {
                    'sender': {
                        'id': 'USER_ID'
                    },
                    'recipient': {
                        'id': 'PAGE_ID'
                    },
                    'timestamp': 1458692752478,
                    'message': {
                        'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                        'seq': 73,
                        'text': 'hello, world!'
                    }
                }
            ]
        }]
    })

    assert incorrect_trigger.value is None
    assert correct_trigger.value == {
        'user': fb_interface.storage.user,
        'session': fb_interface.storage.session,
        'data': {
            'text': {
                'raw': 'hello, world!'
            }
        }
    }


@pytest.mark.asyncio
async def test_handler_selected_option(build_fb_interface):
    fb_interface = await build_fb_interface()

    correct_trigger = utils.SimpleTrigger()
    incorrect_trigger = utils.SimpleTrigger()

    @story.on(receive=option.Match('GREEN'))
    def correct_story():
        @story.part()
        def store_result(message):
            correct_trigger.receive(message)

    @story.on(receive=option.Match('BLUE'))
    def incorrect_story():
        @story.part()
        def store_result(message):
            incorrect_trigger.receive(message)

    await fb_interface.handle({
        'object': 'page',
        'entry': [{
            'id': 'PAGE_ID',
            'time': 1473204787206,
            'messaging': [{
                'sender': {
                    'id': 'USER_ID'
                },
                'recipient': {
                    'id': 'PAGE_ID'
                },
                'timestamp': 1458692752478,
                'message': {
                    'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                    'seq': 73,
                    'text': 'Green!',
                    'quick_reply': {
                        'payload': 'GREEN'
                    }
                }
            }]
        }]
    })

    assert incorrect_trigger.value is None
    assert correct_trigger.value == {
        'user': fb_interface.storage.user,
        'session': fb_interface.storage.session,
        'data': {
            'option': 'GREEN',
            'text': {
                'raw': 'Green!'
            }
        }
    }


@pytest.mark.asyncio
async def test_should_not_process_echo_message_as_regular(build_fb_interface):
    fb_interface = await build_fb_interface()

    echo_trigger = utils.SimpleTrigger()

    @story.on(receive=any.Any())
    def one_story():
        @story.part()
        def sync_part(message):
            echo_trigger.passed()

    await fb_interface.handle({
        'entry': [
            {
                'id': '329188380752158',
                'messaging': [
                    {
                        'message': {
                            'app_id': 345865645763384,
                            'is_echo': 'True',
                            'mid': 'mid.1477350590023:38b1efd593',
                            'seq': 323,
                            'text': 'Hm I dont know what is it'
                        },
                        'recipient': {
                            'id': '1034692249977067'
                        },
                        'sender': {
                            'id': '329188380752158'
                        },
                        'timestamp': 1477350590023
                    }
                ],
                'time': 1477350590772
            }
        ],
        'object': 'page'
    })

    assert not echo_trigger.is_triggered
