import logging

logger = logging.getLogger(__name__)

from .ast import callable as callable_module, common, library, parser, processor

# instantiate handlers

stories_library = library.StoriesLibrary()

parser_instance = parser.Parser()

story_processor_instance = processor.StoryProcessor(
    parser_instance,
    stories_library)

common_stories_instance = common.CommonStoriesAPI(
    parser_instance,
    stories_library)

callable_stories_instance = callable_module.CallableStoriesAPI(
    library=stories_library,
    parser_instance=parser_instance,
    processor_instance=story_processor_instance,
)

# expose story API:

on = common_stories_instance.on
part = common_stories_instance.part
callable = callable_stories_instance.callable

# expose message handler API:

match_message = story_processor_instance.match_message
