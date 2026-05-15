#!/usr/bin/env python3
import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

class TransactionType(Enum):
    ACCOUNT_QUERY = "account_query"
    FUNDS_TRANSFER = "funds_transfer"
    BALANCE_CHECK = "balance_check"
    STATEMENT_REQUEST = "statement_request"
    AUTHENTICATION = "authentication"

@dataclass
class MainframeAccount:
    account_number: str
    holder_name: str
    balance: float
    currency: str = "BRL"
    last_transaction: Optional[str] = None
    status: str = "active"

@dataclass
class CICSResponse:
    transaction_id: str
    response_code: str
    data: Dict
    timestamp: float
    security_token: str

class MainframeEmulator:
    def __init__(self, initial_accounts: List[MainframeAccount] = None):
        self.accounts: Dict[str, MainframeAccount] = {}
        self.transaction_log: List[Dict] = []
        self._racf_users: Dict[str, str] = {}
        if initial_accounts:
            for acc in initial_accounts:
                self.accounts[acc.account_number] = acc
        self._racf_users["ARKHE_GATEWAY"] = hashlib.sha256(b"mock_password_123").hexdigest()
        logger.info("🏦 Mainframe emulador inicializado")

    async def authenticate(self, user_id: str, password: str) -> bool:
        await asyncio.sleep(0.01)
        if user_id not in self._racf_users:
            return False
        stored_hash = self._racf_users[user_id]
        provided_hash = hashlib.sha256(password.encode()).hexdigest()
        return stored_hash == provided_hash

    async def execute_transaction(self, txn_type: TransactionType, parameters: Dict, user_id: str, security_token: Optional[str] = None) -> CICSResponse:
        start_time = time.time()
        await asyncio.sleep(0.05 + (hash(f"{txn_type}{parameters}") % 150) / 1000)
        txn_id = f"CICS{int(time.time() * 1000):012d}{hash(user_id) % 10000:04d}"
        try:
            if txn_type == TransactionType.ACCOUNT_QUERY:
                account = self.accounts.get(parameters.get("account_number"))
                if not account:
                    return CICSResponse(txn_id, "ACNT01", {"error": "Account not found"}, time.time(), "")
                return CICSResponse(
                    txn_id, "00",
                    {"account_number": account.account_number, "holder_name": account.holder_name, "balance": account.balance, "currency": account.currency, "status": account.status},
                    time.time(), hashlib.sha3_256(f"{txn_id}{account.balance}".encode()).hexdigest()[:16]
                )
            elif txn_type == TransactionType.FUNDS_TRANSFER:
                from_acc = parameters.get("from_account")
                to_acc = parameters.get("to_account")
                amount = parameters.get("amount", 0)
                if from_acc not in self.accounts or to_acc not in self.accounts:
                    return CICSResponse(txn_id, "ACNT01", {"error": "Invalid account"}, time.time(), "")
                if self.accounts[from_acc].balance < amount:
                    return CICSResponse(txn_id, "BAL001", {"error": "Insufficient funds"}, time.time(), "")
                self.accounts[from_acc].balance -= amount
                self.accounts[to_acc].balance += amount
                self.accounts[from_acc].last_transaction = txn_id
                self._log_smf_entry({
                    "type": "FUNDS_TRANSFER", "from": from_acc, "to": to_acc, "amount": amount, "user": user_id, "txn_id": txn_id, "timestamp": time.time(),
                })
                return CICSResponse(
                    txn_id, "00",
                    {"transferred": amount, "from_balance": self.accounts[from_acc].balance, "to_balance": self.accounts[to_acc].balance},
                    time.time(), hashlib.sha3_256(f"{txn_id}{amount}".encode()).hexdigest()[:16]
                )
        except Exception as e:
            logger.error(f"❌ Erro na transação {txn_type.value}: {e}")
            return CICSResponse(txn_id, "SYS001", {"error": str(e)}, time.time(), "")

    def _log_smf_entry(self, entry: Dict):
        self.transaction_log.append({"smf_id": f"SMF{len(self.transaction_log) + 1:08d}", "smf_time": time.time(), "smf_type": 110, **entry})

    def get_test_accounts(self) -> List[Dict]:
        return [
            {"account_number": "0001-23456-7", "holder_name": "ARKHE Test Account A", "initial_balance": 10000.00},
            {"account_number": "0001-23456-8", "holder_name": "ARKHE Test Account B", "initial_balance": 5000.00},
        ]
