# Data Product Analytics Platform - Complete Guide

A comprehensive guide to understanding the Data Product Analytics Platform, its architecture, and how all the pieces work together.

---

## Table of Contents

1. [What is this Project?](#what-is-this-project)
2. [Architecture Overview](#architecture-overview)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Key Features Explained](#key-features-explained)
6. [Technology Stack](#technology-stack)
7. [How the AI Chat Works](#how-the-ai-chat-works)
8. [Database Schema](#database-schema)
9. [API Reference](#api-reference)
10. [Setup Guide](#setup-guide)
11. [Troubleshooting](#troubleshooting)

---

## What is this Project?

This platform helps organizations track how their internal **data products** (dashboards, reports, datasets, analytics tools) are being used. Think of it as "Google Analytics" but for your internal data tools.

### Problems it Solves

| Problem | Solution |
|---------|----------|
| "Is anyone using our new dashboard?" | Track Daily/Weekly/Monthly Active Users |
| "Which reports are dying?" | Abandonment risk scoring |
| "What should we improve?" | AI-powered recommendations |
| "Who are our power users?" | User behavior analytics |

### Key Metrics Tracked

- **DAU** (Daily Active Users) - Users who accessed today
- **WAU** (Weekly Active Users) - Users in the last 7 days
- **MAU** (Monthly Active Users) - Users in the last 30 days
- **Adoption Score** - How well a product is being adopted (0-100%)
- **Stickiness Score** - How often users return (DAU/MAU ratio)
- **Abandonment Risk** - Likelihood of users leaving (0-100%)

---

## Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   USER LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐          │
│    │   Browser    │         │   Browser    │         │   Browser    │          │
│    │   (User 1)   │         │   (User 2)   │         │   (User N)   │          │
│    └──────┬───────┘         └──────┬───────┘         └──────┬───────┘          │
│           │                        │                        │                   │
│           └────────────────────────┼────────────────────────┘                   │
│                                    │                                            │
│                                    ▼                                            │
│                        ┌───────────────────────┐                                │
│                        │    Dashboard UI       │                                │
│                        │   (index.html)        │                                │
│                        │  - Summary Cards      │                                │
│                        │  - Product Table      │                                │
│                        │  - Charts             │                                │
│                        │  - AI Chat Panel      │                                │
│                        └───────────┬───────────┘                                │
│                                    │                                            │
└────────────────────────────────────┼────────────────────────────────────────────┘
                                     │ HTTP Requests
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 API LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                        ┌───────────────────────┐                                │
│                        │    FastAPI Server     │                                │
│                        │     (app.py)          │                                │
│                        │    Port: 8001         │                                │
│                        └───────────┬───────────┘                                │
│                                    │                                            │
│              ┌─────────────────────┼─────────────────────┐                      │
│              │                     │                     │                      │
│              ▼                     ▼                     ▼                      │
│    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│    │  /api/products  │   │  /api/summary   │   │   /api/chat     │            │
│    │  /api/track     │   │  /api/insights  │   │   /api/chat/    │            │
│    │                 │   │                 │   │      stats      │            │
│    └────────┬────────┘   └────────┬────────┘   └────────┬────────┘            │
│             │                     │                     │                      │
└─────────────┼─────────────────────┼─────────────────────┼──────────────────────┘
              │                     │                     │
              ▼                     │                     ▼
┌──────────────────────┐            │        ┌──────────────────────────────────┐
│    DATA LAYER        │            │        │         AI LAYER                 │
├──────────────────────┤            │        ├──────────────────────────────────┤
│                      │            │        │                                  │
│  ┌────────────────┐  │            │        │  ┌────────────────────────────┐  │
│  │   SQLite DB    │  │            │        │  │      ChromaDB              │  │
│  │ (analytics.db) │  │            │        │  │   (Vector Store)           │  │
│  │                │  │            │        │  │                            │  │
│  │ - Products     │  │            │        │  │ - Conversation History     │  │
│  │ - Users        │  │            │        │  │ - Semantic Search          │  │
│  │ - Usage Events │  │            │        │  │ - Embeddings               │  │
│  └────────────────┘  │            │        │  └─────────────┬──────────────┘  │
│                      │            │        │                │                 │
│  ┌────────────────┐  │            │        │                ▼                 │
│  │  analytics.py  │◄─┼────────────┘        │  ┌────────────────────────────┐  │
│  │                │  │                     │  │    Foundry Local           │  │
│  │ - Calculations │  │                     │  │    (Phi-4-mini LLM)        │  │
│  │ - Scoring      │  │                     │  │    Port: 51122             │  │
│  │ - Aggregations │  │                     │  │                            │  │
│  └────────────────┘  │                     │  │  - AI Insights             │  │
│                      │                     │  │  - Chat Responses          │  │
│  ┌────────────────┐  │                     │  │  - Recommendations         │  │
│  │   models.py    │  │                     │  └────────────────────────────┘  │
│  │                │  │                     │                                  │
│  │ - DB Schema    │  │                     └──────────────────────────────────┘
│  │ - Demo Data    │  │
│  └────────────────┘  │
│                      │
└──────────────────────┘
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REQUEST FLOW EXAMPLE                                │
│                     "User asks: Which product is at risk?"                   │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐
     │  User    │
     │  Types   │
     │ Question │
     └────┬─────┘
          │
          ▼
     ┌──────────┐      ┌─────────────┐      ┌─────────────────┐
     │  Chat    │─────►│  FastAPI    │─────►│   ChromaDB      │
     │   UI     │      │  /api/chat  │      │  Find similar   │
     └──────────┘      └──────┬──────┘      │  past questions │
                              │             └────────┬────────┘
                              │                      │
                              │◄─────────────────────┘
                              │  (relevant context)
                              │
                              ▼
                       ┌─────────────┐      ┌─────────────────┐
                       │   Fetch     │─────►│    SQLite       │
                       │   Product   │      │  Get all product│
                       │   Data      │      │  metrics        │
                       └──────┬──────┘      └────────┬────────┘
                              │                      │
                              │◄─────────────────────┘
                              │  (product data)
                              │
                              ▼
                       ┌─────────────┐      ┌─────────────────┐
                       │  Build      │─────►│  Foundry Local  │
                       │  Prompt +   │      │  (Phi-4-mini)   │
                       │  Send to AI │      │  Generate       │
                       └──────┬──────┘      │  Response       │
                              │             └────────┬────────┘
                              │                      │
                              │◄─────────────────────┘
                              │  (streaming response)
                              │
                              ▼
                       ┌─────────────┐      ┌─────────────────┐
                       │  Store      │─────►│   ChromaDB      │
                       │  Convo      │      │  Save Q&A for   │
                       │             │      │  future context │
                       └──────┬──────┘      └─────────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │  Stream     │
                       │  Response   │
                       │  to User    │
                       └─────────────┘
```

---

## System Components

### 1. Frontend (User Interface)

**File:** `static/index.html`

The dashboard that users see in their browser. Built with pure HTML, CSS, and JavaScript (no frameworks).

```
┌────────────────────────────────────────────────────────────────┐
│  Data Product Usage Analytics                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │Active   │ │Products │ │Queries  │ │Adoption │ │At Risk  │  │
│  │Users    │ │   6     │ │  4.0K   │ │  100%   │ │   0     │  │
│  │   8     │ │         │ │         │ │         │ │         │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│                                                                 │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐ │
│  │     Products Table          │  │    Query Trends Chart    │ │
│  │  ┌─────────┬─────┬─────┐   │  │         📈               │ │
│  │  │Product  │Score│Risk │   │  │                          │ │
│  │  ├─────────┼─────┼─────┤   │  └──────────────────────────┘ │
│  │  │Customer │100% │ 12% │   │                               │
│  │  │Sales    │100% │ 18% │   │  ┌──────────────────────────┐ │
│  │  │Marketing│100% │ 26% │   │  │     AI Insights          │ │
│  │  └─────────┴─────┴─────┘   │  │  [Generate Insights]     │ │
│  └─────────────────────────────┘  └──────────────────────────┘ │
│                                                          💬    │
└────────────────────────────────────────────────────────────────┘
                                                    Chat Button ──┘
```

**Key UI Components:**
- **Summary Cards** - Quick metrics overview
- **Products Table** - Clickable rows for detailed view
- **Charts** - Visual trends using Chart.js
- **AI Chat** - Floating chat button (bottom-right)
- **Modal** - Detailed product view popup

---

### 2. Backend API (Server)

**File:** `app.py`

The FastAPI server that handles all requests. Think of it as the "brain" that connects everything.

**What it does:**
- Serves the web page
- Handles API requests
- Connects to the database
- Talks to the AI model
- Manages conversation memory

**Key Endpoints:**

| Endpoint | What it does |
|----------|--------------|
| `GET /` | Serves the dashboard page |
| `GET /api/products` | Returns all products with scores |
| `GET /api/summary` | Returns platform statistics |
| `POST /api/chat` | Handles AI chat messages |
| `GET /api/chat/stats` | Returns memory status |

---

### 3. Database Layer

**Files:** `models.py`, `analytics.py`

Stores all the usage data in a SQLite database (a simple file-based database).

**What's stored:**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  data_products  │     │     users       │     │  usage_events   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │     │ id              │
│ name            │◄────┤ user_id         │     │ product_id ─────┼──┐
│ description     │     │ department      │     │ user_id ────────┼──┤
│ owner           │     │ created_at      │     │ event_type      │  │
│ created_at      │     └─────────────────┘     │ timestamp       │  │
└─────────────────┘                             │ query_duration  │  │
        ▲                                       └─────────────────┘  │
        │                                                            │
        └────────────────────────────────────────────────────────────┘
                              Relationships
```

---

### 4. AI Layer

**Files:** `vector_store.py` + External: Foundry Local

Two AI components working together:

#### A. Foundry Local (Phi-4-mini LLM)

The "brain" that generates human-like responses.

```
┌─────────────────────────────────────────────┐
│           Foundry Local                      │
│           Port: 51122                        │
├─────────────────────────────────────────────┤
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │         Phi-4-mini Model            │   │
│   │                                     │   │
│   │  Input:  "Which product is risky?"  │   │
│   │            + Product Data           │   │
│   │            + Past Conversations     │   │
│   │                                     │   │
│   │  Output: "Marketing Attribution     │   │
│   │          has the highest risk at    │   │
│   │          26.4% because..."          │   │
│   └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

#### B. ChromaDB (Vector Store)

The "memory" that remembers past conversations.

```
┌─────────────────────────────────────────────┐
│              ChromaDB                        │
│         (Conversation Memory)                │
├─────────────────────────────────────────────┤
│                                             │
│   How it works:                             │
│                                             │
│   1. User asks: "Which product is risky?"   │
│                        │                    │
│                        ▼                    │
│   2. Convert to numbers (embedding)         │
│      [0.23, -0.45, 0.67, 0.12, ...]        │
│                        │                    │
│                        ▼                    │
│   3. Store with the AI's answer             │
│                        │                    │
│                        ▼                    │
│   4. Next time: Find similar questions      │
│      to provide context                     │
│                                             │
└─────────────────────────────────────────────┘
```

**Why this matters:**
- Without memory: "Tell me more" → AI doesn't know what "more" means
- With memory: "Tell me more" → AI remembers you asked about risky products

---

## Data Flow

### Flow 1: Loading the Dashboard

```
User opens browser
        │
        ▼
┌───────────────────┐
│ GET /             │ ──► Returns index.html
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ GET /api/summary  │ ──► Returns {total_products: 6, active_users: 8, ...}
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ GET /api/products │ ──► Returns [{name: "Customer 360", score: 100}, ...]
└─────────┬─────────┘
          │
          ▼
    Dashboard renders
    with all data
```

### Flow 2: AI Chat Conversation

```
User: "Which products need attention?"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    /api/chat                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: Search ChromaDB for similar past questions         │
│          ──► Found: "Which product is at risk?" (similar)   │
│                                                             │
│  Step 2: Fetch current product data from SQLite             │
│          ──► Got: 6 products with all their metrics         │
│                                                             │
│  Step 3: Build prompt for AI                                │
│          ┌─────────────────────────────────────────────┐    │
│          │ System: You are a data product analyst...   │    │
│          │ Context: Here's the product data: {...}     │    │
│          │ Past Q&A: User previously asked about...    │    │
│          │ User: Which products need attention?        │    │
│          └─────────────────────────────────────────────┘    │
│                                                             │
│  Step 4: Send to Phi-4-mini, stream response back           │
│                                                             │
│  Step 5: Save Q&A to ChromaDB for future reference          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
User sees: "Based on the data, Marketing Attribution
           needs the most attention with a 26.4%
           abandonment risk..."
```

---

## Key Features Explained

### Feature 1: Adoption Score

**What it measures:** How many potential users are actually using the product

```
                    Users who used the product
Adoption Score = ─────────────────────────────── × 100
                    Total potential users

Example:
- Product: Customer 360 Dashboard
- Total employees who could use it: 100
- Employees who actually used it: 85
- Adoption Score: 85%
```

### Feature 2: Stickiness Score

**What it measures:** How often users come back

```
                     Daily Active Users (DAU)
Stickiness Score = ───────────────────────────── × 100
                    Monthly Active Users (MAU)

Example:
- DAU: 20 users
- MAU: 100 users
- Stickiness: 20% (users come back ~6 days/month on average)
```

### Feature 3: Abandonment Risk

**What it measures:** Likelihood that users will stop using the product

```
Factors considered:
├── Declining usage trend         (+risk)
├── Low stickiness               (+risk)
├── Decreasing unique users      (+risk)
├── Fewer queries per user       (+risk)
└── Short session durations      (+risk)

Risk Levels:
├── 0-25%:   Healthy (Green)
├── 25-50%:  Monitor (Yellow)
└── 50-100%: At Risk (Red)
```

### Feature 4: AI-Powered Insights

**What it does:** Analyzes all your data and provides recommendations

```
Input (automatic):
├── All product metrics
├── User behavior patterns
├── Historical trends
└── Past conversations

Output (AI generates):
├── "Marketing Attribution has high abandonment risk"
├── "Consider adding tutorials for new users"
├── "Sales Pipeline shows declining engagement"
└── "Customer 360 is your healthiest product"
```

### Feature 5: Conversation Memory

**What it does:** Remembers what you've discussed

```
Without Memory:
┌─────────────────────────────────────────────┐
│ User: Which product has the highest risk?   │
│ AI: Marketing Attribution at 26.4%          │
│                                             │
│ User: Tell me more about it                 │
│ AI: I don't know what "it" refers to ❌     │
└─────────────────────────────────────────────┘

With Memory:
┌─────────────────────────────────────────────┐
│ User: Which product has the highest risk?   │
│ AI: Marketing Attribution at 26.4%          │
│                                             │
│ User: Tell me more about it                 │
│ AI: Marketing Attribution is an analytics   │
│     tool with 253 queries, 5 users... ✓     │
└─────────────────────────────────────────────┘
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    TECHNOLOGY STACK                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend                                                   │
│  ├── HTML5          - Page structure                        │
│  ├── CSS3           - Styling (dark theme)                  │
│  ├── JavaScript     - Interactivity                         │
│  └── Chart.js       - Data visualization                    │
│                                                             │
│  Backend                                                    │
│  ├── Python 3.8+    - Programming language                  │
│  ├── FastAPI        - Web framework (fast, modern)          │
│  ├── Uvicorn        - ASGI server                           │
│  └── Pydantic       - Data validation                       │
│                                                             │
│  Database                                                   │
│  ├── SQLite         - Main database (usage data)            │
│  └── ChromaDB       - Vector database (AI memory)           │
│                                                             │
│  AI/ML                                                      │
│  ├── Foundry Local  - Local LLM runtime                     │
│  ├── Phi-4-mini     - Microsoft's small language model      │
│  └── ONNX Runtime   - ML inference engine                   │
│                                                             │
│  APIs                                                       │
│  └── OpenAI-compatible API (for Foundry Local)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How the AI Chat Works

### Step-by-Step Breakdown

```
┌──────────────────────────────────────────────────────────────────┐
│                     AI CHAT PIPELINE                              │
└──────────────────────────────────────────────────────────────────┘

STEP 1: User Input
────────────────────
User types: "Why is Marketing Attribution struggling?"
                    │
                    ▼

STEP 2: Context Retrieval (ChromaDB)
────────────────────────────────────
┌─────────────────────────────────────────┐
│ Search for similar past conversations:   │
│                                         │
│ Found 2 relevant conversations:         │
│ 1. "Which product is at risk?" (92%)    │
│ 2. "Tell me about risks" (78%)          │
└─────────────────────────────────────────┘
                    │
                    ▼

STEP 3: Data Gathering (SQLite)
───────────────────────────────
┌─────────────────────────────────────────┐
│ Fetch current metrics:                   │
│                                         │
│ Marketing Attribution:                   │
│ - DAU: 2, WAU: 4, MAU: 5               │
│ - Adoption: 100%                        │
│ - Stickiness: 0%                        │
│ - Abandonment Risk: 26.4%               │
│ - Trend: declining                      │
└─────────────────────────────────────────┘
                    │
                    ▼

STEP 4: Prompt Construction
───────────────────────────
┌─────────────────────────────────────────┐
│ SYSTEM: You are an AI assistant for     │
│ data product analytics...               │
│                                         │
│ CONTEXT: Here's the current data:       │
│ {all product metrics as JSON}           │
│                                         │
│ PAST CONVERSATIONS:                     │
│ - User asked about risks before         │
│ - AI explained Marketing Attribution    │
│                                         │
│ USER: Why is Marketing Attribution      │
│ struggling?                             │
└─────────────────────────────────────────┘
                    │
                    ▼

STEP 5: AI Processing (Phi-4-mini)
──────────────────────────────────
┌─────────────────────────────────────────┐
│ Phi-4-mini analyzes:                    │
│ - The question                          │
│ - Product data                          │
│ - Past context                          │
│                                         │
│ Generates response token by token:      │
│ "Marketing" → "Attribution" → "is" →    │
│ "struggling" → "because" → ...          │
└─────────────────────────────────────────┘
                    │
                    ▼

STEP 6: Response Streaming
──────────────────────────
┌─────────────────────────────────────────┐
│ Tokens sent to browser as they generate:│
│                                         │
│ "Marketing Attribution is struggling    │
│  due to several factors:                │
│                                         │
│  1. Low stickiness (0%) indicates users │
│     aren't returning regularly          │
│                                         │
│  2. High abandonment risk (26.4%)       │
│     suggests declining engagement..."   │
└─────────────────────────────────────────┘
                    │
                    ▼

STEP 7: Memory Storage (ChromaDB)
─────────────────────────────────
┌─────────────────────────────────────────┐
│ Save this conversation:                  │
│                                         │
│ Q: "Why is Marketing Attribution        │
│     struggling?"                        │
│ A: "Marketing Attribution is            │
│     struggling due to..."               │
│                                         │
│ → Converted to embedding vector         │
│ → Stored for future reference           │
└─────────────────────────────────────────┘
```

---

## Database Schema

### Visual Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE SCHEMA                             │
│                      (analytics.db)                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│   data_products     │
├─────────────────────┤
│ id (PRIMARY KEY)    │──────────────────────┐
│ name                │                      │
│ description         │                      │
│ owner               │                      │
│ created_at          │                      │
└─────────────────────┘                      │
                                             │
┌─────────────────────┐                      │
│      users          │                      │
├─────────────────────┤                      │
│ id (PRIMARY KEY)    │──────────────┐       │
│ user_id             │              │       │
│ department          │              │       │
│ created_at          │              │       │
└─────────────────────┘              │       │
                                     │       │
                                     │       │
┌─────────────────────┐              │       │
│   usage_events      │              │       │
├─────────────────────┤              │       │
│ id (PRIMARY KEY)    │              │       │
│ product_id (FK) ────┼──────────────┼───────┘
│ user_id (FK) ───────┼──────────────┘
│ event_type          │
│ timestamp           │
│ tables_accessed     │
│ query_duration_ms   │
└─────────────────────┘

FK = Foreign Key (links to another table)
```

### Sample Data

**data_products:**
| id | name | owner |
|----|------|-------|
| 1 | Customer 360 | Data Team |
| 2 | Sales Pipeline | Sales Ops |
| 3 | Marketing Attribution | Marketing |

**usage_events:**
| id | product_id | user_id | event_type | timestamp |
|----|------------|---------|------------|-----------|
| 1 | 1 | 5 | query | 2024-01-15 09:30:00 |
| 2 | 1 | 3 | query | 2024-01-15 10:15:00 |
| 3 | 2 | 5 | view | 2024-01-15 11:00:00 |

---

## API Reference

### Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                      API ENDPOINTS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GET  /                     → Dashboard HTML page               │
│                                                                 │
│  GET  /api/summary          → Platform statistics               │
│       Response: {                                               │
│         "total_products": 6,                                    │
│         "active_users_30d": 8,                                  │
│         "total_queries_30d": 4001,                              │
│         "avg_adoption_score": 100.0                             │
│       }                                                         │
│                                                                 │
│  GET  /api/products         → All products with scores          │
│       Response: [{                                              │
│         "id": 1,                                                │
│         "name": "Customer 360",                                 │
│         "adoption_score": 100,                                  │
│         "abandonment_risk": 12.5                                │
│       }, ...]                                                   │
│                                                                 │
│  GET  /api/products/{id}    → Single product details            │
│                                                                 │
│  POST /api/chat             → AI chat (streaming)               │
│       Body: {"message": "your question"}                        │
│       Response: Server-Sent Events (streaming)                  │
│                                                                 │
│  GET  /api/chat/stats       → Memory status                     │
│       Response: {                                               │
│         "total_conversations": 5,                               │
│         "memory_enabled": true                                  │
│       }                                                         │
│                                                                 │
│  POST /api/track            → Track usage event                 │
│       Body: {                                                   │
│         "product_name": "Dashboard",                            │
│         "user_id": "user123",                                   │
│         "event_type": "query"                                   │
│       }                                                         │
│                                                                 │
│  POST /api/insights         → Generate AI insights              │
│       Body: {"product_id": 1} (optional)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setup Guide

### Prerequisites Checklist

```
Before you start, make sure you have:

☐ Python 3.8 or higher
  Check: python --version

☐ Foundry Local installed
  Download: https://github.com/microsoft/foundry-local

☐ Visual C++ Redistributable (Windows only, for ChromaDB)
  Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Installation Steps

```
STEP 1: Get the Code
────────────────────
git clone https://github.com/pandeyraunak007/data-product-analytics.git
cd data-product-analytics


STEP 2: Create Virtual Environment (Recommended)
────────────────────────────────────────────────
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate


STEP 3: Install Dependencies
────────────────────────────
pip install -r requirements.txt


STEP 4: Start Foundry Local (in a separate terminal)
────────────────────────────────────────────────────
foundry model run Phi-4-mini-instruct

# Wait until you see "Model loaded successfully"


STEP 5: Start the Application
─────────────────────────────
python app.py

# You should see:
# INFO: Uvicorn running on http://0.0.0.0:8001


STEP 6: Open in Browser
───────────────────────
Open: http://localhost:8001
```

### Verify Everything Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERIFICATION CHECKLIST                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ☐ Dashboard loads with data                                    │
│    → You should see 6 products in the table                     │
│                                                                 │
│  ☐ Charts are displaying                                        │
│    → Query trends chart should show data                        │
│                                                                 │
│  ☐ AI Insights work                                             │
│    → Click "Generate Insights" button                           │
│    → Should see AI-generated recommendations                    │
│                                                                 │
│  ☐ Chat works                                                   │
│    → Click chat icon (bottom-right)                             │
│    → Ask "Which product is at risk?"                            │
│    → Should get a response about Marketing Attribution          │
│                                                                 │
│  ☐ Memory is enabled                                            │
│    → Chat header should show green dot                          │
│    → Should say "Memory: X" (where X is conversation count)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Common Issues and Solutions

```
┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: "DLL load failed" error on Windows                    │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Missing Visual C++ Redistributable                      │
│  SOLUTION:                                                      │
│  1. Download: https://aka.ms/vs/17/release/vc_redist.x64.exe   │
│  2. Install it                                                  │
│  3. Restart the application                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: AI chat returns errors                                │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Foundry Local not running                               │
│  SOLUTION:                                                      │
│  1. Open a new terminal                                         │
│  2. Run: foundry model run Phi-4-mini-instruct                 │
│  3. Wait for "Model loaded successfully"                        │
│  4. Try the chat again                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: Memory shows "No memory" (red dot)                    │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: ChromaDB failed to initialize                           │
│  SOLUTION:                                                      │
│  1. Install Visual C++ Redistributable (Windows)                │
│  2. Delete the chroma_db folder if it exists                    │
│  3. Restart the application                                     │
│                                                                 │
│  NOTE: The app still works without memory, just won't           │
│        remember past conversations                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: Port 8001 already in use                              │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Another application using the port                      │
│  SOLUTION:                                                      │
│  Option A: Kill the other process                               │
│    Windows: netstat -ano | findstr :8001                        │
│             taskkill /PID <PID> /F                              │
│                                                                 │
│  Option B: Change port in app.py                                │
│    Change: uvicorn.run(app, port=8001)                          │
│    To:     uvicorn.run(app, port=8002)                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: Slow AI responses                                     │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Running on CPU instead of GPU                           │
│  SOLUTION:                                                      │
│  - This is normal for CPU-only setups                           │
│  - First response may take 10-30 seconds                        │
│  - Subsequent responses are faster                              │
│  - For faster responses, use a GPU-enabled machine              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

This platform provides:

1. **Visibility** - See how all your data products are being used
2. **Intelligence** - AI analyzes patterns and provides recommendations
3. **Memory** - Conversations are remembered for context-aware responses
4. **Simplicity** - Clean dashboard, no complex setup

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     "Turn your data product usage into actionable insights"     │
│                                                                 │
│                    📊 → 🤖 → 💡                                 │
│                                                                 │
│              Data    AI     Insights                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*Last updated: December 2024*
*Repository: https://github.com/pandeyraunak007/data-product-analytics*
