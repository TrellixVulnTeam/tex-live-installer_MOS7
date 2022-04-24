import asyncio
import time
import logging
import random

import httpx


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from helpers.reader import get_containers
from helpers.download import download_async_client


async def worker_async(queue, client):
    i = 0

    while True:
        res = await queue.get()
        if res is None:
            # Notify the queue that the "work item" has been processed.
            return
        logger.debug(i)
        (packagename, hash, directory) = res

        logger.info((packagename, hash, directory))
        await download_async_client(
            client=client, url=packagename, hash=hash, directory=directory
        )
        queue.task_done()
        i += 1


async def downloader_async(max_parrallel_req=8):
    queue = asyncio.Queue()
    containers = get_containers()
    random.shuffle(containers)
    for container in containers:
        await queue.put(container)

    # Create three worker tasks to process the queue concurrently.
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(max_parrallel_req):
            task = asyncio.create_task(worker_async(queue, client))
            tasks.append(task)

        # Wait until the queue is fully processed.
        await queue.join()

        # Cancel our worker tasks.
        for task in tasks:
            task.cancel()
        # Wait until all worker tasks are cancelled.
        await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    start_1 = time.time()
    await downloader_async(1)
    print(f"downloading with 1 took {time.time() - start_1}")

    start_8 = time.time()
    await downloader_async(8)
    print(f"downloading with 8 took {time.time() - start_8}")

    start_20 = time.time()
    await downloader_async(20)
    print(f"downloading with 20 took {time.time() - start_20}")

    # start_50 = time.time()
    # await downloader(50)
    # print(f"downloading with 20 took {time.time() - start_50}")


if __name__ == "__main__":
    asyncio.run(main())
