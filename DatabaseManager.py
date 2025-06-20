import asyncpg


class DatabaseManager():
    def __init__(self, db_url):
        self.db_url = db_url
        self.connection_pool = None
    
    async def connect(self):
        if self.connection_pool is None:
            self.connection_pool = await asyncpg.create_pool(dsn=self.db_url, ssl="require")
            print("Succesfully connected to the database.")
    
    async def close_connection(self):
        if self.connection_pool:
            await self.connection_pool.close()
            print("connection closed")

    async def create_tables(self):
        await self.connect()
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS users (
                               user_id BIGINT PRIMARY KEY,
                               username TEXT,
                               first_name TEXT,
                               last_name TEXT,
                               created_at TIMESTAMP DEFAULT NOW()
                               );
                               """)
            
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS bookmarks (
                               id SERIAL PRIMARY KEY,
                               user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                               flight_type TEXT NOT NULL,
                               route TEXT NOT NULL,
                               airline TEXT NOT NULL,
                               departure_date TEXT NOT NULL,
                               departure_time TEXT NOT NULL,
                               arrival_date TEXT NOT NULL,
                               arrival_time TEXT NOT NULL,
                               return_flight_departure_date TEXT,
                               return_flight_departure_time TEXT,
                               return_flight_arrival_date TEXT,
                               return_flight_arrival_time TEXT,
                               departure_stops INT NOT NULL,
                               return_stops INT,
                               departure_duration TEXT NOT NULL,
                               return_duration TEXT,
                               price INT NOT NULL,
                               currency TEXT NOT NULL,
                               created_at TIMESTAMP DEFAULT NOW(),
                               CONSTRAINT unique_bookmark_per_flight UNIQUE (user_id, flight_type, route, departure_date, departure_time, arrival_date, arrival_time, return_flight_departure_date, return_flight_departure_time, return_flight_arrival_date, return_flight_arrival_time, departure_stops, price)
                               )
                               """)
            
            print("Tables created succesfuly")

    async def delete_tables(self):
        await self.connect()
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                               DROP TABLE IF EXISTS bookmarks
                               """)
            print("table dropped")
    
    async def insert_user(self, user):
        if self.connection_pool is None:
            await self.connect()
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                               INSERT INTO users (user_id, username, first_name, last_name)
                               VALUES ($1, $2, $3, $4)
                               ON CONFLICT (user_id) DO NOTHING
                            """, user.id, user.username, user.first_name, user.last_name)

    async def insert_bookmark(self, user_id: int, flight_type: str, flight: dict, return_flight: dict = None):
        if self.connection_pool is None:
            await self.connect()
        rf = return_flight or {}

        if flight_type == "Round trip" and return_flight:
            price = return_flight["price"]
        else:
            price = flight["price"]

        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                               INSERT INTO bookmarks (
                               user_id,
                               flight_type,
                               route,
                               airline,
                               departure_date,
                               departure_time,
                               arrival_date,
                               arrival_time,
                               return_flight_departure_date,
                               return_flight_departure_time,
                               return_flight_arrival_date,
                               return_flight_arrival_time,
                               departure_stops,
                               return_stops,
                               departure_duration,
                               return_duration,
                               price,
                               currency
                               ) VALUES (
                               $1, $2, $3, $4, $5, $6, $7, $8,
                               $9, $10, $11, $12,
                               $13, $14, $15, $16,
                               $17, $18
                               )
                               """,
                               user_id,
                               flight_type,
                               flight["airports"],
                               flight["airline"],
                               flight["departure_date"],
                               flight["departure_time"],
                               flight["arrival_date"],
                               flight["arrival_time"],
                               rf.get("departure_date"),
                               rf.get("departure_time"),
                               rf.get("arrival_date"),
                               rf.get("arrival_time"),
                               flight["nr_of_stops"],
                               rf.get("nr_of_stops"),
                               flight["flight_duration"],
                               rf.get("flight_duration"),
                               price,
                               flight["currency"]
                               )
    
    async def get_user_bookmarks(self, user_id: int, limit: int = 10):
        if self.connection_pool is None:
            await self.connect()
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM bookmarks
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2;
            """, user_id, limit)
        return rows
    
    async def delete_bookmark(self, bookmark_id: int):
        if self.connection_pool is None:
            await self.connect()
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM bookmarks WHERE id = $1
            """, bookmark_id)