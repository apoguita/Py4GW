# from Py4GWCoreLib.Builds.DervBoneFarmer import DervBuildFarmStatus
# from Py4GWCoreLib.Builds.DervBoneFarmer import DervBoneFarmer
from Py4GWCoreLib import *


from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Key
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Player
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Weapon
from Py4GWCoreLib.Builds.AutoCombat import AutoCombat


# =================== BUILD ========================
class DervBuildFarmStatus:
    Setup = 'setup'
    Prepare = 'prepare'
    Kill = 'kill'
    Loot = 'loot'
    Wait = 'wait'


class DervBoneFarmer(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Derv Feather Farmer",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code='OgCjkqqLrSYiihdftXjhOXhX0kA',
            skills=[
                GLOBAL_CACHE.Skill.GetID("Signet_of_Mystic_Speed"),
                GLOBAL_CACHE.Skill.GetID("Pious_Fury"),
                GLOBAL_CACHE.Skill.GetID("Grenths_Aura"),
                GLOBAL_CACHE.Skill.GetID("Vow_of_Silence"),
                GLOBAL_CACHE.Skill.GetID("Crippling_Victory"),
                GLOBAL_CACHE.Skill.GetID("Reap_Impurities"),
                GLOBAL_CACHE.Skill.GetID("Vow_of_Piety"),
                GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable"),
            ],
        )

        self.auto_combat_handler: BuildMgr = AutoCombat()
        # assign extra skill attributes from the already populated self.skills
        self.signet_of_mystic_speed = self.skills[0]
        self.pious_fury = self.skills[1]
        self.grenths_aura = self.skills[2]
        self.vow_of_silence = self.skills[3]
        self.criplling_victory = self.skills[4]
        self.reap_impurities = self.skills[5]
        self.vow_of_piety = self.skills[6]
        self.i_am_unstoppable = self.skills[7]

        # Build usage status
        self.status = DervBuildFarmStatus.Setup
        self.spiked = False
        self.spiking = False

    def swap_to_scythe(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] != Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F1.value)
            yield

    def swap_to_shield_set(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] == Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F2.value)
            yield from Routines.Yield.wait(750)

    def has_enough_adrenaline(self, skill_slot):
        skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(skill_slot)

        return GLOBAL_CACHE.SkillBar.GetSkillData(skill_slot).adrenaline_a >= Skill.Data.GetAdrenaline(skill_id)

    def ProcessSkillCasting(self):
        if not (
            Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Skills.CanCast()
        ):
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000)
            return

        if self.status == DervBuildFarmStatus.Loot or self.status == DervBuildFarmStatus.Setup:
            yield from self.swap_to_shield_set()
            yield from Routines.Yield.wait(100)
            return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_signet_of_mystic_speed = Routines.Checks.Effects.HasBuff(player_agent_id, self.signet_of_mystic_speed)
        has_grenths_aura = Routines.Checks.Effects.HasBuff(player_agent_id, self.grenths_aura)
        has_vow_of_silence = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_silence)
        has_vow_of_piety = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_piety)

        if self.status == DervBuildFarmStatus.Prepare:
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_piety)) and not has_vow_of_piety:
                yield from Routines.Yield.Skills.CastSkillID(self.vow_of_piety, aftercast_delay=750)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.grenths_aura)) and not has_grenths_aura:
                yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=100)
                return

            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_silence))
                and has_grenths_aura
                and has_vow_of_piety
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.vow_of_silence, aftercast_delay=100)
                return

        if self.status == DervBuildFarmStatus.Kill:
            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.signet_of_mystic_speed))
                and has_vow_of_silence
                and not has_signet_of_mystic_speed
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.signet_of_mystic_speed, aftercast_delay=750)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.i_am_unstoppable)):
                yield from Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, aftercast_delay=100)
                return

            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_silence))
                and has_grenths_aura
                and has_signet_of_mystic_speed
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.pious_fury, aftercast_delay=100)
                yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=100)
                yield from Routines.Yield.Skills.CastSkillID(self.vow_of_silence, aftercast_delay=100)
                return

            nearest_enemy = Routines.Agents.GetNearestEnemy(Range.Nearby.value)
            vos_buff_time_remaining = (
                GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), self.vow_of_silence)
                if has_vow_of_silence
                else 0
            )
            if (
                has_grenths_aura
                and has_signet_of_mystic_speed
                and has_vow_of_silence
                and nearest_enemy
                and vos_buff_time_remaining > 1500
            ):
                yield from self.swap_to_scythe()
                GLOBAL_CACHE.Player.Interact(nearest_enemy, False)
                if (self.has_enough_adrenaline(4)):
                    yield from Routines.Yield.Skills.CastSkillID(self.criplling_victory, aftercast_delay=400)

                if (self.has_enough_adrenaline(5)):
                    yield from Routines.Yield.Skills.CastSkillID(self.reap_impurities, aftercast_delay=400)


# =================== BUILD END ========================


COF_FARMER = "COF Farmer"
DOOMLORE_SHRINE = "Doomlore Shrine"
COF_LEVEL_1 = "Cathedral of Flames (level 1)"
VIABLE_LOOT = {
    ModelID.Gold_Coins,
    ModelID.Bone,
    ModelID.Pile_Of_Glittering_Dust,
    ModelID.Bottle_Of_Rice_Wine,
    ModelID.Bottle_Of_Vabbian_Wine,
    ModelID.Dwarven_Ale,
    ModelID.Eggnog,
    ModelID.Hard_Apple_Cider,
    ModelID.Hunters_Ale,
    ModelID.Shamrock_Ale,
    ModelID.Witchs_Brew,
    ModelID.Zehtukas_Jug,
    ModelID.Aged_Dwarven_Ale,
    ModelID.Bottle_Of_Grog,
    ModelID.Krytan_Brandy,
    ModelID.Spiked_Eggnog,
    ModelID.Vial_Of_Dye,
    ModelID.Golden_Rin_Relic,
    ModelID.Diessa_Chalice,
}
# handler constants
HANDLE_STUCK = 'handle_stuck'
HANDLE_DANGER = 'handle_danger'

bot = Botting(
    COF_FARMER,
    custom_build=DervBoneFarmer(),
    config_movement_timeout=15000,
    config_movement_tolerance=150,
    upkeep_auto_inventory_management_active=False,
    upkeep_auto_loot_active=False,
)
stuck_timer = ThrottledTimer(3000)
movement_check_timer = ThrottledTimer(3000)
item_id_blacklist = []
is_farming = False
is_looting = False


# region Direct Bot Actions
def return_to_outpost(bot: Botting):
    if bot.config.build_handler.status == DervBuildFarmStatus.Setup:  # type: ignore
        return

    while True:
        is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
        is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        is_explorable = GLOBAL_CACHE.Map.IsExplorable()
        is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

        yield from Routines.Yield.Player.Resign()
        yield from Routines.Yield.wait(1000)

        if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
            yield from Routines.Yield.wait(2000)
            GLOBAL_CACHE.Party.ReturnToOutpost()
            yield from Routines.Yield.wait(4000)
            break  # exit after returning to outpost


def load_skill_bar(bot: Botting):
    yield from bot.config.build_handler.LoadSkillBar()


def farm(bot):
    global looted_areas
    global is_looting
    global is_farming

    if is_farming:
        return

    # Auto detect if enemy in the area
    enemy_array = get_enemy_array(custom_range=Range.Spellcast.value)
    if not len(enemy_array):
        ConsoleLog('Farm COF', 'No enemy detected!')
        return

    ConsoleLog(COF_FARMER, 'Farming...')
    is_farming = True
    bot.config.build_handler.status = DervBuildFarmStatus.Kill

    ConsoleLog(COF_FARMER, 'Killing all! None shall survive!')
    start_time = Utils.GetBaseTimestamp()
    timeout = 120000  # 2 minutes max

    player_id = GLOBAL_CACHE.Player.GetAgentID()

    while True:
        enemy_array = get_enemy_array(custom_range=Range.Spellcast.value)
        if len(enemy_array) == 0:
            if not is_looting:
                is_looting = True
                ConsoleLog(COF_FARMER, 'Setting to [Loot] status')
                bot.config.build_handler.status = DervBuildFarmStatus.Loot
                yield from Routines.Yield.wait(500)
                yield from loot_items()
                yield from Routines.Yield.wait(500)
                ConsoleLog(COF_FARMER, 'Setting back to [Setup] status')
                bot.config.build_handler.status = DervBuildFarmStatus.Setup
                # log from the last epicenter of the begining of the farm
                is_looting = False
            break  # all enemies dead

        # Timeout check
        current_time = Utils.GetBaseTimestamp()
        if timeout > 0 and current_time - start_time > timeout:
            ConsoleLog(COF_FARMER, 'Fight took too long, setting back to [Wait] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Wait
            yield from Routines.Yield.wait(1000)
            yield from Routines.Yield.Player.Resign()
            return

        # Death check
        if GLOBAL_CACHE.Agent.IsDead(player_id):
            # handle death here
            ConsoleLog(COF_FARMER, 'Died fighting, setting back to [Wait] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Wait
            yield from Routines.Yield.wait(1000)
            yield from Routines.Yield.Player.Resign()
            return

        yield from Routines.Yield.wait(100)

    ConsoleLog(COF_FARMER, 'Finished farming.')
    is_farming = False
    yield from Routines.Yield.wait(100)


def loot_items():
    global item_id_blacklist
    filtered_agent_ids = get_valid_loot_array()
    yield from Routines.Yield.wait(500)  # Wait for a second before starting to loot
    ConsoleLog(COF_FARMER, 'Looting items...')
    failed_items_id = yield from Routines.Yield.Items.LootItemsWithMaxAttempts(filtered_agent_ids, log=True)
    if failed_items_id:
        item_id_blacklist = item_id_blacklist + failed_items_id
    ConsoleLog(COF_FARMER, 'Looting items finished')
    yield


def identify_and_salvage_items():
    yield from Routines.Yield.wait(1500)
    yield from AutoInventoryHandler().IDAndSalvageItems()


def buy_id_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    if kits_in_inv < 3:
        yield from Routines.Yield.Merchant.BuyIDKits(3)


def buy_salvage_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    if kits_in_inv <= 3:
        yield from Routines.Yield.Merchant.BuySalvageKits(10)


# endregion


# region Helper Methods
def get_enemy_array(custom_range=Range.Area.value * 1.50):
    px, py = GLOBAL_CACHE.Player.GetXY()
    return Routines.Agents.GetFilteredEnemyArray(px, py, custom_range)


def get_valid_loot_array():
    loot_array = AgentArray.GetItemArray()
    loot_array = AgentArray.Filter.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value * 2.00)

    def is_valid_item(item_id):
        if not Agent.IsValid(item_id):
            return False
        player_agent_id = Player.GetAgentID()
        owner_id = Agent.GetItemAgentOwnerID(item_id)
        if (owner_id == player_agent_id) or (owner_id == 0):
            return True
        return False

    filtered_agent_ids = []
    for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
        item_data = Agent.GetItemAgent(agent_id)
        item_id = item_data.item_id
        model_id = Item.GetModelID(item_id)
        if model_id in VIABLE_LOOT and is_valid_item(agent_id):
            # Black and White Dyes
            if (
                model_id == ModelID.Vial_Of_Dye
                and (GLOBAL_CACHE.Item.GetDyeColor(item_id) == 10 or GLOBAL_CACHE.Item.GetDyeColor(item_id) == 12)
                or model_id != ModelID.Vial_Of_Dye
            ):
                filtered_agent_ids.append(agent_id)
    return filtered_agent_ids


def reset_looted_areas():
    global item_id_blacklist
    item_id_blacklist = []
    yield


def set_bot_to_setup(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Setup  # type: ignore
    yield


def set_bot_to_prepare(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Prepare  # type: ignore
    yield


def set_bot_to_loot(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Loot  # type: ignore
    yield


def _on_death(bot: Botting):
    ConsoleLog(COF_FARMER, "Waiting for a moment reset...")
    yield from Routines.Yield.wait(1000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Farm Loop_2")
    fsm.resume()
    yield


def on_death(bot: Botting):
    ConsoleLog(COF_FARMER, "Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))


def is_inventory_ready():
    salv_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    id_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    if salv_kits_in_inv < 3 or id_kits_in_inv == 0 or free_slots < 4:
        return False
    return True


# endregion


def main_farm(bot: Botting):
    bot.Events.OnDeathCallback(lambda: on_death(bot))
    # override condition for halting movement

    bot.States.AddHeader('Starting Loop')
    if GLOBAL_CACHE.Map.GetMapID() != GLOBAL_CACHE.Map.GetMapIDByName(DOOMLORE_SHRINE):
        bot.Map.Travel(target_map_name=DOOMLORE_SHRINE)
        bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)
    bot.States.AddCustomState(lambda: load_skill_bar(bot), "Loading Skillbar")

    # bot.Move.XY(17113, 12283, "Move close to Merch")
    # bot.Interact.WithNpcAtXY(17290.00, 12426.00, "Interact with Merchant")
    # bot.States.AddCustomState(buy_id_kits, 'Buying ID Kits')
    # bot.States.AddCustomState(buy_salvage_kits, 'Buying Salvage Kits')

    # bot.States.AddCustomState(identify_and_salvage_items, 'Salvaging Items')

    bot.States.AddCustomState(lambda: set_bot_to_setup(bot), "Setup Resign")
    bot.Move.XY(-18815.00, 17923.00, 'Move to NPC')
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x832101, "Temple of the damned Quest")  # Temple of the damned quest 0x832101
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x88, "Enter COF Level 1")  # Enter COF Level 1

    # Resign setup
    bot.Wait.ForMapLoad(target_map_name=COF_LEVEL_1)
    bot.Move.XY(-19665, -8045, "Setup resign spot")
    bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)

    # Actual Farming Loop
    bot.States.AddHeader('Farm Loop')
    bot.Properties.Enable("auto_combat")
    bot.States.AddCustomState(lambda: return_to_outpost(bot), "Return to Seitung Harbor")
    bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)
    bot.States.AddCustomState(lambda: set_bot_to_setup(bot), "Exit Outpost To Farm")
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x832101, "Temple of the damned Quest")  # Temple of the damned quest 0x832101
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x88, "Enter COF Level 1")  # Enter COF Level 1
    bot.Wait.ForMapLoad(target_map_name=COF_LEVEL_1)
    bot.Dialogs.AtXY(-18250.00, -8595.00, 0x84)

    bot.Move.XY(-16623, -8989, 'Move prep spot')
    bot.States.AddCustomState(lambda: set_bot_to_prepare(bot), "Prepare skills")
    bot.Wait.ForTime(3000)

    bot.Move.XY(-15525, -8923, 'Move spot 1')
    bot.Move.XY(-15737, -9093, 'Move spot 2')
    bot.States.AddCustomState(lambda: farm(bot), "Killing Everything Immediately")
    bot.States.AddCustomState(lambda: set_bot_to_loot(bot), "Prepare skills")

    bot.States.AddHeader('ID and Salvage at the End')
    bot.States.AddCustomState(identify_and_salvage_items, "ID and Salvage loot")
    bot.States.AddCustomState(reset_looted_areas, "Reset looted areas")

    bot.Party.Resign()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilCondition(lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()))


bot.SetMainRoutine(main_farm)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Feather_art.png")


if __name__ == "__main__":
    main()
