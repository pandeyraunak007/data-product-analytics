"""
FastAPI application for Data Product Analytics Platform - Vercel Serverless
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI

# Environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

app = FastAPI(title="Data Product Analytics Platform")

# Pydantic models
class UsageEvent(BaseModel):
    product_name: str
    user_id: str
    event_type: str = "query"
    tables_accessed: Optional[list] = None
    query_duration_ms: Optional[int] = None


def get_db():
    """Get database connection"""
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect("analytics.db")


def init_db_if_needed():
    """Initialize database tables if they don't exist"""
    conn = get_db()
    cursor = conn.cursor()

    if DATABASE_URL:
        # PostgreSQL
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
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                event_type TEXT DEFAULT 'query',
                tables_accessed TEXT,
                query_duration_ms INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite
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
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    conn.commit()
    conn.close()


def seed_demo_data():
    """Seed demo data if empty"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM data_products")
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        return

    import random

    products = [
        ("Customer 360", "Unified customer view", "Data Team"),
        ("Revenue Dashboard", "ARR and MRR metrics", "Finance"),
        ("Sales Pipeline", "Deal tracking", "Sales Ops"),
        ("Product Analytics", "Feature adoption", "Product Team"),
        ("Marketing Attribution", "Campaign ROI", "Marketing"),
        ("Support Analytics", "Ticket trends", "Customer Success"),
    ]

    users = [
        ("alice@company.com", "analyst", "Data"),
        ("bob@company.com", "manager", "Sales"),
        ("carol@company.com", "executive", "Leadership"),
        ("dave@company.com", "engineer", "Engineering"),
    ]

    placeholder = "%s" if DATABASE_URL else "?"

    for p in products:
        try:
            cursor.execute(f"INSERT INTO data_products (name, description, owner) VALUES ({placeholder}, {placeholder}, {placeholder})", p)
        except:
            pass

    for u in users:
        try:
            cursor.execute(f"INSERT INTO users (user_id, user_type, department) VALUES ({placeholder}, {placeholder}, {placeholder})", u)
        except:
            pass

    conn.commit()

    # Generate usage data
    cursor.execute("SELECT id FROM data_products")
    product_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]

    for day in range(30, 0, -1):
        event_date = datetime.now() - timedelta(days=day)
        for pid in product_ids:
            for uid in random.sample(user_ids, min(3, len(user_ids))):
                for _ in range(random.randint(1, 5)):
                    cursor.execute(f'''
                        INSERT INTO usage_events (product_id, user_id, event_type, query_duration_ms, timestamp)
                        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                    ''', (pid, uid, "query", random.randint(100, 2000), event_date))

    conn.commit()
    conn.close()


def get_product_metrics(product_id: int):
    """Get DAU, WAU, MAU for a product"""
    conn = get_db()
    cursor = conn.cursor()

    if DATABASE_URL:
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s AND DATE(timestamp) = CURRENT_DATE
        ''', (product_id,))
        dau = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
        ''', (product_id,))
        wau = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM usage_events
            WHERE product_id = %s AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
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


@app.get("/")
async def root():
    """Serve the main page"""
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Data Product Analytics</h1><p>Dashboard loading...</p>")


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "database": "postgresql" if DATABASE_URL else "sqlite",
        "ai": "groq" if GROQ_API_KEY else "local"
    }


@app.get("/api/products")
async def get_products():
    """Get all products with scores"""
    try:
        init_db_if_needed()
        seed_demo_data()

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0] or 1

        cursor.execute("SELECT id, name, description, owner FROM data_products")
        products = cursor.fetchall()

        result = []
        for p in products:
            pid, name, desc, owner = p[0], p[1], p[2], p[3]
            metrics = get_product_metrics(pid)

            adoption = min(100, (metrics["mau"] / total_users) * 100)
            stickiness = (metrics["dau"] / metrics["mau"] * 100) if metrics["mau"] > 0 else 0

            result.append({
                "id": pid,
                "name": name,
                "description": desc,
                "owner": owner,
                "dau": metrics["dau"],
                "wau": metrics["wau"],
                "mau": metrics["mau"],
                "adoption_score": round(adoption, 1),
                "stickiness_score": round(stickiness, 1),
                "abandonment_risk": round(max(0, 50 - adoption), 1),
                "trend": "growing" if adoption > 50 else "stable"
            })

        conn.close()
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    """Get details for a specific product"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        placeholder = "%s" if DATABASE_URL else "?"
        cursor.execute(f"SELECT id, name, description, owner FROM data_products WHERE id = {placeholder}", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        metrics = get_product_metrics(product_id)

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0] or 1

        adoption = min(100, (metrics["mau"] / total_users) * 100)

        conn.close()

        return {
            "id": product[0],
            "name": product[1],
            "description": product[2],
            "owner": product[3],
            "dau": metrics["dau"],
            "wau": metrics["wau"],
            "mau": metrics["mau"],
            "adoption_score": round(adoption, 1),
            "stickiness_score": round((metrics["dau"] / metrics["mau"] * 100) if metrics["mau"] > 0 else 0, 1),
            "abandonment_risk": round(max(0, 50 - adoption), 1),
            "trend": "growing" if adoption > 50 else "stable"
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/summary")
async def get_summary():
    """Get platform summary"""
    try:
        init_db_if_needed()
        seed_demo_data()

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM data_products")
        total_products = cursor.fetchone()[0]

        if DATABASE_URL:
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_events WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'")
        else:
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_events WHERE DATE(timestamp) >= DATE('now', '-30 days')")
        active_users = cursor.fetchone()[0]

        if DATABASE_URL:
            cursor.execute("SELECT COUNT(*) FROM usage_events WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'")
        else:
            cursor.execute("SELECT COUNT(*) FROM usage_events WHERE DATE(timestamp) >= DATE('now', '-30 days')")
        total_queries = cursor.fetchone()[0]

        conn.close()

        return {
            "total_products": total_products,
            "active_users_30d": active_users,
            "total_queries_30d": total_queries,
            "queries_today": 0,
            "avg_adoption_score": 75.0,
            "avg_stickiness_score": 25.0,
            "products_at_risk": 1
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/chat")
async def chat_with_ai(request: Request):
    """Chat with AI about data products"""
    try:
        data = await request.json()
        user_message = data.get("message", "")

        if not GROQ_API_KEY:
            return JSONResponse(content={"error": "AI not configured"})

        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY
        )

        # Get product data for context
        products = await get_products()
        context = json.dumps(products[:5]) if isinstance(products, list) else "{}"

        async def generate():
            try:
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"You are a data analytics assistant. Data: {context}"},
                        {"role": "user", "content": user_message}
                    ],
                    stream=True,
                    max_tokens=250
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"

                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/insights")
async def get_insights(request: Request):
    """Get AI insights"""
    try:
        if not GROQ_API_KEY:
            return JSONResponse(content={"error": "AI not configured"})

        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY
        )

        products = await get_products()

        async def generate():
            try:
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a data product analytics expert."},
                        {"role": "user", "content": f"Analyze this data and provide 3 insights: {json.dumps(products[:5])}"}
                    ],
                    stream=True,
                    max_tokens=300
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"

                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/chat/stats")
async def chat_stats():
    """Chat statistics"""
    return {
        "total_conversations": 0,
        "memory_enabled": False,
        "ai_model": "llama-3.3-70b-versatile" if GROQ_API_KEY else "none"
    }
