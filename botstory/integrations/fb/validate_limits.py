class Invalid(BaseException):
    pass


def validate_greeting_text(message):
    if len(message) > 160:
        raise Invalid('greeting text should not exceed 160 length in characters')


def validate_persistent_menu(menu):
    if len(menu) > 5:
        raise Invalid('menu should not exceed 5 call to actions')

    for item in menu:
        if len(item['title']) > 30:
            raise Invalid('menu item title should not exceed 30 characters')

        if item['type'] == 'postback' and len(item['payload']) > 1000:
            raise Invalid('menu item payload should not exceed 1000 characters')
