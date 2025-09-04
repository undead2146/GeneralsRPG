"""Shim for `adventure.combat` that re-exports implementation from
`adventure.core.combat` during refactor.
"""

from adventure.core.combat import *  # noqa: F401,F403

__all__ = [
    'ActionResult',
    'CombatOutcome',
    'CombatEngine',
]
from dataclasses import dataclass, field
import random
from typing import Any, Dict, List, Optional


@dataclass
class ActionResult:
    damage: int = 0
    diplomacy: int = 0
    crit: bool = False
    fumble: bool = False
    message: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CombatOutcome:
    total_damage: int = 0
    total_diplomacy: int = 0
    crits: List[Any] = field(default_factory=list)
    fumbles: List[Any] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    rounds: int = 0
    slain: bool = False
    persuaded: bool = False


class CombatEngine:
    def __init__(
        self,
        session_snapshot: Dict,
        seed: Optional[int] = None,
        rng: Optional[random.Random] = None,
        resolvers: Optional[Dict[str, Any]] = None,
    ):
        """
        session_snapshot: pure JSON-serializable dict describing the session.
          Expected keys (optional): 'fire', 'airstrike', 'negotiate', 'engineer', 'retreat',
          each mapped to a list of participant dicts with at least 'id' and 'name'.
        seed: optional integer seed used to construct a deterministic RNG if rng not provided.
        rng: optional random.Random instance. If both are None, a new random.Random() is used.
        resolvers: optional mapping of action name -> callable(session, participant, rng) -> ActionResult
        """
        self.session = session_snapshot or {}
        if rng is not None:
            self.rng = rng
        else:
            self.rng = random.Random(seed)

        # default resolver registry
        self.resolvers = resolvers or {
            "fire": self._resolve_fire,
            "airstrike": self._resolve_airstrike,
            "negotiate": self._resolve_negotiate,
            "engineer": self._resolve_engineer,
            "retreat": self._resolve_retreat,
        }

    # Public API ---------------------------------------------------------
    def resolve_round(self) -> CombatOutcome:
        outcome = CombatOutcome()

        # Order: fire, airstrike, negotiate, engineer, retreat
        for action in ("fire", "airstrike", "negotiate", "engineer", "retreat"):
            participants = self.session.get(action, []) or []
            for p in participants:
                resolver = self.resolvers.get(action)
                if not resolver:
                    continue
                result = resolver(p)
                outcome.total_damage += int(result.damage or 0)
                outcome.total_diplomacy += int(result.diplomacy or 0)
                if result.crit:
                    outcome.crits.append(p)
                if result.fumble:
                    outcome.fumbles.append(p)
                if result.message:
                    outcome.messages.append(result.message)

        outcome.rounds = 1

        # Evaluate victory conditions if monster info present
        monster_hp = self.session.get("monster_hp")
        monster_dipl = self.session.get("monster_dipl")
        if monster_hp is not None:
            outcome.slain = outcome.total_damage >= int(monster_hp)
        if monster_dipl is not None:
            outcome.persuaded = outcome.total_diplomacy >= int(monster_dipl)

        return outcome

    def resolve_full(self, max_rounds: int = 6) -> CombatOutcome:
        combined = CombatOutcome()
        for r in range(max_rounds):
            o = self.resolve_round()
            # aggregate
            combined.total_damage += o.total_damage
            combined.total_diplomacy += o.total_diplomacy
            combined.crits.extend(o.crits)
            combined.fumbles.extend(o.fumbles)
            combined.messages.extend([f"[R{r+1}] " + m for m in o.messages])
            combined.rounds += 1
            # if victory reached, stop
            if o.slain or o.persuaded:
                combined.slain = o.slain
                combined.persuaded = o.persuaded
                break
        return combined

    # --- Default resolvers (pure functions using self.rng) -------------
    def _resolve_fire(self, participant: Dict) -> ActionResult:
        roll = self.rng.randint(1, 20)
        dmg = roll * 2
        crit = roll == 20
        fumble = roll == 1
        if crit:
            dmg *= 2
        if fumble:
            dmg = 0
        name = participant.get("name") or str(participant.get("id"))
        msg = f"🔫 {name} fired for {dmg} damage."
        if crit:
            msg += " 💥 Critical!"
        if fumble:
            msg = f"❌ {name} misfired!"
        return ActionResult(damage=dmg, crit=crit, fumble=fumble, message=msg)

    def _resolve_airstrike(self, participant: Dict) -> ActionResult:
        roll = self.rng.randint(1, 20)
        dmg = roll * 3
        crit = roll >= 18
        fumble = roll <= 2
        if crit:
            dmg *= 2
        if fumble:
            dmg = 0
        name = participant.get("name") or str(participant.get("id"))
        msg = f"✈️ {name} called an airstrike for {dmg} damage."
        if crit:
            msg += " 💥 Direct hit!"
        if fumble:
            msg = f"❌ {name}'s airstrike missed!"
        return ActionResult(damage=dmg, crit=crit, fumble=fumble, message=msg)

    def _resolve_negotiate(self, participant: Dict) -> ActionResult:
        roll = self.rng.randint(1, 20)
        dip = roll * 2
        crit = roll >= 18
        fumble = roll <= 2
        if crit:
            dip *= 2
        if fumble:
            dip = 0
        name = participant.get("name") or str(participant.get("id"))
        msg = f"🗨️ {name} attempted negotiation ({dip})."
        if crit:
            msg += " Persuasive!"
        if fumble:
            msg = f"❌ {name} offended the enemy!"
        return ActionResult(diplomacy=dip, crit=crit, fumble=fumble, message=msg)

    def _resolve_engineer(self, participant: Dict) -> ActionResult:
        roll = self.rng.randint(1, 10)
        buff = roll * 2
        name = participant.get("name") or str(participant.get("id"))
        msg = f"🔧 {name} repaired vehicles, boosting attack by {buff}."
        return ActionResult(damage=buff, message=msg)

    def _resolve_retreat(self, participant: Dict) -> ActionResult:
        name = participant.get("name") or str(participant.get("id"))
        msg = f"⚠️ {name} retreated from battle."
        # retreat doesn't change damage/diplomacy by default
        return ActionResult(message=msg)
