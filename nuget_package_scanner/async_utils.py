import asyncio
import logging

async def wait_or_raise(tasks):
    '''
    Utility method that waits for a set of tasks to complete and raises any exceptions before returning.
    Call this method if you require every task to be successful.
    '''
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    assert not pending # raise any timeout errors now
    for d in done:
        if d.exception():
            logging.exception(d.exception)
            raise d.exception()


