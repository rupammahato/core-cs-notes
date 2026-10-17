import asyncio
async def main():
    started = asyncio.Event()
    cleaned = []
    async def peer():
        try:
            started.set()
            await asyncio.Event().wait()
        finally:
            cleaned.append('peer')
    async def fail():
        await started.wait()
        raise ValueError('provider failed')
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(peer())
            group.create_task(fail())
    except* ValueError as errors:
        print('failures:', len(errors.exceptions))
    print('peer cleaned:', cleaned == ['peer'])
asyncio.run(main())
