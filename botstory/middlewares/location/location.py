from botstory import matchers, utils


def get_location(ctx):
    return utils.safe_get(ctx, 'session', 'data', 'location')


@matchers.matcher()
class Any:
    type = 'Location.Any'

    def __init__(self):
        pass

    def validate(self, ctx):
        return get_location(ctx)
