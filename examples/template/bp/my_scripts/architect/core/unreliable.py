
class Unreliable(object):
    @staticmethod
    def _defaultErrorHandler(err):
        # type: (Exception) -> None
        print(err)
        import traceback
        traceback.print_exc()

    def __init__(self):
        self._errorHandler = Unreliable._defaultErrorHandler

    def onError(self, fn):
        self._errorHandler = fn

    def _handleError(self, err):
        try:
            self._errorHandler(err)
            return (None, err)
        except Exception as err:
            print(err)
            return (None, err)

    def tryCall(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs), None
        except Exception as err:
            return self._handleError(err)