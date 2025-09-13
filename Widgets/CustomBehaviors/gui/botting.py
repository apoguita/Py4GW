import PyImGui

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives.skills.follow_party_leader_during_aggro_strategy import FollowPartyLeaderDuringAggroStrategy

the_index = FollowPartyLeaderDuringAggroStrategy.AS_CLOSE_AS_POSSIBLE 
members = list(FollowPartyLeaderDuringAggroStrategy)

@staticmethod
def render():
    global the_index
    
    PyImGui.text(f"multiboxing bot collection")
    PyImGui.separator()

    if not GLOBAL_CACHE.Party.IsPartyLeader():
        PyImGui.text(f"feature restricted to party leader.")
        return

    names = [m.name for m in members]
    cur_index = members.index(the_index)
    new_index = PyImGui.combo("qzdqzd", cur_index, names)
    the_index = members[new_index]

    if PyImGui.button("PLAY"):
        pass


    