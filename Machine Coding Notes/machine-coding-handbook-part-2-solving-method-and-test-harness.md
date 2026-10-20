# Machine Coding Practice — Part 2: Solving Method and Test Harness

**M0: make behavior concrete, then prove the important state transitions.**

## 1. What the interviewer needs to see

A working program should demonstrate requirement understanding, understandable state, deliberate error handling and tests that can catch a plausible bug. A class diagram helps only when it explains how those behaviors are owned. Start with concrete types and add interfaces when an actual interchangeable boundary appears, such as a callback, clock, dispenser or storage adapter.

Atlassian's [engineering guide](https://www.atlassian.com/company/careers/resources/interviewing/engineering) is one public example of an interview process that includes code design and trade-off discussion. This book does not infer a universal round format from that example. Use the language and time limits agreed with the interviewer.

## 2. A six-step solving method

| Step | What to produce | Example |
| --- | --- | --- |
| Clarify | A short contract and excluded scope | Are bookings [start,end)? Is an identical retry accepted? |
| Model | State, IDs, ownership and invariants | Booking ID maps to one assigned room and interval |
| Design API | Inputs, results and errors | MOVE either replaces the booking or leaves the old one |
| Implement | Small compiling core path | Choose a candidate room before changing the map |
| Verify | Success, boundary, failure and history tests | A failed move still exposes the original booking |
| Extend | One justified mechanism per new requirement | Shared storage constraints for concurrent room writers |

For a sixty-minute practice attempt, an example allocation is 8 minutes for scope, 7 for model/API, 30 for implementation, 10 for testing and 5 for explanation. These are practice budgets, not company rules. Compile during implementation, not only when its thirty minutes are over.

## 3. Contract questions that uncover bugs early

Ask about duplicate IDs, empty values, missing entities, tie order, time boundaries, integer units, retry identity, deletion, cancellation, partial failure and retention. When an answer is unavailable, state one reasonable assumption and implement it consistently. Do not silently invent one rule in the code and another in the explanation.

An invariant describes a state that must remain true across accepted operations: no overlapping bookings in a room, nonnegative coin inventory, or a complete correspondence between documents and postings. A precondition describes when an operation may execute. A postcondition describes its result and state change. These are related, but one cannot substitute for another.

The [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-errors) connect error handling to valid object state and scoped resource cleanup. Here domain validation is explicit. Runtime allocation failures are not injected, so do not claim the strong exception guarantee for every multi-container operation.

## 4. Repository layout and reproducibility

| File under examples/machine-coding/ | Role |
| --- | --- |
| common.hpp | Shared standard includes, validation, ASCII command parser and JSON helpers |
| machines.hpp | Eight model classes, independently extracted into the chapters |
| main.cpp | Command adapter; converts parsed input into model calls and JSON |
| api_tests.cpp | Direct C++ tests for callback/reentrancy and validation behavior |
| fixtures.py | Thirty-two authored command traces and expected results |
| verify.py | Compiler invocation, reference histories and recorded observations |
| build_book.py | Inserts exact compiled source sections and recorded traces into authored notes |
| validate_content.py | Audits coverage, source equality, routes and prior-note preservation |
| site-smoke.mjs | Checks production routes, rendered content and scoped search |

All eight models compile in one runner; each invocation chooses one mode and creates fresh in-memory objects. The adapter is separate from each model. This makes command parsing testable without putting CLI syntax into business methods. No third-party C++ library is required.

```powershell
python examples/machine-coding/verify.py
python examples/machine-coding/build_book.py
python examples/machine-coding/validate_content.py
```

The verifier invokes g++ with `-std=c++17 -Wall -Wextra -Wpedantic -Werror -O2`. The [GCC 12.2 warning documentation](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Warning-Options.html) explains these diagnostic options; treating enabled warnings as errors is a compiler check, not proof of runtime correctness. Actual commands and diagnostics are retained in `compile-output.json`. Local executables live in the ignored `.build/` directory.

## 5. Driver protocol

Input is one command per line, at most 4,096 printable ASCII bytes. Space separates tokens. Double-quoted tokens may contain spaces and may be empty; only escaped backslash and escaped double quote are accepted. Tabs, control characters, non-ASCII bytes, malformed quotes and unsupported escapes are rejected. Integer parsing rejects overflow and trailing junk.

Every valid input line produces one JSON response. Success has `ok: true` and `result`, with null for operations that return no value. Domain or parsing rejection has `ok: false` and `error`. The process continues after a rejected line. Wrong mode/argument count exits with status 2 and prints usage/error on stderr.

| Mode | Commands; each displayed argument is required |
| --- | --- |
| kv | SET key value; GET key; ERASE key; BEGIN; COMMIT; ROLLBACK; STATE |
| limiter | INIT limit window; ALLOW key time |
| bus | SUB id topic behavior target; OFF id; PUB topic payload; STATE |
| scheduler | ADD id due priority ok/fail; CANCEL id; ADVANCE time; STATE |
| vending | SELECT item; INSERT denomination; VEND; CANCEL; STATE |
| booking | BOOK id start end people; MOVE id start end people; CANCEL id; STATE |
| search | PUT id text; ERASE id; FIND AND/OR query |
| flags | UPDATE tenant flag version percent; EVAL tenant flag user; BUCKET tenant flag user |

Bus behaviors and scheduler ok/fail actions are test-adapter conveniences. The models accept real callbacks. STATE and BUCKET are diagnostic commands for this harness, not claims about a production public API.

```powershell
@'
BOOK first 10 20 2
BOOK next 20 30 2
STATE
'@ | & ./examples/machine-coding/.build/machines.exe booking
```

The exact output for that behavior is included in T21 of the booking chapter. On a platform without .exe suffix, use the binary name created by verify.py. A g++ compiler supporting C++17 must be available on PATH.

## 6. Shared support code

This is the complete shared header used to compile every listed class. The JSON helpers cover the printable-ASCII values the harness accepts; they are not a general JSON serialization package for arbitrary control characters or Unicode input. Direct API callers must preserve that output scope if they use these helpers.

<!-- BEGIN COMMON -->

```cpp
#pragma once
#include <algorithm>
#include <charconv>
#include <cstdint>
#include <deque>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using Number = std::int64_t;
inline void require(bool condition, const std::string& message) {
    if (!condition) throw std::invalid_argument(message);
}
inline void identifier(const std::string& id) { require(!id.empty(), "empty identifier"); }
inline void timeValue(Number n) { require(n >= 0 && n <= 1000000000000LL, "invalid time"); }
inline std::string json(const std::string& s) {
    std::string out = "\"";
    for (char c : s) { if (c == '\\' || c == '"') out += '\\'; out += c; }
    return out + "\"";
}
inline std::string json(Number n) { return std::to_string(n); }
inline std::string json(bool b) { return b ? "true" : "false"; }
inline std::string json(const std::vector<std::string>& values) {
    std::string out = "[";
    for (const auto& s : values) { if (out.size() > 1) out += ','; out += json(s); }
    return out + ']';
}
inline std::string json(const std::map<std::string, std::string>& values) {
    std::string out = "{";
    for (const auto& [k, v] : values) { if (out.size() > 1) out += ','; out += json(k) + ':' + json(v); }
    return out + '}';
}

// ASCII command format: whitespace tokens or double-quoted strings; only \\ and \" escapes.
inline std::vector<std::string> tokenize(const std::string& line) {
    require(line.size() <= 4096, "line too long");
    for (unsigned char c : line) require(c >= 32 && c <= 126, "ASCII input required");
    std::vector<std::string> out;
    std::size_t i = 0;
    while (i < line.size()) {
        if (line[i] == ' ') { ++i; continue; }
        std::string value;
        if (line[i] == '"') {
            ++i; bool closed = false;
            while (i < line.size()) {
                char c = line[i++];
                if (c == '"') { closed = true; break; }
                if (c == '\\') {
                    require(i < line.size(), "dangling escape"); c = line[i++];
                    require(c == '\\' || c == '"', "invalid escape");
                }
                value += c;
            }
            require(closed && (i == line.size() || line[i] == ' '), "malformed quote");
        } else {
            while (i < line.size() && line[i] != ' ') {
                require(line[i] != '"' && line[i] != '\\', "quote token explicitly");
                value += line[i++];
            }
        }
        out.push_back(value);
    }
    require(!out.empty(), "empty command"); return out;
}
inline Number number(const std::string& s) {
    Number n = 0;
    const auto result = std::from_chars(s.data(), s.data() + s.size(), n);
    require(result.ec == std::errc{} && result.ptr == s.data() + s.size(), "invalid integer");
    return n;
}
inline void arity(const std::vector<std::string>& t, std::size_t n) {
    require(t.size() == n, "wrong arity");
}
```

<!-- END COMMON -->

## 7. Meaningful verification

Test a happy path, an exact boundary, a rejected operation with retained state, and a short history that combines operations. For example, an inner commit followed by outer rollback catches a bug that a standalone SET/GET test cannot.

Use an oracle with a different implementation strategy where practical. The limiter reference scans a full accepted log rather than pruning a deque. The scheduler sorts pending jobs rather than using a heap. Booking uses occupied integer slots for its small random fixture. Search scans original text. Vending enumerates bounded coin combinations rather than copying the DP.

Some reference semantics are necessarily shared, such as the declared hash algorithm or snapshot transaction contract. Agreement is evidence against particular implementation bugs, not a mathematical proof of the contract itself. Fixed hand-authored traces anchor the meaning independently of the generated histories.

The recorded result has 57 named groups, 5,900 checked command responses and 14 direct API assertions. A response count is not 5,900 distinct requirements. The groups and scope boundaries are recorded so the numbers remain interpretable.

## 8. What to say when the scope grows

If asked for threads, identify the shared invariant and the whole operation that must be protected. If asked for multiple servers, identify the shared owner and a storage/coordination mechanism. If asked for durability, describe commit and recovery behavior. If asked for performance, define a workload and measure it before claiming a speedup.

A good extension explanation names the extra failure mode and the mechanism that addresses it. A mutex does not provide persistence, a heap does not provide task durability, and hashing does not authorize access.

Next: [Transactional Key-Value Store](/docs/machine-coding/transactional-key-value-store).
