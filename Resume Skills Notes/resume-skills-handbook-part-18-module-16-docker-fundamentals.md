# Resume Skills Placement Handbook — Part 18
# Module 16: Docker Fundamentals

**Module 16 · 4–5 hours · Tier 2 · Requires: M0, one backend framework; M13 for the PostgreSQL application boundary**

---

## Why this module matters

Docker packages an application's runtime and files into an image and runs it as a container with explicit configuration. It makes application environments easier to distribute, but does not remove operating-system, networking, storage or deployment responsibilities.

An interviewer can start with “Image versus container?” and quickly ask why a container exits, why localhost cannot reach the database, why EXPOSE did not publish a port, whether a volume survives recreation or whether an unhealthy container restarts automatically.

> **The image supplies a filesystem and default configuration; the container supplies a running process and runtime boundaries; durable state and operational policy must be designed explicitly.**

This chapter builds a small API plus PostgreSQL deployment. It connects actual Docker behavior to the existing [OS](/docs/os), [CN](/docs/cn) and [PostgreSQL](/docs/resume-skills/postgresql-backend) notes.

**Verification: 40 checks passed on real Linux containers — five build, six HTTP, five lifecycle, five networking, three readiness, ten runtime and six storage checks.** These are named checks; some contain several assertions. Docker/Compose, the API and the database actually ran. No mocked container engine supplied these results.

### Recorded environment

| Component | Executed version / boundary |
| --- | --- |
| Host | Windows; verifier CPython 3.12.10 |
| Docker client / Linux engine | 29.8.2 / 29.8.2 |
| Docker Compose | 5.5.1 |
| Buildx | 0.37.2 |
| Linux engine kernel | 5.15.153.1-microsoft-standard-WSL2 |
| Engine cgroups | Version 1 in this run |
| Python inside API image | 3.12.15 |
| PostgreSQL inside database container | 18.6 |
| API dependencies | Psycopg/psycopg-binary 3.3.4, psycopg-pool 3.3.1, typing_extensions 4.16.0 |

The host and container Python versions differ. The container uses its image's runtime, not the host's installed interpreter. The Linux container's kernel matches the Docker engine's WSL2 Linux kernel, not the native Windows kernel. This run does not verify Windows containers or ARM execution.

The Python and PostgreSQL tags were resolved to registry digests before this run. Their recorded references are embedded below. Version pins plus recorded digests improve traceability; this is not a claim of a hash-locked, fully hermetic or bit-for-bit reproducible package build.

```json
{
  "PYTHON_IMAGE": "python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1",
  "POSTGRES_IMAGE": "postgres@sha256:77f585114c32fbca283dc835b0596f4e52b51b4c6662d7810b2f4084f60a1873"
}
```

### Run the complete verifier

Start Docker Desktop's Linux engine first. From the repository root:

```powershell
docker pull python:3.12-slim
docker pull postgres:18-alpine
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 examples/resume-skills/module-16-docker/verify.py
```

The last command uses the recorded host interpreter path. On another machine, select Python 3.12 and run verify.py with that interpreter. The host verifier uses standard-library modules; application dependencies are installed inside the image from requirements.lock.txt. Initial image/package downloads need registry/package access.

The verifier requires a Linux Docker engine and existing local copies of the two public base tags. It resolves their digests, assigns a unique Compose project/image, publishes only ephemeral loopback API ports and checks labels before cleanup. It removes its own containers, network, volume and application image. It does not run a global prune or delete unrelated Docker objects.

In this session the engine was initially stopped, with no existing containers. It was started for verification and restored to stopped afterward. Public base images and BuildKit cache were retained. The reusable verifier itself does not shut down your Docker Desktop. **Port 3000 remains stopped.** Native PostgreSQL/MongoDB services and user PDFs are untouched.

---

## 16.1 Image, container, VM and Docker Engine

| Term | What it is | What to avoid confusing it with |
| --- | --- | --- |
| Image | Immutable content/configuration used to create containers | A running process or a database backup |
| Container | Runtime instance with process, writable state and configured boundaries | A complete virtual machine |
| Dockerfile | Build instructions for producing an image | The runtime deployment configuration |
| Registry | Distribution service storing image content/manifests | The local running engine |
| Docker client | CLI/API client sending operations to an engine | Proof that the daemon is available |
| Docker Engine | Service/runtime stack managing container objects | Your HTTP application server |
| Compose | Application/service configuration and lifecycle tooling | A Dockerfile, cluster scheduler or automatic production HA system |

A VM supplies a guest operating system/kernel behind a virtualization boundary. Linux containers normally share the Linux engine host's kernel while isolating selected process/network/mount views. An image can supply a Linux userspace without supplying a separate kernel for every container. References: [Docker architecture](https://docs.docker.com/get-started/docker-overview/), [container versus VM](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/).

On this Windows machine, Docker Desktop's WSL2 backend supplies the Linux engine environment. The picture is:

```text
Windows host: docker CLI / browser / verifier
  -> Docker Desktop / WSL2 Linux environment
       -> Linux Docker engine/runtime
            -> API container: Python + application
            -> DB container: PostgreSQL
            -> network, volume and runtime resource boundaries
```

“Containers share the host kernel” needs that layer specified. Here it means the Linux engine environment's kernel. It does not mean a Linux Python process suddenly uses the Windows NT kernel directly. Reference: [Docker Desktop WSL2 backend](https://docs.docker.com/desktop/features/wsl/).

### What containers isolate and constrain

Linux namespaces provide separate views of selected system resources. Cgroups account for and constrain resources such as CPU, memory and process counts. Filesystem layers/mounts determine visible files. Capabilities, privilege settings and other security mechanisms affect permitted actions.

These are not a guarantee of complete isolation from every host risk. The engine/daemon is a powerful control boundary; privileged containers, host mounts and Docker socket access can change the risk substantially. Our tests inspect/apply specific settings and exercise selected denials, not a container-escape or adversarial isolation audit. Reference: [engine security](https://docs.docker.com/engine/security/).

### Portability has requirements

An image standardizes runtime files and dependencies. It still needs a compatible OS/architecture/kernel environment, configuration, secrets, reachable dependencies and suitable resources. Host-specific bind paths remain host-specific. “It runs in Docker” does not prove every deployment environment has the same behavior.

---

## 16.2 Image contents, layers, tags and digests

An image combines filesystem content with metadata such as default command, user, workdir, environment and exposed-port descriptions. Filesystem-changing build operations can add layers; metadata instructions do not imply one new filesystem layer each.

A container adds its own writable layer unless storage/mount settings override relevant paths. Changes inside that layer do not mutate the original image. The fixture runs a counter in one stopped/restarted container, then in a fresh container: **1,2,1**. Restart preserves the same container layer; recreation starts from the image again.

```json
[
  1,
  2,
  1
]
```

Use volumes or deliberate external storage for durable database state. A container ID is not a durable data identity. A stopped container still exists until removed, which explains why its writable layer can survive start/stop.

### Tags versus content identity

A tag such as python:3.12-slim is a named reference that can move as an image publisher updates it. A digest identifies registry content. The local image configuration ID and a registry manifest/index digest are different identifiers; do not expect the strings to match.

The verifier resolves the pulled tags to RepoDigests and supplies those references to the build and Compose. The Dockerfile/Compose defaults remain convenient tags, so an ordinary future manual run may select newer content. Preserve the recorded digest references when reproducing this specific run, then deliberately update/test them for maintenance. Reference: [container image concepts](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/).

---

## 16.3 Read a Dockerfile as build-time work and runtime defaults

### Exact verified Dockerfile

```dockerfile
ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE} AS wheels
WORKDIR /build
COPY requirements.lock.txt .
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheelhouse -r requirements.lock.txt
COPY . /context-audit
RUN python -c "from pathlib import Path; p=Path('/context-audit'); assert (p/'app.py').exists(); assert not (p/'.env').exists(); assert not (p/'secrets').exists(); Path('/build-only.txt').write_text('builder artifact')"

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app && chown app:app /app
COPY --from=wheels /wheelhouse /wheelhouse
COPY requirements.lock.txt .
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheelhouse -r requirements.lock.txt && rm -rf /wheelhouse
COPY --chown=app:app app.py healthcheck.py ./
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=1s --timeout=3s --start-period=5s --retries=3 CMD ["python", "healthcheck.py"]
CMD ["python", "app.py"]
```

### Instructions and responsibilities

| Instruction | Meaning in this example |
| --- | --- |
| ARG | Select the build's base reference; not automatically a runtime environment value |
| FROM | Begin a stage from the selected image |
| WORKDIR | Set the working directory for later instructions/default execution |
| COPY | Add selected context/stage files |
| RUN | Execute during image build; it is not the container's long-running service |
| ENV | Set default image environment values, overrideable at runtime |
| USER | Set the default runtime user |
| EXPOSE | Describe the expected container port; does not publish a host port |
| HEALTHCHECK | Define a health probe for running containers |
| CMD | Default executable/arguments when creating a container |

This Dockerfile builds wheels in one stage and copies the wheel artifacts into the runtime stage. It does not copy the entire builder filesystem. The runtime image omits /build-only.txt and /context-audit, verified by actually creating a container and inspecting its filesystem.

The temporary wheelhouse is removed from the final visible filesystem after installation. Because it was copied in an earlier layer, deleting it later does not prove its bytes disappeared from all image layers. Do not use copy-then-delete as a secret-removal strategy. Multi-stage selection and build secret mounts solve different problems.

Reference: [Dockerfile instruction reference](https://docs.docker.com/reference/dockerfile/), [multi-stage builds](https://docs.docker.com/build/building/multi-stage/).

### Exact dependency snapshot

```text
psycopg==3.3.4
psycopg-binary==3.3.4
psycopg-pool==3.3.1
typing_extensions==4.16.0
```

These are package-version pins, without distribution hashes. A build still relies on the selected package repository/artifacts. The recorded build installed Linux wheels for the image's interpreter; the host's Windows venv/wheels were not copied into the image.

### Exec form, shell form, CMD and ENTRYPOINT

Exec form supplies an argument array without inserting a shell for expansion. Shell form invokes a shell and introduces shell quoting/process behavior. A foreground Python command is the workload here.

CMD supplies defaults. ENTRYPOINT selects the executable behavior, with CMD commonly supplying default arguments. Providing a command after docker run overrides CMD; with an exec-form ENTRYPOINT it normally supplies replacement arguments to that entrypoint. Read the actual image configuration before guessing which process will run.

The fixture overrides this image's CMD for one-shot Python probes. ENTRYPOINT composition is documented teaching material, not a second entrypoint-image experiment.

---

## 16.4 Build context, ignore rules and cache reuse

The build context is the set of files available to the builder. Dockerfile location and context are separate arguments. COPY resolves allowed sources from that context, not any arbitrary host directory. A build from the repository root can accidentally make resumes, environments or unrelated projects available unless the context/ignore rules are deliberate.

This example's context is only examples/resume-skills/module-16-docker/. It never uses the repository root as the context. Reference: [build context](https://docs.docker.com/build/concepts/context/).

### Exact .dockerignore

```text
.git
.venv
.env
secrets
.run-*
__pycache__
*-results.json
*-output.txt
*-validation.json
validation-summary.json
README.md
*.tmp.py
```

.dockerignore controls files sent/available in that build context. .gitignore controls Git tracking. One does not substitute for the other. Explicit final-stage COPY also narrows what enters the runtime filesystem, but it is not permission to send real secrets into a build context.

The builder's context audit checks that app.py is present while the existing secrets directory is absent. The source password is a **public teaching fixture**, not a user's credential. It is mounted at runtime. No private secret is fetched for this lesson.

### Why copy dependency definitions first?

The dependency snapshot is copied before application/context files. Repeated builds can reuse dependency work when that input and prior cache state remain compatible. A later application source change should not inherently force dependency installation to rerun.

The verifier builds twice without changing inputs and records real CACHED output from BuildKit. That establishes cache reuse in this run, not a guaranteed rebuild duration or a production speedup. Cache invalidation depends on instructions, inputs and the builder's rules; “RUN always reruns” and “everything after an unchanged line is always cached” are both poor explanations. Reference: [cache invalidation](https://docs.docker.com/build/cache/invalidation/).

### Build-time secrets

ARG/ENV are not general secret-storage mechanisms. Real build credentials should use appropriate BuildKit secret/SSH mounts and avoid leaving values in outputs/layers/logs. Runtime secrets have a different lifecycle. This module uses neither private registry credentials nor a real BuildKit secret mount. Reference: [build secrets](https://docs.docker.com/build/building/secrets/).

---

## 16.5 Compose: connect an API to a database

A Dockerfile describes an image build. Compose describes related services, their runtime configuration, storage, networks and dependencies. A Compose project provides a naming/ownership scope; the verifier uses a unique project rather than reusing an existing application.

### Exact compose.yaml

```yaml
services:
  db:
    image: ${POSTGRES_IMAGE:-postgres:18-alpine}
    environment:
      POSTGRES_USER: fixture_owner
      POSTGRES_DB: placement
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - pgdata:/var/lib/postgresql
      - ./bootstrap.sql:/docker-entrypoint-initdb.d/bootstrap.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fixture_owner -d placement"]
      interval: 1s
      timeout: 3s
      retries: 30
    networks: [appnet]
  api:
    image: ${API_IMAGE:?Set API_IMAGE to your lesson image tag}
    build:
      context: .
      args:
        PYTHON_IMAGE: ${PYTHON_IMAGE:-python:3.12-slim}
    environment:
      DB_HOST: db
      DB_NAME: placement
      DB_USER: fixture_app
      DB_PASSWORD_FILE: /run/secrets/db_password
      APP_MESSAGE: ${APP_MESSAGE:-docker-lesson}
    secrets:
      - db_password
    ports:
      - target: 8080
        published: "0"
        host_ip: 127.0.0.1
        protocol: tcp
    depends_on:
      db:
        condition: service_healthy
    init: true
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 256m
    cpus: 0.5
    pids_limit: 64
    stop_grace_period: 10s
    networks: [appnet]
volumes:
  pgdata:
networks:
  appnet:
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

The API and DB share appnet. The API uses DB_HOST=db and port 5432 inside that network. Only the API publishes a host port, bound to 127.0.0.1 and allocated dynamically. The database has no published host port.

The API image runs as UID/GID 10001, with a read-only root filesystem, writable /tmp tmpfs, dropped capabilities, no-new-privileges, an init process and explicit resource limits. These are concrete runtime choices, not properties every container receives automatically.

### Runtime configuration and secrets

APP_MESSAGE is injected at runtime; the same image reports runtime-configuration in the verified request. Changing this value need not require a new image. Changing application files does require a build/redeployment unless a deliberate development bind mount supplies them.

Compose interpolation and container environment are different stages. The host's API_IMAGE/PYTHON_IMAGE variables select image references/configuration; environment entries specify what the container receives. A host .env file used for Compose interpolation is not automatically copied into the container.

The password fixture is mounted at /run/secrets/db_password. The API reads it through DB_PASSWORD_FILE, and the PostgreSQL image accepts POSTGRES_PASSWORD_FILE. A read-only file mount avoids putting that value in the API image environment, but a local Compose file source is still a host file with its own access controls; it is not a fully managed encrypted secret vault. Reference: [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/).

The value m16-public-fixture is intentionally public lesson data. bootstrap.sql uses that same value to initialize a less privileged application role. This literal initialization is not a production credential-generation/rotation workflow.

### Exact database initialization: bootstrap.sql

```sql
CREATE ROLE fixture_app LOGIN PASSWORD 'm16-public-fixture' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE SCHEMA lesson;
CREATE TABLE lesson.items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_key text NOT NULL UNIQUE,
    value text NOT NULL CHECK (length(value) BETWEEN 1 AND 80)
);
GRANT USAGE ON SCHEMA lesson TO fixture_app;
GRANT SELECT, INSERT ON lesson.items TO fixture_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA lesson TO fixture_app;
```

The application role receives only the illustrated data capabilities in lesson. The run checks its superuser/database-creation/role-creation flags are false. It does not claim a full negative SQL privilege test suite; M13 covers additional real permission/constraint failures.

The PostgreSQL 18 official image uses version-specific PGDATA beneath /var/lib/postgresql, so this Compose file mounts the named volume at that parent. Do not copy an older image's storage-path recipe without checking the selected version.

Initialization scripts run when the image initializes an empty data directory. Recreating a container over existing initialized storage does not rerun them as a migration system. Editing bootstrap.sql is not an automatic upgrade of a previously created database. Reference: [official PostgreSQL image behavior](https://github.com/docker-library/docs/blob/master/postgres/README.md).

### Startup ordering is not continuous recovery

depends_on with service_healthy waits for the dependency's declared health condition during startup. A plain started dependency is not proof it can accept useful application queries. The DB probe uses pg_isready; the API readiness probe performs an actual SELECT.

When the DB stops later, Compose's startup ordering does not magically repair the API's open connections. The application/pool must detect failures and reconnect. The verifier stops and starts the DB, observes failure, then sees the same API container recover. Reference: [Compose startup/shutdown ordering](https://docs.docker.com/compose/how-tos/startup-order/).

---

## 16.6 Networking: three different addresses to explain

```text
Windows browser/verifier
  -> 127.0.0.1:<allocated host port>
  -> published mapping
  -> API container interface :8080
       -> db:5432 on appnet
       -> PostgreSQL container :5432

inside API: 127.0.0.1 is the API container's own loopback
inside DB:  127.0.0.1 is the DB container's own loopback
```

Service-to-service traffic uses the container service port, not the host-published API port. The fixture resolves db through service DNS and successfully queries PostgreSQL, while connecting to 127.0.0.1:5432 inside the API fails. There is no PostgreSQL process listening on that API loopback.

Use service names rather than fixed container IPs. Addresses can change after recreation; the name remains the intended discovery boundary and the application needs reconnection handling. Reference: [Compose networking](https://docs.docker.com/compose/how-tos/networking/).

### EXPOSE does not publish

EXPOSE 8080 describes an image's expected port. A created probe container using this image has no host port binding until publishing is configured. The actual API publishes through Compose ports. A Dockerfile line alone does not configure the application to listen either.

Host binding and application binding are separate. Binding the published host port to 127.0.0.1 limits that host path. The application still listens on 0.0.0.0 **inside its container** so forwarded traffic can reach it through the container interface.

A separate test binds its HTTP server only to container 127.0.0.1. Requests inside that container work; the published host path fails. “Use localhost for safety” without specifying which namespace can therefore break connectivity. Reference: [publishing and mapping ports](https://docs.docker.com/engine/network/port-publishing/).

No host port is published for PostgreSQL here. This observation does not replace a full host/VM firewall or network-isolation assessment. TLS ingress, public routing, reverse proxies and cloud security groups are later deployment work.

---

## 16.7 Storage: writable layer, bind mount, volume and tmpfs

| Storage | Ownership/lifetime | Suitable use here |
| --- | --- | --- |
| Container writable layer | Belongs to one container; survives stop/start, not recreation as a new container | Disposable process state |
| Bind mount | A specified path on the daemon host, shared into the container | Development source/configuration or explicit host files |
| Named volume | Engine-managed storage with a separate lifecycle | PostgreSQL data across container recreation |
| tmpfs | Memory-backed temporary mount with runtime lifetime | API /tmp scratch data |

The counter fixture observes 1 then 2 in the same container, and 1 in a fresh one. This is real filesystem behavior, not a claim that every container directory is persistent or that image files changed.

### Bind mounts share and can obscure files

A bind-mounted generated host file reads host-one, then host-two after the host file changes. A container write to that read-only mount fails with the observed read-only-filesystem error. A directory mounted over /app hides the image's app.py even though it remains part of the underlying image.

On Docker Desktop, host-path sharing passes through the Linux environment. With a remote daemon, a bind source belongs to that daemon's host, not magically to the client laptop. Reference: [bind mounts](https://docs.docker.com/engine/storage/bind-mounts/).

A bind mount can also expose writable host data if configured that way. Prefer narrowly scoped paths/permissions. The verifier mounts only generated lesson fixtures and the explicit public initialization/secret files, never the repository root or user documents.

### Volumes outlive ordinary container recreation

The API commits a record, Compose down removes the containers/network while preserving the named volume, then Compose up creates new containers. The new database container returns that same record from the retained storage.

```json
{
  "database_container_recreated": true,
  "records_after_recreation": 1,
  "volume_retained_by_down": true
}
```

The final cleanup uses down --volumes **only for this uniquely owned disposable fixture** after checking project ownership. That deliberately discards the fixture data. An ordinary down and down --volumes have different data consequences.

A volume is not a backup, replica or major-version migration strategy. The test recreates containers over the same data/version; it does not test host failure, disk corruption, disaster recovery or a PostgreSQL major upgrade. Reference: [volumes](https://docs.docker.com/engine/storage/volumes/).

---

## 16.8 Process lifecycle: why containers exit and how they stop

A container's lifecycle follows its main process, not whether an arbitrary background job once started. The fixture's foreground one-shot prints job finished and stops with exit code 0. A deliberately failing process stops with code 7. A shell that backgrounds sleep and exits does not leave the container alive indefinitely.

Keep the intended workload in the foreground. Adding tail -f merely to conceal a failing service creates a misleading running container instead of fixing the failure. Inspect the actual command, exit status and logs.

### PID 1, init and signals

Exec-form CMD avoids an extra command shell in this image. Compose init:true adds a small init process, so the Python application is not itself PID 1 in that configuration. Signal forwarding and child reaping responsibilities must be understood at the actual process tree, not guessed from Dockerfile spelling alone.

The application installs SIGTERM/SIGINT handlers. Its main thread waits on an event while the HTTP serving thread runs. On shutdown it stops accepting, closes the server, waits for owned request threads, closes the pool and logs shutdown_complete. The test observes that event and exit code 0 after docker stop.

Docker stop gives the container its configured stop signal and a grace period before forced termination if it does not exit. That is not proof every application handles the signal correctly. Reference: [container run/lifecycle configuration](https://docs.docker.com/engine/containers/run/).

### Exact demonstration API: app.py

```python
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from threading import Event,Thread
import json,os,signal,socket
import psycopg
from psycopg_pool import ConnectionPool,PoolTimeout
from psycopg.conninfo import make_conninfo

def start():
    password=Path(os.environ['DB_PASSWORD_FILE']).read_text().strip()
    info=make_conninfo(host=os.environ['DB_HOST'],dbname=os.environ['DB_NAME'],user=os.environ['DB_USER'],
        password=password,port=5432,connect_timeout=1,options='-c statement_timeout=1500',application_name='m16-api')
    pool=ConnectionPool(info,min_size=1,max_size=2,timeout=0.5,max_waiting=4,kwargs={'autocommit':True},open=False)
    pool.open();pool.wait(timeout=10)
    stopped=Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,format,*args):pass
        def send_json(self,status,data):
            body=json.dumps(data).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):
            if self.path=='/live':return self.send_json(200,{'status':'live'})
            if self.path=='/':return self.send_json(200,{'service':'module-16','message':os.getenv('APP_MESSAGE','docker-lesson'),'hostname':socket.gethostname(),'uid':os.getuid()})
            try:
                with pool.connection() as conn:
                    if self.path=='/ready':
                        conn.execute('SELECT 1').fetchone();return self.send_json(200,{'status':'ready'})
                    if self.path=='/items':
                        rows=conn.execute('SELECT id,value FROM lesson.items ORDER BY id').fetchall()
                        return self.send_json(200,{'items':[{'id':row[0],'value':row[1]} for row in rows]})
            except (psycopg.Error,PoolTimeout):return self.send_json(503,{'error':'database_unavailable'})
            return self.send_json(404,{'error':'not_found'})
        def do_POST(self):
            if self.path!='/items':return self.send_json(404,{'error':'not_found'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 1<=length<=2048:raise ValueError('body size')
                payload=json.loads(self.rfile.read(length))
                if type(payload) is not dict:raise ValueError('object required')
                key,value=payload.get('request_key'),payload.get('value')
                if type(key) is not str or type(value) is not str or not 1<=len(key)<=80 or not 1<=len(value)<=80:
                    raise ValueError('invalid strings')
            except (ValueError,UnicodeError):return self.send_json(400,{'error':'invalid_input'})
            try:
                with pool.connection() as conn:
                    with conn.transaction():
                        row=conn.execute('INSERT INTO lesson.items(request_key,value) VALUES(%s,%s) ON CONFLICT(request_key) DO NOTHING RETURNING id,value',(key,value)).fetchone()
                        replayed=row is None
                        if replayed:
                            row=conn.execute('SELECT id,value FROM lesson.items WHERE request_key=%s',(key,)).fetchone()
                            if row[1]!=value:return self.send_json(409,{'error':'idempotency_conflict'})
                    return self.send_json(200 if replayed else 201,{'id':row[0],'value':row[1],'replayed':replayed})
            except (psycopg.Error,PoolTimeout):return self.send_json(503,{'error':'database_unavailable'})
    server=ThreadingHTTPServer(('0.0.0.0',8080),Handler)
    server.daemon_threads=False  # server_close waits for owned request threads.
    server.block_on_close=True
    for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,lambda *_:stopped.set())
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    print(json.dumps({'event':'started','uid':os.getuid()}),flush=True)
    try:stopped.wait()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);pool.close()
        print(json.dumps({'event':'shutdown_complete'}),flush=True)

if __name__=='__main__':start()
```

This deliberately small standard-library HTTP server connects Docker configuration to actual database work. It is not a production web-server or ingress template. It has no user authentication/TLS and no full malicious/slow-client ingress test; port publication is local for the fixture.

The write path binds SQL values and commits before returning successful creation. Same-key replay returns the original result, while changed payload returns a controlled conflict. Those HTTP/data checks ensure the deployment serves meaningful application behavior rather than a hard-coded hello response.

```json
{
  "created_status": 201,
  "replay_status": 200,
  "payload_conflict_status": 409,
  "value": "durable fixture"
}
```

Normal fixture requests drain during the tested stop. Long-running/stalled client handling, complete request deadlines, coordinated readiness withdrawal and production connection draining need additional design/testing. Do not convert this one shutdown trace into a universal graceful-shutdown guarantee.

### Health and restart are separate states

The API can be running while unhealthy. Its /live endpoint reports process responsiveness; /ready tests database usefulness. During DB outage, liveness still returns 200 while readiness returns 503. The container eventually becomes unhealthy and remains running, with no restart observed in this configured setup.

The health probe records health; a restart policy/orchestrator reacts according to its own rules. Do not say HEALTHCHECK automatically restarts a broken container. Reference: [restart policies](https://docs.docker.com/engine/containers/start-containers-automatically/).

### Exact healthcheck.py

```python
from urllib.request import urlopen

with urlopen('http://127.0.0.1:8080/ready',timeout=2) as response:
    if response.status!=200:raise SystemExit(1)
```

The probe is an actual HTTP request inside the container. It is not proof that public ingress/TLS, every business dependency or all data paths work. Choose liveness/readiness checks that avoid causing recovery loops or treating normal temporary dependency loss as an instruction to destroy healthy processes.

---

## 16.9 Runtime users, permissions and resource controls

The runtime image's default user is 10001:10001, and the served request reports UID 10001. The API's root filesystem is configured read-only; an attempted /app write is actually denied. The declared /tmp tmpfs accepts intended temporary writes.

The kernel reports zero effective capabilities and no-new-privileges for the inspected API process. The engine records explicit memory, CPU and PID settings:

```json
{
  "memory_bytes": 268435456,
  "nano_cpus": 500000000,
  "pids": 64
}
```

These are verified settings and selected behavior, not an induced OOM, performance benchmark or guarantee against every exhaustion attack. Resource limits can make an overloaded process fail or throttle; the application still needs bounded requests, database pools and work queues.

A non-root user inside a container is a useful layer, not the same as running a rootless Docker daemon. Host mount permissions, user namespaces, capabilities and daemon access remain separate questions. Avoid privileged mode or broad host/socket mounts without a concrete reason. References: [engine security](https://docs.docker.com/engine/security/), [resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).

Logs should go to a managed collection path such as stdout/stderr with appropriate redaction/rotation. This fixture records startup/shutdown events and database diagnostics; it does not send raw request bodies or passwords into application logs. Container log presence is not centralized observability by itself.

---

## 16.10 Architectural understanding: package an API and database deployment

Requirements: distribute the API runtime, configure it separately from the image, connect it to a database, retain database state across API/container changes and diagnose/recover selected failures.

```text
build inputs -> Dockerfile/build stages -> application image -> registry/release identity
                                                  |
runtime configuration/secrets --------------------+
                                                  v
client -> host published port -> API container -> db service name -> DB container
                                   |                                 |
                             logs/health                         named volume
                                   |
                          stop/recreate/reconnect policy
```

### Build path

**Step 1: separate code, configuration and state.** Put application/runtime dependencies in the image. Inject deployment-specific configuration at runtime. Mount/provide secrets through the chosen secret system. Keep durable database data out of the API's writable layer.

**Step 2: choose base/runtime requirements.** Select compatible platform/runtime versions, record or pin content identity and define a maintenance/update policy. Package pins without hashes and a moving tag are not a complete supply-chain guarantee.

**Step 3: make build context deliberate.** Build from the application directory, exclude unnecessary private/generated files and copy dependency definitions before frequently changing source. Use stages to select required runtime artifacts; do not copy an entire development environment by accident.

**Step 4: run the intended foreground process.** Choose exec/shell/entrypoint behavior consciously. Handle stop signals and child processes at the actual process tree. A successful build says nothing about whether the runtime command keeps the correct service alive.

**Step 5: wire service networking.** Use service discovery and container ports between services. Publish only required host paths. Distinguish host loopback, container loopback and container interface binding.

**Step 6: make readiness and data lifecycle explicit.** Wait for the initial dependency condition, then handle later failures/reconnections. Preserve named data across normal recreation; treat volume deletion and major database upgrades as separate deliberate operations.

**Step 7: verify meaningful work.** Create/read/replay actual records, stop the dependency, observe readiness and recover. Recreate containers over retained data. Check logs, role/user/permission boundaries and cleanup instead of relying on “container is Up.”

**Step 8: plan deployment beyond one machine.** Add appropriate production HTTP serving, authenticated/TLS ingress, migrations, backups/restoration, rollout/rollback, secret rotation and metrics/alerts. Compose development success does not prove multi-host availability, scaling or cloud networking. Those are subsequent modules/design extensions.

### Reproduce manually, with a separate lesson project

From examples/resume-skills/module-16-docker/, with Docker's Linux engine running:

```powershell
$env:API_IMAGE='placement-m16:manual'
docker compose --project-name m16-manual config
docker compose --project-name m16-manual build
docker compose --project-name m16-manual up --detach --wait
$apiAddress=(docker compose --project-name m16-manual port api 8080).Trim()
Invoke-RestMethod -Uri ('http://'+$apiAddress+'/ready')
docker compose --project-name m16-manual logs api
docker compose --project-name m16-manual down
```

This manual recipe uses its own fixed lesson project and default base tags unless you set the recorded digest variables. The automated run used unique names/digests and generated host ports; no concrete port/ID from another run is promised.

Ordinary down keeps that manual project's database volume. For a disposable lesson project whose data you intend to discard, down --volumes removes its project-managed volumes too. Do not replace scoped cleanup with docker system prune or a command that removes every host container.

### Diagnose by boundary

| Symptom | First useful checks |
| --- | --- |
| Docker CLI works but run/build cannot connect | Engine availability, selected context and endpoint |
| Build cannot find a file | Context root, Dockerfile path, COPY source and ignore rules |
| Build succeeds but container exits | Effective command, logs, exit status and runtime configuration |
| Published port gives connection failure | Host mapping, application port and container bind address |
| API cannot reach DB at localhost | Service DNS/network and container port; localhost namespace |
| API is running but not useful | Readiness, dependency failures, pool/reconnect behavior |
| New container lost local files | Writable layer versus named storage/mount lifecycle |
| Image files seem missing | Mount obscuring the path, wrong image/command or workdir |
| “Permission denied” after non-root change | Ownership/mode of copied files and mounted storage |
| Shutdown forced or hangs | Signal/process tree, active request draining and grace budget |

Useful read-only tools include ps -a, inspect, logs, compose config and scoped exec probes. stats can show runtime resource usage but is not a controlled load benchmark. Avoid printing secret values merely to prove they exist.

---

## 16.11 Connect this module to a resume discussion

For a Docker claim, explain what your image contains, the main process it runs and how runtime configuration reaches it. Name the actual build context, dependency/cache boundary and image version strategy.

For a deployed backend, trace host ingress to the application and from the application to its datastore. Explain which files survive stop/start versus recreation and what a healthcheck means. An interviewer can assess the mechanism even if your project did not need a large orchestration platform.

Use this fixture's real behaviors as practice, not invented production traffic or a claim that your own resume project used every shown setting. Image size, cold-start time, OOM recovery, cloud deployment and multi-node failover were not benchmarked/tested here.

### Common wrong answers

| Claim | Correction |
| --- | --- |
| “A container is a small VM.” | It normally shares the engine environment's kernel and isolates a process boundary. |
| “A Linux container on Windows shares the Windows kernel.” | This run uses a WSL2 Linux engine/kernel. |
| “The image changes when I edit a file in its container.” | Container writable state is separate from immutable image content. |
| “Every Dockerfile line creates one filesystem layer.” | Metadata/configuration and filesystem-changing operations differ. |
| “EXPOSE publishes a port.” | Publishing is runtime network configuration; the process must also listen correctly. |
| “localhost is the database because both use Docker.” | Each container has its own relevant loopback boundary. |
| “Restart and recreate have the same storage behavior.” | Same-container writable state differs from a new container and from external volumes. |
| “Deleting a secret in a later layer removes it from image history.” | Earlier-layer content may remain; keep real secrets out of those layers. |
| “depends_on solves every database failure.” | Startup conditions do not replace application recovery after startup. |
| “unhealthy automatically means restarted.” | Health and restart/orchestrator policy are separate. |
| “A named volume is a backup.” | Persistent local storage does not establish a tested recovery copy. |
| “Compose up is production HA.” | It does not prove a multi-host availability or rollout design. |

### Must remember

1. Distinguish client, engine, image, container, registry, Dockerfile and Compose.
2. Specify the engine OS/kernel layer when comparing containers with VMs.
3. Image files/configuration and runtime writable/mounted state have different lifetimes.
4. Build context and ignore rules decide what the builder can access.
5. Keep reproducibility/maintenance claims scoped to actual pins, digests and artifacts.
6. Build stages select runtime artifacts; layer deletion is not secret erasure.
7. Main-process/entrypoint/signal behavior determines lifecycle.
8. Service DNS/container ports differ from host published ports and localhost.
9. Preserve durable state deliberately and treat destructive cleanup separately.
10. Startup health, ongoing readiness and restart policy are different mechanisms.
11. Non-root, mount permissions, capabilities, resource limits and daemon privilege are separate layers.
12. Verify application behavior and failure recovery, then state the limits of that evidence.

---

## 16.12 Interview questions and follow-ups

These are curated fundamentals and diagnosis questions, not measured company-frequency rankings. Give a short answer, then use a concrete command/process/network/storage trace.

**Q1. What is Docker?**

A tool/platform for building/distributing images and running containers through an engine. The CLI is a client; the engine manages runtime objects. It standardizes application files/runtime but does not replace deployment networking, data, security or recovery design.

*Follow-up:* Why can docker version show a client while run cannot connect?

**Q2. Image versus container?**

An image is immutable content/default configuration. A container is a runtime instance with process and configured writable/mounted state. You can create several containers from the same image without sharing every writable file automatically.

*Follow-up:* Why did the counter produce 1,2,1?

**Q3. Container versus VM?**

A VM supplies a guest OS/kernel. Linux containers normally share the engine host's Linux kernel while isolating selected resource views. Docker Desktop may itself use a Linux VM/WSL environment, so identify which host layer you mean.

*Follow-up:* Which kernel did this Windows-machine fixture observe?

**Q4. What are namespaces and cgroups?**

Namespaces isolate views of selected system resources; cgroups account for/control resource use. They are different mechanisms and not proof of a perfect security boundary. Capabilities, mounts and daemon access add other concerns.

*Follow-up:* Which settings were inspected versus stress-tested here?

**Q5. What is a Dockerfile?**

An ordered image-build description with build operations and default runtime metadata. RUN executes during build; CMD selects default runtime execution. A successful build does not prove runtime configuration, networking or dependency readiness.

*Follow-up:* Where does Compose fit?

**Q6. What are image layers?**

Filesystem changes that can be composed/reused beneath a container's writable state. Some instructions change metadata rather than adding a filesystem layer. Removing a file in a later layer does not prove earlier content is erased.

*Follow-up:* Why is copy-then-delete wrong for real secrets?

**Q7. What is the build context?**

The files available to the builder, supplied as a build input. COPY refers to that allowed context, which is separate from choosing a Dockerfile path. A broad repository context can expose unrelated/private files unnecessarily.

*Follow-up:* Why build from the module directory here?

**Q8. .dockerignore versus .gitignore?**

.dockerignore filters build-context availability; .gitignore filters Git tracking. They address separate boundaries. Final-stage explicit COPY further narrows runtime files but does not justify sending real secrets into the build in the first place.

*Follow-up:* What did the builder's context audit actually check?

**Q9. How does build caching help?**

Compatible unchanged inputs/instructions can reuse prior work. Copying dependency definitions before frequently changed source can retain dependency work. The repeated fixture build reported CACHED, without establishing a universal rebuild time.

*Follow-up:* Which input change should invalidate a dependency-install step?

**Q10. Why use multi-stage builds?**

To perform build work in one stage and select only required artifacts into a runtime stage. Builder tools/source need not all enter runtime. It is not an automatic guarantee of minimal size or absence of every sensitive artifact.

*Follow-up:* Which builder paths were absent from this runtime filesystem?

**Q11. CMD versus ENTRYPOINT?**

CMD supplies default execution/arguments. ENTRYPOINT defines executable behavior, commonly with CMD defaults appended. Runtime command arguments interact differently depending on the image's configuration and exec/shell form; inspect the actual defaults.

*Follow-up:* Why could the verifier run Python probes with this image?

**Q12. Why prefer exec form for a service command?**

It avoids inserting an extra shell and makes argument/process behavior more explicit. Signal forwarding still depends on the actual process tree; with init:true an init process is PID 1 and the application is its child.

*Follow-up:* Does exec form alone implement graceful shutdown?

**Q13. Why did my container exit immediately?**

Its main process finished or failed, or its command/configuration could not run. Inspect exit status, logs and effective command. Starting a background child then exiting the main shell does not make a durable foreground container workload.

*Follow-up:* What does exit code zero mean for a one-shot job?

**Q14. Stop versus remove versus recreate?**

Stop ends running execution while retaining that container. Remove discards the container and its writable layer. Recreate starts a new instance from image/runtime configuration, with separately mounted volumes retaining data according to their own lifecycle.

*Follow-up:* Which operation preserved the counter and which preserved database data?

**Q15. How does Docker stop an application?**

It sends the configured stop signal and allows a grace period before forced termination if needed. The application/process tree must handle it and release/drain resources. The fixture observed its shutdown log and exit zero for normal requests.

*Follow-up:* What changes with stalled or long-running requests?

**Q16. Does EXPOSE make an API reachable?**

No. It describes expected container ports. The process must listen on the right address/port, and a host path needs publishing or another deliberate network route. A created expose-only probe has no host binding.

*Follow-up:* What does published host 127.0.0.1 change?

**Q17. Why can't the API reach PostgreSQL at localhost?**

Inside the API, localhost refers to the API's own loopback. A separate Compose database is reached by its service DNS name and container port on the shared network. Host-published ports serve a different path.

*Follow-up:* Which address does the browser use versus the API's DB client?

**Q18. Why bind the application to 0.0.0.0 in a container?**

So it accepts traffic arriving through its container interface, including published-port forwarding. A loopback-only container listener can work internally yet fail through the host mapping. Host exposure remains controlled by the publishing configuration.

*Follow-up:* Why is that not equivalent to publishing on every host interface?

**Q19. Bind mount versus named volume?**

A bind mount selects a specific daemon-host path and shares/obscures it at the target. A named volume is engine-managed storage with a separate lifecycle. Use explicit ownership/permissions and understand which host provides the path.

*Follow-up:* Why did mounting an empty directory over /app hide app.py?

**Q20. Does a volume survive Compose down?**

An ordinary down normally preserves this project-managed named volume; the fixture verifies data after container recreation. down --volumes deliberately removes relevant managed volume data. Persistent storage is still not a tested backup.

*Follow-up:* What would a major PostgreSQL image upgrade require beyond recreation?

**Q21. ARG versus ENV?**

ARG is a build-time parameter with defined scope; ENV supplies image/runtime environment defaults. Runtime configuration can override defaults without changing image content. Neither is a general safe secret-storage mechanism.

*Follow-up:* Which values selected bases versus configured the running API?

**Q22. How should secrets reach a container?**

Through a deliberate runtime secret/configuration mechanism with appropriate access controls; build credentials use separate build-secret mechanisms. The fixture mounts a public password file read-only. Local Compose file-backed secrets are not automatically a managed encrypted vault.

*Follow-up:* What is still private if a secret is kept out of the image?

**Q23. Does non-root inside a container mean rootless Docker?**

No. Application UID and daemon/runtime privilege are different layers. Mount ownership, capabilities, user namespaces and daemon access still matter. This fixture verifies UID 10001 plus selected capability/filesystem settings.

*Follow-up:* Why might a mounted directory still produce permission errors?

**Q24. What do memory/CPU/PID limits guarantee?**

They configure resource controls; they do not guarantee acceptable latency or prevent every application overload. The engine records the fixture's limits, but no OOM or throughput benchmark was induced. The app still needs bounded work and pool/request policy.

*Follow-up:* Which workload would you measure before tuning those values?

**Q25. Liveness versus readiness?**

Liveness describes selected process responsiveness; readiness describes suitability for useful traffic, including required dependencies. The fixture returns live 200 and ready 503 during DB outage. Choose probes so they support the intended recovery policy.

*Follow-up:* Why might killing a live process for every dependency hiccup worsen an outage?

**Q26. Does HEALTHCHECK restart unhealthy containers?**

Health reporting and restart/orchestrator policy are separate. The configured API becomes unhealthy while staying running with no restart, then recovers after DB availability returns. Do not infer automatic replacement from the word unhealthy.

*Follow-up:* Where would replacement or traffic withdrawal be configured?

**Q27. What does depends_on solve?**

Configured startup dependency conditions, such as waiting for service_healthy. It does not prove every query/migration is ready or recover all later broken connections. Application reconnection remains necessary; the fixture exercises DB stop/start.

*Follow-up:* What happens when the dependency's address changes on recreation?

**Q28. Tags versus digests?**

Tags are named references that can move; digests identify registry content. The local image configuration ID is another identifier. Record/pin deliberately, then update/test intentionally; a digest plus unhashed package pins is not full hermeticity.

*Follow-up:* Why are the two registry digests recorded separately from the application image ID?

**Q29. What is Docker Compose good for?**

Describing/lifecycling related services, network/storage configuration and local application dependencies. It is useful for reproducible development/test deployment. A successful single-machine Compose run does not prove multi-host HA, safe rollout or disaster recovery.

*Follow-up:* What production responsibilities remain in this example?

**Q30. How would you debug “works locally, fails in Docker”?**

Trace build context/runtime dependencies, effective command/configuration, user/filesystem, listener/publishing, service DNS/dependency readiness and logs/exit state. Test the failing boundary directly rather than rebuilding or adding privileged mode without a reason.

*Follow-up:* Describe one actual failure this fixture reproduced and the correct explanation.

---

## 16.13 Practice tasks and checkpoints

1. **Draw the runtime layers.** Show Windows, WSL2 Linux engine, containers and shared kernel. *Checkpoint:* specify which host kernel is shared and what the image supplies.
2. **Inspect image versus instance.** Read default user/command and compare container writable state. *Checkpoint:* explain 1,2,1 without claiming the image changed.
3. **Audit build context.** Compare .dockerignore, .gitignore and final COPY. *Checkpoint:* keep unrelated repository/resume files and real secrets outside context.
4. **Explain cache/stages.** Read both build logs and list selected runtime artifacts. *Checkpoint:* identify actual CACHED evidence without inventing a performance ratio or secret-erasure guarantee.
5. **Trace networking.** Follow the host-published API path and db:5432. *Checkpoint:* explain expose-only and container-loopback-only failures.
6. **Compare storage lifetimes.** Repeat stop/start, recreation, bind masking and retained volume behavior in a disposable project. *Checkpoint:* distinguish ordinary down from deliberate volume deletion.
7. **Observe process exits.** Compare foreground one-shot, failure and backgrounded shell. *Checkpoint:* use exit/log state instead of masking failure with an unrelated keepalive process.
8. **Trace shutdown.** Read init/exec/signal handling and the shutdown_complete log. *Checkpoint:* design additional slow-request/deadline tests before claiming production draining.
9. **Break a dependency.** Stop the lesson DB and compare live/ready/health/restart state, then recover. *Checkpoint:* separate startup ordering from ongoing reconnection and traffic policy.
10. **Propose production extensions.** Specify ingress/TLS/authentication, migrations, secret rotation, backup restore, rollout and resource monitoring. *Checkpoint:* label those additions beyond the verified local fixture.

### Exit checklist

- [ ] I can distinguish client/engine/image/container/registry/Compose.
- [ ] I can explain Linux namespaces/cgroups and the Windows WSL2 layer.
- [ ] I can interpret Dockerfile build operations and runtime metadata.
- [ ] I can choose a narrow context and explain cache/multi-stage tradeoffs.
- [ ] I can separate tag/digest/package reproducibility claims.
- [ ] I can trace foreground process, init, signals and stop/remove/recreate.
- [ ] I can diagnose host versus container ports, localhost and DNS.
- [ ] I can justify writable layer, bind, volume and tmpfs choices.
- [ ] I can reason about configuration/secrets and non-root permissions.
- [ ] I can distinguish running/live/ready/healthy and restart policy.
- [ ] I can explain actual persistence/recovery/cleanup observations.
- [ ] I can state remaining deployment/security/recovery limits honestly.

These boxes track your study progress, not chapter authoring or passing automated checks.

---

## Sources and verification map

Research refreshed on **14 October 2026**. Docker's current primary documentation supports mechanism/configuration explanations; local artifacts supply the actual engine observations.

| Topic | Primary reference |
| --- | --- |
| Architecture / container / image | [Docker overview](https://docs.docker.com/get-started/docker-overview/), [containers](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/), [images](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/) |
| Windows Linux backend | [Desktop WSL2](https://docs.docker.com/desktop/features/wsl/) |
| Build instructions/stages | [Dockerfile](https://docs.docker.com/reference/dockerfile/), [multi-stage builds](https://docs.docker.com/build/building/multi-stage/) |
| Context/cache/secrets | [Build context](https://docs.docker.com/build/concepts/context/), [cache invalidation](https://docs.docker.com/build/cache/invalidation/), [build secrets](https://docs.docker.com/build/building/secrets/) |
| Networking | [Compose networking](https://docs.docker.com/compose/how-tos/networking/), [port publishing](https://docs.docker.com/engine/network/port-publishing/) |
| Storage | [Bind mounts](https://docs.docker.com/engine/storage/bind-mounts/), [volumes](https://docs.docker.com/engine/storage/volumes/) |
| Compose operations | [Startup ordering](https://docs.docker.com/compose/how-tos/startup-order/), [runtime secrets](https://docs.docker.com/compose/how-tos/use-secrets/) |
| Runtime controls | [Run containers](https://docs.docker.com/engine/containers/run/), [restart policy](https://docs.docker.com/engine/containers/start-containers-automatically/), [security](https://docs.docker.com/engine/security/), [resources](https://docs.docker.com/engine/containers/resource_constraints/) |
| PostgreSQL container behavior | [Official image README](https://github.com/docker-library/docs/blob/master/postgres/README.md) |

### Verification map

Implementation and artifacts are under examples/resume-skills/module-16-docker/.

| Group | Named checks | Actual boundary |
| --- | --- | --- |
| Build | 5 | Compose resolution, real multi-stage build, cache reuse, defaults and final filesystem |
| HTTP | 6 | Real loopback requests through published Docker port to PostgreSQL-backed API |
| Lifecycle | 5 | One-shot/failure/background exit and actual SIGTERM shutdown |
| Network | 5 | Published/unpublished ports, service DNS, separate localhost and failed loopback-only binding |
| Readiness | 3 | DB outage, live/ready/health distinction and recovery without API recreation |
| Runtime | 10 | Health, UID, role flags, mounted secret, capability/privilege/filesystem/resource/kernel evidence |
| Storage | 6 | Writable layer lifetime, bind changes/denial/masking and named-volume persistence |
| Total | **40** | Named checks; some include several assertions |

Implementation: Dockerfile, .dockerignore, compose.yaml, bootstrap.sql, app.py, healthcheck.py and requirements.lock.txt. The public secret fixture is under secrets/. Execution: verify.py. Artifacts include verification-results.json, verification-output.txt, image-build-output.txt, image-rebuild-output.txt, docker-command-output.json, compose-container-output.txt and cleanup-results.json. Engine restoration, chapter/source and site checks are recorded alongside them.

The run removes only owned/labeled resources and validates its generated scratch path before deletion. Its tested host listeners close. Base images/build cache remain available; no global prune is run. Docker Desktop is restored to its earlier stopped state after confirming no containers remain.

No public registry push, cloud deployment, TLS/login/authorization boundary, adversarial isolation, OOM/load benchmark, backup restoration, host crash or PostgreSQL major upgrade is verified. The HTTP server and public credentials are teaching fixtures. The architectural production additions remain proposed work.

---

## Next

Continue to [M17: Linux Deployment, Nginx and PM2](/docs/resume-skills/linux-deployment-nginx-pm2) for process/permission basics, reverse-proxy routing/TLS/timeouts, application lifecycle, graceful shutdown and deployment failure diagnosis.

Revisit [M0: How a Backend Works](/docs/resume-skills/how-backend-works), [M13: PostgreSQL](/docs/resume-skills/postgresql-backend) and [M15: Caching, Jobs and Ingestion](/docs/resume-skills/caching-background-jobs-data-ingestion) for the application/data/work boundaries inside a deployment. The [master roadmap](/docs/resume-skills) shows the remaining sections.

