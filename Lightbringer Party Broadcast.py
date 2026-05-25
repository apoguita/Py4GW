import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Party, Player, Py4GW, SharedCommandType, TitleID


MODULE_NAME = 'Lightbringer Party Broadcast'
MODULE_ICON = 'Textures/Skill_Icons/[1813] - Lightbringer.jpg'


class _State:
    def __init__(self) -> None:
        self.last_status = 'Idle.'


STATE = _State()


def _same_party_accounts(include_self: bool = False) -> list:
    sender_email = str(Player.GetAccountEmail() or '').strip()
    if not sender_email:
        return []

    sender_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
    if sender_account is None:
        return []

    party_id = int(getattr(getattr(sender_account, 'AgentPartyData', None), 'PartyID', 0) or 0)
    if party_id <= 0:
        party_id = int(Party.GetPartyID() or 0)
    if party_id <= 0:
        return []

    accounts: list = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
        account_email = str(getattr(account, 'AccountEmail', '') or '').strip()
        if not account_email:
            continue
        if not include_self and account_email == sender_email:
            continue
        if int(getattr(getattr(account, 'AgentPartyData', None), 'PartyID', 0) or 0) != party_id:
            continue
        accounts.append(account)
    return accounts


def _set_lightbringer_for_party() -> None:
    sender_email = str(Player.GetAccountEmail() or '').strip()
    if not sender_email:
        STATE.last_status = 'No account email available.'
        return

    title_id = int(TitleID.Lightbringer)
    Player.SetActiveTitle(title_id)

    sent_count = 0
    for account in _same_party_accounts(include_self=False):
        receiver_email = str(getattr(account, 'AccountEmail', '') or '').strip()
        if not receiver_email:
            continue
        message_index = int(
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                receiver_email,
                SharedCommandType.SetActiveTitle,
                (float(title_id), 0.0, 0.0, 0.0),
                ('Lightbringer', '', '', ''),
            )
        )
        if message_index >= 0:
            sent_count += 1

    STATE.last_status = f'Set local Lightbringer and sent {sent_count} party message(s).'
    Py4GW.Console.Log(MODULE_NAME, STATE.last_status, Py4GW.Console.MessageType.Info)


def configure():
    return


def main():
    if PyImGui.begin(MODULE_NAME):
        PyImGui.text('Set Lightbringer for this account and all same-party accounts.')
        PyImGui.text(f'Current party id: {int(Party.GetPartyID() or 0)}')
        PyImGui.text(f'Party recipients: {len(_same_party_accounts(include_self=False))}')
        if PyImGui.button('Set Lightbringer For Party'):
            _set_lightbringer_for_party()
        PyImGui.separator()
        PyImGui.text_wrapped(STATE.last_status)
    PyImGui.end()


def ui_main():
    main()


if __name__ == '__main__':
    main()
