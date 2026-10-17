# S8: Checkout, payments and credit ledger

Run `python examples/system-design/module-13-checkout-payments-credit-ledger/verify.py` from the repository root. Standard-library Python; temporary SQLite files and an owned ephemeral merchant HTTP listener are closed/removed afterward. Port 3000 stays unused.

`checkout.py` separates a local simulated provider commit from merchant state, injects reply loss, and converges verified observations on one balanced integer-CREDIT grant. Spending is conditional and reversal appends entries. `verify.py` records 62 checks including four competing calls, rollback and actual merchant HTTP. Provider calls remain local methods. No real money, card data, provider network or external refund is involved.

`lesson.md` is the authored teaching source. The batch `../worked-systems-s7-s9/author.py` embeds exact source and recorded output into Part 15. See the batch README for generation, integration and site validation.
