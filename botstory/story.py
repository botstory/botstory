import logging

logger = logging.getLogger(__name__)

from .ast import callable as callable_module, common, core, parser, processor

# instantiate handlers

core_instance = core.Core()

parser_instance = parser.Parser()

story_processor_instance = processor.StoryProcessor(parser_instance, core_instance)

common_stories_instance = common.CommonStoriesAPI(
    parser_instance, core_instance)

callable_stories_instance = callable_module.CallableStoriesAPI(
    core_instance=core_instance,
    parser_instance=parser_instance,
    processor_instance=story_processor_instance,
)

# expose story API:

on = common_stories_instance.on
part = common_stories_instance.part
callable = callable_stories_instance.callable

# expose message handler API:

match_message = story_processor_instance.match_message
