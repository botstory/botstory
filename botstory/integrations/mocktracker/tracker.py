class MockTracker:
    type = 'interface.tracker'

    def event(self, user,
              event_category=None,
              event_action=None,
              event_label=None,
              event_value=None,
              ):
        pass

    def new_message(self, user, data):
        pass

    def new_user(self, user):
        pass

    def story(self, user, story_name, story_part_name):
        pass
