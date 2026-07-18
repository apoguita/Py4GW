from Py4GWCoreLib import Botting, Py4GW, Quest

bot = Botting("Turn In Rewards")

STEWARD_ID = 147
STEWARD_POSITION = (5332.0, 9048.0)
DIALOG_QUEST_SELECT = 0x846303
DIALOG_QUEST_ACCEPT = 0x846301
DIALOG_QUEST_COLLECT_REWARD = 0x846307
QUEST_ID = 1123
MAX_ITERATIONS = 5000
MOB_STOPPERS_PER_QUEST = 3


# ---------- Utility & Settings Helpers ----------
def get_user_settings():
    if not hasattr(bot.config, "user_vars"):
        bot.config.user_vars = {}
    uv = bot.config.user_vars
    uv.setdefault("desired_mobstopper_quantity", 402)
    uv.setdefault("completed_mobstopper_cycles", 0)
    return uv


def normalize_target_quantity(desired: int, previous: int | None = None) -> int:
    if desired < 0:
        return 0

    remainder = desired % MOB_STOPPERS_PER_QUEST

    if remainder == 0:
        return desired

    if previous is None:
        return desired - remainder + (MOB_STOPPERS_PER_QUEST if remainder >= MOB_STOPPERS_PER_QUEST / 2 else 0)

    if desired > previous:
        return desired + (MOB_STOPPERS_PER_QUEST - remainder)
    else:
        return desired - remainder


# ---------- Settings & UI ----------
def draw_settings_ui():
    import PyImGui
    uv = get_user_settings()
    PyImGui.text("Mobstopper Settings")

    old_desired = int(uv.get("desired_mobstopper_quantity", 9))
    desired = PyImGui.input_int("Desired Mobstoppers", old_desired)

    normalized = normalize_target_quantity(desired, old_desired)
    if normalized != old_desired:
        uv["desired_mobstopper_quantity"] = normalized

    PyImGui.text(f"Completed: {uv.get('completed_mobstopper_cycles', 0)}")
    if PyImGui.button("Reset Completed"):
        uv["completed_mobstopper_cycles"] = 0


bot.UI.override_draw_config(lambda: draw_settings_ui())


def AddCheckQuotaStep(step_name="Check Quota"):
    def _check():
        uv = get_user_settings()
        desired = int(uv.get("desired_mobstopper_quantity", 10))
        completed = int(uv.get("completed_mobstopper_cycles", 0))

        if completed >= desired:
            fsm = bot.config.FSM
            fsm.jump_to_state_by_name("Stop")
            fsm.resume()
        yield

    bot.States.AddCustomState(_check, step_name)


# ---------- Main Bot Routine ----------
def create_bot_routine(bot: Botting) -> None:
    bot.States.AddHeader("Mobstopper Collection Started")

    uv = get_user_settings()
    done = int(uv.get("completed_mobstopper_cycles", 0))
    desired = int(uv.get("desired_mobstopper_quantity", 402))

    if done >= desired:
        AddStopStep()

    bot.States.AddHeader("Travel to Lion's Arch")
    bot.Map.Travel(target_map_id=808)
    bot.States.AddHeader("Take Quest")
    bot.Move.XY(*STEWARD_POSITION, "Move to Steward")
    bot.Dialogs.WithModel(STEWARD_ID, DIALOG_QUEST_SELECT, "Talk to Steward")
    bot.Dialogs.WithModel(STEWARD_ID, DIALOG_QUEST_ACCEPT, "Accept Quest")
    bot.Wait.ForTime(50)
    bot.States.AddHeader(f"Turned in {done}/{desired} Mobstoppers")
    bot.Dialogs.WithModel(STEWARD_ID, DIALOG_QUEST_COLLECT_REWARD, "Collect Reward")
    bot.States.AddHeader("Rejoin LA")
    bot.Map.TravelGH()
    bot.Map.LeaveGH()

    uv["completed_mobstopper_cycles"] = done + MOB_STOPPERS_PER_QUEST
    bot.States.JumpToStepName("[H]Take Quest_3")

    fsm = bot.config.FSM
    fsm.resume()


bot.SetMainRoutine(create_bot_routine)


# ---------- Entry Point ----------

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=None)


if __name__ == "__main__":
    main()
