import asyncio
import functools
from .universal_analytics.tracker import Tracker

from ...utils import queue


class GAStatistics:
    type = 'interface.ga.analytics'
    """
    pageview: [ page path ]
    event: category, action, [ label [, value ] ]
    social: network, action [, target ]
    timing: category, variable, time [, label ]
    """

    def __init__(self,
                 tracking_id,
                 ):
        """
        :param tracking_id: should be like UA-XXXXX-Y
        """
        self.tracking_id = tracking_id

    def get_tracker(self, user):
        return Tracker(
            account=self.tracking_id,
            client_id=user['_id'],
        )

    def story(self, user, story_name, story_part_name):
        queue.add(
            functools.partial(self.get_tracker(user).send,
                              'pageview', '{}/{}'.format(story_name, story_part_name),
                              )
        )

    def event(self, user,
              event_category=None,
              event_action=None,
              event_label=None,
              event_value=None,
              ):
        queue.add(
            functools.partial(self.get_tracker(user).send,
                              'event', event_category, event_action, event_label, event_value
                              )
        )
