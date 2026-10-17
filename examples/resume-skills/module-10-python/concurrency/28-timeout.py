import asyncio
async def main():
    cleaned = []
    async def wait_forever():
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.append(True)
    try:
        async with asyncio.timeout(0.02):
            await wait_forever()
    except TimeoutError:
        print('timed out')
    print('cleaned:', cleaned == [True])
asyncio.run(main())
