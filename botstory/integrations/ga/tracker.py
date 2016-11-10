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
                 account_id,
                 ):
        """
        :param account_id: should be like UA-XXXXX-Y
        """
        self.account_id = account_id

    def story_part(self, user, story_name, story_part_name):
        tracker = Tracker.create(
            account=self.account_id,
            client_id=user['_id'],
        )
        # TODO: should make it async because we don't need to
        # wait result of logging
        tracker.send('pageview', '{}/{}'.format(story_name, story_part_name))
