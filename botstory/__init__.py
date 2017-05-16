from .ast.callable import EndOfStory
from .ast.forking import SwitchOnValue, Undefined
from .story import Story
import os

__all__ = [EndOfStory, Story, SwitchOnValue]

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'version.txt')) as version_file:
    __version__ = version_file.read().strip()
