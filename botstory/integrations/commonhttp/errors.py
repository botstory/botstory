class HttpRequestError(Exception):
    """HTTP error.
    Shortcut for raising HTTP errors with custom code, message and headers.
    :param int code: HTTP Error code.
    :param str message: (optional) Error message.
    :param list of [tuple] headers: (optional) Headers to be sent in response.

    based on https://github.com/KeepSafe/aiohttp/blob/v1.0.5/aiohttp/errors.py#L72
    """

    code = 0
    message = ''
    headers = None

    def __init__(self, *, code=None, message='', headers=None):
        if code is not None:
            self.code = code
        self.headers = headers
        self.message = message

        super().__init__("%s, message='%s'" % (self.code, message))
