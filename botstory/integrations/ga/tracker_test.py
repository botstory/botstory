from . import tracker
from ... import utils


def test_should_put_in_queue_story_part():
    user = utils.build_fake_user()
    ga = tracker.GAStatistics(account_id='UA-XXXXX-Y')
    ga.story_part(user, 'one story', 'one part')

    # TODO: should test that we put story log in a queue
    assert True
