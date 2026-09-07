from ..engine.architect.compact import (
    Component, BaseCompClient,
)

class FeatureBasic(object):
    def __init__(self, name, params):
        self.name = name
        self.params = params

@Component(singleton=True)
class LocalFeaturesComponent(BaseCompClient):

    def onCreate(self, entityId):
        self._features = {} # type: dict[str, FeatureBasic]
        self._discardedFeatures = set()
        self._handlers = {} # type: dict[str, list]

    def applyFromDict(self, dataDict):
        # type: (dict) -> None
        for k, v in dataDict.items():
            self.applyFeature(k, v)

    def hasFeature(self, name):
        feature = self._features.get(name)
        return False if not feature else name not in self._discardedFeatures

    def getFeature(self, name):
        return self._features.get(name)

    def addFeature(self, name, params):
        existed = self._features.get(name)
        if existed:
            return
        feature = FeatureBasic(name, params)
        self._features[name] = feature

    def registerFeatureHandlers(self, name, onApply=None, onRemove=None):
        """
        注册某个 feature 生效/失效时的回调。

        :param onApply: onApply(name, params)
        :param onRemove: onRemove(name)
        """
        self._handlers.setdefault(name, []).append((onApply, onRemove))

    def _callApplyHandlers(self, name):
        feature = self._features.get(name)
        if not feature:
            return
        for onApply, _ in self._handlers.get(name, []):
            if onApply:
                onApply(name, feature.params)

    def _callRemoveHandlers(self, name):
        for _, onRemove in self._handlers.get(name, []):
            if onRemove:
                onRemove(name)

    def removeFeature(self, name):
        if name not in self._features:
            return
        if self.hasFeature(name):
            self.discardFeature(name)
        self._features.pop(name, None)
        self._discardedFeatures.discard(name)

    def clear(self):
        # 切换武器/重置时会清空全部 feature
        for name in list(self._features.keys()):
            if self.hasFeature(name):
                self.discardFeature(name)
        self._features.clear()
        self._discardedFeatures.clear()

    def discardFeature(self, name):
        if not self.hasFeature(name):
            return
        self._discardedFeatures.add(name)
        self._callRemoveHandlers(name)

    def enableFeature(self, name):
        feature = self._features.get(name)
        if not feature:
            return
        if name not in self._discardedFeatures:
            return
        self._discardedFeatures.discard(name)
        self._callApplyHandlers(name)

    def applyFeature(self, name, params):
        wasEnabled = self.hasFeature(name)
        self.addFeature(name, params)
        if not wasEnabled:
            self._discardedFeatures.discard(name)
            self._callApplyHandlers(name)
