class _ModuleLocator: pass
__modname__ = _ModuleLocator.__module__[:_ModuleLocator.__module__.find('.')]
"""
这里是引擎配置, 不建议直接修改.
MOD_* 和 PLUGINS 遵循覆盖原则, 用户可以在脚本根目录下创建 conf.py 覆盖默认配置.
如果你不知道有哪些配置可以修改, 请将引擎配置中 “推荐修改的配置” 和 “插件列表” 复制到你的 conf.py 中
"""



# 推荐修改的配置
MOD_NAME = __modname__
MOD_VERSION = '1.0.0'
MOD_ENGINE_NAME = MOD_NAME
MOD_SYSTEM_NAME = 'ModSubsystem'
MOD_SERVER_MODULES = []
MOD_CLIENT_MODULES = []

# 插件列表
"""
$vendor为系统插件, $user为用户插件
系统插件在{modname}/architect/plugins目录下
用户插件在{modname}/plugins目录下
"""
PLUGINS = [
    '$vendor.event',        # 事件系统
]







# 改了也没什么意义的配置
COMPONENT_NAMESPACE = 'xxx_roninComponent_xxx'  # 组件命名空间
DB_NAME = 'clientKVDb'                          # 数据库命名空间
DB_GLOBAL_NAME = 'clientKVGlobal'               # 全局数据库命名空间
UI_NAMESPACE = 'xxx_roninUi_xxx'                # UI命名空间
ANNOTATION = '_annotation'                      # 装饰器标记
COMPONENT_TAG = '_component'                    # 组件标记
PERSIST_INFO = '_persist_keys'                  # 持久化键标记
EVENT_LISTENER = '_event_listener'              # 事件监听器标记
CUSTOM_EVENT = '_custom_event'                  # 自定义事件标记
SYSTEM_SCHED_ANNO = '_system_sched'             # 系统调度器标记
UI_DEF = '_ui_def'                              # UI定义标记
UI_SINK = '_ui_binder'                          # UI绑定标记
UI_SCREEN = '_ui_screen'                        # UI屏幕标记
UI_HUD = '_ui_hud'                              # UI HUD标记
UI_GESTURE = '_ui_gesture'                      # UI手势类型标记

# 调度器调度名称（不推荐修改）
TIMER_TASK = 'TimerTask'                        # 定时任务
SCHED_BEFORE_UPDATE = 'BeforeUpdate'            # 更新前调度
SCHED_AFTER_UPDATE = 'AfterUpdate'              # 更新后调度
SCHED_UPDATE = 'Update'                         # 更新调度
SCHED_EVENT = 'Event'                           # 事件时调度
SCHED_AFTER_EVENT = 'AfterEvent'                # 事件后调度

class SchedUpdateFlags:
    BeforeUpdate = SCHED_BEFORE_UPDATE
    AfterUpdate = SCHED_AFTER_UPDATE
    Update = SCHED_UPDATE

class SchedEventFlags:
    Event = SCHED_EVENT
    AfterEvent = SCHED_AFTER_EVENT

ASPECT = '_Aspect'

class Aspects:
    Before = '_asp_before'
    After = '_asp_after'
    AfterReturning = '_asp_afterReturning'
    AfterThrowing = '_asp_afterThrowing'
    Replace = '_asp_replace'


try:
    from .. import conf as userConf
except:
    userConf = object()
vendorConf = globals()

def conf(key):
    try:
        return userConf.__dict__[key]
    except:
        return vendorConf[key]