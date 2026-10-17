import os
from pymongo import MongoClient
from bson.codec_options import CodecOptions
from datetime import timezone

CODEC=CodecOptions(tz_aware=True,tzinfo=timezone.utc)

def make_client(*,listeners=None,max_pool_size=4,wait_ms=500):
    port=int(os.environ['M14_PORT'])
    if not 1024<=port<=65535 or port==27017: raise RuntimeError('Explicit non-default fixture port required')
    return MongoClient(f'mongodb://127.0.0.1:{port}/?directConnection=true&replicaSet=m14_fixture',
        appname='placement-m14',maxPoolSize=max_pool_size,waitQueueTimeoutMS=wait_ms,
        serverSelectionTimeoutMS=3000,connectTimeoutMS=1000,socketTimeoutMS=5000,
        event_listeners=listeners or [])

def database(client):
    name=os.environ['M14_DATABASE']
    if not name.startswith('m14_'): raise RuntimeError('Fixture database prefix required')
    return client.get_database(name,codec_options=CODEC)
