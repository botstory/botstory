from .universal_analytics import Tracker


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

    def story_part(self, user, story_name, story_part_name):
        tracker = Tracker.create(
            account=self.tracking_id,
            client_id=user['_id'],
        )
        # TODO: should make it async because we don't need
        # to wait result of tracking
        tracker.send('pageview', '{}/{}'.format(story_name, story_part_name))
