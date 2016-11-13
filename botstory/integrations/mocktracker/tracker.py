class MockTracker:
    type = 'interface.tracker'

    def story(self, user, story_name, story_part_name):
        pass

    def event(self, user,
              event_category=None,
              event_action=None,
              event_label=None,
              event_value=None,
              ):
        pass
