import asyncio
import time
async def main():
    events = []
    async def worker():
        events.append('start')
        await asyncio.sleep(0)
        events.append('done')
        return 7
    coro = worker()
    print(events)
    task = asyncio.create_task(coro)
    print(await task, events)
    events.clear()
    asyncio.get_running_loop().call_soon(events.append, 'tick')
    async def blocks():
        time.sleep(0.01)  # Deliberate blocking example; no timing claim.
        events.append('blocking call returned')
    await blocks()       # No suspension inside blocks().
    events.append('caller continued')
    await asyncio.sleep(0)
    print(events)
    from threading import get_ident
    loop_thread = get_ident()
    thread_id = await asyncio.to_thread(get_ident)
    print('thread offload:', thread_id != loop_thread)
asyncio.run(main())
