# -*- coding: utf-8 -*-
"""
Economy helpers wrapping Redbot bank.
"""

from redbot.core.errors import BalanceTooHigh
from adventure.bank import bank


async def add_cp(user, amount: int):
    """Add credits to a user."""
    try:
        await bank.deposit_credits(user, amount)
    except BalanceTooHigh as e:
        await bank.set_balance(user, e.max_balance)


async def remove_cp(user, amount: int):
    """Remove credits from a user."""
    bal = await bank.get_balance(user)
    if bal >= amount:
        await bank.withdraw_credits(user, amount)
    else:
        await bank.set_balance(user, 0)
