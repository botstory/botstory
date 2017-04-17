# State [![support python versions](https://img.shields.io/pypi/pyversions/botstory.svg)](https://pypi.python.org/pypi/botstory/) [![PyPI version](https://img.shields.io/pypi/v/botstory.svg)](https://pypi.python.org/pypi/botstory/) [![Build Status](https://travis-ci.org/botstory/botstory.svg?branch=develop)](https://travis-ci.org/botstory/botstory) [![Coverage Status](https://coveralls.io/repos/github/botstory/botstory/badge.svg?branch=develop)](https://coveralls.io/github/botstory/botstory?branch=develop) [![](https://img.shields.io/pypi/l/botstory.svg)](https://github.com/botstory/botstory/blob/develop/LICENSE.txt)

Under active development

# Get Started

```python
import botstory
from botstory.integrations import aiohttp, fb, mongodb
import os


story = botstory.Story()

# setup modules

# facebook integration
story.use(fb.FBInterface(
    webhook_url='/webhook{}'.format(os.environ.get('FB_WEBHOOK_URL_SECRET_PART', '')),
    webhook_token=os.environ.get('FB_WEBHOOK_TOKEN', None),
))

# http interface 
story.use(aiohttp.AioHttpInterface(
    port=int(os.environ.get('PORT', 8080)),
))

# db interface
story.use(mongodb.MongodbInterface(
    uri=os.environ.get('MONGODB_URI', 'mongo'),
    db_name=os.environ.get('MONGODB_DB_NAME', 'todobot'),
))

# match user queries
@story.on('Hello')
def hello_story():
    @story.part()
    async def say_hi(ctx):
        await story.say('Hello {}!'.format(ctx['user'].name))
        
        
# start service 

asyncio.get_event_loop().run_until_complete(story.start())

```

# Features

- **Use frontier features of Python**
*Botstory is heavily based on brand new Python features, like async/await.
We always focus on its evolution and don't support legacy versions (<3.5).*

- **All messengers in one place**
*Right now botstory supports only fb Messengers, but we are going to 
support many others. So you can use common code base for different 
platform and seamlessly organize communication between them. As well 
we always open for contribution. And if you sure that one platform 
should be here, just drop PR with unit tests.*

- **More than 90% test coverage**
*Code is covered by tests except few trivial places. 
That way we are almost sure that any changes won't break other 
functionality. And any breaking features won't come hidden.*  

- **Declarative user dialogs**
*Match user queries, lead, fork and loop dialogs.*

- **Store use session**
*We remember user context and could return it any time and on any 
app instance. So you can scale app, and start and stop it without 
fair of bot amnesia.*

- **Easily scale**
*We focus on micro-services and especially on Docker. So you can 
very easy scale any part of the system.*

- **Open source**
*MIT licence gives you many rights. And we are very open for your 
contribution and would love to hear about your experience.*

and many other features

# Background

We are developing botstory mindful of the need to have easily reading API 
which describe dialogues (scenario) of bots in Python language.
Key problem is async nature of any dialog - 
we can wait answer from user for are months and should store context 
until that. As well dialog structure should be simply and clear 
and show sequence of questions and reactions. 
 
Sure dialog can be made in diagrams but my thought that code should 
clear enough to show story of dialog and should be open for modification.

As well it is too hard to use git for store versions of diagrams.

# Install

```bash
pip install botstory
```

# Draft of API 0.0.63

## Simple example

```python
"""
v0.0.63
Bot asks user about destination of space travelling.
- stateless story. it stores context of story (current question and results) somewhere (maybe DB)
"""
@story.on('lets go!')
def stateless_story():
    @story.part()
    async def ask_destination(ctx):
        return await story.ask('Where do you go?', 
                               user=ctx['user'])

    @story.part()
    async def ask_origin(ctx):
        store_destination(ctx['message']['location'])
        return await story.ask('Where do you now?', 
                               user=ctx['user'])

    @story.part()
    async def thanks(ctx):
        store_origin(ctx['message']['location'])
        return await story.say('Thanks!\n'
                               'Give me a minute I will find you right spaceship!', 
                               user=ctx['user'])
```

## example with bifurcations

```python
"""
v0.0.63
Bot asks user about destination of space travelling.
- stateless story. it stores context of story (current question and results) somewhere (maybe DB)
"""
@story.on('lets go!')
def stateless_story_with_bifurcation():
    @story.part()
    async def request_destination(ctx):
        return await story.ask('Where do you go?',
                               user=ctx['user'])

    @story.case('stars')
    def stars():
        @story.part()
        async def receive_destination_options(ctx):
            return await story.ask('Which star do you prefer?', 
                                   user=ctx['user'])

    @story.case('planets')
    def planets():
        @story.part()
        async def request_origin(ctx):
            return await story.ask('Which planet do you prefer?', 
                                   user=ctx['user'])

    @story.case(default=True)
    def other():
        @story.part()
        async def choose_from_top10_planets(ctx):
            return await choose_option(top10_planets,
                                       text='Here is the most popular places. Maybe you would like to choose one?',
                                       user=ctx['user'])

    @story.part()
    async def receive_destination(ctx):
        store_destination(ctx['message']['location'])
        return await story.say('Thanks! Give me a minute I will find you right spaceship!', 
                               user=ctx['user'])

```

## example of callable function

```python

from ... import chat, story
from ...matchers.any import any
from ...matchers.location import location
from ...matchers.text import text


@story.callable()
def ask_location():
    """
    v0.2.2

    case/default/recursion version
    based on indents and no any goto

    :return:
    """
    @story.begin()
    def ask(body=None, options=None, user=None):
        if not options:
            # default aliases for current user
            # like 'home', 'work', or other
            options = default_aleases(user)
        if not body:
            body = default_question(user)
        chat.say(body, options, user)
        return Switch({
            'location': location.Any(),
            'option': option.Any(),
            'text': text.Any(),
        })

    # 2 wait for answer
    @story.case(match='location')
    def location_case():
        @story.part()
        def return_location(message):
            return EndOfStory({
                'location': message,
            })

    @story.case(match='option')
    def aliase():
        @story.part()
        def return_aliase(message):
            # it can be location or any other message data
            return EndOfStory({
                'location': message['option']['data'],
            })

    @story.case(match='text')
    def text_case():
        @story.part()
        def parse_text(message):
            text_message = message['text']['raw']
            # try aliases (common names like home, work, or other)
            aliase = aliases.lookup(text_message)
            if aliase:
                return return EndOfStory({
                    'location': aliase['data'],
                })

            # if it is not alias maybe it is name of some place
            options = googlemap.lookup_location_by_name(text_message)
            if len(options) > 0:
                return {
                    'args': 'many',
                    'wait': chat.choose_option(
                        body='We have few options',
                        options=[{'title': o.name, 'data': o.json()} for o in options],
                        user=message['user'],
                    ),
                }
            else:
                return {
                    'args': None,
                }

        @story.case(equal_to='many')
        def have_options():
            @story.part()
            def choose_one_location_from_many(message):
                location = message['option']['data']
                if location:
                    return EndOfStory({
                        'location': location,
                    })
                else:
                    # choose something else
                    pass

        @story.case(equal_=None)
        def not_any_option():
            @story.check_alternative_stories()
            @story.part()
            def do_you_have_other_data(message):
                text_message = message['text']['raw']
                return chat.ask(
                    body='I can not find {} on map. Do you mean something else? Skip it?'.format(text_message),
                    options=[{
                        'title': 'skip',
                        'data': 'skip',
                    }],
                    user=message['user'],
                )

            @story.part()
            def unknown_name(message):
                if message['option']['data'] == 'skip':
                    return EndOfStory({
                        'location': None,
                    })
                else:
                    # TODO: restart (tail recursion?)
                    return {
                        # ????
                        'recursion': location_case,
                    }

    @story.case(default=True)
    def default_case():
        @story.check_alternative_stories()
        @story.part()
        def react_on_joke(message):
            chat.say('Very funny! :)', message['user'])
            return EndOfStory({
                'location': None,
            })


@story.callable()
def ask_date_time():
    """
    
    ask date time from user

    :return:
    """
    @story.part()
    def ask(body=None, options=None, user=None):
        if not options:
            # default aliases for current user
            # like 'home', 'work', or other
            options = default_aleases(user)
        if not body:
            body = default_question(user)
        chat.say(body, options, user)
        return SwitchOnValue({
            'option': option.Any(),
            'text': text.Any(),
        })
    
    @story.case(match='option')
    def option_case():
        @story.part()
        def return_option(message):
            return {
                'return': message['option']['data']
            }
        
    @story.case(match='text')
    def text_case():
        @story.part()
        def parse_text(message):
            datetime_options = parse_text_to_date_time(message)
            if len(datetime_options) == 0:
                return EndOfStory({
                    'datetime': datetime_options,
                })
            elif len(datetime_options) == 1:
                return EndOfStory({
                    'datetime': datetime_options,
                })
            else:
                return chat.choose_option(
                    body='Hm what time do you mean?',
                    options=[{
                        'title': d['name'], 'data': {'datetime': d['value']}
                    } for d in datetime_options],
                    user=message['user'],
                )
            
        @story.part()
        def return_option(message):
            return EndOfStory({
                'datetime': message['option']['data'],
            })


```
[original sources](https://gist.github.com/hyzhak/b9adcc938abe9bfb4335cf31ef0abbee)
