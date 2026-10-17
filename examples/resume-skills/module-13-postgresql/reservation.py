from uuid import uuid4
from psycopg.errors import ForeignKeyViolation
from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb

class InvalidRequest(ValueError): pass
class OutOfStock(Exception): pass
class IdempotencyConflict(Exception): pass

# Values are bound separately. Fixed schema-qualified identifiers are application-owned.
CLAIM = """
INSERT INTO lesson.reservations (id, tenant_id, request_key, sku, quantity, status)
VALUES (%s,%s,%s,%s,%s,'pending')
ON CONFLICT ON CONSTRAINT reservation_request_unique DO NOTHING
RETURNING id
"""
TAKE_STOCK = """
UPDATE lesson.products SET available=available-%s
WHERE tenant_id=%s AND sku=%s AND available >= %s
RETURNING unit_price_minor, currency
"""

def reserve(conn,*,tenant_id,request_key,sku,quantity,after_claim=None,fail_after_stock=False):
    # tenant_id is trusted authenticated context; this function does not authenticate it.
    if type(tenant_id) is not int or tenant_id<=0:
        raise InvalidRequest('invalid tenant')
    if type(quantity) is not int or not 1<=quantity<=10:
        raise InvalidRequest('quantity must be an integer from 1 to 10')
    if type(request_key) is not str or not 1<=len(request_key)<=80:
        raise InvalidRequest('invalid request key')
    if type(sku) is not str or not 1<=len(sku)<=80:
        raise InvalidRequest('invalid sku')
    if not conn.autocommit or conn.info.transaction_status!=TransactionStatus.IDLE:
        raise ValueError('reserve requires an idle autocommit connection and owns its transaction')
    try:
        with conn.transaction():
            claimed=conn.execute(CLAIM,(uuid4(),tenant_id,request_key,sku,quantity)).fetchone()
            if claimed is None:
                row=conn.execute('SELECT id,sku,quantity,total_minor,currency,status FROM lesson.reservations WHERE tenant_id=%s AND request_key=%s',
                                 (tenant_id,request_key)).fetchone()
                if row is None or row[5]!='reserved': raise RuntimeError('incomplete reservation state')
                if (row[1],row[2])!=(sku,quantity): raise IdempotencyConflict('key reused with different payload')
                return {'reservation_id':str(row[0]),'quantity':row[2], 'total_minor':row[3],
                        'currency':row[4],'replayed':True}
            reservation_id=claimed[0]
            if after_claim: after_claim(conn)  # Deterministic test coordination; not an HTTP option.
            product=conn.execute(TAKE_STOCK,(quantity,tenant_id,sku,quantity)).fetchone()
            if product is None: raise OutOfStock('stock unavailable')
            if fail_after_stock: raise RuntimeError('injected before reservation/outbox completion')
            total=product[0]*quantity
            conn.execute("UPDATE lesson.reservations SET status='reserved',total_minor=%s,currency=%s WHERE id=%s",
                         (total,product[1],reservation_id))
            conn.execute('INSERT INTO lesson.outbox (reservation_id,payload) VALUES (%s,%s)',
                         (reservation_id,Jsonb({'tenant_id':tenant_id,'reservation_id':str(reservation_id),'kind':'reserved'})))
            return {'reservation_id':str(reservation_id),'quantity':quantity,'total_minor':total,
                    'currency':product[1],'replayed':False}
    except ForeignKeyViolation as error:
        if error.diag.constraint_name=='reservation_product_fk':
            raise OutOfStock('stock unavailable') from error
        raise
