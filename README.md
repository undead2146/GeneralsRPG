# Adventure

In this RPG cog originally by locastan - TrustyJAID, Draper, and myself have crafted a fun idle game you can play with the members of your servers.

### >>> This branch is compatible with Red 3.5, and not 3.4.x <<<

If you need a Red 3.4 version of this cog, see [here](https://github.com/aikaterna/gobcog/tree/red3.4).


## Basic Usage

`[p]` in this readme represents your bot's command prefix. Whenever you see a command in this guide, you can receive more detailed help by using `[p]help` with the command name.

To start an adventure, use `[p]adventure` or `[p]a`. Reactions will appear underneath the text of the adventure randomly selected for your group. Use 🗡 to attack the monster, ✨ to use magic on the monster, 🗨 to talk with the monster, 🛐 to pray to the god Herbert (customizable). The more people helping the easier it is to defeat the monster and acquire its loot. 


## Hero/Heroclass

Classes can be chosen at level 10 by using `[p]heroclass`. Available classes are Tinkerer, Berserker, Wizard, Cleric, Ranger and Bard. A prestige class called Psychic is available at Rebirth level 20 (more on the rebirthing system below).  
  
Main Stats: Attack (ATT/ATK), Charisma/Diplomacy (CHA/DIPL), Intelligence (INT)  
Minor Stats: Dexterity (DEX), Luck (LUCK/LUK)  
  
While each class has a main stat that benefits them more than others, Dexterity and Luck benefit every class. Dexterity can lessen your repair bills after a failed adventure and help your hero get critical hits, while luck can benefit the outcome of special attacks, reduce cooldown times, augment critical strikes, affect loot chest outcomes, and reduce the price of items.  
  
**Tinkerers** can forge two different items into a device bound to their very soul.  
Special ability: Use the `[p]forge` command.  
* Forge together two items in your backpack to potentially make an incredibly powerful random item.  
Preferred stat: INT  
At 30 rebirths, Tinkerers can forge Ascended-level items.  
  
**Berserkers** have the option to rage and add big bonuses to attacks, but fumbles hurt.  
Use the `[p]rage` command when attacking in an adventure.  
* Causes a large amount of ATK-based/Physical-based damage.  
Preferred stat: ATK  
Rebirths provide not only a base bonus to attacks as Berserkers grow stronger, but they augment critical strike chance and attack value.  
  
**Clerics** can bless the entire group when praying.  
Use the `[p]bless` command when fighting in an adventure.  
* Bless your groups' damage by invoking your deity. The more people that are participating, the harder the deity smites their foes... if they choose to help.  
Preferred stat: INT  
Every 15 rebirths a Cleric recieves another +1 to their successful prayer damage multiplier.  
  
**Rangers** can gain a special pet, which can find items and give reward bonuses.  
Use the `[p]pet` command to try to catch a pet companion. Pet catching can be spammy, so `[p]pet` can be run in DMs.  
`[p]pet forage` sends a pet to search for items, and `[p]pet free` will free your companion in case you wish to try your hand at capturing something that brings in more gold and loot from fights.  
* Catch one of over 900 randomly-generated pets in search of the legendary beasts rumored to exist...  
Preferred stat: CHA for charming pet companions and enemies, or ATK for pure damage  
  
**Wizards** have the option to focus and add large bonuses to their magic, but their focus can sometimes go astray...  
Use the `[p]focus` command when attacking in an adventure.  
* Causes a large amount of Int-based/Magic-based damage.  
Preferred stat: INT  
  
**Bards** can perform to aid their comrades in diplomacy.  
Use the `[p]music` command when being diplomatic in an adventure.  
* Buffs other Charisma-using players when attacking.  
Preferred stat: CHA  
# Generals: Zero Hour — Adventure (converted)

This repository contains the Adventure cog converted and re-themed for "Generals: Zero Hour". The core play loop and many Adventure commands were retained, but several command aliases and reward flows are overhauled to support a Generals-themed economy (Supplies, Command Points, blueprints, and collectors).

Compatibility: the conversion targets the Red 3.5 command runtime. If you need legacy Adventure behavior, check older branches or the upstream project.


## Quick primer

In this README `[p]` stands for your bot prefix. Many existing Adventure commands are still available (`[p]adventure`, `[p]loot`, `[p]backpack`), but new Generals-focused aliases are provided as thin wrappers that map into the Adventure engine.

Primary aliases you will use:

- `[p]skirmish` — short patrol (quick adventure)
- `[p]operation` — longer, higher-reward adventure
# Generals: Zero Hour — GeneralsRPG

GeneralsRPG is a Generals-themed conversion of the original Adventure cog. It adapts the idle-RPG loop to a Zero Hour style economy and command set while reusing the Adventure engine for combat and persistence.

This README explains the high-level design, primary commands, economy, factions, admin and developer notes, and where to find design documents and tests in the repository.

Compatibility
- Targets the Red 3.5 command runtime. Local tests may need the repository root on `PYTHONPATH` so local `redbot` stubs resolve.


## Quick start (players)

In this README `[p]` denotes your bot prefix. Use `[p]help <command>` for command-specific help.

Primary player commands (aliases mapped to Adventure handlers):

- `[p]skirmish` — short patrol (fast cooldown, Supplies + XP)
- `[p]operation` — long operation (higher rewards, chance for Command Points and blueprints)
- `[p]drill` — training / skill (short cooldown)
- `[p]gather` — collect Supplies and materials
- `[p]salvage` — salvage wrecks for parts and scrap
- `[p]blackmarket` — risky, high-reward action (chance to lose items)
- `[p]stronghold` / `[p]general` — long-instance / miniboss (shared long cooldown)
- `[p]blueprints` — list available blueprints in your backpack
- `[p]build <name>` — craft using blueprints, parts and supplies
- `[p]backpack` / `[p]equip` / `[p]unequip` — inventory management
- `[p]loot` — open loot chests

Notes:
- Existing Adventure commands like `[p]adventure` and `[p]a` remain available and are integrated where appropriate.


## Factions, units & flavor

The conversion introduces Zero Hour flavor: factions, builders/collectors, power mechanics, and super-weapon concepts are represented through theme data and rewards. See `.vscode/PRD-GeneralsRPG.md` and `docs/GENERALS_COMMANDS.md` for the full design.


## Economy & rewards

- Supplies — primary resource for crafting and building.
- Command Points (CP) — rare currency from operations/strongholds for high-tier unlocks.
- Parts / Materials — consumed when crafting/upgrading.
- Blueprints — items used by `[p]build` to craft unique gear or units.

Reward distribution is handled by `adventure/loot.py` and uses per-theme JSON files in `adventure/data/zero_hour/` when the `zero_hour` theme is active.


## Admin / owner

- Change theme: `adventureset theme zero_hour`.
- Theme files: `adventure/data/zero_hour/` (monsters, rewards, recipes, gather tables, etc.).
- Tweak cooldowns and economy keys via `adventureset` configuration (look for `economy.*` and `cooldowns.*` in the code).


## Developer & testing notes

Required test policy: add pytest tests for any new feature or behaviour change (see `.github/instructions` and `.vscode/checklist.md`). Tests should be deterministic and placed under `tests/`.

Run tests locally (PowerShell):

```powershell
$env:PYTHONPATH = "${PWD}" ; pytest -q --maxfail=1
```

Run a focused unit test that avoids full Red imports:

```powershell
python -m pytest tests/unit/test_do_work_rewardengine.py -q
```

Quick syntax check for modified Python files:

```powershell
python -m py_compile adventure/adventure.py adventure/loot.py adventure/backpack.py
```

If pytest fails during collection with `ModuleNotFoundError: redbot`, ensure the repo is on `PYTHONPATH` (above) or run targeted tests that mock out Red objects.


## Where to find more docs

- Command & alias mapping: `docs/Commands.md` and `docs/GENERALS_COMMANDS.md`.
- Product requirements & design: `.vscode/PRD-GeneralsRPG.md`.
- Conversion checklist & CI notes: `.vscode/checklist.md`.


## Contributing

- Keep wrappers thin: delegate to Adventure handlers where possible.
- Add theme JSONs under `adventure/data/zero_hour/` and tests under `tests/`.
- Update `.vscode/agent_rules.md` and run `py_compile` for modified Python files when opening a PR (see `.github/instructions/instruction.instructions.md`).


## Short summary

This repository contains a Generals-themed conversion of the Adventure cog. The README, docs, and theme JSONs should be your first reference when editing or extending the Generals features. Run tests locally with `PYTHONPATH` set and follow the repository checklist before opening PRs.

## Examples

Quick command examples (these are illustrative — exact wording depends on your bot prefix and localization):

- Start a short patrol and show result summary:

	[p]skirmish

	-> "Patrol complete: +120 Supplies, +50 XP. Loot: 1x Scrap Part."

- Run a long operation that can award Command Points and blueprints:

	[p]operation

	-> "Operation successful: +600 Supplies, +2 CP. Found blueprint: 'Tank Frame Fragment'."

- Gather resources:

	[p]gather

	-> "+40 Supplies, +1 Material"

- Craft from a blueprint (consumes blueprint, parts and supplies):

	[p]build tank

	-> "Built: Light Tank (consumed: 5x Parts, 200 Supplies, 1x Tank Blueprint)"

These examples are simplified. Actual results include more detailed battle or loot summaries and may show item comparators, equip suggestions, or join/participation info when run in a shared channel.

