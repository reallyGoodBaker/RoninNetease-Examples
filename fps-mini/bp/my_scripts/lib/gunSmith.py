import colorsys
from ..engine.architect.compact import (
    UiSubsystem, Screen, UiDef,
    QueryVariable, localPlayerId,
    addFrameTimer,
    randomId,
    Asset, LevelClient,
)

from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent

# TODO: Remove
from mod.client.ui.controls.baseUIControl import BaseUIControl

TEXTURE_NONE = 'textures/attachments/none'

gunsmith = QueryVariable('gunsmith')

class AttachmentCategory(object):
    def __init__(self, control):
        # type: (BaseUIControl) -> None
        container = control.GetChildByName('container')
        self.container = container
        self.label = container.GetChildByName('label').asLabel()
        self.image = container.GetChildByName('image').asImage()

    def setVisible(self, visible):
        self.container.SetVisible(visible)

    def setTexture(self, path):
        self.image.SetSprite(path)

    def setText(self, text):
        self.label.SetText(text)


@Screen
@UiDef('gun_smith.main')
class GunSmithUi(UiSubsystem):

    attachmentSelections = {} # type: dict[str, BaseUIControl]
    attachmentCache = {}
    currentSlot = None
    onselect = None
    pivots = set() # type: set[BaseUIControl]
    displayAttachmentControls = set() # type: set[BaseUIControl]

    def onCreate(self):
        self.attachmentSelections = {}
        self.attachmentCache = {}
        self.displayAttachmentControls = set()
        self.pivots = set()
        self.category = AttachmentCategory(self.find('/categories/scroll_mouse/scroll_view/stack_panel/background_and_viewport/scrolling_view_port/scrolling_content/bayonet'))
        self.attachments = self.find('/attachments/scroll_mouse/scroll_view/stack_panel/background_and_viewport/scrolling_view_port/scrolling_content').asStackPanel()
        self.template = self.find('/lib/attachment')
        self.pivotTemplate = self.find('/lib/pivot')
        self.palette = self.find('/palette')
        self.palettePicker = self.find('/palette/picker')
        self.paletteHue = self.find('/palette/hue')
        self.currentHue = 0.0
        self.currentSaturation = 1.0
        self.currentValue = 1.0
        # setAppearanceData() can be called before onCreate() runs (because
        # PushScreen's create can be deferred); do not wipe the value.
        if not isinstance(getattr(self, 'appearanceData', None), dict):
            self.appearanceData = {}
        self.game = LevelClient.getInstance().game
        gunsmith.setValue(localPlayerId(), 1)
        self._bindPaletteEvents()
        self.displaySlot(self.slots[0], self.attachmentsData)


    def onDestroy(self):
        self._saveAppearance()
        addFrameTimer(0.15, lambda: gunsmith.setValue(localPlayerId(), 0), False)
        if hasattr(self, '_ondestroy'):
            self._ondestroy()


    def displayAttachments(self, slots, attachments):
        self.slots = slots
        self.attachmentsData = attachments

    
    def showPivots(self, slot):
        exclude = slot['slotId']
        pivotsToShow = filter(lambda slot: slot['slotId'] != exclude, self.slots)
        parentPath = '/pivots'
        for pivotControl in self.pivots:
            self.RemoveChildControl(pivotControl)
        self.pivots.clear()

        for pivotSlot in pivotsToShow:
            pivotId = randomId()
            self.Clone(
                self.pivotTemplate.GetPath(),
                parentPath,
                pivotId
            )
            pivotControl = self.find(parentPath + '/' + pivotId)
            self.showOnePivot(pivotSlot, pivotControl)


    @staticmethod
    def _iterAttachmentAssets():
        # type: () -> list
        result = []
        try:
            names = dir(Asset.reach('attachments', True))
        except Exception:
            return result
        for name in names:
            if name.startswith('__'):
                continue
            try:
                asset = Asset('attachments.' + name).load()
            except Exception:
                asset = None
            if isinstance(asset, dict):
                result.append(asset)
            # Subpackage: attachments.appearance.*
            try:
                subNames = dir(Asset.reach('attachments.' + name, True))
            except Exception:
                subNames = []
            for sub in subNames:
                if sub.startswith('__'):
                    continue
                try:
                    subAsset = Asset('attachments.' + name + '.' + sub).load()
                except Exception:
                    continue
                if isinstance(subAsset, dict):
                    result.append(subAsset)
        return result

    def findAttachmentById(self, attachmentId):
        # type: (str) -> dict | None
        if attachmentId in self.attachmentCache:
            return self.attachmentCache[attachmentId]
        for asset in self._iterAttachmentAssets():
            if asset and asset.get('attachmentId') == attachmentId:
                self.attachmentCache[attachmentId] = asset
                return asset
        return None

    def showOnePivot(self, pivotSlot, pivotControl):
        # type: (dict, BaseUIControl) -> None
        self.pivots.add(pivotControl)
        label = pivotControl.GetChildByName('label').asLabel()
        image = pivotControl.GetChildByName('image').asImage()
        control = pivotControl.GetChildByName('control').asButton()
        label.SetText(self.game.GetChinese(pivotSlot['displayName']))
        attachId = self.attachmentsData.get(pivotSlot['slotId'])
        if not attachId:
            if pivotSlot.get('attachmentAsset'):
                try:
                    defaultAsset = Asset(pivotSlot['attachmentAsset']).load()
                except Exception:
                    defaultAsset = None
                texture = defaultAsset.get('texture') if defaultAsset else TEXTURE_NONE
            else:
                texture = TEXTURE_NONE
            image.SetSprite(texture)
        else:
            attachAsset = self.findAttachmentById(attachId)
            texture = attachAsset.get('texture') if attachAsset else TEXTURE_NONE
            image.SetSprite(texture)
        self.addEventListener(
            control.GetPath(),
            'click',
            lambda control, ev: self.displaySlot(pivotSlot, self.attachmentsData)
        )


    def _bindPaletteEvents(self):
        # type: () -> None
        self.addEventListener('/palette/picker', 'down', self._onPalettePicker)
        self.addEventListener('/palette/picker', 'move', self._onPalettePicker)
        self.addEventListener('/palette/hue', 'down', self._onPaletteHue)
        self.addEventListener('/palette/hue', 'move', self._onPaletteHue)

    @staticmethod
    def _hsvToRgb255(hue, saturation, value):
        # type: (float, float, float) -> tuple
        r, g, b = colorsys.hsv_to_rgb(
            (hue % 1.0), max(0.0, min(1.0, saturation)),
            max(0.0, min(1.0, value))
        )
        return (
            int(round(r * 255)),
            int(round(g * 255)),
            int(round(b * 255)),
        )

    def _applyPaletteColor(self):
        # type: () -> None
        rgb = self._hsvToRgb255(
            self.currentHue,
            self.currentSaturation,
            self.currentValue
        )
        from .tint import applyAppearance
        applyAppearance({
            'rgb': list(rgb),
            'alpha': 0.6,
        })

    def _clearPaletteColor(self):
        # type: () -> None
        from .tint import clearAppearance
        clearAppearance()

    def _updatePickerPureColor(self):
        # type: () -> None
        pure = self._hsvToRgb255(self.currentHue, 1.0, 1.0)
        color = (
            pure[0] / 255.0,
            pure[1] / 255.0,
            pure[2] / 255.0,
        )
        try:
            control = self.find('/palette/picker/color')
            if control:
                image = control.asImage()
                if image:
                    image.SetSpriteColor(color)
        except Exception as errorObject:
            print '[GunSmith] update picker pure color exception:', repr(errorObject)

    def _paletteLocalFraction(self, control, ev, controlPath):
        # type: (object, object, str) -> tuple
        try:
            origin = self.GetGlobalPosition(controlPath)
            size = control.GetSize()
            rawX = float(ev.x)
            rawY = float(ev.y)
            localX = rawX - float(origin[0])
            localY = rawY - float(origin[1])
            return (
                max(0.0, min(1.0, localX / float(size[0]))),
                max(0.0, min(1.0, localY / float(size[1]))),
            )
        except Exception as errorObject:
            return (0.0, 0.0)

    def _onPalettePicker(self, ev):
        # type: (object) -> None
        x, y = self._paletteLocalFraction(self.palettePicker, ev, '/palette/picker')
        # Picker: bottom-left is origin.
        # x: 0 = white, 1 = pure hue color.
        # y: bottom = dark, top = bright.
        self.currentSaturation = x
        self.currentValue = 1.0 - y
        self._applyPaletteColor()
        self._storeCurrentAppearance()

    def _onPaletteHue(self, ev):
        # type: (object) -> None
        x, y = self._paletteLocalFraction(self.paletteHue, ev, '/palette/hue')
        # Hue strip: top-left origin, y down from red to red (0..1).
        self.currentHue = y
        self._applyPaletteColor()
        self._updatePickerPureColor()
        self._storeCurrentAppearance()

    def _isAppearanceSlot(self, slot):
        # type: (dict) -> bool
        return slot.get('type') in ('appearance', 'tint')

    def _hasAppearanceSelected(self):
        # type: () -> bool
        if isinstance(self.appearanceData, dict) and self.appearanceData:
            return True
        for slot in self.slots:
            if self._isAppearanceSlot(slot) and self.attachmentsData.get(slot['slotId']):
                return True
        return False

    def setAppearanceData(self, appearance):
        # type: (dict) -> None
        self.appearanceData = appearance if isinstance(appearance, dict) else {}

    def _loadAppearanceToPalette(self):
        # type: () -> None
        data = self.appearanceData or {}
        if 'hue' in data:
            self.currentHue = float(data['hue'])
        if 'saturation' in data:
            self.currentSaturation = float(data['saturation'])
        if 'value' in data:
            self.currentValue = float(data['value'])

    def _storeCurrentAppearance(self):
        # type: () -> None
        if not isinstance(self.appearanceData, dict):
            self.appearanceData = {}
        self.appearanceData['hue'] = self.currentHue
        self.appearanceData['saturation'] = self.currentSaturation
        self.appearanceData['value'] = self.currentValue
        rgb = self._hsvToRgb255(
            self.currentHue,
            self.currentSaturation,
            self.currentValue
        )
        self.appearanceData['rgb'] = list(rgb)
        self._saveAppearance()

    def _saveAppearance(self):
        # type: () -> None
        if not isinstance(self.appearanceData, dict) or not self.appearanceData:
            return
        try:
            from .gunClientSync import GunClientSyncSystem
            GunClientSyncSystem.getInstance().requestSetAppearance(
                dict(self.appearanceData)
            )
        except Exception as errorObject:
            print '[GunSmith] save appearance exception:', repr(errorObject)

    def _hasCustomAppearance(self):
        # type: () -> bool
        """Whether the player has already picked/stored a custom tint color.

        Equipping an appearance/skin alone does not count: with no custom
        appearance the overlay must stay at alpha 0 until the palette is used.
        """
        return isinstance(self.appearanceData, dict) and bool(self.appearanceData)

    def _showPaletteForSlot(self, slot):
        # type: (dict) -> None
        if not self.palette:
            return
        isAppearance = self._isAppearanceSlot(slot)
        self.palette.SetVisible(isAppearance)
        if isAppearance:
            self._loadAppearanceToPalette()
            if self._hasCustomAppearance():
                self._applyPaletteColor()
            else:
                self._clearPaletteColor()
            self._updatePickerPureColor()
        elif self._hasAppearanceSelected() and self._hasCustomAppearance():
            # The appearance is still equipped; keep the player-chosen tint
            # visible while browsing other slots. Never invent a color from
            # palette defaults before the player has used the palette.
            self._loadAppearanceToPalette()
            self._applyPaletteColor()
            self._saveAppearance()
        else:
            self._clearPaletteColor()

    def displaySlot(self, slot, attachments):
        self.currentSlot = slot
        if hasattr(self, 'onslotselect') and self.onslotselect:
            self.onslotselect(slot)
        self._showPaletteForSlot(slot)
        slotId = slot['slotId']
        displayName = slot['displayName']
        category = slot['category']
        allAttachments = self.findAllUseableAttachments(category)
        self.category.setText(self.game.GetChinese(displayName))
        self.clearAttachmentDisplay()
        self.showPivots(slot)

        defaultAttachment = None
        if slot.get('attachmentAsset'):
            try:
                defaultAttachment = Asset(slot['attachmentAsset']).load()
            except Exception:
                defaultAttachment = None

        if defaultAttachment:
            self.addAttachmentSelection(defaultAttachment)
        else:
            self.addAttachmentSelection(None)

        for att in allAttachments:
            if defaultAttachment and att['attachmentId'] == defaultAttachment['attachmentId']:
                continue
            self.addAttachmentSelection(att)

        attached = attachments.get(slotId)
        if not attached and defaultAttachment:
            attached = defaultAttachment['attachmentId']
        self.selectAttachment(attached)


    def clearAttachmentDisplay(self):
        for control in self.displayAttachmentControls:
            self.RemoveChildControl(control)
        self.displayAttachmentControls.clear()
        self.attachmentSelections.clear()


    def _currentAttachmentIdForSlot(self, slot):
        # type: (dict) -> str | None
        slotId = slot['slotId']
        if slotId in self.attachmentsData:
            return self.attachmentsData.get(slotId)
        if slot.get('attachmentAsset'):
            try:
                asset = Asset(slot['attachmentAsset']).load()
            except Exception:
                asset = None
            if asset:
                return asset.get('attachmentId')
        return None

    def selectAttachment(self, attachmentId):
        view = self.attachmentSelections.get(attachmentId)
        if not view:
            return
        for element in self.attachmentSelections.values():
            self._visualSelected(element, False)
        self._visualSelected(view, True)
        if not self.currentSlot:
            return
        slotId = self.currentSlot['slotId']
        currentId = self._currentAttachmentIdForSlot(self.currentSlot)

        # If this attachment is already explicitly installed, only highlight it.
        # If it is only the slot default and has not been applied yet, fall
        # through and apply it so the default behavior (e.g. default zoom)
        # actually takes effect.
        if attachmentId == currentId:
            if slotId in self.attachmentsData:
                if attachmentId:
                    attachAsset = self.attachmentCache.get(attachmentId)                         or self.findAttachmentById(attachmentId)
                    texture = attachAsset.get('texture') if attachAsset else TEXTURE_NONE
                    self.category.setTexture(texture)
                else:
                    self.category.setTexture(TEXTURE_NONE)
                return
            if attachmentId is None:
                self.category.setTexture(TEXTURE_NONE)
                return

        if not attachmentId:
            # Directly reflect the removal in the UI's own attachments data.
            self.attachmentsData.pop(slotId, None)
            self.onselect(self.currentSlot, None)
            self.category.setTexture(TEXTURE_NONE)
            return
        attachAsset = self.attachmentCache.get(attachmentId)
        if not attachAsset:
            return
        # Directly reflect the selected attachment in the UI's own data.
        self.attachmentsData[slotId] = attachmentId
        self.onselect(self.currentSlot, attachAsset)
        self.category.setTexture(attachAsset['texture'])


    def _visualSelected(self, control, selected):
        # type: (BaseUIControl, bool) -> None
        img = control.GetChildByName('image').asImage()
        txt = control.GetChildByName('label').asLabel()
        line = control.GetChildByName('bottom')
        if selected:
            img.SetSpriteColor((0, 0, 0))
            txt.SetTextColor((0, 0, 0))
            line.SetSize((100, 36))
            line.SetPosition((0, 0))
            return
        img.SetSpriteColor((1, 1, 1))
        txt.SetTextColor((1, 1, 1))
        line.SetSize((100, 1))
        line.SetPosition((0, 35))


    def findAllUseableAttachments(self, category):
        results = []
        for asset in self._iterAttachmentAssets():
            if not isinstance(asset, dict) or 'category' not in asset:
                continue
            if asset['category'] != category:
                continue
            results.append(asset)
        return results


    def addAttachmentSelection(self, attachAsset):
        if attachAsset:
            self.attachmentCache[attachAsset['attachmentId']] = attachAsset

        controlId = randomId()
        parentPath = self.attachments.GetPath()
        self.Clone(
            self.template.GetPath(),
            parentPath,
            controlId
        )
        newView = self.find(parentPath + '/' + controlId)
        img = newView.GetChildByName('image').asImage()
        label = newView.GetChildByName('label').asLabel()
        eventTarget = newView.GetChildByName('event').asButton()
        attachId = None if attachAsset == None else attachAsset['attachmentId']
        self.attachmentSelections[attachId] = newView
        self.addEventListener(
            eventTarget.GetPath(),
            'click',
            lambda control, ev: self.selectAttachment(attachId)
        )
        self.displayAttachmentControls.add(newView)
        if not attachAsset:
            img.SetSprite(TEXTURE_NONE)
            label.SetText('无')
            return
        img.SetSprite(attachAsset['texture'])
        label.SetText(attachAsset['displayName'])