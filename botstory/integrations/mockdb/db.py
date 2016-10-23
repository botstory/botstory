from ... import utils


class MockDB:
    def __init__(self):
        self.session = None
        self.user = None

    async def get_session(self, **kwargs):
        return self.session

    async def set_session(self, session):
        self.session = session

    async def new_session(self, **kwargs):
        return kwargs

    async def get_user(self, **kwargs):
        return self.user

    async def set_user(self, user):
        self.user = user

    async def new_user(self, **kwargs):
        self.user = utils.JSDict({**kwargs})
        return self.user
