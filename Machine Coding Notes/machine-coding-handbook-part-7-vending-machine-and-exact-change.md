# Machine Coding Practice — Part 7: Vending Machine and Exact Change

**M5: compute a valid sale completely before committing inventory and money.**

## 1. The problem and its purpose

Build a vending machine with item selection, coin insertion, purchase and cancellation. The visible interface looks small, but it combines inventory, customer escrow, machine cash and a state transition. The main coding question is what remains true when a purchase cannot complete.

Clarify denomination support, stock, changing a selection, when inserted money joins machine cash, refunds, and whether the dispenser can fail. Here one customer session exists at a time. SELECT may replace the selection while keeping escrow. Coins can be inserted before selecting. Money uses integer units; there is no floating-point currency arithmetic.

## 2. Supplied fixture and contract

| Component | Initial value |
| --- | --- |
| Tea | Price 4, stock 2 |
| Snack | Price 7, stock 1 |
| Supported coins | 1, 3, 4, 10 |
| Machine cash | Two 3 coins and one 4 coin; total 10 |
| Customer escrow | Empty, maximum credit 1,000 |

VEND requires a selected, stocked item, sufficient credit and an exact change subset. The available change pool includes both machine cash and the current escrow. Any feasible change combination is acceptable; minimum number of coins is not required. A successful sale reduces stock, transfers escrow into cash minus returned change, and resets the session.

If change cannot be made, inventory, cash, credit and selection stay unchanged. CANCEL returns exactly the escrow denominations in sorted order and resets the session. It cannot draw a refund from unrelated machine cash. A repeated CANCEL returns an empty list.

## 3. Invariants and transition reasoning

All counts remain nonnegative. Credit equals the value of escrow. For a successful sale, new machine cash value equals old machine cash value plus the item's price. Inventory decreases by one only at the successful commit point.

Compute candidate availability and change first. Build the returned-coin vector before changing live state. The final in-memory update replaces cash, decrements stock and clears escrow. Domain validation cannot leave half a sale. This does not establish a guarantee for every possible allocation failure, and no such failure is injected.

The unusual denominations expose a real algorithmic trap: to return 6 from available 4, 3 and 3, a greedy largest-first choice gets stuck after 4, while 3+3 works. Bounded subset-sum considers each available physical coin once, iterating amount downward so one coin cannot be reused within its pass.

## 4. Complete model implementation

<!-- BEGIN MODEL -->

```cpp
class VendingMachine {
    struct Item { Number price, stock; };
    const std::vector<Number> denominations_{1, 3, 4, 10};
    std::map<std::string, Item> items_{{"tea", {4, 2}}, {"snack", {7, 1}}};
    std::vector<Number> cash_{0, 2, 1, 0}, escrow_{0, 0, 0, 0};
    std::optional<std::string> selected_;
    Number credit_ = 0;
public:
    void select(const std::string& id) {
        require(items_.count(id) != 0, "unknown item");
        require(items_.at(id).stock > 0, "out of stock"); selected_ = id;
    }
    void insert(Number coin) {
        auto it = std::find(denominations_.begin(), denominations_.end(), coin);
        require(it != denominations_.end(), "unsupported coin");
        require(credit_ + coin <= 1000, "credit limit");
        ++escrow_[static_cast<std::size_t>(it - denominations_.begin())]; credit_ += coin;
    }
    std::vector<Number> vend() {
        require(selected_.has_value(), "select item first");
        auto& item = items_.at(*selected_);
        require(item.stock > 0, "out of stock"); require(credit_ >= item.price, "insufficient credit");
        const Number change = credit_ - item.price;
        auto available = cash_;
        for (std::size_t i = 0; i < cash_.size(); ++i) available[i] += escrow_[i];
        // Bounded subset-sum: each available physical coin is considered once.
        std::vector<std::optional<std::vector<Number>>> dp(static_cast<std::size_t>(change + 1));
        dp[0] = std::vector<Number>(4, 0);
        for (std::size_t i = 0; i < available.size(); ++i) {
            for (Number c = 0; c < available[i]; ++c) {
                for (Number amount = change; amount >= denominations_[i]; --amount) {
                    auto source = static_cast<std::size_t>(amount - denominations_[i]);
                    auto target = static_cast<std::size_t>(amount);
                    if (!dp[target] && dp[source]) { dp[target] = *dp[source]; ++(*dp[target])[i]; }
                }
            }
        }
        require(dp[static_cast<std::size_t>(change)].has_value(), "exact change unavailable");
        auto chosen = *dp[static_cast<std::size_t>(change)];
        std::vector<Number> returned;
        for (std::size_t i = 0; i < cash_.size(); ++i) {
            available[i] -= chosen[i];
            for (Number c = 0; c < chosen[i]; ++c) returned.push_back(denominations_[i]);
        }
        --item.stock; cash_.swap(available); escrow_.assign(4, 0); credit_ = 0; selected_.reset();
        return returned;
    }
    std::vector<Number> cancel() {
        std::vector<Number> returned;
        for (std::size_t i = 0; i < escrow_.size(); ++i)
            for (Number c = 0; c < escrow_[i]; ++c) returned.push_back(denominations_[i]);
        escrow_.assign(4, 0); credit_ = 0; selected_.reset(); return returned;
    }
    std::string state() const {
        std::string stock = "{";
        for (const auto& [id, item] : items_) {
            if (stock.size() > 1) stock += ',';
            stock += json(id) + ':' + json(item.stock);
        }
        Number balance = 0;
        for (std::size_t i = 0; i < cash_.size(); ++i) balance += cash_[i] * denominations_[i];
        return "{\"stock\":" + stock + "},\"cash\":" + json(balance) + ",\"credit\":" + json(credit_)
            + ",\"selected\":" + (selected_ ? json(*selected_) : "null") + '}';
    }
};
```

<!-- END MODEL -->

## 5. Worked command traces

<!-- BEGIN TRACES -->

### T17. Bounded exact change defeats a greedy choice

**Worked explanation:** Tea costs 4 and an inserted 10 needs 6 change. Available 4 and two 3 coins cannot satisfy a greedy 4-first path, but 3+3 is feasible.

Run `python examples/machine-coding/verify.py --trace T17` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SELECT tea
{"ok":true,"result":null}
INSERT 10
{"ok":true,"result":null}
VEND
{"ok":true,"result":[3,3]}
STATE
{"ok":true,"result":{"stock":{"snack":1,"tea":1},"cash":14,"credit":0,"selected":null}}
```

**Common trap:** Canonical currency assumptions do not hold for arbitrary denominations and limited stock.

**Interview follow-up:** Does this contract require any feasible change or minimum-coin change?

### T18. Impossible change leaves the whole session intact

**Worked explanation:** Two inserted 3 coins provide credit 6 for tea, but no available subset makes change 2. Failure retains both escrow coins and stock.

Run `python examples/machine-coding/verify.py --trace T18` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SELECT tea
{"ok":true,"result":null}
INSERT 3
{"ok":true,"result":null}
INSERT 3
{"ok":true,"result":null}
VEND
{"ok":false,"error":"exact change unavailable"}
STATE
{"ok":true,"result":{"stock":{"snack":1,"tea":2},"cash":10,"credit":6,"selected":"tea"}}
CANCEL
{"ok":true,"result":[3,3]}
```

**Common trap:** Deducting stock before checking change can lose inventory on a rejected sale.

**Interview follow-up:** Where would you place the commit point with a physical dispenser?

### T19. Cancel refunds only customer escrow

**Worked explanation:** Cancellation returns the inserted denominations, leaves machine cash unchanged and clears the selected item. A repeated cancel is an empty refund.

Run `python examples/machine-coding/verify.py --trace T19` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SELECT snack
{"ok":true,"result":null}
INSERT 4
{"ok":true,"result":null}
INSERT 1
{"ok":true,"result":null}
CANCEL
{"ok":true,"result":[1,4]}
CANCEL
{"ok":true,"result":[]}
STATE
{"ok":true,"result":{"stock":{"snack":1,"tea":2},"cash":10,"credit":0,"selected":null}}
```

**Common trap:** Refunding from total machine cash allows the session to withdraw unrelated money.

**Interview follow-up:** How do payment IDs make cancellation idempotent across retries?

### T20. Validation, insufficient funds and stockout

**Worked explanation:** Unsupported coins and underpayment do not mutate inventory. Two exact-price sales consume the two teas; selecting a third tea fails.

Run `python examples/machine-coding/verify.py --trace T20` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SELECT tea
{"ok":true,"result":null}
INSERT 2
{"ok":false,"error":"unsupported coin"}
VEND
{"ok":false,"error":"insufficient credit"}
INSERT 4
{"ok":true,"result":null}
VEND
{"ok":true,"result":[]}
SELECT tea
{"ok":true,"result":null}
INSERT 4
{"ok":true,"result":null}
VEND
{"ok":true,"result":[]}
SELECT tea
{"ok":false,"error":"out of stock"}
```

**Common trap:** A purchase button must recheck availability even after selection.

**Interview follow-up:** What changes if several sessions can select the last item?

<!-- END TRACES -->

## 6. Complexity and alternatives

Let C be the total number of available coins, A the required change amount, and D the number of denominations. This implementation uses O(CAD) time because each reachable DP state copies a D-count vector. It uses O(AD) space, plus O(returned coin count) for the result. With fixed D=4 these simplify to O(CA) time and O(A) space; they are pseudopolynomial in the numeric amount.

Credit is capped at 1,000, which bounds the DP amount. A production machine should also cap physical coin counts and service inventory. A predecessor-based DP could reduce copied state. A minimum-coin solution would need a different recurrence and tie-break contract; the current algorithm promises feasibility only.

## 7. Architecture follow-up

The physical world introduces irreversible effects. If a motor dispenses an item but acknowledgement is lost, blindly retrying may dispense twice. If payment is captured and the motor jams, compensation may require a refund rather than a memory rollback.

Separate the domain decision from coin hardware, payment and dispenser adapters. Record sale/attempt IDs, define device acknowledgements and recovery, and decide when an item is reserved. The current program has no hardware, gateway, persistence or concurrent customers. Bridge to [checkout and payments](/docs/system-design/checkout-payments-credit-ledger) for idempotency and reconciliation.

## 8. Interview questions with answers

### Q1. Why separate escrow from machine cash?

Escrow belongs to the current customer until a sale succeeds. That separation makes cancellation exact and prevents rejected purchases from changing the machine's cash ownership.

### Q2. Why not use greedy change?

Limited coin inventory and arbitrary denominations break greedy assumptions. The supplied 6-change example has a feasible 3+3 solution that a 4-first strategy misses.

### Q3. Does the DP return the fewest coins?

No. It keeps the first reachable count vector for each amount. The agreed requirement is any exact feasible subset. Optimize coin count only after clarifying that it is required.

### Q4. Can inserted coins be used for change?

Yes, for this exercise. The candidate pool is cash plus escrow. A real machine's physical coin routing may prevent that, in which case the availability model must change.

### Q5. What does atomic mean here?

For serial calls and exercised domain failures, a rejected sale changes no sale state and a successful one commits its updates together in the model. It is not a distributed or hardware atomicity claim.

### Q6. Why use integer money?

Prices and coin values are exact whole units in this fixture. Binary floating point could introduce equality and rounding errors into exact-change checks. Real multi-currency systems need an explicit smallest-unit and rounding policy.

### Q7. How does the independent oracle check change?

It enumerates bounded denomination-count combinations to decide feasibility, then validates the returned coins against availability and exact value. It permits any valid combination rather than copying the DP's tie-break.

### Q8. How would multiple customer sessions change the design?

Escrow would be per session, while stock and cash would be shared. Selecting the last item would need a reservation or a rechecked atomic purchase decision, plus expiration and refund semantics.

## 9. Practice tasks

- [ ] Require minimum-coin change and a deterministic tie break. Find a fixture where the current first-feasible solution differs.
- [ ] Add a restock/service operation that is forbidden during a customer session. Test rejected service calls preserve escrow.
- [ ] Add an explicit dispenser-failure adapter. Specify whether it is known-before-dispense, known-after-dispense or ambiguous; give a recovery plan for each.
- [ ] Model two sessions competing for one item. Identify the shared commit boundary and the refund behavior for the loser.

Next: [Meeting Room Booking](/docs/machine-coding/meeting-room-booking).
