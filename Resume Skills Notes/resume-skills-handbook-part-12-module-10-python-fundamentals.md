# Resume Skills Placement Handbook — Part 12
# Module 10: Python Fundamentals for Backend Interviews

**Module 10 · 4–5 hours · Tier 1 for Python roles · Requires: M0; M6-M8 help with the application example**

---

## Why this module matters

Python on a resume invites more than syntax questions. You may need to explain why two requests share a list, why an annotated function accepts bad JSON, why an async endpoint blocks unrelated work, or why a worker process cannot see a parent's latest dictionary.

The same language supports web applications, scripts, ingestion pipelines and AI integrations. The backend skill is choosing clear boundaries for values, state, resources and work.

> **Names bind to objects; boundaries establish trust and ownership; scheduling determines when work can progress.**

Use those three ideas to reason through the examples rather than memorizing isolated outputs. This chapter prepares the Python branch before Flask/FastAPI and Django. It includes a small framework-free quote service and a build path for a bounded document-processing system.

**Verification: 44 checks passed: 24 isolated language examples, six concurrency examples and 14 application-boundary checks.** The actual interpreter was **CPython 3.13.15, 64-bit Windows, GIL enabled**, with `Py_GIL_DISABLED=0`. No third-party Python packages are required.

The Python 3.13 documentation currently identifies itself as 3.13.16. The examples were executed on the installed 3.13.15 interpreter; documentation and observed runtime versions are deliberately recorded separately. Other interpreters, free-threaded builds and later versions can differ in implementation details.

### Run the examples

From the repository root:

```powershell
python -X utf8 examples/resume-skills/module-10-python/verify.py
python -X utf8 examples/resume-skills/module-10-python/concurrency/26-bounded-workers.py
python -X utf8 examples/resume-skills/module-10-python/concurrency/30-processes.py
python -X utf8 examples/resume-skills/module-10-python/verify_domain.py
```

Run without `-O`: the verifier refuses optimized mode because some teaching examples contain assertions. Runtime validation in the quote service uses explicit exceptions, so validation does not disappear with assertions.

The verifier executes each snippet in a fresh interpreter, compares stdout with the expected contract, rejects unexpected stderr/nonzero exits, runs the application checks and records the actual results. Workers and event loops are closed before their subprocess exits. Nothing listens on a network port or contacts an external service.

Evidence lives in `examples/resume-skills/module-10-python/`: `cases.json`, `verification-results.json` and `verification-output.txt`.

---

## 10.1 What is Python, and where does it fit?

**Python is a general-purpose programming language. CPython is the interpreter implementation used here. Flask, FastAPI and Django are frameworks written for Python.** A web server/application-server arrangement accepts network traffic and invokes your Python application. Python alone is not a request-routing framework.

```text
Client -> HTTP/reverse proxy -> WSGI or ASGI server -> Python framework
                                                     |
                                                application code
                                              /         |         \
                                         database    job queue    external API
                                                     |
                                                Python worker
```

This is an architectural diagram, not an observation from a deployed project. WSGI/ASGI and framework execution models receive their own treatment in M11.

### Why use Python for a backend?

It offers readable application code, a large library ecosystem, mature web frameworks and close integration with data/AI tools. A team can use the same language across an API, ingestion worker and analysis script.

The trade-offs depend on workload. Object-heavy pure-Python computation can require a different approach from waiting for network responses. Native libraries, processes, batching or another service may be suitable. Measure the real path before attributing latency to the language.

### Is Python interpreted or compiled?

For the CPython path taught here, source is parsed and compiled to a code object containing bytecode, which the interpreter executes. Import machinery can cache compiled module files in `__pycache__`. A `.pyc` cache helps module loading; it does not turn your application into a native executable or remove runtime type behavior. See [Python modules and compiled files](https://docs.python.org/3.13/tutorial/modules.html#compiled-python-files).

Keep four questions separate: language semantics, interpreter implementation, installed version/build, and application architecture. “Python has a GIL” is incomplete without the interpreter/build context.

---

## 10.2 Objects, names, mutation and copying

Assignment binds a name to an object. It does not automatically clone the object. Function arguments establish local parameter bindings to the passed objects. Mutating a shared list is observable by its other users; rebinding the local parameter does not rebind the caller's name. The official FAQ calls argument passing **assignment**: [Python argument passing](https://docs.python.org/3.13/faq/programming.html#how-are-arguments-passed-by-value-or-by-reference).

Draw it before predicting output:

```text
a ----+
      +----> list object ['request']
b ----+

parameter items initially points to the same list.
items.append(...) mutates it.
items = [...] changes only that local binding.
```

**Verified example — Mutation versus local rebinding** (`snippets/01-binding.py`)

```python
def change(items):
    items.append('accepted')
    items = ['local']
a = ['request']
b = a
change(a)
print(a, b, a is b)
x = 4
y = x
x += 1
print(x, y)
```

Actual output:

```text
['request', 'accepted'] ['request', 'accepted'] True
5 4
```

An integer increment creates/reuses an appropriate integer object and rebinds the name; it does not alter the integer seen through another binding. Avoid explaining Python as C++ reference parameters: a function cannot rebind the caller's local variable through an ordinary parameter.

### Shallow copy creates a new outer container

The nested objects remain shared. Deep copying recursively copies supported contained objects, using bookkeeping to handle cycles/shared references. It is not a substitute for deciding ownership, and custom classes can control copying. Database connections, locks and live clients need lifecycle decisions rather than blind cloning. Reference: [copy](https://docs.python.org/3.13/library/copy.html).

**Verified example — Shallow and deep copies** (`snippets/02-copy.py`)

```python
from copy import deepcopy
original = {'tags': ['backend']}
shallow = original.copy()
deep = deepcopy(original)
shallow['tags'].append('python')
shallow['new'] = True
print(original)
print(deep)
print('new' in original, shallow is original)
```

Actual output:

```text
{'tags': ['backend', 'python']}
{'tags': ['backend']}
False False
```

For a request template with a nested list, `template.copy()` can still leak mutations across requests. Prefer constructing request-local state or use immutable representations where appropriate. Deep copy may be expensive and can copy more than intended.

### Immutable container does not imply deeply immutable contents

A tuple cannot replace its stored element references. Its elements can still refer to mutable objects. Augmented assignment may mutate an object and then attempt assignment; the later failure does not roll back the earlier mutation. Reference: [Python expressions](https://docs.python.org/3.13/reference/expressions.html), [compound statements](https://docs.python.org/3.13/reference/compound_stmts.html).

**Verified example — Tuple immutability and augmented assignment** (`snippets/03-tuple.py`)

```python
value = (['a'],)
try:
    value[0] += ['b']
except TypeError:
    print('assignment rejected')
print(value)
try:
    hash(value)
except TypeError:
    print('unhashable')
```

Actual output:

```text
assignment rejected
(['a', 'b'],)
unhashable
```

This is an interview trap with an application lesson: an exception is not an automatic transaction rollback for arbitrary Python mutations. Design the state transition before changing shared state.

---

## 10.3 Equality, identity and collection choices

`==` asks about equality, which classes can define. `is` asks whether two expressions refer to the same object. Use `is None` to test the absence singleton; use `==` for ordinary value comparison. Integer/string interning is not a reliable application contract.

Booleans are an integer subtype. This affects both validation and dictionary/set keys: equal numeric keys represent one entry. Reference: [Python data model](https://docs.python.org/3.13/reference/datamodel.html).

**Verified example — Identity and equality** (`snippets/04-equality.py`)

```python
a = [1]
b = [1]
print(a == b, a is b, a is None)
print(True == 1, isinstance(True, int), type(True) is int)
print(len({True: 'first', 1: 'second', 1.0: 'third'}))
print({True: 'first', 1: 'second', 1.0: 'third'}[1])
```

Actual output:

```text
True False False
True True False
1
third
```

A quantity validator using only `isinstance(value, int)` accepts `True`. If the JSON contract requires an integer and excludes booleans, explicitly enforce that rule. Equality also does not establish identity, ownership or authorization.

### Pick the collection for its job

| Collection | Useful property | Backend example / caution |
| --- | --- | --- |
| `list` | Ordered mutable sequence | Request-local rows; front removals shift elements |
| `tuple` | Fixed element references | Composite lookup key when every component is hashable |
| `dict` | Key/value lookup; insertion order | ID-to-record map; order is not sorted order |
| `set` | Unique hashable elements | Membership/deduplication; no specified iteration order |
| `frozenset` | Immutable set | Fixed permission collection; still check actual grants |
| `deque` | Efficient operations at both ends | In-process FIFO, with explicit synchronization if needed |

Typical built-in list indexing is constant time; membership scans are linear. Dict/set lookup is normally average constant time, with hash/equality cost and collisions affecting behavior. These are data-structure guides, not a latency guarantee or a benchmark from this chapter. A Python deque is not a durable job broker.

**Verified example — Collection operations and stable sort** (`snippets/05-collections.py`)

```python
from collections import deque
items = [3, 1, 2]
print(items.sort(), items)
print(items[-1], items[::2])
queue = deque(['a', 'b'])
print(queue.popleft(), list(queue))
rows = [('first', 2), ('second', 1), ('third', 2)]
print(sorted(rows, key=lambda row: row[1]))
print(sorted(set(['api', 'db', 'api'])))
```

Actual output:

```text
None [1, 2, 3]
3 [1, 3]
a ['b']
[('second', 1), ('first', 2), ('third', 2)]
['api', 'db']
```

The stable sort preserves the original order of rows with equal sort keys. Sorting a set's values explicitly gives deterministic presentation; relying on its incidental iteration order does not. List methods such as `sort` modify the list and return `None`. See [data structures](https://docs.python.org/3.13/tutorial/datastructures.html).

### Hashability and dictionary order

A key needs a stable hash and equality behavior consistent with hashing. A tuple containing a list is unhashable. User-defined instances can be hashable by identity even when their attributes change; “all mutable objects are unhashable” is too broad. Do not mutate fields used by custom hashing/equality while an object is a key.

**Verified example — Hashability and insertion order** (`snippets/06-dict.py`)

```python
data = {'a': 1, 'b': 2}
data['a'] = 3
print(list(data))
del data['a']
data['a'] = 4
print(list(data))
print({('tenant', 7): 'row'}[('tenant', 7)])
try:
    data[[]] = 1
except TypeError:
    print('list key rejected')
```

Actual output:

```text
['a', 'b']
['b', 'a']
row
list key rejected
```

Replacing a value leaves its key's position intact; removing and reinserting moves it to the end. For paginated APIs, insertion order in one process is not a cross-request database ordering contract. Specify query ordering and a stable tie-breaker as in M6.

### Missing, null and false are different cases

**Verified example — Missing, null and false values** (`snippets/07-absence.py`)

```python
MISSING = object()
data = {'limit': 0, 'note': None}
print(data.get('limit') or 20)
print(20 if data.get('limit') is None else data['limit'])
print(data.get('note', MISSING) is None)
print(data.get('unknown', MISSING) is MISSING)
print(bool([]), bool('False'))
```

Actual output:

```text
20
0
True
True
False True
```

`value or default` replaces every false value, including valid zero, empty text and an empty list. Use a specific `None` check when that is the contract. Use a sentinel when missing and explicitly supplied `None` have different meanings. This matters for PATCH requests and optional configuration. Python's truth-value and Boolean-operation rules are documented under [built-in types](https://docs.python.org/3.13/library/stdtypes.html#truth-value-testing).

---

## 10.4 Functions, defaults, scope and closures

### Defaults are evaluated when the function is defined

The same default object can be reused by later calls. A list default is usually a bug for request-local accumulation. Use `None` or a unique sentinel and construct fresh state inside the call. Reference: [default argument values](https://docs.python.org/3.13/tutorial/controlflow.html#default-argument-values).

**Verified example — Default arguments persist across calls** (`snippets/08-defaults.py`)

```python
def bad(value, items=[]):
    items.append(value)
    return items
first = bad('a')
second = bad('b')
print(first, second, first is second)
def good(value, items=None):
    if items is None:
        items = []
    items.append(value)
    return items
print(good('a'), good('b'))
```

Actual output:

```text
['a', 'b'] ['a', 'b'] True
['a'] ['b']
```

The first returned list also changes when the second call appends to that same object. Replacing only the parameter name would have a different effect.

### LEGB is a useful first map

Ordinary function lookup searches local, enclosing function, module-global and built-in scopes. Assignment inside a function normally makes that name local for that function. `nonlocal` refers to an existing enclosing function binding; `global` targets a module binding. Classes and annotation scopes have additional rules, so LEGB is a starting explanation rather than the complete language specification. See [execution model](https://docs.python.org/3.13/reference/executionmodel.html).

**Verified example — Local binding and nonlocal closure** (`snippets/09-scope.py`)

```python
count = 10
def broken():
    count += 1
try:
    broken()
except UnboundLocalError:
    print('local read before binding')
def counter():
    value = 0
    def next_value():
        nonlocal value
        value += 1
        return value
    return next_value
next_value = counter()
print(next_value(), next_value(), count)
```

Actual output:

```text
local read before binding
1 2 10
```

A module-global variable is not shared between unrelated worker processes. A closure can keep a binding alive after its outer function returns, but that does not make the closure thread-safe or persistent.

### Closures capture bindings; they do not automatically snapshot loop values

**Verified example — Late-bound closures and explicit capture** (`snippets/10-closures.py`)

```python
late = [lambda: i for i in range(3)]
early = [lambda i=i: i for i in range(3)]
print([fn() for fn in late])
print([fn() for fn in early])
```

Actual output:

```text
[2, 2, 2]
[0, 1, 2]
```

In the second version, the default expression is evaluated for each lambda creation. This is a useful explicit capture for scalar values. Capturing a mutable object still captures that object, not a deep snapshot. A normal nested function with an explicit parameter is often clearer than a dense lambda.

### Function signatures describe calling rules

**Verified example — Positional-only and keyword-only arguments** (`snippets/11-arguments.py`)

```python
def route(resource, /, *, limit=20, **options):
    return resource, limit, sorted(options)
print(route('orders', limit=5, trace=True))
try:
    route(resource='orders')
except TypeError:
    print('positional-only argument required')
try:
    route('orders', 5)
except TypeError:
    print('limit must be keyword')
```

Actual output:

```text
('orders', 5, ['trace'])
positional-only argument required
limit must be keyword
```

Before `/` are positional-only parameters; after `*` are keyword-only parameters. `*args` collects additional positional arguments into a tuple, and `**kwargs` collects additional keyword arguments into a dict. Unpacking at a call site expands arguments; it does not bypass the function's signature rules.

Keyword-only settings make service calls easier to review: `timeout=...` is clearer than an unexplained positional number. Do not use arbitrary `**kwargs` to silently accept unknown API-body fields.

---

## 10.5 Decorators: functions that transform callables

A decorator receives a callable and returns the object bound to the decorated name. For a simple function, `@trace` corresponds to defining the function and then assigning `total = trace(total)`. A wrapper can add behavior before/after delegation, change arguments or even replace execution entirely.

**Verified example — Decorator wrapping and metadata** (`snippets/12-decorator.py`)

```python
from functools import wraps
calls = []
def trace(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        calls.append(fn.__name__)
        return fn(*args, **kwargs)
    return wrapper
@trace
def total(a, b=2):
    return a + b
print(total(3), total.__name__, calls)
print(total.__wrapped__(4, 5))
```

Actual output:

```text
5 total ['total']
9
```

`functools.wraps` preserves useful metadata and provides `__wrapped__`; it does not automatically validate arguments, preserve all behavior or make a wrapper async-aware. Reference: [functools.wraps](https://docs.python.org/3.13/library/functools.html#functools.wraps).

For an async function, a synchronous wrapper that only creates/returns a coroutine does not measure its awaited execution. An async-aware wrapper must await the wrapped coroutine and handle cancellation appropriately. For authentication decorators, the important question is where identity is established and which execution path can bypass the check.

Stacked decorators apply from the bottom upward. Their runtime wrapper behavior then follows the nesting they constructed. Do not describe decorator order without tracing the actual wrappers.

---

## 10.6 Iterables, iterators, generators and comprehensions

An **iterable** can supply an iterator through `iter(...)`. An **iterator** supplies successive values through `next(...)` and signals exhaustion with `StopIteration`. An iterator's `__iter__` returns itself. Lists can create new iterators for repeated passes; one iterator tracks one advancing position. See [iterators and generators](https://docs.python.org/3.13/tutorial/classes.html#iterators).

**Verified example — Iterable versus one-shot iterator** (`snippets/13-iterator.py`)

```python
values = [1, 2]
it = iter(values)
print(iter(it) is it, next(it))
print(list(it), list(it))
print(list(values), list(values))
try:
    next(it)
except StopIteration:
    print('exhausted')
```

Actual output:

```text
True 1
[2] []
[1, 2] [1, 2]
exhausted
```

This is why passing a generator into a function that first counts it and then processes it can produce no records on the second pass. Either process in one pass, construct a new iterator from a repeatable source, or materialize deliberately within a memory budget.

### A generator suspends its function at yield

Calling a generator function creates a generator object. Its body starts when iteration advances it. Local state survives suspension. Explicitly closing a started generator runs its cleanup path; merely abandoning it is not a portable resource-management plan.

**Verified example — Lazy execution and explicit cleanup** (`snippets/14-generator.py`)

```python
def stream():
    print('start')
    try:
        yield 10
        yield 20
    finally:
        print('cleanup')
gen = stream()
print('created')
print(next(gen))
gen.close()
print(list(gen))
```

Actual output:

```text
created
start
10
cleanup
[]
```

A `break` from an ordinary loop does not by itself promise that every possible iterator's resources close immediately. If a generator owns a file/client, establish an explicit cleanup contract, for example a surrounding context manager or `contextlib.closing`. If a consumer retains the generator, its resources can otherwise remain open.

### Comprehension versus generator expression

**Verified example — Eager lists and lazy generator expressions** (`snippets/15-comprehensions.py`)

```python
seen = []
def mark(x):
    seen.append(x)
    return x * x
eager = [mark(x) for x in range(3)]
print(eager, seen)
seen.clear()
lazy = (mark(x) for x in range(3))
print(seen)
print(next(lazy), seen)
print(sum(lazy), seen)
```

Actual output:

```text
[0, 1, 4] [0, 1, 2]
[]
0 [0]
5 [0, 1, 2]
```

A list comprehension eagerly builds its result. A generator expression generally computes elements as consumed, although its outermost iterable expression is evaluated when the generator expression is created. Laziness reduces materialization when the surrounding pipeline also streams; it does not guarantee constant total memory. A downstream `list(...)` or an unbounded results map can still retain everything. Reference: [generator expressions](https://docs.python.org/3.13/reference/expressions.html#generator-expressions).

For ingestion, distinguish a streaming parser, a bounded batch and a full-file loader. A generator around an already-loaded document does not undo that earlier allocation.

---

## 10.7 Exceptions and deterministic resource cleanup

Use exceptions to communicate failure without silently substituting plausible success values. Catch the types you can handle at the boundary that can decide what to do.

| Construct | Purpose | Common mistake |
| --- | --- | --- |
| `try/except` | Handle a selected failure | Catching everything and returning success |
| `else` | Run after the try body succeeds | Putting unrelated work inside a broad catch |
| `finally` | Cleanup while leaving the block | Returning and hiding an error |
| `raise ... from exc` | Translate while retaining the cause | Losing the diagnostic chain |
| `with` | Enter/exit a resource scope | Assuming every context manager is a transaction |

Reference: [errors and exceptions](https://docs.python.org/3.13/tutorial/errors.html).

**Verified example — Exception translation preserves cause** (`snippets/16-exceptions.py`)

```python
class InvalidQuantity(ValueError):
    pass
def parse(text):
    try:
        return int(text)
    except ValueError as exc:
        raise InvalidQuantity('quantity must be an integer') from exc
try:
    parse('many')
except InvalidQuantity as exc:
    print(str(exc))
    print(type(exc.__cause__).__name__)
```

Actual output:

```text
quantity must be an integer
ValueError
```

The application can map `InvalidQuantity` to its public error contract while logging the cause appropriately. A bare `raise` inside a handler re-raises the active exception. Avoid exposing raw exception tracebacks, SQL or credentials to API clients.

### A context manager is a lifecycle protocol

`with` calls `__enter__` and then `__exit__` when leaving the body. An exit method can suppress an exception by returning a true value. The generator-based `contextmanager` pattern yields once; cleanup belongs in `finally` so it also executes when the body raises. See [contextlib](https://docs.python.org/3.13/library/contextlib.html).

**Verified example — Context cleanup on failure** (`snippets/17-context.py`)

```python
from contextlib import contextmanager
@contextmanager
def resource():
    print('open')
    try:
        yield 'handle'
    finally:
        print('close')
try:
    with resource() as handle:
        print(handle)
        raise ValueError('failed')
except ValueError:
    print('propagated')
```

Actual output:

```text
open
handle
close
propagated
```

This context manager cleans up and lets the error propagate. A database client's transaction context can additionally commit/rollback according to that client's contract. A generic file context simply manages the file; `with` itself does not add database semantics.

Neither `finally` nor `with` guarantees cleanup after forced process termination or power loss. That is a durable-state/recovery problem, as demonstrated in M9. Do not depend on garbage collection for prompt file, cursor or connection release.

**Verified example — Returning from finally hides an error** (`snippets/18-finally.py`)

```python
def broken():
    try:
        raise ValueError('lost')
    finally:
        return 'masked'
print(broken())
```

Actual output:

```text
masked
```

The result hides the original exception. Keep control-flow changes out of cleanup blocks unless suppressing the error is explicitly intended and reviewed. For async resources, `async with` allows asynchronous entry/exit; it does not make blocking code inside the body non-blocking.

---

## 10.8 Classes, dataclasses and interfaces

Classes group state and behavior. Calling an instance method binds the instance as `self`. `classmethod` receives the class and is useful for alternative constructors; `staticmethod` receives neither an automatic instance nor class. Reference: [classes](https://docs.python.org/3.13/tutorial/classes.html).

**Verified example — Class attributes and bound methods** (`snippets/20-classes.py`)

```python
class Service:
    shared = []
    def __init__(self, name):
        self.name = name
    def label(self):
        return self.name
    @classmethod
    def create(cls, name):
        return cls(name)
    @staticmethod
    def valid(name):
        return bool(name)
a, b = Service.create('a'), Service('b')
a.shared.append('visible')
print(b.shared, a.label(), Service.valid(''))
print(a.label.__self__ is a)
```

Actual output:

```text
['visible'] a False
True
```

The class-level list is shared by instances that have not shadowed the attribute. Put per-instance mutable state in `__init__`. This same ownership issue appears with singleton services and module-level caches.

Prefer composition when one object uses another responsibility: a quote service can depend on a catalog interface without inheriting from a database connection. Python supports inheritance and method resolution, but a backend interview often benefits more from explaining boundaries than reciting a hierarchy.

### Dataclasses reduce record boilerplate

A dataclass can generate initialization, representation and equality methods. `default_factory` constructs fresh defaults per instance. `frozen=True` blocks ordinary attribute assignment; it is not deep immutability or input validation. See [dataclasses](https://docs.python.org/3.13/library/dataclasses.html).

**Verified example — Factories and shallow frozen behavior** (`snippets/19-dataclass.py`)

```python
from dataclasses import dataclass, field, FrozenInstanceError
@dataclass(frozen=True)
class Request:
    tags: list[str] = field(default_factory=list)
a, b = Request(), Request()
a.tags.append('changed')
print(a.tags, b.tags)
try:
    a.tags = []
except FrozenInstanceError:
    print('rebinding rejected')
```

Actual output:

```text
['changed'] []
rebinding rejected
```

Choose tuples/frozensets or other carefully designed values for nested data that should resist ordinary mutation. Even a frozen dataclass can hold a live mutable object. Hashability must still match the fields and equality policy.

### Duck typing and protocols

Duck typing means code depends on supported operations rather than requiring one concrete class. A `typing.Protocol` describes such an interface for static tools; it does not implement the behavior or automatically validate an object received over HTTP. A small injected catalog/clock is often enough to test an application service without a framework.

---

## 10.9 Type hints describe a contract; runtime validation establishes it

Useful forms include `list[str]`, `dict[str, int]`, `int | None`, `Literal[...]`, `TypedDict`, `Protocol` and generics that preserve relationships between input/output types. Python is dynamically typed: objects have types, while names can be rebound to other objects. Dynamic typing does not mean arbitrary operations are valid.

Type checkers analyze code; annotations alone do not reject runtime arguments. A `TypedDict` value is an ordinary dict at runtime. See [typing](https://docs.python.org/3.13/library/typing.html).

**Verified example — Annotations do not validate runtime inputs** (`snippets/21-typing.py`)

```python
from typing import TypedDict
class Body(TypedDict):
    quantity: int
def echo(quantity: int) -> int:
    return quantity
body: Body = {'quantity': 'many'}
print(echo(body['quantity']))
print(isinstance(body, dict))
print(echo.__annotations__['quantity'] is int)
```

Actual output:

```text
many
True
True
```

This deliberately violates its annotations and executes successfully. A configured static checker should report the mismatches, but **no static type checker was run for this chapter**. The verified claim is that the interpreter did not enforce the annotations.

The syntax and annotation inspection shown are for the stated Python 3.13 runtime with no postponed-annotation import. Do not generalize annotation-evaluation details across every version/build.

### A backend boundary needs more than field types

| Layer | Question |
| --- | --- |
| Transport | Is the body within limits, correctly encoded and valid JSON? |
| Shape | Is it an object with allowed fields? |
| Value | Is quantity an allowed integer, with booleans excluded? |
| Identity/authorization | Which authenticated principal and tenant may perform the action? |
| Domain | Does the trusted catalog permit this product and compute this price? |
| Persistence | Which invariant must be enforced transactionally? |
| Serialization | Which fields may leave the service? |

A framework validation library can help with the first value/shape rules, but authorization and domain consistency still need explicit decisions. `cast(...)`, a type annotation and a dataclass constructor are not interchangeable with validation.

---

## 10.10 Money, timestamps, Unicode and JSON

Use integer minor units when the business contract supplies a fixed currency/unit and integer precision suffices. Decimal arithmetic is useful for decimal business calculations, with explicit rounding/precision rules. Constructing `Decimal` from a binary float imports its approximation; construct from a validated decimal string when that is the source contract. Reference: [decimal](https://docs.python.org/3.13/library/decimal.html).

Use aware timestamps for instants and an explicit conversion/serialization policy. UTC storage does not define local business-day rules; those need the business timezone and daylight-saving policy. A monotonic clock serves elapsed-time deadlines, while a wall-clock timestamp serves recorded instants. Reference: [datetime](https://docs.python.org/3.13/library/datetime.html).

**Verified example — Money, text bytes and aware timestamps** (`snippets/22-values.py`)

```python
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
import json
print(0.1 + 0.2 == 0.3)
print(Decimal('0.1') + Decimal('0.2') == Decimal('0.3'))
print(Decimal('2.675').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
text = '₹'
raw = text.encode('utf-8')
print(len(text), len(raw), raw.decode('utf-8') == text)
stamp = datetime.fromisoformat('2026-10-14T12:00:00+05:30')
print(stamp.astimezone(timezone.utc).isoformat())
print(json.dumps({'amount_paise': 12500}, sort_keys=True))
```

Actual output:

```text
False
True
2.68
1 3 True
2026-10-14T06:30:00+00:00
{"amount_paise": 12500}
```

The rupee symbol is one code point here and three UTF-8 bytes. A text length is not a byte-size limit or a universal count of visible characters. HTTP receives bytes; decoding must use the agreed encoding. Signatures need the original bytes, as M9 established.

JSON does not directly encode arbitrary Python objects such as a datetime or Decimal with a domain-specific meaning. Select a public representation deliberately. Python's standard decoder also has policies around duplicate keys and non-finite numbers; a strict API may need to override defaults. Reference: [json](https://docs.python.org/3.13/library/json.html).

The quote example rejects duplicate keys and non-finite constants instead of letting different parsers disagree about the request. Decimal rounding is demonstrated separately; the quote calculation uses integer paise and does not claim to implement taxes or every currency's minor-unit rules.

---

## 10.11 Modules, packages and virtual environments

An import loads/initializes a module when needed and binds a module or selected names. Normally a repeated import of the same loaded module name reuses its object from `sys.modules`. Module initialization is code execution, so importing should not unexpectedly start a server or charge a customer. See [modules](https://docs.python.org/3.13/tutorial/modules.html).

The fixture file for the next example contains:

```python
print('module initialized')
label = 'initial'
items = []
```

**Verified example — Imports cache module objects and bind names** (`snippets/23-imports.py`)

```python
import import_fixture
from import_fixture import label, items
import import_fixture as again
import_fixture.label = 'changed'
import_fixture.items.append('row')
print(again is import_fixture, label, again.label, items)
```

Actual output:

```text
module initialized
True initial changed ['row']
```

`from module import label` binds the object selected at that time. Rebinding `module.label` later does not retarget the imported name; mutating the shared list is visible. Imports can expose partial initialization during circular dependencies, so separate domain code from framework startup and keep dependency direction clear.

### Script entry point and spawn

`if __name__ == '__main__':` distinguishes top-level execution from ordinary import. With spawned worker processes, the child imports code in a new interpreter. Guard process-pool creation so importing the module does not recursively start more pools. Keep worker functions importable at module scope, as the process example does.

### Environment is an interpreter plus its dependencies

A virtual environment provides an isolated package installation context. It is not a container, OS boundary or dependency lock by itself. Match the interpreter used to run the program with the interpreter used to install dependencies. See [virtual environments](https://docs.python.org/3.13/tutorial/venv.html).

Optional PowerShell workflow for a separate application; these are setup instructions, not actions performed by the chapter verifier:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip --version
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m your_package
```

Calling the environment's interpreter directly avoids needing shell activation. The requirements file must exist and should be maintained with a reproducibility policy; this module needs no packages and creates no environment. Avoid naming a local file `json.py` or `typing.py` and accidentally shadowing a library module.

---

## 10.12 Memory lifetime: reachability, references and cycles

CPython uses reference counting together with cyclic garbage collection. Removing a name removes one reference; other containers/closures may still retain the object. A self-cycle can remain after the last external strong reference disappears until cyclic collection runs. Other Python implementations need not use the same strategy. Reference: [data model](https://docs.python.org/3.13/reference/datamodel.html), [gc](https://docs.python.org/3.13/library/gc.html).

**Verified example — Collect an unreachable reference cycle explicitly** (`snippets/24-gc.py`)

```python
import gc
import weakref
class Node:
    pass
was_enabled = gc.isenabled()
gc.disable()
try:
    item = Node()
    item.self = item
    ref = weakref.ref(item)
    del item
    print(ref() is not None)
    gc.collect()
    print(ref() is None)
finally:
    if was_enabled:
        gc.enable()
```

Actual output:

```text
True
True
```

The test temporarily disables automatic cyclic collection, creates an unreachable cycle, observes it through a weak reference, explicitly collects and restores the previous setting. It avoids asserting exact reference counts, object addresses, collection-generation counts or RSS changes. A weak reference observes without keeping this object alive: [weakref](https://docs.python.org/3.13/library/weakref.html).

A process retaining a huge cache still has reachable objects; calling `gc.collect()` is not a fix for its retention policy. Removing objects also does not promise immediate return of all allocated memory to the OS. Bound caches and understand who owns references. For connections/files, explicit lifecycle scopes remain the practical rule.

---

## 10.13 Asyncio: cooperative progress, not automatic parallel execution

An `async def` call creates a coroutine object. Its body runs when awaited or scheduled as a task. `asyncio.run` manages a top-level event loop for a standalone program; framework code normally runs within a server-managed loop and should not create a nested one.

A task advances until it completes, raises or suspends on an awaitable that needs to wait. Other ready tasks can then advance on that loop's thread. An `await` is not guaranteed to suspend if its awaitable completes immediately. Reference: [coroutines and tasks](https://docs.python.org/3.13/library/asyncio-task.html).

**Verified example — Coroutine creation, scheduling and blocking calls** (`concurrency/25-async-lifecycle.py`)

```python
import asyncio
import time
async def main():
    events = []
    async def worker():
        events.append('start')
        await asyncio.sleep(0)
        events.append('done')
        return 7
    coro = worker()
    print(events)
    task = asyncio.create_task(coro)
    print(await task, events)
    events.clear()
    asyncio.get_running_loop().call_soon(events.append, 'tick')
    async def blocks():
        time.sleep(0.01)  # Deliberate blocking example; no timing claim.
        events.append('blocking call returned')
    await blocks()       # No suspension inside blocks().
    events.append('caller continued')
    await asyncio.sleep(0)
    print(events)
    from threading import get_ident
    loop_thread = get_ident()
    thread_id = await asyncio.to_thread(get_ident)
    print('thread offload:', thread_id != loop_thread)
asyncio.run(main())
```

Actual output:

```text
[]
7 ['start', 'done']
['blocking call returned', 'caller continued', 'tick']
thread offload: True
```

Trace the second half carefully: the scheduled callback cannot run while `time.sleep` blocks the loop thread. Awaiting `blocks()` does not help because that coroutine never suspends. `asyncio.sleep(0)` finally permits another turn. The output demonstrates ordering, not a latency benchmark.

`asyncio.to_thread` invokes a callable on a thread, as the thread-identity check demonstrates. It can keep blocking I/O away from the loop, but a shared thread pool has finite resources. Cancellation of the awaiter does not forcibly stop a callable already running in its thread. Native libraries may have their own thread/connection safety requirements.

For CPU-heavy pure-Python work on this GIL-enabled build, moving work to a thread does not generally provide multicore Python-bytecode execution. It can still contend for the GIL. A process pool, native implementation or durable worker may be more appropriate.

### Bound both active work and queued work

Creating a task for every item and adding a semaphore bounds simultaneous entry into a region, but all those task objects may already exist. A large ingestion source needs a bounded producer/consumer design and an explicit policy for retained results.

**Verified example — Bounded queue and fixed async worker count** (`concurrency/26-bounded-workers.py`)

```python
import asyncio
async def main():
    queue = asyncio.Queue(maxsize=3)
    gate = asyncio.Event()
    active = peak = max_queued = 0
    results = {}
    async def producer():
        nonlocal max_queued
        for value in range(8):
            await queue.put(value)
            max_queued = max(max_queued, queue.qsize())
        for _ in range(3):
            await queue.put(None)
    async def worker():
        nonlocal active, peak
        while True:
            value = await queue.get()
            try:
                if value is None:
                    return
                active += 1
                peak = max(peak, active)
                if active == 3:
                    gate.set()
                try:
                    await gate.wait()
                    await asyncio.sleep(0)
                    results[value] = value * value
                finally:
                    active -= 1
            finally:
                queue.task_done()
    async with asyncio.TaskGroup() as group:
        group.create_task(producer())
        for _ in range(3):
            group.create_task(worker())
    await queue.join()
    assert active == 0 and queue.empty()
    assert results == {x: x * x for x in range(8)}
    assert peak == 3 and max_queued <= 3
    print('jobs:', len(results), 'peak:', peak, 'queued:', max_queued)
async def bounded_run():
    await asyncio.wait_for(main(), timeout=5)
asyncio.run(bounded_run())
```

Actual output:

```text
jobs: 8 peak: 3 queued: 3
```

There are exactly three worker tasks and one producer task. The queue can hold at most three waiting items. The first three active jobs wait at a gate so the test actually reaches three simultaneous in-flight jobs; later progress uses async suspension. This is deterministic coordination, not a claim about scheduler fairness or network throughput.

The sample retains eight results in a dictionary so assertions can compare them. For an unbounded stream, persist or emit each result instead of growing that dictionary. A queue capacity of three plus three workers can retain queued and active jobs separately; “queue length three” does not mean only three total jobs exist.

`asyncio.Queue` is an in-process, event-loop-oriented primitive, not a cross-thread/process broker or restart-safe job store. Reference: [asyncio queues](https://docs.python.org/3.13/library/asyncio-queue.html).

### TaskGroup makes task lifetime a scope

TaskGroup waits for its tasks. When a task fails with an ordinary error, it cancels remaining group tasks and aggregates failures after cleanup. Cancellation and special base exceptions have distinct rules; do not replace the documentation with “every exception behaves identically.” See [TaskGroup](https://docs.python.org/3.13/library/asyncio-task.html#task-groups).

**Verified example — TaskGroup cancels siblings and waits for cleanup** (`concurrency/27-taskgroup.py`)

```python
import asyncio
async def main():
    started = asyncio.Event()
    cleaned = []
    async def peer():
        try:
            started.set()
            await asyncio.Event().wait()
        finally:
            cleaned.append('peer')
    async def fail():
        await started.wait()
        raise ValueError('provider failed')
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(peer())
            group.create_task(fail())
    except* ValueError as errors:
        print('failures:', len(errors.exceptions))
    print('peer cleaned:', cleaned == ['peer'])
asyncio.run(main())
```

Actual output:

```text
failures: 1
peer cleaned: True
```

The failing task waits until its peer is running, so cleanup is actually exercised. `except*` handles matching members of an exception group. Contrast with default `asyncio.gather` behavior: its first propagated exception does not automatically mean every other supplied task has been cancelled. Choose failure semantics deliberately and account for tasks you start.

### Deadlines request cancellation; they do not reverse effects

**Verified example — Timeout cancellation runs finally** (`concurrency/28-timeout.py`)

```python
import asyncio
async def main():
    cleaned = []
    async def wait_forever():
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.append(True)
    try:
        async with asyncio.timeout(0.02):
            await wait_forever()
    except TimeoutError:
        print('timed out')
    print('cleaned:', cleaned == [True])
asyncio.run(main())
```

Actual output:

```text
timed out
cleaned: True
```

The cleanup executes because the suspended coroutine receives cancellation and unwinds. A CPU loop or blocking call that never yields can delay cancellation and the timeout handler. Do not swallow `CancelledError` and continue indefinitely; cleanup should normally allow cancellation to propagate.

The deadline here is a local event-loop timer. A remote request might already have committed before the caller times out. Local cancellation is not a refund, transaction rollback, thread kill or proof of remote failure. Reuse M9's idempotency/reconciliation reasoning.

---

## 10.14 Threads, processes and the GIL

Concurrency means work can overlap in progress; parallelism means execution can occur simultaneously. Async tasks, OS threads and processes offer different scheduling and memory boundaries.

| Mechanism | State/lifecycle | Useful fit | Important limit |
| --- | --- | --- | --- |
| Async tasks | Usually one loop thread; cooperative suspension | Many compatible network waits | Blocking work stalls that loop |
| Threads | Shared process memory; OS scheduling | Blocking I/O libraries; native operations | Shared-state races; GIL context matters |
| Processes | Separate address spaces/interpreters | CPU-heavy independent Python work | Startup, serialization, IPC and memory cost |
| Durable jobs | External persisted ownership/retry state | Work that must survive an API process | Requires idempotency, retries and recovery design |

The final row is an application architecture choice, not another Python execution primitive.

### What the GIL means in this chapter

In the tested conventional CPython build, the GIL permits one thread at a time to execute Python bytecode in a given interpreter. I/O and native extensions can release it. That does not mean the OS process has one thread or that all native work is serialized. See [threading and the GIL](https://docs.python.org/3.13/library/threading.html#gil-and-performance-considerations).

Python 3.13 also offers an optional experimental free-threaded CPython build. Build capability and current GIL state are separate questions; incompatible extension imports can affect GIL behavior. This chapter did not install or benchmark a free-threaded build. Use its [free-threading guide](https://docs.python.org/3.13/howto/free-threading-python.html) before making deployment claims.

### The GIL is not a business lock

**Verified example — GIL does not make a read-modify-write transaction** (`concurrency/29-threads.py`)

```python
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
barrier = Barrier(2, timeout=5)
state = {'value': 0}
def unsafe():
    old = state['value']
    barrier.wait()  # Both threads read before either writes.
    state['value'] = old + 1
with ThreadPoolExecutor(max_workers=2) as pool:
    jobs = [pool.submit(unsafe) for _ in range(2)]
    for job in jobs:
        job.result(timeout=10)
print('unsynchronized:', state['value'])
state['value'] = 0
lock = Lock()
def safe():
    for _ in range(1000):
        with lock:
            state['value'] += 1
with ThreadPoolExecutor(max_workers=2) as pool:
    jobs = [pool.submit(safe) for _ in range(2)]
    for job in jobs:
        job.result(timeout=10)
print('locked:', state['value'])
```

Actual output:

```text
unsynchronized: 1
locked: 2000
```

Both threads read the old value before either writes because the barrier forces that interleaving. The result loses an increment even with the GIL enabled. This does not depend on hoping a particular bytecode gets interrupted during a tight loop.

The second path locks the whole update. A lock protecting one field does not protect a larger invariant unless every relevant read/write participates. Do not hold a blocking thread lock across arbitrary async awaits. Use loop-appropriate synchronization for tasks, thread locks for shared threads, and database transactions/constraints for state shared across processes or hosts. See [async synchronization](https://docs.python.org/3.13/library/asyncio-sync.html).

### Explicit spawned processes

**Verified example — Explicit spawn, picklable worker and copied arguments** (`concurrency/30-processes.py`)

```python
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
def squares(n):
    return os.getpid(), sum(x * x for x in range(n))
def append_copy(values):
    values.append('child')
    return values
if __name__ == '__main__':
    context = multiprocessing.get_context('spawn')
    original = ['parent']
    with ProcessPoolExecutor(max_workers=2, mp_context=context) as pool:
        rows = list(pool.map(squares, [5, 9]))
        copied = pool.submit(append_copy, original).result(timeout=10)
    assert all(pid != os.getpid() for pid, value in rows)
    assert original == ['parent'] and copied == ['parent', 'child']
    print('method:', context.get_start_method())
    print('results:', [value for pid, value in rows])
    print('parent:', original, 'child:', copied)
```

Actual output:

```text
method: spawn
results: [30, 204]
parent: ['parent'] child: ['parent', 'child']
```

The test uses the spawn context explicitly and checks that execution occurs in a different process. The parent list remains unchanged; the child's modified copy is returned explicitly. It does not assert which of the two worker slots ran each task or claim a speedup.

Workers and transported arguments/results must meet the executor's serialization/importability requirements. Passing a lambda, closure, open connection or huge document graph can be unsuitable. Startup and IPC costs can dominate small jobs. The context manager closes the executor before the program exits. Reference: [ProcessPoolExecutor](https://docs.python.org/3.13/library/concurrent.futures.html#processpoolexecutor), [multiprocessing programming guidelines](https://docs.python.org/3.13/library/multiprocessing.html#programming-guidelines).

Choose based on the actual bottleneck: waiting for a remote API, running Python code, invoking a native library, or surviving process failure. “Use async everywhere” and “use processes everywhere” both omit essential constraints.

---

## 10.15 Build a small application boundary: trusted quote calculation

Before adding Flask/FastAPI routing, isolate a request's meaning from the framework. This example accepts raw UTF-8 JSON bytes, constructs a validated request record, uses a trusted principal and catalog, and produces an explicit public response.

```text
raw bytes -> parse/validate -> QuoteInput ----+
                                            |
trusted Principal -> tenant-scoped catalog -> make_quote -> Quote
                                                          |
                                                public_response -> JSON bytes
```

The principal is a **local trusted fixture**, not authentication derived from the body. In a web application, middleware/dependencies must establish it from a verified session/token. A body cannot select its own tenant.

### Invariants and contracts

| Boundary | Rule |
| --- | --- |
| Body | At most 4,096 bytes; strict UTF-8 and valid JSON |
| Shape | Exactly product_id and quantity; duplicate keys rejected |
| Quantity | An actual int, excluding bool, from 1 through 100 |
| Product | Nonempty bounded string; lookup scoped to trusted tenant |
| Price | Taken from server-owned catalog; integer paise, INR fixture |
| Time | Injected aware timestamp, normalized to UTC |
| Response | Explicit field allowlist; no internal cost, tenant or user field |

The 4,096-byte limit is a fixture policy. A real HTTP adapter also needs streaming read limits, media-type checks, deadlines and error mapping. Applying a byte check after a complete HTTP read does not prevent earlier transport allocation.

### Complete implementation: quote_service.py

This is the same source imported by the verifier. The internal service expects the validated request from `parse_body` and a trusted principal; constructing `QuoteInput` directly from arbitrary values does not validate them. Keep every external entry path behind its validation/authentication boundary.

```python
"""Pure application boundary; no framework, persistence or authentication."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json

class InvalidRequest(ValueError):
    pass

class ProductNotFound(LookupError):
    pass

@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str

@dataclass(frozen=True)
class QuoteInput:
    product_id: str
    quantity: int

@dataclass(frozen=True)
class Price:
    amount_paise: int
    currency: str
    internal_cost_paise: int

@dataclass(frozen=True)
class Quote:
    tenant_id: str
    product_id: str
    quantity: int
    total_paise: int
    currency: str
    created_at: datetime

# Trusted local fixtures, scoped by tenant. No client-provided price.
CATALOG = {
    ('alpha', 'basic'): Price(12500, 'INR', 7000),
    ('beta', 'team'): Price(25000, 'INR', 14000),
}

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidRequest('duplicate JSON key')
        result[key] = value
    return result

def reject_constant(value):
    raise InvalidRequest('non-finite JSON number')

def parse_body(raw: bytes) -> QuoteInput:
    if len(raw) > 4096:
        raise InvalidRequest('body too large')
    try:
        body = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidRequest('invalid UTF-8 JSON') from exc
    if type(body) is not dict or set(body) != {'product_id', 'quantity'}:
        raise InvalidRequest('expected product_id and quantity only')
    product_id, quantity = body['product_id'], body['quantity']
    if type(product_id) is not str or not 1 <= len(product_id) <= 80:
        raise InvalidRequest('invalid product_id')
    if type(quantity) is not int or not 1 <= quantity <= 100:
        raise InvalidRequest('quantity must be an integer from 1 to 100')
    return QuoteInput(product_id, quantity)

def make_quote(principal: Principal, request: QuoteInput, *, now: datetime) -> Quote:
    # principal comes from trusted authentication middleware in a later module.
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('clock must supply an aware timestamp')
    price = CATALOG.get((principal.tenant_id, request.product_id))
    if price is None:
        raise ProductNotFound('product not found')
    return Quote(principal.tenant_id, request.product_id, request.quantity,
                 price.amount_paise * request.quantity, price.currency,
                 now.astimezone(timezone.utc))

def public_response(quote: Quote) -> bytes:
    # Explicit allowlist; dataclasses.asdict is not an API disclosure policy.
    body = {'product_id': quote.product_id, 'quantity': quote.quantity,
            'total_paise': quote.total_paise, 'currency': quote.currency,
            'created_at': quote.created_at.isoformat()}
    return json.dumps(body, sort_keys=True, allow_nan=False).encode('utf-8')
```

### Request trace

1. The bytes represent product `basic` and quantity 2.
2. Parsing rejects ambiguous keys, wrong shape and invalid value types.
3. The trusted fixture principal selects tenant `alpha`.
4. Only `('alpha', 'basic')` is considered in the catalog.
5. Its trusted unit price is multiplied by the validated quantity.
6. Serialization selects public fields and formats the UTC instant.

Actual public response recorded by the verifier, formatted here for readability:

```json
{
  "created_at": "2026-10-14T06:30:00+00:00",
  "currency": "INR",
  "product_id": "basic",
  "quantity": 2,
  "total_paise": 25000
}
```

A request containing a forged price or tenant fails the exact-field rule. Asking for tenant beta's product through the alpha principal fails the scoped catalog lookup. A boolean quantity fails despite being an integer subclass. The tests also check valid boundary quantities, non-UTC clock normalization, duplicate keys, invalid encoding, missing/extra fields and an oversized body.

### What this example establishes

It verifies language-level validation, trusted lookup and response projection using local fixtures. It does not persist a quote, reserve inventory, authorize a purchase, authenticate a real client, send HTTP traffic, or guarantee a price remains valid later. A checkout needs a durable server-side order/quote policy, currency/rounding rules and payment verification; connect to M9 and later database modules.

The catalog is a module-level read fixture. Production updates/shared state need a proper ownership/persistence design; a mutable global dictionary is not a multi-process database.

---

## 10.16 Architectural understanding: a document-processing backend

This is a **design/build exercise**, not an implemented or benchmarked resume project. It connects Python fundamentals to ingestion and AI systems without pretending a few async tasks are a durable pipeline.

### Start with the requirement

An authenticated user submits a document; the system extracts text, divides it into chunks, calls an external embedding API and records searchable results. Jobs may take longer than an HTTP deadline and must be isolated by tenant. A retry must not silently create duplicate durable records.

```text
Client -> authenticated upload API -> object storage + job record
                                               |
                                      durable job delivery
                                               |
                                             worker
                                               |
                               validate format/size/tenant
                                               |
                            parser / CPU extraction process
                                               |
                              streaming chunks, bounded batches
                                               |
                            bounded async embedding requests
                                               |
                            tenant-scoped result persistence
                                               |
                               job completion/failure status
```

The queue, storage and persistence choices remain to be implemented in later modules. This diagram is a proposed architecture, with the language/concurrency pieces illustrated by this chapter's runnable examples.

### A practical build order

| Step | Build | Verify before extending |
| --- | --- | --- |
| 1 | Pure chunk transformation with explicit input/output | Empty input, Unicode, limits, repeatability |
| 2 | Generator-based reading and bounded batches | Source is actually streamed; consumer does not retain all rows |
| 3 | Async provider adapter with deadlines | Failure, cancellation and response validation |
| 4 | Fixed workers plus bounded queue | Active requests and queued work remain bounded |
| 5 | Separate CPU extraction where justified | Spawn/importability, serialization, worker failures |
| 6 | Durable job and result records | Atomic state transitions, idempotent writes, tenant ownership |
| 7 | API/status routes and deployment | Authentication, restart recovery, observability |

### Trace one failure before discussing scale

Suppose embeddings are stored, then the worker stops before acknowledging its job. The broker may redeliver it. The next worker needs a durable key such as a tenant/document-version/chunk/model tuple and a consistent upsert/completion policy. A Python set containing processed IDs is lost on restart and is not shared across worker processes.

Cancellation while waiting for the provider does not establish that the provider did no work. Persist enough progress to reconcile/retry under the provider's contract. M9's uncertain-outcome and idempotency lessons apply even though the transport and domain differ.

### Common bottlenecks and fixes to investigate

| Observation | Hypothesis to verify | Possible response |
| --- | --- | --- |
| Every API request pauses during parsing | CPU/blocking work on API loop | Isolate extraction; enforce input budgets |
| Memory grows with file size | Eager loading or retained tasks/results | Stream where supported; bound batches and task creation |
| Provider returns throttling errors | Concurrency exceeds contract | Bound concurrency; backoff/retry with deadlines |
| Jobs disappear after restart | In-memory ownership only | Durable queue/state and recovery |
| Duplicate rows after redelivery | Missing durable uniqueness | Business idempotency key and atomic update |
| Two tenants see the same chunks | Incomplete ownership filtering | Tenant binding on job, storage and retrieval paths |

These are hypotheses/design responses, not measured causes from this repository. The lesson is to select the boundary that owns the problem before adding another library.

---

## 10.17 Resume connection and choice defence

Your syllabus maps Python to backend frameworks and AI/ingestion work. This chapter provides the language foundation for those areas; it does not establish which concurrency strategy any particular resume project actually used.

A defensible explanation follows a concrete path:

- State what your Python process received and returned.
- Identify trusted identity, validation and serialization boundaries.
- Explain which work waited for I/O and which performed computation.
- Identify mutable state and whether it was request-local, process-local or durable.
- Describe failure handling and evidence from actual code/tests.
- Give the alternative you considered and the requirement that decided it.

If the project code used a synchronous client, say so. Then discuss async adaptation or thread offload as a proposed improvement, with its constraints. Do not claim a process pool, durable queue or measured speedup merely because it appears in these notes.

### Python versus the JavaScript stack already studied

| Topic | Python here | JavaScript/Node connection |
| --- | --- | --- |
| Language/runtime | Python / CPython | JavaScript / Node.js with V8 |
| Type checking | Optional static tooling; annotations not input validation | TypeScript compilation not input validation |
| Coroutine invocation | Async call creates coroutine; scheduling/awaiting runs it | JS async function starts and returns a Promise |
| Blocking | Synchronous work blocks its current thread | Synchronous JS blocks its event-loop thread |
| Shared mutation | Lists/dicts can be aliased | Objects/arrays can be aliased |
| Worker memory | Processes isolate ordinary objects | Node processes/worker threads have distinct transfer/share rules |

Do not transfer exact JavaScript microtask-ordering rules to asyncio. Carry over the questions about ownership, waiting, cancellation and failure instead.

---

## 10.18 Must remember

1. Binding a name, mutating an object and copying a graph are different operations.
2. Tuple/frozen dataclass immutability can still leave nested mutable contents.
3. `is` tests identity; `==` tests equality. Booleans can pass an integer instance check.
4. A missing field, explicit null and valid zero need separate policy.
5. Mutable defaults and class/module containers can leak state across calls or instances.
6. A generator is lazy and usually one-shot; the full pipeline decides memory usage.
7. An exception does not undo earlier Python mutations or remote effects.
8. Context managers establish cleanup contracts; garbage collection is not a deadline.
9. Type hints, dataclasses and runtime validation perform different jobs.
10. Async syntax does not offload blocking work or automatically bound task creation.
11. The GIL depends on implementation/build and does not protect business invariants.
12. Process workers need explicit data transfer and lifetime; in-memory state is not durable ownership.

---

## 10.19 Common wrong answers

| Wrong answer | Better explanation |
| --- | --- |
| Python passes every argument by C++ reference | Parameters bind passed objects; local rebinding does not rebind caller variables |
| Assignment copies the object | It normally creates another binding to that object |
| A tuple cannot change anything inside it | Its element references are fixed; nested mutable objects can change |
| `is` is a faster equality operator | It asks a different question: identity |
| Dicts are sorted | They preserve insertion order; sorting is explicit |
| A set gives deterministic display order | Its iteration order is not the presentation contract |
| `or default` only handles missing values | It replaces all false values, including valid zero |
| Default lists are fresh for every call | The default object is created at function definition |
| A decorator is just an annotation | It executes a transformation and can replace behavior |
| A generator makes the whole pipeline constant-memory | Upstream loading/downstream retention still matter |
| A frozen dataclass validates JSON and is deeply immutable | Neither claim follows from `frozen=True` |
| Type hints reject wrong HTTP input | Runtime parsing/value/auth rules must establish the contract |
| `with` always rolls back errors | Behavior depends on the context manager |
| `async def` makes any function non-blocking | Its synchronous code still runs on the executing thread |
| A semaphore prevents creation of too many tasks | It limits a protected region; task creation may already be unbounded |
| The GIL makes updates safe | Compound invariants still need coordination |
| Python threads can never run anything in parallel | Native work/GIL release and free-threaded builds require context |
| Processes share the parent's mutable dict | Ordinary arguments cross a serialization/address-space boundary |
| A timeout proves the provider failed | Remote outcome can remain uncertain |
| An in-memory queue survives a restart | Durable ownership needs external persistence/recovery |

---

## 10.20 Interview Q&A

These are selected fundamentals and follow-ups for the resume's Python branch, not a measured ranking of company questions. Answer the mechanism first, then give the relevant example.

**Q1. What is Python, and how is it different from CPython or FastAPI?**

Python is the language; CPython is one implementation that executes it; FastAPI is a web framework used by an application. The server/framework and business code have separate responsibilities.

**Follow-up:** Draw where the network connection, route, runtime and database sit.

**Q2. Is Python compiled or interpreted?**

CPython compiles source into code objects/bytecode and executes them through its interpreter. Calling it only interpreted omits that compilation step; calling its bytecode a native executable is also misleading.

**Follow-up:** What does a cached .pyc file improve?

**Q3. How are arguments passed?**

Parameters bind to the passed objects. Mutating a shared mutable object can affect the caller's view; rebinding the local parameter does not rebind the caller's variable.

**Follow-up:** Trace snippet 01 before running it.

**Q4. Shallow copy versus deep copy?**

A shallow copy duplicates the outer structure while retaining references to nested objects. Deep copying recursively copies supported contents with bookkeeping. Choose according to ownership; a live client is not just another value to clone.

**Follow-up:** Why can a copied request template still leak tags?

**Q5. Can an immutable tuple contain mutable data?**

Yes. The tuple's element references are fixed, while an element can refer to a list that changes. Such a tuple may also be unhashable.

**Follow-up:** Why did augmented assignment raise after mutating the list?

**Q6. When should you use is instead of ==?**

Use identity when you need the same object, commonly `is None` or a unique sentinel. Use equality for value comparisons. Interning is not an application correctness rule.

**Follow-up:** Can a class customize equality?

**Q7. Why can True be accepted as an integer quantity?**

Bool is an int subtype, so an integer instance check includes it. Enforce the exact API rule, such as an actual int within a range, with booleans excluded.

**Follow-up:** Why do True, 1 and 1.0 occupy one dict key position?

**Q8. How would you choose list, tuple, dict, set or deque?**

Choose by ordering, lookup, uniqueness, mutation and end-operation requirements. A set suits membership; a dict maps IDs to values; a deque suits local FIFO operations. Include memory/lifecycle and persistence constraints.

**Follow-up:** Why is an in-memory deque insufficient for restart-safe jobs?

**Q9. Are dictionaries sorted? Are sets ordered?**

Dicts preserve insertion order, which differs from sorted order. Sets have no specified iteration order for a presentation contract. Sort explicitly when deterministic display is required.

**Follow-up:** What happens when a dict key is removed and reinserted?

**Q10. What is wrong with value or default for an optional field?**

It replaces every false value, including valid zero and empty values. Use a None check or sentinel according to the contract for absence versus explicit null.

**Follow-up:** How would you model a PATCH that clears a field?

**Q11. Why are mutable default arguments dangerous?**

The default is evaluated once at definition and can be reused across calls. Create a new request-local container inside the function when the caller supplies no value.

**Follow-up:** Why does the first returned list change after a later call?

**Q12. Explain scope, global and nonlocal.**

Ordinary function lookup follows local, enclosing function, module-global and built-in scopes. A local assignment affects binding rules for the whole function. Global targets the module namespace; nonlocal targets an existing enclosing function binding.

**Follow-up:** Does a global dict synchronize multiple worker processes?

**Q13. Why do lambdas in a loop often return the same final value?**

They refer to the same enclosing binding when invoked later. A default argument can capture the current value at function creation, or use a helper with an explicit argument.

**Follow-up:** Does capturing a list create a deep snapshot?

**Q14. What is a decorator, and why use wraps?**

A decorator transforms a callable/object bound to a name. A wrapper can intercept execution; wraps preserves useful metadata and an unwrapping link. It does not automatically handle async execution correctly.

**Follow-up:** Where should an async timing wrapper await the function?

**Q15. Iterable versus iterator versus generator?**

An iterable supplies an iterator; an iterator advances through next and becomes exhausted. A generator is a particular iterator whose function suspends at yield. A list can supply fresh iterators; a particular generator is normally one-shot.

**Follow-up:** What happens if you count and then process the same iterator?

**Q16. Do generators guarantee constant memory?**

They can avoid materializing generated values, but the source may already be loaded and the consumer may retain everything. Bound the complete pipeline, not only one expression.

**Follow-up:** Identify where the bounded worker sample still stores all results.

**Q17. How do you handle an exception without losing its cause?**

Catch the error you can translate and raise the domain error from the original exception. Handle/log at an appropriate boundary and keep internal details out of public responses.

**Follow-up:** Why can return inside finally hide an error?

**Q18. What does with guarantee?**

It invokes the context manager's entry/exit protocol for the lexical scope, including ordinary exception unwinding. Cleanup/suppression/transaction behavior belongs to that manager. Forced termination can bypass normal cleanup.

**Follow-up:** How does a file context differ from a database transaction context?

**Q19. What do dataclasses and frozen=True provide?**

They reduce record boilerplate; frozen blocks ordinary field assignment. A default factory avoids sharing one mutable default. Nested mutability, input validation and authorization remain separate concerns.

**Follow-up:** Why can a frozen dataclass's list still change?

**Q20. Are Python type hints runtime validation?**

No. Static tools inspect them, and some frameworks/libraries use them to drive validation, but annotations by themselves do not reject arbitrary runtime values. Parse and validate external data explicitly.

**Follow-up:** Is TypedDict a distinct runtime dictionary class?

**Q21. How would you represent money and timestamps in an API?**

Define currency/unit/rounding first. Use integer minor units where appropriate or Decimal with explicit policy. Record aware instants and choose an explicit serialized timezone/format; local business dates need additional timezone rules.

**Follow-up:** Why does Decimal constructed from a float retain an approximation?

**Q22. What happens during import, and why guard main?**

Module initialization executes code and ordinary repeated imports reuse the loaded module. Guard startup so import does not run a server or create another process pool. Spawned children need safe importable worker code.

**Follow-up:** Why does rebinding module.label not retarget a from-imported name?

**Q23. What problem does a virtual environment solve?**

It separates an interpreter's project package context. Use that interpreter for installation and execution, with a maintained dependency policy. It does not provide OS isolation or automatically lock versions.

**Follow-up:** How do you diagnose pip installing into the wrong Python?

**Q24. How does CPython reclaim memory?**

Reference counting and cyclic collection participate in object lifetime on this implementation. Reachable caches remain live. Do not depend on immediate finalization for resources or assume collection immediately reduces OS memory usage.

**Follow-up:** What did the weak-reference cycle test actually establish?

**Q25. What happens when you call an async function?**

It creates a coroutine object. Awaiting/scheduling it runs its body; tasks cooperate through suspension on the event loop. Merely constructing the coroutine does not execute the function body.

**Follow-up:** How does this differ from a JavaScript async function invocation?

**Q26. Why can an async endpoint block unrelated requests?**

It still executes synchronous work on its thread. A blocking client or CPU loop prevents that event loop from advancing other tasks. Use a compatible async client, bounded thread offload for appropriate blocking I/O, or a suitable CPU/durable worker boundary.

**Follow-up:** Does cancelling to_thread kill the running thread function?

**Q27. How do you limit concurrency for a large input stream?**

Use a fixed worker count and bounded input queue, with controlled result retention. A semaphore can limit active calls while still allowing excessive task creation. Include deadlines, error propagation and cleanup.

**Follow-up:** What happens if a worker fails while the producer is blocked on queue.put?

**Q28. What do TaskGroup and timeout change?**

TaskGroup scopes/waits for task lifetime and coordinates failures/cancellation. A timeout requests cancellation and translates it at its boundary. Neither reverses a committed remote effect or forcibly interrupts arbitrary blocking code.

**Follow-up:** Why is default gather failure behavior a separate choice?

**Q29. What is the GIL, and does it prevent races?**

On the tested GIL-enabled CPython build, it limits simultaneous Python-bytecode execution in a given interpreter. Native work may release it; free-threaded builds change the context. Compound application updates still need synchronization.

**Follow-up:** Explain the barrier-controlled lost increment without relying on timing luck.

**Q30. Threads, processes or async: which would you choose for document ingestion?**

First identify the work. Async can overlap compatible API waits; threads can isolate suitable blocking I/O; processes can isolate CPU-heavy Python computation. Restart-safe jobs need durable ownership beyond these primitives. Bound memory/concurrency and measure the actual path.

**Follow-up:** What happens after results commit but before the worker acknowledges its job?

---

## 10.21 Practice tasks and answer checkpoints

### 1. Repair a shared request template

A template contains a nested list of tags. Two requests use `template.copy()` and append different tags. Explain the leak and redesign ownership.

**Checkpoint:** The outer dicts differ but the nested list is shared. Build fresh request-local state or deliberately copy the needed nested values. Do not blindly deep-copy live clients.

### 2. Predict before running

Work through snippets 03, 08 and 10 on paper. Explain every binding/mutation, including the failed tuple assignment.

**Checkpoint:** The tuple's nested list changes before assignment fails; the default list is reused; late-bound lambdas observe the shared final binding. Compare your trace with captured stdout.

### 3. Preserve a valid zero

Design an optional configuration field that distinguishes absent, explicit null and zero. Describe which states mean default, clear and a valid value.

**Checkpoint:** A sentinel distinguishes missing from null. A generic truthiness test loses zero. The final policy depends on the API contract.

### 4. Stream without silently consuming twice

Write a function that receives a one-shot iterator and reports both count and transformed output without a preliminary counting pass.

**Checkpoint:** Compute count while consuming once, or intentionally materialize within a declared budget. Reusing an exhausted iterator yields no later records.

### 5. Add an async-aware decorator

Design a wrapper that records success/failure around an awaited coroutine while preserving metadata. Explain what happens on cancellation.

**Checkpoint:** The async wrapper awaits execution, uses wraps, accounts for cleanup/cancellation and does not return an unawaited coroutine while pretending it measured completion. This is a new exercise, not a verified snippet already included.

### 6. Extend quote validation

Add a request field for an optional promo code. Define absence/null/empty behavior and ensure the client cannot directly select a discount amount or tenant.

**Checkpoint:** Update the exact shape rule intentionally, validate the new value and look up allowed promotions through trusted context. Add rejected and boundary cases before changing pricing behavior.

### 7. Diagnose an event-loop stall

An async route reads a huge document with a synchronous parser and then awaits an external API. Explain why other requests stall during parsing.

**Checkpoint:** The parser runs synchronously on the route's executing thread. Identify CPU versus blocking I/O behavior, budgets and library safety before choosing thread/process/durable offload. Async syntax alone changes none of that.

### 8. Change bounded-worker failure behavior

Make one worker in example 26 fail and verify that producer/peer tasks do not hang forever. Remove the fixed results dict for a streaming sink.

**Checkpoint:** Keep task lifetime scoped, preserve task_done accounting where needed, test cancellation while queue.put/get waits, and bound the sink's buffering. Do not claim the modified system is durable.

### 9. Defend a process boundary

Choose which data a parser worker receives and returns. Explain why sending a live database connection or entire mutable application graph is unsuitable.

**Checkpoint:** Use importable worker code and small serializable inputs/results. Specify startup/lifetime, errors, timeouts and ownership. Measure before claiming a speedup.

### 10. Whiteboard the ingestion system

Use section 10.16. Show tenant identity, storage/job keys, streaming boundaries, active/queued limits and the crash after result commit but before acknowledgement.

**Checkpoint:** Durable idempotency/state transitions belong in shared storage. Local Python locks/sets/task groups do not solve cross-process recovery or tenant authorization by themselves.

---

## 10.22 Exit checklist

Leave these unchecked until you can demonstrate the behavior with the page closed.

- [ ] I can distinguish Python, CPython, a framework and an application server.
- [ ] I can trace name binding, aliasing, mutation and shallow/deep copying.
- [ ] I can explain identity, equality, hashability and collection ordering.
- [ ] I can handle missing/null/zero without a truthiness bug.
- [ ] I can repair mutable defaults and late-bound loop closures.
- [ ] I can explain a decorator's transformation and async wrapper requirements.
- [ ] I can distinguish iterables, iterators and generators and manage cleanup.
- [ ] I can preserve exception causes and avoid hiding errors in finally.
- [ ] I can explain what dataclasses and type hints do and do not enforce.
- [ ] I can validate raw input and serialize only intended public fields.
- [ ] I can distinguish text/code-point length from UTF-8 byte size.
- [ ] I can explain virtual environments, import caching and a safe entry point.
- [ ] I can separate object reachability from external-resource lifecycle.
- [ ] I can trace coroutine creation, scheduling, suspension and cancellation.
- [ ] I can bound queued work, active work and retained results separately.
- [ ] I can explain the tested GIL build and demonstrate a race despite it.
- [ ] I can justify threads/processes/async/durable jobs for a concrete workload.
- [ ] I can draw the ingestion design and explain its duplicate/restart path.

---

## 10.23 Sources and reproducible evidence

Primary documentation was checked during authoring on 14 October 2026. The examples record the installed runtime independently. Source links appear beside the mechanisms they support; these are documentation references rather than measured interview-frequency evidence.

| Topic | Primary reading |
| --- | --- |
| Objects and binding | [Data model](https://docs.python.org/3.13/reference/datamodel.html), [execution model](https://docs.python.org/3.13/reference/executionmodel.html), [argument passing FAQ](https://docs.python.org/3.13/faq/programming.html#how-are-arguments-passed-by-value-or-by-reference) |
| Functions and values | [Control flow/functions](https://docs.python.org/3.13/tutorial/controlflow.html), [expressions](https://docs.python.org/3.13/reference/expressions.html), [built-in types](https://docs.python.org/3.13/library/stdtypes.html), [copy](https://docs.python.org/3.13/library/copy.html) |
| Collections and object design | [Data structures](https://docs.python.org/3.13/tutorial/datastructures.html), [classes/iterators](https://docs.python.org/3.13/tutorial/classes.html), [dataclasses](https://docs.python.org/3.13/library/dataclasses.html), [typing](https://docs.python.org/3.13/library/typing.html) |
| Lifecycle | [Exceptions](https://docs.python.org/3.13/tutorial/errors.html), [contextlib](https://docs.python.org/3.13/library/contextlib.html), [functools](https://docs.python.org/3.13/library/functools.html), [gc](https://docs.python.org/3.13/library/gc.html), [weakref](https://docs.python.org/3.13/library/weakref.html) |
| Backend representations | [Decimal](https://docs.python.org/3.13/library/decimal.html), [datetime](https://docs.python.org/3.13/library/datetime.html), [JSON](https://docs.python.org/3.13/library/json.html) |
| Packaging | [Modules](https://docs.python.org/3.13/tutorial/modules.html), [virtual environments](https://docs.python.org/3.13/tutorial/venv.html) |
| Concurrency | [Async tasks](https://docs.python.org/3.13/library/asyncio-task.html), [queues](https://docs.python.org/3.13/library/asyncio-queue.html), [synchronization](https://docs.python.org/3.13/library/asyncio-sync.html), [threading](https://docs.python.org/3.13/library/threading.html), [multiprocessing](https://docs.python.org/3.13/library/multiprocessing.html), [executors](https://docs.python.org/3.13/library/concurrent.futures.html), [free-threaded CPython](https://docs.python.org/3.13/howto/free-threading-python.html) |

### Verification scope

| Group | Checks | Evidence |
| --- | --- | --- |
| Language | 24 | Fresh interpreter per snippet; captured stdout checked exactly |
| Concurrency | 6 | Coroutine lifecycle/blocking/thread offload, bounded workers, TaskGroup cleanup, timeout cleanup, coordinated thread race/lock, explicit spawned processes |
| Application | 14 | Real standard-library parsing/service/projection; valid boundaries and rejected fixtures |
| Total | **44** | Machine-readable results plus human-readable transcript |

Process tests verify separate execution and transferred values, not performance. Async jobs/provider failures are local fixtures, not real network calls. The architecture is a proposed build exercise. No free-threaded run, static type-checker run, framework server, database, external API or production deployment is claimed for M10.

---

## Next

Continue to [M11: Flask, FastAPI and Python Request Handling](/docs/resume-skills/flask-fastapi-python-request-handling). It will connect these Python boundaries to routes, WSGI/ASGI servers, request context, validation/dependencies and the actual execution model of sync versus async handlers.

For shared API/security/reliability concepts, revisit [M6: REST APIs and HTTP](/docs/resume-skills/rest-apis-http), [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy) and [M9: Webhooks and Payments](/docs/resume-skills/webhooks-payments-reliable-integrations). Use the [master roadmap](/docs/resume-skills) to choose the Python or Node branch.
