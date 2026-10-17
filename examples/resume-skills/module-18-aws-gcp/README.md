# M18: AWS and GCP Fundamentals for This Resume

Part 20 examples: official SDK message serialization and Google-auth token verification offline, plus real loopback HTTP cache/worker experiments with transactional SQLite. Recorded 14 October 2026 on Windows, CPython 3.12.10; google-auth 2.62.0, google-cloud-tasks 2.26.0, cryptography 50.0.2 and requests 2.34.2.

## Run

From the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-18-aws-gcp/.venv
& 'examples/resume-skills/module-18-aws-gcp/.venv/Scripts/python.exe' -m pip install -r examples/resume-skills/module-18-aws-gcp/requirements.lock.txt
& 'examples/resume-skills/module-18-aws-gcp/.venv/Scripts/python.exe' -X utf8 examples/resume-skills/module-18-aws-gcp/verify.py
```

Choose a suitable Python 3.12 interpreter. Initial package install needs registry access; verification uses local fixtures. The full observed dependency snapshot is pinned without hashes. It does not promise identical wheel availability on every platform.

No AWS/GCP client/account/credentials are used. task_request.py constructs message types without a CloudTasksClient or ADC lookup. The fictional project, service account and example.test URL are teaching values; no request is enqueued. Tokens are signed with generated local RSA keys, and Google-auth receives a fixture public-key response through an injected transport. No tested token is Google-issued and no provider certificates are fetched.

The verifier owns only loopback HTTP listeners and a validated temporary directory/database under this module. It closes the listeners/threads and removes the scratch directory/database. Generated private keys stay in memory and bearer tokens are not written into results. Port 3000 is unused; Docker is not started.

## Results

| Group | Checks |
| --- | --- |
| Official SDK message | 9 |
| Token validation | 14 |
| Real HTTP/SQLite worker | 16 |
| Real HTTP local cache | 14 |
| **Total** | **53** |

The suite verifies bytes/base64 and protobuf round trips, stable tenant-scoped task names, explicit identity/audience/deadline fields, negative token/signature/caller cases, forged-header rejection, canonical job/tenant scope, pre/post-commit failure responses, 16 concurrent duplicate requests with one effect, recreated-handler replay, cache variants, private/auth/cookie bypass, error/Vary handling, injected-clock TTL and local invalidation.

These are local application/library checks. EC2/VPC/IAM/ALB/CloudFront and Cloud Tasks service behavior are researched from official documentation. The local cache is not CloudFront and the request driver is not Cloud Tasks. The effect is a SQLite row in the same transaction, not an external payment/vector write.

## Files

- task_request.py: offline official SDK message builder; trusted configured destination, bytes body, OIDC fields and hashed operation name.
- worker.py: official token verifier integration, canonical tenant/job lookup, unique transactional effect and HTTP handler.
- cache_demo.py: conservative public-response cache lesson, not a general HTTP cache.
- verify.py: actual fixtures, negative tests, concurrent delivery, HTTP origin/proxy and scoped cleanup.
- iam-read-object-policy.json / ec2-trust-policy.json: illustrative AWS policies, parsed locally but not uploaded or evaluated by AWS.
- requirements.txt / requirements.lock.txt: direct and full observed dependency snapshots.
- verification-results.json / verification-output.txt: actual check/runtime/results.
- task-request.json: offline SDK JSON after protobuf round trip, not a captured provider response.
- certificate-transport-results.json: local trust/transport boundary.
- cleanup-results.json: closed listeners and temporary database removal.
- content-validation.json / site-validation.json / validation-summary.json: chapter/source and website evidence.

The chapter includes 30 interview Q&As, ten exercises, 12 unchecked learning items, official sources and end-to-end architecture/failure walkthroughs. It embeds teaching sources and recorded SDK/cache/delivery JSON exactly. The current installed Task schema includes retry_config; provider and SDK versions matter when applying defaults/overrides.

No live cloud policies/network, EC2/ALB/CDN resources, Google-issued token/key rotation, queue creation/dispatch/backoff/deadline, public TLS, cloud failover, outbox dispatcher, external effect or production load/cost measurement was verified. No cloud charges were incurred by these examples.
