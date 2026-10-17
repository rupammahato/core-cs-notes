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
