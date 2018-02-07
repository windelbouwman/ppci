""" Event system """


class Event:
    def __init__(self):
        self._handlers = []

    def __call__(self):
        for handler in self._handlers:
            handler()

    def __iadd__(self, handler):
        assert callable(handler)
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self


class Events:
    def __init__(self):
        self.on_stop = Event()
        self.on_start = Event()
