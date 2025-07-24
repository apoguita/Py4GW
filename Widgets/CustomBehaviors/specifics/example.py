from Widgets.CustomBehaviors.specifics.assassin_vaettir_farm.assassin_vaettir_farm_killing import AssassinVaettirFarm_Killing_UtilitySkillBar
from Widgets.CustomBehaviors.specifics.assassin_vaettir_farm.assassin_vaettir_farm_running import AssassinVaettirFarm_Running_UtilitySkillBar

assassin_vaettir_farm_killing: AssassinVaettirFarm_Killing_UtilitySkillBar = AssassinVaettirFarm_Killing_UtilitySkillBar()
assassin_vaettir_farm_killing.act() # call that in the main while loop, this is non-blocking
assassin_vaettir_farm_killing.player_stuck(heart_of_shadow_target_agent_id=0) # call that when you want to trigger specific capabilities

assassin_vaettir_farm_running: AssassinVaettirFarm_Running_UtilitySkillBar = AssassinVaettirFarm_Running_UtilitySkillBar()
assassin_vaettir_farm_running.act() # call that in the main while loop, this is non-blocking
assassin_vaettir_farm_running.player_stuck(heart_of_shadow_target_agent_id=0) # call that when you want to trigger specific capabilities






