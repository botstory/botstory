import logging

from . import parser
from .. import di

logger = logging.getLogger(__name__)


class StoriesScope:
    def __init__(self):
        self.stories = []

    def add(self, story):
        self.stories.append(story)

    def match(self, message):
        matched_stories = [
            story for story in self.stories
            if story.extensions['validator'].validate(message)]
        return matched_stories[0] if len(matched_stories) > 0 else None

    def by_topic(self, topic):
        return [s for s in self.stories if s.topic == topic]


@di.desc(reg=False)
class StoriesLibrary:
    """
    storage of
     - global scope stories
     - callable stories
    """

    def __init__(self):
        self.callable_scope = StoriesScope()
        self.global_scope = StoriesScope()

    def clear(self):
        self.callable_scope = StoriesScope()
        self.global_scope = StoriesScope()

    def add_global(self, story):
        self.global_scope.add(story)

    def add_callable(self, story):
        self.callable_scope.add(story)

    def get_callable_by_topic(self, topic):
        return self.callable_scope.by_topic(topic)[0]

    def get_right_story(self, message):
        return self.global_scope.match(message)

    def get_story_by_topic(self, topic, stack=None):
        """
        get story and take about context stack
        :param topic:
        :param stack:
        :return:
        """
        options = self.callable_scope.by_topic(topic) + self.global_scope.by_topic(topic)

        if len(options) > 0:
            return options[0]

        if not stack or len(stack) == 0:
            return None

        # Or it seems that we are somewhere on a leaves
        # so we're trying to find root of last story and than
        # get right sub story
        parent = self.get_story_by_topic(stack[-1]['topic'], stack[:-2])
        if not parent:
            return None
        inner_stories = [
            story.children for story in parent.story_line if isinstance(story, parser.StoryPartFork)
            ]

        inner_stories = [item for sublist in inner_stories for item in sublist]

        child_options = [story for story in inner_stories if story.topic == topic]
        if len(child_options) == 0:
            return None
        elif len(child_options) == 1:
            return child_options[0]
        else:
            raise Error('We have few options with the same name {}'.format(topic))
