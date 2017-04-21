import logging
from .. import di
from ..integrations.mocktracker import tracker as tracker_module

logger = logging.getLogger(__name__)


@di.desc(reg=False)
class Users:
    def __init__(self):
        self._tracker = tracker_module.MockTracker()

    @di.inject()
    def add_tracker(self, tracker):
        logger.debug('add_tracker')
        logger.debug(tracker)
        self._tracker = tracker

    def on_new_user_comes(self, user):
        """
        each interface that create new user should call this method.
        as well if someone need to catch new user it is good place
        to do it

        :param user:
        :return:
        """
        self._tracker.new_user(user)

    def clear(self):
        self._tracker = tracker_module.MockTracker()
