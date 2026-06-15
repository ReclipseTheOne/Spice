# bank_ledger - entry point.
#
# Build & run from this folder:
#     python build.spice.py --run

from account import Account


def main() -> None {
    account: Account = Account("Ada")

    # Each deposit() call also prints a timestamped line - that print is injected
    # by the @!print_on_call compile-time annotation on the method.
    account.deposit(100.0)
    account.deposit(45.50)
    account.withdraw(30.0)

    print(account.statement())
}


main()
