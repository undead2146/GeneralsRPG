"""Migration package for ``adventure.core``.

Expose a small, stable public API for consumers during the refactor. This
keeps imports short (``from adventure.core import craft_from_blueprint``)
and reduces errors caused by relative import chains.
"""

from .items import Item, craft_from_blueprint  # type: ignore
from .units import UnitState  # type: ignore
from .rewards import RewardEngine  # type: ignore

__all__ = ["Item", "craft_from_blueprint", "UnitState", "RewardEngine"]
