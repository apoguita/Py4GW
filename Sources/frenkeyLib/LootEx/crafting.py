from datetime import datetime
import math
from typing import Generator, Callable, List

from Py4GW import Console
from PyItem import PyItem

from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Item import Bag, Item
from Py4GWCoreLib.Merchant import Trading
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.Item_enums import Bags, ItemType
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from Sources.frenkeyLib.LootEx.enum import MAX_CHARACTER_GOLD, ActionState
from Sources.frenkeyLib.LootEx.cache import Cached_Item
from Sources.frenkeyLib.LootEx.models import CraftingRecipe, Ingredient
from Sources.frenkeyLib.LootEx import utility

CONSET_RECIPES = {
    ModelID.Essence_Of_Celerity,
    ModelID.Armor_Of_Salvation,
    ModelID.Grail_Of_Might,
}

# ---------------------------------------------------------------------
# Generic coroutine wrapper (identical behavior to TraderCoroutine)
# ---------------------------------------------------------------------

class CraftingCoroutine:
    def __init__(self, generator_fn: Callable[[], Generator]):
        self.generator_fn = generator_fn
        self.generator = None
        self.state = ActionState.Pending
        self.started_at = datetime.min

    def step(self) -> ActionState:
        if self.state == ActionState.Pending:
            self.generator = self.generator_fn()
            self.state = ActionState.Running
            self.started_at = datetime.now()

        try:
            if self.generator:
                next(self.generator)
                return self.state
            else:
                self.state = ActionState.Completed
                return self.state

        except StopIteration:
            self.state = ActionState.Completed
            return self.state

        except Exception as e:
            ConsoleLog(
                "LootEx",
                f"Crafting coroutine error: {e}",
                Console.MessageType.Error
            )
            self.state = ActionState.Timeout
            return self.state


# ---------------------------------------------------------------------
# CraftingAction
# ---------------------------------------------------------------------

class CraftingAction:
    def __init__(
        self,
        recipe: CraftingRecipe,
        *,
        max_amount: int = -1,
        include_storage: bool = False,
        include_material_storage: bool = False,
        conset_baseline: int = 0,
    ):
        self.recipe = recipe
        recipe.get_item_data()
        
        self.max_amount = max_amount
        self.include_storage = include_storage
        self.include_material_storage = include_material_storage
        self.conset_baseline = conset_baseline

        self.crafted_count = 0
        self._start_time: datetime | None = None
        self.coroutine: CraftingCoroutine | None = None

    # -----------------------------------------------------------------
    # Entry point
    # -----------------------------------------------------------------

    def run(self) -> CraftingCoroutine:
        return CraftingCoroutine(self._gen_main)

    # -----------------------------------------------------------------
    # Main generator
    # -----------------------------------------------------------------

    def _gen_main(self) -> Generator:
        self._start_time = datetime.now()

        self.recipe.get_item_data()
        item = self.recipe.item

        if not item:
            ConsoleLog(
                "LootEx",
                f"Crafting aborted: recipe item not resolved (model_id={self.recipe.model_id})",
                Console.MessageType.Warning
            )
            return

        ConsoleLog(
            "LootEx",
            f"Starting CraftingAction for '{item.name}'",
            Console.MessageType.Info
        )
        
        yield from self._withdraw_required_ingredients()

        while self._can_continue():
            yield from self._check_preconditions()
            yield from self._execute_craft()
            yield from self._confirm_craft()

        ConsoleLog(
            "LootEx",
            f"CraftingAction completed for '{item.name}'. Crafted {self.crafted_count}x.",
            Console.MessageType.Info
        )        

    # -----------------------------------------------------------------
    # Conditions
    # -----------------------------------------------------------------

    def _can_continue(self) -> bool:
        if self.max_amount >= 0 and self.crafted_count >= self.max_amount:
            return False

        return True

    # -----------------------------------------------------------------
    # Preconditions
    # -----------------------------------------------------------------
    def _is_available(self) -> bool:
        offered_items = Trading.Crafter.GetOfferedItems()
        offered_item = next(
            (
                i for i in offered_items
                if Item.GetModelID(i) == self.recipe.model_id
            ),
            None
        )
        
        return offered_item is not None

    def _check_preconditions(self) -> Generator:
        item = self.recipe.item
        if not item:
            ConsoleLog(
                "LootEx",
                f"Cannot check preconditions: recipe item not resolved (model_id={self.recipe.model_id})",
                Console.MessageType.Warning
            )
            raise StopIteration

        if Inventory.GetFreeSlotCount() <= 0:
            ConsoleLog(
                "LootEx",
                f"Cannot craft '{item.name}': no free inventory slots.",
                Console.MessageType.Info
            )
            raise StopIteration

        if Inventory.GetGoldOnCharacter() < self.recipe.price:
            ConsoleLog(
                "LootEx",
                f"Cannot craft '{item.name}': insufficient gold.",
                Console.MessageType.Info
            )
            raise StopIteration

        for ingredient in self.recipe.ingredients:
            if not self._has_ingredient(ingredient):
                ConsoleLog(
                    "LootEx",
                    f"Cannot craft '{item.name}': missing ingredient "
                    f"{ingredient.item.name if ingredient.item else ingredient.model_id}",
                    Console.MessageType.Info
                )
                raise StopIteration

        yield

    # -----------------------------------------------------------------
    # Ingredient resolution
    # -----------------------------------------------------------------

    def _has_ingredient(self, ingredient: Ingredient) -> bool:
        player_skillpoints = Player.GetSkillPointData()[0] if self.recipe.skill_points > 0 else 0
        
        inv_amount = Inventory.GetModelCount(ingredient.model_id)
        storage_amount = (
            Inventory.GetModelCountInStorage(ingredient.model_id)
            if self.include_storage else 0
        )
        material_storage_amount = (
            Inventory.GetModelCountInMaterialStorage(ingredient.model_id)
            if self.include_material_storage else 0
        )

        return self.recipe.skill_points <= player_skillpoints and (inv_amount + storage_amount + material_storage_amount) >= ingredient.amount

    def _resolve_inventory_item(self, ingredient: Ingredient) -> Cached_Item | None:        
        inventory_array, _ = utility.Util.GetZeroFilledBags(start_bag = Bag.Backpack, end_bag = Bag.Bag_2)
        
        item_id = next(
            (
                i for i in inventory_array
                if Item.GetModelID(i) == ingredient.model_id and Item.Properties.GetQuantity(i) >= ingredient.amount
            ),
            None
        )
        
        return Cached_Item(item_id) if item_id else None

    def _withdraw_model_id_from_storage(self, model_id: int, amount: int):
        """
        Withdraw exactly `amount` items of model_id into inventory.
        Never over-withdraws.
        """
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        remaining = amount
        if remaining <= 0:
            return

        def withdraw_from(bag_start, bag_end):
            nonlocal remaining
            storage, _ = utility.Util.GetZeroFilledBags(bag_start, bag_end)
            for item_id in storage:
                if remaining <= 0:
                    return
                if Item.GetModelID(item_id) != model_id:
                    continue

                qty = Item.Properties.GetQuantity(item_id)
                if qty <= 0:
                    continue

                to_move = min(qty, remaining)
                Inventory.WithdrawItemFromStorage(item_id, to_move)
                remaining -= to_move
                yield

        if self.include_storage:
            yield from withdraw_from(
                Bag.Storage_1,
                Bag(settings.max_xunlai_storage.value),
            )

        if self.include_material_storage and remaining > 0:
            yield from withdraw_from(
                Bag.Material_Storage,
                Bag.Material_Storage,
            )
                        
    def _withdraw_required_ingredients(self):
            """
            Ensures all required ingredients for the entire planned crafting amount
            are present in inventory. Stack-aware (MAX_STACK_SIZE = 250).
            """

            if not self.include_storage and not self.include_material_storage:
                return

            ## Withdraw Gold if needed
            gold_needed = self.recipe.price * self.max_amount
            gold_on_character = Inventory.GetGoldOnCharacter()
            gold_in_storage = Inventory.GetGoldInStorage()
            
            if gold_in_storage > 0 and gold_on_character < gold_needed:
                gold_to_withdraw = min(gold_in_storage, gold_needed - gold_on_character)
                ConsoleLog(
                    "LootEx",
                    f"Withdrawing {utility.Util.format_currency(gold_to_withdraw)} gold from storage.",
                    Console.MessageType.Info
                )
                Inventory.WithdrawGold(gold_to_withdraw)
                yield

            for ingredient in self.recipe.ingredients:
                total_needed = ingredient.amount * self.max_amount
                in_inventory = Inventory.GetModelCount(ingredient.model_id)

                if in_inventory >= total_needed:
                    continue

                missing = total_needed - in_inventory
                available_storage = Inventory.GetModelCountInStorage(ingredient.model_id) if self.include_storage else 0
                available_storage += Inventory.GetModelCountInMaterialStorage(ingredient.model_id) if self.include_material_storage else 0

                if available_storage <= 0:
                    ConsoleLog(
                        "LootEx",
                        f"Missing ingredient '{ingredient.item.name if ingredient.item else ingredient.model_id}' "
                        f"({missing} needed, none in storage).",
                        Console.MessageType.Warning
                    )
                    raise StopIteration

                ConsoleLog(
                    "LootEx",
                    f"Withdrawing {missing}x '{ingredient.item.name if ingredient.item else ingredient.model_id}' from storage.",
                    Console.MessageType.Info
                )

                yield from self._withdraw_model_id_from_storage(
                    ingredient.model_id,
                    missing
                )
            
            yield Routines.Yield.wait(500)
                
    # -----------------------------------------------------------------
    # Execute craft
    # -----------------------------------------------------------------

    def _execute_craft(self) -> Generator:
        item = self.recipe.item
        if not item:
            ConsoleLog(
                "LootEx",
                f"Cannot execute craft: recipe item not resolved (model_id={self.recipe.model_id})",
                Console.MessageType.Warning
            )
            raise StopIteration

        ingredients_ids: List[int] = []
        ingredients_amounts: List[int] = []

        for ingredient in self.recipe.ingredients:
            inv_item = self._resolve_inventory_item(ingredient)
            if not inv_item:
                raise StopIteration

            ingredients_ids.append(inv_item.id)
            ingredients_amounts.append(ingredient.amount)

        offered_items = Trading.Crafter.GetOfferedItems()
        offered_item = next(
            (
                i for i in offered_items
                if Item.GetModelID(i) == self.recipe.model_id
            ),
            None
        )

        if not offered_item:
            ConsoleLog(
                "LootEx",
                f"Crafter does not offer item '{item.name}'.",
                Console.MessageType.Warning
            )
            raise StopIteration

        ConsoleLog(
            "LootEx",
            f"Crafting '{item.name}' for {utility.Util.format_currency(self.recipe.price)}",
            Console.MessageType.Info
        )

        Trading.Crafter.CraftItem(
            offered_item,
            self.recipe.price,
            ingredients_ids,
            ingredients_amounts
        )

        self._craft_start_time = datetime.now()
        yield

    # -----------------------------------------------------------------
    # Confirm craft
    # -----------------------------------------------------------------

    def _confirm_craft(self) -> Generator:
        start = datetime.now()

        while True:
            if (datetime.now() - start).total_seconds() > 1.5:
                ConsoleLog(
                    "LootEx",
                    "Craft confirmation timeout.",
                    Console.MessageType.Warning
                )
                return

            # simple heuristic: gold decreased
            if Inventory.GetGoldOnCharacter() < MAX_CHARACTER_GOLD:
                self.crafted_count += 1
                return

            yield

def plan_even_consets(
    *,
    iron: int,
    dust: int,
    feathers: int,
    cur_essence: int,
    cur_armor: int,
    cur_grail: int,
):
    COST = 50

    plan = {
        ModelID.Essence_Of_Celerity: 0,
        ModelID.Armor_Of_Salvation: 0,
        ModelID.Grail_Of_Might: 0,
    }

    def can_craft_essence():
        # return feathers >= COST and dust >= COST
        return dust >= COST

    def can_craft_armor():
        return iron >= COST

    def can_craft_grail():
        return iron >= COST and dust >= COST

    while True:
        counts = {
            ModelID.Essence_Of_Celerity: cur_essence + plan[ModelID.Essence_Of_Celerity],
            ModelID.Armor_Of_Salvation: cur_armor + plan[ModelID.Armor_Of_Salvation],
            ModelID.Grail_Of_Might: cur_grail + plan[ModelID.Grail_Of_Might],
        }

        lowest = min(counts.values())

        crafted = False

        # Try to raise the lowest consets
        for conset in sorted(counts, key=lambda k: counts[k]):
            if counts[conset] > lowest:
                continue

            if conset == ModelID.Essence_Of_Celerity and can_craft_essence():
                feathers -= COST
                dust -= COST
                plan[ModelID.Essence_Of_Celerity] += 1
                crafted = True
                break

            if conset == ModelID.Armor_Of_Salvation and can_craft_armor():
                iron -= COST
                plan[ModelID.Armor_Of_Salvation] += 1
                crafted = True
                break

            if conset == ModelID.Grail_Of_Might and can_craft_grail():
                # SAFETY CHECK:
                # after crafting Grail, can we still catch up Armor and Essence?
                if (iron - COST) >= COST and (dust - COST) >= COST:
                    iron -= COST
                    dust -= COST
                    plan[ModelID.Grail_Of_Might] += 1
                    crafted = True
                    break

        if not crafted:
            break

    return plan

def mat(model_id: int) -> int:
    from Sources.frenkeyLib.LootEx.settings import Settings
    
    settings = Settings()
    if not settings:
        return 0

    return (
        Inventory.GetModelCount(model_id)
        + Inventory.GetModelCountInStorage(model_id)
        + Inventory.GetModelCountInMaterialStorage(model_id)
        if settings.auto_withdraw_materials else
        Inventory.GetModelCount(model_id)
    )

def get_missing_materials_to_evenout() -> list[Ingredient]:
    """
    Returns a dict of model_id -> missing amount to even out consets.
    """
    from Sources.frenkeyLib.LootEx.settings import Settings
    from Sources.frenkeyLib.LootEx.data import Data

    data = Data()
    if not data or not data.Recipes:
        return []

    settings = Settings()
    if not settings:
        return []
    
    # ------------------------------------------------------------
    # Current conset counts
    # ------------------------------------------------------------
    cur_essence = (
        Inventory.GetModelCount(ModelID.Essence_Of_Celerity)
        + Inventory.GetModelCountInStorage(ModelID.Essence_Of_Celerity)
    )
    cur_armor = (
        Inventory.GetModelCount(ModelID.Armor_Of_Salvation)
        + Inventory.GetModelCountInStorage(ModelID.Armor_Of_Salvation)
    )
    cur_grail = (
        Inventory.GetModelCount(ModelID.Grail_Of_Might)
        + Inventory.GetModelCountInStorage(ModelID.Grail_Of_Might)
    )

    # ------------------------------------------------------------
    # Available materials
    # ------------------------------------------------------------

    iron = mat(ModelID.Iron_Ingot)
    dust = mat(ModelID.Pile_Of_Glittering_Dust)
    feathers = mat(ModelID.Feather)

    # ------------------------------------------------------------
    # Run the EVEN CONSET PLANNER
    # ------------------------------------------------------------
    conset_plan = plan_even_consets(
        iron=iron,
        dust=dust,
        feathers=feathers,
        cur_essence=cur_essence,
        cur_armor=cur_armor,
        cur_grail=cur_grail,
    )

    ingredients: dict[int, Ingredient] = {}
    
    for con, amount in conset_plan.items():
        if amount > 0:
            recipe = next((r for r in data.Recipes if r.item_type == ItemType.Usable and r.model_id == con), None)
            if not recipe:
                continue

            for ingredient in recipe.ingredients:
                if ingredient.model_id in ingredients:
                    ingredients[ingredient.model_id].amount += ingredient.amount * amount
                else:
                    ingredients[ingredient.model_id] = Ingredient(
                        item_type=ingredient.item_type,
                        model_id=ingredient.model_id,
                        amount=ingredient.amount * amount,
                        rarity=ingredient.rarity
                    )

    return list(ingredients.values())
    
def BuildCraftingQueueFromCrafter() -> list[CraftingAction]:
    """
    Builds the crafting queue by inspecting the current crafter and
    planning consets evenly using plan_even_consets().
    Pure planning phase – no inventory mutations.
    """
    from Sources.frenkeyLib.LootEx.settings import Settings
    from Sources.frenkeyLib.LootEx.data import Data

    data = Data()
    if not data or not data.Recipes:
        return []

    settings = Settings()
    if not settings:
        return []

    # ------------------------------------------------------------
    # Current conset counts
    # ------------------------------------------------------------
    cur_essence = (
        Inventory.GetModelCount(ModelID.Essence_Of_Celerity)
        + Inventory.GetModelCountInStorage(ModelID.Essence_Of_Celerity)
    )
    cur_armor = (
        Inventory.GetModelCount(ModelID.Armor_Of_Salvation)
        + Inventory.GetModelCountInStorage(ModelID.Armor_Of_Salvation)
    )
    cur_grail = (
        Inventory.GetModelCount(ModelID.Grail_Of_Might)
        + Inventory.GetModelCountInStorage(ModelID.Grail_Of_Might)
    )

    # ------------------------------------------------------------
    # Available materials
    # ------------------------------------------------------------

    iron = mat(ModelID.Iron_Ingot)
    dust = mat(ModelID.Pile_Of_Glittering_Dust)
    feathers = mat(ModelID.Feather)

    # ------------------------------------------------------------
    # Run the EVEN CONSET PLANNER
    # ------------------------------------------------------------
    conset_plan = plan_even_consets(
        iron=iron,
        dust=dust,
        feathers=feathers,
        cur_essence=cur_essence,
        cur_armor=cur_armor,
        cur_grail=cur_grail,
    )

    if not conset_plan:
        return []

    # ------------------------------------------------------------
    # Build CraftingActions from the plan
    # ------------------------------------------------------------
    queue: list[CraftingAction] = []

    offered_items = Trading.Merchant.GetOfferedItems() + Trading.Crafter.GetOfferedItems() + Trading.Trader.GetOfferedItems()

    for recipe in data.Recipes + data.Conversions:        
        recipe.get_item_data()
        item = recipe.item
        if not item:
            continue
    
        enabled = settings.conversions.get(
            item.get_name(ServerLanguage.English), False
        )
        
        if not enabled:
            continue

        if not any(
            Item.GetModelID(i) == recipe.model_id
            for i in offered_items
        ):
            continue

        max_by_ingredients = float("inf")        
                
        for ingredient in recipe.ingredients:
            inv_amount = Inventory.GetModelCount(ingredient.model_id)
            storage_amount = (
                Inventory.GetModelCountInStorage(ingredient.model_id)
                if settings.auto_withdraw_materials else 0
            )
            material_storage_amount = (
                Inventory.GetModelCountInMaterialStorage(ingredient.model_id)
                if settings.auto_withdraw_materials else 0
            )

            total = inv_amount + storage_amount + material_storage_amount
            possible = total // ingredient.amount
            max_by_ingredients = min(max_by_ingredients, possible)

        if max_by_ingredients <= 0:
            continue

        gold = Inventory.GetGoldOnCharacter()
        max_by_gold = gold // recipe.price if recipe.price > 0 else max_by_ingredients
        craftable_amount = math.floor(min(max_by_ingredients, max_by_gold))

        if craftable_amount <= 0:
            continue
            
        if recipe.model_id in CONSET_RECIPES and settings.auto_even_consets:
            planned = math.floor(min(
                conset_plan.get(ModelID(recipe.model_id), 0),
                craftable_amount
            ))
            
            if planned <= 0:
                continue

            queue.append(
                CraftingAction(
                    recipe=recipe,
                    max_amount=planned,
                    include_storage=settings.auto_withdraw_materials,
                    include_material_storage=settings.auto_withdraw_materials,
                    conset_baseline={
                        ModelID.Essence_Of_Celerity: cur_essence,
                        ModelID.Armor_Of_Salvation: cur_armor,
                        ModelID.Grail_Of_Might: cur_grail,
                    }[ModelID(recipe.model_id)],
                )
            )
            
        else:
            queue.append(
                CraftingAction(
                    recipe=recipe,
                    max_amount=craftable_amount,
                    include_storage=settings.auto_withdraw_materials,
                    include_material_storage=settings.auto_withdraw_materials,
                )
            )

        ConsoleLog(
            "LootEx",
            f"Queued crafting of {craftable_amount}x '{item.name}'.",
            Console.MessageType.Info
        )

    return queue