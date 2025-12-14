from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import sqlite3
import json

DB_PATH = "analytics.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Data Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            owner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            user_type TEXT DEFAULT 'analyst',
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Usage Events table - tracks every query/access
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            event_type TEXT DEFAULT 'query',
            tables_accessed TEXT,
            query_duration_ms INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES data_products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Daily aggregates for faster analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            date DATE NOT NULL,
            unique_users INTEGER DEFAULT 0,
            total_queries INTEGER DEFAULT 0,
            avg_query_duration_ms REAL,
            UNIQUE(product_id, date),
            FOREIGN KEY (product_id) REFERENCES data_products(id)
        )
    ''')

    conn.commit()
    conn.close()


# Pydantic models for API
class DataProduct(BaseModel):
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None


class User(BaseModel):
    user_id: str
    user_type: str = "analyst"
    department: Optional[str] = None


class UsageEvent(BaseModel):
    product_name: str
    user_id: str
    event_type: str = "query"
    tables_accessed: Optional[list] = None
    query_duration_ms: Optional[int] = None


class ProductScore(BaseModel):
    product_name: str
    adoption_score: float
    stickiness_score: float
    abandonment_risk: float
    dau: int
    wau: int
    mau: int
    trend: str


def seed_demo_data():
    """Seed database with demo data for demonstration"""
    conn = get_db()
    cursor = conn.cursor()

    # Check if data exists
    cursor.execute("SELECT COUNT(*) FROM data_products")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Demo data products
    products = [
        ("Customer 360", "Unified customer view across all touchpoints", "Data Team"),
        ("Sales Pipeline", "Real-time sales funnel and conversion metrics", "Sales Ops"),
        ("Marketing Attribution", "Multi-touch attribution model", "Marketing Analytics"),
        ("Product Analytics", "User behavior and feature adoption", "Product Team"),
        ("Financial Reports", "P&L, revenue, and cost analysis", "Finance"),
        ("Inventory Dashboard", "Stock levels and supply chain metrics", "Operations"),
    ]

    for p in products:
        cursor.execute("INSERT OR IGNORE INTO data_products (name, description, owner) VALUES (?, ?, ?)", p)

    # Demo users
    users = [
        ("alice@company.com", "analyst", "Marketing"),
        ("bob@company.com", "data_scientist", "Data Science"),
        ("carol@company.com", "executive", "Leadership"),
        ("dave@company.com", "analyst", "Sales"),
        ("eve@company.com", "engineer", "Engineering"),
        ("frank@company.com", "analyst", "Finance"),
        ("grace@company.com", "pm", "Product"),
        ("henry@company.com", "analyst", "Operations"),
    ]

    for u in users:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, user_type, department) VALUES (?, ?, ?)", u)

    conn.commit()

    # Generate usage events for the past 30 days
    import random

    cursor.execute("SELECT id, name FROM data_products")
    products = cursor.fetchall()

    cursor.execute("SELECT id, user_id FROM users")
    users = cursor.fetchall()

    # Different usage patterns for different products
    usage_patterns = {
        "Customer 360": {"base_users": 6, "queries_per_user": 8, "trend": "growing"},
        "Sales Pipeline": {"base_users": 5, "queries_per_user": 12, "trend": "stable"},
        "Marketing Attribution": {"base_users": 3, "queries_per_user": 5, "trend": "declining"},
        "Product Analytics": {"base_users": 7, "queries_per_user": 15, "trend": "growing"},
        "Financial Reports": {"base_users": 4, "queries_per_user": 3, "trend": "stable"},
        "Inventory Dashboard": {"base_users": 2, "queries_per_user": 2, "trend": "declining"},
    }

    tables = ["customers", "orders", "transactions", "events", "sessions", "users", "products", "campaigns"]

    for day_offset in range(30, 0, -1):
        event_date = datetime.now() - timedelta(days=day_offset)

        for product in products:
            product_id, product_name = product
            pattern = usage_patterns.get(product_name, {"base_users": 3, "queries_per_user": 5, "trend": "stable"})

            # Adjust based on trend
            trend_multiplier = 1.0
            if pattern["trend"] == "growing":
                trend_multiplier = 0.5 + (0.5 * (30 - day_offset) / 30)
            elif pattern["trend"] == "declining":
                trend_multiplier = 1.0 - (0.5 * (30 - day_offset) / 30)

            # Weekend reduction
            if event_date.weekday() >= 5:
                trend_multiplier *= 0.3

            num_users = int(pattern["base_users"] * trend_multiplier * random.uniform(0.7, 1.3))
            num_users = max(1, min(num_users, len(users)))

            active_users = random.sample(users, num_users)

            for user in active_users:
                user_id = user[0]
                num_queries = int(pattern["queries_per_user"] * random.uniform(0.5, 1.5))

                for _ in range(num_queries):
                    tables_accessed = random.sample(tables, random.randint(1, 3))
                    query_duration = random.randint(100, 5000)

                    # Random time during the day
                    event_time = event_date.replace(
                        hour=random.randint(8, 18),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )

                    cursor.execute('''
                        INSERT INTO usage_events
                        (product_id, user_id, event_type, tables_accessed, query_duration_ms, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (product_id, user_id, "query", json.dumps(tables_accessed), query_duration, event_time))

    conn.commit()
    conn.close()
    print("Demo data seeded successfully!")
