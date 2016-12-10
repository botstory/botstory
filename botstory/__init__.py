from . import chat, story


class Story:
    def on(self, receive):
        return story.on(receive)

    def part(self):
        return story.part()

    async def ask(self, body, options=None, user=None):
        return await chat.ask(body, options, user)

    def use(self, middleware):
        return story.use(middleware)

    async def setup(self, event_loop=None):
        return await story.setup(event_loop)

    async def start(self, event_loop=None):
        return await story.start(event_loop)

    def clear(self):
        return story.clear()
