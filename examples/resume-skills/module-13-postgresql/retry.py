from psycopg.errors import SerializationFailure, DeadlockDetected

def serializable(pool,operation,*,attempts=3,on_retry=None):
    if type(attempts) is not int or attempts<1: raise ValueError('attempts must be positive')
    for attempt in range(attempts):
        try:
            with pool.connection() as conn:
                with conn.transaction():
                    conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                    return operation(conn)
        except (SerializationFailure,DeadlockDetected) as error:
            if on_retry: on_retry(error.sqlstate)
            if attempt+1==attempts: raise
    raise AssertionError('unreachable')
