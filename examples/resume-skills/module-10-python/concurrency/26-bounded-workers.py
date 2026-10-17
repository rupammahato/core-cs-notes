import asyncio
async def main():
    queue = asyncio.Queue(maxsize=3)
    gate = asyncio.Event()
    active = peak = max_queued = 0
    results = {}
    async def producer():
        nonlocal max_queued
        for value in range(8):
            await queue.put(value)
            max_queued = max(max_queued, queue.qsize())
        for _ in range(3):
            await queue.put(None)
    async def worker():
        nonlocal active, peak
        while True:
            value = await queue.get()
            try:
                if value is None:
                    return
                active += 1
                peak = max(peak, active)
                if active == 3:
                    gate.set()
                try:
                    await gate.wait()
                    await asyncio.sleep(0)
                    results[value] = value * value
                finally:
                    active -= 1
            finally:
                queue.task_done()
    async with asyncio.TaskGroup() as group:
        group.create_task(producer())
        for _ in range(3):
            group.create_task(worker())
    await queue.join()
    assert active == 0 and queue.empty()
    assert results == {x: x * x for x in range(8)}
    assert peak == 3 and max_queued <= 3
    print('jobs:', len(results), 'peak:', peak, 'queued:', max_queued)
async def bounded_run():
    await asyncio.wait_for(main(), timeout=5)
asyncio.run(bounded_run())
