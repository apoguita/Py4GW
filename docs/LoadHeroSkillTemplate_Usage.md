# Loading Hero Skill Templates - Usage Guide

## Overview
The `LoadHeroSkillTemplate` function allows you to load a skill build (template code) onto a hero in your party.

## IMPORTANT: Party Position vs Hero ID

The function expects a **1-based party position** (1 = first hero, 2 = second hero, etc.), **NOT** a Hero ID (like Koss=6).

### What is Party Position?
- **Party Position 1** = The first hero in your party (could be any hero)
- **Party Position 2** = The second hero in your party
- **Party Position 3** = The third hero in your party
- etc.

### What is Hero ID?
- **Hero ID** is a unique identifier for each specific hero:
  - Norgu = 1
  - Koss = 6
  - Tahlkora = 3
  - etc. (see PyParty.HeroType)

## Usage Methods

### Method 1: Using Party Position (Default)
Use this when you want to load a template on "the first hero" or "the second hero" in your party, regardless of which specific hero it is.

```python
from Py4GWCoreLib import SkillBar

# Load a template on the first hero in your party
result = SkillBar.LoadHeroSkillTemplate(1, "OQATEjpUjIACVAAAAAAAAAA")

# Load a template on the second hero in your party
result = SkillBar.LoadHeroSkillTemplate(2, "OQASEDqEC1vcNABWAAAA")
```

### Method 2: Using Hero ID (Recommended for specific heroes)
Use this when you want to load a template on a **specific hero** (e.g., always load on Koss).

```python
from Py4GWCoreLib import SkillBar
from PyParty import HeroType

# Load a template on Koss (wherever Koss is in your party)
result = SkillBar.LoadHeroSkillTemplateByHeroID(HeroType.Koss, "OQATEjpUjIACVAAAAAAAAAA")

# Load a template on Tahlkora
result = SkillBar.LoadHeroSkillTemplateByHeroID(HeroType.Tahlkora, "OQASEDqEC1vcNABWAAAA")
```

### Method 3: Using Hero Name (Most User-Friendly)
Use this when you want to specify the hero by name.

```python
from Py4GWCoreLib import SkillBar

# Load a template on Koss by name
result = SkillBar.LoadHeroSkillTemplateByName("Koss", "OQATEjpUjIACVAAAAAAAAAA")

# Load a template on Tahlkora by name
result = SkillBar.LoadHeroSkillTemplateByName("Tahlkora", "OQASEDqEC1vcNABWAAAA")
```

## Common Mistakes

### ❌ WRONG: Using Hero ID with LoadHeroSkillTemplate
```python
from PyParty import HeroType

# This will try to load the template on the 6th hero in your party, NOT on Koss!
# (Koss has hero_id=6, but that's not the same as party position 6)
SkillBar.LoadHeroSkillTemplate(HeroType.Koss, "template")  # WRONG!
```

### ✅ CORRECT: Use the right method for your intent
```python
from PyParty import HeroType

# If you want to load on Koss specifically:
SkillBar.LoadHeroSkillTemplateByHeroID(HeroType.Koss, "template")  # CORRECT

# OR
SkillBar.LoadHeroSkillTemplateByName("Koss", "template")  # CORRECT

# If you want to load on "the first hero" (whoever that is):
SkillBar.LoadHeroSkillTemplate(1, "template")  # CORRECT
```

## Return Values
All methods return `True` if successful, `False` otherwise:

```python
result = SkillBar.LoadHeroSkillTemplateByName("Koss", "OQATEjpUjIACVAAAAAAAAAA")
if not result:
    print("Failed - Koss might not be in your party or template is invalid")
```

## Hero ID Reference
Common Hero IDs from PyParty.HeroType:
- Norgu = 1
- Goren = 2  
- Tahlkora = 3
- Master Of Whispers = 4
- Acolyte Jin = 5
- Koss = 6
- Dunkoro = 7
- Acolyte Sousuke = 8
- Melonni = 9
- Zhed Shadowhoof = 10
- General Morgahn = 11
- Magrid The Sly = 12
- Zenmai = 13
- Olias = 14
- Razah = 15
- MOX = 16
- Keiran Thackeray = 17
- Jora = 18
- Pyre Fierceshot = 19
- Anton = 20
- Livia = 21
- Hayda = 22
- Kahmu = 23
- Gwen = 24
- Xandra = 25
- Vekk = 26
- Ogden = 27
- Mercenary Heroes = 28-35
- Miku = 36
- Zei Ri = 37

## Troubleshooting

**Error: "Failed to load skill template on hero at party position X"**
- The hero doesn't exist at that party position (you might only have 2 heroes but tried position 3)
- The template code is invalid

**Error: "Hero 'Koss' (ID: 6) is not in your party"**
- The specified hero is not in your current party
- Add the hero to your party first

**Why is my template not loading?**
1. Make sure you're using the correct method for your intent (party position vs hero ID)
2. Verify the hero is in your party
3. Check that the template code is valid
4. Ensure you have the skills unlocked
