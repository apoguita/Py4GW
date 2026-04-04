import Py4GW
from PyItem import ItemModifier
from Py4GWCoreLib.enums_src.Item_enums import Rarity
from Py4GWCoreLib.item_mods_src.decoded_modifier import DecodedModifier
from Py4GWCoreLib.item_mods_src.properties import InherentProperty, InscriptionProperty, ItemProperty, PrefixProperty, SuffixProperty
from typing import TypeVar, cast

T = TypeVar("T", bound=ItemProperty)

class ItemModifierParser:
    def __init__(self, runtime_modifiers: list[ItemModifier], rarity: Rarity | int = Rarity.Blue):
        self.modifiers: list[DecodedModifier] = []
        self.properties: list[ItemProperty] = []
        self.rarity: Rarity = Rarity(rarity) if isinstance(rarity, int) else rarity

        self._decode(runtime_modifiers)
        self._build_properties()

    def _decode(self, runtime_modifiers: list[ItemModifier]):        
        for mod in runtime_modifiers:
            decoded = DecodedModifier.from_runtime(mod)
            if decoded is not None:
                self.modifiers.append(decoded)

    def _build_properties(self):
        from Py4GWCoreLib.item_mods_src.upgrades import Inherent, _INHERENT_UPGRADES
        from Py4GWCoreLib.item_mods_src.upgrade_parser import get_property_factory
        handled_modifiers : list[DecodedModifier] = []    
            
        def _match_inherent_modifiers(inherent_type: type[Inherent], unhandled_modifiers: list[DecodedModifier]) -> list[DecodedModifier] | None:
            matched_modifiers: list[DecodedModifier] = []

            for prop_id in inherent_type.property_identifiers:
                match = next((mod for mod in unhandled_modifiers if mod.identifier == prop_id), None)
                if match is None:
                    return None

                matched_modifiers.append(match)

            return matched_modifiers
        
        for mod in self.modifiers:
            factory = get_property_factory().get(mod.identifier)
            if factory:
                prop = factory(mod, self.modifiers, self.rarity)
                    
                if prop:
                    if isinstance(prop, (PrefixProperty, SuffixProperty, InscriptionProperty)):
                        handled_modifiers.append(prop.modifier)
                        
                        if isinstance(prop, PrefixProperty) and (prefix := cast(PrefixProperty, prop)).upgrade:
                            for p in prefix.upgrade.properties.values():
                                if p and p not in handled_modifiers:
                                    handled_modifiers.append(p.modifier)
                        
                        if isinstance(prop, SuffixProperty) and (suffix := cast(SuffixProperty, prop)).upgrade:
                            for p in suffix.upgrade.properties.values():
                                if p and p not in handled_modifiers:
                                    handled_modifiers.append(p.modifier)
                        
                        if isinstance(prop, InscriptionProperty) and (inscription := cast(InscriptionProperty, prop)).upgrade:
                            for p in inscription.upgrade.properties.values():
                                if p and p not in handled_modifiers:
                                    handled_modifiers.append(p.modifier)
                    
                    
                    #only add if no property of that type already exists, since some modifiers have multiple entries with the same identifier but different args
                    # if not any(isinstance(p, type(prop)) and p.modifier.arg == prop.modifier.arg for p in self.properties):
                    self.properties.append(prop)
                else:
                    self.properties.append(ItemProperty(mod, rarity=self.rarity))
        
        unhandled_modifiers = [mod for mod in self.modifiers if mod not in handled_modifiers]
        inherent_types = sorted(_INHERENT_UPGRADES, key=lambda u: len(u.property_identifiers), reverse=True)
    
        for inherent_type in inherent_types:
            matched_modifiers = _match_inherent_modifiers(inherent_type, unhandled_modifiers)
            
            if matched_modifiers is None:
                continue
            
            upgrade = inherent_type.compose_from_modifiers(matched_modifiers[0], matched_modifiers, self.modifiers, self.rarity)
            if upgrade is not None:
                self.properties.append(InherentProperty(modifier=matched_modifiers[0], rarity=self.rarity, upgrade=upgrade))
                unhandled_modifiers = [mod for mod in unhandled_modifiers if mod not in matched_modifiers]
            
    def get_properties(self) -> list[ItemProperty]:
        return self.properties
