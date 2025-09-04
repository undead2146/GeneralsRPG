# Generals: Zero Hour  Command Reference

This file is a concise, actionable command specification extracted from the PRD (`.vscode/PRD-GeneralsRPG.md`). Use it as the single source-of-truth for command names, aliases, cooldowns, primary rewards, and notes for implementation in the Adventure cog.

## Core commands

- `[p]skirmish`
  - Alias for short adventure / hunt. Cooldown: 60s. Rewards: Supplies, parts, chance for Supply Crates.
  - Implementation: thin wrapper that calls the existing `adventure`/`_adventure` handler with short difficulty.

- `[p]operation`
  - Alias for long adventure / operation. Cooldown: 1h. Rewards: Supplies, Command Points (CP), rare blueprints.
  - Implementation: wrapper that calls `adventure`/`_adventure` with long difficulty.

- `[p]drill`
  - Alias for training/skill. Cooldown: 15m. Rewards: XP, chance to recruit specialist unit.
  - Implementation: forward to existing `skill` handler.

- `[p]gather`
  - Resource gather (5m). Rewards: Supplies, materials.
  - Implementation: wrapper to `loot`/`backpack` resource functions.

- `[p]salvage`
  - Salvage destroyed vehicles for parts (5m). Rewards: unit parts, scrap.
  - Implementation: wrapper to `backpack` or `loot` handler with salvage item table.

- `[p]blackmarket`
  - Risky smuggling (5m). Rewards: high-risk resources, chance to lose items.
  - Implementation: special-case wrapper that may consult player reputation or probability tables.

- `[p]stronghold`
  - Long instance (12h). Rewards: rare tech, promotions.
  - Implementation: either call `adventure` with a long preset or add a dedicated handler that reuses `_simple` logic.

- `[p]general`
  - Miniboss / General encounter (12h shared with stronghold). Rewards: large XP, rare doctrine unlocks.

- `[p]blueprints`
  - Show available buildable items/tech.

- `[p]build <unit>`
  - Craft unit/upgrades using parts and supplies.

- `[p]duel @user`
  - PvP skirmish. Cooldown: 2h.

- `[p]warzone`
  - FFA/event (daily).

Status: The core Generals command wrappers (`skirmish`, `operation`, `drill`, `gather`, `salvage`, `blackmarket`, `stronghold`, `general`, `blueprints`, `build`, `duel`, `warzone`) have been implemented as thin delegates (mixin in `adventure/wrappers.py`) and mixed into the Adventure cog. Reward mapping for gather/salvage/blackmarket is implemented in `adventure/loot.py` to produce Supplies and Command Points when theme drops indicate them. Theme JSONs for `zero_hour` (including `gather.json`, `salvage.json`, `blackmarket.json`, `rewards.json`, `recipes.json`) were added. Full pytest collection may still require local redbot stubs (see `.vscode/checklist.md`).

## Action mapping (in-adventure)

The Adventure cog uses actions like `fight`, `magic`, `talk`, `pray`, `run`. Map them to Generals semantics:

- fight -> fire (direct weapon attack)
- magic -> airstrike / special weapon (tech)
- talk -> negotiate / diplomacy
- pray -> repair / engineer (support)
- run -> retreat / maneuver

Implementation note: preserve the internal action-token semantics (to avoid deep engine changes). Translate flavor text and map special effects where needed.

## Cooldowns & shared cooldown groups

- Short actions (skirmish, gather, salvage, blackmarket): 5m or 1m depending on command. Make cooldowns configurable in `adventureset`.
- Long actions (operation, stronghold, general): 12h/1h groupings; share cooldown where appropriate.

## Economy: currencies & rewards

- Supplies: primary gatherable currency (replaces some coin flows).
- Command Points (CP): rare currency from operations/stronghold.
- Parts/materials: crafting inputs for `build` and blueprint unlocks.

Implementation note: add configuration keys under `adventureset` global config (e.g., `economy.supplies_enabled`, `economy.cp_enabled`) and update reward flows in `loot.py`/`economy.py` to optionally grant Supplies/CP instead of coins.

## Wrapper implementation checklist

1. Add thin wrapper commands in `adventure/adventure.py` for: `skirmish`, `operation`, `drill`, `gather`, `salvage`, `blackmarket`, `stronghold`, `general`.
2. Each wrapper should call existing handlers where possible (`_adventure`, `skill`, `loot`, `backpack`) to reuse cooldowns, reward math, and persistence.
3. Add localized messages to `locales/messages.pot` for new command names/flavor.
4. Add or extend `adventure/data/zero_hour/` JSON tables for `salvage`/`gather` drops and any new monsters/units.
5. Add unit tests that validate wrapper functions exist and theme files contain required keys (tests should not import Red runtime; use source inspection or mocks).

## Tests and CI

- Keep tests environment-agnostic (inspect files or mock Red objects). CI (GitHub Actions) should run pytest and can be extended later to run full integration tests in a Red-enabled environment.

## Short-term priorities

- Finish wrappers for gather/salvage/blackmarket and add their theme JSONs.
- Wire Supplies & CP grant points into `loot.py` reward logic as optional keys.
- Add messages to `locales/messages.pot`.

## Examples

Short usage examples (replace `[p]` with your bot prefix):

- Short patrol / skirmish (quick):

  [p]skirmish

  -> "Skirmish complete: +120 Supplies, +40 XP. Loot: 1x Scrap Part."

- Long operation (higher reward, chance for CP/blueprints):

  [p]operation

  -> "Operation successful: +600 Supplies, +2 CP. Found blueprint: 'Tank Frame Fragment'."

- Training / drill (skill XP):

  [p]drill

  -> "Drill complete: +30 XP, chance to recruit a specialist: failed."

- Gather resources:

  [p]gather

  -> "+40 Supplies, +1 Material"

- Salvage for parts:

  [p]salvage

  -> "+3 Parts, +20 Supplies"

- Black Market (risky):

  [p]blackmarket

  -> "Blackmarket run: +200 Supplies, -10% chance to lose an item: None lost."

- Crafting from blueprint:

  [p]build tank

  -> "Built: Light Tank (consumed: 5x Parts, 200 Supplies, 1x Tank Blueprint)"

These examples are illustrative; real output varies by theme, player stats, and participation.

## Where changes are stored

- Theme data: `adventure/data/zero_hour/`
- Cog edits: `adventure/adventure.py`
- Tests: `tests/theme/test_zero_hour.py`
- Docs & conversion notes: `.vscode/conversion_notes.md`, `docs/GENERALS_COMMANDS.md`, `docs/Commands.md`

---

## Crafting details (blueprints & recipes)

Blueprints are represented as `Item` objects with `rarity` set to `event`. The `build` command consumes one blueprint item and, when a recipe exists, consumes required parts and supplies from the player's backpack.

Current recipe model (temporary - stored in code):
- RECIPES map: fragment -> { parts: int, supplies: int, product: str }
- Example: `"tank": {"parts": 5, "supplies": 100, "product": "Tank"}`

Behavior of `[p]build <name>`:
- Finds a blueprint Item in the backpack where `blueprint_name` is a substring of the Item name (case-insensitive).
- If a recipe is found for that blueprint, requires the specified `parts` and `supplies` to be present in the backpack and consumes them (parts are taken from items with a `parts` attribute; supplies are matched by name containing "supply").
- If the recipe requirements are met, the blueprint is consumed and a crafted `Item` is created and added to the backpack.
- If recipe requirements are not met, the build command returns a user-facing error message and nothing is consumed.
