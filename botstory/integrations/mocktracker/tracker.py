import logging

logger = logging.getLogger(__name__)


class MockTracker:
    type = 'interface.tracker'

    def event(self, *args, **kwargs):
        logging.debug('event')
        logging.debug(kwargs)
        logging.debug(args)

    def new_message(self, *args, **kwargs):
        logging.debug('new_message')
        logging.debug(kwargs)
        logging.debug(args)

    def new_user(self, *args, **kwargs):
        logging.debug('new_user')
        logging.debug(kwargs)
        logging.debug(args)

    def story(self, *args, **kwargs):
        logging.debug('story')
        logging.debug(kwargs)
        logging.debug(args)
