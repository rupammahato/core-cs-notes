# Resume Skills Placement Handbook — Part 5
# Module 3: TypeScript Fundamentals

**Module 3 · 3–4 hours · Tier 1 · Requires: M1; M2 for promise examples**

---

## Why this module matters

A function expects a number but receives a string. A refactor renames a field in one service and misses its callers. A handler assumes a successful response contains data even though the error variant does not. TypeScript can expose many of these mistakes before execution.

It cannot establish that an incoming JSON payload matches an interface, that a user owns a document, or that a stock update is atomic. Those facts need runtime checks and appropriate application/database rules.

> **Use types to describe trusted relationships inside the program. At external boundaries, establish the facts with runtime code before relying on those types.**

This is the bridge from JavaScript fundamentals to typed Node/Express applications. The goal is to explain what the compiler knows, why it accepts/rejects a program, and what JavaScript actually executes.

**Verification:** 26 examples were checked with the repository's installed **TypeScript 7.0.2**. Sixteen compiled and their emitted ES-module JavaScript ran on **Node.js v22.14.0**. Ten intentionally invalid examples were rejected with the recorded diagnostic codes, and no JavaScript was emitted for them. No ts-ignore or ts-expect-error suppressions are used.

### How to run the examples

From the repository root:

```powershell
node examples/resume-skills/module-3-typescript/verify.mjs
node examples/resume-skills/module-3-typescript/verify.mjs 23-boundary
node examples/resume-skills/module-3-typescript/verify.mjs 16-exhaustive
```

The verifier uses the compiler already installed in study-guide/node_modules. It creates isolated temporary projects, compiles each input.mts, checks actual diagnostics/output, and removes only its own temporary directory. No new packages, external service or internet connection are needed when those dependencies are present.

### Compiler context used here

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022", "DOM"],
    "types": [],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noEmitOnError": true,
    "outDir": "./out"
  },
  "files": ["./input.mts"]
}
```

Each example is its own module/project. The DOM declarations supply console's declaration for these small examples; this is not a browser application and does not use DOM runtime APIs. Real Node projects normally use appropriate Node declarations. Explicit types: [] keeps ambient package selection controlled.

The flags matter: strict includes strict null checking and other checks, while noUncheckedIndexedAccess and exactOptionalPropertyTypes are additional options, not automatically implied by strict.

---

## 3.1 What TypeScript is and where it runs

### Source, checker and runtime

TypeScript adds a static type system and related syntax/tooling to JavaScript. A compiler/toolchain checks the source and produces runnable JavaScript as appropriate for its configuration.

```text
TypeScript source
   |
   +--> static checking --> diagnostics / editor feedback / build gate
   |
   +--> emit or transform --> JavaScript --> Node or browser runtime

External request data ---------------------> runtime validation still required
```

Checking and emitting are distinct operations. A tool can strip syntax without doing full type checking. A project can check types without emitting because another tool handles transformation.

### Type annotations are not runtime objects

**Verified example 01-erasure: Type annotations and interfaces disappear**

```typescript
interface Product { id: number; name: string }
type ProductId = number;
const id: ProductId = 7;
const product: Product = { id, name: 'Keyboard' };
console.log(typeof id, product.name);
```

Compiler accepted. Actual runtime output:

```text
number Keyboard
```


Actual emitted JavaScript:

```javascript
const id = 7;
const product = { id, name: 'Keyboard' };
console.log(typeof id, product.name);
export {};
```

The Product interface, ProductId alias and variable annotations are absent. id is still a JavaScript number; product is still an ordinary object.

An interface is not a constructor. You cannot use instanceof Product when Product exists only as an interface. Use a runtime predicate/schema, or a real constructor when that is the relevant contract.

Do not overstate this as “every TypeScript construct has no runtime effect.” Ordinary classes are runtime values, and features such as non-const enums can emit runtime JavaScript. This chapter focuses mainly on erasable type syntax.

See [TypeScript's basics](https://www.typescriptlang.org/docs/handbook/2/basic-types.html) and [enum reference](https://www.typescriptlang.org/docs/handbook/enums.html).

### Why it is useful

| Benefit | Concrete example |
| --- | --- |
| Catch incompatible calls | A quantity argument is a string where a number is required |
| Describe allowed states | A failure result has an error, not a success value |
| Preserve relationships | A generic getter returns the type of the selected property |
| Support refactors | Renaming a known field exposes affected checked callers |
| Document boundaries | A function declares what trusted input/result it expects |

These benefits depend on accurate declarations, checks and toolchain enforcement. They do not prove that the program meets every business requirement.

**Interview line:** “TypeScript checks relationships before execution and gives better tooling. The runtime still executes JavaScript, so external data and business invariants need runtime enforcement.”

---

## 3.2 Basic notation and inference

### Start with the values from M1

| Runtime concept | Typical TypeScript description |
| --- | --- |
| String | string |
| Number | number; there is no separate integer runtime type |
| Boolean | boolean |
| Missing/empty | undefined and null, with explicit policies |
| Array of numbers | number[] or Array of number |
| Fixed positions | A tuple such as [number, string] |
| Object shape | An interface or object type |
| Function | Parameter and result types |
| Later result | Promise with a fulfillment type |

Use lowercase string/number/boolean for primitive descriptions rather than wrapper-object types String/Number/Boolean.

### Inference is still checking

**Verified example 02-inference: Inference and annotations describe the same JavaScript values**

```typescript
let retries = 2;
const mode = 'safe';
function total(price: number, quantity: number): number {
  return price * quantity;
}
const scores = [1, 2, 3].map(value => value * 2);
console.log(total(25000, retries), mode, scores.join(','));
```

Compiler accepted. Actual runtime output:

```text
50000 safe 2,4,6
```


The compiler infers retries as number and the map callback parameter as number. An explicit annotation is useful at an API boundary or where a contract should remain stable; it is not necessary on every local variable.

A const primitive literal can retain a narrow literal type. A mutable binding or mutable object property may widen to a broader type because later changes are allowed.

For example, const mode = 'safe' can retain the literal type 'safe'. A const object binding does not make all its properties immutable; M1's binding/object distinction still applies.

### Check an incompatible call

**Verified example 03-argument: A checked function call rejects the wrong argument type**

```typescript
function total(price: number, quantity: number): number {
  return price * quantity;
}
total(25000, '2');
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(4,14): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
```


The compiler catches this checked call. It does not mean an unchecked JavaScript caller, an inaccurate declaration or unvalidated JSON can never deliver a string at runtime.

There is also no special integer type here: a parameter typed number can receive 1.5, NaN or an out-of-range value. Validate the numeric policy where it matters.

Reference: [Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html).

---

## 3.3 Structural typing and extra properties

### Compatible by shape

TypeScript commonly compares the structure a value provides with the structure a consumer requires, rather than requiring the value to have been declared with a particular interface name.

**Verified example 04-structural: Structural compatibility does not remove extra fields**

```typescript
interface PublicUser { id: number; name: string }
const stored = { id: 7, name: 'Rupam', passwordHash: 'demo-only' };
const view: PublicUser = stored;
function label(user: PublicUser): string { return user.name; }
console.log(label(stored), view === stored);
console.log(JSON.stringify(view));
```

Compiler accepted. Actual runtime output:

```text
Rupam true
{"id":7,"name":"Rupam","passwordHash":"demo-only"}
```


stored provides id and name, so it can be used where PublicUser is required. The runtime object still includes passwordHash.

**Critical backend lesson:** assigning to PublicUser is not response sanitization. JSON.stringify serializes the actual object's fields, not the interface's list of fields.

Construct a new response object containing allowed fields. Example 21 does that explicitly.

Class private/protected members and other type-system details add compatibility rules; “structural” is a useful core model, not a claim that every conceivable type comparison ignores origin.

### Why did this similar assignment fail?

**Verified example 05-excess: Fresh object literals receive an excess-property check**

```typescript
interface PublicUser { id: number; name: string }
const user: PublicUser = { id: 7, name: 'Rupam', passwordHash: 'demo-only' };
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(2,50): error TS2353: Object literal may only specify known properties, and 'passwordHash' does not exist in type 'PublicUser'.
```


A fresh object literal is subject to an excess-property check in this assignment. That catches many misspelled or unexpected properties.

It is not a universal exact-object guarantee. Example 04 uses an existing object variable and is accepted because its required structure is compatible.

| Situation | What to conclude |
| --- | --- |
| Fresh literal rejected for an extra field | This particular checked construction violates the target shape |
| Existing compatible object accepted | It supplies the required structure; extra runtime fields may remain |
| Remote JSON typed as PublicUser | No runtime validation/filtering has occurred merely from the type |
| New object built by selecting id/name | Actual response fields have been selected by executable code |

See [type compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) and [object types](https://www.typescriptlang.org/docs/handbook/2/objects.html).

---

## 3.4 Unions, nullability, optional fields and indexed access

### A union means one of the permitted possibilities

Before narrowing string | number, you can only use operations valid for the possibilities still under consideration.

**Verified example 06-narrowing: Control flow narrows a union**

```typescript
function normalize(id: string | number): string {
  if (typeof id === 'string') return id.trim();
  return id.toFixed(0);
}
console.log(normalize(' 7 '), normalize(8));
function text(value: string | null): string {
  if (value === null) return 'missing';
  return value.length === 0 ? 'empty' : value.toUpperCase();
}
console.log(text(''), text(null), text('ok'));
```

Compiler accepted. Actual runtime output:

```text
7 8
empty missing OK
```


Control flow establishes which branch is possible. The code preserves the difference between an empty string and a missing value rather than using a broad truthiness check.

Useful narrowing evidence includes typeof, explicit equality, suitable in checks, discriminant properties and instanceof for real runtime constructors.

Remember typeof null is object from M1. A generic object check must account for null and often arrays.

### Null must be handled deliberately

**Verified example 10-null: Strict null checking requires a check**

```typescript
function upper(value: string | null): string {
  return value.toUpperCase();
}
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(2,10): error TS18047: 'value' is possibly 'null'.
```


Under strict null checking, a value that might be null is not treated as a definitely present string.

Check it, return an explicit missing result, throw according to the contract, or choose a justified default. A non-null assertion does not perform a runtime check; example 09 demonstrates that failure.

### Optional is a policy about absence

**Verified example 11-optional: Exact optional properties distinguish absence from undefined**

```typescript
interface Patch { name?: string }
const patch: Patch = { name: undefined };
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(2,7): error TS2375: Type '{ name: undefined; }' is not assignable to type 'Patch' with 'exactOptionalPropertyTypes: true'. Consider adding 'undefined' to the types of the target's properties.
  Types of property 'name' are incompatible.
    Type 'undefined' is not assignable to type 'string'.
```


With exactOptionalPropertyTypes enabled, name?: string permits an omitted name or a present string. A present undefined needs to be allowed explicitly if the contract requires it.

Reading an optional property can still produce undefined because the property may be absent. The option changes permitted assignments; it does not make optional reads always present.

For PATCH APIs, decide what omission, null, undefined and an empty string mean. JSON does not represent undefined as an ordinary property value, but internal JavaScript objects can contain it.

Reference: [exactOptionalPropertyTypes](https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html).

### An array index may not exist

**Verified example 12-index: Unchecked indexing adds undefined to a possible missing element**

```typescript
function firstLength(values: string[]): number {
  return values[0].length;
}
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(2,10): error TS2532: Object is possibly 'undefined'.
```


The checked array could be empty. noUncheckedIndexedAccess makes an unchecked index reflect that possibility.

Read the element, check whether it is undefined, then use it. A length assumption or cast is not a substitute for an established invariant.

Reference: [noUncheckedIndexedAccess](https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html).

### Tuples describe positions

**Verified example 25-tuple: Tuples describe positions and as const is compile-time readonly**

```typescript
type Coordinate = readonly [latitude: number, longitude: number];
const point = [22.57, 88.36] as const;
function describe([latitude, longitude]: Coordinate): string {
  return latitude + ',' + longitude;
}
console.log(describe(point), point.length, Object.isFrozen(point));
```

Compiler accepted. Actual runtime output:

```text
22.57,88.36 2 false
```


The two positions carry separate roles and a known length at the type level. Position labels aid readability; they do not create named runtime properties.

as const gives this literal a readonly tuple description. It does not call Object.freeze. Runtime mutation through unchecked code/other aliases remains a separate concern.

---

## 3.5 any, unknown, assertions and never

### any removes checks along that path

**Verified example 08-any: Explicit any bypasses checks even under strict**

```typescript
const input: any = 7;
try { console.log(input.toUpperCase()); }
catch (error: unknown) {
  console.log(error instanceof Error ? error.name : 'unknown failure');
}
```

Compiler accepted. Actual runtime output:

```text
TypeError
```


strict does not ban explicit any. The invalid method call compiles and fails at runtime.

any can spread through assignments and expressions, causing later code to lose useful checking. If it is necessary at an integration point, keep its scope narrow and document the reason.

### unknown requires evidence

**Verified example 07-unknown: unknown requires evidence before property access**

```typescript
function readName(value: unknown): string {
  return value.name;
}
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(2,10): error TS18046: 'value' is of type 'unknown'.
```


unknown can hold any value, but it does not let the consumer assume a property or operation without narrowing/assertion.

Prefer unknown for untrusted data and caught exceptions. Check what you need, then work with the narrowed value.

The difference is not runtime representation: any and unknown annotations both disappear. It is which operations the checker permits before evidence exists.

### Assertions state a belief; they do not establish a fact

**Verified example 09-assertion: An assertion is not conversion or validation**

```typescript
const quantity = JSON.parse('"two"') as number;
console.log(typeof quantity, quantity + 1);
function readLength(value: string | undefined): number { return value!.length; }
try { console.log(readLength(undefined)); }
catch (error: unknown) {
  console.log(error instanceof Error ? error.name : 'unknown failure');
}
```

Compiler accepted. Actual runtime output:

```text
string two1
TypeError
```


JSON.parse returns a string here. as number changes the compiler's view, not the runtime value. The + operation therefore concatenates.

The non-null assertion in readLength similarly removes a compiler concern without checking undefined. Execution still throws.

Use an assertion when there is an independently established invariant the checker cannot express, not as a way to silence an unexplained boundary error.

| Construct | Role |
| --- | --- |
| unknown | Require evidence before use |
| any | Bypass checking in that path |
| as T | Assert a type relationship for the checker |
| value! | Assert null/undefined are absent |
| Runtime validator | Execute checks and reject/normalize data |
| never | Describe an impossible value/path under the current type model |

never is useful for exhaustive handling. It is not a value you receive from a failed API call; a failure still needs a representable result or exception.

---

## 3.6 type vs interface, unions vs intersections

### The practical comparison

| Feature | interface | type alias |
| --- | --- | --- |
| Name an object shape | Yes | Yes |
| Describe callable shapes | Yes | Yes |
| Name a primitive or union | Cannot directly alias them | Yes |
| Combine object requirements | extends | Intersection, among other constructions |
| Repeated declaration under the same interface name | Can merge in suitable scope | Cannot redeclare an alias that way |
| Creates runtime validation | No | No |

Use a consistent project convention. A common choice is interfaces for extensible object contracts and aliases for unions/type transformations; neither universally replaces the other.

**Verified example 17-interface-alias: Interfaces can merge; aliases can name unions**

```typescript
interface User { id: number }
interface User { name: string }
interface Admin extends User { role: 'admin' }
type UserId = string | number;
type Identified = User & { active: boolean };
const admin: Admin = { id: 7, name: 'Rupam', role: 'admin' };
const active: Identified = { ...admin, active: true };
const id: UserId = admin.id;
console.log(id, active.name, active.active);
```

Compiler accepted. Actual runtime output:

```text
7 Rupam true
```


Two User interface declarations merge their requirements here. UserId names a union, and Identified uses an intersection.

Unintended interface merging can also create surprising requirements. Prefer deliberate ownership of shared declarations.

### Union is either; intersection is both

A | B accepts values compatible with at least one alternative. A & B requires the combined obligations.

An intersection does not mean “merge JSON at runtime,” and incompatible fields can create an impossible requirement.

**Verified example 26-intersection: Conflicting intersection requirements can produce never**

```typescript
type Impossible = { id: string } & { id: number };
const item: Impossible = { id: 7 };
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(2,28): error TS2322: Type 'number' is not assignable to type 'never'.
```


id would have to satisfy both string and number. A normal number does not satisfy that requirement, which becomes never for this property.

Look at the overlapping field types when debugging intersections; adding more casts does not repair an inconsistent contract.

---

## 3.7 Discriminated unions model state

### Prefer valid combinations over unrelated optional fields

A response with optional value and optional error can accidentally describe both, neither or an inconsistent combination.

A discriminant creates alternatives whose fields match the state.

**Verified example 15-result: A discriminated union models valid result states**

```typescript
type Result<T> =
  | { ok: true; value: T }
  | { ok: false; error: string };
function assertNever(value: never): never {
  throw new Error('Unexpected variant');
}
function describe(result: Result<number>): string {
  switch (result.ok) {
    case true: return 'value:' + result.value;
    case false: return 'error:' + result.error;
    default: return assertNever(result);
  }
}
console.log(describe({ ok: true, value: 7 }));
console.log(describe({ ok: false, error: 'missing' }));
```

Compiler accepted. Actual runtime output:

```text
value:7
error:missing
```


After the ok check, the compiler knows which fields exist. The result representation forces callers to handle success and failure explicitly.

This is useful for parsing, service results, loading states and job state machines. It does not by itself ensure that every external producer sends a valid variant.

### Exhaustiveness exposes missed changes

**Verified example 16-exhaustive: A missing variant fails an exhaustive switch**

```typescript
type Job =
  | { state: 'queued' }
  | { state: 'done'; output: string }
  | { state: 'failed'; error: string };
function assertNever(value: never): never {
  throw new Error('Unexpected variant');
}
function describe(job: Job): string {
  switch (job.state) {
    case 'queued': return 'waiting';
    case 'done': return job.output;
    default: return assertNever(job);
  }
}
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(12,33): error TS2345: Argument of type '{ state: "failed"; error: string; }' is not assignable to parameter of type 'never'.
```


The failed variant remains possible in default. It cannot be passed to a function demanding never.

Adding a new variant can therefore expose consumers that omitted it. This is a valuable refactoring tool for job/payment/workflow states.

assertNever throws if execution reaches it. Its static role relies on the surrounding input types being trustworthy. Unvalidated runtime data can still violate those assumptions.

Reference: [narrowing and exhaustiveness](https://www.typescriptlang.org/docs/handbook/2/narrowing.html).

---
## 3.8 Generics preserve useful relationships

### Generic is not a more complicated spelling of any

A generic type parameter lets a function express a relationship that varies with each call.

If a function returns any, the caller loses checking. If it returns T related to its input T, the caller retains that relationship.

**Verified example 18-generics: Generics preserve relationships between input and output types**

```typescript
function get<T, K extends keyof T>(object: T, key: K): T[K] {
  return object[key];
}
function first<T>(items: readonly T[]): T | undefined {
  return items[0];
}
const user = { id: 7, name: 'Rupam' };
const name: string = get(user, 'name');
const id: number = get(user, 'id');
console.log(name, id, first([10, 20]), first([]));
```

Compiler accepted. Actual runtime output:

```text
Rupam 7 10 undefined
```


get(user, 'name') returns the property type string. get(user, 'id') returns number. first preserves an element type but admits undefined for an empty array.

A generic function cannot assume arbitrary methods exist on T. Add a constraint when the implementation requires a capability, such as a length property.

### Read the getter one piece at a time

| Piece | Meaning |
| --- | --- |
| T | The object's type for this call |
| keyof T | The known permissible property keys of T |
| K extends keyof T | The selected key must be compatible with those keys |
| T[K] | The value type for that selected key |
| object[key] | The actual runtime property lookup |

**Verified example 19-generic-key: A key constraint rejects nonexistent known keys**

```typescript
function get<T, K extends keyof T>(object: T, key: K): T[K] {
  return object[key];
}
get({ id: 7 }, 'email');
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(4,16): error TS2345: Argument of type '"email"' is not assignable to parameter of type '"id"'.
```


The type constraint detects a nonexistent known key. Runtime property lookup still follows JavaScript rules, including optional properties and inherited properties where relevant.

TypeScript generics do not generate separate runtime function copies for each T in the C++ template sense. The type parameters are erased; runtime logic must still handle the actual values correctly.

Reference: [generics](https://www.typescriptlang.org/docs/handbook/2/generics.html).

---

## 3.9 Derive types with operators and utility types

### Type-level operators vs runtime operations

| Operator | Type-level question |
| --- | --- |
| keyof User | Which keys does this type describe? |
| typeof configuration in a type position | What is the type of this existing value? |
| User['name'] | What is the type of this property? |
| T[K] | What type is selected by this key parameter? |

JavaScript typeof value produces a runtime string such as object. TypeScript typeof in a type position refers to the compiler's type of a value. Same spelling, different roles.

For example, `Readonly<typeof mutable>` in example 13 derives a type from an existing variable. It does not execute typeof mutable and turn the string object into a schema.

Reference: [keyof](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html), [type-position typeof](https://www.typescriptlang.org/docs/handbook/2/typeof-types.html) and [indexed access types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html).

### Common utility types

| Utility | Typical purpose |
| --- | --- |
| Partial of T | Make the described properties optional |
| Required of T | Make them required |
| Pick of T and keys | Select a subset of properties |
| Omit of T and keys | Describe the remaining properties |
| Readonly of T | Disallow property assignment through that typed view |
| Record of keys and value type | Describe a mapping |
| ReturnType of a function type | Derive its result type |
| Awaited of T | Derive the value obtained by awaiting T |
| NonNullable of T | Remove null and undefined alternatives |
| Exclude of a union and members | Remove compatible union members |
| Extract of a union and members | Retain compatible union members |

These operate on types. Partial is shallow; it does not recursively turn a nested object into a deep patch. Omit does not delete a property from an object. NonNullable does not check a value at runtime.

**Verified example 21-utilities: Utility types derive contracts without runtime field filtering**

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  passwordHash: string;
}
type PublicUser = Pick<User, 'id' | 'name'>;
type Editable = Partial<Pick<User, 'name' | 'email'>>;
type NewUser = Omit<User, 'id'>;
const stored: User = {
  id: 7, name: 'Rupam', email: 'r@example.test', passwordHash: 'demo-only'
};
function toPublic(user: User): PublicUser {
  return { id: user.id, name: user.name };
}
const update: Editable = { name: 'New name' };
const defaults: Required<Editable> = { name: '', email: '' };
const totals: Record<'accepted' | 'rejected', number> = { accepted: 1, rejected: 0 };
const draft: NewUser = { name: defaults.name, email: '', passwordHash: 'demo-only' };
console.log(JSON.stringify(toPublic(stored)));
console.log(update.name, totals.accepted, draft.name.length);
```

Compiler accepted. Actual runtime output:

```text
{"id":7,"name":"Rupam"}
New name 1 0
```


The response omits passwordHash because toPublic constructs a new object with selected fields. Pick alone did not do that work.

### PATCH contracts deserve explicit field ownership

`Partial<User>` may permit fields the client must never control, such as IDs, tenant ownership, roles or stored password hashes.

`Partial<Pick<User, 'name' | 'email'>>` is a better static description for this editable subset. Still validate values, reject/select runtime fields and authorize the resource. A type alias does not grant or deny permissions.

When designing a public DTO, balance reuse against coupling. Deriving every external request directly from a database row type can expose internal changes or accidentally widen what clients may send.

Reference: [utility types](https://www.typescriptlang.org/docs/handbook/utility-types.html).

---

## 3.10 readonly, const and runtime immutability

### Keep three mechanisms separate

| Mechanism | What it constrains |
| --- | --- |
| const binding | Reassignment of that variable binding |
| readonly type property/view | Assignment allowed by the checker through that view |
| Object.freeze | Runtime changes to the frozen object's own properties, with shallow semantics |

**Verified example 13-readonly: Readonly is shallow and does not freeze an aliased object**

```typescript
const mutable = { id: 7, settings: { theme: 'light' } };
const view: Readonly<typeof mutable> = mutable;
mutable.id = 8;
view.settings.theme = 'dark';
console.log(view.id, view.settings.theme, Object.isFrozen(view));
```

Compiler accepted. Actual runtime output:

```text
8 dark false
```


Readonly is shallow here. view.settings remains an object whose theme is writable, and mutable still points to the same outer object.

Even top-level id changes are visible through view because the other alias updates the shared object.

**Verified example 14-readonly-write: A readonly property rejects assignment through that view**

```typescript
interface User { readonly id: number }
const user: User = { id: 7 };
user.id = 8;
```

Compiler rejected. Actual diagnostic (no JavaScript emitted):

```text
input.mts(3,6): error TS2540: Cannot assign to 'id' because it is a read-only property.
```


This write is rejected through the readonly view. That static restriction does not imply that the object was frozen or cloned.

### Why this matters in backend code

A readonly configuration parameter can communicate that a function should not modify it. It does not prevent another owner from modifying the same object during a longer asynchronous workflow.

If you need a stable snapshot, decide whether to copy the relevant data, use immutable ownership, synchronize updates or otherwise establish the required invariant.

M1's shallow-copy and alias rules still apply. TypeScript descriptions do not change those runtime identities.

---

## 3.11 as const, satisfies and assertions

### Use each for its actual job

| Form | Role |
| --- | --- |
| An explicit variable annotation | Give the binding a declared contract |
| as SomeType | Tell the checker to treat the expression according to an asserted relationship |
| as const on a suitable literal | Preserve literal information and readonly literal structure |
| satisfies SomeType | Check compatibility while keeping the expression's inferred type, subject to contextual typing |
| A runtime check/schema | Establish facts about an actual value |

**Verified example 20-satisfies: satisfies checks compatibility without a broad annotation**

```typescript
type RouteName = 'health' | 'submit';
type Route = { method: 'GET' | 'POST'; path: string };
const routes = {
  health: { method: 'GET', path: '/health' },
  submit: { method: 'POST', path: '/submit' }
} as const satisfies Record<RouteName, Route>;
const method: 'GET' = routes.health.method;
console.log(method, routes.submit.path, Object.isFrozen(routes));
```

Compiler accepted. Actual runtime output:

```text
GET /submit false
```


The map must supply the required route names with valid route shapes. as const retains the method literals and readonly description. satisfies checks compatibility with the route map.

The assignment to method demonstrates that health.method remains the literal GET in this example. Object.isFrozen confirms that no runtime freezing happened.

Do not describe satisfies as a runtime assertion or a conversion. It can provide contextual typing, so avoid the absolute claim that it can never influence inference. Its practical role is to check compatibility without replacing the expression with a broad variable annotation.

Useful cases include route maps, configuration objects and exhaustive handler registries. Runtime-loaded configuration still needs parsing/validation.

Reference: [TypeScript 4.9 satisfies documentation](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html).

---

## 3.12 Functions, promises and void

### Declare the contract at useful boundaries

A function type describes parameters and results. Optional/default parameters, rest parameters and overloads can express different call contracts.

Use a union when one implementation can clearly accept the alternatives. Use overloads when callers need distinct input/output relationships that a single broad union would lose. The implementation must still implement every advertised path; overload declarations are not runtime dispatch logic.

### Promise types describe fulfillment

**Verified example 22-functions: Promise return types and void callbacks remain runtime JavaScript**

```typescript
async function load(): Promise<{ id: number }> {
  return { id: 7 };
}
type Loaded = Awaited<ReturnType<typeof load>>;
const user: Loaded = await load();
const callback: () => void = () => 7;
console.log(user.id, callback());
```

Compiler accepted. Actual runtime output:

```text
7 7
```


load returns a promise whose fulfillment value has id. `Awaited<ReturnType<typeof load>>` derives that value type.

`Promise<T>` does not encode a separate checked rejection type. The operation can still reject or throw according to its implementation. Use a discriminated result type when callers should handle known application failures as values, while retaining appropriate unexpected-error handling.

M2 still determines when the operation starts, who waits and what happens on failure.

### void is not an exact runtime undefined promise

In a callback type () => void, void means the consumer does not rely on a useful return value. TypeScript can accept a function returning a value in that position, as the output 7 demonstrates.

This differs from explicitly annotating an implementation's return as void and then returning a number inside it, which would be a type error.

**Async callback trap:** a callback API that ignores returns may accept a function that returns a promise, but the API still does not await that promise. The assigned type alone does not establish completion/error ownership. M2's forEach and floating-promise rules still apply.

Use the API's actual contract, appropriate linting and explicit joins/error handling. Do not claim that a type annotation has made a synchronous callback consumer asynchronous.

Reference: [More on Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html).

---

## 3.13 Build a runtime validation boundary

### Start from unknown

Request bodies, parsed files, queue messages, environment variables and upstream responses arrive from outside the checked program.

A generic fetch helper returning `Promise<T>`, an ORM row assertion or JSON.parse followed by as T does not establish that those values match T.

```text
HTTP bytes / external data
        |
Body size / format / JSON syntax checks
        |
unknown
        |
Runtime shape, field and value validation
        |
Explicitly constructed typed request
        |
Identity + resource authorization + business rules
        |
Authoritative data operation
        |
Selected response fields
```

The exact ordering of identity checks and input parsing depends on the application, but every required boundary must exist. Validation alone is not authorization.

### Contract of this learning validator

- Input is JSON-decoded data; direct JavaScript samples additionally exercise NaN and numeric bounds.
- productId is a positive safe integer.
- quantity is an integer from one through ten, a chosen per-request policy.
- Unknown enumerable string fields are rejected.
- Success constructs a new object with only productId and quantity.
- There is no numeric-string coercion.
- Invalid shape/fields/values produce a discriminated error result.

**Verified example 23-boundary: Validate unknown input and construct a trusted request object**

```typescript
type QuoteInput = { productId: number; quantity: number };
type Parsed =
  | { ok: true; value: QuoteInput }
  | { ok: false; error: string };
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function parseQuote(input: unknown): Parsed {
  if (!isRecord(input)) return { ok: false, error: 'shape' };
  if (Object.keys(input).some(key => key !== 'productId' && key !== 'quantity')) {
    return { ok: false, error: 'fields' };
  }
  const productId = input.productId;
  const quantity = input.quantity;
  if (typeof productId !== 'number' || !Number.isSafeInteger(productId) || productId < 1) {
    return { ok: false, error: 'productId' };
  }
  if (typeof quantity !== 'number' || !Number.isSafeInteger(quantity) ||
      quantity < 1 || quantity > 10) {
    return { ok: false, error: 'quantity' };
  }
  return { ok: true, value: { productId, quantity } };
}
const samples: unknown[] = [
  JSON.parse('{"productId":7,"quantity":2}'),
  { productId: 7, quantity: 1 },
  { productId: 7, quantity: 10 },
  { productId: '7', quantity: 2 },
  { productId: 7, quantity: NaN },
  null, [], {},
  { productId: 7, quantity: '2' },
  { productId: 7, quantity: 0 },
  { productId: 7, quantity: 1.5 },
  { productId: 7, quantity: 11 },
  { productId: Number.MAX_SAFE_INTEGER + 1, quantity: 2 },
  { productId: 7, quantity: 2, tenantId: 'other' }
];
for (const sample of samples) {
  const result = parseQuote(sample);
  console.log(result.ok ? JSON.stringify(result.value) : result.error);
}
```

Compiler accepted. Actual runtime output:

```text
{"productId":7,"quantity":2}
{"productId":7,"quantity":1}
{"productId":7,"quantity":10}
productId
quantity
shape
shape
productId
quantity
quantity
quantity
quantity
productId
fields
```


### Trace successful input

1. The value must be a non-null, non-array object.
2. No unexpected JSON field is permitted.
3. productId must satisfy the representation and safe-integer rules.
4. quantity must satisfy the integer/range policy.
5. Success returns a newly constructed QuoteInput.
6. The caller narrows Parsed using ok before reading value or error.

The fourteen samples cover valid normal/lower/upper quantities, wrong ID type, NaN quantity, null, arrays, missing fields, numeric strings, zero, fractional/excess quantity, unsafe IDs and an unexpected tenant field.

### What is still not established?

- That productId exists.
- That the caller can access the product or tenant.
- That stock is available or reserved atomically.
- That a client-supplied price should be trusted.
- That the request body was within a safe byte limit.
- That malformed JSON was caught by the transport/body-parser layer.
- That arbitrary JavaScript proxies/getters/prototypes have been sanitized.
- That every future code path preserves the validated invariant.

This is a small JSON-data parser, not a universal object-security library or a complete API server. M5/M6 will attach boundary handling to real routes; M7/M8 handle identity/permissions.

The one-through-ten rule is an example policy. In a real application decide whether such a limit belongs in the input schema or a product-specific business rule, and keep the source of that policy clear.

### Type predicates are contracts too

**Verified example 24-lying-guard: A user-written type predicate can lie**

```typescript
interface User { name: string }
function isUser(value: unknown): value is User {
  return true; // Incorrect implementation.
}
const input: unknown = 7;
if (isUser(input)) {
  try { console.log(input.name.toUpperCase()); }
  catch (error: unknown) {
    console.log(error instanceof Error ? error.name : 'unknown failure');
  }
}
```

Compiler accepted. Actual runtime output:

```text
TypeError
```


The compiler trusts this explicitly declared predicate. It does not prove that the body correctly establishes the claimed User shape.

The predicate intentionally lies, and execution throws. Review and test custom guards with hostile/boundary inputs. A schema library can provide systematic parsing and inferred types, but the schema and transformations must still describe the intended contract correctly.

Do not generalize from this to “types are useless.” The lesson is that unchecked assertions, any, inaccurate declarations and incorrect predicates can undermine the facts the checker relies on.

---

## 3.14 Where TypeScript fits in application architecture

### Separate the contracts

| Layer | Static description | Runtime responsibility |
| --- | --- | --- |
| Transport input | unknown before parsing | Decode, limit, validate and map failures |
| Request DTO | Validated field/value shape | Construct from accepted input |
| Application service | Typed operation inputs/results | Permissions, business rules, orchestration |
| Database adapter | Query/row types | Parameterization, constraints, transactions |
| Upstream adapter | Expected response/result type | Status/body/schema checks and error mapping |
| Public response DTO | Intended exposed fields | Explicit projection/serialization |
| Shared package | Compile-time consumer contract | Version compatibility at deployed boundaries |

A shared TypeScript interface can catch mismatches between checked callers in a coordinated build. It does not force an independently deployed old service to send the new format. Distributed contracts still need runtime compatibility and versioning decisions.

Likewise, a type called AuthorizedUser does not itself authenticate anyone. The construction path must establish the identity/permission facts it claims.

### Compiler options are part of the explanation

| Option/tooling concern | Why it matters |
| --- | --- |
| strict | Enables a family of stronger checks |
| strictNullChecks | Keeps null/undefined distinct from definitely present values |
| noImplicitAny | Flags parameters/positions requiring an implicit any where applicable |
| noUncheckedIndexedAccess | Reflects possibly missing indexed values |
| exactOptionalPropertyTypes | Distinguishes omitted optional fields from explicit undefined assignments |
| noEmitOnError | Blocks compiler output when errors are reported |
| noEmit | Check without producing output through this compiler |
| target | Controls the JavaScript syntax target for emission |
| module/moduleResolution | Model the project's module/runtime/toolchain setup |
| lib and ambient declarations | Describe APIs to the checker; do not install those APIs |

noEmitOnError is enabled by this verifier; do not assume every TypeScript setup stops emission by default. A separate transpiler or framework build can have its own behavior, so ensure CI actually runs type checking and gates release as intended.

A declaration for an API is not a polyfill. Merely selecting a newer lib does not make that API available in an older runtime.

References: [strict](https://www.typescriptlang.org/tsconfig/strict.html), [noEmitOnError](https://www.typescriptlang.org/tsconfig/noEmitOnError.html), [lib](https://www.typescriptlang.org/tsconfig/lib.html) and [types](https://www.typescriptlang.org/tsconfig/types.html).

### Modules and declaration files

A .d.ts file describes types for existing runtime code; it does not implement that code. An inaccurate declaration can make a bad runtime assumption look valid.

Type-only imports can carry compile-time names without requiring runtime exports for those names. Normal value imports must correspond to actual module behavior.

This verifier uses .mts inputs and emits .mjs with NodeNext settings. A real Node/Next/library project must choose module options for its own toolchain; copying this isolated teaching configuration blindly is not the goal.

Reference: [TypeScript modules](https://www.typescriptlang.org/docs/handbook/2/modules.html).

### A practical development loop

1. Define external input and public output contracts.
2. Validate external data and select output fields with executable code.
3. Describe service relationships and valid states with types.
4. Let inference handle straightforward local values.
5. Run type checking as a required check.
6. Test important runtime failures and invariants separately.
7. Recheck declarations/runtime assumptions when a dependency changes.

**Resume connection:** explain both the developer benefit and the boundary limit. “I used TypeScript” becomes more convincing when you can show a missed variant caught during refactoring and invalid external data rejected at runtime.

---

## Must remember

1. TypeScript provides static checking; JavaScript still executes at runtime.
2. Interfaces and type aliases do not create validators or constructors.
3. Checking, transformation and emission are separate toolchain concerns.
4. Inference provides types without annotations everywhere.
5. number does not mean positive integer, finite value or valid money.
6. Structural compatibility usually requires the needed shape, not exact runtime fields.
7. Fresh-literal excess-property checks are not universal sanitization.
8. Unions require narrowing before variant-specific operations.
9. Nullability and indexed access depend on compiler options.
10. Optional property absence and present undefined can differ.
11. any bypasses useful checking; unknown requires evidence.
12. Assertions and non-null assertions do not execute checks.
13. type and interface overlap but have different capabilities.
14. Intersections require both contracts and can become impossible.
15. Discriminated unions model valid states and support exhaustive handling.
16. Generics preserve relationships; their parameters do not exist at runtime.
17. keyof, type-position typeof and indexed access derive descriptions.
18. Utility types change descriptions, not object contents.
19. readonly and as const do not freeze runtime objects.
20. satisfies checks compatibility without being runtime validation.
21. Promise types do not automatically encode rejection contracts.
22. A void callback consumer may ignore a real returned value/promise.
23. A declared type predicate can be incorrectly implemented.
24. Typed data still needs authorization, transactions and business rules.
25. Compiler declarations do not create missing runtime APIs.
26. Passing type checks is one kind of evidence, not proof of all behavior.

---

## Common wrong answers

| Wrong claim | Correction |
| --- | --- |
| “TypeScript runs instead of JavaScript.” | The runtime executes JavaScript or toolchain-transformed code |
| “An interface validates my JSON.” | Interfaces are erased; execute validation |
| “Every TypeScript construct is erased.” | Some features emit runtime code |
| “No annotation means no checking.” | Inference supplies types |
| “number means integer.” | Integer/range/finiteness need checks |
| “PublicUser assignment removes private fields.” | The runtime object is unchanged |
| “Extra fields always cause a type error.” | Fresh-literal checks differ from general structural compatibility |
| “strict disallows explicit any.” | Explicit any remains an escape hatch |
| “unknown is just any with another name.” | unknown restricts operations until evidence/assertion |
| “as number converts a string.” | It changes the checker view, not the value |
| “A non-null assertion prevents null errors.” | It performs no runtime check |
| “Optional always means present undefined is allowed.” | exactOptionalPropertyTypes can distinguish the assignment |
| “Arrays always have an element at index zero.” | An indexed value can be missing |
| “type and interface are identical in every use.” | Aliases can name unions; interfaces can merge |
| “An intersection merges two objects.” | It combines type requirements |
| “Generics create runtime type information.” | Type parameters are erased |
| “Omit deletes the property.” | It changes a type; executable code must select/delete actual data |
| “Readonly means deep immutable.” | It is a static view, often shallow, with aliases still relevant |
| “as const calls Object.freeze.” | It does not |
| “satisfies validates environment configuration.” | It checks the compiled expression, not arbitrary loaded data |
| “`Promise<T>` specifies every possible failure type.” | It describes fulfillment, not a checked rejection union |
| “void means nothing can be returned at runtime.” | A callback may return a value that the consumer ignores |
| “A type predicate is proven correct.” | Its explicitly declared contract can lie |
| “Shared types guarantee service version compatibility.” | Independently deployed producers still need compatible runtime contracts |
| “A valid DTO proves the caller owns the resource.” | Authorization is separate |
| “A lib declaration installs the API.” | It supplies types, not runtime implementation |
| “Any build that strips TypeScript did type checking.” | Check the actual toolchain and CI gate |

---

## Interview Q&A bank

**Q1. What is TypeScript?**
A statically checked extension of JavaScript with tooling and type syntax. Runtime execution still follows the emitted/transformed JavaScript.
**Follow-up:** Which checks disappear? Interfaces, aliases and annotations do not remain as runtime validators.

**Q2. Why use it in a backend?**
It catches many incompatible calls, describes service contracts and valid states, and supports safer refactoring.
**Follow-up:** Does it replace request validation? No.

**Q3. Type checking vs transpilation?**
Checking analyzes relationships; transformation/emission produces runnable code. A tool can do one without the other.
**Follow-up:** Where is your CI check enforced?

**Q4. Annotation vs inference?**
Annotations declare a contract; inference derives types from expressions and context.
**Follow-up:** Must every local variable be annotated? No.

**Q5. What is structural typing?**
Compatibility commonly depends on required structure rather than a shared declared name.
**Follow-up:** Does assigning a narrower public type strip extra fields? No.

**Q6. Why do some extra fields cause errors and others do not?**
Fresh object literals receive excess-property checks in relevant contexts; existing compatible objects can retain extras.
**Follow-up:** How do you create a safe response? Explicitly project allowed fields.

**Q7. any vs unknown?**
any bypasses checking along that path. unknown accepts values but requires evidence before unsafe operations.
**Follow-up:** Which would you choose for external JSON? unknown before validation.

**Q8. What is a union?**
A value may match one of the alternatives. Narrow before using operations specific to one.
**Follow-up:** Why can truthiness lose an empty string or zero?

**Q9. What is narrowing?**
Control-flow evidence reduces the possibilities the checker considers at a point.
**Follow-up:** Does typeof value being object exclude null? No.

**Q10. What does strictNullChecks change?**
Null/undefined remain distinct possibilities rather than being treated as definitely present values.
**Follow-up:** Does value! execute a check? No.

**Q11. Optional property vs property containing undefined?**
An optional property may be absent; a required property with undefined in its type must still be present in the described shape.
**Follow-up:** What does exactOptionalPropertyTypes add? It distinguishes absence from explicit undefined assignment unless undefined is permitted.

**Q12. Why use noUncheckedIndexedAccess?**
It exposes possibly missing indexed values instead of assuming every lookup succeeds.
**Follow-up:** How do you repair a possibly missing first element? Check it or establish a real nonempty contract.

**Q13. type vs interface?**
Both describe object contracts. Aliases can name unions/other expressions; interfaces support extension and suitable declaration merging.
**Follow-up:** Does either construct runtime data? No.

**Q14. Union vs intersection?**
A union allows alternatives; an intersection requires combined obligations.
**Follow-up:** What if the same field must be string and number? The property requirement can become never.

**Q15. What is never for?**
It describes impossible values/paths in the type model and supports exhaustive checks.
**Follow-up:** How does adding a job state expose missed handling? The remaining variant no longer fits never.

**Q16. What is a discriminated union?**
A set of alternatives distinguished by a common property with distinct literal values.
**Follow-up:** Why prefer it to unrelated optional value/error fields? It describes valid combinations more precisely.

**Q17. What problem do generics solve?**
They preserve reusable relationships between types at each call.
**Follow-up:** Why not return any? It discards the relationship and checking.

**Q18. Explain keyof and T[K].**
keyof describes allowable keys; T[K] selects a property type for a key.
**Follow-up:** Does the key constraint create runtime checks for arbitrary strings? No.

**Q19. What do utility types do?**
They derive new type descriptions from existing ones.
**Follow-up:** Does Omit remove a secret field at runtime? No.

**Q20. readonly vs const vs freeze?**
Const restricts binding reassignment, readonly restricts checked writes through a view, and freeze applies shallow runtime restrictions to an object.
**Follow-up:** Can another alias still change a readonly view's observed data? Yes.

**Q21. What does as const do?**
It preserves suitable literal information and readonly literal structure for checking.
**Follow-up:** Does it freeze an array? No.

**Q22. What is satisfies for?**
It checks expression compatibility while retaining its inferred type rather than assigning a broad annotation.
**Follow-up:** Can contextual typing influence inference? Yes.

**Q23. What does `Promise<T>` describe?**
Its fulfillment value type. Known failure values can be modeled with a result union, but promise rejection is not a separate checked type parameter.
**Follow-up:** Does it change scheduling? No; M2 still applies.

**Q24. Why can a void callback return a value?**
The callback contract permits the consumer to ignore the result; a value-returning implementation can be assigned in that context.
**Follow-up:** Does that mean the consumer awaits an async callback? No.

**Q25. Are user-written type guards always safe?**
No. An explicitly declared predicate can assert a relationship its implementation does not establish.
**Follow-up:** How do you improve confidence? Review the checks and verify valid, invalid and boundary inputs.

**Q26. How do you validate external input?**
Treat it as unknown, execute format/shape/value checks, then construct the accepted typed value.
**Follow-up:** What still needs enforcement? Identity, permissions, existence, business rules and state invariants.

**Q27. What is a declaration file?**
A .d.ts describes types for runtime code; it supplies no implementation.
**Follow-up:** Can inaccurate declarations hide a runtime error? Yes.

**Q28. Does compiling imply no bugs?**
No. Types address selected relationships under assumptions. Runtime behavior, external inputs, permissions, races and product requirements still need appropriate evidence.
**Follow-up:** Explain one compiler check and one separate runtime check from this module.

---

## Practice

1. **Trace erasure.** Predict example 01's emitted JavaScript before reading the captured output. Identify which names are only types.
2. **Project safely.** Extend PublicUser with an avatar URL. Construct a new response and show that passwordHash and email remain absent.
3. **Narrow without losing valid values.** Write a function accepting number | null that preserves zero and handles null explicitly.
4. **Handle an optional patch.** Define omission as “unchanged” and null as “clear” for a display name. Explain the type and runtime checks.
5. **Complete the state machine.** Add a canceled job variant to example 16. Handle every variant so the compiler accepts it.
6. **Preserve a relationship.** Write a generic last function returning T | undefined for a readonly array. Test an empty array.
7. **Review a DTO.** Explain why Partial of a complete account row is a risky external update contract. Select only allowed fields.
8. **Break the guard.** Replace example 24's incorrect predicate with checks for non-null object and a string name. Test null, arrays, numbers and a missing name.
9. **Extend the validator.** Add a permitted coupon field with a bounded string policy. Define missing/empty/null behavior and verify both accepted and rejected inputs.
10. **Defend the architecture.** A frontend and backend share a TypeScript package. Explain what it catches during a joint build and what can still fail when their deployed versions differ.

### Answer checkpoints

- **2:** annotation alone does not filter; inspect the serialized constructed object.
- **3:** use an explicit null check instead of discarding zero through truthiness.
- **4:** optional plus null captures two states, but the handler must actually distinguish them.
- **5:** a deliberately exhaustive default still reveals forgotten variants.
- **6:** empty input must remain represented; do not assert existence without a contract.
- **7:** ownership/role/password fields should not become editable merely because they are optional.
- **8:** a useful predicate's runtime checks must establish its declared shape.
- **9:** change the field whitelist and accepted result construction as well as the static type.
- **10:** checked source compatibility does not prove deployed wire-format compatibility.

---

## Exit checklist

- [ ] I can explain type checking, transformation and runtime execution separately.
- [ ] I can identify erased syntax and avoid claiming all TypeScript features are erased.
- [ ] I can use inference and explicit boundary annotations deliberately.
- [ ] I understand structural compatibility and fresh-literal excess checks.
- [ ] I can prevent secret fields from leaking through response projection.
- [ ] I can narrow unions without dropping zero or empty strings accidentally.
- [ ] I can explain nullability, optional fields and indexed-access options.
- [ ] I can distinguish any, unknown, assertions and runtime validation.
- [ ] I can choose type/interface and debug incompatible intersections.
- [ ] I can model a result/job state with a discriminated union.
- [ ] I can implement exhaustive handling using never.
- [ ] I can explain a generic getter's input/output relationship.
- [ ] I can derive types with keyof, typeof, indexed access and common utilities.
- [ ] I can distinguish readonly/const/as const from runtime freezing and copying.
- [ ] I can explain satisfies without calling it runtime validation.
- [ ] I can explain Promise fulfillment types and void callback return behavior.
- [ ] I can review/test custom type predicates.
- [ ] I can run the validator and explain all fourteen input outcomes.
- [ ] I can state which authorization/state guarantees are still missing.
- [ ] I can run all 26 compiler/runtime cases and explain their evidence.

---

## Next

[M4: Node.js — What It Is and How It Works](/docs/resume-skills/nodejs) connects JavaScript, asynchronous control flow and typed contracts to V8, native APIs, libuv, OS I/O, worker pools, event-loop phases, modules, streams and worker threads.

Keep these boundaries clear: types describe relationships, runtime validation establishes input facts, and the runtime/application/database determine execution and state guarantees.

### Sources and reproducible evidence

- [TypeScript basics](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html), [object types](https://www.typescriptlang.org/docs/handbook/2/objects.html) and [type compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html).
- [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html), [generics](https://www.typescriptlang.org/docs/handbook/2/generics.html), [More on Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html) and [utility types](https://www.typescriptlang.org/docs/handbook/utility-types.html).
- [keyof](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html), [type-position typeof](https://www.typescriptlang.org/docs/handbook/2/typeof-types.html), [indexed access](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html), [satisfies](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html), [modules](https://www.typescriptlang.org/docs/handbook/2/modules.html) and [enums](https://www.typescriptlang.org/docs/handbook/enums.html).
- Compiler options: [strict](https://www.typescriptlang.org/tsconfig/strict.html), [exactOptionalPropertyTypes](https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html), [noUncheckedIndexedAccess](https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html), [noEmitOnError](https://www.typescriptlang.org/tsconfig/noEmitOnError.html), [lib](https://www.typescriptlang.org/tsconfig/lib.html) and [types](https://www.typescriptlang.org/tsconfig/types.html).
- Original artifacts: examples/resume-skills/module-3-typescript/cases.json, verify.mjs, results.json and verification-output.txt. results.json includes actual emitted JavaScript for accepted cases and actual diagnostics for rejected cases.
- Verified with TypeScript 7.0.2 and Node.js v22.14.0 using the explicit configuration above. Diagnostic wording can change across compiler versions; the preserved run states what was checked here.
