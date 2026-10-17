# Resume Skills Placement Handbook — Part 21
# Module 19: Git, CI/CD, Testing, Observability and Performance

**Estimated time: 5–6 hours | Tier: 1 concepts | Requires: M6 APIs, M16 Docker, M17 deployment and M18 cloud; M4 Node.js for the executable service**

---

## Why this module exists

A backend engineer needs to explain how a change becomes a release, how a broken change is caught, and how a production symptom is investigated. Git, a CI platform, tests and telemetry support different parts of that path. A green pipeline or a high requests-per-second number is useful only when you can say exactly what it establishes.

This chapter connects the resume's Git/GitHub Actions/deployment skills with a practical release workflow and defensible performance claims. It teaches fundamentals and useful interview follow-ups; it is not a measured company-question frequency ranking.

**Organizing principle: identify the exact source, verify the intended behavior, promote a known artifact, and keep evidence of what the running system does.**

---

## 1. One change from edit to operation

```text
Working files -> reviewed staged snapshot -> Git commit / PR
   -> CI: install/check/test/package
   -> artifact + revision + integrity/provenance evidence
   -> deployment environment + configuration
   -> readiness/useful-route verification
   -> selected release + monitored rollout
   -> diagnose, roll forward or roll back when needed
```

| Tool or practice | Main question |
| --- | --- |
| Git | Which snapshot and history are we discussing? |
| CI | Does this change pass the checks that run automatically? |
| Delivery/deployment pipeline | Which artifact moves to which environment, after which gates? |
| Tests | Which behavior and failure boundaries have evidence? |
| Logs | Which events happened for this request/job? |
| Metrics | How often, how long, how many and how saturated? |
| Traces | Which operations formed this request's path? |
| Performance experiment | How did this workload behave under stated conditions? |

These support each other. A commit does not prove correctness; a test does not prove capacity; a trace does not authenticate a caller; a selected release does not prove the database is compatible.

Revisit [M17](/docs/resume-skills/linux-deployment-nginx-pm2) for process/reload/rollback boundaries and [M18](/docs/resume-skills/aws-gcp-fundamentals) for cloud routing, identities and managed work.

---

## 2. Execution environment and evidence boundary

**Recorded on 14 October 2026:**

| Tool/library | Recorded version |
| --- | --- |
| Python | 3.12.10 |
| Node | v22.14.0 |
| Git | git version 2.55.0.windows.5 |
| PyYAML | 6.0.2 |
| @opentelemetry/api | 1.9.1 |
| @opentelemetry/core | 2.12.0 |
| @opentelemetry/sdk-trace-base | 2.12.0 |
| @opentelemetry/sdk-trace-node | 2.12.0 |

The verifier creates disposable repositories, a local bare remote, release directories and candidate processes under a validated owned scratch directory. Git mutations, commits and pushes affect only those fixtures. The handbook repository's HEAD stays unchanged; no main-repository staging, commit, history rewrite or remote push is performed.

The HTTP gateway, dependency endpoint and load generator run in **one Node process** for the telemetry/load lesson. Candidate release smoke checks use separate owned Node processes. All listening sockets bind to host loopback with ephemeral ports. Port 3000 is unused; Docker and cloud accounts are not needed.

### Reproduce

From the repository root in PowerShell:

```powershell
Set-Location examples/resume-skills/module-19-git-ci-observability
npm ci --ignore-scripts
python -m venv .venv
& '.venv/Scripts/python.exe' -m pip install -r requirements.txt
& '.venv/Scripts/python.exe' -X utf8 verify.py
```

Use an appropriate Python 3.12 interpreter. PyYAML parses the teaching workflow; Node runs the service/tests and Git runs fixture history operations. Initial npm/pip installation needs registry access. package-lock.json records exact JavaScript dependencies with registry integrity metadata; requirements.txt pins the YAML parser without hashes.

The recorded npm audit returned zero reported vulnerabilities for this installed snapshot. That is an audit result at a point in time, not proof of application security. Official action tags were resolved to full commits and stored in action-pins.json.

The GitHub Actions YAML stays at ci.example.yml inside the example folder, outside .github/workflows. It was parsed and statically checked, **not executed on a hosted Actions runner**. The local release lab verifies real packaging, digest checks and HTTP candidates; it does not deploy a remote server or exercise branch protection/environment approvals.

---

## 3. Git fundamentals: working tree, index and commit

Git records snapshots and their relationships. A commit identifies a snapshot together with metadata and parent commit relationships. A branch is a movable reference to a commit; HEAD indicates the current checkout context. In a detached checkout, HEAD can identify a commit directly rather than an ordinary branch.

The **working tree** contains your current files. The **index/staging area** holds the proposed next snapshot. The **HEAD commit** is the current recorded snapshot. git add updates the index for selected content; git commit records the index. Editing a file after staging can make its working version different from both staged and committed versions. [Git's recording-changes guide](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository)

Actual fixture contents:

```json
{
  "head": "base",
  "index": "staged",
  "working": "working"
}
```

| Command | What to inspect |
| --- | --- |
| git status --short | Which paths have staged/unstaged/untracked changes? |
| git diff | Working-tree changes relative to the index |
| git diff --staged | Proposed staged changes relative to HEAD |
| git show HEAD:path | Content in the recorded snapshot |
| git show :path | Content currently in the index |
| git log --graph --oneline --decorate --all | Commit relationships and references |

In the fixture, git restore --staged state.txt reset the index's version to the recorded content while preserving the edited working file. A later git restore state.txt restored the working file from the index. These are different operations. [Git restore reference](https://git-scm.com/docs/git-restore)

A commit message should explain the concrete change and its reason. A pull request adds review/discussion and checks around commits; it is a hosting workflow, not the Git object that stores your source snapshot. .gitignore prevents ordinary accidental addition of matching untracked files; it does not erase already committed secrets or remove tracked files automatically.

---

## 4. Branching, merging, rebasing and conflicts

### 4.1 Fast-forward versus merge commit

When the current tip is an ancestor of the incoming tip, a fast-forward can move the reference to that existing commit. Diverged histories need a different integration choice. A normal merge can create a commit with both histories as parents; a deliberate no-fast-forward merge can also record a merge boundary.

```text
Before a diverged merge:        After a merge commit:

A--B (main)                    A--B------M (main)
 \                              \      /
  C (feature)                    C----/  (feature)
```

The fixture made independent main/feature changes and observed two parent IDs in the merge commit. A separate fast-forward moved a peer checkout to an already existing remote commit. It then created divergence and verified that --ff-only refused to integrate it without moving HEAD. [Git branching and merging](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)

### 4.2 What a conflict means

A conflict means Git could not automatically select a combined result for some content. It is not proof that one branch is wrong. Inspect the intent of both changes, resolve the resulting file deliberately, stage it, and complete the operation; rerun relevant checks on the combined behavior.

```bash
git status
git diff
# Edit the conflicted file to the intended final content.
git add path/to/file
git commit
```

For the fixture's same-line conflict, Git stopped with unmerged index entries and conflict markers. git merge --abort restored its pre-merge HEAD/file. A second attempt was resolved explicitly and produced a two-parent merge. A rebase conflict uses its own continue/abort workflow; do not treat every in-progress operation as a merge.

### 4.3 Rebase replays commits

Rebase takes selected changes and replays them on a new base. The rewritten commits have new identities. It can create a linear integration history, but it does not make conflict resolution or review unnecessary. Rewriting commits already used by others needs coordination. [Git rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)

Actual replay:

```json
{
  "before": "ccea9dcb72ca1f6f6d22a233a3b8a76b956fdac6",
  "after": "c39640cf02d94d22ad7454b0b482d87b7a8a4d95",
  "new_parent": "8736d1a5686e0bd5c803508239d8d55c55e3b2b3"
}
```

The new commit had a different ID and the advanced main commit as its parent. The fixture compared the old/new file patch and found the intended patch unchanged. That is evidence for this replay, not a guarantee that every rebase preserves every behavioral interaction.

### 4.4 Revert, reset and restore answer different questions

| Operation | Typical purpose | Effect to understand |
| --- | --- | --- |
| restore | Change working/index content from a selected source | Can discard selected local content depending on options |
| reset --soft | Move HEAD while retaining index/work content | Changes which snapshot is considered committed |
| reset --mixed | Move HEAD and reset index, retain working content | Changes staged state as well |
| reset --hard | Move HEAD and reset index/working content | Can discard local tracked changes |
| revert | Make a new inverse commit | Keeps the original commit in history; inverse can conflict |

The fixture tests restore and revert. Reset modes are documented concepts, not commands run against your handbook repository. A reverted code change does not undo a sent email, deployed schema or payment automatically. [Git reset](https://git-scm.com/docs/git-reset), [Git revert](https://git-scm.com/docs/git-revert)

---

## 5. Remotes, fetch, pull and source identity

A remote name such as origin identifies a configured repository location. A remote-tracking reference such as origin/main is a locally stored observation updated by operations like fetch. It is not a permanently live view of the remote.

The local remote experiment recorded:

```json
{
  "before_peer_head": "8736d1a5686e0bd5c803508239d8d55c55e3b2b3",
  "remote_head": "be6a4cba77016d0457de1755dd8898cab5b958f4"
}
```

After the peer fetched, origin/main changed but its own HEAD and working snapshot stayed on the earlier commit. An explicit fast-forward then integrated the new tip. pull combines fetching with a selected integration behavior, which can depend on options/configuration. Explain that behavior instead of assuming pull always creates a merge commit. [Git fetch](https://git-scm.com/docs/git-fetch)

For a release, record the full source revision rather than only a branch name that can move. A tag can identify a release point, but tags/references also have policy and trust requirements. The fixture's release revision includes a committed copy of the actual source-bundle files and verifies their Git blob identities before packaging. No commit was made in the main handbook repository.

Integrity is not authorship or approval. Knowing an artifact's hash confirms identity relative to an expected hash; trusting the expected hash/source and knowing who approved it are additional requirements.

---

## 6. CI, continuous delivery and continuous deployment

**Continuous integration** means integrating changes frequently with automated checks that expose integration problems. **Continuous delivery** keeps a change in a deployable state with a release decision still possible. **Continuous deployment** automatically releases qualifying changes to the chosen production environment. Teams use the abbreviation CD for the latter two, so clarify which behavior is meant.

```text
CI:        install -> syntax/lint/type checks -> tests -> package evidence
Delivery:  CI -> known artifact -> staging/verification -> release decision
Deployment: qualifying artifact -> automated production rollout/promotion
```

Running a pipeline on every push is automation; its usefulness depends on meaningful checks. A pipeline that only prints success does not establish application behavior. A green result also applies to a particular revision/environment and the tests actually executed.

### 6.1 Keep stages and evidence explicit

| Stage | Useful evidence | What it does not establish alone |
| --- | --- | --- |
| Install | Lockfile-compatible dependency resolution | Correct application behavior |
| Syntax/lint/type | Selected structural rules/checks pass | Runtime input validity or useful business results |
| Unit/integration tests | Checked behaviors and failures pass | All possible inputs or production capacity |
| Package | Artifact and manifest created from intended inputs | Correct deployment environment/configuration |
| Smoke/readiness | Candidate answers selected useful probes | Long-duration correctness under all traffic |
| Promote/rollout | Intended artifact selected/routed | Data/schema rollback compatibility |
| Monitor | Error/latency/health changes observed | Automatic diagnosis without context |

Build once and promote the identified artifact where practical. Rebuilding separately for every environment can introduce different dependencies or generated output. Environment-specific configuration remains a separate input that must also be validated and tracked.

---

## 7. GitHub Actions: workflow, event, job, step and runner

A workflow describes automation triggered by configured events. Jobs execute on runners; steps in a job can run commands or use actions. Jobs can express dependencies through needs. Steps share the job's filesystem, but a shell-local variable from one step is not automatically a shell variable in the next. Use the platform's explicit environment/output mechanisms. [GitHub workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows), [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)

| Term | Concrete role |
| --- | --- |
| Event | Why this run started: push, PR or manual dispatch |
| Job | A unit with runner/settings and ordered steps |
| Runner | Machine/environment executing job steps |
| Step | Command/action invocation within the job |
| Action | Reusable implementation used by a step |
| Context/expression | Platform metadata available for configuration/conditions |
| Artifact | Named output retained/transferred from a run |
| Cache | Reusable dependency/build data that may be missing or restored |

### 7.1 The researched teaching workflow

The following file is stored outside the active workflow directory. Full action commits were resolved from the official repositories' v7 tags on the recorded date. The action's own runtime and runner requirements are separate from the application's selected Node version. [Official checkout](https://github.com/actions/checkout), [setup-node](https://github.com/actions/setup-node), [upload-artifact](https://github.com/actions/upload-artifact)

```yaml
# Teaching example: intentionally outside .github/workflows and not activated.
name: M19 fixture CI
"on":
  pull_request:
    paths: ['examples/resume-skills/module-19-git-ci-observability/**']
  push:
    branches: [main]
    paths: ['examples/resume-skills/module-19-git-ci-observability/**']
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  verify-and-package:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    defaults:
      run:
        working-directory: examples/resume-skills/module-19-git-ci-observability
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # resolved v7
        with:
          persist-credentials: false
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # resolved v7
        with:
          node-version: '22.14.0'
          cache: npm
          cache-dependency-path: examples/resume-skills/module-19-git-ci-observability/package-lock.json
      - name: Install locked dependencies
        run: npm ci --ignore-scripts
      - name: Check JavaScript syntax
        run: npm run check
      - name: Test real HTTP contracts
        run: npm test
      - name: Verify tracing and local measurement mechanics
        run: node verify.mjs
      - name: Package source bundle once
        run: python3 build_artifact.py --revision "$GITHUB_SHA"
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # resolved v7
        with:
          name: m19-source-${{ github.sha }}
          path: |
            examples/resume-skills/module-19-git-ci-observability/release-artifact.zip
            examples/resume-skills/module-19-git-ci-observability/release-manifest.json
            examples/resume-skills/module-19-git-ci-observability/release-artifact.sha256
          if-no-files-found: error
          retention-days: 7
```

The workflow performs CI and packages a source bundle; it contains no production deployment. Tests/checks precede packaging, upload fails if the expected files are missing, and job permissions are restricted to contents:read. The paths assume the example remains in this repository layout.

Local checks parse the YAML and confirm events, read-only token permissions, official commit pins, step ordering and non-persisted checkout credentials. They do not validate every GitHub expression or execute the job on Ubuntu. A hosted runner may still expose version/platform differences that these Windows-local checks do not exercise.

### 7.2 Lockfiles, caches and artifacts

npm ci installs from the lockfile and requires the manifest/lock relationship to be consistent. The package cache can speed retrieval, but a cache miss should not change correctness. The setup-node cache is not a substitute for installing dependencies. [GitHub dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)

An artifact is the output you identify, retain and move between stages. Here that is a source ZIP, file-hash manifest and ZIP digest. It is not a self-contained runtime image: dependencies must be supplied from the locked tree. A cache is disposable acceleration data; treating it as your only release record makes reproducibility and rollback fragile. [Workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data)

### 7.3 Permissions, untrusted input and deployment ownership

Pinning an action to a reviewed full commit prevents a movable tag from silently selecting different action code. It does not make the action harmless or freeze the contents of a mutable hosted runner image. Keep token permissions and available secrets scoped to the job's actual task. Avoid interpolating untrusted PR fields directly into shell code. [GitHub secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)

PR code is untrusted until the appropriate review boundary. In particular, combining a privileged pull_request_target context with execution of untrusted checkout code can expose credentials. The example uses an ordinary pull_request trigger and no cloud secret/deployment step.

Concurrency settings control competing runs, not business transactions. Canceling an obsolete CI run can be useful; interrupting a deployment halfway through can require different coordination. A production design should define which release may write the deployment pointer and how partial operations recover.

For cloud deployment, supported OIDC federation can exchange a narrowly trusted job identity for temporary cloud credentials. id-token:write only enables requesting the workflow token; it does not itself grant cloud resource access. Configure the cloud trust restrictions and resource permissions separately. No OIDC exchange occurs here. [GitHub OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect)

---

## 8. Testing: choose a boundary and a failure worth catching

### 8.1 Unit, integration, contract and end-to-end

| Test shape | Boundary | Example in this curriculum |
| --- | --- | --- |
| Unit | Small isolated behavior | Percentile/error-budget calculations against known cases |
| Integration | Real components interacting | HTTP gateway → dependency endpoint; SQLite transaction + worker |
| API contract assertion | Status/schema/semantics at an interface | Stable successful/error response fields |
| Consumer-driven contract suite | Independently agreed consumer/provider expectations | A separate possible extension; not implemented here |
| End-to-end | Intended user/system path across deployed components | Login/create/job/result through actual ingress; needs its own environment |

The boundaries matter more than one universal test-count pyramid. Prefer many fast, focused tests and enough realistic boundary checks to catch failure modes. Mocking every database/HTTP call cannot prove a real SQL transaction or protocol integration. Conversely, a huge end-to-end suite can be slow and hard to diagnose if it replaces simpler checks unnecessarily.

### 8.2 The actual HTTP contract tests

These use Node's built-in test runner with real local HTTP calls. The dependency is a local teaching service, not a real production downstream. They assert API contracts inside integration tests; they are not an independently maintained consumer-driven contract system. [Node test runner](https://nodejs.org/api/test.html)

```javascript
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { createTelemetry } from './telemetry.mjs';
import { createApplication } from './app.mjs';
import { attempt } from './load.mjs';
const telemetry = createTelemetry();
const app = await createApplication(telemetry);
const url = 'http://127.0.0.1:' + app.port;
after(async () => { await app.close(); await telemetry.close(); });
test('success contract over real HTTP', async () => {
  const response = await attempt(url + '/work?delay=1');
  assert.equal(response.status, 200);
  const body = JSON.parse(response.body);
  assert.equal(body.result, 'computed'); assert.equal(body.release, 'v1');
  assert.match(body.request_id, /^[a-f0-9-]{36}$/); assert.match(body.trace_id, /^[a-f0-9]{32}$/);
});
test('invalid input is rejected at the API boundary', async () => {
  const response = await attempt(url + '/work?delay=999');
  assert.equal(response.status, 400); assert.equal(JSON.parse(response.body).error, 'delay must be 0..200ms');
});
test('dependency failure has a stable public error contract', async () => {
  const response = await attempt(url + '/work?delay=1&fail=1');
  assert.equal(response.status, 503); assert.equal(JSON.parse(response.body).error, 'dependency unavailable');
  assert.ok(!response.body.includes('stack'));
});
```

Three tests passed: success fields, invalid input and a stable upstream-failure response. Other modules supply authorization, webhook, database, retry and ingestion tests. These three do not claim full regression coverage for all backend behavior.

### 8.3 Useful failure tests

Ask what could go wrong at the chosen boundary: a missing field, wrong tenant, duplicate delivery, concurrent write, timeout after commit, failed dependency, malformed response or incompatible deployment. Check both the response and durable state when side effects matter.

Use deterministic clocks/data where appropriate, isolate resources and clean them. Sleep-based assertions against narrow timing windows can be flaky. A timeout assertion should establish a boundary, not require a particular scheduler's exact millisecond result.

Coverage reports describe which code was exercised under a particular tool/model. High coverage does not prove that the assertions catch business errors. A test that merely repeats the implementation's arithmetic with the same bug can pass convincingly; use independently known cases and observable outcomes.

---

## 9. Executable release gates and rollback

### 9.1 What the local artifact contains

The source ZIP contains app.mjs, telemetry.mjs, serve.mjs, load.mjs, statistics.mjs, contract.test.mjs, package.json and package-lock.json, plus manifest.json. The fixture Git revision includes those exact files under a committed service/ snapshot. File hashes identify their bytes; the archive SHA-256 identifies the built ZIP.

Candidate extraction occurs beneath the same module so Node resolves the already installed, locked dependencies from the parent module's node_modules. This is a local source-bundle laboratory, not a portable production image. A real deployment must provision the intended runtime/dependencies or package them appropriately.

```python
"""Source-bundle integrity and local promotion helpers, not a deployment platform."""
from pathlib import Path
import hashlib,json,os,zipfile

FILES=('app.mjs','telemetry.mjs','serve.mjs','load.mjs','statistics.mjs','contract.test.mjs','package.json','package-lock.json')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def package(source,destination,revision,release):
    source,destination=Path(source),Path(destination)
    manifest={'revision':revision,'release':release,'files':{name:digest(source/name) for name in FILES}}
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:archive.write(source/name,name)
        archive.writestr('manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest,digest(destination)

def extract_verified(archive_path,expected_digest,destination):
    destination=Path(destination).resolve()
    if digest(archive_path)!=expected_digest:raise ValueError('Artifact digest mismatch')
    with zipfile.ZipFile(archive_path) as archive:
        names=archive.namelist()
        if len(names)!=len(FILES)+1 or set(names)!=set(FILES)|{'manifest.json'}:
            raise ValueError('Unexpected archive paths')
        destination.mkdir()
        for name in names:
            if (destination/name).resolve().parent!=destination:raise ValueError('Archive path escaped release')
        archive.extractall(destination)
    manifest=json.loads((destination/'manifest.json').read_text())
    if set(manifest['files'])!=set(FILES) or not all(digest(destination/name)==value for name,value in manifest['files'].items()):
        raise ValueError('Extracted source mismatch')
    return manifest

def promote(pointer,manifest,artifact_digest):
    pointer=Path(pointer)
    temporary=pointer.with_name('current.new.json')
    temporary.write_text(json.dumps({'release':manifest['release'],'revision':manifest['revision'],'artifact_sha256':artifact_digest},indent=2)+'\n')
    os.replace(temporary,pointer)
```

### 9.2 What failed, and what stayed selected

The pipeline first packaged, extracted and HTTP-smoked v1 before selecting it. It then ran these failures:

- An intentionally failing real Node test stopped before packaging; the prohibited output ZIP was absent.
- A changed archive failed the expected digest check before extraction/promotion.
- A candidate reporting unhealthy returned a failing HTTP response, and v1 remained selected.

The valid v2 candidate passed integrity and actual health/useful-route checks, then its revision/digest was selected. A local rollback reselected the retained v1 artifact metadata.

Actual gate and selection result:

```json
{
  "runs": [
    [
      {
        "stage": "syntax",
        "status": "passed"
      }
    ],
    [
      {
        "stage": "test",
        "status": "failed",
        "error_type": "CalledProcessError"
      }
    ],
    [
      {
        "stage": "integrity",
        "status": "failed",
        "error_type": "ValueError"
      }
    ],
    [
      {
        "stage": "smoke",
        "status": "failed",
        "error_type": "HTTPError"
      }
    ],
    [
      {
        "stage": "integrity",
        "status": "passed"
      },
      {
        "stage": "smoke",
        "status": "passed"
      },
      {
        "stage": "promote",
        "status": "passed"
      }
    ]
  ],
  "selected_before_rollback": {
    "release": "v2",
    "revision": "28d1ef891abe9eccb6a500b58f848c999bb1da28",
    "artifact_sha256": "08f759f02e3da6adb962199975b2f04471966e84b1dfa08db96211657930f183"
  },
  "selected_after_rollback": {
    "release": "v1",
    "revision": "28d1ef891abe9eccb6a500b58f848c999bb1da28",
    "artifact_sha256": "9bdc4dff5b90451d62177466a57b2b905a7478fdfaa82dda15f330432874cf6f"
  },
  "artifact_sha256": "08f759f02e3da6adb962199975b2f04471966e84b1dfa08db96211657930f183",
  "boundary": "Candidate source bundle resolves locked dependencies from module node_modules; no remote runner or external deployment. Pointer replacement does not reroute a running server."
}
```

The current.json pointer is replaced atomically as a local file operation. It is **not a traffic router**. Candidate processes are separate smoke targets and are stopped afterward. The test does not claim a live blue/green cutover, user-traffic rollback, power-loss durability of the pointer or multi-controller coordination.

The injected unhealthy candidate uses the same v2 source bundle with failing runtime health configuration. It demonstrates a configuration/readiness gate; it is not a separately compiled broken binary. The recorded archive remains available as release-artifact.zip with its manifest/digest for inspection.

### 9.3 What production promotion adds

Identify and authenticate the artifact/provenance, verify environment configuration and schema compatibility, start candidate capacity, check useful readiness, route a controlled portion of traffic, watch release-specific errors/latency, then finish or roll back according to explicit criteria.

A checksum only protects identity relative to a trusted expected digest. An attacker who can replace both the artifact and its expected digest defeats that comparison. Signatures/attestations, protected build identities and approval policy address additional trust requirements. Those are documented extensions here.

Application rollback must account for database migrations and external side effects. Reverting Git or selecting an old ZIP does not reconstruct deleted data. Use compatible changes and tested recovery plans rather than treating code selection as a universal undo operation.

---

## 10. Observability: logs, metrics and traces

Observability is the ability to investigate internal behavior from the system's outputs. Instrumentation creates telemetry; monitoring evaluates selected conditions; diagnosis uses context to explain symptoms. Logs, metrics and traces are complementary signals. OpenTelemetry provides APIs/SDKs and propagation/export mechanisms; it is not itself the storage/query/dashboard backend for every deployment. [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/)

```text
Request arrives
  -> log event with request/trace/release context
  -> count operation, observe duration/in-flight work
  -> span for inbound work
      -> span for dependency call
          -> propagated context -> dependency span
  -> collector/backend/query/alerting, if configured
```

This fixture uses **real OpenTelemetry trace SDK spans with an in-memory exporter**. Logs and metric counters/histogram are custom in-memory teaching structures exposed as JSON. No collector, remote exporter, Prometheus scrape format, dashboard or hosted alerting backend is exercised.

### 10.1 Structured logs and correlation

A structured log has deliberate fields that can be searched consistently. Useful production fields often include event time, severity, operation/request/trace identity, service/release, route and outcome. Avoid dumping entire requests, headers, environments or error objects containing secrets.

Actual completed-request log:

```json
{
  "event": "request_complete",
  "request_id": "0c47c565-8d36-4201-ab71-69efa03857b5",
  "trace_id": "6446a797d81e0689e2338ebc7ab55481",
  "route": "/work",
  "status": 200,
  "duration_ms": 18.873400000000004,
  "release": "v1"
}
```

The response, log and exported trace share the request's identifiers. The fixture records monotonic duration and an allowlisted field set; it does not implement production retention, event-time indexing or centralized collection. A canary value supplied through Authorization, Cookie and a query parameter was absent from the serialized application logs.

A correlation ID is not a permission credential. Validate any user-controlled identifier you log, and bound its format/length to avoid log injection/cardinality surprises. This fixture generates a fresh UUID for its request ID instead of accepting an arbitrary client value.

### 10.2 Metrics: counters, gauges and histograms

| Instrument concept | Typical meaning | Example |
| --- | --- | --- |
| Counter | Cumulative events since the process/instrument reset | Completed request count |
| Gauge | Value at an observation instant | In-flight work, queue size, memory |
| Histogram | Distribution represented by observations/buckets/count/sum | Request duration |

Rates are derived from changes in counters over a time window; handle process resets. Histograms use units and boundaries that must be known. In this fixture, request durations are seconds in the histogram and milliseconds in logs/client measurements. Its buckets are cumulative and the Inf bucket equals the observation count.

The /metrics endpoint returns custom JSON and is excluded from measuring itself. Labels are limited to route templates/unmatched and status classes. Raw URLs, request IDs, tenant IDs or trace IDs as metric labels can create excessive time-series cardinality. Put per-request identity in appropriate logs/traces rather than duplicating it into every metric label.

Actual snapshot before the load runs:

```json
{
  "requests": {
    "/work|2xx": 12,
    "/work|4xx": 1,
    "unmatched|4xx": 3,
    "/work|5xx": 1
  },
  "active": 0,
  "histogram": {
    "count": 17,
    "sum_seconds": 0.27249239999999986,
    "cumulative_buckets": {
      "1": 17,
      "0.01": 6,
      "0.05": 17,
      "0.1": 17,
      "0.5": 17,
      "Inf": 17
    }
  }
}
```

The suite checks counts against request counters, cumulative-bucket ordering and in-flight return to zero. These metrics describe handler behavior in one process; they are not a customer-level availability SLI or proof that a timed-out client received a response.

---

## 11. Tracing and context propagation

A trace links work for an operation. A span represents one timed operation, with a span ID, shared trace ID, parent relationship and selected attributes/status. Concurrent requests need separate active context. W3C traceparent provides a standard propagation format; trusted instrumentation extracts and injects it across boundaries. [OpenTelemetry propagation](https://opentelemetry.io/docs/concepts/context-propagation/), [W3C Trace Context](https://www.w3.org/TR/trace-context/)

### 11.1 Actual SDK setup

```javascript
import { context, propagation, trace } from '@opentelemetry/api';
import { W3CTraceContextPropagator } from '@opentelemetry/core';
import { InMemorySpanExporter, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';

export function createTelemetry() {
  const exporter = new InMemorySpanExporter();
  const provider = new NodeTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exporter)] });
  provider.register({ propagator: new W3CTraceContextPropagator() });
  return {
    tracer: provider.getTracer('placement-m19', '1.0.0'),
    spans: () => exporter.getFinishedSpans().map(span => ({
      name: span.name, kind: span.kind, trace_id: span.spanContext().traceId,
      span_id: span.spanContext().spanId, parent_span_id: span.parentSpanContext?.spanId ?? null,
      status: span.status.code, attributes: span.attributes,
      duration_ms: span.duration[0] * 1000 + span.duration[1] / 1e6,
    })),
    close: async () => { await provider.forceFlush(); await provider.shutdown(); context.disable(); propagation.disable(); trace.disable(); },
  };
}
```

The gateway extracts incoming context, starts a SERVER span, starts a CLIENT span for its HTTP call and injects context into that call. The dependency endpoint extracts it and starts its SERVER span. All run in the same Node process/provider for this exercise, but the propagation crosses an actual HTTP request boundary.

```text
gateway SERVER span
   |
   +-- outbound CLIENT span
         |
         +-- dependency SERVER span
```

The suite verified three distinct span IDs under one trace, correct parent links, a valid incoming parent, replacement of zero/invalid incoming IDs, error status on a failed dependency path and isolation across eight concurrent requests. The exact recorded span graph is in trace-output.json. [Official JavaScript instrumentation](https://opentelemetry.io/docs/languages/js/instrumentation/)

### 11.2 The actual gateway/dependency implementation

```javascript
import http from 'node:http';
import { once } from 'node:events';
import { randomUUID } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { context, propagation, SpanKind, SpanStatusCode, trace } from '@opentelemetry/api';

export async function createApplication(telemetry, { release = 'v1', unhealthy = false } = {}) {
  const logs = [], requests = {}, bounds = [.01, .05, .1, .5, 1];
  const histogram = { count: 0, sum_seconds: 0, cumulative_buckets: Object.fromEntries([...bounds, 'Inf'].map(bound => [bound, 0])) };
  let active = 0;
  function send(res, status, body) {
    if (res.destroyed) return;
    res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(body));
  }
  const dependency = http.createServer((req, res) => {
    const parent = propagation.extract(context.active(), req.headers);
    context.with(parent, () => telemetry.tracer.startActiveSpan('dependency GET /compute', { kind: SpanKind.SERVER }, async span => {
      const url = new URL(req.url, 'http://fixture.invalid');
      await new Promise(resolve => setTimeout(resolve, Number(url.searchParams.get('delay'))));
      const status = url.searchParams.get('fail') === '1' ? 503 : 200;
      span.setAttribute('http.response.status_code', status);
      if (status >= 500) span.setStatus({ code: SpanStatusCode.ERROR });
      send(res, status, { result: status === 200 ? 'computed' : 'unavailable' }); span.end();
    }));
  });
  dependency.listen(0, '127.0.0.1'); await once(dependency, 'listening');
  const dependencyPort = dependency.address().port;
  const gateway = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://fixture.invalid');
    if (url.pathname === '/metrics') return send(res, 200, { requests, active, histogram });
    const route = ['/work', '/health'].includes(url.pathname) ? url.pathname : 'unmatched';
    const requestId = randomUUID(), started = performance.now();
    const parent = propagation.extract(context.active(), req.headers);
    context.with(parent, () => telemetry.tracer.startActiveSpan('gateway GET ' + route, { kind: SpanKind.SERVER }, async span => {
      let status = 500;
      const traceId = trace.getSpan(context.active()).spanContext().traceId;
      active++;
      try {
        if (req.method !== 'GET') { status = 405; return send(res, status, { error: 'method not allowed' }); }
        if (route === '/health') { status = unhealthy ? 503 : 200; return send(res, status, { ready: !unhealthy, release }); }
        if (route !== '/work') { status = 404; return send(res, status, { error: 'route not found' }); }
        const delay = Number(url.searchParams.get('delay') ?? 5);
        if (!Number.isInteger(delay) || delay < 0 || delay > 200) { status = 400; return send(res, status, { error: 'delay must be 0..200ms' }); }
        const fail = url.searchParams.get('fail') === '1' ? '1' : '0';
        const result = await telemetry.tracer.startActiveSpan('gateway HTTP dependency', { kind: SpanKind.CLIENT }, async child => {
          try {
            const headers = {}; propagation.inject(context.active(), headers);
            return await new Promise((resolve, reject) => {
              const request = http.get({ hostname: '127.0.0.1', port: dependencyPort, path: '/compute?delay=' + delay + '&fail=' + fail, headers, agent: false }, response => {
                response.resume(); response.on('end', () => {
                  child.setAttribute('http.response.status_code', response.statusCode);
                  if (response.statusCode >= 500) child.setStatus({ code: SpanStatusCode.ERROR });
                  resolve(response.statusCode);
                });
                response.on('error', reject);
              });
              request.setTimeout(1000, () => request.destroy(new Error('dependency timeout')));
              request.on('error', reject);
            });
          } catch (error) { child.setStatus({ code: SpanStatusCode.ERROR }); throw error; }
          finally { child.end(); }
        });
        status = result;
        send(res, status, { request_id: requestId, trace_id: traceId, release,
          ...(status === 200 ? { result: 'computed' } : { error: 'dependency unavailable' }) });
      } catch {
        status = 503; send(res, status, { error: 'dependency unavailable', request_id: requestId, trace_id: traceId, release });
      } finally {
        const duration = (performance.now() - started) / 1000;
        const key = route + '|' + Math.floor(status / 100) + 'xx';
        requests[key] = (requests[key] ?? 0) + 1;
        histogram.count++; histogram.sum_seconds += duration;
        for (const bound of bounds) if (duration <= bound) histogram.cumulative_buckets[bound]++;
        histogram.cumulative_buckets.Inf++;
        active--;
        logs.push({ event: 'request_complete', request_id: requestId, trace_id: traceId, route, status, duration_ms: duration * 1000, release });
        span.setAttribute('http.route', route); span.setAttribute('http.response.status_code', status);
        if (status >= 500) span.setStatus({ code: SpanStatusCode.ERROR });
        span.end();
      }
    }));
  });
  gateway.listen(0, '127.0.0.1'); await once(gateway, 'listening');
  return { port: gateway.address().port, dependencyPort, logs,
    metrics: () => structuredClone({ requests, active, histogram }),
    close: async () => {
      for (const server of [gateway, dependency]) await new Promise((resolve, reject) => {
        server.close(error => error ? reject(error) : resolve()); server.closeIdleConnections();
      });
    },
  };
}
```

The delay/failure controls are bounded local test inputs. There is no authentication/business database in this API, and it is not a production server-hardening example. Dependency timeout here is a configured socket inactivity timeout; the load generator below separately uses an absolute client deadline. Those are different mechanisms.

Trace context is untrusted input, not caller identity. Sampling means a trace ID can exist without all spans being exported. Choose sampling, attribute privacy, retention, resource/service labels and exporter failure behavior deliberately. The fixture has no OTLP transport, cross-host clock experiment, sampling-volume comparison or span-loss recovery test.

---

## 12. Performance: define what the number means

### 12.1 Latency, throughput, concurrency and utilization

| Quantity | Meaning | Common confusion |
| --- | --- | --- |
| Latency | Time for a defined attempt/operation boundary | Client end-to-end time is not the same as server handler time |
| Throughput | Completed work per unit time under stated criteria | Attempted HTTP requests are not necessarily successful business operations |
| Concurrency | Work in progress at an instant | It is not automatically the same as arrival rate |
| Utilization | How busy a particular resource is | Low average CPU does not rule out a pool, lock or downstream bottleneck |
| Saturation | Demand/queueing beyond a resource's immediately usable capacity | More concurrency can increase queue time without useful throughput |

Report failures and deadlines alongside success latency. A fast 503 can inflate attempted RPS while providing no useful work. If every timeout disappears from the dataset, a struggling service can appear artificially fast.

Node's event-loop delay/utilization tools help investigate scheduling pressure, but they do not replace CPU profiling or downstream metrics. Event-loop histogram values use nanoseconds; convert units before comparing with millisecond request times. [Node performance APIs](https://nodejs.org/api/perf_hooks.html)

### 12.2 Percentiles need a population and a convention

p95 is a quantile of a specified observation population. It is not a guarantee that every future request will complete within that value. The fixture uses the **nearest-rank** convention: sort n samples and select rank ceil(p × n), using one-based ranks. Other tools can interpolate differently.

The independent reference dataset 1 through 100 produces p50=50, p95=95 and p99=99. Empty samples produce no latency claim. Non-finite/negative durations are rejected. The helper includes HTTP errors and client errors in the declared all-attempt population.

```javascript
export function percentile(values, fraction) {
  if (!(fraction > 0 && fraction <= 1)) throw new RangeError('fraction must be in (0,1]');
  if (!values.length) return null;
  if (values.some(value => !Number.isFinite(value) || value < 0)) throw new RangeError('finite nonnegative samples required');
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.ceil(fraction * sorted.length) - 1];
}

export function summarize(samples, elapsedSeconds) {
  if (!Number.isFinite(elapsedSeconds) || elapsedSeconds <= 0) throw new RangeError('positive measurement duration required');
  const values = samples.map(sample => sample.latency_ms);
  const successful = samples.filter(sample => sample.status >= 200 && sample.status < 300 && !sample.error).length;
  const round = value => value === null ? null : Number(value.toFixed(3));
  return {
    attempts: samples.length, successful, failed: samples.length - successful,
    error_ratio: samples.length ? (samples.length - successful) / samples.length : 0,
    elapsed_seconds: round(elapsedSeconds),
    attempted_rps: round(samples.length / elapsedSeconds), successful_rps: round(successful / elapsedSeconds),
    mean_ms: values.length ? round(values.reduce((a, b) => a + b, 0) / values.length) : null,
    p50_ms: round(percentile(values, .50)), p95_ms: round(percentile(values, .95)), p99_ms: round(percentile(values, .99)),
    percentile_method: 'nearest rank across all completed attempts, including HTTP failures and client errors',
  };
}

export function errorBudget(total, good, target) {
  if (!Number.isInteger(total) || total <= 0 || !Number.isInteger(good) || good < 0 || good > total || !(target > 0 && target < 1)) {
    throw new RangeError('invalid SLI inputs');
  }
  const observedError = (total - good) / total;
  return { total, good, bad: total - good, target, observed_good_ratio: good / total,
    allowed_bad: Number((total * (1 - target)).toFixed(6)),
    burn_rate: Number((observedError / (1 - target)).toFixed(6)) };
}
```

Do not average p95 values from several hosts and call it the fleet p95. Merge a compatible underlying distribution/histogram where possible and calculate the intended quantile. Histogram bucket boundaries affect estimated precision; precomputed summary quantiles have different aggregation limits. [Prometheus histogram/summary guidance](https://prometheus.io/docs/practices/histograms/)

With only 60 observations, this nearest-rank p99 selects the slowest recorded attempt. That is a valid calculation on this sample, not a statistically strong estimate of a production tail. Keep sample size/window and errors visible.

### 12.3 Closed versus open workload models

In a closed model, each of a fixed number of slots/users waits for its attempt before starting another. When the service slows, the achieved arrival rate can decrease. An open arrival-rate model schedules attempts independently and can expose different overload/queueing behavior.

This harness is closed and bounded. It does not measure an independently fixed arrival rate. Workload models and coordinated omission matter when interpreting latency under overload. [k6 open/closed model documentation](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)

### 12.4 The actual load harness

```javascript
import http from 'node:http';
import { performance, monitorEventLoopDelay } from 'node:perf_hooks';
import { summarize } from './statistics.mjs';

export function attempt(url, { deadlineMs = 500, headers = {} } = {}) {
  const started = performance.now();
  return new Promise(resolve => {
    const controller = new AbortController();
    const deadline = setTimeout(() => controller.abort(), deadlineMs);
    let completed = false;
    const finish = result => {
      if (completed) return;
      completed = true; clearTimeout(deadline);
      resolve({ ...result, latency_ms: performance.now() - started });
    };
    const request = http.get(url, { agent: false, headers, signal: controller.signal }, response => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', chunk => { body += chunk; });
      response.on('end', () => finish({ status: response.statusCode, error: null, body, headers: response.headers }));
      response.on('error', error => finish({ status: 0, error: error.code ?? 'RESPONSE_ERROR', body: '' }));
    });
    request.on('error', error => finish({ status: 0, error: error.name === 'AbortError' ? 'DEADLINE' : (error.code ?? 'CLIENT_ERROR'), body: '' }));
  });
}

export async function runLoad(url, { requests = 60, concurrency = 4, warmup = 6, deadlineMs = 500 } = {}) {
  if (!Number.isInteger(requests) || requests < 1 || !Number.isInteger(concurrency) || concurrency < 1 || concurrency > requests) {
    throw new RangeError('bounded positive request count and concurrency required');
  }
  for (let i = 0; i < warmup; i++) await attempt(url, { deadlineMs });
  const delay = monitorEventLoopDelay({ resolution: 10 }); delay.enable();
  const cpuStart = process.cpuUsage();
  const started = performance.now();
  let next = 0;
  const samples = [];
  await Promise.all(Array.from({ length: concurrency }, async () => {
    while (next < requests) { next++; samples.push(await attempt(url, { deadlineMs })); }
  }));
  const elapsed = (performance.now() - started) / 1000;
  delay.disable();
  const cpu = process.cpuUsage(cpuStart);
  return { configuration: { model: 'closed: each slot starts again only after its previous attempt ends', requests, concurrency, warmup, deadline_ms: deadlineMs, keepalive: false },
    summary: summarize(samples, elapsed), samples,
    local_process: { cpu_user_ms: cpu.user / 1000, cpu_system_ms: cpu.system / 1000,
      rss_end_bytes: process.memoryUsage().rss, event_loop_samples: delay.count,
      event_loop_p99_ms: delay.count ? delay.percentile(99) / 1e6 : null,
      scope: 'load generator and both fixture HTTP services share this Node process' } };
}
```

The main run uses 60 measured requests, concurrency four, six sequential warm-up attempts, a 500ms client deadline and fresh HTTP connections without keepalive. The route requests a 10ms timer delay at the dependency. Requested timer delay is not measured end-to-end latency: scheduling, sockets, SDK export and both service hops add work.

Raw samples, status/error, configuration, elapsed duration, local CPU usage, RSS at the end and event-loop observations are saved in load-results.json. The client uses a monotonic clock and an absolute abort deadline. Rates use unrounded elapsed time; displayed values are rounded.

Actual recorded runs:

```json
{
  "normal": {
    "configuration": {
      "model": "closed: each slot starts again only after its previous attempt ends",
      "requests": 60,
      "concurrency": 4,
      "warmup": 6,
      "deadline_ms": 500,
      "keepalive": false
    },
    "summary": {
      "attempts": 60,
      "successful": 60,
      "failed": 0,
      "error_ratio": 0,
      "elapsed_seconds": 0.45,
      "attempted_rps": 133.411,
      "successful_rps": 133.411,
      "mean_ms": 29.671,
      "p50_ms": 30.574,
      "p95_ms": 32.974,
      "p99_ms": 33.105,
      "percentile_method": "nearest rank across all completed attempts, including HTTP failures and client errors"
    },
    "local_process": {
      "cpu_user_ms": 0,
      "cpu_system_ms": 0,
      "rss_end_bytes": 56262656,
      "event_loop_samples": 28,
      "event_loop_p99_ms": 22.855679,
      "scope": "load generator and both fixture HTTP services share this Node process"
    }
  },
  "errors": {
    "attempts": 12,
    "successful": 0,
    "failed": 12,
    "error_ratio": 1,
    "elapsed_seconds": 0.043,
    "attempted_rps": 282.319,
    "successful_rps": 0,
    "mean_ms": 10.369,
    "p50_ms": 5.993,
    "p95_ms": 15.736,
    "p99_ms": 15.736,
    "percentile_method": "nearest rank across all completed attempts, including HTTP failures and client errors"
  },
  "deadlines": {
    "attempts": 4,
    "successful": 0,
    "failed": 4,
    "error_ratio": 1,
    "elapsed_seconds": 0.035,
    "attempted_rps": 115.461,
    "successful_rps": 0,
    "mean_ms": 17.231,
    "p50_ms": 15.166,
    "p95_ms": 19.979,
    "p99_ms": 19.979,
    "percentile_method": "nearest rank across all completed attempts, including HTTP failures and client errors"
  }
}
```

The failure run completed 12 attempts with failure responses and zero successful throughput. The deadline run retained four client-deadline failures in its population. A client abort does not establish that server/dependency execution stopped immediately; cancellation needs an application design, as M18 also explains for task deadlines.

### 12.5 What these measurements cannot support

This is a short local mechanism demonstration on one Windows machine. Client, gateway, dependency and trace export share one Node process. There is no real database, TLS, cross-host network, realistic payload distribution or saturation search. One run cannot establish production capacity, a stable p99, a speedup over a baseline or a resume project's benchmark.

A useful capacity experiment separates load generation from the target, records hardware/runtime/commit, controls workload/state/warm-up, increases load in planned stages, measures errors and queueing, monitors resource limits and repeats comparisons under the same conditions. Keep raw data and specify the acceptance criteria before claiming an improvement.

---

## 13. SLI, SLO, SLA and alerts

An **SLI** is a defined measurement of user-visible service behavior. An **SLO** is the objective for that measurement over a window. An **SLA** is an agreement that can attach contractual consequences. Define which requests count, what good means, the window and the observation point before discussing percentages. [Google SRE SLO implementation](https://sre.google/workbook/implementing-slos/)

Synthetic, computed error-budget example:

```json
{
  "total": 1000,
  "good": 995,
  "bad": 5,
  "target": 0.999,
  "observed_good_ratio": 0.995,
  "allowed_bad": 1,
  "burn_rate": 5
}
```

This is reference arithmetic, not production availability evidence. The bad-event fraction divided by the allowed bad-event fraction gives the illustrated burn rate. A useful alert also needs a meaningful window, traffic volume and action; one instantaneous ratio is not a complete paging policy.

Start operational diagnosis with traffic, latency, errors and saturation, then add service-specific signals such as queue age, database pool wait and cache effectiveness. Alert on symptoms that require intervention, and use diagnostic metrics/logs/traces to investigate causes. [Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)

---

## 14. Architectural understanding: build a reviewable release and diagnosis path

### 14.1 Proposed production structure

```text
PR / reviewed source revision
  -> CI install/check/test
  -> trusted artifact build + identity/provenance
  -> staging candidate + realistic boundary checks
  -> deployment decision / controlled automation
  -> candidate capacity / readiness / compatible schema
  -> controlled traffic promotion
  -> release-tagged logs + metrics + traces
  -> health/error/latency evidence -> continue, roll forward or roll back
```

For a small backend, keep the pipeline understandable. Identify who owns source approval, artifact production, deployment permissions and the current-release pointer. Prevent unreviewed code from acquiring production credentials. Define a recovery path for interrupted deployments and a data-compatibility strategy.

### 14.2 A practical implementation order

1. **Make source identity explicit.** Review the actual staged diff, integrate conflicts deliberately and record the intended revision.
2. **Choose meaningful checks.** Test pure calculations cheaply, real API/data boundaries where needed, and negative authorization/retry cases from previous modules.
3. **Package once.** Record artifact identity, locked dependencies/runtime and configuration requirements. Verify the expected digest from a trusted source.
4. **Start a private candidate.** Check useful readiness and a representative route/dependency operation. Check configuration and migrations, not only process existence.
5. **Promote with recovery rules.** Coordinate traffic routing and draining. Retain the previous compatible artifact and define when to stop/roll back.
6. **Instrument before an incident.** Connect request/job IDs to logs/traces, record bounded metrics and include the release identity. Protect sensitive data and telemetry budgets.
7. **Measure under a declared workload.** State the model, concurrency/arrival behavior, payload, warm-up, duration, errors and percentiles. Retain raw samples and compare like with like.

The fixture verifies pieces of this path locally. Artifact trust/attestations, hosted runner execution, production routing, schema evolution and fleet observability remain separately proposed work.

### 14.3 Failure walkthrough: p95 worsens after deployment

```text
1. Identify release, affected window/routes and client-visible symptom.
2. Compare traffic/error/latency distributions with the relevant baseline.
3. Separate success, failure and timeout populations; inspect saturation.
4. Find correlated logs/traces for slow requests and dependency spans.
5. Check pool waits, query shape, event-loop blocking, retries and cold starts.
6. Use the rollout policy to mitigate, then verify the user-visible path.
7. Preserve evidence and add the smallest regression check that catches the cause.
```

If the downstream span is slow while CPU is low, more web workers may worsen a shared database bottleneck. If the load generator is saturated, its achieved rate is not the server's capacity. If errors become fast, successful throughput can fall while attempted RPS rises. Diagnose the boundary before optimizing code based on one average.

For the resume's load-balancer project, use this structure to defend throughput/remapping/latency claims: exact code revision, workload and baseline, hardware/process topology, success definition, warm-up/duration, raw samples, failures and repeatability. The local experiment here is not a replacement measurement of that project.

---

## 15. Must remember and common wrong answers

| Say this | Avoid this |
| --- | --- |
| Commit records the staged snapshot | Commit always records every current file edit |
| Fetch updates observed remote refs; integration is separate | Fetch necessarily changes my working branch |
| Rebase creates new commit identities | Rebase only moves a label without changing commits |
| Revert records an inverse change | Revert erases the original history or external effects |
| CI checks a particular revision under stated conditions | Green CI proves the whole production system is correct |
| Cache accelerates retrieval; artifact identifies output | Dependency cache is my only deployable release record |
| A trusted digest comparison checks artifact identity | A hash by itself proves who built/approved the artifact |
| Trace context correlates work | traceparent authenticates the caller |
| Metrics need bounded labels and explicit units | Request IDs should label every time series |
| Percentiles need a population and calculation convention | Average host p95 is automatically fleet p95 |
| Report errors and successful work alongside attempted RPS | Fast failures prove high useful throughput |
| A closed model changes achieved arrival rate as latency changes | A fixed number of users is a fixed external arrival rate |

---

## 16. Interview questions and follow-ups

### Q1. What are working tree, index and HEAD?

Current files, proposed staged snapshot and the current recorded checkout/commit context. A file can have three different versions simultaneously. The fixture observed base/staged/working and verified that unstaging preserved working content.

### Q2. What does git add actually do?

It updates the index for selected content so a subsequent commit can record that staged snapshot. Editing again afterward does not automatically update the earlier staged version. Review both ordinary and staged diffs before explaining what the commit contains.

### Q3. Branch versus commit versus pull request?

A commit identifies a recorded snapshot/history relationship; a branch is a movable reference. A pull request is a hosting review/integration workflow around changes. A branch name can move, so record the exact revision when discussing a release or measurement.

### Q4. Fetch versus pull?

Fetch obtains updates and refreshes appropriate remote-tracking references without automatically integrating them into the checked-out branch. Pull also performs a selected integration behavior. Options/configuration determine whether that integration fast-forwards, merges or rebases.

### Q5. Merge versus rebase?

Merge combines histories and can record multiple parents; a fast-forward can simply move a tip. Rebase replays selected changes on another base and creates new commits. Both require deliberate conflict handling and relevant checks; rewriting shared history needs coordination.

### Q6. How do you resolve a conflict?

Inspect operation state and both changes' intent, edit the desired combined content, stage it and complete the appropriate merge/rebase workflow. Test the resulting behavior. If abandoning the operation, use its appropriate abort procedure; deleting conflict markers alone does not establish correctness.

### Q7. Revert versus reset versus restore?

Revert creates an inverse commit while retaining history. Reset changes HEAD/index/working state depending on mode; restore changes selected content from a source. Understand the affected states before using them. None automatically undoes database mutations or external side effects.

### Q8. What is CI?

Frequent integration with automated checks that reveal change/integration problems. Explain which revision triggers which install/check/test/package stages. A job running on each push is useful only if its checks establish meaningful behavior.

### Q9. Continuous delivery versus continuous deployment?

Delivery keeps a validated change ready for a release decision. Deployment automatically releases qualifying changes to the intended environment. Clarify what CD means in the team and where approval, promotion and recovery responsibilities sit.

### Q10. What are workflow, job, step and runner?

A workflow is event-driven automation; jobs execute on runners; steps run commands/actions within jobs. Job dependencies and permissions are explicit. Separate shell invocations do not magically share shell-local variables, even though steps share a job workspace.

### Q11. Why use a lockfile and npm ci?

To install the recorded dependency graph consistently and detect manifest/lock inconsistency. A cache may speed retrieval but cannot replace installation or checks. Reproducibility also depends on runtime/platform and other build inputs, not just the top-level package versions.

### Q12. Why pin Actions to full commits and minimize permissions?

It fixes the selected action source relative to a reviewed immutable identity and limits what a compromised step can access. It does not prove the action safe or freeze the runner. PR code, shell interpolation, secrets and cloud trust remain separate boundaries.

### Q13. Artifact versus dependency cache?

An artifact is a named output retained/promoted for a run/revision. A cache is reusable acceleration data that may disappear or be restored. Record release identity independently of the cache and avoid rebuilding unknown variants for each environment.

### Q14. Does a checksum prove a release is trustworthy?

It proves byte identity relative to a trusted expected checksum. If both can be replaced, that comparison does not establish origin or approval. Trusted build identities, review and provenance/signature policy address additional requirements.

### Q15. Unit versus integration versus contract testing?

Unit checks isolate small behavior; integration checks real component interaction; contract assertions check an interface's expected shape/semantics. Consumer-driven contracts can add an independently maintained consumer/provider boundary. State what was real, mocked and independently checked.

### Q16. Does 100% coverage mean the code is correct?

No. It describes exercised code under a coverage model, not whether assertions detect business failures. Use meaningful negative/concurrent/failure cases and known references. A test that reproduces the same implementation bug can pass with high coverage.

### Q17. What should a release smoke test check?

At least intended readiness and a useful representative route, including required configuration/dependencies. Process existence and a static 200 are weaker evidence. The local pipeline rejects an unhealthy candidate but does not demonstrate a production traffic switch.

### Q18. What makes rollback safe?

A known compatible artifact/configuration, controlled routing/draining, explicit rollback criteria and data/schema compatibility. Selecting an old binary does not restore deleted data. The fixture reselects local metadata; real routing and database recovery need separate tests.

### Q19. Logs versus metrics versus traces?

Logs describe events, metrics aggregate measurements and traces connect timed operations along a path. Correlation links them, while each has cost/privacy/retention trade-offs. A monitoring dashboard alone is not a full explanation of a failure.

### Q20. What does OpenTelemetry provide?

Instrumentation APIs/SDKs, context propagation and export mechanisms for telemetry signals. It is not automatically the storage/query/alerting backend. This example uses real trace SDK spans with an in-memory exporter, custom logs and custom JSON metrics.

### Q21. Trace ID versus span ID versus request ID?

Trace ID groups related traced work; span IDs identify individual timed operations and parent relationships. A request ID can correlate one ingress operation. They are correlation context, not user identity or authorization. A trace may be sampled incompletely or not exported.

### Q22. Why avoid user/request IDs as metric labels?

They can create unbounded cardinality and expensive series. Prefer bounded route/status/service dimensions for aggregation, and use appropriate logs/traces for individual operations. Keep privacy and telemetry budgets explicit.

### Q23. Counter versus gauge versus histogram?

Counter records cumulative events, gauge represents an observed value, and histogram represents a distribution with known units/boundaries/count/sum. Rates need a window and reset handling. Histogram quantile precision and aggregation differ from precomputed summary quantiles.

### Q24. Latency versus throughput versus concurrency?

Latency is time at a defined boundary; throughput is completed work per time; concurrency is work in progress. Report attempted and successful work separately. More concurrency can produce queueing/errors rather than additional useful throughput.

### Q25. What is p95, and can you average server p95s?

A quantile of a specified sample population using a defined convention. Averaging host p95s generally does not produce the fleet quantile. Aggregate compatible underlying distributions where possible and state the sample/window/error population.

### Q26. Why is mean latency insufficient?

It can hide a slow tail and its population may exclude failures. Show appropriate percentiles, errors/timeouts, count/window and workload conditions. A percentile based on a tiny short run is still a small-sample observation, not a stable production guarantee.

### Q27. Open versus closed load model?

Closed slots wait before generating their next request; achieved arrival rate decreases as the target slows. An open model schedules arrivals independently and needs explicit handling when the generator cannot keep up. The choice changes overload/queueing evidence.

### Q28. How do you make a throughput claim defensible?

Record revision, runtime/hardware, topology, workload/model, payload/state, warm-up/window, successful operation criteria, failures and raw samples. Separate load generation from the target for capacity work and compare repeated runs under the same conditions. Local fast failures are not useful throughput.

### Q29. SLI versus SLO versus SLA?

SLI is the defined measurement; SLO is its target/window; SLA is an agreement that may attach consequences. Define good events and observation point first. Error-budget/burn arithmetic does not create a complete alerting policy without windows, traffic and an action.

### Q30. Design a pipeline and diagnose a p95 regression after release.

Trace reviewed source → meaningful checks → identified artifact → candidate → controlled promotion → release-aware telemetry/recovery. Check actual user-visible distributions/errors and saturation, then correlate logs/traces to slow dependencies or application work. Distinguish a code rollback, data recovery and a measurement artifact.

---

## 17. Practice tasks

1. **Explain three snapshots.** Stage one file version, edit again, inspect HEAD/index/working content and unstage without discarding the edit.
2. **Integrate deliberately.** Reproduce independent merge, same-line conflict/abort/resolve and a rebase. Compare parents/IDs and test combined behavior.
3. **Observe remote state.** Fetch from the disposable remote without moving HEAD, fast-forward, then create divergence and observe --ff-only refusal.
4. **Review the workflow.** Identify events, runner, steps, permissions, immutable action refs, install/check/test/package order and what remains unverified locally.
5. **Break a release gate.** Run the intentional failing-test, corrupted-artifact and unhealthy-candidate cases; prove the last good selection remains.
6. **Trace a request.** Locate its response/log/three-span graph, inject a valid incoming parent and compare concurrent contexts.
7. **Bound telemetry.** Supply credential/query canaries, inspect logs, and explain why route/status labels are preferable to per-user/request labels.
8. **Recalculate a report.** Derive nearest-rank percentiles and attempted/successful rates from raw samples. Keep HTTP errors/deadlines in the declared population.
9. **Critique the load experiment.** List shared-process, closed-model, duration, payload, connection and dependency limitations; plan a separate capacity test.
10. **Walk a regression.** Define an SLI/SLO and rollout criterion, diagnose a post-release latency symptom, then specify a compatible mitigation and a meaningful regression check.

---

## 18. Exit checklist

- [ ] I can distinguish working tree, index and recorded snapshot.
- [ ] I can explain merge/rebase/conflict/abort and fetch versus integration.
- [ ] I can explain restore/reset/revert without confusing code and external state.
- [ ] I can distinguish CI, continuous delivery and continuous deployment.
- [ ] I can read an Actions workflow and identify its permissions/trust boundaries.
- [ ] I can separate artifacts, caches, integrity and provenance.
- [ ] I can choose meaningful unit/integration/contract/failure checks.
- [ ] I can demonstrate failed candidate gates and describe real rollback requirements.
- [ ] I can correlate logs/metrics/traces while bounding sensitive data/cardinality.
- [ ] I can explain latency/rate/concurrency, percentile population and workload model.
- [ ] I can critique a benchmark and retain failures/raw evidence.
- [ ] I can define an SLI/SLO and diagnose a release regression by boundary.

These remain learning checks for you to demonstrate, not authoring completion ticks.

---

## 19. Sources and verification map

Primary sources researched:

- Git: [recording changes](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository), [branching/merging](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging), [rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing), [fetch](https://git-scm.com/docs/git-fetch), [restore](https://git-scm.com/docs/git-restore), [reset](https://git-scm.com/docs/git-reset) and [revert](https://git-scm.com/docs/git-revert).
- GitHub: [workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows), [syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [secure use](https://docs.github.com/en/actions/reference/security/secure-use), [caches](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching), [artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data), [OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect) and the official [checkout](https://github.com/actions/checkout), [setup-node](https://github.com/actions/setup-node), [upload-artifact](https://github.com/actions/upload-artifact) repositories.
- Telemetry/runtime: [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/), [propagation](https://opentelemetry.io/docs/concepts/context-propagation/), [JavaScript instrumentation](https://opentelemetry.io/docs/languages/js/instrumentation/), [W3C Trace Context](https://www.w3.org/TR/trace-context/), [Node tests](https://nodejs.org/api/test.html) and [performance APIs](https://nodejs.org/api/perf_hooks.html).
- Measurement/operation: [Prometheus histograms](https://prometheus.io/docs/practices/histograms/), [k6 workload models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/), [Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/) and [SLO implementation](https://sre.google/workbook/implementing-slos/).

Current documentation may describe newer runtime/platform behavior than the executable snapshot. Refresh runner/action requirements, APIs, policies and dependency status before applying them elsewhere.

**62 checks passed:**

| Group | Named checks | Evidence |
| --- | --- | --- |
| Git | 15 | Actual isolated repositories, index/branch histories, conflict/rebase/revert, local remote/fetch and source snapshot |
| HTTP contracts | 3 | Real Node test-runner requests and interface assertions |
| Additional HTTP | 4 | Actual success/input/route/dependency responses |
| Tracing | 7 | Official SDK spans, propagated parent links, invalid context, errors and concurrent isolation |
| Logs | 2 | Correlation and credential/query canary exclusion |
| Metrics | 4 | Bounded labels, count/buckets and in-flight completion |
| Statistics | 8 | Known quantiles, invalid/empty input, failure populations/rates and synthetic budget |
| Load mechanics | 5 | Actual attempts, warm-up exclusion, raw-sample quantiles, failure throughput and client deadlines |
| Local release pipeline | 9 | Syntax/contracts, initial good candidate, test/hash/health gates, promotion, metadata rollback and closed processes/ports |
| Workflow static | 5 | YAML/events/permissions/pins/order/checkout settings; not hosted execution |
| **Total** | **62** | Named checks; repeated contract execution is not counted again |

Files are under examples/resume-skills/module-19-git-ci-observability/. verify.py orchestrates the full run; git_lab.py and pipeline.py implement the owned history/candidate lifecycle. The chapter embeds telemetry.mjs, app.mjs, contract.test.mjs, statistics.mjs, load.mjs, release.py and ci.example.yml exactly.

Evidence includes verification-results.json, git-results.json, node-results.json, pipeline-results.json, verification-output.txt, contract-test-output.txt, node-verification-output.txt, trace-output.json, application-log-output.json and load-results.json. release-artifact.zip, release-manifest.json and release-artifact.sha256 preserve the source bundle; action-pins.json and dependency-audit.json record dependency/action observations. cleanup-results.json and content/site validation artifacts accompany them.

Scratch repositories/releases, candidate processes and listeners are removed; the retained public source bundle/results are intentional. No handbook-repository commit/push, hosted workflow, production/cloud deployment, traffic cutover, database migration/restore, remote telemetry backend or production capacity/availability claim is part of this verification. Docker was not started.

---

## Next

Continue to [M20: React Fundamentals](/docs/resume-skills/react-fundamentals) for components, state, rendering, hooks/effects, forms, API state and the frontend side of a full-stack explanation.

Revisit [M4: Node.js](/docs/resume-skills/nodejs) for event-loop/work boundaries, [M17: Deployment](/docs/resume-skills/linux-deployment-nginx-pm2) for lifecycle/draining, and [M18: AWS/GCP](/docs/resume-skills/aws-gcp-fundamentals) for cloud identity/routing/workflow boundaries. The [master roadmap](/docs/resume-skills) shows the remaining sections.
