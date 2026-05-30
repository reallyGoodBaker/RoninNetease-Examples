from ....compact import Component, BaseCompClient

@Component()
class AnimationDilation(BaseCompClient):
    def onCreate(self, _):
        self._value = 1
        self._oldValue = 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._oldValue = self._value
        self._value = value