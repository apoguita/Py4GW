ui_msgs_names = {
    0x10000007: {
        "name": "RerenderAgentModel",
        "wparam": {
            'agent_id': None
        }
    },
    0x10000009: {
        "name": "UpdateAgentEffects"
    },
    0x10000019: {
        "name": "ShowAgentNameTag",
        "wparam": {
            "AgentNameTagInfo*": None
        }
    },
    0x1000001A: {
        "name": "kHideAgentNameTag"
    },
    0x1000001B: {
        "name": "kSetAgentNameTagAttribs",
        "wparam": {
            "AgentNameTagInfo*": None
        }
    },
    0x10000020: {
        "name": "kChangeTarget",
        "wparam": {
            "ChangeTargetUIMsg*": None
        }
    },
    0x10000027: {
        "name": "kAgentStartCasting",
        "wparam": {
            "UIPacket::kAgentStartCasting*": None
        }
    },
    0x10000029: {
        "name": "kShowMapEntryMessage",
        "wparam": {
            "title": None,
            "subtitle": None
        }
    },
    0x1000002A: {
        "name": "kSetCurrentPlayerData"
    },
    0x10000034: {
        "name": "kPostProcessingEffect",
        "wparam": {
            "UIPacket::kPostProcessingEffect": None
        }
    },
    0x10000038: {
        "name": "kHeroAgentAdded"
    },
    0x10000039: {
        "name": "kHeroDataAdded"
    },
    0x10000040: {
        "name": "kShowXunlaiChest"
    },
    0x10000046: {
        "name": "kMinionCountUpdated"
    },
    0x10000047: {
        "name": "kMoraleChange",
        "wparam": {
            "agent_id": None,
            "morale_percent": None
        }
    },
    0x10000050: {
        "name": "kLoginStateChanged",
        "wparam": {
            "is_logged_in": None,
            "unknown": None
        }
    },
    0x10000055: {
        "name": "kEffectAdd",
        "wparam": {
            "agent_id": None,
            "GW::Effect*": None
        }
    },
    0x10000056: {
        "name": "kEffectRenew",
        "wparam": {
            "GW::Effect*": None
        }
    },
    0x10000057: {
        "name": "kEffectRemove",
        "wparam": {
            "effect_id": None
        }
    },
    0x1000005E: {
        "name": "kUpdateSkillbar",
        "wparam": {
            "agent_id": None
        }
    },
    0x1000005B: {
        "name": "kSkillActivated",
        "wparam": {
            "agent_id": None,
            "skill_id": None
        }
    },
    0x10000065: {
        "name": "kTitleProgressUpdated",
        "wparam": {
            "title_id": None
        }
    },
    0x10000066: {
        "name": "kExperienceGained",
        "wparam": {
            "experience_amount": None
        }
    },
    0x1000007E: {
        "name": "kWriteToChatLog",
        "wparam": {
            "UIPacket::kWriteToChatLog*": None
        }
    },
    0x1000007F: {
        "name": "kWriteToChatLogWithSender",
        "wparam": {
            "UIPacket::kWriteToChatLogWithSender*": None
        }
    },
    0x10000081: {
        "name": "kPlayerChatMessage",
        "wparam": {
            "UIPacket::kPlayerChatMessage*": None
        }
    },
    0x10000089: {
        "name": "kFriendUpdated",
        "wparam": {
            "GW::Friend*": None
        }
    },
    0x1000008A: {
        "name": "kMapLoaded"
    },
    0x10000090: {
        "name": "kOpenWhisper",
        "wparam": {
            "wchar* name": None
        }
    },
    0x1000009B: {
        "name": "kLogout",
        "wparam": {
            "unknown": None,
            "character_select": None
        }
    },
    0x1000009C: {
        "name": "kCompassDraw",
        "wparam": {
            "UIPacket::kCompassDraw*": None
        }
    },
    0x100000A0: {
        "name": "kOnScreenMessage",
        "wparam": {
            "wchar_** encoded_string": None
        }
    },
    0x100000A4: {
        "name": "kDialogBody",
        "wparam": {
            "DialogBodyInfo*": None
        }
    },
    0x100000A1: {
        "name": "kDialogButton",
        "wparam": {
            "DialogButtonInfo*": None
        }
    },
    0x100000B1: {
        "name": "kTargetNPCPartyMember",
        "wparam": {
            "unk": None,
            "agent_id": None
        }
    },
    0x100000B2: {
        "name": "kTargetPlayerPartyMember",
        "wparam": {
            "unk": None,
            "player_number": None
        }
    },
    0x100000BB: {
        "name": "kQuotedItemPrice",
        "wparam": {
            "item_id": None,
            "price": None
        }
    },
    0x100000C0: {
        "name": "kStartMapLoad",
        "wparam": {
            "map_id": None
        }
    },
    0x100000C5: {
        "name": "kWorldMapUpdated"
    },
    0x100000C5: {
        "name": "WorldMapUpdated"
    },
    0x100000D8: {
        "name": "GuildMemberUpdated",
        "wparam": {
            "GuildPlayer::name_ptr": None
        }
    },
    0x100000DF: {
        "name": "ShowHint",
        "wparam": {
            "icon_type": None,
            "message_enc": None
        }
    },
    0x100000EA: {
        "name": "UpdateGoldCharacter",
        "wparam": {
            "unk": None,
            "gold_character": None
        }
    },
    0x100000EB: {
        "name": "UpdateGoldStorage",
        "wparam": {
            "unk": None,
            "gold_storage": None
        }
    },
    0x100000EC: {
        "name": "InventorySlotUpdated"
    },
    0x100000ED: {
        "name": "EquipmentSlotUpdated"
    },
    0x100000EF: {
        "name": "InventorySlotCleared"
    },
    0x100000F0: {
        "name": "EquipmentSlotCleared"
    },
    0x100000F8: {
        "name": "PvPWindowContent"
    },
    0x10000100: {
        "name": "PreStartSalvage",
        "wparam": {
            "item_id": None,
            "kit_id": None
        }
    },
    0x10000103: {
        "name": "TradePlayerUpdated",
        "wparam": {
            "GW::TraderPlayer*": None
        }
    },
    0x10000104: {
        "name": "ItemUpdated",
        "wparam": {
            "UIPacket::kItemUpdated*": None
        }
    },
    0x1000010F: {
        "name": "MapChange",
        "wparam": {
            "map_id": None
        }
    },
    0x10000113: {
        "name": "CalledTargetChange",
        "wparam": {
            "player_number": None,
            "target_id": None
        }
    },
    0x10000117: {
        "name": "ErrorMessage",
        "wparam": {
            "error_index": None,
            "error_encoded_string": None
        }
    },
    0x10000118: {
        "name": "PartyHardModeChanged",
        "wparam": {
            "is_hard_mode": None
        }
    },
    0x10000119: {
        "name": "PartyAddHenchman"
    },
    0x1000011A: {
        "name": "PartyRemoveHenchman"
    },
    0x1000011C: {
        "name": "PartyAddHero"
    },
    0x1000011D: {
        "name": "PartyRemoveHero"
    },
    0x10000122: {
        "name": "PartyAddPlayer"
    },
    0x10000124: {
        "name": "PartyRemovePlayer"
    },
    0x1000012D: {
        "name": "PartyDefeated"
    },
    0x10000135: {
        "name": "PartySearchInviteReceived",
        "wparam": {
            "UIPacket::kPartySearchInviteReceived*": None
        }
    },
    0x10000137: {
        "name": "PartySearchInviteSent"
    },
    0x10000138: {
        "name": "PartyShowConfirmDialog",
        "wparam": {
            "UIPacket::kPartyShowConfirmDialog": None
        }
    },
    0x1000013E: {
        "name": "PreferenceEnumChanged",
        "wparam": {
            "UiPacket::kPreferenceEnumChanged": None
        }
    },
    0x1000013F: {
        "name": "PreferenceFlagChanged",
        "wparam": {
            "UiPacket::kPreferenceFlagChanged": None
        }
    },
    0x10000140: {
        "name": "PreferenceValueChanged",
        "wparam": {
            "UiPacket::kPreferenceValueChanged": None
        }
    },
    0x10000141: {
        "name": "UIPositionChanged",
        "wparam": {
            "UIPacket::kUIPositionChanged": None
        }
    },
    0x10000149: {
        "name": "QuestAdded",
        "wparam": {
            "quest_id": None
        }
    },
    0x1000014A: {
        "name": "QuestDetailsChanged",
        "wparam": {
            "quest_id": None
        }
    },
    0x1000014C: {
        "name": "ClientActiveQuestChanged",
        "wparam": {
            "quest_id": None
        }
    },
    0x1000014E: {
        "name": "ServerActiveQuestChanged",
        "wparam": {
            "UIPacket::kServerActiveQuestChanged*": None
        }
    },
    0x1000014F: {
        "name": "UnknownQuestRelated"
    },
    0x10000155: {
        "name": "ObjectiveAdd",
        "wparam": {
            "UIPacket::kObjectiveAdd*": None
        }
    },
    0x10000156: {
        "name": "ObjectiveComplete",
        "wparam": {
            "UIPacket::kObjectiveComplete*": None
        }
    },
    0x10000157: {
        "name": "ObjectiveUpdated",
        "wparam": {
            "UIPacket::kObjectiveUpdated*": None
        }
    },
    0x10000160: {
        "name": "TradeSessionStart",
        "wparam": {
            "trade_state": None,
            "player_number": None
        }
    },
    0x10000166: {
        "name": "TradeSessionUpdated"
    },
    0x10000170: {
        "name": "CheckUIState"
    },
    0x10000174: {
        "name": "CloseSettings"
    },
    0x10000175: {
        "name": "ChangeSettingsTab",
        "wparam": {
            "is_interface_tab": None
        }
    },
    0x10000177: {
        "name": "GuildHall",
        "wparam": {
            "gh_key": ["uint32_t[4]"]
        }
    },
    0x10000179: {
        "name": "LeaveGuildHall"
    },
    0x1000017A: {
        "name": "Travel"
    },
    0x1000017B: {
        "name": "OpenWikiUrl",
        "wparam": {
            "url": "char*"
        }
    },
    0x10000189: {
        "name": "AppendMessageToChat",
        "wparam": {
            "message": "wchar_t*"
        }
    },
    0x10000197: {
        "name": "HideHeroPanel",
        "wparam": {
            "hero_id": None
        }
    },
    0x10000198: {
        "name": "ShowHeroPanel",
        "wparam": {
            "hero_id": None
        }
    },
    0x1000019E: {
        "name": "MoveItem",
        "wparam": {
            "item_id": None,
            "to_bag": None,
            "to_slot": None,
            "prompt": "bool"
        }
    },
    0x100001A0: {
        "name": "InitiateTrade"
    },
    0x100001B9: {
        "name": "OpenTemplate",
        "wparam": {
            "GW::UI::ChatTemplate*": None
        }
    }
}
