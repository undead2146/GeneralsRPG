import inspect

import adventure.wrappers as top_wrappers
import adventure.commands.wrappers as cmd_wrappers


def test_wrapper_classes_exist():
    assert hasattr(top_wrappers, "WrapperCommands"), "top-level shim must expose WrapperCommands"
    assert hasattr(cmd_wrappers, "WrapperCommands"), "commands.wrappers must expose WrapperCommands"


def test_wrapper_methods_present():
    expected = {
        "skirmish",
        "operation",
        "drill",
        "gather",
        "salvage",
        "blackmarket",
        "stronghold",
        "general",
        "blueprints",
        "build",
        "duel",
        "warzone",
    }
    cls = cmd_wrappers.WrapperCommands
    # Ensure methods exist on the class (they may be functions or descriptors)
    missing = {name for name in expected if not hasattr(cls, name)}
    assert not missing, f"WrapperCommands is missing methods: {sorted(missing)}"


def test_wrapper_is_mixin_callable():
    # Create a tiny concrete class mixing the wrapper to ensure it can be instantiated
    class Concrete(cmd_wrappers.WrapperCommands):
        def __init__(self):
            # minimal properties used by some wrappers
            self.config = type("C", (), {"user": lambda _ : None})()
            self._daily_bonus = 0

    inst = Concrete()
    # verify that method objects are bound correctly
    assert inspect.ismethod(getattr(inst, "skirmish"))
    assert inspect.ismethod(getattr(inst, "build"))
