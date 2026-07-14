"""Sandbox escrow helpers — simulates locking/releasing crypto in a smart-contract escrow.

This is intentionally a deterministic mock suitable for demos / local development.
It generates Ethereum-style transaction hashes and tracks lock/release state on the Transfer.
Real mainnet / testnet contracts can replace these helpers later without changing the API surface.
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Transfer


def generate_tx_hash() -> str:
    """Return a 32-byte hex hash prefixed with 0x (66 chars)."""
    return "0x" + secrets.token_hex(32)


def lock_in_escrow(transfer: "Transfer") -> "Transfer":
    """Mark funds as locked in the sandbox escrow contract."""
    transfer.escrow_status = "locked"
    transfer.escrow_tx_hash = generate_tx_hash()
    transfer.escrow_release_tx_hash = ""
    return transfer


def release_from_escrow(transfer: "Transfer") -> "Transfer":
    """Release escrowed funds to the recipient (sandbox)."""
    transfer.escrow_status = "released"
    transfer.escrow_release_tx_hash = generate_tx_hash()
    return transfer
