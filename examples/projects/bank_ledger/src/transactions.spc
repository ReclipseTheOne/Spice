# Ledger entries.
#
# `TxType` tags each entry; `Transaction` is an immutable-ish record of one
# movement of money. The data class gives us the constructor, repr and equality.

enum TxType {
    DEPOSIT,
    WITHDRAWAL
}


data class Transaction(kind: TxType, amount: float) {
    def signed_amount() -> float {
        if self.kind == TxType.WITHDRAWAL {
            return -self.amount
        }
        return self.amount
    }
}
