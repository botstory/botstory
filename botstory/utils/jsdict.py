import json
import logging
logger = logging.getLogger(__name__)


class JSDict:
    def __init__(self, response):
        # don't use self.__dict__ here
        self._response = response

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, key):
        return self._response.get(key, None)

    def __getitem__(self, item):
        return self._response.get(item, None)

    def __str__(self):
        return 'JSDict({})'.format(json.dumps(self._response))

    def __iter__(self):
        logger.debug('JSDict.__iter__')
        logger.debug(list(iter(self._response)))
        return iter(self._response)

    def items(self):
        return self._response.items()
