import asyncio
import json

trace = []
async def work():
    trace.append('ran')

async def main():
    pending = work()
    trace.append(len(trace))
    await pending

asyncio.run(main())
print(json.dumps(trace))
