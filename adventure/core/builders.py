"""Builder commands moved into `adventure.core` for modularization.

This file was copied from the top-level `adventure.builders` to allow
gradual refactor. It keeps the same implementation for now.
"""
from typing import Optional

try:
	from redbot.core import commands
except Exception:
	class commands:
		class hybrid_command:
			def __init__(self, *a, **k):
				pass

		class cooldown:
			def __init__(self, *a, **k):
				pass

		class bot_has_permissions:
			def __init__(self, *a, **k):
				pass

		class guild_only:
			def __init__(self, *a, **k):
				pass

from adventure.charsheet import Character
from adventure.helpers import smart_embed


class BuilderCommands:
	"""Simple builders mixin.

	Commands implemented:
	- `/builder buy <type>`: adds a builder count to the character.
	- `/builder assign <building_id>`: assigns a builder to a building (increments assigned count).
	- `/builder upgrade <building_id>`: increases building level.
	"""

	@commands.hybrid_command(name="builder buy")
	async def builder_buy(self, ctx: commands.Context, builder_type: Optional[str] = "dozer"):
		try:
			c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
		except Exception:
			return await smart_embed(ctx, "Unable to load character data.")

		builders = getattr(c, "builders", {}) or {}
		builders[builder_type] = builders.get(builder_type, 0) + 1
		c.builders = builders
		await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
		return await smart_embed(ctx, f"Purchased builder '{builder_type}'. You now have {builders[builder_type]}.", success=True)

	@commands.hybrid_command(name="builder assign")
	async def builder_assign(self, ctx: commands.Context, building_id: Optional[str] = None):
		if not building_id:
			return await smart_embed(ctx, "Specify a building id to assign a builder to.")
		try:
			c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
		except Exception:
			return await smart_embed(ctx, "Unable to load character data.")

		builders = getattr(c, "builders", {}) or {}
		total_builders = sum(builders.values())
		if total_builders <= 0:
			return await smart_embed(ctx, "No builders available to assign.")

		if not hasattr(c, "buildings") or building_id not in (c.buildings or {}):
			return await smart_embed(ctx, "You do not own that building to assign a builder to.")

		assigned = c.buildings[building_id].get("assigned", 0)
		c.buildings[building_id]["assigned"] = assigned + 1
		await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
		return await smart_embed(ctx, f"Assigned a builder to {building_id}. (Assigned: {assigned+1})", success=True)

	@commands.hybrid_command(name="builder upgrade")
	async def builder_upgrade(self, ctx: commands.Context, building_id: Optional[str] = None):
		if not building_id:
			return await smart_embed(ctx, "Specify a building id to upgrade.")
		try:
			c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
		except Exception:
			return await smart_embed(ctx, "Unable to load character data.")

		if not hasattr(c, "buildings") or building_id not in (c.buildings or {}):
			return await smart_embed(ctx, "You do not own that building to upgrade.")

		lvl = c.buildings[building_id].get("level", 1)
		c.buildings[building_id]["level"] = lvl + 1
		await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
		return await smart_embed(ctx, f"Upgraded {building_id} to level {lvl+1}.", success=True)

"""Wrapper re-export for `adventure.builders` while migrating to adventure.core."""
from adventure.builders import *  # noqa: F401,F403
