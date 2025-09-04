"""Minimal placeholder defaults for `adventure.core.defaults`.

During the refactor the real defaults may live in either
`adventure.defaults` or `adventure.core.defaults`. Importing the other
module can cause a circular import during test collection. Provide a
small, import-time-safe fallback here so `from adventure.core.defaults
import default_global, ...` always succeeds during tests.
"""

# Minimal placeholders used for import-time stability. Tests or the real
# implementation can override these with the real values when available.
default_user = {}
default_guild = {}
default_global = {}

__all__ = ["default_user", "default_guild", "default_global"]
