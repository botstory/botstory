# Idea

Easy reading API to describe dialongs (scenary) of bots in Python language.
Key problem is asyn nature of any dialog - 
we can wait for are months answer from user and should store context 
until that. As well dialog structure should be simply and clear 
and show sequence of questions and reactions. 
 
Sure dialog can be made in diagrams but my thought that code should 
clear enough to show story of dialog and should be open for modification. 

# Draft of API 0.2.0

## Simple example

```python
"""
v0.2.0
Bot asks user about destionation of space travelling.
- stateless story. it stores context of story (current question and results) somewhere (maybe DB)
"""
@story.on('lets go!')
def stateless_story(message):
    return ask_location(message['user'], text='Where do you go?')

    @story.then()
    def then(message):
        store_destination(message['location'])
        return ask_location(message['user'], text='Where do you now?')

    @story.then()
    def then(message):
        store_origin(message['location'])
        return tell(message['user'], 'Thanks! Give me a minute I will find you right spaceship!')
```

## example with bifurcations

```python
"""
v0.2.1
Bot asks user about destionation of space travelling.
- stateless story. it stores context of story (current question and results) somewhere (maybe DB)
"""
@story.on('lets go!')
def stateless_story_with_bifurcation():
    @story.then()
    def request_destination(message):
        return ask_location(message['user'], text='Where do you go?')

    @story.then()
    def receive_destination(message):
        location = message['location]']
        if location == 'stars':
            #cycle back
            return ask_location(message['user'], text='Which star do you prefer?', then=receive_destination)
        elif location == 'planets':
            #cycle back
            return ask_location(message['user'], text='Which planet do you prefer?', then=receive_destination)
        elif:
            return choose_option(top10_planets, 
                                 text='Here is the most popular places. Maybe you would like to choose one?',
                                 then=receive_destination_options)
        else:
            store_destination(message['location'])
            return request_origin(message)

    @story.then()
    def receive_destination_options(message):
        store_destination(message['location'])
        return request_origin(message)

    @story.then()
    def request_origin(message):
        return ask_location(message['user'], text='Where do you now?', topic='get-origin')

    @story.then()
    def receive_origin(message):
        store_origin(message['location'])
        return tell(message['user'], 'Thanks! Give me a minute I will find you right spaceship!')
```

[original sources](https://gist.github.com/hyzhak/b9adcc938abe9bfb4335cf31ef0abbee)
