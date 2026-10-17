from contextlib import asynccontextmanager
from typing import Annotated
from uuid import uuid4
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from domain import (Audit, Catalog, Lease, Principal, QuoteIn, QuoteOut, ProductOut,
                    Unauthenticated, ProductNotFound, authenticate, build_quote, FIXED_NOW)

bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix='/api')

def principal(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    try:
        header = None if credentials is None else credentials.scheme + ' ' + credentials.credentials
        return authenticate(header)
    except Unauthenticated:
        raise HTTPException(401, 'unauthenticated', headers={'WWW-Authenticate': 'Bearer'})

async def lease(request: Request):
    value = Lease(request.app.state.audit, request.state.request_id)
    try:
        yield value
    finally:
        value.close()

async def require_json(request: Request):
    media = request.headers.get('content-type', '').split(';', 1)[0].strip().lower()
    if media != 'application/json' and not (media.startswith('application/') and media.endswith('+json')):
        raise HTTPException(415, 'expected_json')

PrincipalDep = Annotated[Principal, Depends(principal)]
LeaseDep = Annotated[Lease, Depends(lease, scope='function')]

@router.post('/quotes', response_model=QuoteOut, dependencies=[Depends(require_json)])
async def quote(body: QuoteIn, request: Request, who: PrincipalDep, resource: LeaseDep):
    request.app.state.audit.add(request.state.request_id, 'route')
    return build_quote(request.app.state.catalog, who, body, request.app.state.clock())

@router.get('/products/{product_id}', response_model=ProductOut)
async def product(product_id: str, request: Request, who: PrincipalDep, resource: LeaseDep):
    request.app.state.audit.add(request.state.request_id, 'route')
    return request.app.state.catalog.product(who, product_id)

@router.get('/products', response_model=list[ProductOut])
async def products(request: Request, who: PrincipalDep, resource: LeaseDep,
                   limit: Annotated[int, Query(ge=1, le=10)] = 10):
    return request.app.state.catalog.products(who, limit)

def create_app(*, clock=lambda: FIXED_NOW):
    audit = Audit()
    @asynccontextmanager
    async def lifespan(app):
        app.state.catalog = Catalog()
        app.state.clock = clock
        audit.add('application', 'startup')
        try:
            yield
        finally:
            app.state.catalog.close()
            audit.add('application', 'shutdown')

    app = FastAPI(title='Placement Quote API', lifespan=lifespan)
    app.state.audit = audit
    app.include_router(router)

    @app.middleware('http')
    async def request_metadata(request, call_next):
        request.state.request_id = uuid4().hex
        audit.add(request.state.request_id, 'before')
        response = await call_next(request)
        audit.add(request.state.request_id, 'after')
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, error):
        return JSONResponse({'detail': [{'loc': list(e['loc']), 'type': e['type']}
                                       for e in error.errors()]}, status_code=422)

    @app.exception_handler(ProductNotFound)
    async def missing(request, error):
        return JSONResponse({'error': 'product_not_found'}, status_code=404)

    @app.get('/health')
    async def health():
        return {'status': 'ok', 'framework': 'fastapi'}

    return app
