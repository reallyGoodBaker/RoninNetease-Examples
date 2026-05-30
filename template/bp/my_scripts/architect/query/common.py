from ..component import getComponent, getComponentWithQuery, getEntities
from ..component.core import components, _findNamedComp, singletonId
from ..core.basic import serverApi, clientApi, isServer
from ..core.annotation import AnnotationHelper
from ..conf import COMPONENT_TAG


class _Query:
    def __init__(self, entityId, comps):
        # type: (str, list) -> None
        self.entityId = entityId
        self.comps = comps

    def iter(self):
        return getComponent(self.entityId, self.comps) or []
    
    def __enter__(self):
        result = getComponent(self.entityId, self.comps)
        if result is None:
            raise Exception()
        return result
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return True


def query(entityId, comps):
    # type: (int, list) -> _Query
    return _Query(entityId, comps) # type: ignore


class EntityId:
    pass

class ExtraArguments:
    pass

class ExtraArgDict:
    pass

FakeComponents = [EntityId, ExtraArguments, ExtraArgDict]

def _getQueryArgs(entityId, compClsSrc, required, excluded, args, kwargs):
    # type: (str, list, list, list, list, dict) -> list | None
    compCls = compClsSrc[:]
    entityIdIndex = -1
    extraArgsIndex = -1
    extraArgDict = -1
    if EntityId in compCls:
        entityIdIndex = compCls.index(EntityId)
        compCls[entityIdIndex] = None
    if ExtraArguments in compCls:
        extraArgsIndex = compCls.index(ExtraArguments)
        compCls[extraArgsIndex] = None
    if ExtraArgDict in compCls:
        extraArgDict = compCls.index(ExtraArgDict)
        compCls[extraArgDict] = None
    result = getComponentWithQuery(entityId, compCls, required, excluded)
    if not result:
        return None
    if entityIdIndex >= 0:
        result[entityIdIndex] = entityId
    if extraArgsIndex >= 0:
        result[extraArgsIndex] = args
    if extraArgDict >= 0:
        result[extraArgDict] = kwargs
    return result


def _isCompAllSingleton(compCls):
    # type: (list) -> bool
    singletonCount = 0
    compSize = len(compCls)
    for comp in compCls:
        if type(comp) == str:
            return False
        if comp == EntityId:
            return False
        if AnnotationHelper.getAnnotation(comp, COMPONENT_TAG).get('singleton'): # type: ignore
            singletonCount += 1
    return singletonCount == compSize


def Query(*compCls, **options):
    """
    Args:
        compCls (list[type[BaseCompServer|BaseCompClient]]): 组件类或组件类名
        required (list[type[BaseCompServer|BaseCompClient]]): 必须包含的组件, 不会包含在查询结果中
        excluded (list[type[BaseCompServer|BaseCompClient]]): 必须排除的组件, 不会包含在查询结果中

    使用 Query 查询时，`self` 为 ~entityId字符串~ 类实例,
    请一定要搭配 Sched.Tick() , Sched.Render() 等调度装饰器使用，否则不会执行。
    （不再使用 entityId 的理由是，这样做更符合直觉，且组件可以自行缓存 entityId）

    可以使用伪组件 ``EntityId``、``ExtraArguments``、``ExtraArgDict``
    来分别获取 *组件绑定的实体ID* ，*传入方法的参数列表* ，
    以及 *传入方法的参数字典* ，其中伪组件的位置没有要求。

    被这个装饰器装饰后，函数不会正常接收参数，而是在查询过程中动态注入参数，
    请不要尝试在子系统类中使用 self.xxx 调用被这个装饰器装饰的方法，
    除非你非常了解动态参数注入是如何实现的。

    **注意**：无法支持此版本之前的代码，请重构代码以使用此版本，重构方法为导入伪组件 `EntityId`,
    在参数列表的 self 后面加入 `id, ` 将之前代码中使用的self替换成id
    """
    required = options.get('required', [])
    excluded = options.get('excluded', [])
    def decorator(fn):
        isAllSingleton = _isCompAllSingleton(compCls) # type: ignore
        def wrapper(inst, *args, **kwargs):
            _compList = list(compCls)
            if isAllSingleton:
                args = _getQueryArgs(None, _compList, required, excluded, args, kwargs) # type: ignore
                if args:
                    fn(inst, *args)
            else:
                for entityId in getEntities():
                    if not entityId:
                        continue
                    comps = _getQueryArgs(entityId, _compList, required, excluded, args, kwargs) # type: ignore
                    if comps:
                        fn(inst, *comps)
        return wrapper
    return decorator