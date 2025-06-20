import asyncio
from DatabaseManager import DatabaseManager

db_url = "postgresql://neondb_owner:npg_pSG1g7wruVTm@ep-twilight-night-a2fnu5re-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

async def main():
    db = DatabaseManager(db_url)
    await db.connect()
    await db.create_tables()
#    await db.delete_tables()


asyncio.run(main())