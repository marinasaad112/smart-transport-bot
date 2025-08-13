# db.py
import asyncpg
from config import DATABASE_URL

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    
    # جدول العملاء
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE,
            subscription_type TEXT,
            full_name TEXT,
            phone_number TEXT,
            city TEXT,
            neighborhood TEXT
        )
    """)

    # جدول الكباتن
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS captains (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE,
            subscription_type TEXT,
            full_name TEXT,
            phone_number TEXT,
            car_type TEXT,
            seats INTEGER,
            city TEXT,
            neighborhoods TEXT[] -- مصفوفة من ٣ أحياء
        )
    """)
 # جدول معلومات السيارة المرتبط بالكابتن
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles_info (
            id SERIAL PRIMARY KEY,
            captain_id BIGINT REFERENCES captains(user_id) ON DELETE CASCADE,
            plate_number TEXT NOT NULL,
            car_model TEXT,
            car_color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # جدول المطابقات
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            client_id BIGINT,
            captain_id BIGINT,
            status TEXT
        )
    """)

    await conn.close()

async def get_conn():
    return await asyncpg.connect(DATABASE_URL)
