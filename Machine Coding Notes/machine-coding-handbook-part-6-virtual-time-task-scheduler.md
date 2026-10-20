# Machine Coding Practice — Part 6: Virtual Time Task Scheduler

**M4: separate scheduling order, task state and execution outcome.**

## 1. The problem and its purpose

Build an in-memory scheduler that runs due callbacks when an explicit ADVANCE command moves virtual time. A scheduler decides when work becomes eligible. A worker executes that work. Combining them in one small process is useful practice, provided their responsibilities remain clear.

Clarify priority direction, ties, cancellation, task-ID reuse, retries and whether callbacks may modify the scheduler. Here earlier due time wins, higher integer priority wins at equal due time, and insertion order wins the final tie. IDs remain reserved forever. There are no automatic retries. Callbacks cannot schedule, cancel or advance through this scheduler while it is running.

## 2. State machine and API

```text
ADD -> scheduled -> succeeded
                -> failed
                -> cancelled
```

The queue stores scheduled entries ordered by due time, priority and sequence. The status map is authoritative: cancellation updates it, while the old heap entry remains until popped. Terminal states do not transition again. No transient running state is exposed; callbacks execute synchronously inside ADVANCE.

The invariants are that each accepted ID has one status, only scheduled entries may execute, and virtual time never decreases. Queue tombstones may outlive cancellation, but they cannot override authoritative terminal state.

| Command | Behavior |
| --- | --- |
| ADD id due priority ok/fail | Store a real no-op or throwing callback supplied by the adapter |
| CANCEL id | True only when a scheduled task changes to cancelled |
| ADVANCE now | Drain due, noncancelled tasks and return their outcomes |
| STATE | All known task IDs and statuses |

Time is an integer from 0 to 10^12 and never decreases. Priority is in 0..1,000,000. A task can be due at the current time, but ADD never runs it immediately. Another ADVANCE at that same time will run it.

## 3. Implementation reasoning

A priority queue returns the next eligible task efficiently. C++ priority-queue comparison expresses which element has lower precedence; explicitly test the direction rather than guessing. The standard's [priority_queue overview](https://eel.is/c++draft/priority.queue) describes its ordering requirement. This lab compiles the implementation in C++17, while the linked live draft can contain newer facilities.

On ADVANCE, validate time, set a scope-owned running guard, and pop entries while due <= now. Skip cancelled entries. Execute each action inside its own catch boundary, record succeeded or failed, and continue. A callback attempting to mutate the scheduler is rejected; if it does not handle that exception itself, its task fails.

The injected clock avoids sleeps and wall-clock jitter. It does not simulate CPU duration, thread preemption or real deadlines. All eligible callbacks execute serially and can block the caller indefinitely if their own code blocks.

## 4. Complete model implementation

<!-- BEGIN MODEL -->

```cpp
class VirtualScheduler {
    struct Task { Number due, priority, sequence; std::string id; std::function<void()> action; };
    struct Later {
        bool operator()(const Task& a, const Task& b) const {
            if (a.due != b.due) return a.due > b.due;
            if (a.priority != b.priority) return a.priority < b.priority;
            return a.sequence > b.sequence;
        }
    };
    Number now_ = 0, sequence_ = 0;
    bool running_ = false;
    std::priority_queue<Task, std::vector<Task>, Later> queue_;
    std::map<std::string, std::string> states_;
public:
    void schedule(const std::string& id, Number due, Number priority, std::function<void()> action) {
        require(!running_, "scheduler is running"); require(static_cast<bool>(action), "empty action");
        identifier(id); timeValue(due); require(due >= now_, "task in past");
        require(priority >= 0 && priority <= 1000000, "invalid priority");
        require(states_.count(id) == 0, "duplicate task");
        queue_.push({due, priority, sequence_++, id, std::move(action)}); states_[id] = "scheduled";
    }
    bool cancel(const std::string& id) {
        require(!running_, "scheduler is running");
        identifier(id); auto it = states_.find(id);
        if (it == states_.end() || it->second != "scheduled") return false;
        it->second = "cancelled"; return true;
    }
    std::vector<std::string> advance(Number now) {
        require(!running_, "scheduler is running");
        timeValue(now); require(now >= now_, "time regressed"); now_ = now;
        struct Guard { bool& flag; explicit Guard(bool& f) : flag(f) { flag = true; } ~Guard() { flag = false; } } guard(running_);
        std::vector<std::string> result;
        while (!queue_.empty() && queue_.top().due <= now) {
            auto task = queue_.top(); queue_.pop();
            if (states_.at(task.id) != "scheduled") continue;
            std::string status = "succeeded";
            try { task.action(); } catch (...) { status = "failed"; }
            states_[task.id] = status; result.push_back(task.id + ":" + status);
        }
        return result;
    }
    const auto& states() const { return states_; }
};
```

<!-- END MODEL -->

## 5. Worked command traces

<!-- BEGIN TRACES -->

### T13. Time, priority, then insertion order

**Worked explanation:** Earlier due times win before priority is considered. Equal due times use higher priority, then stable insertion sequence.

Run `python examples/machine-coding/verify.py --trace T13` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
ADD low 5 1 ok
{"ok":true,"result":null}
ADD high 5 9 ok
{"ok":true,"result":null}
ADD tie 5 9 ok
{"ok":true,"result":null}
ADD early 4 0 ok
{"ok":true,"result":null}
ADVANCE 5
{"ok":true,"result":["early:succeeded","high:succeeded","tie:succeeded","low:succeeded"]}
```

**Common trap:** A priority-only heap can run a future task before a due task.

**Interview follow-up:** Why does a comparator need a strict weak ordering?

### T14. Cancelled heap entries are skipped

**Worked explanation:** Cancellation changes authoritative state without searching the heap. A popped tombstone is discarded and the ID remains reserved.

Run `python examples/machine-coding/verify.py --trace T14` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
ADD a 2 0 ok
{"ok":true,"result":null}
CANCEL a
{"ok":true,"result":true}
CANCEL a
{"ok":true,"result":false}
ADVANCE 2
{"ok":true,"result":[]}
ADD a 3 0 ok
{"ok":false,"error":"duplicate task"}
STATE
{"ok":true,"result":{"a":"cancelled"}}
```

**Common trap:** Reusing an ID without generation numbers can revive an obsolete heap entry.

**Interview follow-up:** When would heap compaction become necessary?

### T15. A throwing action does not block later tasks

**Worked explanation:** The runner supplies an action that really throws. The scheduler records failed and continues draining due work, without rerunning completed actions.

Run `python examples/machine-coding/verify.py --trace T15` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
ADD bad 1 0 fail
{"ok":true,"result":null}
ADD good 1 0 ok
{"ok":true,"result":null}
ADVANCE 1
{"ok":true,"result":["bad:failed","good:succeeded"]}
ADVANCE 1
{"ok":true,"result":[]}
STATE
{"ok":true,"result":{"bad":"failed","good":"succeeded"}}
```

**Common trap:** Marking a task successful before invoking it hides execution failure.

**Interview follow-up:** What new states and attempt IDs would retries require?

### T16. Time validation precedes queue mutation

**Worked explanation:** After advancing to 10, a task due at 9 is invalid. A valid task due at the current time runs on the next explicit ADVANCE.

Run `python examples/machine-coding/verify.py --trace T16` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
ADVANCE 10
{"ok":true,"result":[]}
ADD past 9 0 ok
{"ok":false,"error":"task in past"}
ADVANCE 9
{"ok":false,"error":"time regressed"}
ADD now 10 0 ok
{"ok":true,"result":null}
ADVANCE 10
{"ok":true,"result":["now:succeeded"]}
```

**Common trap:** Executing immediately inside ADD creates inconsistent reentrancy semantics.

**Interview follow-up:** How does a real worker wake when a new earliest task is inserted?

<!-- END TRACES -->

## 6. Complexity and retention

For Q queued entries and N retained task IDs, ADD costs O(log Q + log N), ignoring strings and callable costs. CANCEL uses an O(log N) status lookup. ADVANCE popping k entries costs O(k(log Q + log N)) plus action execution and output costs. Cancelled entries still contribute to Q until their due times are drained.

The queue and status map retain separate state. Status storage grows with every accepted unique ID; cancellation does not reclaim an ID. Heap compaction and terminal-state retention policies are legitimate follow-ups, but ID reuse then needs a generation token so an old queued entry cannot execute a new task accidentally.

## 7. Architecture follow-up

A real background-work system needs durable task storage, worker claiming, leases, retries with backoff, dead-letter handling, shutdown and observable attempts. A process may crash after an external side effect but before recording success. The local status map cannot guarantee exactly-once external execution.

Use idempotency at the side-effect boundary and define lease ownership before allowing multiple workers. A periodic job additionally needs recurrence semantics: fixed rate versus fixed delay, missed runs and catch-up limits. None of those extensions are executed here. Bridge to [job schedulers and workers](/docs/system-design/job-scheduler-workers).

## 8. Interview questions with answers

### Q1. Why not sort every time?

A full sort is a useful simple oracle and may be enough at small scale. The heap maintains the next entry incrementally, reducing repeated ordering work as tasks are inserted and drained.

### Q2. Why does priority not override due time?

Priority orders tasks already tied on their due time under this contract. Letting a high-priority future task block an earlier due task would change eligibility and can delay runnable work.

### Q3. Is cancellation an O(1) heap removal?

No heap search is performed. The ordered status map lookup is O(log N); the queued entry becomes a tombstone that will be discarded later, with its normal pop cost.

### Q4. Can cancelled IDs be reused?

Not here. Permanent reservation avoids ambiguity with obsolete heap entries. Reuse needs generation numbers in both the heap and authoritative state, plus a retention policy.

### Q5. What proves callback failure isolation?

The worked trace runs an action that throws before a succeeding action. Direct tests also exercise non-standard exceptions and attempts to schedule, cancel or reenter while running.

### Q6. Why use virtual time?

Tests can hit exact due times without waiting or depending on machine load. The same model can later sit behind a real clock adapter, but that adapter needs separate integration tests.

### Q7. Does succeeded mean a task can never run again after a crash?

Only within the current in-memory object. Restart loses both task and status state. Durable attempts and side-effect idempotency are separate requirements.

### Q8. How should periodic work handle a long pause?

Choose whether to skip, coalesce or replay missed occurrences, and cap catch-up work. The answer depends on the task; issuing every missed email may be wrong while reconciling missed billing periods may be required.

## 9. Practice tasks

- [ ] Add a query for the next due time that skips tombstones. Test an all-cancelled heap.
- [ ] Add retries with an explicit maximum attempt count and backoff. Keep attempt identity separate from logical task identity.
- [ ] Add heap compaction. Show that execution order is unchanged and stale entries cannot revive an ID.
- [ ] Specify graceful shutdown for a worker adapter. Distinguish stop accepting, stop claiming, wait for running work and lease expiration.

Next: [Vending Machine and Exact Change](/docs/machine-coding/vending-machine-and-exact-change).
