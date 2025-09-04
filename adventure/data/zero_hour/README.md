Zero Hour theme data

This folder contains the per-theme JSON files that drive Generals-specific rewards, recipes, monsters, and gather/salvage tables. The Adventure engine loads these JSON files when the theme `zero_hour` is active.

Typical files and brief schema examples:

- rewards.json
  - Defines drop tables and mapping to Supplies/CP/Items.
  - Example:
    {
      "drops": [
        { "id": "supplies_small", "type": "supplies", "amount": 50, "weight": 60 },
        { "id": "parts_small", "type": "parts", "amount": 2, "weight": 30 },
        { "id": "blueprint_fragment", "type": "blueprint", "name": "Tank Fragment", "weight": 10 }
      ]
    }

- gather.json / salvage.json / blackmarket.json
  - Action-specific drop tables. Same format as rewards.json.

- recipes.json
  - Mapping of blueprint names to required parts and supplies.
  - Example:
    {
      "tank": { "parts": 5, "supplies": 200, "product": "Light Tank" }
    }

- monsters.json
  - Enemy data and resistances. Used by the adventure engine for flavor and balance.

Guidelines
- Keep weights and amounts reasonable for the game's balance.
- Add unit tests under `tests/unit/` for new reward or recipe behavior.
- When editing JSONs, validate formatting with a JSON linter and run the unit tests.
