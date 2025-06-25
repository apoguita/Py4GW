from Py4GWCoreLib import *

class Blessings(Enum):
    # — Nightfall: Sunspear promotion bounties —
    Corsair_Bounty   = (1794, 1842, 1971, 1972)
    Giant_Hunt       = (1853, 1963, 1964)
    Heket_Hunt       = (1837, 1838, 1977, 1978)
    Kournan_Bounty   = (1839, 1843, 1979, 1980)
    Mandragor_Hunt   = (1791, 1840, 1841, 1852, 1961, 1962)
    Minotaur_Hunt    = (1832, 1969, 1970)
    Monster_Hunt     = (1822, 1823, 1824, 1825, 1850, 1959, 1960, 2043, 2044)
    Plant_Hunt       = (1795, 1833, 1834, 1973, 1974)
    Skale_Hunt       = (1790, 1835, 1836, 1975, 1976)
    Skree_Battle     = (1792, 1828, 1965, 1966)
    Undead_Hunt      = (1796, 1854, 1981, 1982)
    Insect_Hunt      = (1967)

    # — Nightfall: Lightbringer promotion bounties —
    Anguish_Hunt     = (1898, 2040)
    Demon_Hunt       = (1831,)
    Dhuum_Battle     = (1844, 2030, 2031)
    Elemental_Hunt   = (1826, 1827, 1846, 2032, 2033)
    Margonite_Battle = (1849, 2036, 2037)
    Menzies_Battle   = (1845, 2038, 2039)
    Monolith_Hunt    = (1847, 1848, 2034, 2035)
    Titan_Hunt       = (1851, 2041, 2042)

    # — Factions —
    Blessing_of_the_Kurzicks = (593, 912)
    Blessing_of_the_Luxons   = (1947, 1946)

    # — Eye of the North —
    Dwarven_Raider           = (2445, 2446, 2447, 2448, 2549, 2565, 2566, 2567, 2568)
    Vanguard_Patrol          = (2457, 2458, 2459, 2460, 2550, 2578)
    Asuran_Bodyguard         = (2434, 2435, 2436, 2481, 2548, 2552)
    Norn_Hunting_Party       = (2469, 2470, 2471, 2472, 2551, 2591, 2592, 2593, 2594)

    def __init__(self, *ids):
        self.ids = ids

    @classmethod
    def all_ids(cls) -> list[int]:
        """Flatten every member’s IDs into one list."""
        return [i for member in cls for i in member.ids]

    @classmethod
    def any_active(cls, me) -> bool:
        """Return True if any of these IDs has an active effect on `me`."""
        return any(Effects.EffectExists(me, i) for i in cls.all_ids())

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Normalize a member name like Corsair_Bounty" → "Corsair Bounty"""
        return name.replace('_', ' ').title()

# Cache your player agent once
me = Player.GetAgentID()

# Return the first active blessing ID, or None
def find_first_active_blessing(me):
    for sid in Blessings.all_ids():
        if Effects.EffectExists(me, sid):
            return sid
    return None

# Return True if any blessing ID is active on `me`
def has_any_blessing(me):
    return any(Effects.EffectExists(me, sid) for sid in Blessings.all_ids())

# Called once per-game‑frame by your Py4GW ImGui hook
def on_imgui_render(me):
    PyImGui.begin("Blessing Checker")

    first_id = find_first_active_blessing(me)
    if first_id is not None:
        member = next((m for m in Blessings if first_id in m.ids), None)
        if member:
            nice = Blessings.normalize_name(member.name)
            PyImGui.text(f"First active blessing: {nice} (ID {first_id})")
        else:
            PyImGui.text(f"First active blessing ID: {first_id}")
    else:
        PyImGui.text("No active blessing found.")

    any_active = has_any_blessing(me)
    PyImGui.text(f"Any active? {'Yes' if any_active else 'No'}")
    PyImGui.end()

def main():
    on_imgui_render(me)
