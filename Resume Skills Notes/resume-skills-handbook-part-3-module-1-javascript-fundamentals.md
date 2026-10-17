# Resume Skills Placement Handbook — Part 3
# Module 1: JavaScript Fundamentals for Interviews

**Module 1 · 4–5 hours · Tier 1 · Requires: M0; basic programming familiarity**

---

## Why this module matters

Node.js, Express, React and Next.js share a language, but their bugs are often explained incorrectly as framework problems.

A copied configuration still changes the original. A callback loses its receiver. A loop produces several functions that all read the same final value. A JSON round trip silently drops fields. These are language behaviors, and changing frameworks does not remove them.

> **Reason about JavaScript using three questions: what value does this binding currently hold, which object is shared, and which environment or receiver does this function use? Most interview predictions become a trace of those three things.**

The purpose is practical fluency: read a handler, predict its behavior and avoid losing data or trust boundaries while transforming objects.

**Verification:** all thirty numbered snippets below ran in isolated Node.js v22.14.0 processes as **ES modules**. Their captured output is preserved with the source and verifier in examples/resume-skills/module-1-javascript/. Caught error names are real outputs; they are not comments copied from a textbook.

### Scope and execution context

- This chapter teaches the language model.
- M2 teaches promises, async/await and scheduling.
- M4 teaches Node's runtime and I/O.
- Browser DOM APIs are outside this chapter.
- Every snippet is a separate ES module. Top-level this is undefined; modules use strict mode.
- A classic browser script, a CommonJS file and a developer console can have different top-level behavior. State the context before predicting this or scope.

### How to run the examples

From the repository root:

```powershell
node examples/resume-skills/module-1-javascript/verify.mjs
node examples/resume-skills/module-1-javascript/verify.mjs 16-loop
```

The first command checks all thirty cases. The second checks and prints the selected case's actual output.

---

## 1.1 JavaScript, the engine and the host

JavaScript defines language operations: values, functions, property access, control flow and exceptions.

An engine implements those operations. A host environment supplies additional capabilities. Node exposes server-side facilities; browsers expose facilities such as the DOM.

```text
Language behavior          Host/runtime capability
-----------------------    ----------------------------
scope, closures, this      HTTP listener, file access
arrays and objects         DOM events or server sockets
exceptions and functions   timers, process/environment APIs
```

This distinction matters when someone says “JavaScript can read a file.” JavaScript syntax describes the program; the host API determines which file operations exist and what permissions apply.

Functions are values. You can assign a function to a variable, pass it as an argument or return it. Frameworks use this to receive your handlers and call them later.

That does not yet explain when a callback runs; M2 supplies that part.

**Interview line:** “JavaScript is the language; the engine executes its semantics; the host supplies environment-specific APIs. Node and the browser therefore share the language but expose different capabilities.”

---

## 1.2 Values have types; bindings hold values

### The type picture

| Kind | Values |
| --- | --- |
| Primitive | undefined, null, boolean, number, bigint, string, symbol |
| Object | Plain objects, arrays, functions, maps, sets, dates and many other objects |

A mutable binding can later hold a different type. The value has a type; declaring a variable does not make it a permanently typed integer in the C++ sense.

Primitive values are immutable. Reassigning a binding holding a string is different from modifying that string value.

### typeof is useful but not a complete validator

**Verified example 01-types: Values, typeof and arrays**

```javascript
console.log(typeof 7, typeof '7', typeof true);
console.log(typeof undefined, typeof null, typeof NaN);
console.log(typeof [], Array.isArray([]), typeof (() => {}));
```

Actual output:

```text
number string boolean
undefined object number
object true function
```


Interpret the surprising parts:

- typeof null returns object, a historical quirk. Test null explicitly.
- NaN is a number value representing an invalid/not-a-number numeric result.
- Arrays are objects. Array.isArray is the deliberate array check.
- Functions are callable objects; typeof gives function for them.

Do not build a validator from “typeof value is object” alone: that admits null and arrays as well as ordinary objects.

[MDN's type guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Data_structures) is the reference for the language's type categories.

### Missing vs deliberately empty

- undefined often appears when a binding/property/result has no supplied value.
- null is an explicit value that an API may choose to represent absence.
- Neither tells you the product meaning by itself. Define the contract: missing field, clear field and empty string can mean different operations.

**Backend connection:** a PATCH payload that omits a field need not mean the same thing as one that explicitly sets it to null.

---

## 1.3 Assignment, arguments and const

### A conceptual alias diagram

This diagram explains identity, not physical stack/heap addresses.

```text
quantity ------> number value 2
copy ----------> number value 2

original ----+
             +--> object { stock: 4 }
alias -------+
```

Reassigning copy changes its binding. Mutating through alias changes the shared object.

**Verified example 02-alias: Primitive copies and object aliases**

```javascript
let quantity = 2;
let copiedQuantity = quantity;
copiedQuantity = 5;
const original = { stock: 4 };
const alias = original;
alias.stock = 1;
console.log(quantity, copiedQuantity);
console.log(original.stock, original === alias);
```

Actual output:

```text
2 5
1 true
```


### JavaScript arguments are passed by value

For an object value, the caller and parameter initially identify the same object. The function can mutate that object's properties. Rebinding the local parameter does not replace the caller's binding.

**Verified example 03-arguments: Mutation versus parameter rebinding**

```javascript
function change(item, count) {
  item.stock = 1;
  item = { stock: 99 };
  count = 99;
}
const item = { stock: 4 };
let count = 2;
change(item, count);
console.log(item.stock, count);
```

Actual output:

```text
1 2
```


Trace it:

| Step | Caller item | Parameter item | Caller count |
| --- | --- | --- | --- |
| Enter change | Original object | Same object | 2 |
| Mutate stock | Original now has stock=1 | Same object | 2 |
| Rebind item | Still original | New object with stock=99 | 2 |
| Rebind count | Still original | New object | Still 2 |

This is why “objects are passed by reference” is an incomplete interview answer. It suggests parameter reassignment can change the caller's variable, which this example disproves.

Compared with C++: an object parameter here is not a C++ object-by-value copy. Assigning a new object to the JavaScript parameter changes only that local binding; assigning through a C++ reference parameter can instead change the caller's object. Describe the shared-object identity and local rebinding explicitly.

### const constrains the binding

**Verified example 04-const: Const fixes a binding, not its object**

```javascript
const options = { retries: 2 };
options.retries = 3;
console.log(options.retries);
try { options = { retries: 4 }; }
catch (error) { console.log(error.name); }
```

Actual output:

```text
3
TypeError
```


| Declaration | Reassign binding? | Block scoped? | Object automatically immutable? |
| --- | --- | --- | --- |
| var | Yes | No; function scoped inside a function | No |
| let | Yes | Yes | No |
| const | No after initialization | Yes | No |

Prefer const when the binding is not reassigned, and let when it is. This communicates intent; it does not prove the referenced data is safe from mutation.

Object.freeze restricts the surface properties of an object and is shallow; nested objects need their own policy. It is not server authorization or a substitute for input validation. [Object.freeze reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze)

---

## 1.4 Shallow copies, nested updates and deep cloning

### What object spread actually changes

Spreading an ordinary object's own enumerable properties makes a new outer object. If a property value identifies another object, that nested identity remains shared.

**Verified example 05-shallow: Spread shares nested objects**

```javascript
const original = { name: 'Asha', address: { city: 'Goa' } };
const copy = { ...original };
copy.name = 'Ravi';
copy.address.city = 'Pune';
console.log(original.name, original.address.city);
console.log(original === copy, original.address === copy.address);
```

Actual output:

```text
Asha Pune
false true
```


```text
original ------> { name: "Asha", address: ---+ }
                                           |
copy ----------> { name: "Ravi", address: --+--> { city: "Pune" }
```

The top-level name changed only on copy. Both address properties still reach the same nested object.

### Copy the path you intend to change

**Verified example 06-path-copy: Copy the changed nested path**

```javascript
const original = { name: 'Asha', address: { city: 'Goa' } };
const updated = { ...original, address: { ...original.address, city: 'Pune' } };
console.log(original.address.city, updated.address.city);
console.log(original.address === updated.address);
```

Actual output:

```text
Goa Pune
false
```


The updated address is a new object, so changing its city does not mutate the original address.

This is the basis of many immutable state updates. It does not require recursively cloning every unrelated branch; unchanged branches may remain shared if code treats them appropriately.

### Deep cloning is a capability, not a magic operation

**Verified example 07-clone: Structured clone and cycles**

```javascript
const original = { address: { city: 'Goa' } };
original.self = original;
const copy = structuredClone(original);
copy.address.city = 'Pune';
console.log(original.address.city, copy.address.city);
console.log(copy !== original, copy.self === copy);
try { structuredClone({ run() {} }); }
catch (error) { console.log(error.name); }
```

Actual output:

```text
Goa Pune
true true
DataCloneError
```


structuredClone handles supported data values and can preserve circular relationships inside the copied graph. The clone's self points to the clone, not the original.

It cannot clone arbitrary executable behavior: the function-valued property produces DataCloneError in this example. It is not a way to reproduce arbitrary class instances, accessors, descriptors or external resources with all their original semantics.

JSON cloning has different limitations, examined in §1.12.

| Technique | New outer object? | Nested object identity |
| --- | --- | --- |
| Direct assignment | No | Same object |
| Object spread | Yes | Shared where nested values are objects |
| Copy changed path | Yes | Replaced along the selected path |
| structuredClone | New supported data graph | Copies supported nested data; not arbitrary behavior |

**When to use:** copy the changed path for a deliberate update; clone supported data when independent ownership of the full data graph is actually needed.

**Common mistake:** treating spread or a rest object as a recursive clone.

---

## 1.5 Numbers, coercion and equality

### Number is not a decimal money type

Ordinary JavaScript numbers use IEEE-754 binary floating-point behavior.

**Verified example 08-numbers: Floating point and integer boundaries**

```javascript
console.log(0.1 + 0.2);
console.log(0.1 + 0.2 === 0.3);
console.log(Number.isSafeInteger(9007199254740991));
console.log(Number.isSafeInteger(9007199254740992));
console.log(25000 * 2);
```

Actual output:

```text
0.30000000000000004
false
true
false
50000
```


The last line is the quote amount from M0: two units at 25000 paise give 50000 paise.

Using integer minor units avoids many decimal rounding errors, but it does not remove range limits or currency-specific rules. Check safe integer bounds and define rounding where a calculation introduces fractions. M9 will cover money and ledger correctness.

BigInt represents integers beyond Number's exact range; it is not a decimal fraction type. Do not blindly mix it with Number arithmetic, and plan its serialization.

### Equality: choose the operation deliberately

**Verified example 09-equality: Strict, loose and same-value equality**

```javascript
console.log(0 == '0', 0 === '0');
console.log(null == undefined, null === undefined);
console.log(NaN === NaN, Object.is(NaN, NaN));
console.log(0 === -0, Object.is(0, -0));
console.log({} === {}, [NaN].includes(NaN), [NaN].indexOf(NaN));
```

Actual output:

```text
true false
true false
false true
true false
false true -1
```


| Operation | Coercion? | NaN equals itself? | Distinguishes +0/-0? |
| --- | --- | --- | --- |
| Strict equality === | No type conversion | No | No |
| Loose equality == | Can convert types | No | No |
| Object.is | No | Yes | Yes |
| SameValueZero, used by Set/Map and includes | No | Yes | No |

Two separately created objects are not equal merely because their properties look the same. Equality compares their identity.

**Default habit:** use strict equality for ordinary application comparisons. Use explicit conversion/validation at a boundary. If a deliberate loose comparison is used, explain its exact purpose rather than saying double equals is always meaningless.

### Conversion is not validation

**Verified example 10-coercion: Plus and explicit conversion**

```javascript
console.log('5' + 1, '5' - 1);
console.log(Number(''), Number('  '));
console.log(Boolean('false'), Boolean([]), Boolean({}));
console.log(Number.isNaN(Number('2x')), parseInt('2x', 10));
```

Actual output:

```text
51 4
0 0
true true true
true 2
```


The plus operator can concatenate a string. Numeric subtraction converts these string operands. Number accepts empty/whitespace-only strings as zero. parseInt accepts a numeric prefix and ignores the remaining x.

A query parameter that looks numeric is still a string in many HTTP APIs. “Convert it and hope” is not a contract.

**Do not memorize a hundred obscure equality puzzles.** Learn the conversion boundary, identity and the handful of special numeric cases that change real application behavior.

[Equality reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Equality_comparisons_and_sameness)

---

## 1.6 Truthiness, default values and optional access

### Falsy is broader than missing

The falsy primitive values include false, numeric zero/-0, 0n, empty string, null, undefined and NaN. Non-empty strings are truthy, including the string false. Empty arrays and ordinary empty objects are truthy.

Do not apply this to every exotic host object: the browser's legacy document.all is an exceptional case, irrelevant to this Node module.

### Nullish coalescing vs logical OR

**Verified example 11-defaults: Nullish versus falsy defaults**

```javascript
for (const value of [0, false, '', null, undefined]) {
  console.log(JSON.stringify([value ?? 'fallback', value || 'fallback']));
}
```

Actual output:

```text
[0,"fallback"]
[false,"fallback"]
["","fallback"]
["fallback","fallback"]
["fallback","fallback"]
```


Each output pair is [nullish result, OR result].

- ?? defaults only for null or undefined.
- || defaults for any falsy left operand.
- These operators return an operand value; they do not necessarily return a boolean.

A zero retry count may mean “do not retry.” Replacing it with a default silently changes policy. Sometimes empty string should count as invalid; then validation, rather than ?? alone, must establish that rule.

### Optional chaining is not universal error suppression

**Verified example 28-optional: Optional access only guards nullish values**

```javascript
const user = { profile: null };
console.log(user.profile?.city ?? 'unknown');
console.log({ count: 0 }.count ?? 10);
try { const item = { run: 3 }; item.run?.(); }
catch (error) { console.log(error.name); }
try { absentRoot?.name; }
catch (error) { console.log(error.name); }
```

Actual output:

```text
unknown
0
TypeError
ReferenceError
```


Optional chaining guards nullish access/call targets at the positions where it is used. It does not make a non-callable number into a function, and it does not allow an undeclared root identifier.

It also does not validate that a present value has the correct product meaning.

**Comparison:** use optional access to handle an allowed missing branch, ?? for an allowed missing value, and explicit validation for a required field.

[Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing), [optional chaining](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining)

---

## 1.7 Scope and hoisting: trace bindings, not moving lines

### Lexical scope

A function's accessible outer bindings follow where the function is defined. A nested block can introduce its own let/const bindings.

var inside a function is scoped to that function, not to its if/for block.

**Verified example 12-scope: Function scope and block scope**

```javascript
function inspect() {
  var label = 'outer';
  if (true) {
    var label = 'inner';
    let local = 'block';
  }
  console.log(label);
  try { console.log(local); }
  catch (error) { console.log(error.name); }
}
inspect();
```

Actual output:

```text
inner
ReferenceError
```


The second var declaration writes the same function-scoped label. local belongs to the if block, so the outside read is invalid.

### What hoisting should mean in an answer

Before statements execute, the environment establishes bindings according to declaration rules. Source lines are not physically moved around.

**Verified example 13-hoisting: Var initialization and the temporal dead zone**

```javascript
console.log(count);
var count = 3;
try { console.log(typeof limit); }
catch (error) { console.log(error.name); }
let limit = 4;
console.log(limit);
```

Actual output:

```text
undefined
ReferenceError
4
```


| Declaration in the illustrated scope | Before its initialization point |
| --- | --- |
| var | Binding initialized to undefined |
| let / const | Binding exists but is uninitialized; access is in the TDZ |
| Ordinary function declaration | Function available through its binding |
| const holding a function expression | const binding has TDZ rules |

TDZ means **temporal dead zone**. It depends on execution reaching initialization, not merely where a line is written visually.

typeof an undeclared name ordinarily returns undefined, but typeof a lexical binding in its TDZ throws. Example 13 deliberately tests the latter.

### A function declaration is not the same as a const arrow

**Verified example 14-functions: Declaration versus const function expression**

```javascript
console.log(add(2, 3));
function add(a, b) { return a + b; }
try { console.log(multiply(2, 3)); }
catch (error) { console.log(error.name); }
const multiply = (a, b) => a * b;
console.log(multiply(2, 3));
```

Actual output:

```text
5
ReferenceError
6
```


The call to add works because of the function-declaration rules. multiply is still an uninitialized const at the earlier call.

Avoid block-level function-declaration puzzles unless the execution mode and surrounding scopes are explicit; historical sloppy-script behavior can complicate them.

**Common wrong answer:** “let and const are not hoisted.” A more useful answer is that their bindings are created but inaccessible until initialized.

[let and TDZ reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)

---

## 1.8 Closures: the centrepiece

### What is a closure?

A function together with access to the lexical environment where it was created. It can use an outer binding after the surrounding function call has returned.

The important distinction is **access to a binding** versus **a previously computed value**.

### A closure sees the current binding

**Verified example 15-closure-binding: Closures retain access to bindings**

```javascript
let token = 'old';
const readToken = () => token;
token = 'new';
console.log(readToken());
```

Actual output:

```text
new
```


The function reads token when called. Changing token before that call changes what it reads.

### Independent factory calls establish independent state

**Verified example 17-factory: Independent closure state**

```javascript
function makeCounter() {
  let count = 0;
  return () => ++count;
}
const a = makeCounter();
const b = makeCounter();
console.log(a(), a(), b(), a());
```

Actual output:

```text
1 2 1 3
```


```text
makeCounter call A             makeCounter call B
count binding A: 0              count binding B: 0
      ^                              ^
      |                              |
function a                     function b

a(), a(), b(), a() -> state evolves in the corresponding environment
```

This supports factories, per-instance private state and callbacks configured with dependencies. It does not provide distributed persistence: a process restart can lose this state.

### The loop question without asynchronous distractions

**Verified example 16-loop: Var and let loop closures without timers**

```javascript
const shared = [];
const separate = [];
for (var i = 0; i < 3; i++) shared.push(() => i);
for (let j = 0; j < 3; j++) separate.push(() => j);
console.log(JSON.stringify(shared.map(read => read())));
console.log(JSON.stringify(separate.map(read => read())));
```

Actual output:

```text
[3,3,3]
[0,1,2]
```


No timer or promise appears. All functions are called only after their loops finish.

- The var loop uses one shared i binding, now holding 3.
- The let loop creates the relevant per-iteration j bindings.
- Each closure reads the binding it captured, not a copied source-code line.

This isolates the closure issue. M2 will add callback scheduling separately.

### Why a closure can still return a stale-looking value

**Verified example 18-snapshot: A captured binding versus an earlier computed value**

```javascript
function makeReader() {
  let count = 0;
  const message = 'count=' + count;
  return {
    increment() { count++; },
    current() { return count; },
    snapshot() { return message; },
  };
}
const reader = makeReader();
reader.increment();
console.log(reader.current(), reader.snapshot());
```

Actual output:

```text
1 count=0
```


current reads the evolving count. snapshot reads message, which was computed once when count was zero and never reassigned.

The closure is not broken. The program chose to retain a precomputed string.

This distinction matters in UI effects, request factories and callbacks that capture an earlier request/version. Determine which binding is being read and when the derived value was computed.

### Lifetime and memory

A reachable closure can keep captured data reachable. Garbage collection may reclaim unreachable objects/environments, with engine-specific optimizations.

Do not say “the whole stack frame lives forever.” The useful application concern is whether a long-lived callback retains a large object or user-specific state unnecessarily.

**Security connection:** putting a mutable current-user variable in process-wide closure state can mix requests. Closures do not automatically establish request isolation.

[Closures reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)

---

## 1.9 Regular-function this and arrow-function this

this is a different question from lexical variable lookup.

### For ordinary method calls, inspect the call site

**Verified example 19-this: The call site supplies this**

```javascript
function readName() { return this.name; }
const a = { name: 'Asha', readName };
const b = { name: 'Ravi', readName };
console.log(a.readName(), b.readName());
const detached = a.readName;
try { detached(); }
catch (error) { console.log(error.name); }
console.log(detached.call(b));
const bound = detached.bind(a);
console.log(bound.call(b));
```

Actual output:

```text
Asha Ravi
TypeError
Ravi
Asha
```


Read the calls individually:

| Call | Receiver behavior in this example |
| --- | --- |
| a.readName() | this identifies a |
| b.readName() | this identifies b |
| detached() | Plain strict-mode call; this is undefined |
| detached.call(b) | Explicit receiver b |
| bound.call(b) | The bound ordinary call retains a |

The detached function is the same function value. It does not permanently belong to a just because it was read from that object.

call invokes with an explicit receiver and separate arguments. apply invokes with an explicit receiver and an argument list. bind produces a function with a receiver/pre-bound arguments for later ordinary calls.

Constructor calls have their own rules; the table concerns ordinary calls, not every use of new.

### Arrow functions do not create their own this

**Verified example 20-arrow: An object literal does not create lexical this**

```javascript
const user = { name: 'Asha', read: () => this };
console.log(user.read() === undefined);
console.log(user.read.call({ name: 'Ravi' }) === undefined);
```

Actual output:

```text
true
true
```


This object literal does not introduce a this binding. The arrow reads the surrounding ES-module this, which is undefined. call cannot replace an arrow's lexical this.

Changing to a classic browser script can change that enclosing value. That is why the execution mode is part of an output question.

### An arrow is useful inside a correctly called method

**Verified example 21-arrow-callback: An arrow can retain an enclosing method's this**

```javascript
const service = {
  name: 'catalog',
  makeReaders() {
    return {
      arrow: () => this.name,
      regular: function () { return this.name; },
    };
  },
};
const readers = service.makeReaders();
console.log(readers.arrow());
console.log(readers.regular.call({ name: 'worker' }));
```

Actual output:

```text
catalog
worker
```


makeReaders is invoked as service.makeReaders(), giving its method call the service receiver. The arrow retains access to that surrounding this.

The returned regular function uses the receiver supplied to its later call.

### Function form comparison

| Behavior | Ordinary function | Arrow function |
| --- | --- | --- |
| Own this binding | Determined by invocation rules | No; reads enclosing this |
| Own arguments binding | Yes for ordinary functions | No; use rest or enclosing arguments |
| Explicit call/apply receiver | Can affect it | Does not replace lexical this |
| Constructor capability | Some ordinary functions support new | Arrow functions do not |
| Suitable object method needing dynamic receiver | Usually yes | Usually not as an object-literal method |
| Callback retaining an enclosing receiver | Bind/capture deliberately | Often convenient |

Not every ordinary-looking function is constructible: methods, async functions and generators have their own rules. Do not generalize “every non-arrow supports new.”

**Backend bug:** passing a class method as a handler can detach its receiver. Know whether the receiving API binds a receiver, or bind/wrap it deliberately.

[this reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this), [arrow reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions)

---

## 1.10 Objects, prototypes and class syntax

### Property lookup

For an ordinary object property read, JavaScript checks the object, then its prototype chain, ending at null.

```text
options -> defaults -> Object.prototype -> null
   |
own properties are checked first
```

**Verified example 22-prototype: Lookup, shadowing and own properties**

```javascript
const defaults = { retries: 2 };
const options = Object.create(defaults);
console.log(options.retries, Object.hasOwn(options, 'retries'));
options.retries = 5;
console.log(options.retries, defaults.retries);
delete options.retries;
console.log(options.retries, 'retries' in options);
console.log(Object.getPrototypeOf(options) === defaults);
```

Actual output:

```text
2 false
5 2
2 true
true
```


Initially retries is inherited. An assignment creates an own shadowing property in this example. Deleting that own property exposes the inherited value again.

This description assumes ordinary writable data properties. Accessors, non-writable properties and proxies can change how writes behave.

### Own property vs inherited property

| Check | What it asks |
| --- | --- |
| Object.hasOwn(object, key) | Does this object itself own the property? |
| key in object | Is it present on the object or prototype chain? |
| Object.getPrototypeOf(object) | What is the next prototype object? |

For untrusted dictionaries, distinguish own data from inherited names. Map or a deliberately constructed dictionary can be a better fit depending on the contract. Avoid arbitrary prototype mutation.

### Classes use the prototype model, with additional semantics

**Verified example 23-class: Class methods and per-instance arrow fields**

```javascript
class Counter {
  count = 0;
  increment() { return ++this.count; }
  read = () => this.count;
}
const a = new Counter();
const b = new Counter();
console.log(Object.hasOwn(a, 'increment'), Object.hasOwn(a, 'read'));
console.log(a.increment === b.increment, a.read === b.read);
a.increment();
const detachedRead = a.read;
console.log(detachedRead());
```

Actual output:

```text
false true
true false
1
```


increment is a shared prototype method here. read is an arrow field initialized separately on each instance and captures that instance's this.

| Member in this example | Location | Same function across instances? |
| --- | --- | --- |
| increment method | Counter.prototype | Yes |
| read arrow field | Instance own property | No |
| count field | Instance own property | Data per instance |

The arrow field makes the extracted read callable without losing its receiver, at the cost of a separate function per instance.

“Classes are just identical to constructor functions” is too broad. Class bodies are strict, class declarations have lexical initialization behavior, and features such as private fields carry additional semantics.

**C++ bridge:** JavaScript objects/prototypes explain property lookup and method sharing; do not import a C++ vtable or destructor-lifetime model unchanged.

[Prototype-chain reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain)

---

## 1.11 Destructuring, rest, arrays, maps and sets

### Destructuring defaults trigger on undefined

**Verified example 24-destructure: Defaults, rest and nested references**

```javascript
const input = { limit: 0, cursor: null, meta: { source: 'web' } };
const { limit = 10, cursor = 'start', ...rest } = input;
rest.meta.source = 'mobile';
console.log(limit, cursor, input.meta.source);
function sum(...values) { return values.reduce((total, value) => total + value, 0); }
console.log(sum(1, 2, 3));
```

Actual output:

```text
0 null mobile
6
```


limit stays zero. cursor stays null. A destructuring default is not a nullish default and not a falsy default.

Object rest makes a new outer object, but rest.meta still identifies the original nested object. Function rest collects arguments into an array.

### Read and transform arrays deliberately

**Verified example 25-array: Array transforms and sorting**

```javascript
const values = [10, 2, 1];
console.log(JSON.stringify([...values].sort()));
console.log(JSON.stringify([...values].sort((a, b) => a - b)));
console.log(JSON.stringify(values));
console.log(JSON.stringify(values.filter(n => n > 1).map(n => n * 2)));
console.log(values.reduce((total, n) => total + n, 0));
const same = values.sort((a, b) => a - b);
console.log(same === values, JSON.stringify(values));
```

Actual output:

```text
[1,10,2]
[1,2,10]
[10,2,1]
[20,4]
13
true [1,2,10]
```


| Operation | Purpose | Mutates the original array itself? |
| --- | --- | --- |
| map | Produce one transformed result per element | No, but its callback may mutate objects |
| filter | Keep selected elements | No; retained object identities remain shared |
| find | Find first matching value | No intrinsic mutation |
| some / every | Test existence / universal condition | No intrinsic mutation |
| reduce | Accumulate a result | Depends on callback behavior |
| sort | Sort the array | Yes |
| Spread into a new array | New outer array | Nested object identities remain shared |

Default sort compares string representations, so it is not numeric ascending order. A numeric comparator supplies numeric order.

A copied array protects the original array's order, not every object inside it.

**Complexity reasoning:** map/filter traverse elements; account for the callback's cost. Sorting cost depends on implementation and comparator behavior; do not claim a specific sorting algorithm is guaranteed by the language. [sort reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)

### Map/Set equality and object keys

**Verified example 26-map: Key identity and set membership**

```javascript
const key = { id: 7 };
const cache = new Map([[key, 'hit']]);
console.log(cache.get(key), cache.has({ id: 7 }));
console.log(new Set([NaN, NaN, 0, -0]).size);
const byId = new Map([[7, 'number'], ['7', 'string']]);
console.log(byId.size, byId.get(7), byId.get('7'));
```

Actual output:

```text
hit false
2
2 number string
```


The newly created object with id=7 is not the same key as key. Number 7 and string 7 are distinct keys. Set uses SameValueZero, so the two NaNs and the signed zeros collapse into two entries.

Use a stable domain identifier as a cache key if the goal is to associate separately reconstructed objects with the same record.

**Do not claim Map must be a hash table with guaranteed worst-case O(1).** It provides language-level key semantics and average access better than linear under the specification's requirements; implementation details and actual costs require separate evidence.

---

## 1.12 JSON and validation at an API boundary

### Serialization changes the available representation

**Verified example 27-json: JSON is not a universal object clone**

```javascript
console.log(JSON.stringify({ missing: undefined, empty: null, bad: NaN, fn() {} }));
console.log(JSON.stringify([undefined, NaN]));
try { JSON.stringify({ id: 1n }); }
catch (error) { console.log(error.name); }
const cyclic = {};
cyclic.self = cyclic;
try { JSON.stringify(cyclic); }
catch (error) { console.log(error.name); }
```

Actual output:

```text
{"empty":null,"bad":null}
[null,null]
TypeError
TypeError
```


These are default JSON behaviors, with no custom replacer/toJSON policy:

| Value/context | Observed behavior here |
| --- | --- |
| undefined/function-valued object property | Omitted |
| undefined in an array | null |
| NaN | null |
| BigInt | TypeError |
| Circular object | TypeError |

Serialization is not a universal deep-copy operation. Dates and class instances also require deliberate representation choices.

A successful JSON parse only establishes syntactically valid JSON. It does not establish that quantity is a safe positive integer or that a caller owns the record.

[JSON.stringify reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify)

### Parse the shape your contract actually permits

**Verified example 29-boundary: Parse a positive integer deliberately**

```javascript
function parseQuantity(raw) {
  if (typeof raw !== 'string' || !/^[1-9][0-9]*$/.test(raw)) return null;
  const value = Number(raw);
  return Number.isSafeInteger(value) ? value : null;
}
for (const raw of ['2', '', '2x', '0', '-1', '1.5', '9007199254740993']) {
  console.log(JSON.stringify(raw), parseQuantity(raw));
}
```

Actual output:

```text
"2" 2
"" null
"2x" null
"0" null
"-1" null
"1.5" null
"9007199254740993" null
```


This deliberately narrow parser accepts positive decimal integer strings without leading zeros. It rejects empty strings, numeric prefixes, fractions, negative values and integers outside the safe range.

The rules are **this parser's contract**, not a universal definition of every valid number. If the product permits zero, leading zeros or decimals, change the contract and verify those cases.

The successful result is a number; null is the failure signal. Since zero is not valid here, there is no ambiguity between a valid zero and failure.

M0's quantity checks use this same idea: establish the accepted representation before using it in business logic.

### Spread order can overwrite authority

**Verified example 30-field-order: Spread order is a trust-boundary decision**

```javascript
const verifiedTenant = 'tenant-A';
const input = { title: 'Report', tenantId: 'tenant-B', isAdmin: true };
const unsafe = { tenantId: verifiedTenant, ...input };
const ordered = { ...input, tenantId: verifiedTenant };
const allowed = { title: input.title, tenantId: verifiedTenant };
console.log(unsafe.tenantId, ordered.tenantId);
console.log(Object.hasOwn(ordered, 'isAdmin'), Object.hasOwn(allowed, 'isAdmin'));
```

Actual output:

```text
tenant-B tenant-A
true false
```


Later spread/explicit properties win for the duplicate keys shown.

Reversing the tenantId order fixes that one overwrite, but the ordered object still retains the caller-supplied isAdmin field. The allowlisted object avoids importing it.

This demonstrates object construction, not a complete authorization system. A real endpoint still derives trusted tenant identity, checks permissions and validates each allowed field.

**Interview follow-up:** “Would placing tenantId last make the endpoint secure?” Answer: it protects that one field in this construction; complete resource/action authorization and input validation still need to run.

---

## 1.13 Resume connections

These examples illustrate mechanisms; they do not claim the underlying project source was inspected.

| Resume area | Language behavior to be ready to explain |
| --- | --- |
| Node/Express APIs | Query strings need deliberate parsing; receivers and callback bindings need clear ownership |
| HR ingestion/nested records | A shallow object copy can share nested state; field selection/spread can also omit or overwrite data |
| Multi-tenant data access | Trusted fields must not be overwritten by caller data; shared mutable closure state is not request isolation |
| Credit/payment calculations | Decimal floating-point, safe integer range and JSON representation need explicit contracts |
| React/Next.js UI state | Copying the changed path, captured values and callback receivers matter before framework-specific rules |
| Caches/load-balancer configuration | Object identity affects keys; process-local closures are not shared durable state |

### Five-question debugging procedure

1. What is the value's type at this boundary?
2. Which bindings identify the same object?
3. Is a copied object shallow, selectively copied or independently cloned?
4. Which lexical environment or this receiver does the function use?
5. Does serialization/defaulting change the contract?

This procedure is more useful than guessing which framework component is broken.

---

## Must remember

1. null is primitive even though typeof reports object.
2. An object value can be shared by several bindings; a parameter can mutate it without rebinding the caller.
3. const prevents binding reassignment, not nested mutation.
4. Spread/rest usually make only an outer copy.
5. Copy each changed nested path when independent updates are needed.
6. structuredClone supports a data graph, not arbitrary executable behavior.
7. Number is binary floating point; integer money still has range and rounding contracts.
8. Equality of objects is identity, not structural similarity.
9. Empty arrays/objects and the string false are truthy.
10. ??, || and destructuring defaults have different triggers.
11. let/const bindings are inaccessible in their TDZ, including through typeof.
12. A closure keeps access to lexical bindings; derived values may still have been computed earlier.
13. Each relevant let loop iteration has its own binding; a var loop can share one.
14. Ordinary-function this depends on invocation; extracting a method can lose its receiver.
15. Arrows read enclosing this; an object literal alone does not supply it.
16. Prototype lookup and own-property checks answer different questions.
17. sort mutates and needs a comparator for numeric ordering.
18. JSON serialization may omit, change or reject values.
19. Conversion alone is not boundary validation.
20. Spread order is not a complete security policy.

---

## Common wrong answers

| Wrong answer | Correct reasoning |
| --- | --- |
| “All objects are passed by reference.” | Arguments are passed by value; object identity is shared, but local parameter rebinding does not rebind the caller |
| “const means immutable.” | It fixes a binding; object properties can remain mutable |
| “Spread deep-clones my object.” | Nested object identities remain shared |
| “JSON parse/stringify is a general clone.” | It loses/changes/rejects values under its representation rules |
| “0.1 + 0.2 is exactly 0.3.” | Binary floating point produces the verified approximation |
| “Two identical-looking objects are equal with ===.” | Separate objects have different identities |
| “The string false is falsy.” | It is a non-empty string and therefore truthy |
| “|| is always a safe default.” | It can overwrite valid zero, false or empty string |
| “let and const are not hoisted.” | Their bindings are created but uninitialized until execution reaches initialization |
| “A closure freezes all current values.” | It retains access to bindings; values explicitly computed earlier can remain snapshots |
| “The callback was created on an object, so this is that object.” | Ordinary this depends on invocation; arrow this comes from an enclosing context |
| “call changes an arrow's this.” | It does not replace lexical this |
| “Every regular function is constructible.” | Methods/async functions/generators have different capabilities |
| “Class syntax replaces prototypes.” | Instance lookup/method sharing still uses prototypes, with class-specific semantics |
| “sort is numeric and non-mutating.” | Its default comparison is string-based and it mutates the array |
| “Number(raw) validates a query parameter.” | Conversion accepts inputs that may violate the intended contract |
| “Putting tenantId last solves authorization.” | It prevents one overwrite; permissions and field validation remain necessary |

---

## Interview Q&A bank

**Q1. What does dynamically typed mean in JavaScript?**
Values have types, while a reassignable binding can later hold a value of another type.
**Follow-up:** Does const add a fixed type? No; it constrains reassignment.

**Q2. Primitive vs object?**
Primitives are immutable values. Objects have identity and can usually contain mutable properties; arrays/functions are objects.
**Follow-up:** Is null an object? No, despite its typeof result.

**Q3. Is JavaScript pass-by-value or pass-by-reference?**
Arguments are passed by value. An object argument lets the parameter reach the same object, so mutation is visible; parameter rebinding does not replace the caller's binding.
**Follow-up:** Explain example 03.

**Q4. What does const guarantee?**
The initialized binding cannot be reassigned. It does not recursively freeze the referenced data.
**Follow-up:** Does Object.freeze deep-freeze? It is shallow.

**Q5. Shallow vs deep copy?**
A shallow copy duplicates an outer structure while nested object identities can remain shared. A deep data clone duplicates supported nested data as well.
**Follow-up:** Why selectively copy a path? It gives independence where the update occurs.

**Q6. Is structuredClone a universal replacement for all copying?**
No. It supports specified data types/graphs and rejects functions; arbitrary class behavior and external resources need their own policy.
**Follow-up:** Does it handle cycles? Example 07 verifies a supported circular graph.

**Q7. Why can decimal money arithmetic be unsafe with Number?**
Binary floating-point cannot represent every decimal exactly. Integer minor units help, with safe ranges, scale and rounding rules still required.
**Follow-up:** Is BigInt a decimal type? No.

**Q8. === vs ==?**
Strict equality avoids type coercion; loose equality applies conversion rules. Neither makes two separate objects structurally equal.
**Follow-up:** Why is Object.is useful? It handles NaN and signed zero differently.

**Q9. Why does a map lookup using a new object fail?**
The new object is a different identity, even with the same fields.
**Follow-up:** What key should represent a record across reconstruction? Usually a stable domain ID with a defined type.

**Q10. || vs ?? vs destructuring defaults?**
OR defaults on falsy; nullish coalescing defaults on null/undefined; destructuring defaults on undefined.
**Follow-up:** What happens to a valid zero? It survives ?? and a destructuring default.

**Q11. What is the TDZ?**
The execution interval in which a lexical binding exists but has not been initialized, so reads fail.
**Follow-up:** Does typeof bypass it? No.

**Q12. Function declaration vs expression?**
An ordinary declaration can be available before its statement executes. An expression assigned to const follows that binding's initialization rules.
**Follow-up:** Is the expression body the problem? The earlier access to the uninitialized binding is.

**Q13. What is a closure?**
A function with access to its surrounding lexical environment, including bindings used after the outer call has returned.
**Follow-up:** Snapshot or live binding? Trace what is actually captured/read.

**Q14. Why does the var loop produce the same value?**
Its functions share one loop binding, read after the loop finishes. The let version provides separate per-iteration bindings.
**Follow-up:** Does this require asynchronous code? Example 16 does not.

**Q15. How can closures produce apparently stale output?**
They may read a binding holding a value computed earlier and never refreshed, as message does in example 18.
**Follow-up:** Is garbage collection the cause? No.

**Q16. How is this chosen?**
For ordinary calls, invocation rules determine the receiver. An arrow instead reads this from the enclosing context.
**Follow-up:** What happens when a method is extracted? A later plain call may lose its receiver.

**Q17. call, apply and bind?**
call/apply invoke with an explicit receiver using separate arguments/an argument list; bind makes a function for later ordinary invocation with a fixed receiver/pre-bound arguments.
**Follow-up:** Can they replace arrow this? No.

**Q18. Why use an arrow inside a method?**
It can retain that method invocation's this for a later callback.
**Follow-up:** Why not always use an arrow as an object-literal method? The literal does not supply a lexical this binding.

**Q19. What is a prototype?**
An object's internal prototype link participates in inherited property lookup, continuing until null.
**Follow-up:** How do you distinguish inherited and own data? Object.hasOwn versus in.

**Q20. Where are class methods and arrow fields stored?**
In the example, the ordinary method is shared on the prototype; the arrow field is a separate function on each instance.
**Follow-up:** Trade-off? Convenient retained receiver versus per-instance function allocation.

**Q21. Does map/filter guarantee immutable data?**
They create outer result arrays, but callbacks and nested shared objects can still mutate data.
**Follow-up:** What does sort do? It sorts its array in place.

**Q22. Why is JSON cloning unreliable?**
Default JSON representation omits some object properties, changes unsupported numeric values and rejects BigInt/cycles in these examples.
**Follow-up:** What should an API do? Define explicit serializable fields and validation.

**Q23. Why not just parseInt every numeric input?**
It accepts a prefix such as 2x as 2, which can violate the intended contract.
**Follow-up:** What should be checked? Accepted representation, value range and business meaning.

**Q24. How do JavaScript fundamentals affect tenant security?**
Shared mutable state and object-field overwrites can cross intended boundaries. Use trusted context, deliberate field selection and real authorization.
**Follow-up:** Is object construction alone enough? No.

---

## Practice

1. **Prediction first:** cover the outputs of examples 03, 05, 13, 16, 19, 24 and 27. Explain each line before checking.
2. **Nested update:** extend a user object with preferences.notifications.email. Change only that email preference without mutating the original changed path.
3. **Closure factory:** build independent per-instance counters with increment and read. Explain which callers share state.
4. **Snapshot repair:** modify example 18 so snapshot returns a newly computed count string. Explain why that changes the result.
5. **Receiver repair:** make the detached handler in example 19 return Asha reliably. Show a bound version and a wrapper version.
6. **Boundary contract:** change the parser to accept zero but still reject empty strings, fractions and unsafe integers. Use an unambiguous failure representation.
7. **Field allowlist:** define an update payload with only title and summary. Demonstrate that tenantId, isAdmin and unknown fields cannot enter the update object.
8. **Array discipline:** sort records by numeric score while preserving the original outer order. Then explain why nested record mutation remains a separate concern.

### Answer checkpoints

- **2:** create new objects along preferences -> notifications; unrelated unchanged branches may remain shared.
- **3:** each factory call needs its own binding; returning two functions from one call can deliberately share that call's state.
- **4:** compute the string in the called function using the current count.
- **5:** bind fixes the ordinary receiver; a wrapper calls the method on its intended receiver.
- **6:** zero must be a successful value distinct from failure; validate the representation and safe-integer range.
- **7:** select allowed fields explicitly and validate their values. This still does not replace resource permission checks.
- **8:** copy the array before sort; array copying does not deep-clone its record objects.

---

## Exit checklist

- [ ] I can identify all seven primitive types and the important typeof surprises.
- [ ] I can trace object aliases, mutation and parameter rebinding.
- [ ] I can distinguish binding constness from data immutability.
- [ ] I can demonstrate shallow-copy sharing and a deliberate nested update.
- [ ] I understand structuredClone and JSON representation limits.
- [ ] I can explain numeric precision/safe integer checks without promising universal money safety.
- [ ] I can choose equality and Map/Set keys deliberately.
- [ ] I can distinguish falsy, nullish and undefined-only defaults.
- [ ] I can trace var/let/const scope and TDZ behavior.
- [ ] I can explain closures, independent factories and the loop example.
- [ ] I can distinguish a captured binding from a precomputed snapshot.
- [ ] I can predict ordinary and arrow this in the stated ES-module context.
- [ ] I can repair a detached handler deliberately.
- [ ] I can explain own/inherited properties and prototype method sharing.
- [ ] I can transform/sort arrays without accidental outer mutation.
- [ ] I can validate string inputs instead of relying on coercion.
- [ ] I can explain why field selection matters at a trust boundary.
- [ ] I can reproduce the thirty snippet outputs and explain caught errors.

---

## Next

[M2: Asynchronous JavaScript](/docs/resume-skills/asynchronous-javascript) adds the execution timeline: call stack, host operations, callbacks, promises, async/await, microtasks, errors and bounded concurrency.

Keep the closure/receiver model from this chapter. Scheduling determines when a function runs; it does not erase the function's captured bindings or receiver rules.

### Sources and reproducible evidence

- [MDN language overview](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Language_overview) and [data types](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Data_structures).
- [Equality comparisons](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Equality_comparisons_and_sameness), [let/TDZ](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let) and [closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures).
- [this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this), [arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions), [prototype chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain).
- [Shallow copying](https://developer.mozilla.org/en-US/docs/Glossary/Shallow_copy), [structured cloning](https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone), [Object.freeze](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze).
- [Nullish defaults](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing), [optional chaining](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining), [sort](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort) and [JSON.stringify](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify).
- Original source/verification: examples/resume-skills/module-1-javascript/cases.json, verify.mjs, results.json and verification-output.txt. Every numbered example above embeds its preserved source and captured output.
