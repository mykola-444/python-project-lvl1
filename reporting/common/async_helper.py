import asyncio

import aiohttp


class AsyncHelper:
    @staticmethod
    async def async_run(iterable_data: list, func: 'function', parallel_calls_count=5) -> None:
        semaphore = asyncio.Semaphore(parallel_calls_count)
        print(iterable_data)
        async with aiohttp.ClientSession() as async_session:
            tasks = [func(semaphore, async_session, _data) for _data in iterable_data]
            await asyncio.gather(*tasks)