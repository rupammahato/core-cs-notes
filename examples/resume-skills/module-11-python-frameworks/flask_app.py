from uuid import uuid4
from flask import Flask, Blueprint, g, request, jsonify, current_app
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException
from domain import (Audit, Catalog, Lease, QuoteIn, QuoteOut, ProductOut,
                    Unauthenticated, ProductNotFound, authenticate, build_quote, FIXED_NOW)

api = Blueprint('api', __name__, url_prefix='/api')

@api.before_request
def prepare():
    g.request_id = uuid4().hex
    current_app.extensions['audit'].add(g.request_id, 'before')
    g.lease = Lease(current_app.extensions['audit'], g.request_id)
    try:
        g.principal = authenticate(request.headers.get('Authorization'))
    except Unauthenticated:
        return jsonify(error='unauthenticated'), 401, {'WWW-Authenticate': 'Bearer'}

@api.post('/quotes')
def quote():
    if not request.is_json:
        return jsonify(error='expected_json'), 415
    body = QuoteIn.model_validate(request.get_json())
    current_app.extensions['audit'].add(g.request_id, 'route')
    value = build_quote(current_app.extensions['catalog'], g.principal, body,
                        current_app.config['CLOCK']())
    return jsonify(QuoteOut.model_validate(value).model_dump(mode='json'))

@api.get('/products/<product_id>')
def product(product_id):
    current_app.extensions['audit'].add(g.request_id, 'route')
    value = current_app.extensions['catalog'].product(g.principal, product_id)
    return jsonify(ProductOut.model_validate(value).model_dump(mode='json'))

@api.get('/products')
def products():
    text = request.args.get('limit', '10')
    if not text.isascii() or not text.isdecimal() or not 1 <= int(text) <= 10:
        return jsonify(error='invalid_limit'), 400
    values = current_app.extensions['catalog'].products(g.principal, int(text))
    return jsonify(items=[ProductOut.model_validate(v).model_dump(mode='json') for v in values])

def create_app(*, clock=lambda: FIXED_NOW):
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=4096, CLOCK=clock)
    app.extensions['audit'] = Audit()
    app.extensions['catalog'] = Catalog()
    app.register_blueprint(api)

    @app.get('/health')
    def health():
        return {'status': 'ok', 'framework': 'flask'}

    @app.after_request
    def after(response):
        if hasattr(g, 'request_id'):
            app.extensions['audit'].add(g.request_id, 'after')
            response.headers['X-Request-ID'] = g.request_id
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.teardown_request
    def cleanup(error):
        if hasattr(g, 'lease'):
            g.lease.close()
        if hasattr(g, 'request_id'):
            app.extensions['audit'].add(g.request_id, 'teardown')

    @app.errorhandler(ValidationError)
    def invalid(error):
        # Do not echo the whole rejected body or validation internals.
        return jsonify(error='invalid_body'), 422

    @app.errorhandler(ProductNotFound)
    def missing(error):
        return jsonify(error='product_not_found'), 404

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()  # Preserve status and protocol headers such as Allow.
        response.data = app.json.dumps({'error': error.name.lower().replace(' ', '_')})
        response.content_type = 'application/json'
        return response

    return app
