"""Core types moved from top-level `adventure.types`.

This file mirrors the original data structures and is intended to be the
source-of-truth for any future refactors that move game logic into
`adventure.core`.
"""
from typing import List, TypedDict


class MiniBoss(TypedDict):
	requirements: List[str]
	defeat: str
	special: str


class Monster(TypedDict):
	hp: int
	pdef: float
	mdef: float
	cdef: float
	dipl: int
	image: str
	boss: bool
	miniboss: MiniBoss
	color: str
