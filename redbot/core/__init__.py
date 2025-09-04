class Config:
    def __init__(self):
        pass


class commands:
    class Cog:
        pass


class _BankStub:
    async def get_currency_name(self, *a, **k):
        return "Credits"

    async def get_balance(self, user):
        return 0

bank = _BankStub()


class errors:
    class BalanceTooHigh(Exception):
        pass


__all__ = ["Config", "commands", "bank"]
