from __future__ import annotations

from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke

from ...GlobalCache import GLOBAL_CACHE
from ...Py4GWcorelib import ActionQueueManager
from ...enums_src.UI_enums import ControlAction
from ..BehaviourTrees import BT
from .helpers import _run_bt_tree


class Keybinds:
    @staticmethod
    def PressKeybind(keybind_index:int, duration_ms:int=125, log=False):
        tree = BT.Keybinds.PressKeybind(keybind_index, duration_ms, log)
        yield from _run_bt_tree(tree)

    @staticmethod
    def TakeScreenshot(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_Screenshot.value, 75, log=log)
    
    @staticmethod
    def CallTarget(log=False):
        ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
        from ..Yield import Yield
        yield from Yield.wait(100)
       
    @staticmethod
    def CloseAllPanels(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_CloseAllPanels.value, 75, log=log)
        
    @staticmethod
    def ToggleInventory(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ToggleInventoryWindow.value, 75, log=log)
            
    @staticmethod
    def OpenScoreChart(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenScoreChart.value, 75, log=log)
        
    @staticmethod
    def OpenTemplateManager(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenTemplateManager.value, 75, log=log)
        
    @staticmethod
    def OpenSaveEquipmentTemplate(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenSaveEquipmentTemplate.value, 75, log=log)
        
    @staticmethod
    def OpenSaveSkillTemplate(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenSaveSkillTemplate.value, 75, log=log)
        
    @staticmethod
    def OpenParty(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenParty.value, 75, log=log)
        
    @staticmethod
    def OpenGuild(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenGuild.value, 75, log=log)
        
    @staticmethod
    def OpenFriends(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenFriends.value, 75, log=log)
        
    @staticmethod
    def ToggleAllBags(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ToggleAllBags.value, 75, log=log)
        
    @staticmethod
    def OpenMissionMap(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenMissionMap.value, 75, log=log)
        
    @staticmethod
    def OpenBag2(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenBag2.value, 75, log=log)
        
    @staticmethod
    def OpenBag1(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenBag1.value, 75, log=log)
        
    @staticmethod
    def OpenBelt(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenBelt.value, 75, log=log)
        
    @staticmethod
    def OpenBackpack(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenBackpack.value, 75, log=log)
        
    @staticmethod
    def OpenSkillsAndAttributes(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenSkillsAndAttributes.value, 75, log=log)
        
    @staticmethod
    def OpenQuestLog(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenQuestLog.value, 75, log=log)
        
    @staticmethod
    def OpenWorldMap(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenWorldMap.value, 75, log=log)
        
    @staticmethod
    def OpenHeroPanel(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenHero.value, 75, log=log)    

    @staticmethod
    def CycleEquipment(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_CycleEquipment, 75, log=log)
        
    @staticmethod
    def ActivateWeaponSet(index:int, log=False):
        if index < 1 or index > 4:
            return
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ActivateWeaponSet1.value + (index - 1), 75, log=log)

    @staticmethod
    def DropBundle(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_DropItem, 75, log=log)
        
    @staticmethod
    def OpenChat(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenChat, 75, log=log)
        
    @staticmethod
    def ReplyToChat(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ChatReply, 75, log=log)
        
    @staticmethod
    def OpenAlliance(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenAlliance, 75, log=log)
        
    @staticmethod   
    def MoveBackwards(duration_ms:int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_MoveBackward.value, duration_ms, log=log)

    @staticmethod
    def MoveForwards(duration_ms:int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_MoveForward.value, duration_ms, log=log)

    @staticmethod
    def StrafeLeft(duration_ms:int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_StrafeLeft.value, duration_ms, log=log)

    @staticmethod
    def StrafeRight(duration_ms:int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_StrafeRight.value, duration_ms, log=log)

    @staticmethod
    def TurnLeft(duration_ms:int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TurnLeft.value, duration_ms, log=log)

    @staticmethod
    def TurnRight(duration_ms:int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TurnRight.value, duration_ms, log=log)
        
    @staticmethod
    def ReverseCamera(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ReverseCamera.value, 75, log=log)
        
    @staticmethod
    def CancelAction(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_CancelAction.value, 75, log=log)
        
    @staticmethod
    def Interact(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_Interact.value, 75, log=log)
        
    @staticmethod
    def ReverseDirection(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ReverseDirection.value, 75, log=log)
        
    @staticmethod
    def AutoRun(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_Autorun.value, 75, log=log)
        
    @staticmethod
    def Follow(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_Follow.value, 75, log=log)
        
    @staticmethod
    def TargetPartyMember(index:int, log=False):
        if index < 1 or index > 12:
            return
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetPartyMember1.value + (index - 1), 75, log=log)
    
    @staticmethod
    def TargetNearestItem(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetNearestItem.value, 75, log=log)
        
    @staticmethod
    def TargetNextItem(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetNextItem.value, 75, log=log)
        
    @staticmethod
    def TargetPreviousItem(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetPreviousItem.value, 75, log=log)
        
    @staticmethod
    def TargetPartyMemberNext(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetPartyMemberNext.value, 75, log=log)
        
    @staticmethod
    def TargetPartyMemberPrevious(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetPartyMemberPrevious.value, 75, log=log)
        
    @staticmethod
    def TargetAllyNearest(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetAllyNearest.value, 75, log=log)
        
    @staticmethod
    def ClearTarget(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ClearTarget.value, 75, log=log)
        
    @staticmethod
    def TargetSelf(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetSelf.value, 75, log=log)
        
    @staticmethod
    def TargetPriorityTarget(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetPriorityTarget.value, 75, log=log)
        
    @staticmethod
    def TargetNearestEnemy(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetNearestEnemy.value, 75, log=log)
        
    @staticmethod
    def TargetNextEnemy(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetNextEnemy.value, 75, log=log)
        
    @staticmethod
    def TargetPreviousEnemy(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TargetPreviousEnemy.value, 75, log=log)
        
    @staticmethod
    def ShowOthers(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ShowOthers.value, 75, log=log)
        
    @staticmethod
    def ShowTargets(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ShowTargets.value, 75, log=log)
        
    @staticmethod
    def CameraZoomIn(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_CameraZoomIn.value, 75, log=log)
        
    @staticmethod
    def CameraZoomOut(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_CameraZoomOut.value, 75, log=log)
        
    @staticmethod
    def ClearPartyCommands(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_ClearPartyCommands.value, 75, log=log)
        
    @staticmethod
    def CommandParty(log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_CommandParty.value, 75, log=log)
        
    @staticmethod
    def CommandHero(hero_index:int, log=False):
        if hero_index < 1 or hero_index > 7:
            return
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_CommandHero1.value + (hero_index - 1), 75, log=log)
    
    @staticmethod
    def OpenHeroPetCommander(hero_index:int, log=False):
        if hero_index < 1 or hero_index > 7:
            return
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenHero1PetCommander.value + (hero_index - 1), 75, log=log)

    @staticmethod
    def OpenHeroCommander(hero_index:int, log=False):
        if hero_index < 1 or hero_index > 7:
            return
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_OpenHeroCommander1.value + (hero_index - 1), 75, log=log)
        
    @staticmethod
    def HeroSkill(hero_index:int, skill_slot:int, log=False):
        party_size = GLOBAL_CACHE.Party.GetPartySize()
        if hero_index < 1 or hero_index > party_size:
            return
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_Hero1Skill1.value + (hero_index - 1) * 8 + (skill_slot - 1), 75, log=log)
        
    @staticmethod
    def UseSkill(slot:int, log=False):
        if slot < 1 or slot > 8:
            return
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_UseSkill1.value + (slot - 1), 75, log=log)
