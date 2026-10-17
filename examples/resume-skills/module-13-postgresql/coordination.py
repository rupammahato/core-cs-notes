from threading import Thread, Event
import time

def wait_blocked(observer,waiting_pid,blocking_pid,timeout=5):
    deadline=time.monotonic()+timeout
    while True:
        blockers=observer.execute('SELECT pg_blocking_pids(%s)',(waiting_pid,)).fetchone()[0]
        if blocking_pid in blockers: return
        if time.monotonic()>deadline: raise AssertionError('Expected database lock wait not observed')
        time.sleep(0.005)

def background_update(conn,query,params=None):
    box={}
    done=Event()
    def worker():
        try:
            cursor=conn.execute(query,params)
            box['rowcount']=cursor.rowcount
            conn.commit()
        except Exception as error:
            box['error']=error
            conn.rollback()
        finally: done.set()
    thread=Thread(target=worker,daemon=True)
    thread.start()
    return thread,done,box

def finish(thread,done,conn):
    thread.join(6)
    if thread.is_alive():
        conn.cancel()
        thread.join(2)
    if thread.is_alive() or not done.is_set(): raise AssertionError('Database worker did not finish')
