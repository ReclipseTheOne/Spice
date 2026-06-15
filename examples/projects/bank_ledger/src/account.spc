# An account composes a list of Transactions and derives its balance from them.
#
# A `final` method (`number` can't be overridden), a compile-time
# annotation (`@!print_on_call`, which injects a log line and then vanishes),
# and composition (the account owns its Transaction history).

from transactions import TxType, Transaction


class Account {
    def Account(owner: str) {
        self.owner = owner
        self.history: list = []
        self.balance: float = 0.0
    }

    final def number() -> str {
        return f"acct:{self.owner}"
    }

    @!print_on_call(time_format="%H:%M:%S")
    def deposit(amount: float) -> None {
        self.balance = self.balance + amount
        self.history.append(Transaction(TxType.DEPOSIT, amount))
    }

    def withdraw(amount: float) -> None {
        if amount > self.balance {
            raise ValueError("insufficient funds")
        }
        self.balance = self.balance - amount
        self.history.append(Transaction(TxType.WITHDRAWAL, amount))
    }

    def statement() -> str {
        lines: list = [f"Statement for {self.owner} ({self.number()})"]
        for tx in self.history {
            lines.append(f"  {tx.kind.name:<11} {tx.signed_amount():+.2f}")
        }
        lines.append(f"  balance:    {self.balance:.2f}")
        return "\n".join(lines)
    }
}
