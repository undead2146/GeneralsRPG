import traceback
def test_import_monolithic_module():
    """Original import test kept for diagnostics but run as a test so pytest
    reports failures cleanly. This intentionally imports `adventure.adventure`.
    """
    import importlib
    try:
        adv = importlib.import_module('adventure.adventure')
        assert hasattr(adv, '__file__')
    except Exception as e:
        # Reraise to let pytest capture the traceback
        raise


def test_import_modular_api():
    """New test: import the refactored modular subpackages instead of the
    huge monolithic module. This makes the test suite align with the
    architecture described in `docs/Architecture.md`.
    """
    import importlib

    modules = [
        'adventure.core',
        'adventure.core.game_session',
        'adventure.core.character',
        'adventure.commands',
        'adventure.commands.backpack',
        'adventure.ui',
        'adventure.ui.menus',
    ]

    for m in modules:
        importlib.import_module(m)

