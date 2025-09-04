"""Developer-only commands for Adventure moved to adventure.commands.dev

This module contains owner/developer utilities and remains import-compatible
via the top-level adventure.dev shim.
"""
from __future__ import annotations

from typing import Optional

try:
    from redbot.core import commands
except Exception:  # pragma: no cover - test shim
    # Minimal commands shim for import-time safety in tests
    class _CommandsShim:
        class Cog:
            pass

        @staticmethod
        def is_owner(*a, **k):
            return lambda f: f

        @staticmethod
        def command(*a, **k):
            return lambda f: f

    commands = _CommandsShim()

# Defensive: ensure `is_owner` exists on the imported `commands` object so
# decorators like `@commands.is_owner()` are import-time-safe.
try:
    if not hasattr(commands, "is_owner"):
        commands.is_owner = lambda *a, **k: (lambda f: f)
except Exception:
    pass

try:
    from redbot.core.i18n import Translator
except Exception:  # pragma: no cover - test shim
    def Translator(name, file):
        return lambda s: s

from adventure.helpers import ConfirmView

_ = Translator("Adventure", __file__)


class DevCommands(commands.Cog):
    """Developer convenience commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def devreset(self, ctx: commands.Context, user_id: Optional[int] = None):
        """Reset a user's adventure data (developer only)."""
        await ctx.send(_("This command is a placeholder in the refactor."))
