"""Minimal redbot.core.bank stub for tests: exposes Account and BankPruneError used by adventure.bank imports."""

class BankPruneError(Exception):
    """Stub exception for bank prune errors."""
    pass


class Account:
    def __init__(self, *a, **k):
        # minimal attributes used by code under test
        self.balance = 0

    async def deposit(self, amount):
        self.balance += amount

    async def withdraw(self, amount):
        if amount > self.balance:
            raise BankPruneError("Insufficient funds")
        self.balance -= amount


