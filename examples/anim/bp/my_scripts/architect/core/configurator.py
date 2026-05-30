from .basic import isServer, clientApi, serverApi


class _ModuleLocator(object):
    pass


__modname__ = _ModuleLocator.__module__[:_ModuleLocator.__module__.find('.')]
__framework__ = __modname__ + '.architect'
__dirname__ = __framework__ + '.core'


MOD_CONST_NAMES = [
    'MOD_NAME',
    'MOD_VERSION',
    'MOD_ENGINE_NAME',
    'MOD_SYSTEM_NAME',
]
MOD_ARRAYS = [
    'MOD_SERVER_MODULES',
    'MOD_CLIENT_MODULES',
    'PLUGINS',
]

VendorPlugins = __dirname__[:__dirname__.rfind('.')] + '.plugins'
UserPlugins = __modname__ + '.plugins'

def modConf():
    from .. import conf
    engineConf = conf.__dict__ # type: dict[str, str | list[str]]
    try:
        from ... import conf as mUserConf
        userConf = mUserConf.__dict__ # type: dict[str, str | list[str]]
    except ImportError:
        raise ImportError('请在 {} 文件夹中创建 conf.py 文件，并定义 MOD_ENGINE_NAME 和 MOD_SYSTEM_NAME, 如果你已经有了conf文件夹, 请在 __init__.py 中定义以上两个常量'.format(__modname__))

    def getter(key):
        # type: (str) -> str | list[str] | set[str] | None
        if key in MOD_CONST_NAMES:
            _user = userConf.get(key) # type: ignore
            if _user is None:
                return engineConf.get(key)
            return _user
        elif key in MOD_ARRAYS:
            _user = userConf.get(key) # type: ignore
            if _user is None:
                return engineConf.get(key)
            rawConf = engineConf.get(key) # type: ignore
            if isinstance(_user, list) and isinstance(rawConf, list):
                return set(rawConf + _user)
        else:
            return None
    return getter