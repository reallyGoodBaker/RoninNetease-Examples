from ..conf import ANNOTATION

def _getAnnotation(target):
    if hasattr(target, ANNOTATION):
        return getattr(target, ANNOTATION)
    return None

def _getOrCreateAnnotation(target):
    if hasattr(target, ANNOTATION):
        return getattr(target, ANNOTATION)
    anno = {}
    setattr(target, ANNOTATION, anno)
    return anno

class AnnotationHelper:
    @staticmethod
    def addAnnotation(target, key, value):
        # type: (type, object, object) -> None
        annotation = _getOrCreateAnnotation(target)
        annotation[key] = value

    @staticmethod
    def getAnnotation(target, key):
        # type: (type, object) -> object
        anno = _getAnnotation(target)
        if not anno:
            return None
        return anno.get(key)
    
    @staticmethod
    def findAnnotatedMethods(target, key):
        # type: (object, object) -> list
        methods = []
        for attr_name in dir(target):
            attr = getattr(target, attr_name)
            if callable(attr) and hasattr(attr, ANNOTATION):
                if key in getattr(attr, ANNOTATION):
                    methods.append(attr)
        return methods
    
    @staticmethod
    def findAnnotatedClasses(target, key):
        # type: (type, object) -> list
        classes = []
        for attr_name in dir(target):
            attr = getattr(target, attr_name)
            if isinstance(attr, type) and hasattr(attr, ANNOTATION):
                if key in getattr(attr, ANNOTATION):
                    classes.append(attr)
        return classes
    
    @staticmethod
    def findAnnotatedAttributes(target, key):
        # type: (type, object) -> list
        attributes = []
        for attr_name in dir(target):
            attr = getattr(target, attr_name)
            if not callable(attr) and hasattr(attr, ANNOTATION):
                if key in getattr(attr, ANNOTATION):
                    attributes.append(attr)
        return attributes