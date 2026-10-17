# Module 3: TypeScript Fundamentals

Twenty-six isolated compiler/runtime examples for the Resume Skills handbook.

From the repository root:

```powershell
node examples/resume-skills/module-3-typescript/verify.mjs
node examples/resume-skills/module-3-typescript/verify.mjs 23-boundary
node examples/resume-skills/module-3-typescript/verify.mjs 16-exhaustive
```

The runner uses the TypeScript compiler installed in study-guide/node_modules/typescript/bin/tsc. Study-guide dependencies must already be installed; no new dependencies or external services are needed for verification. To use a different compiler script, set PLACEMENT_TSC_PATH to its bin/tsc path. Diagnostic wording/codes can vary across compiler versions.

Verified with TypeScript 7.0.2 and Node.js v22.14.0. Sixteen cases compile to ES-module JavaScript and run; ten deliberately invalid cases must be rejected with exactly the expected distinct diagnostic codes and must not emit JavaScript. Invalid cases use no diagnostic suppression comments.

Each case gets a temporary project containing input.mts and tsconfig.json. The compiler options use ES2022, NodeNext, strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes and noEmitOnError. Ambient package types are explicitly empty; ES2022/DOM declarations support these self-contained snippets including console. They do not provide browser runtime APIs in Node. A real Node application should use appropriate Node declarations.

Compiler invocations have a ten-second timeout; emitted JavaScript executions have a five-second timeout. The runner checks exit codes, stderr, diagnostic codes, no emission for rejected cases and exact runtime output for accepted cases. Finally it removes only the exact temporary directory it created, after verifying its resolved parent and name.

Artifacts:

- cases.json: source and expected output or diagnostic codes.
- verify.mjs: compiler/runtime verification harness.
- results.json: actual diagnostics, emitted JavaScript, runtime output and compiler options.
- verification-output.txt: preserved full-run log.
- validation-summary.json and site-build-output.txt: chapter/site verification evidence.

Coverage includes erasure, inference, structural compatibility, excess properties, narrowing, unknown/any/assertions, nullability, indexed access, readonly aliases, discriminated results, exhaustiveness, interfaces/aliases, generics, satisfies, utilities, promise/void function types, tuples and impossible intersections. The runtime input parser checks fourteen normal/boundary/invalid samples.

These checks establish the documented compiler behavior and example outputs. The parser is a small JSON-data boundary demonstration; it does not implement authentication, resource authorization, body-size limits, inventory transactions or universal JavaScript object sanitization.
