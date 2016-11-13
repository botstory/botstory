import asyncio
from .universal_analytics.tracker import Tracker


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

    async def story_part(self, user, story_name, story_part_name):
        tracker = Tracker(
            account=self.tracking_id,
            client_id=user['_id'],
        )

        # TODO: should make it async because we don't need
        # to wait result of tracking
        await tracker.send('pageview', '{}/{}'.format(story_name, story_part_name))

    async def event(self, user,
                    event_category=None,
                    event_action=None,
                    event_label=None,
                    event_value=None,
                    fields_object=None,
                    ):
        tracker = Tracker(
            account=self.tracking_id,
            client_id=user['_id'],
        )

        # TODO: should make it async because we don't need
        # to wait result of tracking
        await tracker.send('event',
                           event_category, event_action, event_label, event_value, fields_object)


async def store_story_page():
    s = GAStatistics(tracking_id='UA-86885596-3')
    await s.story_part({'_id': 'test-user'},
                       'test-story',
                       'test-part',
                       )


async def trigger_event():
    import random
    s = GAStatistics(tracking_id='UA-86885596-3')
    await s.event({'_id': 'test-user'},
                  event_category='test-category',
                  event_action=random.choice(
                      'attainment, achievement, accomplishment, progress, breakthrough, effort'.split(',')
                  ).strip(),
                  event_value=str(random.randint(100000, 999999)),
                  )


if __name__ == '__main__':
    print('just logged story parts')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(trigger_event())
else:
    print('not logged')
