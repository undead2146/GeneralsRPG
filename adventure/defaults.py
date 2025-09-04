"""Shim for `adventure.defaults` re-exporting from `adventure.core.defaults`.

This keeps imports stable while the real implementation lives in
`adventure.core.defaults`.
"""

try:
    from adventure.core.defaults import *  # noqa: F401,F403
except Exception:
    # During the refactor or in test environments the `adventure.core.defaults`
    # module may not be importable. Provide minimal placeholders so code that
    # does `from adventure.defaults import default_global, ...` doesn't fail at
    # import/collection time. Empty dicts are safe for register_* calls used in
    # tests and can be extended later with real defaults.
    default_user = {}
    default_guild = {}
    default_global = {}

__all__ = [
    "default_user",
    "default_guild",
    "default_global",
]
