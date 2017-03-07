import asyncio
from botstory.ast import story_context
import logging
from unittest import mock
import pytest

from . import messenger
from .. import commonhttp, mockdb, mockhttp
from ... import di, Story, utils
from ...middlewares import any, option

logger = logging.getLogger(__name__)

story = None


def teardown_function(function):
    logger.debug('tear down!')
    story.clear()


@pytest.mark.asyncio
async def test_send_text_message():
    user = utils.build_fake_user()

    global story
    story = Story()

    interface = story.use(messenger.FBInterface(page_access_token='qwerty1'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.start()

    await interface.send_text_message(
        recipient=user, text='hi!', quick_replies=None
    )

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/messages/',
        params={
            'access_token': 'qwerty1',
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
async def test_truncate_long_message():
    user = utils.build_fake_user()

    global story
    story = Story()

    interface = story.use(messenger.FBInterface(page_access_token='qwerty1'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.start()

    very_long_message = 'very_long_message' * 100
    await interface.send_text_message(
        recipient=user,
        text=very_long_message,
        quick_replies=None,
        options={
            'overflow': 'cut'
        }
    )

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/messages/',
        params={
            'access_token': 'qwerty1',
        },
        json={
            'message': {
                'text': very_long_message[:640],
            },
            'recipient': {
                'id': user['facebook_user_id'],
            },
        }
    )


@pytest.mark.asyncio
async def test_truncate_with_ellipsis_long_message_by_default():
    user = utils.build_fake_user()

    global story
    story = Story()

    interface = story.use(messenger.FBInterface(page_access_token='qwerty1'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.start()

    very_long_message = 'very_long_message' * 100
    await interface.send_text_message(
        recipient=user,
        text=very_long_message,
        quick_replies=None,
    )

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/messages/',
        params={
            'access_token': 'qwerty1',
        },
        json={
            'message': {
                'text': very_long_message[:638] + '\u2026',
            },
            'recipient': {
                'id': user['facebook_user_id'],
            },
        }
    )


@pytest.mark.asyncio
async def test_integration():
    user = utils.build_fake_user()

    global story
    story = Story()

    story.use(messenger.FBInterface(page_access_token='qwerty2'))
    story.use(mockdb.MockDB())
    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.say('hi there!', user=user)

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/messages/',
        params={
            'access_token': 'qwerty2',
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

    global story
    story = Story()

    story.use(messenger.FBInterface(page_access_token='qwerty3'))
    story.use(mockdb.MockDB())
    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.ask(
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
            'access_token': 'qwerty3',
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
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(
        webhook_url='/webhook',
        webhook_token='some-token',
    ))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.start()

    mock_http.webhook.assert_called_with(
        '/webhook',
        fb_interface.handle,
        'some-token',
    )


@pytest.mark.asyncio
async def test_should_request_user_data_once_we_do_not_know_current_user():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(
        page_access_token='qwerty4',
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
            'access_token': 'qwerty4',
        },
    )


@pytest.mark.asyncio
async def test_should_request_user_data_and_fail():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(
        page_access_token='qwerty5',
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
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(
        page_access_token='qwerty6',
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
    global story
    story = Story()

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

        global story
        story = Story()

        storage = story.use(mockdb.MockDB())
        fb = story.use(messenger.FBInterface(page_access_token='qwerty'))

        await story.start()

        await storage.set_session(session)
        await storage.set_user(user)

        return fb, story

    return builder


@pytest.mark.asyncio
async def test_handler_raw_text(build_fb_interface):
    fb_interface, story = await build_fb_interface()

    correct_trigger = utils.SimpleTrigger()
    incorrect_trigger = utils.SimpleTrigger()

    @story.on('hello, world!')
    def correct_story():
        @story.part()
        def store_result(ctx):
            correct_trigger.receive(story_context.get_message_data(ctx))

    @story.on('Goodbye, world!')
    def incorrect_story():
        @story.part()
        def store_result(ctx):
            incorrect_trigger.receive(story_context.get_message_data(ctx))

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
        'text': {
            'raw': 'hello, world!'
        }
    }


@pytest.mark.asyncio
async def test_handler_selected_option(build_fb_interface):
    fb_interface, story = await build_fb_interface()

    correct_trigger = utils.SimpleTrigger()
    incorrect_trigger = utils.SimpleTrigger()

    @story.on(receive=option.Match('GREEN'))
    def correct_story():
        @story.part()
        def store_result(ctx):
            correct_trigger.receive(story_context.get_message_data(ctx))

    @story.on(receive=option.Match('BLUE'))
    def incorrect_story():
        @story.part()
        def store_result(ctx):
            incorrect_trigger.receive(story_context.get_message_data(ctx))

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
        'option': 'GREEN',
        'text': {
            'raw': 'Green!'
        }
    }


@pytest.mark.asyncio
async def test_handler_postback(build_fb_interface):
    fb_interface, story = await build_fb_interface()

    correct_trigger = utils.SimpleTrigger()
    incorrect_trigger = utils.SimpleTrigger()

    @story.on(receive=option.Match('GREEN'))
    def correct_story():
        @story.part()
        def store_result(ctx):
            correct_trigger.receive(story_context.get_message_data(ctx))

    @story.on(receive=option.Match('BLUE'))
    def incorrect_story():
        @story.part()
        def store_result(ctx):
            incorrect_trigger.receive(story_context.get_message_data(ctx))

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
                'postback': {
                    'payload': 'GREEN'
                },
            }]
        }]
    })

    assert incorrect_trigger.value is None
    assert correct_trigger.value == {
        'option': 'GREEN',
    }


@pytest.mark.asyncio
async def test_should_not_process_echo_delivery_and_read_messages_as_regular(build_fb_interface):
    fb_interface, story = await build_fb_interface()

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
                'messaging': [{
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
                }, {
                    'read': {
                        'seq': 2697,
                        'watermark': 1477354670744
                    },
                    'recipient': {
                        'id': '329188380752158'
                    },
                    'sender': {
                        'id': '1034692249977067'
                    },
                    'timestamp': 1477354672037
                }, {
                    'delivery': {
                        'mids': [
                            'mid.1477354667117:8fedc43d37'
                        ],
                        'seq': 2679,
                        'watermark': 1477354668538
                    },
                    'recipient': {
                        'id': '329188380752158'
                    },
                    'sender': {
                        'id': '1034692249977067'
                    },
                    'timestamp': 0
                }],
                'time': 1477350590772
            }
        ],
        'object': 'page'
    })

    assert not echo_trigger.is_triggered


@pytest.mark.asyncio
async def test_set_greeting_text():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty7'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await fb_interface.set_greeting_text('Hi there {{user_first_name}}!')

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty7',
        },
        json={
            'setting_type': 'greeting',
            'greeting': {
                'text': 'Hi there {{user_first_name}}!',
            },
        }
    )


@pytest.mark.asyncio
async def test_can_set_greeting_text_before_inject_http():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty8'))
    await fb_interface.set_greeting_text('Hi there {{user_first_name}}!')

    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.setup()

    # give few a moment for lazy initialization of greeting text
    await asyncio.sleep(0.1)

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty8',
        },
        json={
            'setting_type': 'greeting',
            'greeting': {
                'text': 'Hi there {{user_first_name}}!',
            },
        }
    )


@pytest.mark.asyncio
async def test_can_set_greeting_text_in_constructor():
    global story
    story = Story()

    fb = story.use(messenger.FBInterface(
        greeting_text='Hi there {{user_first_name}}!',
        page_access_token='qwerty9',
    ))

    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.setup()

    # give few a moment for lazy initialization of greeting text
    await asyncio.sleep(0.1)

    mock_http.delete.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty9',
        },
        json={
            'setting_type': 'greeting',
        },
    )

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty9',
        },
        json={
            'setting_type': 'greeting',
            'greeting': {
                'text': 'Hi there {{user_first_name}}!',
            },
        }
    )


@pytest.mark.asyncio
async def test_remove_greeting_text():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty10'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await fb_interface.remove_greeting_text()

    mock_http.delete.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty10',
        },
        json={
            'setting_type': 'greeting',
        }
    )


@pytest.mark.asyncio
async def test_set_greeting_call_to_action_payload():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty11'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await fb_interface.set_greeting_call_to_action_payload('SOME_PAYLOAD')

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty11',
        },
        json={
            'setting_type': 'call_to_actions',
            'thread_state': 'new_thread',
            'call_to_actions': [{'payload': 'SOME_PAYLOAD'}]
        }
    )


@pytest.mark.asyncio
async def test_remove_greeting_call_to_action_payload():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty12'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await fb_interface.remove_greeting_call_to_action_payload()

    mock_http.delete.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty12',
        },
        json={
            'setting_type': 'call_to_actions',
            'thread_state': 'new_thread',
        }
    )


@pytest.mark.asyncio
async def test_set_persistent_menu():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty13'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await fb_interface.set_persistent_menu([{
        'type': 'postback',
        'title': 'Help',
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
    }, {
        'type': 'web_url',
        'title': 'View Website',
        'url': 'http://petersapparel.parseapp.com/'
    }])

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty13',
        },
        json={
            'setting_type': 'call_to_actions',
            'thread_state': 'existing_thread',
            'call_to_actions': [{
                'type': 'postback',
                'title': 'Help',
                'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
            }, {
                'type': 'web_url',
                'title': 'View Website',
                'url': 'http://petersapparel.parseapp.com/'
            }]
        }
    )


@pytest.mark.asyncio
async def test_can_set_persistent_menu_before_http():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty14'))
    await fb_interface.set_persistent_menu([{
        'type': 'postback',
        'title': 'Help',
        'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
    }, {
        'type': 'web_url',
        'title': 'View Website',
        'url': 'http://petersapparel.parseapp.com/'
    }])

    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.setup()

    # give few a moment for lazy initialization of greeting text
    await asyncio.sleep(0.1)

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty14',
        },
        json={
            'setting_type': 'call_to_actions',
            'thread_state': 'existing_thread',
            'call_to_actions': [{
                'type': 'postback',
                'title': 'Help',
                'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
            }, {
                'type': 'web_url',
                'title': 'View Website',
                'url': 'http://petersapparel.parseapp.com/'
            }]
        }
    )


@pytest.mark.asyncio
async def test_can_set_persistent_menu_inside_of_constructor():
    global story
    story = Story()

    story.use(messenger.FBInterface(
        page_access_token='qwerty15',
        persistent_menu=[{
            'type': 'postback',
            'title': 'Help',
            'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
        }, {
            'type': 'web_url',
            'title': 'View Website',
            'url': 'http://petersapparel.parseapp.com/'
        }]
    ))

    mock_http = story.use(mockhttp.MockHttpInterface())

    await story.setup()

    # give few a moment for lazy initialization of greeting text
    await asyncio.sleep(0.1)

    mock_http.delete.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty15',
        },
        json={
            'setting_type': 'call_to_actions',
            'thread_state': 'existing_thread',
        }
    )

    mock_http.post.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty15',
        },
        json={
            'setting_type': 'call_to_actions',
            'thread_state': 'existing_thread',
            'call_to_actions': [{
                'type': 'postback',
                'title': 'Help',
                'payload': 'DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
            }, {
                'type': 'web_url',
                'title': 'View Website',
                'url': 'http://petersapparel.parseapp.com/'
            }]
        }
    )


@pytest.mark.asyncio
async def test_remove_persistent_menu():
    global story
    story = Story()

    fb_interface = story.use(messenger.FBInterface(page_access_token='qwerty16'))
    mock_http = story.use(mockhttp.MockHttpInterface())

    await fb_interface.remove_persistent_menu()

    mock_http.delete.assert_called_with(
        'https://graph.facebook.com/v2.6/me/thread_settings',
        params={
            'access_token': 'qwerty16',
        },
        json={
            'setting_type': 'call_to_actions',
            'thread_state': 'existing_thread'
        }
    )


def test_get_fb_as_deps():
    global story
    story = Story()

    story.use(messenger.FBInterface())

    with di.child_scope():
        @di.desc()
        class OneClass:
            @di.inject()
            def deps(self, fb):
                self.fb = fb

        assert isinstance(di.injector.get('one_class').fb, messenger.FBInterface)


def test_bind_fb_deps():
    global story
    story = Story()

    story.use(messenger.FBInterface())
    story.use(mockdb.MockDB())
    story.use(mockhttp.MockHttpInterface())

    with di.child_scope():
        @di.desc()
        class OneClass:
            @di.inject()
            def deps(self, fb):
                self.fb = fb

        assert isinstance(di.injector.get('one_class').fb.http, mockhttp.MockHttpInterface)
        assert isinstance(di.injector.get('one_class').fb.storage, mockdb.MockDB)
