__**Draft board**__
**API**
**`Merchant``**
`GetSalvageKitsToBuy()`
```return the amount of missing salvage kits```

`GetIdentificationKitsToBuy`
```return the amount of missing identification kits```

`GetLockpicksToBuy`
```return the amount of missing lockpicks```

`GetSalvageUses()`
```return the sum of uses left on all salvage kits```

`GetIdentificationKitUses()`
```return the sum of uses left on all identification kits```

`GetLockpicks()`
```return the sum of lockpicks left in inventory```

`GetItemsToSell()`
```return the amount of items that should be sold```

`GetItemsToBuy()`
```return a list of tuples of model_ids and amount we need to buy from a merchant```

**`Inventory`**
`ProcessInventory()`
```return bool while processing, false while not```