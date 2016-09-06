from .middlewares.text.text import Text

core = {
    'current_topic': None,
    'current_part': 0,
    'topic': None,
    'stories': []
}


def clear():
    core['stories'] = []


def on(receive):
    def fn(one_story):
        validator = Text.Match(receive)

        core['stories'].append({
            'validator': validator,
            'topic': one_story.__name__,
            'parts': []
        })

        # to parse inner sub-stories
        one_story()

    return fn


def then():
    def fn(part_of_story):
        last_story = core['stories'][-1]
        last_story['parts'].append(part_of_story)

    return fn


def match_message(message):
    matched_stories = [task for task in core['stories'] if task['validator'].validate(message)]
    if len(matched_stories) == 0:
        return

    story = matched_stories[0]
    core['current_topic'] = story['topic']
    core['current_part'] = 0
    parts = story['parts']
    idx = 0
    while idx < len(parts):
        part = parts[idx]
        idx += 1
        result = part(message)
        # TODO: work with async requests
