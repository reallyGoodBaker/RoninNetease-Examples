from ...engine.architect.plugins.animation.utils import BaseActionDispatcher, Dispatch
from ...engine.architect.compact import SubsystemManager

@Dispatch('animation.template.weapons.pistol.fp.reload')
@Dispatch('animation.template.weapons.pistol.fp.reload_slide_stop')
class ReloadAmmoDispatcher(BaseActionDispatcher):
    def notifyReloadStart(self, entity, animEx):
        SubsystemManager.getInstance().bus.execute('reloadAmmo')


@Dispatch('animation.template.weapons.pistol.fp.aim_last_shoot')
class LastAimShoot(BaseActionDispatcher):
    def notifyResetStart(self, entityId, animComp):
        SubsystemManager.getInstance().bus.execute('stopAiming')