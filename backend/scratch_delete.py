import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def delete_agencies():
    async with AsyncSessionLocal() as session:
        await session.execute(text('DELETE FROM agencies;'))
        await session.commit()
        print('All agencies deleted')

if __name__ == '__main__':
    asyncio.run(delete_agencies())
