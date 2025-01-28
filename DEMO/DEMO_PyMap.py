# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PyMap        #Map functions and classes
import PyAgent      #Agent functions and classes
import PyPlayer     #Player functions and classes
import PyParty      #Party functions and classes
import PyItem       #Item functions and classes
import PyInventory  #Inventory functions and classes
import PySkill      #Skill functions and classes
import PySkillbar   #Skillbar functions and classes
import PyMerchant   #Merchant functions and classes
import traceback    #traceback to log stack traces
# End Necessary Imports


module_name = "PyMap_DEMO"

map_instance = PyMap.PyMap()

def draw_window():
    global map_instance
    map_instance.GetContext()
    
    if PyImGui.begin(module_name):
        if PyImGui.collapsing_header("Instance Fields", PyImGui.TreeNodeFlags.DefaultOpen):
            PyImGui.text(f"Instance ID: {map_instance.map_id.ToInt()}")
            PyImGui.text(f"Instance Name: {map_instance.map_id.GetName()}")         
            PyImGui.separator()

            region_type_instance = map_instance.region_type.Get()
            PyImGui.text(f"Region ID: {map_instance.server_region.ToInt()}")
            PyImGui.text(f"Region Name: {map_instance.server_region.GetName()}") 
            PyImGui.text(f"Is Mission Outpost? {'Yes' if region_type_instance == PyMap.RegionType.MissionOutpost else 'No'}")
            PyImGui.separator()

            continent = map_instance.continent.Get()
            PyImGui.text(f"Continent (ID: {map_instance.continent.ToInt()}, name: {map_instance.continent.GetName()})")
            PyImGui.text(f"Is Elona? {'Yes' if continent == PyMap.ContinentType.Elona else 'No'}")
            PyImGui.separator()

            PyImGui.text(f"Party Size: {map_instance.max_party_size}")
            PyImGui.separator()

            PyImGui.text(f"Is Map Ready? {'Yes' if map_instance.is_map_ready else 'No'}")
            PyImGui.text(f"Instance Time: {map_instance.instance_time}")

            if PyImGui.collapsing_header("Map Fields", PyImGui.TreeNodeFlags.DefaultOpen):
                PyImGui.text(f"MapID: {map_instance.map_id.ToInt()}")
                instance_type = map_instance.instance_type.Get()

                campaign = map_instance.campaign.Get()
                PyImGui.text(f"Campaign ID: {map_instance.campaign.ToInt()}")
                PyImGui.text(f"Campaign Name: {map_instance.campaign.GetName()}")
                PyImGui.text(f"Is Factions? {'Yes' if campaign == PyMap.CampaignType.Factions else 'No'}")
                PyImGui.separator()

                if PyImGui.collapsing_header("Travel"):
                    if PyImGui.button("Travel Method 1"):
                        success = map_instance.Travel(857)  # Embark Beach
                    if PyImGui.button("Travel Method 2"):
                        success = map_instance.Travel(248, 0, 0)  # Great Temple Of Balthazar

                    PyImGui.separator()

                if PyImGui.collapsing_header("Outpost Exclusive Fields"):
                    PyImGui.text(f"Is Outpost? {'Yes' if instance_type == PyMap.InstanceType.Outpost else 'No'}")
                    PyImGui.text(f"Map Name: {map_instance.map_id.GetName()}")
                    PyImGui.separator()

                    region_type = map_instance.server_region.Get()
                    PyImGui.text(f"Is America? {'Yes' if region_type == PyMap.ServerRegionType.America else 'No'}")
                    PyImGui.text(f"Region ID: {map_instance.server_region.ToInt()}")
                    PyImGui.text(f"Region Name: {map_instance.server_region.GetName()}")
                    PyImGui.separator()

                    PyImGui.text(f"District: {map_instance.district}")
                    PyImGui.separator()

                    language = map_instance.language.Get()
                    PyImGui.text(f"Language ID: {map_instance.language.ToInt()}")
                    PyImGui.text(f"Language Name: {map_instance.language.GetName()}")
                    PyImGui.text(f"Is English? {'Yes' if language == PyMap.LanguageType.English else 'No'}")
                    PyImGui.separator()

                    PyImGui.text(f"Has Enter Button? {'Yes' if map_instance.has_enter_button else 'No'}")
                    PyImGui.separator()

                    if map_instance.has_enter_button and map_instance.instance_type.Get() == PyMap.InstanceType.Outpost:
                        if PyImGui.button("Enter Mission"):
                            map_instance.EnterChallenge()
                        PyImGui.text("Not sure how CancelEnterChallenge works :(")
                        if PyImGui.button("Cancel Enter"):
                            map_instance.CancelEnterChallenge()

                if PyImGui.collapsing_header("Explorable Exclusive Fields"):
                    PyImGui.text(f"Is In Cinematic: {map_instance.is_in_cinematic}")
                    PyImGui.separator()
                    PyImGui.text(f"Is Vanquishable? {'Yes' if map_instance.is_vanquishable_area else 'No'}")
                    PyImGui.separator()

                    if PyImGui.collapsing_header("Hard Mode Exclusive Fields"):
                        PyImGui.text(f"Foes Killed: {map_instance.foes_killed}")
                        PyImGui.text(f"Foes to Kill: {map_instance.foes_to_kill}")

        PyImGui.end()


# main() must exist in every script and is the entry point for your Script's execution.
def main():
    try:
        draw_window()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}")
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}")
    finally:
        pass  # Replace with your actual code


# This ensures that main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
