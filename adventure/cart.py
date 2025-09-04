# Compatibility shim re-exporting the Trader UI from the new location.

"""Top-level shim for ``adventure.cart``.

The implementation moved to :mod:`adventure.ui.cart`. Keep this shim so
third-party imports that reference ``adventure.cart`` continue to work
during the refactor.
"""

from adventure.ui.cart import *  # noqa: F401,F403

__all__ = ["Trader", "TraderModal", "TraderSelect", "TraderButton"]
