from . import matchers
from .middlewares.any import any
from .middlewares.text import text
from .utils import is_string

core = {
    'stories': []
}


def clear():
    core['stories'] = []


def get_validator(receive):
    if isinstance(receive, list):
        return any.AnyOf([get_validator(r) for r in receive])
    elif is_string(receive):
        return text.Match(receive)
    else:
        return receive


def on(receive):
    def fn(one_story):
        validator = get_validator(receive)

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
    session = message['session']
    if session.wait_for_message:
        validator = matchers.deserialize(session.wait_for_message['data'])
        if validator.validate(message):
            step = session.wait_for_message['step']
            session.wait_for_message = None
            story = [s for s in core['stories'] if s['topic'] == session.current_topic][0]
            return process_story(
                idx=step,
                message=message,
                story=story,
                session=session,
            )

    matched_stories = [task for task in core['stories'] if task['validator'].validate(message)]
    if len(matched_stories) == 0:
        return

    story = matched_stories[0]
    session.current_topic = story['topic']
    return process_story(
        idx=0,
        message=message,
        story=story,
        session=session,
    )


def process_story(session, message, story, idx=0):
    steps = story['parts']
    while idx < len(steps):
        step = steps[idx]
        idx += 1
        result = step(message)
        if result:
            # TODO: should wait result of async operation
            # (for example answer from user)
            result = get_validator(result)
            session.wait_for_message = {
                'type': result.type,
                'data': matchers.serialize(result),
                'step': idx,
            }
            return
