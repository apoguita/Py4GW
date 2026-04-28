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
        from Py4GWCoreLib.item_mods_src.upgrades import _INHERENT_UPGRADES
        from Py4GWCoreLib.item_mods_src.upgrade_parser import get_property_factory
        handled_modifiers : list[DecodedModifier] = []    
        
        try:
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
                else:
                    self.properties.append(ItemProperty(mod, rarity=self.rarity))
            
            unhandled_modifiers = [mod for mod in self.modifiers if mod not in handled_modifiers]
            inherent_types = sorted(_INHERENT_UPGRADES, key=lambda u: len(u.upgrade_info), reverse=True)
        
            for inherent_type in inherent_types:
                matched_modifiers = inherent_type._match_property_modifiers(unhandled_modifiers)

                if matched_modifiers is None:
                    continue
                
                try:
                    matched_property_modifiers = [prop_mod for _, prop_mod in matched_modifiers]
                    if not matched_property_modifiers:
                        continue

                    upgrade = inherent_type.compose_from_modifiers(matched_property_modifiers[0], unhandled_modifiers, self.modifiers, self.rarity)
                    if upgrade is not None:
                        self.properties.append(InherentProperty(modifier=matched_property_modifiers[0], rarity=self.rarity, upgrade=upgrade))
                        unhandled_modifiers = [mod for mod in unhandled_modifiers if mod not in matched_property_modifiers]
                        
                except Exception as e:
                    print(f"Error composing inherent upgrade {inherent_type.__name__}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error building properties: {e}")
            
    def get_properties(self) -> list[ItemProperty]:
        return self.properties
