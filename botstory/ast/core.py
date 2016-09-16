class Core:
    def __init__(self):
        self.stories = []
        self.callable = []

    def clear(self):
        self.stories = []
        self.callable = []

    def add_story(self, one_story):
        self.stories.append(one_story)

    def add_callable(self, one_callable):
        self.callable.append(one_callable)

    def get_callable_by_topic(self, topic):
        return [s for s in self.callable if s['topic'] == topic][0]

    def get_right_story(self, message):
        matched_stories = [task for task in self.stories if task['validator'].validate(message)]
        return matched_stories[0] if len(matched_stories) > 0 else None

    def get_story_by_topic(self, topic):
        return [s for s in [*self.callable, *self.stories] if s['topic'] == topic][0]
