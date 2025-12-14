from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from openai import OpenAI
import json

from models import init_db, seed_demo_data, UsageEvent, get_db
from analytics import (
    get_all_product_scores,
    get_product_details,
    get_query_frequency,
    get_retention_cohorts
)
from vector_store import (
    store_conversation,
    get_relevant_conversations,
    store_data_product_info,
    get_conversation_count,
    persist,
    is_available as chromadb_available
)

app = FastAPI(title="Data Product Usage Analytics Platform")

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()
    seed_demo_data()

# Foundry Local API client for AI insights
client = OpenAI(
    base_url="http://127.0.0.1:51122/v1",
    api_key="not-needed"
)
MODEL = "Phi-4-mini-instruct-generic-cpu:5"

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r") as f:
        return f.read()


@app.get("/api/products")
async def get_products():
    """Get all data products with their scores"""
    return get_all_product_scores()


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    """Get detailed analytics for a specific product"""
    details = get_product_details(product_id)
    if not details:
        raise HTTPException(status_code=404, detail="Product not found")
    return details


@app.post("/api/track")
async def track_usage(event: UsageEvent):
    """Track a usage event"""
    conn = get_db()
    cursor = conn.cursor()

    # Get or create product
    cursor.execute("SELECT id FROM data_products WHERE name = ?", (event.product_name,))
    product = cursor.fetchone()
    if not product:
        cursor.execute("INSERT INTO data_products (name) VALUES (?)", (event.product_name,))
        product_id = cursor.lastrowid
    else:
        product_id = product[0]

    # Get or create user
    cursor.execute("SELECT id FROM users WHERE user_id = ?", (event.user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (event.user_id,))
        user_id = cursor.lastrowid
    else:
        user_id = user[0]

    # Record event
    cursor.execute('''
        INSERT INTO usage_events (product_id, user_id, event_type, tables_accessed, query_duration_ms)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        product_id,
        user_id,
        event.event_type,
        json.dumps(event.tables_accessed) if event.tables_accessed else None,
        event.query_duration_ms
    ))

    conn.commit()
    conn.close()

    return {"status": "success", "message": "Event tracked"}


@app.get("/api/summary")
async def get_summary():
    """Get overall platform summary"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM data_products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_events WHERE DATE(timestamp) >= DATE('now', '-30 days')")
    active_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usage_events WHERE DATE(timestamp) >= DATE('now', '-30 days')")
    total_queries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usage_events WHERE DATE(timestamp) = DATE('now')")
    queries_today = cursor.fetchone()[0]

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
    """Get AI-powered insights using Foundry Local"""
    data = await request.json()
    product_id = data.get("product_id")

    if product_id:
        details = get_product_details(product_id)
        if not details:
            raise HTTPException(status_code=404, detail="Product not found")
        context = details
    else:
        context = {
            "summary": await get_summary(),
            "products": get_all_product_scores()
        }

    prompt = f"""You are a Data Product Manager analyzing usage analytics. Based on the following data, provide 3-4 actionable insights and recommendations.

Data:
{json.dumps(context, indent=2)}

Focus on:
1. Adoption opportunities
2. Engagement improvements
3. Risk mitigation for declining products
4. User behavior patterns

Be specific and actionable. Format as bullet points."""

    async def generate():
        try:
            stream = client.chat.completions.create(
                model=MODEL,
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
    """Chat with AI about data products with conversation memory"""
    data = await request.json()
    user_message = data.get("message", "")
    product_id = data.get("product_id")

    # Build context from data
    if product_id:
        details = get_product_details(product_id)
        if not details:
            raise HTTPException(status_code=404, detail="Product not found")
        context = details
    else:
        summary = await get_summary()
        products = get_all_product_scores()
        context = {
            "summary": summary,
            "products": products
        }

    # Retrieve relevant past conversations from ChromaDB
    relevant_conversations = get_relevant_conversations(user_message, n_results=3)
    conversation_context = ""
    if relevant_conversations:
        conversation_context = "\n\nRelevant past conversations:\n"
        for conv in relevant_conversations:
            conversation_context += f"---\n{conv['content']}\n"

    system_prompt = f"""You are an AI assistant specialized in data product analytics. You help users understand their data products' usage, adoption, and health metrics.

Here is the current data about the data products:
{json.dumps(context, indent=2)}
{conversation_context}

Answer the user's questions based on this data and any relevant past conversations. Be concise, helpful, and provide specific numbers when relevant. If asked about a specific product, focus on that product's metrics. Remember context from previous conversations when applicable."""

    # Collect full response for storing in ChromaDB
    full_response = []

    async def generate():
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                stream=True,
                max_tokens=500
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response.append(content)
                    yield f"data: {json.dumps({'content': content})}\n\n"

            # Store the conversation in ChromaDB after completion
            complete_response = "".join(full_response)
            if complete_response:
                store_conversation(
                    user_message=user_message,
                    assistant_response=complete_response,
                    metadata={"product_id": str(product_id) if product_id else "all"}
                )
                persist()

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/chat/stats")
async def get_chat_stats():
    """Get chat statistics"""
    return {
        "total_conversations": get_conversation_count(),
        "memory_enabled": chromadb_available()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
