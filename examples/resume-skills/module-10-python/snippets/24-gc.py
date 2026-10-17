import gc
import weakref
class Node:
    pass
was_enabled = gc.isenabled()
gc.disable()
try:
    item = Node()
    item.self = item
    ref = weakref.ref(item)
    del item
    print(ref() is not None)
    gc.collect()
    print(ref() is None)
finally:
    if was_enabled:
        gc.enable()
