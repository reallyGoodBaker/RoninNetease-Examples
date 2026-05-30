class Context(object):
    _contexts = {}

    def __init__(self, name):
        self.name = name
        self._records = {} # type: dict[tuple[str, str], dict]
        Context._contexts[name] = self

    def record(self, category, key, value=None):
        if value is None:
            self._records[(category, key)] = True
        else:
            self._records[(category, key)] = value

    def iter(self):
        return self._records.items()

    @staticmethod
    def get(name):
        if name not in Context._contexts:
            return Context(name)
        return Context._contexts.get(name, None)


class ContextRecorder(object):
    def __init__(self, category):
        self._contexts = [] # type: list[Context]
        self._category = category

    def top(self):
        return self._contexts[-1]

    def start(self, name):
        self._contexts.append(Context.get(name))

    def stop(self):
        if len(self._contexts) == 0:
            return
        self._contexts.pop()

    def record(self, key, value=None):
        if len(self._contexts) == 0:
            return
        for ctx in self._contexts:
            ctx.record(self._category, key, value)

    _recorders = {}

    @staticmethod
    def get(category):
        # type: (str) -> ContextRecorder
        if category not in ContextRecorder._recorders:
            ContextRecorder._recorders[category] = ContextRecorder(category)
        return ContextRecorder._recorders[category]