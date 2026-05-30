class DBSource:
    def getData(self, key):
        # type: (str) -> object
        pass
    
    def setData(self, key, value):
        # type: (str, object) -> None
        pass

    def removeData(self, key):
        # type: (str) -> None
        pass

    def clearData(self):
        # type: () -> None
        pass

    def createView(self, key):
        # type: (str) -> DatabaseView
        return DatabaseView(self, key)
 
    def createArrayView(self, key):
        # type: (str) -> DatabaseArrayView
        return DatabaseArrayView(self, key)

    _inst = None

    @classmethod
    def getInstance(cls):
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst


class DatabaseView:
    def __init__(self, db, key):
        # type: (DBSource, str) -> None
        self.cache = db.getData(key) or {}
        self.db = db
        self.key = key

    def get(self, item, default=None):
        v = self.cache.get(item) # type: ignore
        if v is None:
            self.set(item, default)
            return default
        return v
    
    def set(self, key, value):
        self.cache[key] = value # type: ignore
        self.db.setData(self.key, self.cache)

    def has(self, item):
        return item in self.cache

    def batch(self, updater):
        cache = self.cache
        for k, v in self.cache.items(): # type: ignore
            updater(v, k, cache)


class DatabaseArrayView:
    def __init__(self, db, key):
        # type: (DBSource, str) -> None
        self.cache = db.getData(key) or []
        self.db = db
        self.key = key

    def get(self, item, default=None):
        v = self.cache[item] # type: ignore
        if v is None:
            self.set(item, default)
            return default
        return v
    
    def set(self, key, value):
        self.cache[key] = value # type: ignore
        self.db.setData(self.key, self.cache)

    def batch(self, updater):
        cache = self.cache
        for i, v in enumerate(self.cache): # type: ignore
            updater(v, i, cache)

    def size(self):
        return len(self.cache) # type: ignore

    def iter(self):
        return self.cache