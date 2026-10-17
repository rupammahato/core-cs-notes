# Resume Skills Placement Handbook — Part 20
# Module 18: AWS and GCP Fundamentals for This Resume

**Estimated time: 4–5 hours | Tier: 2 | Requires: M15 jobs/caching, M16 Docker, M17 deployment; CN networking/TLS and M7–M8 authentication/security**

---

## Why this module exists

Saying deployed on AWS should lead to a request path you can explain. Which machine runs the application? Which address is public? Who can connect to the database? Who is allowed to read an object? What happens when a target fails? Similarly, used Cloud Tasks should lead to a clear producer, queue, worker, identity and retry story.

This chapter covers the resume-linked AWS EC2, Elastic Load Balancing and CDN concepts, and GCP Cloud Tasks. IAM, VPC networking, object storage and managed workers are supporting bridges. CloudFront is the named AWS CDN example; it is not an assertion that your resume's unspecified CDN was CloudFront.

**Organizing principle: cloud changes who operates a component, but it does not remove its network, identity, state or failure boundaries.**

These are selected fundamentals and useful interview follow-ups, not measured company-question rankings. Architecture examples are proposed designs; they do not invent account resources, costs, availability measurements or project implementation details.

---

## 1. Cloud versus the backend on your laptop

Cloud computing supplies infrastructure and managed services through provider APIs. A virtual machine still runs processes and opens sockets; a managed queue still needs a worker with correct side effects. The useful question is which responsibilities the provider takes over and which remain with the application team.

| Concern | Laptop example | Cloud example | Application responsibility that remains |
| --- | --- | --- | --- |
| Compute | Local Node/Python process | EC2 VM or managed application runtime | Correct code, configuration and resource budgets |
| Network | Loopback/LAN and OS firewall | VPC/subnets/routes/security groups/load balancer | Intended exposure and a reachable service |
| Identity | Local user/environment | IAM role/service account and temporary credentials | Least privilege and business authorization |
| Storage | Local file/SQLite | Block storage, object store or managed database | Data model, retention, integrity and recovery requirements |
| Async work | Local durable-job example | Cloud Tasks HTTP dispatch | Idempotent effects, meaningful completion and failure handling |
| Delivery | Direct origin requests | CDN/edge cache | Safe cache keys, freshness and private-data policy |

For EC2, AWS operates the underlying infrastructure; customers retain responsibilities such as guest OS/application maintenance and configuration. The split differs for managed services. Managed does not mean the provider knows your tenant rules or whether an import was correct. [AWS shared responsibility model](https://aws.amazon.com/compliance/shared-responsibility-model/)

Revisit [M0](/docs/resume-skills/how-backend-works), [M16](/docs/resume-skills/docker-fundamentals) and [M17](/docs/resume-skills/linux-deployment-nginx-pm2): runtime, image, VM, process manager and load balancer occupy different layers.

---

## 2. Scope and evidence: what ran here

No AWS/GCP account was used, no cloud API was called, and no resources were provisioned. Neither cloud CLI was available on PATH during discovery. The practical work uses an isolated Python environment and real host-loopback HTTP servers, SQLite transactions and cryptographic token verification.

**Recorded on 14 October 2026:** CPython 3.12.10 on Windows.

| Library | Recorded version |
| --- | --- |
| google-auth | 2.62.0 |
| google-cloud-tasks | 2.26.0 |
| cryptography | 50.0.2 |
| requests | 2.34.2 |

### Reproduce the local examples

From the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-18-aws-gcp/.venv
& 'examples/resume-skills/module-18-aws-gcp/.venv/Scripts/python.exe' -m pip install -r examples/resume-skills/module-18-aws-gcp/requirements.lock.txt
& 'examples/resume-skills/module-18-aws-gcp/.venv/Scripts/python.exe' -X utf8 examples/resume-skills/module-18-aws-gcp/verify.py
```

Use a suitable Python 3.12 interpreter. Initial package installation needs registry access; the actual verification uses local fixtures. requirements.lock.txt records the complete observed dependency snapshot without package hashes. On another platform, wheel availability still matters.

The examples deliberately use example.test hostnames and a fictional project/service-account name. They construct an official SDK message without creating a client or looking up application-default credentials. Token signatures are real, but the signing key is freshly generated locally and the certificate transport returns its public key from memory. **No tested token was Google-issued.**

Three areas of evidence must stay distinct:

| Area | What establishes it |
| --- | --- |
| EC2/VPC/IAM/ALB/CloudFront behavior | Current official provider documentation and explicitly proposed designs |
| SDK payload and token validation mechanics | Installed Google libraries, offline message round trips and generated-key negative tests |
| Cache/private-data and duplicate-worker behavior | Actual requests through local HTTP servers and actual SQLite transactions |

The local cache is not CloudFront, the HTTP caller is not Cloud Tasks, and the SQLite store is not a cloud database. The tests make selected application failure boundaries concrete. Port 3000 is unused, all owned listeners close and the temporary database is removed. Docker remains unused for this module.

---

## 3. Regions, Availability Zones and failure domains

An AWS Region is a geographic area. Availability Zones are isolated locations within a Region. A design spread across zones can tolerate some location failures if traffic routing, remaining capacity and data dependencies also support that failure. A Region choice also affects latency, available services and data-location requirements. [AWS Regions and Zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)

```text
Region
  |
  +-- AZ A: application capacity and its subnet
  |
  +-- AZ B: application capacity and its subnet

Regional routing/services and shared data still need their own design.
```

Two workers on the same EC2 instance improve process-level concurrency/recovery; they remain on one host. Two instances in the same zone address some host failures; they remain exposed to that zone's failure. Two zones still do not constitute tested multi-Region disaster recovery.

Availability is a property of the complete dependency path. If both application zones use one unavailable data service, the extra web capacity may not serve useful requests. Replication, failover, backups and restore tests solve different problems. Avoid giving one architecture label credit for all of them.

GCP also organizes resources by project and location, but resource scope depends on the service. For Cloud Tasks, the queue resource path contains a project and location. Do not assume every resource in either provider is zonal or automatically replicated globally.

---

## 4. EC2: what the backend runs on

An EC2 instance is a virtual server. An AMI supplies the initial machine image; an instance type describes a compute/memory/network resource configuration. Your application still needs its runtime, configuration, files, service lifecycle and reachable listening socket. [EC2 overview](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html)

### 4.1 Image, VM, container and process

```text
AMI -> launched EC2 virtual machine
          |
          +-- OS/users/network interfaces/filesystems
          +-- Nginx / Node / PM2, if selected for this VM
          +-- or container runtime -> application container(s)
```

An AMI and a Docker image are different packaging layers. Starting a VM does not mean your application's process started correctly. Starting a container does not imply a public route exists. M16/M17 provide the executable inner layers.

### 4.2 Storage distinctions worth knowing

| Storage category | Suitable conceptual use | Question to ask |
| --- | --- | --- |
| Block volume, such as EBS | Disk attached to compute, subject to its lifecycle/configuration | Does it persist after the planned instance action, and how is it backed up? |
| Instance-local temporary storage | Scratch/cache where loss is acceptable | What happens on stop or host replacement? |
| Object store, such as S3 | Uploaded documents/assets addressed as objects | What controls object access, lifecycle, versioning and deletion? |
| Database | Queries, constraints, transactions and coordinated records | What are the availability, backup and restore guarantees? |

Persistent does not mean replicated everywhere or backed up against every failure. Object storage is a supporting bridge here; it is not a relational database or a guarantee that arbitrary code can treat remote objects like an ordinary local POSIX filesystem.

### 4.3 What deployment adds beyond launching an instance

Choose a trusted release, configure a service identity and startup, validate dependencies, expose only intended ingress, obtain certificates, bound logs and resources, and plan updates/recovery. The same chmod/cwd/environment mistakes from M17 still occur on EC2.

Cloud costs also include resources outside the application process: storage, data transfer, addresses, load balancers, NAT, logs and retained backups can contribute. Use current provider pricing for the actual Region and workload; this chapter contains no measured bill or fixed-price promise. Stopping a VM is not proof that every related charge stopped.

---

## 5. Network reachability: trace the complete path

### 5.1 VPC, subnet, route and address

A VPC defines a virtual network boundary. A subnet supplies an address range within a zone. A route table selects where destination traffic goes; a security group controls allowed traffic for associated resources. They answer different questions.

For the ordinary direct public-IPv4 EC2 path, internet access requires the intended public address mapping, an attached internet gateway and appropriate subnet routing, plus permission and a listening service. A subnet with an internet-gateway route is public; that classification does not automatically give every instance a public IPv4 address. [AWS internet gateway and public-subnet explanation](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)

```text
Client -> DNS result -> public endpoint
       -> route/gateway and address mapping
       -> security controls
       -> OS interface/firewall
       -> listening application/proxy
```

Opening a security-group port does not create a process. Starting a process does not create an internet-gateway route. A public IPv4 address does not repair missing routing. Keep IPv4 and IPv6 analysis separate; their address and egress designs differ.

### 5.2 Public ingress does not require public application/database instances

```text
Internet
   |
   v
Internet-facing ALB in the intended public subnets
   |
   v
Application targets at private addresses
   |
   v
Database at an intended private endpoint
```

The application needs a path for requests from the ALB and whatever outbound dependencies it uses. A private target does not need a public address merely because users reach it through the public load balancer. Outbound internet access may need an appropriate NAT/egress design; private service access may use provider endpoints. Those are separate from the inbound ALB path.

### 5.3 Security groups versus network ACLs

| Property | Security group | Network ACL |
| --- | --- | --- |
| Main association | Resource/network interface | Subnet |
| Rule effect | Allow rules; effective permissions aggregate across attached groups | Ordered allow/deny rules |
| Connection behavior | Stateful tracking for allowed flows | Stateless evaluation, including return path |
| Useful diagnosis | Is this intended source/protocol/port allowed? | Do both directions, including response traffic, pass subnet policy? |

Stateful does not mean unlimited access from the peer to any unrelated port. SG rules are not evaluated as IAM permissions. NACLs and OS firewall rules can still block a flow that an SG permits. [AWS security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html), [network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html)

### 5.4 A scoped rule plan for the illustrated deployment

**Illustrative configuration, not applied to AWS:**

| Destination | Intended inbound source | Port / purpose |
| --- | --- | --- |
| ALB security group | Intended client networks | HTTPS listener |
| App security group | ALB security group | Selected target and health-check port(s) |
| Database security group | App/worker security group(s) that need access | Database protocol/port |
| Administrative path | Controlled management access design | Explicitly chosen management mechanism |

An SG reference authorizes the relevant traffic from associated interfaces; it does not copy the referenced group's rules. Avoid opening the application port to the world when the requirement is ALB-only access. Review outbound permissions and the health-check path too. [AWS SG rule/reference semantics](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)

### 5.5 The localhost trap after adding an ALB

In M17, Nginx and Node share a host namespace, so Nginx can use Node's loopback socket. An ALB is elsewhere: it cannot connect to your instance's 127.0.0.1-only application.

You could expose the VM's Nginx on the intended private interface, restricted to the ALB, and retain Node on loopback. Or expose the application on a suitable private/all-interface socket with appropriately scoped controls. Which hop the target group points at must match the actual listener. A wider bind address is not itself an authorization policy.

---

## 6. IAM: who may call which API?

IAM governs access to cloud resources. Application authorization governs whether a user may access a tenant record. Network permission governs whether a connection can reach a service. Satisfying one does not automatically satisfy the other two.

### 6.1 Principal, role, action, resource and conditions

| Term | Question it answers |
| --- | --- |
| Principal | Who is making the request? |
| Role | Which assumable identity/permission context is being used? |
| Action | Which provider API operation is requested? |
| Resource | Which object, queue, bucket or other target is in scope? |
| Condition | Which additional context must match? |
| Trust policy | Who is allowed to assume the role? |
| Permissions policy | What may that identity do once used? |

For AWS, an applicable explicit deny overrides an allow. Boundaries, organization policies, resource policies and cross-account rules can affect effective access; do not reduce every IAM decision to one identity policy. The JSON below is an illustrative policy, not a complete evaluator. [AWS policy evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadImportObjectsOnly",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::placement-fixture-data/imports/*"
    }
  ]
}
```

It illustrates a narrow GetObject permission for an import prefix. It does not grant ListBucket, upload/delete access, arbitrary prefixes or KMS permissions. The example bucket is fictional. Parsing valid JSON locally cannot establish that a deployed principal can actually use it.

### 6.2 EC2 roles and temporary credentials

An EC2 instance can obtain temporary role credentials via an attached instance profile. Supported SDK credential providers can obtain and refresh them, avoiding long-lived access keys in source or baked images. A role's trust relationship and its permissions are different parts of the setup. [IAM roles for EC2 applications](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html)

Illustrative EC2 trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

This is not the object-read policy above: it expresses who may assume the role. Neither policy was uploaded, attached or evaluated by AWS in this module.

Temporary credentials still require protection. Avoid exposing metadata/credential access through SSRF or logging. A broad instance role can give multiple processes on that instance broad access; consider the identity boundary of the actual compute platform. Revisit [M8](/docs/resume-skills/api-security-authorization-multi-tenancy) for request authorization and secret handling.

### 6.3 GCP service accounts are workload identities

A service account identifies a workload; role bindings grant it particular permissions. The producer that enqueues a task and the identity that the task presents to its worker may be different. A service account's email is an identifier, not a credential that proves the caller owns it.

Prefer the platform's supported workload credentials/federation to distributing permanent private-key files. In the local tests, the fictional email is checked only after actual signature/issuer/audience/time verification against the injected fixture trust. The source never trusts the email merely because a request body or header contains it.

---

## 7. Elastic Load Balancing: listener → rule → target group → target

Elastic Load Balancing is the service family. ALB is the application-layer HTTP/HTTPS option; NLB serves transport-level connection use cases. Pick based on required protocol and routing behavior. They are not interchangeable names for a VM process. [Elastic Load Balancing overview](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html)

```text
Client HTTPS
   |
   v
ALB listener and certificate
   |
   +-- host/path rule --> target group A --> selected target
   |
   +-- another rule --> target group B --> selected target
```

A listener accepts a configured protocol/port. Rules select a routing action. A target group identifies registered backends and their protocol/port and health policy. A target can be one of the supported target types; the appropriate type must match the deployment. [ALB target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html)

### 7.1 Health is a routing observation

An HTTP health check probes a configured path/port and decides success using configured response criteria and thresholds. Choose a path that answers the readiness question you actually need. A process existing, a socket accepting, a liveness response and useful dependency readiness are different observations.

For example, a probe that requires an end-user login can return 401 even when the API is otherwise healthy. A redirecting root path or wrong virtual-host routing can also mismatch your chosen check. Diagnose the target health reason and the actual probe path. Do not solve a routing mismatch by accepting every error code as healthy.

**Important documented exception:** if the target group has only unhealthy registered targets, an ALB can route to them in fail-open mode. Health checks are therefore not a security boundary or a universal promise that unhealthy targets never receive requests. [Official ALB health-check behavior](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)

### 7.2 Deregistration and application draining

During release/scale-in, remove or deregister a target deliberately, allow the intended draining period, and coordinate application shutdown/dependency closure. Load-balancer draining and PM2 worker reload are different layers. Their deadlines and overlap capacity must agree. [ALB target-group attributes and deregistration](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html#deregistration-delay)

No live ALB health transition or drain was tested here. M17's successful local PM2 reload does not prove that an external ALB stops routing at the correct time. A staging test should record target registration/health/draining state, real requests and application lifecycle together.

### 7.3 Scaling and availability

Vertical scaling gives a machine more resources. Horizontal scaling adds instances/processes. Auto Scaling is a mechanism for changing capacity according to configured policies; it is not instantaneous capacity or proof that a database scales with the web tier.

More workers also multiply connection pools and process-local jobs. Shared sessions, cache correctness, queue pressure, database capacity and warm-up time can become the actual constraint. Spread capacity across failure domains only when routing and data dependencies support the intended recovery.

---

## 8. CDN: what is served from the edge, and under which key?

A CDN can serve suitable content from locations closer to clients. The origin remains responsible for generating/storing the authoritative content. A hit may avoid an origin request; a miss forwards work toward the origin. A CDN, load balancer and database solve different problems.

CloudFront is the concrete service example here. A distribution's behavior selects an origin and policies for requests. A cache key decides which requests may share a stored response; forwarding additional fields to the origin does not automatically mean those fields distinguish cache entries. [CloudFront cache keys](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html)

### 8.1 Cache equivalence is a correctness decision

If changing a request field can change the response, either include the relevant variant in a safe cache design or bypass shared caching for that path. Query language, content encoding, selected headers, authentication and cookies can matter. Including everything can destroy hit rate; excluding a security-relevant field can leak data.

```text
Public versioned asset -> shared cache can be useful
Authenticated /me     -> explicit private-response policy and safe forwarding
Tenant dashboard      -> authorization + deliberate caching boundary
```

For ordinary private API responses, a conservative baseline is a caching-disabled behavior plus the origin request policy needed to pass authentication. CloudFront's Authorization forwarding has specific behavior; disabling caching alone is not a substitute for checking that the origin receives the header. [CloudFront authorization/401 guidance](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/http-401-unauthorized.html)

### 8.2 TTL: origin headers and distribution policy interact

TTL bounds how long a cached response may be reused under the selected policy. The browser and CDN can have different caching lifetimes. Content invalidation is another mechanism; it does not retroactively retract every browser copy. Versioned asset names can make release changes explicit.

**CloudFront trap:** a positive minimum TTL can force caching even when the origin sends no-cache, no-store or private. For sensitive responses, inspect the actual behavior and cache policy rather than assuming a header alone overrides everything. A managed policy name is not a security review. [CloudFront cache policy TTLs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cache-key-understand-cache-policy.html), [expiration behavior](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html)

### 8.3 Executable local cache lesson

This deliberately conservative local cache allows only /public, selected query/header variants, anonymous requests and suitable successful public responses. It bypasses Authorization/Cookie requests, Set-Cookie/private/no-store/error responses and unmodeled Vary fields. It is not a generic HTTP cache or an implementation of CloudFront policy.

```python
"""Conservative local cache lesson; not a CloudFront implementation."""
import re, threading, time
from urllib.parse import parse_qsl, urlsplit

class PublicCache:
    def __init__(self,clock=time.monotonic):
        self.clock=clock
        self.entries={}
        self.lock=threading.Lock()

    def key(self,path,headers):
        parsed=urlsplit(path)
        headers={k.lower():v for k,v in headers.items()}
        if parsed.path!='/public' or 'authorization' in headers or 'cookie' in headers:return None
        query=parse_qsl(parsed.query,keep_blank_values=True)
        if any(k!='lang' for k,v in query):return None
        return parsed.path,tuple(query),headers.get('accept-language','')

    def fetch(self,path,headers,origin):
        key=self.key(path,headers)
        with self.lock:
            item=self.entries.get(key) if key is not None else None
            if item and item[0]>self.clock():return (*item[1],'HIT')
            if key is not None:self.entries.pop(key,None)
        status,response_headers,body=origin(path,headers)
        lower={k.lower():v for k,v in response_headers.items()}
        control={part.strip().lower() for part in lower.get('cache-control','').split(',')}
        ttl=next((int(part.split('=')[1]) for part in control if re.fullmatch(r'max-age=\d+',part)),0)
        vary={part.strip().lower() for part in lower.get('vary','').split(',') if part.strip()}
        eligible=(key is not None and status==200 and 'public' in control
                  and not control&{'private','no-store','no-cache'}
                  and 'set-cookie' not in lower and vary<={'accept-language'} and 0<ttl<=60)
        if eligible:
            with self.lock:self.entries[key]=(self.clock()+ttl,(status,response_headers,body))
        return status,response_headers,body,('MISS' if eligible else 'BYPASS')

    def invalidate_public(self):
        with self.lock:self.entries.clear()
```

The verifier runs a real HTTP origin and a real HTTP proxy/cache on loopback, then observes:

```json
{
  "first_state": "MISS",
  "second_state": "HIT",
  "same_origin_call": true,
  "stale_version": "v1",
  "after_expiry": "v2",
  "after_local_invalidation": "v3",
  "origin_calls": 18,
  "clock": "injected monotonic time; expiry advanced 31 seconds"
}
```

The second anonymous request reused a response without another origin call. Query and Accept-Language variants separated. Authenticated/cookie paths bypassed the shared cache. Updating the origin did not change a still-fresh cached v1 response; advancing the injected clock past its TTL fetched v2, and an explicit local invalidation fetched v3.

The injected clock makes expiry deterministic; it does not measure 31 seconds of provider edge behavior. The cache has no capacity eviction, revalidation/ETags, compressed variants, distributed invalidation, request coalescing or load claim. CloudFront's managed policies and minimum TTL are researched provider behavior, not reproduced by this local class.

---

## 9. Cloud Tasks: producer, queue, worker and acknowledgement

Cloud Tasks dispatches tasks to a configured worker endpoint. For HTTP targets, the task contains the request destination, method/body and optionally a token configuration. A producer creates the task; the service manages delivery; the worker performs the business operation.

```text
Authenticated application
  -> commit job / enqueue intent
  -> Cloud Tasks create request
  -> queue scheduling + dispatch policy
  -> HTTPS worker request with configured identity
  -> verify caller, validate job, apply idempotent effect
  -> acknowledge success after durable completion
```

Task enqueue success means the service accepted a task, not that its business operation completed. A worker's success status is an acknowledgement to the delivery system. Returning success before durable work or durable handoff can lose the operation if the process then dies. [Create HTTP target tasks](https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks)

### 9.1 Cloud Tasks versus cron, in-process background work and pub/sub

| Mechanism | Main purpose | Remaining question |
| --- | --- | --- |
| In-process background task | Work after/request-adjacent to a response in the same runtime | What persists if the process stops? |
| Cron/scheduled trigger | Initiate work according to time | Who owns durable execution, locking and retries? |
| Task queue | Deliver a work request with configured scheduling/retries/rate | Is the worker idempotent and does it acknowledge safely? |
| Publish/subscribe messaging | Decouple event publishers and interested consumers | Which consumers, subscriptions, delivery guarantees and replay rules apply? |

Cloud Tasks is not the same product as Cloud Scheduler or Pub/Sub. M15 teaches the queue/application foundation; this chapter adds the provider's HTTP/token/request boundaries.

### 9.2 Rate, concurrency, deadlines and retries

Dispatch rate limits constrain attempts over time; concurrent-dispatch limits constrain simultaneously outstanding work. Retries consume capacity too. A low concurrency limit can bound downstream pressure even if the configured rate is high; slow workers can create backlog without a CPU spike.

The HTTP attempt succeeds on a 2xx response; non-2xx or missing responses are subject to retry policy. A 400 is not automatically a permanent-error acknowledgement. System throttling can further reduce dispatch rates, particularly with overload/error responses. [HTTP target response behavior](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks#HttpRequest), [queue rate limits](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues#RateLimits)

RetryConfig includes attempts, retry duration and backoff settings. Its documented stopping rule combines maxAttempts and maxRetryDuration; do not assume the first of two independently configured limits always ends delivery. Use the current reference for zero/unlimited settings. The current Task reference and installed SDK also expose task-level retry_config; inspect applicable overrides before assuming the queue default always governs. The offline message here sets no retry override. [RetryConfig](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/RetryConfig)

An attempt deadline ends the service's wait for the worker response; it does not guarantee that the worker stops executing. Align platform request limits, application work/cancellation and retry semantics. Long work may need bounded stages or a durable handoff. No actual provider backoff timeline, task expiry or deadline cancellation was measured here.

### 9.3 Duplicate delivery and task names

Cloud Tasks documentation explicitly warns that duplicate executions occur. Workers must tolerate retries and concurrent duplication. Do not infer exactly-once business effects from a delivery service's normal behavior. [Cloud Tasks duplicate-execution guidance](https://docs.cloud.google.com/tasks/docs/common-pitfalls#duplicate_execution)

An explicit task name can help deduplicate creates, but the service retains names for a bounded period after deletion. That is not permanent business idempotency. The current create reference documents delayed name reuse and recommends distributed/hashed identifiers. Use durable application uniqueness for the operation itself. [Task create/name deduplication](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks/create)

---

## 10. Constructing an official SDK task without calling the cloud

The request below uses google-cloud-tasks message types, but it creates no CloudTasksClient, calls no API and does not discover credentials. Deployment URLs are trusted configuration. The fixture chooses HTTPS and a URL-shaped audience without a query as its own worker contract; that validation is stricter than merely accepting the provider's raw URL field.

```python
"""Construct an SDK message offline. No client, ADC lookup or enqueue call."""
import hashlib, json
from urllib.parse import urlsplit
from google.cloud import tasks_v2
from google.protobuf.duration_pb2 import Duration

PARENT='projects/placement-fixture/locations/us-central1/queues/ingestion'
TARGET='https://worker.example.test/tasks/import'
AUDIENCE='https://worker.example.test/tasks/import'
SERVICE_ACCOUNT='task-invoker@placement-fixture.iam.gserviceaccount.com'

def build_request(tenant_id, job_id, value, *, target=TARGET, audience=AUDIENCE):
    # These deployment values must come from trusted configuration, not a client URL.
    for url in (target,audience):
        parsed=urlsplit(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError('Expected a configured HTTPS URL')
    if urlsplit(audience).query:raise ValueError('This worker audience excludes query parameters')
    fields={'tenant_id':tenant_id,'job_id':job_id,'value':value}
    if not all(type(v) is str and 1<=len(v)<=80 for v in fields.values()):
        raise ValueError('Expected bounded string fields')
    identity=json.dumps([tenant_id,job_id],separators=(',',':')).encode()
    name=PARENT+'/tasks/'+hashlib.sha256(identity).hexdigest()
    body=json.dumps(fields,sort_keys=True,separators=(',',':')).encode()
    task=tasks_v2.Task(
        name=name,dispatch_deadline=Duration(seconds=30),
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,url=target,
            headers={'Content-Type':'application/json'},body=body,
            oidc_token=tasks_v2.OidcToken(service_account_email=SERVICE_ACCOUNT,audience=audience),
        ),
    )
    return tasks_v2.CreateTaskRequest(parent=PARENT,task=task)
```

The stable hashed name includes tenant and job ID. The job record must already be authorized and immutable where required; hashing an identifier is not authorization. The small value in this example makes payload conflicts visible. Larger document work should normally reference authorized durable data instead of embedding large/sensitive content in queue metadata.

Actual SDK JSON representation after a protobuf round trip:

```json
{
  "parent": "projects/placement-fixture/locations/us-central1/queues/ingestion",
  "task": {
    "name": "projects/placement-fixture/locations/us-central1/queues/ingestion/tasks/5e2a2208f9534574f27f70d8bfd5f9c92e459d5338b807c1e984ee122dc70c88",
    "httpRequest": {
      "url": "https://worker.example.test/tasks/import",
      "httpMethod": 1,
      "headers": {
        "Content-Type": "application/json"
      },
      "body": "eyJqb2JfaWQiOiJqb2ItMSIsInRlbmFudF9pZCI6InRlbmFudC1hIiwidmFsdWUiOiJoZWxsbyJ9",
      "oidcToken": {
        "serviceAccountEmail": "task-invoker@placement-fixture.iam.gserviceaccount.com",
        "audience": "https://worker.example.test/tasks/import"
      }
    },
    "dispatchDeadline": "30s",
    "dispatchCount": 0,
    "responseCount": 0,
    "view": 0
  },
  "responseView": 0
}
```

The observed enum value 1 corresponds to POST in this installed SDK. Output/default fields appear in this SDK serialization; this is not a captured server response or a hand-written REST request recommendation. The body is bytes in Python; its JSON representation is base64. The verifier decodes that representation once and recovers the original JSON object. Pre-base64-encoding the bytes before giving them to the SDK would change what the worker receives.

The message includes a 30s dispatch deadline, explicit OIDC audience and fictional service-account email. It was serialized/deserialized successfully. That establishes message-shape mechanics, not permissions, queue existence, endpoint reachability or successful Google token issuance.

---

## 11. Cloud Tasks identity: separate three permission boundaries

| Boundary | Identity / permission question |
| --- | --- |
| Application → task creation API | May this producer create tasks in this queue? |
| Task token configuration | May the creator act as the selected service account, and may the Cloud Tasks service agent generate the configured token? |
| Delivered request → worker | Does the worker accept this verified identity for this endpoint/operation? |

The OIDC service account must be in the queue's project; the caller needs iam.serviceAccounts.actAs on it. Queue-create permission alone does not imply permission to impersonate arbitrary service accounts. The Cloud Tasks service agent also needs its documented service-agent/token configuration. A managed target can add its own invoker IAM check. [OidcToken reference](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/OidcToken), [authenticated task setup](https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks#token)

For a general HTTPS worker, an OIDC ID token represents the caller to the intended audience. Google API endpoints hosted on googleapis.com generally expect an OAuth access token instead. This is workload authentication, not proof of which end user owns a tenant job.

### 11.1 What a worker verifies

1. Require the intended bearer-token form.
2. Verify the signature using trusted provider keys, with appropriate key retrieval/caching behavior.
3. Verify the accepted issuer, intended audience and time validity.
4. Authorize the verified workload identity, rather than any signed identity.
5. Look up the canonical job within its tenant/business scope and validate the allowed operation.

Decoding a JWT is not verification. A header like X-CloudTasks-TaskName can be useful metadata; by itself it cannot prove a request came from Cloud Tasks. A caller can forge a header if it can reach the endpoint. Similarly, the JWT's audience must match your worker's configured accepted value; a valid token for some other service must be rejected.

For a managed worker such as Cloud Run, distinguish platform IAM verification and application job authorization. If using a custom audience, configure both producer and target to accept it; do not assume an arbitrary route URL is the correct audience for every hosting platform.

### 11.2 The actual token tests

The application uses google.oauth2.id_token.verify_oauth2_token with an explicit audience and zero allowed skew for the fixture. It then enforces the expected verified email. The verifier injects an in-memory public-key response at the library transport boundary. Real deployment must use the provider's trusted keys/transport and a deliberate clock/key-cache policy. [Official Google-auth token verifier](https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.id_token.html)

The 14 token checks cover valid signed fixture identity, untrusted signature, tampered payload, wrong audience, wrong issuer, expiry, future issued-at, unauthorized service account, unverified email, unknown key ID, missing issued-at, missing bearer, unsigned algorithm and malformed input. Additional real HTTP checks reject forged task headers and a signed but unauthorized caller.

The test claims use a Google issuer string to exercise the library's issuer check, while the key comes from our local fixture. They are **locally issued test tokens, not genuine Google credentials**. No generated private key or bearer token is written into the result artifacts. The certificate-transport artifact records that responses came from the fixture, not Google.

---

## 12. Executable worker: acknowledge after one durable effect

The worker authenticates the caller, validates a small payload, selects an existing tenant/job record and uses a SQLite transaction for the business effect and completion state. Its composite primary key is the durable duplicate boundary. No fault can be selected from a client header/body; the verifier injects faults into local store state.

```python
"""Teaching worker: injected token verifier, real HTTP and transactional SQLite."""
import json, sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from google.auth import exceptions
from google.oauth2 import id_token

class AuthenticationError(Exception):pass
class AuthorizationError(Exception):pass

class TokenVerifier:
    def __init__(self, request, audience, service_account):
        self.request=request
        self.audience=audience
        self.service_account=service_account

    def verify(self, authorization):
        if not authorization or not authorization.startswith('Bearer '):
            raise AuthenticationError('Bearer token required')
        token=authorization[7:]
        if not token or len(token)>8192:raise AuthenticationError('Invalid token length')
        try:
            claims=id_token.verify_oauth2_token(token,self.request,audience=self.audience,clock_skew_in_seconds=0)
        except (ValueError,exceptions.GoogleAuthError) as error:
            raise AuthenticationError('Token verification failed') from error
        if claims.get('email_verified') is not True or claims.get('email')!=self.service_account:
            raise AuthorizationError('Caller service account not allowed')
        return claims

class Store:
    def __init__(self,path):
        self.path=str(path)
        self.faults={}
        with closing(self.connect()) as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS jobs(
              tenant TEXT NOT NULL,id TEXT NOT NULL,value TEXT NOT NULL,
              state TEXT NOT NULL DEFAULT 'pending',PRIMARY KEY(tenant,id));
            CREATE TABLE IF NOT EXISTS effects(
              tenant TEXT NOT NULL,id TEXT NOT NULL,value TEXT NOT NULL,
              PRIMARY KEY(tenant,id),FOREIGN KEY(tenant,id) REFERENCES jobs(tenant,id));
            ''')

    def connect(self):
        db=sqlite3.connect(self.path,timeout=5)
        db.execute('PRAGMA foreign_keys=ON')
        return db

    def seed(self,tenant,job,value):
        db=self.connect()
        try:
            with db:db.execute('INSERT INTO jobs(tenant,id,value) VALUES(?,?,?)',(tenant,job,value))
        finally:db.close()

    def apply(self,payload):
        if type(payload) is not dict or set(payload)!={'tenant_id','job_id','value'}:
            return 400,{'error':'invalid payload'}
        tenant,job,value=(payload[k] for k in ('tenant_id','job_id','value'))
        if not all(type(v) is str and 1<=len(v)<=80 for v in (tenant,job,value)):
            return 400,{'error':'invalid fields'}
        db=self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT value FROM jobs WHERE tenant=? AND id=?',(tenant,job)).fetchone()
            if row is None:return 404,{'error':'job not found'}
            if row[0]!=value:return 409,{'error':'job payload changed'}
            done=db.execute('SELECT value FROM effects WHERE tenant=? AND id=?',(tenant,job)).fetchone()
            if done:return 200,{'status':'replayed','job_id':job}
            # Faults are controlled by the verifier, never by request headers/body.
            fault=self.faults.pop((tenant,job),None)
            if fault=='before_commit':return 503,{'error':'injected pre-commit failure'}
            db.execute('INSERT INTO effects(tenant,id,value) VALUES(?,?,?)',(tenant,job,value))
            db.execute("UPDATE jobs SET state='complete' WHERE tenant=? AND id=?",(tenant,job))
            db.commit()
            if fault=='after_commit':return 503,{'error':'injected acknowledgement failure'}
            return 201,{'status':'applied','job_id':job}
        finally:
            if db.in_transaction:db.rollback()
            db.close()

    def effects(self):
        db=self.connect()
        try:return db.execute('SELECT tenant,id,value FROM effects ORDER BY tenant,id').fetchall()
        finally:db.close()

def make_server(store,verifier):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup();self.connection.settimeout(3)
        def log_message(self,*args):pass
        def reply(self,status,body):
            raw=json.dumps(body).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_GET(self):self.reply(405,{'error':'POST required'})
        def do_POST(self):
            if self.path!='/tasks/import':return self.reply(404,{'error':'route not found'})
            try:verifier.verify(self.headers.get('Authorization'))
            except AuthenticationError:return self.reply(401,{'error':'unauthenticated'})
            except AuthorizationError:return self.reply(403,{'error':'caller forbidden'})
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError:return self.reply(400,{'error':'invalid length'})
            if not 0<length<=4096:return self.reply(413,{'error':'body length limit'})
            try:payload=json.loads(self.rfile.read(length))
            except (ValueError,OSError):return self.reply(400,{'error':'invalid JSON'})
            try:status,body=store.apply(payload)
            except sqlite3.OperationalError:return self.reply(503,{'error':'storage unavailable'})
            self.reply(status,body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.daemon_threads=False
    return server
```

### 12.1 What the transaction protects

```text
BEGIN IMMEDIATE
  -> find canonical (tenant, job)
  -> reject missing/changed operation
  -> if effect already exists: return saved completion semantics
  -> insert unique effect
  -> mark job complete
COMMIT
  -> acknowledge successful application
```

The fixture serializes SQLite writers and enforces a unique composite key. The effect is another row in the same database transaction. This does not establish exactly-once email delivery, vector-store writes, payment calls or any effect in a separate system. Those need their own idempotency/outbox/reconciliation design.

A service account authorized for this endpoint is still trusted to invoke its allowed jobs. The tenant test prevents selecting a tenant-a-only job under tenant-b and validates canonical values; it does not implement per-end-user login, tenant-specific service-account roles or revocation. The producer must establish the original user's permission before creating the job.

### 12.2 Actual delivery/failure observations

```json
{
  "first": 201,
  "replay": 200,
  "before_commit_attempts": [
    503,
    201
  ],
  "after_commit_attempts": [
    503,
    200
  ],
  "concurrent_status_counts": {
    "201": 1,
    "200": 15
  },
  "effects": [
    [
      "tenant-a",
      "job-1",
      "hello"
    ],
    [
      "tenant-a",
      "job-after",
      "after"
    ],
    [
      "tenant-a",
      "job-before",
      "before"
    ],
    [
      "tenant-a",
      "job-concurrent",
      "concurrent"
    ],
    [
      "tenant-b",
      "job-1",
      "other-tenant"
    ]
  ],
  "recreated_worker_status": 200
}
```

The before-commit injection returned 503 with no effect, then retry created the effect. The after-commit injection committed first but deliberately returned 503 as a failed acknowledgement; retry returned the saved completion. This models acknowledgement ambiguity using an actual failure response, not a dropped network packet or provider delivery run.

Sixteen concurrent HTTP requests for one job produced one 201 and fifteen 200 responses, with one database effect. A recreated HTTP worker using the same database replayed an earlier completion. The same job ID under a different tenant remained a separate operation.

### 12.3 Permanent failures and retry policy

The fixture returns 400/404/409 for invalid or conflicting requests to make those conditions visible. If it were placed directly behind Cloud Tasks, those non-2xx responses would remain subject to retry policy. It does not magically classify them as terminal.

A production worker should distinguish unauthorized requests from authenticated business failures. For a permanent business failure, a useful pattern is to durably record the terminal job result and acknowledge completion of handling, while making that failure visible through job status/alerts. A transient dependency failure can return a retryable failure response. Define this deliberately; never return success just to silence retries before preserving the outcome.

---

## 13. Architectural understanding: build a cloud backend and ingestion path

### 13.1 Start with requirements and a request/data map

Assume an authenticated document-processing backend. Users upload authorized documents, submit imports, see job progress and retrieve permitted results. Ask about file size/format, tenant isolation, latency, processing duration, data location, recovery, volume, cost and provider constraints before choosing services.

```text
Interactive request path (illustrative AWS deployment)

Client -> DNS -> optional CDN behavior
                  | static/public cache policy
                  | authenticated API pass-through policy
                  v
                ALB HTTPS listener / host-path rule
                  |
                  +-> private app target in AZ A
                  +-> private app target in AZ B
                           |
                           +-> durable database
                           +-> authorized object storage

Asynchronous HTTP work path (illustrative Cloud Tasks deployment)

Authorized API -> job + outbox transaction -> enqueue dispatcher
                 -> Cloud Tasks queue -> authenticated HTTPS worker
                 -> idempotent processing/checkpoint -> durable completion
```

The diagrams teach two resume-linked deployment paths. They do not assert that your actual projects combine providers. If one system spans providers, include cross-provider credentials, latency, egress, network reachability and failure ownership explicitly rather than treating the arrow as free.

### 13.2 A build path with concrete checkpoints

1. **Make the application work privately.** Validate a release and dependencies using M13/M16/M17. Confirm the intended listener and an actual useful readiness check.
2. **Design cloud network and identity.** Specify VPC/subnets/routes, target/health ports and scoped SG rules. Assign the workload role needed for its exact storage/queue operations. Keep database/admin exposure deliberate.
3. **Add ingress and check the whole path.** Configure listener/rules/target groups, HTTPS and DNS. Test a real route, forwarded context and health reason codes. Ensure the target is not reachable through an unintended bypass.
4. **Apply CDN policies per content type.** Start with public versioned assets and explicit authenticated API behavior. Verify query/header variants and credential forwarding. Test two distinct users/tenants, not only an anonymous hit.
5. **Create durable job intent.** Authorize the user and persist a canonical tenant/job record with enqueue intent atomically. Use an outbox dispatcher or equivalent recovery mechanism for the DB-to-queue gap.
6. **Configure task dispatch identity.** Verify producer queue permission, actAs/service-agent setup, worker audience and target invoker policy. Test a valid delivery and negative authentication paths in staging.
7. **Prove duplicate/failure behavior.** Inject failure before and after the effect, concurrent duplicate delivery, deadline ambiguity and a permanent business error. Inspect durable state and the user-visible job result.
8. **Operate it.** Monitor error/latency, target health, queue age/backlog, retry rates, database pressure and cost. Test target replacement, a rollout failure and recovery with defined acceptance criteria.

Only the local portions listed in the verification map are executed here. Live networking, policies, tokens, queue scheduling, AZ failures and cloud billing require separate staging evidence.

### 13.3 The database-to-queue gap

Two independent calls create failure windows:

```text
commit job, then enqueue -> process may stop before enqueue
enqueue, then commit job -> worker may run before job exists or commit fails
```

An outbox keeps job creation and dispatch intent in one database transaction. A dispatcher retries sending the intent and marks its progress. Stable task names can reduce duplicate creates within provider retention rules; durable worker idempotency remains necessary. A reconciliation process can locate old pending jobs and incomplete dispatch intent.

The local module does not implement an outbox dispatcher or call CreateTask. It proves the consumer-side duplicate boundary and the request construction separately. Revisit [M9](/docs/resume-skills/webhooks-payments-reliable-integrations) and [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) for reliable integration and durable-work foundations.

### 13.4 External effects and tenant-safe ingestion

For an embeddings/document pipeline, include authorized object references, parser limits, tenant-scoped chunk/vector metadata and idempotent result identifiers. A token authenticating the worker caller does not authorize arbitrary paths supplied in a payload. The worker should read canonical job data and enforce its allowed scope.

If the database and vector store cannot participate in one transaction, track stages and reconcile partial results. Repeated execution must not duplicate charges or make one tenant's vectors retrievable by another. M23/M24 will expand the AI-specific storage/retrieval path; this chapter does not invent a tested embedding provider integration.

---

## 14. Troubleshooting cloud failures by boundary

| Symptom | First questions | Useful evidence |
| --- | --- | --- |
| No connection to EC2 endpoint | Correct DNS/address/route? SG/NACL/OS policy? Process bound correctly? | Intended path/configuration plus listening sockets and network diagnostics |
| ALB target unhealthy | Registered/enabled target? Correct health path/port/protocol/matcher? | Target reason codes, probe/app logs, SG path |
| ALB response failure after release | Target available? Protocol/path match? Dependency slow? | Correlated ingress/app logs and target state |
| AWS API AccessDenied | Which actual principal/role? Which action/resource and applicable policies? | SDK error, identity context and policy evaluation |
| CDN serves wrong/private response | Which behavior/key/TTL? Are auth/cookies safely forwarded and caching disabled where required? | Response headers, behavior/policies, distinct-user tests |
| Task create denied | Producer permission and actAs scope? | CreateTask error and intended identities |
| Worker 401/403 | Token signature/issuer/audience/time? Expected service account? Platform invoker policy? | Safe claim metadata and auth failure class, without token logging |
| Job executes repeatedly | No acknowledgement? Timeout? Permanent failure? Lost post-commit response? | Attempt status, durable job/effect state, retry/queue age |
| Queue backlog grows | Arrival rate, attempts, concurrency, worker service time and downstream pressure? | Queue age/backlog, dispatch/error rates and worker/dependency metrics |

A useful diagnostic order is: identify the request/operation and its correlation ID, find the last successful boundary, inspect the next boundary's evidence, then change the component that owns the failure. Do not widen IAM permissions to fix a closed TCP socket or increase a proxy timeout to fix an invalid audience.

For an AWS network failure, reason about the intended packet path before changing every rule. For task delivery, distinguish creation, scheduling, authenticated admission, business execution and acknowledgement. A task appearing in a queue and a job appearing complete are different facts.

---

## 15. Resume connection and explanation drills

A useful 30-second answer:

> EC2 supplies the virtual machine; the application still needs configuration and a running service. An ALB provides an ingress/routing and target-health layer. A CDN can reduce suitable origin traffic, but its cache key and private-response policy must be correct. Cloud Tasks delivers HTTP work requests with configured identity and retries, so the worker verifies the caller and makes effects idempotent before acknowledging.

For two minutes, trace a request and a job separately, then name the network and IAM boundaries. For five minutes, add health/fail-open behavior, private targets, pool/state limits, CDN variants, enqueue ambiguity, outbox and post-commit retry.

When discussing resume experience, state the exact service you actually used, your contribution and your evidence. Do not rename an unspecified CDN as CloudFront, claim multi-zone operation without configuration/evidence, or turn the local tests into a measured production uptime/latency result.

---

## 16. Must remember and common wrong answers

| Say this | Avoid this |
| --- | --- |
| Cloud services have explicit operation/identity/network boundaries | Cloud means the provider handles every application problem |
| Region, zone, host and worker are different failure domains | Two PM2 workers provide multi-zone availability |
| Route, address, permission and listener must fit the path | Opening a security-group port makes any app reachable |
| IAM authorization and TCP reachability are different | An admin role automatically opens the network |
| Private application targets can sit behind public ingress | Every backend instance needs a public IPv4 address |
| ALB health routing has a documented all-unhealthy fail-open case | Unhealthy targets can never receive a request |
| Cache keys decide which responses can be shared | Forwarding a header always makes it part of the cache key |
| CloudFront minimum TTL interacts with origin cache headers | no-store always overrides every distribution policy |
| SDK message validation is offline shape evidence | A serialized task proves cloud enqueue and delivery worked |
| Verify token authenticity, audience and caller authorization | A task header or decoded JWT proves identity |
| Stable task naming is bounded create deduplication | A task ID gives permanent exactly-once effects |
| Commit durable work before a success acknowledgement | Return 200 and assume unfinished work will survive |

---

## 17. Interview questions and follow-ups

### Q1. What changes when you move a backend to the cloud?

The provider supplies chosen infrastructure/managed services, while your application still needs correct configuration, identity, network exposure, state and recovery. Explain the responsibility split for the actual service rather than treating cloud as one deployment mode.

### Q2. What is EC2, and how is it different from Docker?

EC2 provides virtual machines. Docker packages/runs containers, which can run on an EC2 host or elsewhere. A machine image, container image, application runtime and process are different layers. Starting either does not establish user reachability or application correctness.

### Q3. Region versus Availability Zone?

A Region is a geographic area; zones are isolated locations within it. Spreading a design across zones addresses a different failure domain from multiple processes on one host. Data dependencies, routing and remaining capacity must support the intended failure.

### Q4. Does two-instance deployment guarantee high availability?

No. Inspect placement, health/routing, capacity, shared data, configuration and recovery. Two instances may share a zone or a failing dependency. Availability is about the whole request path and its tested failure behavior.

### Q5. What is a VPC, subnet and route table?

A VPC defines the virtual network; a subnet supplies an address range in a zone; a route table selects forwarding destinations. Permissions and application sockets are additional boundaries. Trace the actual packet path rather than assigning all networking behavior to one resource.

### Q6. Why can an EC2 instance with a public IP still be unreachable?

Check DNS/address, internet-gateway attachment/routing, SG/NACL/OS policy and the listening process/address. A public address alone does not create the complete path. A service bound only to loopback cannot accept an external connection on its private interface.

### Q7. Security group versus network ACL?

Security groups apply allow rules to associated resources and track permitted flows; NACLs apply ordered subnet rules without stateful return tracking. They can both affect reachability. Opening one layer does not override another or start the application.

### Q8. Why put application instances in private subnets behind an ALB?

It allows a deliberate public ingress while backends use private addressing and scoped inbound rules. They still need dependency/management access and suitable outbound paths. The choice must match operational requirements; it is not automatic security for business data.

### Q9. Why does localhost stop working when an ALB becomes the caller?

The ALB is not in the application's host loopback namespace. It needs a reachable target interface/port. Expose the intended private target hop with appropriate controls, such as VM Nginx forwarding locally to Node, and align the target group's port with that listener.

### Q10. What does IAM control?

Which authenticated principals may perform which cloud API actions on which resources under applicable conditions/policies. It does not replace network routing or tenant-record authorization. An applicable explicit deny can override an allow; inspect the actual principal and full policy context.

### Q11. Why use an EC2 IAM role instead of hardcoded access keys?

An attached instance profile can supply temporary role credentials that supported SDK providers obtain/refresh. This reduces long-lived secret distribution and scopes workload access. The role still needs least privilege, correct trust and protection from credential exposure.

### Q12. Trust policy versus permissions policy?

Trust determines who may assume the role. Permissions determine what the resulting identity may do. The example EC2 service trust does not itself grant S3 object access. Valid JSON also does not prove the effective cloud authorization outcome.

### Q13. What are listener, target group and target?

A listener accepts traffic on a protocol/port; its rules choose routing actions. A target group contains registered backends with a configured protocol/port and health policy. A target is a selected backend endpoint of a supported type. Trace a concrete request through these relationships.

### Q14. ALB versus NLB?

ALB serves application-layer HTTP/HTTPS routing needs; NLB addresses transport-level connection use cases. Select based on required protocol/features and current documentation. Neither name describes your application process manager, and neither fixes invalid application responses.

### Q15. Can an unhealthy ALB target still receive traffic?

Yes: the documented all-registered-targets-unhealthy case can fail open. Health checks guide routing and have thresholds/delays; they are not an access-control policy. Read the target reason codes and design service behavior for requests arriving during failure.

### Q16. What should a readiness check prove?

That the instance can accept the intended class of work under your chosen policy. Distinguish process liveness from useful dependency readiness and avoid checks that require end-user credentials accidentally. A health response remains a sampled observation, not a permanent correctness guarantee.

### Q17. Vertical scaling versus horizontal scaling?

Vertical changes resources per machine; horizontal adds capacity units. More web workers can multiply pools/state and overload a shared dependency. Choose scaling policy using workload and bottleneck evidence, with warm-up time and failure headroom accounted for.

### Q18. CDN versus load balancer?

A CDN can reuse suitable responses near users; a load balancer routes traffic among backends. They can appear in one request path and have separate TLS, health and policy boundaries. A CDN miss may still reach a load-balanced origin.

### Q19. What is a cache key and why is it a security concern?

It defines which requests share a cached response. Omitting a field that changes private/tenant content can leak responses. Forwarding that field to the origin does not automatically include it in the key. Prefer explicit safe behavior for authenticated API routes.

### Q20. Does Cache-Control: no-store always prevent CloudFront caching?

No: the distribution's cache-policy minimum TTL matters, and a positive minimum can force caching despite no-store/private. Inspect the actual behavior/policy. The local conservative cache respects those headers; it does not reproduce CloudFront's configurable minimum-TTL rule.

### Q21. What does Cloud Tasks do?

It manages task dispatch to a worker, including configured scheduling, rate/concurrency and retries. The worker performs the business operation. Task creation acceptance, delivery admission and completed business work are separate milestones requiring separate evidence.

### Q22. Does Cloud Tasks guarantee exactly-once business execution?

No: provider documentation warns of duplicate execution. Make the business operation idempotent with durable uniqueness and atomic updates where possible. Name deduplication and ordinary successful delivery cannot replace the worker's correctness boundary.

### Q23. OIDC token versus OAuth access token for task delivery?

An OIDC ID token is generally suited to authenticating the caller to an intended worker audience. Google API endpoints generally expect an OAuth access token instead. Configure the target's actual accepted identity/audience; do not use a user-login explanation for every service-to-service request.

### Q24. Which permissions are needed around authenticated task creation?

Check producer permission to create tasks, actAs permission for the selected service account, the Cloud Tasks service agent's token setup, and target-side invoker/authorization policy. The service account for OIDC must be in the queue project. One enqueuer role does not authorize every identity and endpoint.

### Q25. Why are task headers insufficient authentication?

An external caller can supply metadata-looking headers if it can reach the worker. Verify the bearer signature and issuer/audience/time, then authorize the verified caller. The real HTTP fixture rejects a request with a forged task-name header but no token.

### Q26. What happens if a worker commits but its acknowledgement fails?

Delivery may retry even though the effect exists. The worker must detect durable completion and return compatible saved semantics without repeating the effect. The local test returned 503 after commit, then 200 on retry with one effect; this was a fault injection, not a provider delivery observation.

### Q27. Is task-name deduplication enough?

No. Its retention is bounded, and business work can be invoked by other paths or concurrent attempts. Keep a tenant-scoped operation identifier and canonical payload/result in durable storage. The SDK's stable hash helps name requests but does not authorize or atomically apply the job.

### Q28. Why use an outbox when creating a job and enqueuing it?

A database transaction and task-create API call are separate operations. A crash between them can lose dispatch intent or expose uncommitted work. Persist job and enqueue intent atomically, retry dispatch and retain idempotency/reconciliation. This module documents that architecture without implementing a cloud dispatcher.

### Q29. How do you handle permanent job errors and growing backlog?

Preserve permanent business failure durably and decide acknowledgement policy; non-2xx is still subject to retry rules. For backlog, inspect arrival/attempt rates, concurrency, service time, auth failures and dependencies. Do not increase dispatch rate when the downstream is already saturated.

### Q30. Design a cloud document-processing backend and explain failure recovery.

Draw ingress/CDN/ALB/private application/data and the authorized job/outbox/queue/worker path. Assign identities, tenant scope, health and cache policy. Explain pre/post-commit retry, dependency limits, recovery and monitoring. Label what was actually verified: local SDK/crypto/HTTP/SQLite here, versus live cloud policy/delivery/failover that needs staging evidence.

---

## 18. Practice tasks

1. **Draw reachability.** Trace DNS, public endpoint, route, SG/NACL, target interface and listening process. Explain why changing only one cannot repair every failure.
2. **Choose failure domains.** Compare two processes, two hosts in one zone and two zones with a shared data dependency. State the failure each arrangement can address.
3. **Review identities.** Explain the two illustrative AWS policies and the principal/action/resource they intend. List missing context needed to establish real access.
4. **Design target health.** Pick a health path/matcher and explain registration, failure thresholds, draining and the all-unhealthy exception. Plan staging evidence.
5. **Break cache equivalence.** Compare language/query variants and two authenticated identities through the local proxy. Explain a production policy that avoids response leakage.
6. **Inspect a task message.** Deserialize the official SDK request, decode its body once and identify target, audience, caller identity and deadline. State what it does not prove.
7. **Run negative token cases.** Test wrong signature/audience/issuer/time/caller and forged metadata headers. Explain the fixture trust versus real provider trust.
8. **Reproduce acknowledgement ambiguity.** Observe no effect before commit and one effect after the failed acknowledgement. Retry and compare durable state/status.
9. **Test duplicate business work.** Send concurrent requests for the same job, then for the same ID under another tenant. Explain why an external payment/vector write needs a separate strategy.
10. **Prepare an operational walkthrough.** Diagnose a queue backlog and a private-target network failure, name the evidence at each boundary, and outline outbox recovery and a staging rollout.

---

## 19. Exit checklist

- [ ] I can distinguish cloud services, VM/container/process layers and responsibility boundaries.
- [ ] I can explain Region/zone/host/worker failure domains without an availability overclaim.
- [ ] I can trace EC2/ALB reachability through route, address, permissions and listener.
- [ ] I can distinguish security groups, NACLs, IAM and application authorization.
- [ ] I can explain role trust, scoped permissions and temporary credentials.
- [ ] I can draw listener/rule/target-group/target and explain the health fail-open exception.
- [ ] I can reason about CDN keys, credential forwarding and minimum TTL.
- [ ] I can distinguish task creation, delivery, work and acknowledgement.
- [ ] I can explain task identity/audience permissions and reject forged headers.
- [ ] I can demonstrate durable duplicate handling and post-commit retry semantics.
- [ ] I can explain the enqueue gap, outbox and external-effect limitations.
- [ ] I can separate local fixture evidence from live cloud verification still required.

These remain unchecked until you can demonstrate the skill; authoring a chapter does not mark your learning complete.

---

## 20. Sources and verification map

Official references researched for this chapter:

- AWS: [EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html), [Regions/Zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html), [internet gateways](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html), [security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html), [SG references](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html), [NACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html), [IAM evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) and [EC2 roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html).
- AWS ingress/cache: [ELB family](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html), [ALB target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html), [health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html), [deregistration](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html#deregistration-delay), [CloudFront keys](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html), [TTL policy](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cache-key-understand-cache-policy.html), [expiration](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html) and [authorization forwarding](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/http-401-unauthorized.html).
- Google: [HTTP task creation](https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks), [HTTP target behavior](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks#HttpRequest), [task names](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks/create), [RetryConfig](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/RetryConfig), [queue limits](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues), [OIDC config](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/OidcToken), [duplicate execution](https://docs.cloud.google.com/tasks/docs/common-pitfalls) and [Google-auth verification](https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.id_token.html).

Version-sensitive fields, policies, quotas and pricing should be refreshed before use. The current Task message includes retry_config; older tutorials may describe a narrower queue-only model. The fixture snapshots installed libraries and does not claim that offline serialization validates server-side acceptance.

**53 checks passed:**

| Group | Named checks | Evidence boundary |
| --- | --- | --- |
| SDK | 9 | Official protobuf/JSON round trip, bytes/base64, naming/tenant scope, explicit identity/deadline and local input contract |
| Authentication | 14 | Official verifier with actual generated-key signatures and injected local trust; negative claim/signature/caller cases |
| Worker | 16 | Real loopback HTTP, transactional SQLite, pre/post-commit failures, concurrent duplicates, tenant scope and recreated handler |
| Cache | 14 | Real HTTP origin/proxy, variant isolation, private/bypass rules, injected-clock expiry and local invalidation |
| **Total** | **53** | Named local checks, some with multiple assertions |

Implementation is under examples/resume-skills/module-18-aws-gcp/: task_request.py, worker.py, cache_demo.py and verify.py, plus the dependency snapshot and illustrative policy JSON. The chapter embeds tested teaching sources and the SDK/result JSON exactly. verification-results.json and verification-output.txt record execution; task-request.json records offline message JSON; certificate-transport-results.json records fixture key transport; cleanup-results.json records closed listeners and scratch/database removal. Content/site validation artifacts accompany them.

No AWS IAM evaluator, security-group/network deployment, EC2 instance, live ALB/CloudFront, Google-issued token/key rotation, Cloud Tasks create/dispatch/backoff/deadline, public TLS endpoint, cloud failover, outbox dispatcher, external business effect or production load/cost measurement was verified. The standard-library HTTP servers are local teaching tools. No account credentials were required and Docker was not started.

---

## Next

Continue to [M19: Git, CI/CD, Testing, Observability and Performance](/docs/resume-skills/git-ci-cd-testing-observability-performance) for reproducible releases, pipelines, test boundaries, logs/metrics/traces, latency distributions and defensible performance measurements.

Revisit [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) for durable work/cache foundations, [M17](/docs/resume-skills/linux-deployment-nginx-pm2) for the application/proxy process path, and [M8](/docs/resume-skills/api-security-authorization-multi-tenancy) for business/tenant authorization. The [master roadmap](/docs/resume-skills) shows the remaining sections.
