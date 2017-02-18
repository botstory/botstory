import botstory
from botstory.utils import build_fake_session, build_fake_user


class Talk:
    def __init__(self, session=None, user=None, story=None):
        if not user:
            user = build_fake_user()
        if not session:
            session = build_fake_session()
        self.session = session
        self.user = user
        self.story = story

    def __enter__(self):
        self.story = botstory.Story()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.story.clear()
        return self

    def __call__(self, *args, **kwargs):
        return self.wrap_user_talk(args[0])

    async def wrap_user_talk(self, fn):
        async def fn_wrapper(payload):
            mutated_ctx = await fn(payload,
                                   self.session,
                                   self.user,
                                   self.story)
            self.session = mutated_ctx['session']
            self.user = mutated_ctx['user']
            return mutated_ctx

        return fn_wrapper


async def location(loc, session=None, user=None, story=None):
    return await story.match_message({
        'data': {
            'location': loc,
        },
        'session': session,
        'user': user
    })


async def pure_text(text, session=None, user=None, story=None):
    return await story.match_message({
        'data': {
            'text': {'raw': text},
        },
        'session': session,
        'user': user
    })


async def option(payload, session=None, user=None, story=None):
    return await story.match_message({
        'data': {
            'option': payload,
        },
        'session': session,
        'user': user
    })
