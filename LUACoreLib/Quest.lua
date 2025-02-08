local Quest = {}

function Quest.quest_instance()
    return PyQuest.PyQuest()
end

function Quest.GetActiveQuest()
    return Quest.quest_instance():get_active_quest_id()
end

function Quest.SetActiveQuest(quest_id)
    Quest.quest_instance():set_active_quest_id(quest_id)
end

function Quest.AbandonQuest(quest_id)
    Quest.quest_instance():abandon_quest(quest_id)
end

return Quest
