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
