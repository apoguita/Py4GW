from Bots.marks_coding_corner.ConsPrinter import EMBARK_BEACH
from Py4GWCoreLib import Botting, Py4GW, Quest, Player, GLOBAL_CACHE, Routines, PyAgent, Skill
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

bot = Botting("Skeleton Collector")

MAX_ITERATIONS = 5000
EMBARK_BEACH_ID = 857
TEMPLE_OF_THE_AGES_ID = 138
THE_UNDERWORLD_ID = 72
GRENTH_STATUE_POSITON = (-4081.25, 19761.32)
GRENTH_STATUE_SECOND_POSITON = (-4047.92, 19868.73)
VOICE_OF_GRENTH_POSITION = (-4124.00, 19829.00)

TRAP_PLACED = False

VOICE_OF_GRENTH_ID = 83
ENTER_UW_DIALOG = 0x85
ENTER_UW_ACCEPT = 0x86
UW_SCROLL_ID = 3746
RANGER_TEMPLATE = "OgcSc5PTTQ4O2k1kxkAAAAAA"
PARAGON_TEMPLATE = "OQei8xlMNBh7YTWTGTCAAAAAAA"
RITUALIST_TEMPLATE = "OAeR8ZaCC3xmsmMmEAAAAAA"
NECROMANCER_TEMPLATE = "OAdSY4PTTQ4O2k1kxkAAAAAA"
SKELETON_AGENT_MODEL_ID = 2342
SKELETON_TRAP_ID = 32558


def _force_reset():
    ConsoleLog("Skeleton Collector", "Unmanaged fail → force soft reset.", Py4GW.Console.MessageType.Warning)
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Killing_Skeleton_5")
    fsm.resume()
    yield


def _set_trap_used(val: bool):
    global TRAP_PLACED
    TRAP_PLACED = bool(val)


def initialize_bot():
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("auto_loot")
    bot.Properties.Disable("hero_ai")
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("auto_combat")
    bot.helpers.Events.set_on_unmanaged_fail(lambda: bot.States.AddManagedCoroutine("ForceReset", _force_reset()))


def get_other_accounts():
    me = GLOBAL_CACHE.Player.GetAccountEmail()
    out = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
        if not acc or not getattr(acc, "AccountEmail", None):
            continue
        if acc.AccountEmail == me:
            continue
        out.append(acc.Email if hasattr(acc, "Email") else acc.AccountEmail)
    return out


def broadcast_item(model_id: int, repeat=5, use_locally=True, delay=100):
    sender = GLOBAL_CACHE.Player.GetAccountEmail()
    for email in get_other_accounts():
        GLOBAL_CACHE.ShMem.SendMessage(sender_email=sender, receiver_email=email, command=SharedCommandType.UseItem,
                                       params=(float(model_id), float(repeat)), )

    if use_locally:
        for _ in range(max(1, int(repeat))):
            item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(model_id)
            if not item_id:
                ConsoleLog("ItemBroadCaster", f"ItemId für Model {model_id} nicht gefunden.",
                           Py4GW.Console.MessageType.Warning)
                break
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Routines.Yield.wait(delay)

    yield


def broadcast_skill(skill_name: str, cast_locally=True, delay=300):
    skill_id = int(GLOBAL_CACHE.Skill.GetID(skill_name) or 0)
    if not skill_id:
        ConsoleLog("SkillBroadCaster", f"Skill '{skill_name}' not found.", Py4GW.Console.MessageType.Error)
        return

    target_id = Player.GetTargetID()
    ConsoleLog("SkillBroadCaster", f"Target ID is {target_id}", Py4GW.Console.MessageType.Info)
    if not target_id:
        ConsoleLog("SkillBroadCaster", "No current target on main account.", Py4GW.Console.MessageType.Warning)
        return

    sender = GLOBAL_CACHE.Player.GetAccountEmail()
    for email in get_other_accounts():
        GLOBAL_CACHE.ShMem.SendMessage(sender_email=sender, receiver_email=email, command=SharedCommandType.UseSkill,
                                       params=(float(target_id), float(skill_id)), )

    if cast_locally:
        slot = int(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) or 0)
        if 1 <= slot <= 8:
            yield from Routines.Yield.Skills.CastSkillSlot(slot, aftercast_delay=delay)

    yield


def get_user_settings():
    if not hasattr(bot.config, "user_vars"):
        bot.config.user_vars = {}
    uv = bot.config.user_vars
    uv.setdefault("desired_mobstopper_quantity", 402)
    uv.setdefault("completed_mobstopper_cycles", 0)
    return uv


def draw_settings_ui():
    import PyImGui
    uv = get_user_settings()
    PyImGui.text("Mobstopper Settings")

    desired = int(uv.get("desired_mobstopper_quantity", 10))

    uv["desired_mobstopper_quantity"] = desired

    PyImGui.text(f"Completed: {uv.get('completed_mobstopper_cycles', 0)}")
    if PyImGui.button("Reset Completed"):
        uv["completed_mobstopper_cycles"] = 0


bot.UI.override_draw_config(lambda: draw_settings_ui())


def GoToGrenthStatue():
    bot.States.AddHeader("Moving to Grenth Statue")
    bot.Move.XY(*GRENTH_STATUE_POSITON, "Move to Grenth Statue")


def KneelBeforeStatue():
    def _kneel():
        Player.SendChatCommand("kneel")
        yield from Routines.Yield.wait(300)
        bot.Move.XY(*GRENTH_STATUE_SECOND_POSITON, "Move to second Grenth Statue position")
        yield from Routines.Yield.wait(600)

    bot.States.AddCustomState(_kneel, "Kneel")


def EnterUw():
    bot.States.AddHeader("Speaking With Voice of Grenth for Entering the Underworld")

    bot.Move.XYAndInteractNPC(*VOICE_OF_GRENTH_POSITION, "Interact with Voice of Grenth")
    bot.Move.XYAndInteractNPC(*VOICE_OF_GRENTH_POSITION, "Interact with Voice of Grenth")
    bot.Wait.ForTime(300)

    if Player.GetTargetID() == 11:
        bot.States.JumpToStepName("[H]Speaking With Voice of Grenth for Entering the Underworld_3")

    bot.Dialogs.WithModel(VOICE_OF_GRENTH_ID, ENTER_UW_DIALOG, "Yes. To serve Grenth.")
    # bot.Dialogs.WithModel(VOICE_OF_GRENTH_ID, ENTER_UW_ACCEPT, "Accept.")

    bot.Wait.ForMapLoad(target_map_id=THE_UNDERWORLD_ID)
    bot.Wait.ForTime(300)

def UseTrap():
    bot.States.AddHeader("Using Skeleton Trap")
    _set_trap_used(False)

    bot.Wait.ForTime(100)
    bot.States.AddCustomState(lambda: broadcast_skill("By_Urals_Hammer"), "Broadcast By_Urals_Hammer")
    bot.Wait.ForTime(10)
    bot.States.AddCustomState(lambda: broadcast_item(SKELETON_TRAP_ID, repeat=1, use_locally=True, delay=0),
        "Place Skeleton Trap")

    # Mark as completed once the placement state has run
    def _mark_trap_done():
        _set_trap_used(True)
        yield

    bot.States.AddCustomState(_mark_trap_done, "Mark Trap Used")


def KillSkeleton():
    bot.States.AddHeader("Killing Skeleton")
    bot.Target.Model(SKELETON_AGENT_MODEL_ID)
    bot.States.AddCustomState(lambda: broadcast_skill("Shroud_of_Distress"), "Broadcast Dash Shroud_of_Distress")
    bot.Wait.ForTime(1010)
    bot.States.AddCustomState(lambda: broadcast_skill("Dash"), "Broadcast Dash")
    bot.States.AddCustomState(lambda: broadcast_skill("Deaths_Charge"), "Broadcast Deaths_Charge")
    bot.Wait.ForTime(3600)
    bot.States.AddCustomState(lambda: broadcast_skill("Light_of_Deldrimor"), "Broadcast Light_of_Deldrimor")
    bot.Wait.ForTime(1100)


def PartyResign():
    bot.States.AddHeader("Resigning Party")
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.ForMapLoad(target_map_id=TEMPLE_OF_THE_AGES_ID)


def Reset():
    bot.States.AddHeader("Resetting")
    bot.Wait.ForMapToChange(target_map_id=TEMPLE_OF_THE_AGES_ID)
    bot.Wait.ForTime(200)
    ActionQueueManager().ResetAllQueues()
    bot.States.JumpToStepName(
        "[H]Moving to Grenth Statue_2")


def create_bot_routine(bot: Botting) -> None:
    bot.States.AddHeader("Skeleton Collection Started")
    bot.States.AddCustomState(initialize_bot, "Initialize Bot")
    # bot.Templates.Routines.PrepareForFarm(map_id_to_travel=TEMPLE_OF_THE_AGES_ID)
    bot.Templates.Pacifist()
    GoToGrenthStatue()
    KneelBeforeStatue()
    EnterUw()
    # EnterUwPerScroll()
    KillSkeleton()

    UseTrap()
    bot.Wait.UntilCondition(lambda: TRAP_PLACED)
    bot.Wait.ForTime(150)  # small buffer
    bot.Wait.ForTime(1500)
    PartyResign()
    Reset()


bot.SetMainRoutine(create_bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=None)


if __name__ == "__main__":
    main()
