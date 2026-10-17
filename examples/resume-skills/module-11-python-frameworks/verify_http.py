import json
import httpx
from flask_app import create_app as flask_factory
from fastapi_app import create_app as fastapi_factory
from checks import Checks, equal, require
from servers import flask_server, fastapi_server, assert_port_closed

checks = Checks('http')
ports = []
observations = {}
for name, factory, serve in [('flask', flask_factory, flask_server),
                              ('fastapi', fastapi_factory, fastapi_server)]:
    app = factory()
    with serve(app) as base, httpx.Client(base_url=base, trust_env=False, timeout=5) as client:
        ports.append(int(base.rsplit(':', 1)[1]))
        auth = {'Authorization': 'Bearer alpha-demo-token'}
        valid = {'product_id': 'basic', 'quantity': 2}
        def check(label, fn): checks.check(name + ': ' + label, fn)
        def post(body, headers=auth): return client.post('/api/quotes', json=body, headers=headers)
        def status(response, expected):
            equal(response.status_code, expected)
            rid = response.headers.get('x-request-id')
            if rid:
                audit = app.extensions['audit'] if name == 'flask' else app.state.audit
                trace = audit.trace(rid)
                if 'lease-open' in trace:
                    equal(trace.count('lease-close'), 1)
                if expected == 422:
                    require('route' not in trace, 'invalid body reached business route')
        check('health is public', lambda: status(client.get('/health'), 200))
        check('missing credentials rejected', lambda: status(post(valid, {}), 401))
        check('unknown credential rejected', lambda: status(post(valid, {'Authorization': 'Bearer wrong'}), 401))
        def challenge():
            response = post(valid, {})
            equal(response.headers.get('www-authenticate'), 'Bearer')
        check('401 has Bearer challenge', challenge)
        def success():
            response = post(valid)
            status(response, 200)
            body = response.json()
            equal(body['total_paise'], 25000)
            equal(body['quantity'], 2)
            equal(set(body), {'product_id','quantity','total_paise','currency','created_at'})
            require(body['created_at'] in ('2026-10-14T06:30:00Z', '2026-10-14T06:30:00+00:00'))
            observations[name + '_quote'] = body
            observations[name + '_trace'] = (app.extensions['audit'] if name == 'flask'
                                             else app.state.audit).trace(response.headers['x-request-id'])
        check('validated quote uses trusted price and public response', success)
        check('cross-tenant product hidden', lambda: status(post({'product_id':'team','quantity':1}), 404))
        def beta():
            response = post({'product_id':'team','quantity':1}, {'Authorization':'Bearer beta-demo-token'})
            status(response, 200)
            equal(response.json()['total_paise'], 25000)
        check('beta sees its own product', beta)
        for label, value in [('boolean', True), ('string', '2'), ('float', 2.0),
                             ('zero', 0), ('over cap', 101), ('null', None)]:
            check(label + ' quantity rejected', lambda value=value: status(post({'product_id':'basic','quantity':value}), 422))
        check('unknown fields rejected', lambda: status(post({**valid, 'tenant_id':'beta', 'total_paise':1}), 422))
        check('missing field rejected', lambda: status(post({'product_id':'basic'}), 422))
        check('malformed JSON rejected', lambda: status(client.post('/api/quotes', content=b'{',
              headers={**auth, 'Content-Type':'application/json'}), 400 if name == 'flask' else 422))
        check('wrong media type rejected', lambda: status(client.post('/api/quotes', content='text',
              headers={**auth, 'Content-Type':'text/plain'}), 415))
        def public_product():
            response = client.get('/api/products/basic', headers=auth)
            status(response, 200)
            equal(response.json(), {'product_id':'basic','amount_paise':12500,'currency':'INR'})
        check('product response excludes internal cost', public_product)
        check('unknown product returns 404', lambda: status(client.get('/api/products/unknown', headers=auth), 404))
        def listing():
            response = client.get('/api/products?limit=1', headers=auth)
            status(response, 200)
            items = response.json()['items'] if name == 'flask' else response.json()
            equal([item['product_id'] for item in items], ['basic'])
        check('query limit parsed and list tenant-filtered', listing)
        check('invalid query limit rejected', lambda: status(client.get('/api/products?limit=0', headers=auth),
                                                           400 if name == 'flask' else 422))
        def method():
            response = client.put('/api/quotes', json=valid, headers=auth)
            status(response, 405)
            require('POST' in response.headers.get('allow', ''))
        check('405 preserves Allow header', method)
        check('unknown route returns 404', lambda: status(client.get('/missing'), 404))
        def metadata():
            response = post(valid)
            equal(response.headers['cache-control'], 'no-store')
            equal(len(response.headers['x-request-id']), 32)
            trace = (app.extensions['audit'] if name == 'flask' else app.state.audit).trace(response.headers['x-request-id'])
            equal(trace, ['before','lease-open','route','after','lease-close','teardown'] if name == 'flask'
                         else ['before','lease-open','route','lease-close','after'])
        check('metadata and request-resource lifecycle observed', metadata)
        if name == 'flask':
            check('configured body limit rejects large JSON', lambda: status(client.post('/api/quotes',
                  content=json.dumps({'product_id':'x'*5000,'quantity':1}),
                  headers={**auth, 'Content-Type':'application/json'}), 413))
        else:
            def openapi():
                schema = client.get('/openapi.json').json()
                require('post' in schema['paths']['/api/quotes'])
                props = schema['components']['schemas']['QuoteIn']['properties']
                equal(props['quantity']['type'], 'integer')
                equal(props['quantity']['minimum'], 1)
                equal(schema['components']['schemas']['QuoteIn']['additionalProperties'], False)
                require('HTTPBearer' in schema['components']['securitySchemes'])
                observations['openapi_version'] = schema['openapi']
            check('OpenAPI describes schema constraints and security', openapi)
            check('documentation route responds', lambda: status(client.get('/docs'), 200))
            def invalid_privacy():
                response = post({**valid, 'secret': 'do-not-echo'})
                status(response, 422)
                require('do-not-echo' not in response.text)
            check('custom validation handler excludes rejected input values', invalid_privacy)
    assert_port_closed(base)
    if name == 'fastapi':
        equal(app.state.audit.trace('application'), ['startup','shutdown'])
        equal(app.state.catalog.closed, True)
checks.save(observations=observations, ports=ports, listeners_closed=True,
            transports='Real loopback HTTP: Werkzeug development WSGI and Uvicorn ASGI')
