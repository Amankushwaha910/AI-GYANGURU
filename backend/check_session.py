from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
# async_sessionmaker().__call__() returns an AsyncSession
# AsyncSession IS a context manager (__aenter__/__aexit__ are defined)
# So: async with async_sessionmaker()() as session   works correctly

import inspect
src = inspect.getsource(AsyncSession.__aenter__)
print("AsyncSession.__aenter__ exists:", bool(src))

# Check what async_sessionmaker() returns
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

async def test():
    # Just check the type
    sm = async_sessionmaker
    # The instance (factory) when called returns AsyncSession
    # AsyncSession has __aenter__ so it IS a context manager
    print("AsyncSession is async context manager:", hasattr(AsyncSession, '__aenter__'))

asyncio.run(test())
