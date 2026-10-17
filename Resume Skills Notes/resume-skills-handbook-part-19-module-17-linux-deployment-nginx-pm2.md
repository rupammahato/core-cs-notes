# Resume Skills Placement Handbook — Part 19
# Module 17: Linux Deployment, Nginx and PM2

**Estimated time: 4–5 hours | Tier: 2 | Requires: M4 Node.js, M6 HTTP, M16 Docker; OS processes/signals and CN TCP/TLS**

---

## Why this module exists

An API working in your terminal is only one part of deployment. A deployed backend needs a stable entry point, a process that survives a worker crash, deliberate permissions, useful logs, configuration, and a way to change code without unnecessarily interrupting requests.

This chapter answers the basic interview ladder: What does deploying a Node application actually mean? Why put Nginx in front of it? What does PM2 manage? Which process owns the port? What happens during a reload? Where do you look when the browser says 502?

**Organizing principle: follow the request, follow the process, and identify which component owns each failure.**

The questions are selected for this resume and their usefulness in explaining mechanisms. They are not a measured ranking of company interview frequency. Nginx and PM2 appearing on a resume supports asking about them; it does not prove a particular production configuration or uptime claim.

---

## 1. Deployment in one picture

Deployment means putting a particular application release and its configuration into an environment where intended users can reach it and operators can maintain it.

```text
Client
  | DNS lookup, TCP connection, TLS handshake
  v
Public ingress / firewall rules
  |
  v
Nginx: listening socket, TLS, routing, request limits, access log
  | HTTP on a private/loopback address
  v
Node HTTP server: application routes, validation, business logic
  | database pool / cache client / durable queue client
  v
Data and external services

PM2 daemon --> starts, watches process lifecycle, replaces Node workers
OS service manager --> can start PM2 after host boot
```

Nginx and PM2 have different jobs. Nginx receives network requests. PM2 starts and manages application processes. PM2 cluster workers can share an application port; this does not make PM2 the public HTTP policy layer.

| Component | Owns | Does not automatically provide |
| --- | --- | --- |
| Linux | Processes, users, sockets, files, scheduling, signals | Application-specific readiness or valid business results |
| Nginx | Incoming HTTP/TLS connection and selected upstream forwarding | Correct transactions, authenticated ownership checks, healthy application code |
| Node application | Request semantics, validation, authorization, resource cleanup | Host reboot recovery simply because it called listen |
| PM2 | Managed worker lifecycle, application logs, configured restart/reload | Database durability, multiple-host availability, successful schema rollback |
| systemd on a typical Linux VM | Boot/service lifecycle and supervision | Application deployment compatibility without explicit checks |

Revisit [M0](/docs/resume-skills/how-backend-works) for process/port/runtime vocabulary, [M4](/docs/resume-skills/nodejs) for Node internals, and [CN: HTTP](/docs/cn/http-web) for request semantics.

---

## 2. What was actually run

The authoring machine is Windows. Its only WSL distribution available for this work was docker-desktop. The executable example therefore uses a **real Linux container** as a temporary, single-host laboratory. Nginx and PM2 share its Linux network namespace; Node binds to its loopback address. This models the network/process relationship of one VM without claiming that a container is a full VM.

The image deliberately contains multiple tools and a harness-controlled lifecycle. Its sleep entrypoint is for the verifier. It is not a suggested production multi-service container design; a container deployment normally delegates lifecycle to the chosen container platform and chooses supervisors deliberately.

**Recorded on 14 October 2026:**

| Tool | Recorded version |
| --- | --- |
| node | v22.23.3 |
| pm2 | 7.0.4 |
| nginx | nginx version: nginx/1.22.1 |
| openssl | OpenSSL 3.0.22 25 Aug 2026 (Library: OpenSSL 3.0.22 25 Aug 2026) |
| linux | Linux 5.15.153.1-microsoft-standard-WSL2 |
| debian | 12.15 |

Docker client/engine: 29.8.2. The Node base image used for the build was resolved to:

```text
node@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392
```

The PM2 dependency tree is captured in package-lock.json. Debian packages are installed from the configured repositories during the build; the base digest and JavaScript lock do not freeze a future apt repository. These are observed versions, not a recommendation to deploy an old Nginx version or a promise that all current security fixes are installed.

### Reproduce the exercise

From the repository root, with Docker Desktop's Linux engine running:

```powershell
docker pull node:22-bookworm-slim
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 examples/resume-skills/module-17-linux-nginx-pm2/verify.py
```

Choose your Python interpreter path on another machine. The host verifier uses the Python standard library; Node, PM2, Nginx, OpenSSL and the Linux-side verifier run inside the image. The committed lockfile is used by npm ci. Initial Docker registry, Debian repository and npm registry access is required.

The reusable verifier assumes the engine is already running. It builds a uniquely labeled image, creates one owned container, publishes only the proxy's HTTP/TLS ports on ephemeral host loopback ports, runs real requests and removes the owned container/image and generated host scratch directory. It does not configure your host firewall, startup services or PM2 home. Port 3000 is unused.

In the recorded authoring session, Docker was initially stopped, was started for these examples, and was restored to stopped after confirming no containers remained. The public base image and build cache remain available. The temporary TLS private key existed only in the removed container; neither it nor a real credential is copied into these notes.

### Dependency audit boundary

The actual npm audit report, saved in dependency-audit.json, reported **eight high-severity package entries** in this locked PM2 dependency tree. The report includes direct advisory entries for basic-ftp, braces and js-yaml, plus their affected dependency ancestors; eight entries does not mean eight independent exploits.

This fixture uses a trusted CJS process declaration, disables file watching, and does not exercise FTP, PAC files or untrusted YAML parsing. Those facts bound the demonstrated paths; they do not establish that the package tree is safe for production. No automatic forced downgrade or unverified dependency override was applied. Re-audit and assess patched versions and exposure before adopting a real deployment. This is a functional learning snapshot, with the audit evidence retained.

---

## 3. Linux basics that explain deployment failures

### 3.1 Process, parent, user and working directory

A process is a running program with an address space, open file descriptors, environment and credentials. A PID identifies it during its lifetime. The parent/child relationship explains why a shell, PM2 daemon, worker and Nginx master can appear as different processes.

Linux users and groups influence what files and sockets the process can access. Running application workers with a dedicated unprivileged identity limits the damage of some mistakes. It is not a substitute for authorization or patching. In this laboratory, the Node workers actually ran as **UID 1000**. The verifier and Nginx master use root inside the owned container; Nginx workers use www-data. Do not infer that the entire container is non-root.

Relative file paths resolve against a working directory, which need not be the directory where the script is stored. A service started after reboot can therefore fail while the same command works in your shell. The PM2 declaration sets cwd explicitly; the observed application working directory was /opt/fixture.

Read-only diagnostic commands for a typical Linux host:

```bash
id
pwd
ps -eo pid,ppid,user,args
ss -lntp
ls -ld /srv /srv/placement /srv/placement/current
ls -l /srv/placement/current
```

Use the output to answer concrete questions: Is the intended process alive? Which identity runs it? What is listening? Is the address loopback or a public interface? Can the service identity traverse every parent directory? Some socket/process details require elevated visibility; lack of displayed metadata is not proof that no process exists.

### 3.2 Permissions: why chmod 777 is a poor diagnosis

For ordinary files, r permits reading, w writing and x execution. Directory permissions have different operational meanings: r lists names, x permits searching/traversing the directory, and w together with the necessary search permission permits changing directory entries. Ownership, groups, ACLs and additional security policies can affect the final result.

For the familiar three octal digits, read=4, write=2 and execute/search=1. Thus 600 gives the owner read/write; 640 also gives the group read; 755 gives the owner rwx and group/others r-x. The right mode depends on what the file is for. Secret material and executable assets should not receive identical permissions by habit. [Linux chmod documentation](https://man7.org/linux/man-pages/man1/chmod.1.html)

Two actual negative tests make the distinction visible:

| Fixture | Attempt made as the Node user | Observed result |
| --- | --- | --- |
| root-owned ordinary file, mode 600 | Read file | EACCES |
| root-owned parent directory, mode 700; child file mode 644 | Read child by its full path | EACCES |

The second case fails at parent-directory traversal even though the file itself is readable by others. Inspect the path, identity and required operation instead of granting every user write access. [Linux path resolution](https://man7.org/linux/man-pages/man7/path_resolution.7.html)

### 3.3 Environment belongs to a running process

An environment variable supplies configuration to a process. It does not edit application source, and changing a shell variable does not reach backward into already-running workers. A newly created child receives an environment derived from its parent or explicitly supplied at creation.

The exercise starts a child with RELEASE=inherited-v1, changes the parent's variable to parent-changed, then lets the child print its value. It prints inherited-v1. PM2 adds another lifecycle boundary: its managed environment can be retained across a restart unless explicitly updated. The real PM2 tests below demonstrate this.

Environment values are strings. Validate required values at startup and fail clearly on invalid ports, URLs or timeouts. Keep development defaults deliberate. Do not dump the entire environment into logs: credentials can be present. A secret delivered as an environment value is still available to the process and potentially privileged diagnostics.

### 3.4 Signals are requests with different guarantees

SIGTERM is commonly used to request termination. PM2 normally starts graceful stopping with SIGINT. An application can handle those signals and close resources. SIGKILL cannot be handled to finish an in-flight transaction; it is a forced termination mechanism.

Signals alone do not define a safe shutdown protocol. The application, proxy and supervisor must agree on admission, completion and deadlines. Do not promise that a killed worker finishes every request. The crash test intentionally uses SIGKILL on one fixture worker; PM2 replaces it, but that is recovery after failure, not proof that interrupted work completed. PM2's signal sequence and configurable kill timeout are documented in its [graceful shutdown guide](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/).

---

## 4. Listening addresses and the reverse proxy

A listening socket is bound to an address and port within a network namespace. On a single VM, 127.0.0.1:9000 can be reached locally while avoiding direct binding on the VM's public interface. Nginx on that same VM can forward to it.

```text
Same Linux namespace in this fixture:
Nginx 0.0.0.0:8080 and :8443 --> Node cluster 127.0.0.1:9000

Separate container namespaces, as in M16:
proxy container localhost != application container localhost
use an intended service/network address instead
```

The application was reachable through Linux loopback and through the published Nginx proxy. Connecting to port 9000 on the fixture container's bridge address failed. That observation proves the binding behavior tested here; it is not an audit of a real cloud firewall. Host-side inspection verified that only ports 8080/8443 were published and both were restricted to 127.0.0.1.

A **reverse proxy** receives client requests on behalf of one or more servers. It can centralize TLS, routing, limits, buffering and logs. A **forward proxy** acts on behalf of clients reaching other servers. The Node application server still executes the application. See the official [Nginx beginner's guide](https://nginx.org/en/docs/beginners_guide.html) for the static/proxy distinction.

Why use a proxy even with one application process? You may want a stable public endpoint, independent certificate handling, static-file serving or explicit ingress policies. It also adds configuration and another failure boundary. Choose it for requirements, not because every backend must contain Nginx.

---

## 5. The executable Nginx configuration

The fixture uses unprivileged listening ports internally so host ports 80/443 are not needed. A real public VM commonly listens on 80/443, with firewall and certificate configuration appropriate to that host. Paths here are fixture paths, not universal package defaults.

```nginx
user www-data;
worker_processes 1;
pid /run/m17/nginx.pid;
error_log /run/m17/error.log info;
events { worker_connections 256; }
http {
    log_format trace '$request_id $status $upstream_status $request_time $upstream_response_time "$request"';
    access_log /run/m17/access.log trace;
    client_max_body_size 1k;
    client_header_timeout 3s;
    client_body_timeout 3s;
    send_timeout 3s;
    keepalive_timeout 2s;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    # Single trusted ingress: replace client-supplied forwarding headers.
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $request_id;
    proxy_connect_timeout 1s;
    proxy_send_timeout 2s;
    proxy_read_timeout 1s;
    proxy_next_upstream off;
    server {
        listen 8080;
        listen 8443 ssl;
        server_name localhost;
        ssl_certificate /run/m17/tls/cert.pem;
        ssl_certificate_key /run/m17/tls/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        add_header X-Fixture-Release v1 always;
        location = /static/index.txt { root /run/m17; }
        location /api/ { proxy_pass http://127.0.0.1:9000/; }
        location /keep/ { proxy_pass http://127.0.0.1:9000; }
        location /drain/ {
            proxy_read_timeout 4s;
            proxy_pass http://127.0.0.1:9000/;
        }
        location / { return 404; }
    }
}
```

### 5.1 URI rewriting: a slash can change the route

For the simple prefix locations used here, a proxy_pass with a URI replaces the matching location prefix. A proxy_pass without a URI forwards the request URI in the tested unchanged case. Regex/named locations, rewrite directives and variables introduce further rules; do not extrapolate from one example to every Nginx configuration. [Official proxy_pass semantics](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)

Actual outputs:

```json
{
  "strip": "/echo?x=1",
  "preserve": "/keep/echo?x=1"
}
```

Trace them:

```text
GET /api/echo?x=1
location /api/ + proxy_pass http://127.0.0.1:9000/
Node receives /echo?x=1

GET /keep/echo?x=1
location /keep/ + proxy_pass http://127.0.0.1:9000
Node receives /keep/echo?x=1
```

When an API works directly but returns 404 through the proxy, compare the path that the application actually receives. A route mismatch is different from an unreachable upstream.

### 5.2 Forwarded headers are a trust boundary

After TLS termination, the application sees the proxy connection, which may be plain HTTP and have the proxy's IP. Forwarding headers carry context, but a client can also send headers with those names.

This example has one trusted ingress and replaces X-Forwarded-For with its socket peer, X-Forwarded-Proto with its connection scheme, and X-Request-ID with a generated identifier. A request carrying forged values did not preserve them:

```json
{
  "host": "127.0.0.1",
  "forwarded_for": "127.0.0.1",
  "forwarded_proto": "http",
  "request_id": "fde061e6f26033302bf335d576285401"
}
```

Appending X-Forwarded-For can be appropriate in a deliberately configured multi-proxy chain; it requires a consistent trusted-hop model. Never select an arbitrary client-supplied address as authoritative just because it appears first in a string. If using Express trust proxy, restrict it to the real topology and prevent clients from bypassing that boundary. Revisit [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy).

The application does not implement authentication, tenant authorization or secure-cookie policy here. Observing forwarded_proto=https is not proof that those features work.

### 5.3 Request limits and timeout ownership

| Boundary in the fixture | Setting | Actual evidence or limit |
| --- | --- | --- |
| Nginx request body | client_max_body_size 1k | A 2,048-byte body returned 413 |
| Application body | 2,048-byte streaming count | Source guard; not separately exercised beyond Nginx in this suite |
| Upstream connect | proxy_connect_timeout 1s | Configured; no controlled delayed-connect experiment |
| Upstream response gaps | proxy_read_timeout 1s on /api/ | Silent 1,500ms application response produced 504 |
| Long request used for drain | 4s proxy read timeout on /drain/ | 1,600ms request completed during worker reload |
| Application receiving headers/body | Explicit Node settings | Configured; slowloris resistance not established by this suite |
| Application stop | Force deadline 4s; PM2 kill timeout 5s | Normal drain completed; deadline exhaustion not injected |

proxy_read_timeout bounds the gap between successive upstream reads; it is not a whole-request stopwatch. A stream that keeps making progress can outlive it. Proxy connect, proxy send, client ingress and application dependency deadlines address different phases. Budget the complete request instead of increasing every timeout when an endpoint slows down. [Nginx proxy timeout documentation](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout)

Nginx body, client-body and response-send limits are documented separately in its [HTTP core module](https://nginx.org/en/docs/http/ngx_http_core_module.html). A maximum body size is not a complete upload strategy: streaming, temporary disk use, parsing limits, authorization and downstream storage still matter.

Buffering is also a design choice. Response buffering can decouple an upstream from a slow reader, but streaming/SSE routes need deliberate behavior and timeout settings. This suite does not test SSE, WebSockets, upstream keepalive-pool tuning or every buffering path. Do not present the single Connection header setting here as a universal WebSocket configuration.

---

## 6. TLS termination without confusing encryption and trust

TLS termination means the TLS connection ends at Nginx. The proxy decrypts the HTTP request and opens its configured upstream connection. Here that upstream is loopback HTTP within one Linux namespace; production traffic crossing hosts may require TLS on that leg too.

Nginx needs the server certificate and matching private key. The private key should be readable by the required server identity and otherwise restricted. The official [HTTPS configuration guide](https://nginx.org/en/docs/http/configuring_https_servers.html) explains the certificate/key and chain relationship.

The verifier generates a fresh one-day, self-signed certificate with localhost and 127.0.0.1 in its SAN. The key has mode 600. A test client explicitly trusts that certificate, then sends HTTPS requests. A client using its ordinary trust store rejects it. The certificate was also copied temporarily to the host test client to verify the actual published TLS endpoint, then removed.

| Observation | What it establishes |
| --- | --- |
| Explicitly trusted client receives 200 | A real TLS connection and proxied request worked with fixture trust |
| Default-trust client rejects certificate | Self-signing did not establish ordinary public trust |
| Application receives forwarded_proto=https | Nginx conveyed the tested inbound scheme |
| Key mode 600 | Recorded ordinary permission setting, not a complete secret-management audit |

A public deployment additionally needs correct DNS, certificate issuance/renewal, hostname coverage, full chain, expiry monitoring and suitable TLS policy. A successful local handshake is not a public certificate or proof that renewal works. For redirects, use a controlled canonical host and account for trusted upstream TLS termination; avoid blindly constructing security-sensitive redirects from an unvalidated Host header.

---

## 7. PM2: what it manages and what cluster mode changes

PM2 is a process manager. Its daemon tracks application definitions and worker status, starts workers and can restart them. The daemon and workers are separate processes. Your terminal need not remain attached for daemon-managed workers to run.

Useful commands for an application you own:

```bash
pm2 start ecosystem.config.cjs
pm2 list
pm2 describe m17-api
pm2 logs m17-api --lines 100 --nostream
pm2 restart m17-api
pm2 reload m17-api
pm2 stop m17-api
pm2 delete m17-api
```

stop leaves a stopped application definition; delete removes it from PM2's current managed list. Neither is a database backup or a deletion of source code. PM2_HOME selects the daemon's state location; running a CLI as a different user or with a different home can show a different list. The fixture scopes all PM2 commands to the node user and /run/m17/pm2. [PM2 process management](https://pm2.keymetrics.io/docs/usage/process-management/)

### 7.1 The actual process declaration

```javascript
module.exports = {
  apps: [{
    name: 'm17-api',
    script: '/opt/fixture/app.cjs',
    cwd: '/opt/fixture',
    instances: 2,
    exec_mode: 'cluster',
    wait_ready: true,
    listen_timeout: 5000,
    kill_timeout: 5000,
    min_uptime: 1000,
    max_restarts: 5,
    restart_delay: 200,
    watch: false,
    merge_logs: true,
    out_file: '/run/m17/logs/api-out.log',
    error_file: '/run/m17/logs/api-error.log',
    env: { NODE_ENV: 'production', PORT: '9000' },
  }],
};
```

Two instances are chosen to make process boundaries visible; they are not a measured capacity optimum. wait_ready makes the application send an explicit readiness message after listening. The example has no external database; in a real service, define which dependencies must be usable before announcing readiness.

watch=false avoids file-change restarts during the exercise. min_uptime, max_restarts and restart_delay bound a particular crash-loop policy; they do not turn broken code into a working release. The official [ecosystem declaration reference](https://pm2.keymetrics.io/docs/usage/application-declaration/) defines these fields.

### 7.2 Cluster mode is multiple processes

PM2 cluster mode uses Node's cluster machinery to run multiple application processes that can share a server port. Each worker has its own JavaScript heap and event loop. It can use multiple CPU cores, but each worker can still block its own event loop. [PM2 cluster mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/), [Node cluster](https://nodejs.org/api/cluster.html)

Actual initial worker PIDs and process-local counters:

```json
{
  "initial_pids": [
    46,
    58
  ],
  "per_worker_counters": {
    "46": [
      1,
      2,
      3,
      4,
      5
    ],
    "58": [
      1,
      2,
      3,
      4,
      5
    ]
  }
}
```

Both workers handled requests, and each began its own counter at 1. Do not treat the observed alternating distribution as a guaranteed scheduling order. The test demonstrates separate memory, not an external shared counter.

Consequences:

- In-memory sessions are not shared automatically. Use an appropriate shared session store or a deliberately different session design.
- A per-process rate limiter does not create one global request budget. Revisit M8/M15 for consistent shared enforcement.
- Starting a cron job inside every web worker can duplicate scheduled work. Put durable scheduling/claiming outside that assumption.
- A connection pool is normally per worker. Two workers with a pool maximum of ten can request up to twenty application connections before other process types are counted.
- WebSocket connections remain tied to particular processes; cross-worker messaging needs a design. Stateful transports can also require routing/session handling that a simple HTTP fixture does not demonstrate.

Scaling workers on one machine does not survive that machine disappearing. Nginx and PM2 on one VM remain in that VM's failure domain; M18 introduces the cloud/multiple-host boundary.

### 7.3 Crash recovery and environment changes: observed behavior

The verifier killed one known fixture worker with SIGKILL. PM2 replaced that PID, kept two online workers, and increased a restart counter. This shows worker recovery. It does not show transparent recovery of every request or database write interrupted by that crash.

Environment experiment:

```text
Initial workers:                         RELEASE=v1
CLI supplies v2, restart without update: workers still return v1
CLI supplies v2, restart --update-env:   new workers return v2
```

The process declaration deliberately does not hardcode RELEASE, allowing the test to isolate the managed environment behavior. Ecosystem env/env_production blocks are another configuration source; changing a declaration and selecting an environment has its own semantics. Consult the [PM2 environment guide](https://pm2.keymetrics.io/docs/usage/environment/) and verify the value from the new running process instead of assuming a shell edit applied.

---

## 8. Graceful shutdown and reload, step by step

### 8.1 The application must cooperate

For this bounded HTTP fixture:

```text
SIGINT/SIGTERM
  -> mark draining
  -> stop admitting new connections
  -> close idle keepalive connections
  -> let already accepted bounded requests finish
  -> close application resources
  -> exit before supervisor's hard deadline
```

An already accepted request can finish while new admission stops. A readiness endpoint returning 503 is useful only if an upstream or orchestrator actually observes it and acts; it does not remove the process from every routing path by itself.

The application source is deliberately small enough to inspect. It has no database, TLS listener, authentication or durable queue. It uses a force deadline shorter than PM2's kill timeout. The async delay is bounded for the drain experiment; it is not representative of every long-lived connection.

```javascript
'use strict';
const http = require('node:http');
const { randomUUID } = require('node:crypto');
const port = Number(process.env.PORT || 9000);
const release = process.env.RELEASE || 'v1';
let draining = false, counter = 0;
const log = (event, fields = {}) => console.log(JSON.stringify({ event, pid: process.pid, ...fields }));
const server = http.createServer(async (req, res) => {
  const id = req.headers['x-request-id'] || randomUUID();
  const url = new URL(req.url, 'http://fixture.invalid');
  const reply = (status, body) => {
    if (res.destroyed) return;
    res.writeHead(status, { 'content-type': 'application/json', 'x-request-id': id });
    res.end(JSON.stringify(body));
  };
  log('request_start', { id, path: url.pathname });
  res.on('finish', () => log('request_finish', { id, status: res.statusCode }));
  if (url.pathname === '/live') return reply(200, { live: true });
  if (url.pathname === '/ready') return reply(draining ? 503 : 200, { ready: !draining });
  if (draining) return reply(503, { error: 'draining' });
  if (req.method === 'GET' && url.pathname === '/slow') {
    const ms = Number(url.searchParams.get('ms') || 600);
    if (!Number.isInteger(ms) || ms < 0 || ms > 2000) return reply(400, { error: 'bad delay' });
    await new Promise(resolve => setTimeout(resolve, ms));
    return reply(200, { pid: process.pid, release, delayed_ms: ms });
  }
  if (req.method === 'GET' && url.pathname === '/counter') {
    return reply(200, { pid: process.pid, counter: ++counter });
  }
  if (req.method === 'POST' && url.pathname === '/echo') {
    let bytes = 0, chunks = [];
    for await (const chunk of req) {
      bytes += chunk.length;
      if (bytes > 2048) { reply(413, { error: 'body too large' }); req.resume(); return; }
      chunks.push(chunk);
    }
    return reply(200, { bytes, body: Buffer.concat(chunks).toString('utf8') });
  }
  if (req.method === 'GET' && ['/echo', '/keep/echo'].includes(url.pathname)) {
    return reply(200, {
      pid: process.pid, uid: process.getuid(), cwd: process.cwd(), release,
      url: req.url, remote: req.socket.remoteAddress,
      headers: { host: req.headers.host, forwarded_for: req.headers['x-forwarded-for'],
        forwarded_proto: req.headers['x-forwarded-proto'], request_id: id },
    });
  }
  reply(404, { error: 'route not found' });
});
server.requestTimeout = 5000;
server.headersTimeout = 3000;
server.keepAliveTimeout = 1000;
server.timeout = 6000;
server.on('clientError', (_error, socket) => socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n'));
function shutdown(signal) {
  if (draining) return;
  draining = true;
  log('shutdown_start', { signal });
  const deadline = setTimeout(() => {
    log('shutdown_forced'); server.closeAllConnections(); process.exit(1);
  }, 4000);
  deadline.unref();
  server.close(() => {
    clearTimeout(deadline); log('shutdown_complete'); process.exit(0);
  });
  server.closeIdleConnections();
}
process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
server.listen(port, '127.0.0.1', () => {
  log('listening', { port, release, uid: process.getuid() });
  if (process.send) process.send('ready');
});
```

For the tested Node version, server.close stops accepting new connections and waits for active work; closeIdleConnections handles idle HTTP connections. closeAllConnections is a forceful HTTP-connection operation, and upgraded WebSockets require separate tracking. Node's receive timeouts do not independently enforce a business-operation deadline after a complete request arrives. [Node HTTP server lifecycle](https://nodejs.org/api/http.html#serverclosecallback)

### 8.2 Restart and reload are different operations

A restart stops/replaces workers. A cluster reload attempts a rolling replacement: new workers become ready while existing ones finish. Its success depends on readiness, sufficient overlap capacity and timely shutdown. A timeout can force fallback behavior. Treat the official zero-downtime description as the intended operating mode, not an unconditional guarantee for arbitrary code, overload or broken releases.

Actual reload result:

```json
{
  "before_pids": [
    220,
    233
  ],
  "after_pids": [
    265,
    278
  ],
  "sample_count": 34,
  "sample_statuses": [
    200
  ],
  "drained_request": {
    "pid": 220,
    "release": "v2",
    "delayed_ms": 1600
  }
}
```

The test began a 1,600ms request, waited until the application logged its start, then launched a PM2 reload and sent additional small requests. All recorded sample requests returned 200. Both old worker PIDs were replaced. The long request returned from an old PID, and its finish log preceded that worker's shutdown_complete log. No shutdown_forced event occurred in this normal reload.

This is a concrete bounded drain experiment. It is not a load benchmark, proof of every possible request succeeding, a WebSocket-draining test or evidence that forced shutdown never occurs. It also changes process instances while retaining the same application source; a real release still needs code/schema compatibility checks.

### 8.3 A useful deadline relationship

Allow enough time for accepted bounded work, with margin before the supervisor's hard stop. Account for upstream removal delays, dependency cancellations, database pool closure and long-lived connections. If the business operation cannot finish before the deadline, decide whether to cancel, persist resumable work or return a job identifier. Increasing kill_timeout indefinitely can merely hide a leak.

Once an operation has side effects, retries require idempotency and transaction reasoning. PM2 replacing a worker cannot tell a client whether its payment committed. Revisit [M9](/docs/resume-skills/webhooks-payments-reliable-integrations) and [M15](/docs/resume-skills/caching-background-jobs-data-ingestion).

---

## 9. Logs and diagnosis: locate the failing hop

Nginx access logs describe incoming requests and selected upstream timing/status. Nginx error logs explain failures such as connection refusal or upstream timeout. Application logs describe route execution, dependency errors and lifecycle. PM2 logs describe managed process behavior and capture stdout/stderr. You need more than one view to connect a worker replacement to a user-visible failure.

The fixture logs a generated request ID at the proxy and echoes it from the application. Its application log contains JSON request_start, request_finish and shutdown events. The Nginx log format records request ID, response status, upstream status, overall request time and upstream response time. The suite verifies a particular ID appears in both the proxied response and the access log. [Nginx log module](https://nginx.org/en/docs/http/ngx_http_log_module.html)

Avoid logging authorization headers, secrets or complete sensitive request bodies. Decide retention, rotation, disk limits, access controls and central collection. PM2 log files do not remain bounded merely because PM2 runs. File rotation/modules and external collection are deployment choices, not part of these tests. [PM2 log management](https://pm2.keymetrics.io/docs/usage/log-management/)

| Symptom | First boundary to inspect | Evidence to seek |
| --- | --- | --- |
| Connection refused before HTTP | Target address/port and listening process | ss output, process state, firewall path |
| TLS trust/name failure | Certificate identity, chain and client trust | Actual certificate/SAN/expiry, intended hostname |
| Nginx 404 | Location/static routing, then upstream URI if proxied | Access/upstream status and application received path |
| Nginx 413 | Ingress size policy | Request size, configured location/body limit |
| Nginx 502 | Invalid/unavailable upstream response | Error log, upstream socket, protocol/address, worker state |
| Nginx 504 | Upstream timing boundary | Error log, dependency latency, response-gap settings |
| Application 500 | Application execution | Correlated error/trace, dependency and business failure |
| Worker repeatedly restarting | Process exit/config/resource boundary | PM2 restart count, stderr, exit reason, environment |
| App works in shell but not service | Identity/cwd/env/startup boundary | Actual running process credentials and configuration |

The fixture reproduced 502 by stopping both application workers while leaving Nginx running, and 504 with a silent delayed application response. Those are examples, not exclusive definitions: other upstream failures can produce the same status. Diagnose the error log before assigning a root cause.

Do not blindly retry every failed POST. A proxy error can occur after an upstream accepted or committed work. This configuration disables proxy_next_upstream for clarity; real retry policy must account for operation semantics and deduplication.

---

## 10. Nginx reload and PM2 boot persistence are separate

### 10.1 Validate a candidate before changing the live configuration

Nginx has a master process and workers. A configuration reload starts workers with the new configuration and asks old workers to finish existing clients. Its control documentation describes validation/application failure handling and keeping the existing configuration when applying a reload fails. [Nginx process control](https://nginx.org/en/docs/control.html)

In this suite, the verifier first ran nginx -t on a **separate invalid candidate**. It failed; the live configuration was not overwritten or signaled, and requests kept working with the same master PID. Then a valid candidate changed a response header from v1 to v2, passed nginx -t and was reloaded; the master PID stayed the same and the new header appeared.

Be precise: the first test establishes the validate-before-apply workflow. It does not directly inject an invalid HUP into the live master or test every reload failure. In a real release, syntax validation still cannot prove that the new upstream port, route, certificate renewal or application behavior is correct.

### 10.2 Save/resurrect is not a host reboot test

```bash
pm2 save
pm2 resurrect
```

The first saves the managed application list; the second can restore a saved list. The suite saved two worker definitions, stopped/deleted them from the current list, and resurrected them. They became ready and returned the expected v2 environment. The PM2 daemon itself remained available during this experiment.

To restore after host reboot on a typical VM, an OS startup service must launch the appropriate PM2 environment and resurrect the intended saved list. PM2's documented workflow includes running pm2 startup as the intended user, reviewing/executing its generated privileged command, and using pm2 save. Generated paths and service identities depend on the machine. Changing the Node installation path can require refreshing startup integration. [PM2 startup guide](https://pm2.keymetrics.io/docs/usage/startup/)

**Documented deployment workflow, not executed here:**

```bash
# As the dedicated application user on the intended VM:
pm2 startup
# Review and run the host-specific command PM2 prints with its required privileges.
pm2 save
# Inspect the actual generated unit; substitute its real name:
systemctl status pm2-placement
journalctl -u pm2-placement --since '10 minutes ago'
```

The unit name above is illustrative. This container does not boot systemd as its service manager. No host reboot, generated service installation or journal recovery was performed. Also do not put the same application's workers under two competing supervisors without deciding which one owns restart and stop behavior.

---

## 11. Architectural understanding: build and operate a small backend deployment

### 11.1 Start with requirements

Assume a small authenticated API with PostgreSQL, a public HTTPS endpoint, bounded request sizes, moderate traffic and deployments by a small team. Before selecting worker count, ask about latency targets, peak concurrency, CPU/memory, pool limits, background work, acceptable downtime, data recovery and cost. Those answers determine whether a single VM is sufficient.

```text
DNS api.example.test
   |
   v
VM ingress: intended HTTPS exposure and controlled administrative access
   |
   v
Nginx :443 -- controlled forwarding context --> Node cluster loopback :9000
                                                 |
                                                 +--> PostgreSQL pool per worker
                                                 +--> shared cache/session state if needed
                                                 +--> durable job enqueue

Dedicated app identity; immutable release directory; runtime configuration
PM2 worker lifecycle; OS startup service; bounded logs and monitoring
```

This is a proposed production extension. The fixture verifies the proxy/process boundary, not the illustrated authentication, database, public DNS, firewall or durable jobs.

### 11.2 A build path with reviewable checkpoints

1. **Package a release.** Record the source revision, supported Node version, lockfile and build output. Use dependency installation/build steps appropriate to that application. M16 explains a container alternative; a VM release directory is another option.
2. **Choose identities and paths.** Give the service only the read/traverse/write access it needs. Keep writable uploads/logs/state separate from release code. Confirm cwd and environment from the actual running process.
3. **Bring up the application privately.** Validate required configuration, bind the intended private address, and probe meaningful readiness. Test a real route and a dependency operation without opening an unnecessary public application port.
4. **Configure ingress.** Use a reviewed Nginx candidate with the correct upstream path/address, trusted forwarding rules, body limits, deadlines and logs. Validate syntax, then verify behavior through the proxy.
5. **Complete HTTPS and exposure.** Configure the real hostname, trusted certificate chain and renewal, then test from the expected client path. Verify that application/database ports are not accidentally exposed.
6. **Exercise lifecycle.** Test a worker failure, a normal drain/reload, a failed startup and resource exhaustion behavior within a controlled environment. Add boot recovery verification on a disposable VM or staging host.
7. **Prepare rollback and recovery.** Retain a known release, specify data compatibility and test restoration. Write down the exact health signal and conditions that stop a rollout.

The first working deployment is not complete until you can diagnose a bad release and recover it. The next modules add cloud reachability and CI/observability.

### 11.3 Release directories and rollback

A common VM approach stores immutable releases under /srv/placement/releases/<revision>, keeps a current pointer, and defines which release PM2 should launch. Switching a symlink alone does not replace running processes: existing workers retain their loaded code and configuration. Start/reload the intended release and verify what the new process reports. Do not assume a declaration's cwd/script resolution follows a changed symlink exactly as intended; inspect it on the actual setup.

Rollback means returning to an earlier compatible application/configuration, then verifying behavior. It does not reverse database mutations automatically. A destructive migration can make the earlier application unusable. Prefer compatible expand/migrate/contract changes where appropriate; roll out application and schema changes in an order that permits overlap.

For more explicit cutover, a blue/green design can start a candidate on a separate private port, probe it, change the proxy upstream, drain the previous release and retain it briefly for rollback. That requires capacity for overlap and a plan for shared schema, sessions and background workers. It remains a design here; no blue/green release or schema migration was performed.

### 11.4 Walk through a failed deployment

Suppose Nginx returns 502 immediately after a release:

```text
1. Confirm Nginx itself is responding; capture request ID and error log.
2. Inspect configured upstream address/protocol/path.
3. Check ss and PM2 status as the intended service identity.
4. Read startup stderr: bad environment? missing file? denied permission?
5. Probe the private application endpoint if it is listening.
6. If the candidate is faulty, restore a compatible known release/config.
7. Verify through the public ingress path and monitor for repeated failure.
```

Examples of different fixes: a process bound on the wrong address needs a binding correction; a missing variable needs a validated environment update; EACCES needs the appropriate identity/path access; database connection exhaustion needs a pool/concurrency diagnosis. A larger Nginx timeout does not fix a closed application port.

If 504 appears only under load, inspect event-loop blocking, pool waits, slow queries and dependency timeouts. Increasing PM2 instances can worsen an already saturated database by multiplying pools. Scale using measurements and bottleneck ownership, not only CPU count.

---

## 12. Resume connection and explanation drills

An honest 30-second answer:

> Linux hosts the processes and sockets. Nginx receives HTTP/TLS requests and forwards selected routes to the Node application. PM2 manages the application workers and can replace a crashed worker or attempt a rolling reload. The application still needs validation, shared state, graceful shutdown and useful readiness. I diagnose failures by checking the proxy, listening socket and worker logs in order.

For a two-minute explanation, add the request path, trusted forwarding headers, one timeout boundary and what happens during reload. For a five-minute discussion, add permissions/environment, per-worker memory/pools, startup persistence, rollback compatibility and the single-host failure domain.

If discussing your resume's load balancer, distinguish that project's routing algorithm from Nginx reverse proxying and PM2 worker lifecycle. Explain which part you implemented yourself, how health was detected, and how any throughput claim was measured. The fixture's successful HTTP samples are not a benchmark of that resume project.

---

## 13. Must remember and common wrong answers

| Say this | Avoid this |
| --- | --- |
| A process owns a listening socket in a network namespace | Port 9000 is reachable everywhere once the app starts |
| Nginx forwards requests; PM2 manages worker lifecycle | Nginx and PM2 are interchangeable load balancers |
| Cluster workers have separate heaps | All workers share a global JavaScript object |
| A restart can retain PM2's managed environment | Editing the shell always updates running workers |
| A reload needs readiness, overlap capacity and bounded shutdown | PM2 guarantees zero dropped requests in all situations |
| A readiness signal needs a consumer and policy | /ready automatically stops all traffic |
| proxy_read_timeout is an upstream response-gap limit | It is always the maximum duration of a complete request |
| 502 and 504 identify boundaries to investigate | Every 502 means one particular bug |
| save/resurrect and OS startup integration are separate | pm2 save alone guarantees reboot recovery |
| TLS needs identity/trust and a protected key | Any self-signed certificate gives normal public trust |
| File access depends on identity and parent traversal | chmod 777 is the standard deployment fix |
| Rollback must account for data/schema compatibility | Reverting code automatically reverts the database |

---

## 14. Interview questions and follow-ups

### Q1. What does deploying a backend mean?

Putting a particular application release and configuration into a reachable, operable environment. Explain the process, address/port, ingress, dependencies, lifecycle, logs and recovery. Uploading source without starting/configuring a service does not complete that path.

### Q2. What is Nginx and why put it before Node?

A web server that can act as a reverse proxy. It can centralize TLS, routing, limits and logs while Node executes application logic. The reason to add it depends on requirements and the chosen platform; an extra component also needs configuration and operation.

### Q3. Reverse proxy versus forward proxy?

A reverse proxy receives requests on behalf of backend servers. A forward proxy helps clients reach other destinations. Identify whose endpoint the client intentionally contacts and where the proxy forwards the request.

### Q4. What is PM2?

A process manager that starts and tracks applications, captures logs and applies configured restart/reload behavior. It manages worker lifecycle; it does not make application transactions durable or provide multi-host availability by itself.

### Q5. Can Node serve HTTP without Nginx or PM2?

Yes: Node's HTTP server can listen directly. The surrounding deployment still needs intentional TLS/ingress and lifecycle ownership, whether supplied by Node configuration, an OS supervisor, a platform or other components. Explain which responsibility each selected tool handles.

### Q6. What is the difference between 127.0.0.1 and 0.0.0.0 when listening?

127.0.0.1 is IPv4 loopback in that namespace. 0.0.0.0 binds all IPv4 interfaces there; it is not a destination address clients normally use. External reachability also depends on namespace, publishing, routing and firewall configuration. IPv6 binding is a separate consideration.

### Q7. Why does localhost work on a VM but fail between containers?

The VM's processes can share one network namespace. Separate containers generally have separate loopback interfaces. A proxy in one container must use the intended service/network address for another, rather than its own localhost. M16 demonstrates that boundary.

### Q8. What is the Nginx master/worker model?

The master coordinates configuration/lifecycle and workers handle connections. Reloading can start workers with new configuration while old workers finish existing clients. The suite observed a stable master PID across a valid reload; that does not prove every possible connection type drains successfully.

### Q9. Why run nginx -t before reload?

It checks the candidate's configuration syntax and relevant referenced resources before applying it. The fixture rejected an invalid separate candidate while live requests kept working. A successful check still cannot prove correct business routing or that a new application version is healthy.

### Q10. How can a trailing slash in proxy_pass break an API?

In the tested prefix case, providing a URI replaces the matched prefix; omitting it preserves the path. Thus /api/echo can become /echo. Compare the actual upstream URI with application routes and account for the additional rules around rewrites, variables and regex locations.

### Q11. What is TLS termination?

The TLS session ends at the proxy, which forwards a separate upstream request. Upstream HTTP may be appropriate on a controlled local path; a cross-host leg may require its own TLS. Encryption, certificate identity, trust, renewal and application authorization are distinct concerns.

### Q12. Does a successful self-signed HTTPS test prove public TLS works?

No. The fixture client explicitly trusted its generated certificate; a default-trust client rejected it. Public operation additionally requires the intended hostname, trusted issuance/chain, renewal and correct exposure. The exercise verifies the local TLS mechanism.

### Q13. Why are X-Forwarded-For and X-Forwarded-Proto sensitive?

Applications may use them for client IP, secure redirects, rate limits or cookie decisions. Clients can forge them unless trusted ingress reconstructs or validates the context. Configure trusted hops and prevent direct bypass; the right treatment depends on the proxy topology.

### Q14. What is the difference between 502 and 504?

502 commonly indicates an invalid or unavailable upstream response; 504 indicates an upstream timeout boundary. The fixture reproduced them using stopped workers and a silent delayed route. Inspect logs and the actual connection phase; the same status can have several causes.

### Q15. Is proxy_read_timeout a complete request deadline?

No: it measures a gap between successive reads from the upstream. Other phases have other limits, and a progressing stream can last longer. Set end-to-end budgets and dependency cancellation deliberately instead of assuming this directive bounds all work.

### Q16. How would you prevent oversized requests?

Set appropriate ingress limits and validate/count bytes at the application boundary, with parsing and storage limits for the format. The suite demonstrated Nginx returning 413 for a body over its limit. Size limits alone do not establish upload safety, authorization or bounded processing cost.

### Q17. What changes in PM2 cluster mode?

Multiple application processes can share the server port. Their heaps and event loops are separate. This can use multiple cores, but it changes state and connection budgeting. The exercise saw two PIDs and two independent counters; worker scheduling order is not a guarantee.

### Q18. Can I store sessions or a global rate limit in a JavaScript Map?

A Map is process-local and disappears on worker replacement. With multiple workers it also fragments the state. Use an appropriate shared store or different protocol design when the requirement is shared/durable state, and account for concurrency and failure there.

### Q19. Why can adding workers overload PostgreSQL?

Each worker can create its own pool. Multiply the configured maximum by all relevant workers/hosts and include background/admin connections. More web workers can increase contention on the same data service. Use pool/concurrency limits and measurements from the actual bottleneck.

### Q20. What is the difference between PM2 restart and reload?

Restart replaces processes; cluster reload attempts rolling replacement with readiness and shutdown coordination. Reload can still fail or fall back on timeouts. This fixture verified a successful bounded reload with sampled traffic, not an unconditional zero-loss guarantee.

### Q21. How do you gracefully stop a Node HTTP server?

Mark it draining, stop new admission, close idle connections, wait for bounded active requests and close resources before an explicit deadline. Handle the supervisor's signal. Track upgraded connections separately and define a policy for work that cannot finish. Forced termination is still possible.

### Q22. Why does PM2 use wait_ready?

It lets the application explicitly announce that initialization is complete instead of relying only on process existence. The fixture announces after listening. A real service must choose which dependencies and checks are required; a ready message is not a permanent health guarantee.

### Q23. Does SIGKILL run shutdown handlers?

No. Do not depend on it to release application resources cleanly or finish writes. OS process resources are reclaimed, but external side effects require their own correctness design. PM2 replacement restores a worker, not the outcome of an interrupted operation.

### Q24. Why did a new environment variable not reach the application?

Check which process received it and whether PM2 updated the managed environment. In the experiment, restart without --update-env retained v1; an explicit update produced v2. Also inspect ecosystem environment selection and the real running process, without leaking secrets.

### Q25. What do pm2 save and resurrect prove?

They persist and restore a managed process list. The suite restored two deleted definitions within the same available daemon environment. Boot recovery additionally needs correct startup integration and must be tested on the actual service-manager setup.

### Q26. How do you debug permission denied after deployment?

Identify the failing operation, service user, ownership, modes and every parent directory's search permission. Check ACLs/policies when relevant. The fixture's mode-644 file was inaccessible behind a mode-700 parent; granting file read permission alone did not solve traversal.

### Q27. Which logs help diagnose a request failure?

Correlate ingress access/error logs with application/dependency and process-manager events using a request ID. Compare final response status, upstream status/timing and worker restart history. Protect sensitive data and bound log storage; one log file rarely describes the entire failure.

### Q28. How would you roll back a bad release?

Select a known compatible application/configuration, start or reload it, and verify through the real ingress. Retain release artifacts and define rollback criteria. Check schema/data compatibility first: code rollback cannot automatically undo destructive migrations or external side effects.

### Q29. Does Nginx plus PM2 make a highly available system?

They can improve operation within a host, but one host remains one failure domain. Multiple hosts, routing/health policy, shared data, capacity, backups and tested recovery are separate requirements. Do not convert a worker-restart test into a multi-zone availability claim.

### Q30. Design and diagnose a small Node deployment in five minutes.

State requirements, draw client → ingress/TLS → private Node workers → database/queue, then assign identity, configuration, logs and lifecycle ownership. Explain pool/state implications, a bounded reload, rollback and boot recovery. Walk a 502 through upstream socket/process checks and a 504 through timing/dependency checks; distinguish verified behavior from proposed production additions.

---

## 15. Practice tasks

1. **Trace one request.** Draw the address, protocol, path and owning process at every hop. Explain which namespace each localhost belongs to.
2. **Diagnose file access.** Reproduce a readable file behind an unsearchable parent directory as an unprivileged user; fix only the required access.
3. **Predict routing.** Write expected upstream URIs for the two proxy_pass variants, then run requests and compare received paths.
4. **Test forwarding trust.** Send forged forwarding headers through the intended ingress. Verify which values survive and explain your trusted-hop policy.
5. **Explain TLS trust.** Make one explicitly trusted local request and one default-trust rejection. Describe what a public certificate adds and how renewal would be verified.
6. **Break the upstream.** Stop your owned application, capture 502 and its proxy error, restore it, then trigger a bounded silent-delay 504 and compare evidence.
7. **Observe process boundaries.** Show two worker PIDs and independent counters. Calculate the potential pool maximum for a proposed worker/pool configuration.
8. **Verify a drain.** Begin a bounded request, wait for its start log, reload and confirm finish-before-exit. State the cases this test does not cover.
9. **Check configuration persistence.** Compare environment restart/update behavior and save/resurrect. Plan a separate staging-VM reboot test with success criteria.
10. **Plan a compatible rollback.** Sketch release paths, readiness/cutover, previous-release retention and a schema change safe for both overlapping versions. Identify one migration that would break that plan.

---

## 16. Exit checklist

- [ ] I can trace a request through Nginx to Node and assign each responsibility.
- [ ] I can explain process/user/cwd/environment and diagnose parent-directory traversal.
- [ ] I can distinguish loopback binding from public reachability and container namespaces.
- [ ] I can predict the tested proxy_pass URI behavior and verify a route mismatch.
- [ ] I can explain forwarded-header trust without trusting arbitrary client values.
- [ ] I can distinguish local TLS encryption from public certificate trust and renewal.
- [ ] I can diagnose 413, 502 and 504 using the relevant boundary and logs.
- [ ] I can explain independent cluster memory and per-worker database pools.
- [ ] I can demonstrate environment update and worker crash recovery without overclaiming.
- [ ] I can explain readiness, draining, force deadlines and reload limitations.
- [ ] I can separate save/resurrect from verified host reboot recovery.
- [ ] I can outline a rollback that accounts for schema and external side effects.

These are learning checks for you to demonstrate, not authoring completion ticks.

---

## 17. Sources and verification map

Primary documentation researched for this chapter:

- [Nginx beginner's guide](https://nginx.org/en/docs/beginners_guide.html), [process control](https://nginx.org/en/docs/control.html), [proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html), [HTTP core](https://nginx.org/en/docs/http/ngx_http_core_module.html), [access log module](https://nginx.org/en/docs/http/ngx_http_log_module.html) and [HTTPS configuration](https://nginx.org/en/docs/http/configuring_https_servers.html).
- [PM2 process management](https://pm2.keymetrics.io/docs/usage/process-management/), [ecosystem declaration](https://pm2.keymetrics.io/docs/usage/application-declaration/), [environment](https://pm2.keymetrics.io/docs/usage/environment/), [cluster mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/), [signals/readiness](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/), [startup](https://pm2.keymetrics.io/docs/usage/startup/) and [logs](https://pm2.keymetrics.io/docs/usage/log-management/).
- [Node HTTP](https://nodejs.org/api/http.html), [Node cluster](https://nodejs.org/api/cluster.html), [Linux chmod](https://man7.org/linux/man-pages/man1/chmod.1.html) and [path resolution](https://man7.org/linux/man-pages/man7/path_resolution.7.html).

Official current documentation can describe versions newer than the executable snapshot. The tested source uses the subset recorded here. Refresh version-sensitive behavior and security status before applying it elsewhere.

**40 checks passed** against actual processes and requests:

| Group | Named checks | Evidence |
| --- | --- | --- |
| Linux | 6 | UID/cwd, file denial, directory traversal denial, child environment snapshot, loopback-only app |
| Nginx | 14 | Syntax, static/proxy routes, URI rewrite, trusted headers, body limits/statuses, timeout, logs, candidate validation and reload |
| TLS | 4 | Explicit fixture trust, forwarded scheme, default-trust rejection and key permissions |
| PM2 | 8 | Two workers, both serving, private counters, crash replacement, environment retention/update, save and resurrect |
| Lifecycle | 5 | New PIDs, successful sampled requests, active request completion, finish-before-exit and no forced normal drain |
| Host | 3 | Only loopback proxy publications, actual published HTTP and actual published HTTPS |
| **Total** | **40** | Named checks, some with multiple assertions |

Implementation: app.cjs, ecosystem.config.cjs, nginx.conf, Dockerfile, package.json/package-lock.json, verify_linux.py and verify.py under examples/resume-skills/module-17-linux-nginx-pm2/. The chapter embeds the three application/configuration sources exactly. The Dockerfile builds the Linux laboratory:

```dockerfile
ARG NODE_IMAGE=node:22-bookworm-slim
FROM ${NODE_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx openssl python3 procps iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/fixture
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts
ENV PATH="/opt/fixture/node_modules/.bin:${PATH}"
COPY app.cjs ecosystem.config.cjs nginx.conf verify_linux.py ./
RUN mkdir -p /run/m17 /run/m17/tls /run/m17/static /run/m17/logs /run/m17/pm2 \
    && printf 'm17-static-ok\n' > /run/m17/static/index.txt \
    && chown -R node:node /run/m17/logs /run/m17/pm2
# A test harness shares one Linux network namespace to model a single VM.
# This is not a production multi-service container entrypoint.
CMD ["sleep", "infinity"]
```

Results: verification-results.json, linux-results.json, verification-output.txt, linux-command-output.json, docker-command-output.json and image-build-output.txt. Actual application and Nginx logs are saved separately. dependency-audit.json preserves the package report. cleanup-results.json and engine-session-results.json record owned-resource removal and the authoring-session engine restoration; chapter/site validation files are stored alongside them.

Untested production extensions include public DNS/CA issuance and renewal, host/systemd reboot recovery, cloud firewall/IAM, authentication, a real application database, blue/green cutover, database migrations, backup restore, adversarial ingress, slow clients, WebSocket/SSE draining, deadline exhaustion and production load/capacity. The fixture does not claim a production-hardened dependency tree or universal zero-downtime behavior.

---

## Next

Continue to [M18: AWS and GCP Fundamentals for This Resume](/docs/resume-skills/aws-gcp-fundamentals) for regions/AZs, EC2, network reachability, IAM, load-balancer health, CDN paths and Cloud Tasks delivery/authentication boundaries.

Revisit [M16: Docker](/docs/resume-skills/docker-fundamentals) for packaging/network/storage boundaries, [M13: PostgreSQL](/docs/resume-skills/postgresql-backend) for per-worker pools, and [M15: Caching, Jobs and Ingestion](/docs/resume-skills/caching-background-jobs-data-ingestion) for work that should outlive a web request. The [master roadmap](/docs/resume-skills) shows the remaining sections.
