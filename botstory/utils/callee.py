import inspect


def callee():
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    return ' / '.join([calframe[i][3] for i in range(1, len(calframe))])
