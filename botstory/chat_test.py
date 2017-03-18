import aiohttp
import logging
import pytest

from botstory import Story
import botstory.integrations.fb.messenger
from botstory.middlewares import location
from botstory.utils import answer, SimpleTrigger

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_interface(mocker):
    mocker.patch.object(
        botstory.integrations.fb.messenger.FBInterface,
        'send_text_message',
        aiohttp.test_utils.make_mocked_coro('something'),
    )
    mocker.patch.object(
        botstory.integrations.fb.messenger.FBInterface,
        'send_list',
        aiohttp.test_utils.make_mocked_coro('something'),
    )
    mocker.patch.object(
        botstory.integrations.fb.messenger.FBInterface,
        'send_template',
        aiohttp.test_utils.make_mocked_coro('something'),
    )
    return botstory.integrations.fb.messenger.FBInterface()


@pytest.mark.asyncio
async def test_should_say(mock_interface):
    with answer.Talk() as talk:
        story = talk.story
        story.use(mock_interface)

        @story.on('hi there!')
        def one_story():
            @story.part()
            async def then(message):
                await story.say('Nice to see you!', message['user'])

        await talk.pure_text('hi there!')

        mock_interface.send_text_message.assert_called_once_with(
            recipient=talk.user,
            text='Nice to see you!',
            options=None,
        )


# TODO: move to middlewares/location/test_location.py
@pytest.mark.asyncio
@pytest.mark.skip
async def test_ask_location(mock_interface):
    with answer.Talk() as talk:
        story = talk.story
        story.use(mock_interface)

        @story.on('SOS!')
        def one_story():
            @story.part()
            async def then(message):
                await story.ask_location('Hey, bro! Where is your rocket?', message['user'])

        await talk.pure_text('SOS!')

        mock_interface.send_text_message.assert_called_once_with(talk.user, text='Hey, bro! Where is your rocket?')


@pytest.mark.asyncio
@pytest.mark.skip
async def test_get_location_as_result_of_asking_of_location(mock_interface):
    trigger = SimpleTrigger()

    with answer.Talk() as talk:
        story = talk.story
        story.use(mock_interface)

        @story.on('SOS!')
        def one_story():
            @story.part()
            def then(ctx):
                return story.ask_location('Hey, bro! Where is your rocket?', ctx['user'])

            @story.part()
            def then(ctx):
                trigger.receive(location.get_location(ctx))

        await talk.pure_text('SOS!')
        await talk.location('somewhere')

        assert trigger.result() == 'somewhere'


@pytest.mark.asyncio
async def test_should_list_elements(mock_interface):
    with answer.Talk() as talk:
        story = talk.story
        story.use(mock_interface)

        @story.on('hi there!')
        def one_story():
            @story.part()
            async def then(ctx):
                await story.list_elements(elements=[{
                    'title': 'Classic T-Shirt Collection',  # (*) required
                    'image_url': 'https://peterssendreceiveapp.ngrok.io/img/collection.png',
                    'subtitle': 'See all our colors',
                    'default_action': {
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/shop_collection',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    },
                    'buttons': [{
                        'title': 'View',
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/collection',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    }]
                }, {
                    'title': 'Classic White T-Shirt',
                    'image_url': 'https://peterssendreceiveapp.ngrok.io/img/white-t-shirt.png',
                    'subtitle': '100% Cotton, 200% Comfortable',
                    'default_action': {
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/view?item=100',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    },
                    'buttons': [{
                        'title': 'Shop Now',
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/shop?item=100',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    }]
                }], buttons=[{
                    'title': 'View More',
                    'payload': 'payload',
                }], user=ctx['user'])

        await talk.ask('hi there!')

        mock_interface.send_list.assert_called_once_with(
            recipient=talk.user,
            elements=[{
                'title': 'Classic T-Shirt Collection',  # (*) required
                'image_url': 'https://peterssendreceiveapp.ngrok.io/img/collection.png',
                'subtitle': 'See all our colors',
                'default_action': {
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/shop_collection',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                },
                'buttons': [{
                    'title': 'View',
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/collection',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                }]
            }, {
                'title': 'Classic White T-Shirt',
                'image_url': 'https://peterssendreceiveapp.ngrok.io/img/white-t-shirt.png',
                'subtitle': '100% Cotton, 200% Comfortable',
                'default_action': {
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/view?item=100',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                },
                'buttons': [{
                    'title': 'Shop Now',
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/shop?item=100',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                }]
            }], buttons=[{
                'title': 'View More',
                'payload': 'payload',
            }],
            options=None,
        )


@pytest.mark.asyncio
async def test_should_send_tempalate_based_message(mock_interface):
    with answer.Talk() as talk:
        story = talk.story
        story.use(mock_interface)

        payload = {
            'template_type': 'receipt',
            'recipient_name': 'Stephane Crozatier',
            'order_number': '12345678902',
            'currency': 'USD',
            'payment_method': 'Visa 2345',
            'order_url': 'http://petersapparel.parseapp.com/order?order_id=123456',
            'timestamp': '1428444852',
            'elements': [{
                'title': 'Classic White T-Shirt',
                'subtitle': '100% Soft and Luxurious Cotton',
                'quantity': 2,
                'price': 50,
                'currency': 'USD',
                'image_url': 'http://petersapparel.parseapp.com/img/whiteshirt.png'
            }, {
                'title': 'Classic Gray T-Shirt',
                'subtitle': '100% Soft and Luxurious Cotton',
                'quantity': 1,
                'price': 25,
                'currency': 'USD',
                'image_url': 'http://petersapparel.parseapp.com/img/grayshirt.png'
            }],
            'address': {
                'street_1': '1 Hacker Way',
                'street_2': '',
                'city': 'Menlo Park',
                'postal_code': '94025',
                'state': 'CA',
                'country': 'US'
            },
            'summary': {
                'subtotal': 75.00,
                'shipping_cost': 4.95,
                'total_tax': 6.19,
                'total_cost': 56.14
            },
            'adjustments': [{
                'name': 'New Customer Discount',
                'amount': 20
            }, {
                'name': '$10 Off Coupon',
                'amount': 10
            }]
        }

        await story.send_template(payload,
                                  user=talk.user)

        mock_interface.send_template.assert_called_once_with(recipient=talk.user,
                                                             payload=payload)
