# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PyKeystroke  #keystroke functions and classes
import traceback    #traceback to log stack traces
# End Necessary Imports
import Py4GWcorelib as CoreLib

#thos scriupt is created just as a test of functions, doesnt have any other purpose


module_name = "Test script"

def DrawWindow():
    global module_name
    try:
        description = "This is a test for the PingHandler class \nIt creates a callback and stores basic ping statistics."


        width, height = 400, 500
        PyImGui.set_next_window_size(width, height)

        if PyImGui.begin(module_name):
            PyImGui.text(f"Player Name: {CoreLib.Player.GetName()}")
            if PyImGui.button("Send test to chat channel"):
                CoreLib.Player.SendChat('#',"test message")

            if PyImGui.button("Send whisper to player"):
                CoreLib.Player.SendWhisper("Player Name","test message")

            PyImGui.separator()
            primary, secondary = CoreLib.Agent.GetProfessionNames(CoreLib.Player.GetAgentID())
            PyImGui.text(f"{primary}/{secondary}")

            primary_short, secondary_short = CoreLib.Agent.GetProfessionShortNames(CoreLib.Player.GetAgentID())
            PyImGui.text(f"{primary_short}/{secondary_short}")
            PyImGui.separator()
            PyImGui.text(f"Level: {CoreLib.Agent.GetLevel(CoreLib.Player.GetAgentID())}")
            PyImGui.text(f"Energy: {CoreLib.Agent.GetEnergy(CoreLib.Player.GetAgentID())}")
            PyImGui.text(f"Max Energy: {CoreLib.Agent.GetMaxEnergy(CoreLib.Player.GetAgentID())}")
            PyImGui.text(f"Energy Regen: {CoreLib.Agent.GetEnergyRegen(CoreLib.Player.GetAgentID())}")
            PyImGui.separator()
            PyImGui.text(f"Health: {CoreLib.Agent.GetHealth(CoreLib.Player.GetAgentID())}")
            PyImGui.text(f"Max Health: {CoreLib.Agent.GetMaxHealth(CoreLib.Player.GetAgentID())}")
            PyImGui.text(f"Health Regen: {CoreLib.Agent.GetHealthRegen(CoreLib.Player.GetAgentID())}")
            PyImGui.separator()
            PyImGui.text(f"Is Moving: {CoreLib.Agent.IsMoving(CoreLib.Player.GetAgentID())}")
            velocityx, velocityy = CoreLib.Agent.GetVelocityVector(CoreLib.Player.GetAgentID())
            PyImGui.text(f"Velocity X: {velocityx} Velocity Y: {velocityy}")
            PyImGui.separator()
            PyImGui.text(f"IsMartial: {CoreLib.Agent.IsMartial(CoreLib.Player.GetAgentID())}")
            PyImGui.text(f"Get casting Skill: {CoreLib.Agent.GetCastingSkill(CoreLib.Player.GetAgentID())}")

            #weapon extra data
            weapon_item_type, offhand_item_type, weapon_item_id, offhand_item_id = CoreLib.Agent.GetWeaponExtraData(CoreLib.Player.GetAgentID())

            PyImGui.text(f"Weapon Item Type: {weapon_item_type}")
            PyImGui.text(f"Offhand Item Type: {offhand_item_type}")
            PyImGui.text(f"Weapon Item ID: {weapon_item_id}")
            PyImGui.text(f"Offhand Item ID: {offhand_item_id}")
            PyImGui.separator()
            PyImGui.text(f"Skill Name: {CoreLib.Skill.GetName(817)}")
            PyImGui.text(f"Skill Type: {CoreLib.Skill.GetTypeName(817)}")
            PyImGui.text(f"Energy Cost: {CoreLib.Skill.GetEnergyCost(817)}")
            PyImGui.separator()
            #get party leader
            party_leader_id = CoreLib.Party.GetPartyLeaderID()
            PyImGui.text(f"PartyLeader ID: {party_leader_id}")
            PyImGui.text(f"IsSpirirt: {CoreLib.Agent.IsSpirit(party_leader_id)}")
            PyImGui.separator()
            if PyImGui.button("Invite Player"):
                CoreLib.Party.InvitePlayer("Test Name")
            PyImGui.end()


    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in PerformTask: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

key_w_toggle = False
key_i_toggle = False

def DrawWindow2():
    global module_name
    global key_w_toggle, key_i_toggle
    try:
        description = "This is a test for the PingHandler class \nIt creates a callback and stores basic ping statistics."

        key_sender = PyKeystroke.PyScanCodeKeystroke()
        virtual_key_sender = PyKeystroke.PyScanCodeKeystroke() #?? bad

        key_senderA = PyKeystroke.PyScanCodeKeystroke()
        key_senderB = PyKeystroke.PyScanCodeKeystroke()
        key_senderC = PyKeystroke.PyScanCodeKeystroke()

        width, height = 400, 500
        PyImGui.set_next_window_size(width, height)

        if PyImGui.begin(module_name+"2"):
            PyImGui.text(f"Player Name: {CoreLib.Player.GetName()}")


            PyImGui.separator()
            PyImGui.text("Keystroke Using ScanCodes")
            if PyImGui.collapsing_header("scan codes"):
                if PyImGui.button("Push Keystroke W"):
                    key_sender.PushKey(CoreLib.Key.W.value)

                if PyImGui.button("Press Keystroke W"):
                    key_sender.PressKey(CoreLib.Key.W.value)

                if PyImGui.button("Release Keystroke W"):
                    key_sender.ReleaseKey(CoreLib.Key.W.value)

                PyImGui.separator()
                if PyImGui.button("Push Keystroke F11"):
                    key_sender.PushKey(CoreLib.Key.F11.value)

                PyImGui.separator()

                if PyImGui.button("Push Keystroke Space"):
                    key_sender.PushKey(CoreLib.Key.Space.value)

                PyImGui.separator()

                if PyImGui.button("Push Keystroke Combo"):
                    key_sender.PushKeyCombo([CoreLib.Key.W.value, CoreLib.Key.A.value])

                if PyImGui.button("Press Keystroke Combo"):
                    key_sender.PressKeyCombo([CoreLib.Key.W.value, CoreLib.Key.A.value])

                if PyImGui.button("Release Keystroke Combo"):
                    key_sender.ReleaseKeyCombo([CoreLib.Key.W.value, CoreLib.Key.A.value])

            if PyImGui.collapsing_header("CoreLib functions"):
                if PyImGui.button("Press Keystroke W"):
                    CoreLib.Keystroke.Press(CoreLib.Key.W)
                 
                if PyImGui.button("Release Keystroke W"):
                    CoreLib.Keystroke.Release(CoreLib.Key.W)

                 
                if PyImGui.button("Press And Release Keystroke I"):
                    CoreLib.Keystroke.PressAndRelease(CoreLib.Key.I)


            PyImGui.separator()
            PyImGui.text("Keystroke Using Virtual Codes (virtual keys not reliable)")
            if PyImGui.collapsing_header("Virtual codes"):
                if PyImGui.button("Push Keystroke W"):
                    virtual_key_sender.PushKey(CoreLib.Key.W.value)

                if PyImGui.button("Press Keystroke W"):
                    virtual_key_sender.PressKey(CoreLib.Key.W.value)

                if PyImGui.button("Release Keystroke W"):
                    virtual_key_sender.ReleaseKey(CoreLib.Key.W.value)

                PyImGui.separator()

                if PyImGui.button("Push Keystroke Combo"):
                    virtual_key_sender.PushKeyCombo([CoreLib.Key.Ctrl.value, CoreLib.Key.Shift.value, CoreLib.Key.C.value])

                if PyImGui.button("Press Keystroke Combo"):
                    virtual_key_sender.PressKeyCombo([CoreLib.Key.Ctrl.value, CoreLib.Key.Shift.value, CoreLib.Key.C.value])

                if PyImGui.button("Release Keystroke Combo"):
                    virtual_key_sender.ReleaseKeyCombo([CoreLib.Key.Ctrl.value, CoreLib.Key.Shift.value, CoreLib.Key.C.value])

            PyImGui.separator()
            if PyImGui.button("Drop buff"):
                CoreLib.Buffs.DropBuff(58)

            PyImGui.separator()
            if PyImGui.button("Send Dialog"):
                CoreLib.Player.SendDialog(0x84)

            if PyImGui.button("Send Dialog Take"):
                CoreLib.Player.SendChatCommand("dialog take")
            PyImGui.end()


    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in PerformTask: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def DrawWindowItems():
    global module_name
    global key_w_toggle, key_i_toggle
    try:
 
        width, height = 400, 500
        PyImGui.set_next_window_size(width, height)

        if PyImGui.begin(module_name+"Items"):
            PyImGui.text(f"First ID Kit: {CoreLib.Inventory.GetFirstIDKit()}")
            PyImGui.text(f"First Salvage Kit: {CoreLib.Inventory.GetFirstSalvageKit()}")
            PyImGui.text(f"First Unid Item: {CoreLib.Inventory.GetFirstUnidentifiedItem()}")
            PyImGui.text(f"First Unsalvaged Item: {CoreLib.Inventory.GetFirstSalvageableItem()}")


            PyImGui.separator()
            
            if PyImGui.button("Identify First Available Item"):
                CoreLib.Inventory.IdentifyFirst()

            if PyImGui.button("Salvage First Available Item"):
                if not CoreLib.Inventory.IsInSalvageSession():
                    CoreLib.Inventory.SalvageFirst()

            if CoreLib.Inventory.IsInSalvageSession() and CoreLib.Inventory.IsSalvageSessionDone():
                CoreLib.Inventory.FinishSalvage()

            PyImGui.text(f"Modifiers count: {CoreLib.Inventory.Item.GetModifiersCount(39)}")
            modifiers = CoreLib.Inventory.Item.GetModifiers(39)

            if len(modifiers) == 0:
                PyImGui.text("No Modifiers")
            else:
                for idx, modifier in enumerate(modifiers):
                    PyImGui.text(f"Modifier {idx + 1}:")
                    PyImGui.text(f"  {modifier.ToString()}")
                    PyImGui.separator()


            PyImGui.end()


    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in PerformTask: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        DrawWindow()
        DrawWindow2()
        DrawWindowItems()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
