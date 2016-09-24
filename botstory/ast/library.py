import logging
import itertools

from . import parser

logger = logging.getLogger(__name__)


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

    def get_story_by_topic(self, topic, stack=[]):
        """
        get story and take about context stack
        :param topic:
        :param stack:
        :return:
        """
        options = [s for s in [*self.callable_stories, *self.message_handling_stories] if s.topic == topic]

        if len(options) > 0:
            return options[0]

        if len(options) == 0 and stack and len(stack) > 0:
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

        return None
