from PyItem import ItemModifier
from Py4GWCoreLib.enums_src.Item_enums import Rarity
from Sources.frenkeyLib.ItemHandling.Mods.decoded_modifier import DecodedModifier
from Sources.frenkeyLib.ItemHandling.Mods.properties import ItemProperty
from typing import TypeVar

T = TypeVar("T", bound=ItemProperty)

class ItemModifierParser:
    def __init__(self, runtime_modifiers: list[ItemModifier], rarity: Rarity = Rarity.Blue):
        self.modifiers: list[DecodedModifier] = []
        self.properties: list[ItemProperty] = []
        self.rarity: Rarity = rarity

        self._decode(runtime_modifiers)
        self._build_properties()

    def _decode(self, runtime_modifiers: list[ItemModifier]):        
        for mod in runtime_modifiers:
            decoded = DecodedModifier.from_runtime(mod)
            if decoded is not None:
                self.modifiers.append(decoded)

    def _build_properties(self):
        from Sources.frenkeyLib.ItemHandling.Mods.upgrade_parser import get_property_factory

        for mod in self.modifiers:
            factory = get_property_factory().get(mod.identifier)
            if factory:
                prop = factory(mod, self.modifiers, self.rarity)
                    
                if prop:
                    #only add if no property of that type already exists, since some modifiers have multiple entries with the same identifier but different args
                    # if not any(isinstance(p, type(prop)) and p.modifier.arg == prop.modifier.arg for p in self.properties):
                    self.properties.append(prop)
                else:
                    self.properties.append(ItemProperty(mod, rarity=self.rarity))
                        
    def get_properties(self) -> list[ItemProperty]:
        return self.properties
