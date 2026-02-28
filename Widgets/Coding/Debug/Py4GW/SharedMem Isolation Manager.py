import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, ImGui, Color, Routines

MODULE_NAME = "Shared Memory Isolation Manager"


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Lists all active shared-memory accounts, including isolated ones,")
    PyImGui.text("and lets you toggle per-account isolation in place.")
    PyImGui.end_tooltip()


def _draw_account_row(account):
    email = str(account.AccountEmail or "").strip()
    if not email:
        return

    label = account.AgentData.CharacterName or account.AccountName or email
    isolated = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(email))
    new_isolated = PyImGui.checkbox(f"{label}##iso_{email}", isolated)
    if new_isolated == isolated:
        return

    GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(email, new_isolated)


def draw():
    if not Routines.Checks.Map.MapValid():
        return

    if ImGui.Begin(MODULE_NAME, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData(sort_results=True, include_isolated=True) or []
        if not accounts:
            PyImGui.text("No shared-memory accounts found.")
        else:
            PyImGui.text(f"Accounts: {len(accounts)}")
            PyImGui.separator()
            for account in accounts:
                _draw_account_row(account)
    ImGui.End(MODULE_NAME)


def main():
    pass


if __name__ == "__main__":
    main()
