from enum import Enum


            # follow_party_leader_strategy = FollowPartyLeaderStrategy.CLOSEST
            # we want a better one

# some classes do not need to attack. 
# so FollowPartyLeaderStrategy.FAREST - if leader is in AGGRO, they stay at max Range.Spellcast of leader.

            
# some classes are caster. so FollowPartyLeaderStrategy.MID - if leader is in AGGRO, they stay at Range.Spellcast /2 of leader.
# some classes are melee. so FollowPartyLeaderStrategy.MID - if leader is in AGGRO, they stay at Range.Spellcast /2 of leader. they are moved thanks to autoattack.
            
# only if leader is a melee. if leader a caster, what do we do

# Create an enumeration
class FollowPartyLeaderDuringAggroStrategy(Enum):
    STAY_FARTHEST = 1 
    MID_DISTANCE = 2
    CLOSE = 3
    AS_CLOSE_AS_POSSIBLE = 4

