# S4: Ticket booking and limited-inventory reservation

Run `python verify.py` from this directory with Python 3.12+. Recorded runtime: Python 3.12.10 / SQLite 3.49.1. `booking.py` implements the domain and actual loopback callback contract; the shared standard-library HTTP/transaction/verifier helpers are in `../worked-systems-s4-s6/`.

57 named checks cover validation, atomic group/last-seat holds, fixed expiry and replay, owner scope, exact provider binding, event/payment dedupe, late/extra-charge refund intent, injected rollback, reopen and real HTTP. Two contenders use independent thread-owned connections. Pending refund intent is not an executed provider refund.

No real payment, cloud account, PostgreSQL execution, distributed clock/lock, production authentication/TLS or load benchmark is included. Hold records are retained under a finite 128-row lesson cap; confirmed cancellation, renewals, waits and refund execution remain unimplemented.

`lesson.md` is authored prose. Regenerate all three chapters with `python ../worked-systems-s4-s6/author.py`; integrate and run the single site verification there. See the [batch instructions](../worked-systems-s4-s6/README.md). All owned listeners/SQLite resources/threads and temporary files are removed; port 3000 and Docker remain stopped.
