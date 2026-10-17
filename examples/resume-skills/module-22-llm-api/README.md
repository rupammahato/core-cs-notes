# M22: LLM and AI API Fundamentals

Part 24 practice fixture, recorded 15 October 2026 on Windows/Python 3.12.10. Direct dependencies: OpenAI Python SDK 3.31.0, httpx 0.28.1 and tiktoken 0.14.0. The SDK supports this explicitly supplied httpx client; its additional dependencies are pinned in requirements-lock.txt. The handbook site's dependencies were not upgraded.

## Reproduce

From the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-22-llm-api/.venv
& examples/resume-skills/module-22-llm-api/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-22-llm-api/requirements-lock.txt
& examples/resume-skills/module-22-llm-api/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-22-llm-api/verify.py
```

Installation and the first cl100k_base vocabulary download need network access. The vocabulary is cached under the ignored .token-cache/ directory; runtime provider-like requests go to an owned 127.0.0.1 HTTP peer. The client rejects external origins and supplies a fixed synthetic key, without reading real credentials. No model/provider account or inference charge is involved. fixture-model and fixture/provider-model are local placeholders, not real model recommendations.

To reproduce handbook validation after installing study-guide dependencies:

```powershell
python -X utf8 examples/resume-skills/module-22-llm-api/validate_site.py
```

The validator uses a cached Google Fonts response fixture when available; otherwise the Next.js handbook build needs font network access. It starts and stops an owned temporary site preview. Port 3000 stays stopped. Docker is not started.

## Verified results

| Group | Checks |
| --- | --- |
| Actual tokenizer / capacity arithmetic | 5 |
| Runtime card contract | 10 |
| SDK / Responses HTTP parsing | 11 |
| Chat/OpenRouter-shaped serialization | 4 |
| Actual HTTP SSE handling | 5 |
| Tool HTTP exchange / round bound | 6 |
| Local tool authorization / replay | 6 |
| Actual HTTP retry / timeout behavior | 12 |
| Retry-After / jitter policy | 4 |
| Decimal cost / budget / concurrency | 8 |
| Deterministic grader mechanics | 4 |
| Local-origin boundary | 2 |
| Resource closure | 2 |
| **Total** | **79** |

The actual SDK sends and parses local HTTP. The handwritten peer controls complete, refused, incomplete, empty and invalid responses; Responses function-call rounds; fragmented UTF-8 SSE; truncated/failed streams; 429/503/400/401/quota conditions and a short real read timeout. Its synthetic usage includes cached input and a reasoning subset. No actual language model produces these outputs.

The retry wrapper owns attempt counting with SDK retries disabled. It honors numeric/date Retry-After values, rejects hints beyond its remaining budget and bounds fallback jitter. The timeout case has one network attempt and is not automatically replayed. HTTP phase timeouts are distinct from a strict end-to-end deadline.

Tool identity comes from the trusted caller, and model arguments cannot select the principal. The fixture rejects unknown tools, another owner's note and conflicting call reuse. Its replay dictionary is process-local and read-only; it is not durable write idempotency.

The cost rates are hypothetical USD per million tokens, not provider prices. The 0.0025 estimate uses synthetic 1000 input / 200 cached-subset / 100 output tokens; its 40 reasoning tokens are already within output. Two real threads compete for one affordable reservation. The in-memory ledger retains unknown reservations and records overage liabilities; it is not distributed or crash-safe.

The four grader predictions are handcrafted. One passes by construction, which is not 25% model accuracy. Format, label correctness and allowed-source scope are scored separately; free-text entailment/grounding is not established by this grader.

## Files

- client.py: local-only SDK constructor, Responses schema request and chat-compatible request.
- contracts.py: card schema, runtime limits/source scope and complete/refusal extraction.
- tools.py: read-only trusted-principal dispatcher and bounded function-call loop.
- streaming.py: semantic delta preview and terminal completion validation.
- reliability.py: bounded read-only HTTP retry owner and Retry-After/jitter policy.
- accounting.py: hypothetical Decimal cost and locked in-process reservation/settlement.
- evaluation.py: deterministic grader mechanics for handcrafted cases.
- fixture_server.py: counted handwritten HTTP/SSE peer; not a provider emulator or LLM.
- verify.py: actual local SDK/HTTP/tokenizer/policy/concurrency checks and cleanup.
- requirements.txt / requirements-lock.txt: direct and full dependency pins.
- dependency-check.txt: pip check output, not a security audit.
- verification-results.json / verification-output.txt / cleanup-results.json: actual evidence and resource closure.
- content-validation.json / site-validation.json / validation-summary.json: chapter fidelity and handbook build/routes/search/cleanup checks.
- validate_site.py / site-smoke.mjs: repeatable handbook validation.

The chapter embeds seven source files exactly, eight observed result objects, 30 interview Q&As, ten exercises and twelve unchecked learning items. Generated environments, tokenizer cache and Python bytecode are ignored.

## Limits

No real provider request, model inference, key/account access, paid charge, hosted routing/retention verification, browser streaming UI, model-quality evaluation, production deployment or durable database was used. Tests establish SDK serialization/parsing and selected local application behavior. They do not establish live provider schema enforcement, model correctness, prompt-injection resistance, real pricing, latency or billing. OpenAI-specific API guidance was researched with the OpenAI Docs skill; OpenRouter guidance uses its official documentation.
