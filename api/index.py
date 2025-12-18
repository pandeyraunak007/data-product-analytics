"""
FastAPI application for Data Product Analytics Platform
Supports both local (SQLite + Foundry Local) and Vercel (PostgreSQL + OpenAI) deployment
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

# Detect environment
IS_VERCEL = os.environ.get("VERCEL", False)
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Database setup - PostgreSQL for Vercel, SQLite for local
if DATABASE_URL:
    # PostgreSQL (Vercel/Supabase)
    import psycopg2
    from psycopg2.extras import RealDictCursor

    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    def get_cursor(conn):
        return conn.cursor(cursor_factory=RealDictCursor)

    # PostgreSQL date functions
    DATE_NOW = "CURRENT_DATE"
    def date_offset(days):
        return f"CURRENT_DATE - INTERVAL '{abs(days)} days'"

    DB_TYPE = "postgresql"
else:
    # SQLite (Local development)
    import sqlite3

    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analytics.db")

    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def get_cursor(conn):
        return conn.cursor()

    # SQLite date functions
    DATE_NOW = "DATE('now')"
    def date_offset(days):
        return f"DATE('now', '{days} days')"

    DB_TYPE = "sqlite"

# AI Client setup
if GROQ_API_KEY:
    # Groq API (Vercel) - Free tier with fast inference
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY
    )
    AI_MODEL = "llama-3.3-70b-versatile"  # Free, fast, high quality
else:
    # Foundry Local (Local development)
    client = OpenAI(
        base_url="http://127.0.0.1:51122/v1",
        api_key="not-needed"
    )
    AI_MODEL = "Phi-4-mini-instruct-generic-cpu:5"

app = FastAPI(title="Data Product Analytics Platform")

# Pydantic models
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


# Database initialization
def init_db():
    conn = get_db()
    cursor = get_cursor(conn)

    if DB_TYPE == "postgresql":
        # PostgreSQL schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_products (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                owner TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                user_type TEXT DEFAULT 'analyst',
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_events (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES data_products(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                event_type TEXT DEFAULT 'query',
                tables_accessed TEXT,
                query_duration_ms INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                owner TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                user_type TEXT DEFAULT 'analyst',
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
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

    conn.commit()
    conn.close()


def seed_demo_data():
    """Seed database with demo data"""
    conn = get_db()
    cursor = get_cursor(conn)

    # Check if data exists
    cursor.execute("SELECT COUNT(*) FROM data_products")
    result = cursor.fetchone()
    count = result[0] if isinstance(result, (list, tuple)) else result.get('count', 0)

    if count > 0:
        conn.close()
        return

    import random

    # SaaS Data Products
    products = [
        ("Customer 360", "Unified customer view across all touchpoints", "Data Team"),
        ("Revenue Dashboard", "Real-time ARR, MRR, and revenue metrics", "Finance"),
        ("Sales Pipeline", "Deal tracking, forecasting, and conversion metrics", "Sales Ops"),
        ("Product Analytics", "Feature adoption, user journeys, and engagement", "Product Team"),
        ("Marketing Attribution", "Multi-touch attribution and campaign ROI", "Marketing Analytics"),
        ("Campaign Performance", "Email, ads, and content marketing metrics", "Growth Team"),
        ("SEO Dashboard", "Organic traffic, rankings, and keyword analysis", "Content Team"),
        ("Social Media Analytics", "Engagement, reach, and sentiment analysis", "Brand Team"),
        ("Support Ticket Analytics", "CSAT, response times, and ticket trends", "Customer Success"),
        ("Inventory Dashboard", "Stock levels, supply chain, and logistics", "Operations"),
        ("Vendor Scorecard", "Supplier performance and contract metrics", "Procurement"),
        ("HR Analytics", "Headcount, attrition, and hiring funnel", "People Team"),
        ("Employee Engagement", "Survey results and team health scores", "HR"),
        ("API Usage Monitor", "Endpoint usage, latency, and error rates", "Engineering"),
        ("Infrastructure Costs", "Cloud spend, resource utilization", "DevOps"),
        ("Security Dashboard", "Threats, vulnerabilities, and compliance", "Security Team"),
        ("Executive KPI Board", "Company OKRs and strategic metrics", "Leadership"),
        ("Board Reporting", "Investor metrics and quarterly summaries", "CEO Office"),
    ]

    for p in products:
        if DB_TYPE == "postgresql":
            cursor.execute("INSERT INTO data_products (name, description, owner) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING", p)
        else:
            cursor.execute("INSERT OR IGNORE INTO data_products (name, description, owner) VALUES (?, ?, ?)", p)

    # Users
    users = [
        ("ceo@company.com", "executive", "Leadership"),
        ("cfo@company.com", "executive", "Finance"),
        ("cto@company.com", "executive", "Engineering"),
        ("alice.chen@company.com", "data_scientist", "Data Science"),
        ("bob.kumar@company.com", "data_analyst", "Data Science"),
        ("emma.wilson@company.com", "sales_manager", "Sales"),
        ("frank.jones@company.com", "account_exec", "Sales"),
        ("ivy.garcia@company.com", "marketing_manager", "Marketing"),
        ("jack.martinez@company.com", "growth_analyst", "Marketing"),
        ("mia.jackson@company.com", "product_manager", "Product"),
        ("peter.martin@company.com", "engineer", "Engineering"),
        ("uma.walker@company.com", "cs_manager", "Customer Success"),
    ]

    for u in users:
        if DB_TYPE == "postgresql":
            cursor.execute("INSERT INTO users (user_id, user_type, department) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING", u)
        else:
            cursor.execute("INSERT OR IGNORE INTO users (user_id, user_type, department) VALUES (?, ?, ?)", u)

    conn.commit()

    # Get product and user IDs
    cursor.execute("SELECT id, name FROM data_products")
    products_data = cursor.fetchall()

    cursor.execute("SELECT id, user_id FROM users")
    users_data = cursor.fetchall()

    # Generate usage data for last 30 days
    for day_offset in range(30, 0, -1):
        event_date = datetime.now() - timedelta(days=day_offset)
        is_weekend = event_date.weekday() >= 5

        for product in products_data:
            if isinstance(product, dict):
                product_id, product_name = product['id'], product['name']
            else:
                product_id, product_name = product[0], product[1]

            # Skip some products on weekends
            if is_weekend and random.random() > 0.3:
                continue

            num_users = random.randint(2, min(8, len(users_data)))
            active_users = random.sample(list(users_data), num_users)

            for user in active_users:
                if isinstance(user, dict):
                    user_db_id = user['id']
                else:
                    user_db_id = user[0]

                num_queries = random.randint(1, 10)

                for _ in range(num_queries):
                    query_duration = random.randint(100, 3000)
                    hour = random.randint(8, 18)
                    event_time = event_date.replace(
                        hour=hour,
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )

                    if DB_TYPE == "postgresql":
                        cursor.execute('''
                            INSERT INTO usage_events (product_id, user_id, event_type, query_duration_ms, timestamp)
                            VALUES (%s, %s, %s, %s, %s)
                        ''', (product_id, user_db_id, "query", query_duration, event_time))
                    else:
                        cursor.execute('''
                            INSERT INTO usage_events (product_id, user_id, event_type, query_duration_ms, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (product_id, user_db_id, "query", query_duration, event_time))

    conn.commit()
    conn.close()
    print("Demo data seeded successfully!")


# Analytics functions
def get_dau_wau_mau(product_id: int) -> dict:
    conn = get_db()
    cursor = get_cursor(conn)

    if DB_TYPE == "postgresql":
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s AND DATE(timestamp) = CURRENT_DATE
        ''', (product_id,))
        dau = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s AND DATE(timestamp) >= CURRENT_DATE - INTERVAL '7 days'
        ''', (product_id,))
        wau = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s AND DATE(timestamp) >= CURRENT_DATE - INTERVAL '30 days'
        ''', (product_id,))
        mau = cursor.fetchone()[0] or 0
    else:
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = ? AND DATE(timestamp) = DATE('now')
        ''', (product_id,))
        dau = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
        ''', (product_id,))
        wau = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-30 days')
        ''', (product_id,))
        mau = cursor.fetchone()[0] or 0

    conn.close()
    return {"dau": dau, "wau": wau, "mau": mau}


def calculate_adoption_score(product_id: int, total_users: int) -> float:
    if total_users == 0:
        return 0
    metrics = get_dau_wau_mau(product_id)
    adoption = (metrics["mau"] / total_users) * 100
    return min(100, round(adoption, 1))


def calculate_stickiness_score(product_id: int) -> float:
    metrics = get_dau_wau_mau(product_id)
    if metrics["mau"] == 0:
        return 0
    stickiness = (metrics["dau"] / metrics["mau"]) * 100
    normalized = min(100, (stickiness / 20) * 100)
    return round(normalized, 1)


def calculate_abandonment_risk(product_id: int) -> float:
    conn = get_db()
    cursor = get_cursor(conn)

    if DB_TYPE == "postgresql":
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s AND DATE(timestamp) >= CURRENT_DATE - INTERVAL '7 days'
        ''', (product_id,))
        recent_users = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s
            AND DATE(timestamp) >= CURRENT_DATE - INTERVAL '14 days'
            AND DATE(timestamp) < CURRENT_DATE - INTERVAL '7 days'
        ''', (product_id,))
        previous_users = cursor.fetchone()[0] or 0
    else:
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
        ''', (product_id,))
        recent_users = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = ?
            AND DATE(timestamp) >= DATE('now', '-14 days')
            AND DATE(timestamp) < DATE('now', '-7 days')
        ''', (product_id,))
        previous_users = cursor.fetchone()[0] or 0

    conn.close()

    if previous_users == 0:
        return 50

    decline = ((previous_users - recent_users) / previous_users) * 100
    return max(0, min(100, round(decline, 1)))


def get_usage_trend(product_id: int) -> str:
    risk = calculate_abandonment_risk(product_id)
    if risk < 20:
        return "growing"
    elif risk < 40:
        return "stable"
    return "declining"


def get_query_frequency(product_id: int, days: int = 30) -> list:
    conn = get_db()
    cursor = get_cursor(conn)

    if DB_TYPE == "postgresql":
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM usage_events
            WHERE product_id = %s AND DATE(timestamp) >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (product_id, days))
    else:
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM usage_events
            WHERE product_id = ? AND DATE(timestamp) >= DATE('now', ?)
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (product_id, f'-{days} days'))

    results = []
    for row in cursor.fetchall():
        if isinstance(row, dict):
            results.append({"date": str(row['date']), "count": row['count']})
        else:
            results.append({"date": str(row[0]), "count": row[1]})

    conn.close()
    return results


def get_all_product_scores() -> list:
    conn = get_db()
    cursor = get_cursor(conn)

    cursor.execute("SELECT COUNT(*) FROM users")
    result = cursor.fetchone()
    total_users = result[0] if isinstance(result, (list, tuple)) else result.get('count', 0)

    cursor.execute("SELECT id, name, description, owner FROM data_products")
    products = cursor.fetchall()

    scores = []
    for product in products:
        if isinstance(product, dict):
            product_id, name, description, owner = product['id'], product['name'], product['description'], product['owner']
        else:
            product_id, name, description, owner = product

        metrics = get_dau_wau_mau(product_id)

        scores.append({
            "id": product_id,
            "name": name,
            "description": description,
            "owner": owner,
            "dau": metrics["dau"],
            "wau": metrics["wau"],
            "mau": metrics["mau"],
            "adoption_score": calculate_adoption_score(product_id, total_users),
            "stickiness_score": calculate_stickiness_score(product_id),
            "abandonment_risk": calculate_abandonment_risk(product_id),
            "trend": get_usage_trend(product_id)
        })

    conn.close()
    return sorted(scores, key=lambda x: x["mau"], reverse=True)


def get_product_details(product_id: int) -> dict:
    conn = get_db()
    cursor = get_cursor(conn)

    cursor.execute("SELECT COUNT(*) FROM users")
    result = cursor.fetchone()
    total_users = result[0] if isinstance(result, (list, tuple)) else result.get('count', 0)

    if DB_TYPE == "postgresql":
        cursor.execute("SELECT id, name, description, owner FROM data_products WHERE id = %s", (product_id,))
    else:
        cursor.execute("SELECT id, name, description, owner FROM data_products WHERE id = ?", (product_id,))

    product = cursor.fetchone()
    if not product:
        conn.close()
        return None

    if isinstance(product, dict):
        product_id, name, description, owner = product['id'], product['name'], product['description'], product['owner']
    else:
        product_id, name, description, owner = product

    metrics = get_dau_wau_mau(product_id)

    details = {
        "id": product_id,
        "name": name,
        "description": description,
        "owner": owner,
        "dau": metrics["dau"],
        "wau": metrics["wau"],
        "mau": metrics["mau"],
        "adoption_score": calculate_adoption_score(product_id, total_users),
        "stickiness_score": calculate_stickiness_score(product_id),
        "abandonment_risk": calculate_abandonment_risk(product_id),
        "trend": get_usage_trend(product_id),
        "query_frequency": get_query_frequency(product_id)
    }

    conn.close()
    return details


# Initialize on startup
@app.on_event("startup")
async def startup():
    init_db()
    seed_demo_data()


# Mount static files (only for local development)
if not IS_VERCEL:
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")
    if os.path.exists(static_path):
        with open(static_path, "r") as f:
            return f.read()
    return "<h1>Data Product Analytics Platform</h1><p>Static files not found.</p>"


@app.get("/api/products")
async def get_products():
    return get_all_product_scores()


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    details = get_product_details(product_id)
    if not details:
        raise HTTPException(status_code=404, detail="Product not found")
    return details


@app.post("/api/track")
async def track_usage(event: UsageEvent):
    conn = get_db()
    cursor = get_cursor(conn)

    # Get or create product
    if DB_TYPE == "postgresql":
        cursor.execute("SELECT id FROM data_products WHERE name = %s", (event.product_name,))
    else:
        cursor.execute("SELECT id FROM data_products WHERE name = ?", (event.product_name,))

    product = cursor.fetchone()
    if not product:
        if DB_TYPE == "postgresql":
            cursor.execute("INSERT INTO data_products (name) VALUES (%s) RETURNING id", (event.product_name,))
            product_id = cursor.fetchone()[0]
        else:
            cursor.execute("INSERT INTO data_products (name) VALUES (?)", (event.product_name,))
            product_id = cursor.lastrowid
    else:
        product_id = product[0] if isinstance(product, (list, tuple)) else product['id']

    # Get or create user
    if DB_TYPE == "postgresql":
        cursor.execute("SELECT id FROM users WHERE user_id = %s", (event.user_id,))
    else:
        cursor.execute("SELECT id FROM users WHERE user_id = ?", (event.user_id,))

    user = cursor.fetchone()
    if not user:
        if DB_TYPE == "postgresql":
            cursor.execute("INSERT INTO users (user_id) VALUES (%s) RETURNING id", (event.user_id,))
            user_id = cursor.fetchone()[0]
        else:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (event.user_id,))
            user_id = cursor.lastrowid
    else:
        user_id = user[0] if isinstance(user, (list, tuple)) else user['id']

    # Record event
    tables_json = json.dumps(event.tables_accessed) if event.tables_accessed else None
    if DB_TYPE == "postgresql":
        cursor.execute('''
            INSERT INTO usage_events (product_id, user_id, event_type, tables_accessed, query_duration_ms)
            VALUES (%s, %s, %s, %s, %s)
        ''', (product_id, user_id, event.event_type, tables_json, event.query_duration_ms))
    else:
        cursor.execute('''
            INSERT INTO usage_events (product_id, user_id, event_type, tables_accessed, query_duration_ms)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, user_id, event.event_type, tables_json, event.query_duration_ms))

    conn.commit()
    conn.close()
    return {"status": "success", "message": "Event tracked"}


@app.get("/api/summary")
async def get_summary():
    conn = get_db()
    cursor = get_cursor(conn)

    cursor.execute("SELECT COUNT(*) FROM data_products")
    result = cursor.fetchone()
    total_products = result[0] if isinstance(result, (list, tuple)) else result.get('count', 0)

    if DB_TYPE == "postgresql":
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_events WHERE DATE(timestamp) >= CURRENT_DATE - INTERVAL '30 days'")
    else:
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_events WHERE DATE(timestamp) >= DATE('now', '-30 days')")
    result = cursor.fetchone()
    active_users = result[0] if isinstance(result, (list, tuple)) else result.get('count', 0)

    if DB_TYPE == "postgresql":
        cursor.execute("SELECT COUNT(*) FROM usage_events WHERE DATE(timestamp) >= CURRENT_DATE - INTERVAL '30 days'")
    else:
        cursor.execute("SELECT COUNT(*) FROM usage_events WHERE DATE(timestamp) >= DATE('now', '-30 days')")
    result = cursor.fetchone()
    total_queries = result[0] if isinstance(result, (list, tuple)) else result.get('count', 0)

    if DB_TYPE == "postgresql":
        cursor.execute("SELECT COUNT(*) FROM usage_events WHERE DATE(timestamp) = CURRENT_DATE")
    else:
        cursor.execute("SELECT COUNT(*) FROM usage_events WHERE DATE(timestamp) = DATE('now')")
    result = cursor.fetchone()
    queries_today = result[0] if isinstance(result, (list, tuple)) else result.get('count', 0)

    conn.close()

    scores = get_all_product_scores()
    avg_adoption = sum(p["adoption_score"] for p in scores) / len(scores) if scores else 0
    avg_stickiness = sum(p["stickiness_score"] for p in scores) / len(scores) if scores else 0
    at_risk = len([p for p in scores if p["abandonment_risk"] > 50])

    return {
        "total_products": total_products,
        "active_users_30d": active_users,
        "total_queries_30d": total_queries,
        "queries_today": queries_today,
        "avg_adoption_score": round(avg_adoption, 1),
        "avg_stickiness_score": round(avg_stickiness, 1),
        "products_at_risk": at_risk
    }


@app.post("/api/insights")
async def get_ai_insights(request: Request):
    data = await request.json()
    product_id = data.get("product_id")

    if product_id:
        details = get_product_details(product_id)
        if not details:
            raise HTTPException(status_code=404, detail="Product not found")
        context = details
    else:
        summary = await get_summary()
        context = {
            "summary": summary,
            "products": get_all_product_scores()
        }

    prompt = f"""You are a Data Product Manager analyzing usage analytics. Based on the following data, provide 3-4 actionable insights.

Data:
{json.dumps(context, indent=2)}

Focus on: adoption opportunities, engagement improvements, risk mitigation.
Be specific and actionable. Format as bullet points."""

    async def generate():
        try:
            stream = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful data product analytics expert."},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                max_tokens=500
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    product_id = data.get("product_id")

    if product_id:
        details = get_product_details(product_id)
        if not details:
            raise HTTPException(status_code=404, detail="Product not found")
        context = {
            "name": details.get("name"),
            "adoption": details.get("adoption_score"),
            "stickiness": details.get("stickiness_score"),
            "risk": details.get("abandonment_risk"),
            "dau": details.get("dau"),
            "mau": details.get("mau"),
            "trend": details.get("trend")
        }
    else:
        products = get_all_product_scores()
        context = [{"name": p["name"], "adoption": p["adoption_score"],
                    "risk": p["abandonment_risk"], "trend": p["trend"]} for p in products]

    system_prompt = f"""You are a data product analytics assistant. Be concise and specific.

Data: {json.dumps(context)}

Answer based on this data. Use numbers when relevant."""

    async def generate():
        try:
            stream = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                stream=True,
                max_tokens=250,
                temperature=0.7
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/chat/stats")
async def get_chat_stats():
    return {
        "total_conversations": 0,
        "memory_enabled": False,
        "ai_model": AI_MODEL,
        "database": DB_TYPE
    }


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
