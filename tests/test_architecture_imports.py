def test_import_architecture_modules():
    """Smoke test: import core, commands and ui modules to ensure the
    re-organized package layout is loadable in test environments.
    """
    import importlib, sys

    # Ensure project root is on sys.path in test env
    ROOT = ""
    if ROOT not in sys.path and "." not in sys.path:
        sys.path.insert(0, ROOT)

    mods = [
        'adventure.core',
        'adventure.core.game_session',
        'adventure.commands',
        'adventure.commands.backpack',
        'adventure.ui',
        'adventure.ui.menus',
    ]

    for m in mods:
        importlib.import_module(m)

    # If we reached here without ImportError, consider it a pass
    assert True
