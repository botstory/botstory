class FBInterface:
    type = 'interface.facebook'

    def __init__(self, token=None):
        self.token = token

    def send_text_message(self, sender, text, options=None):
        # TODO
        pass
