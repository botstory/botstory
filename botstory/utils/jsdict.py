import json


class JSDict:
    def __init__(self, response):
        # don't use self.__dict__ here
        self._response = response

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, key):
        try:
            return self._response[key]
        except KeyError:
            return None

    def __str__(self):
        return 'JSDict({})'.format(json.dumps(self._response))
