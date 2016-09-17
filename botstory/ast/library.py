class StoriesLibrary:
    """
    storage of all available stories
    """
    def __init__(self):
        self.message_handling_stories = []
        self.callable_stories = []

    def clear(self):
        self.message_handling_stories = []
        self.callable_stories = []

    def add_message_handler(self, story):
        self.message_handling_stories.append(story)

    def add_callable(self, story):
        self.callable_stories.append(story)

    def get_callable_by_topic(self, topic):
        return [s for s in self.callable_stories if s.topic == topic][0]

    def get_right_story(self, message):
        matched_stories = [story for story in self.message_handling_stories
                           if story.extensions['validator'].validate(message)]
        return matched_stories[0] if len(matched_stories) > 0 else None

    def get_story_by_topic(self, topic):
        return [s for s in [*self.callable_stories, *self.message_handling_stories] if s.topic == topic][0]
