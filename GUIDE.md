# Data Product Analytics Platform - Complete Guide

A comprehensive guide to understanding the Data Product Analytics Platform, its architecture, and how all the pieces work together.

**Live Demo:** https://data-product-analytics.vercel.app

---

## Table of Contents

1. [What is this Project?](#what-is-this-project)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Modes](#deployment-modes)
4. [System Components](#system-components)
5. [Data Flow](#data-flow)
6. [Key Features Explained](#key-features-explained)
7. [Technology Stack](#technology-stack)
8. [How the AI Chat Works](#how-the-ai-chat-works)
9. [Database Schema](#database-schema)
10. [API Reference](#api-reference)
11. [Setup Guide](#setup-guide)
12. [Troubleshooting](#troubleshooting)

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
│         LOCAL MODE                              CLOUD MODE (Vercel)              │
│    ┌───────────────────────┐             ┌───────────────────────┐              │
│    │    FastAPI Server     │             │  Vercel Serverless    │              │
│    │     (app.py)          │             │   (api/index.py)      │              │
│    │    Port: 8001         │             │   Auto-scaling        │              │
│    └───────────┬───────────┘             └───────────┬───────────┘              │
│                │                                     │                          │
└────────────────┼─────────────────────────────────────┼──────────────────────────┘
                 │                                     │
                 ▼                                     ▼
┌────────────────────────────────┐    ┌────────────────────────────────┐
│        LOCAL DATA LAYER        │    │       CLOUD DATA LAYER         │
├────────────────────────────────┤    ├────────────────────────────────┤
│                                │    │                                │
│  ┌────────────────┐            │    │  ┌────────────────┐            │
│  │   SQLite DB    │            │    │  │Neon PostgreSQL │            │
│  │ (analytics.db) │            │    │  │  (Cloud DB)    │            │
│  └────────────────┘            │    │  └────────────────┘            │
│                                │    │                                │
│  ┌────────────────┐            │    │  ┌────────────────┐            │
│  │   ChromaDB     │            │    │  │   Groq API     │            │
│  │ (AI Memory)    │            │    │  │(Llama 3.3 70B) │            │
│  └────────────────┘            │    │  │    FREE        │            │
│                                │    │  └────────────────┘            │
│  ┌────────────────┐            │    │                                │
│  │ Foundry Local  │            │    │                                │
│  │ (Phi-4-mini)   │            │    │                                │
│  └────────────────┘            │    │                                │
│                                │    │                                │
│  Cost: $0                      │    │  Cost: $0 (all free tiers)     │
└────────────────────────────────┘    └────────────────────────────────┘
```

---

## Deployment Modes

This application supports two deployment modes:

### Local Mode (Development)

Best for development and testing on your machine.

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MODE                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Database:     SQLite (analytics.db)                        │
│  AI Model:     Foundry Local (Phi-4-mini)                   │
│  AI Memory:    ChromaDB (vector store)                      │
│  Server:       FastAPI + Uvicorn                            │
│  Port:         8001                                         │
│                                                             │
│  Requirements:                                              │
│  - Python 3.8+                                              │
│  - Foundry Local running                                    │
│  - ~4GB RAM for AI model                                    │
│                                                             │
│  Pros:                                                      │
│  ✓ No internet required (after setup)                       │
│  ✓ Full conversation memory                                 │
│  ✓ Data stays on your machine                               │
│  ✓ Customizable                                             │
│                                                             │
│  Cons:                                                      │
│  ✗ Requires local setup                                     │
│  ✗ Slower AI responses (CPU)                                │
│  ✗ Not shareable                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Cloud Mode (Vercel)

Best for sharing and production use.

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD MODE (Vercel)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Database:     Neon PostgreSQL (cloud)                      │
│  AI Model:     Groq API (Llama 3.3 70B)                     │
│  AI Memory:    Disabled (serverless limitation)             │
│  Server:       Vercel Serverless Functions                  │
│  URL:          https://data-product-analytics.vercel.app    │
│                                                             │
│  Requirements:                                              │
│  - Vercel account (free)                                    │
│  - Neon account (free)                                      │
│  - Groq account (free)                                      │
│                                                             │
│  Pros:                                                      │
│  ✓ No setup required to use                                 │
│  ✓ Fast AI responses (Groq)                                 │
│  ✓ Shareable URL                                            │
│  ✓ Auto-scaling                                             │
│  ✓ All FREE                                                 │
│                                                             │
│  Cons:                                                      │
│  ✗ No conversation memory                                   │
│  ✗ Requires internet                                        │
│  ✗ Cold starts possible                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Comparison Table

| Feature | Local Mode | Cloud Mode (Vercel) |
|---------|------------|---------------------|
| **URL** | http://localhost:8001 | https://data-product-analytics.vercel.app |
| **Database** | SQLite | Neon PostgreSQL |
| **AI Provider** | Foundry Local (Phi-4-mini) | Groq (Llama 3.3 70B) |
| **AI Speed** | Slow (CPU) | Fast (cloud GPU) |
| **Memory** | Yes (ChromaDB) | No |
| **Setup** | Required | One-click |
| **Cost** | $0 | $0 |
| **Sharing** | Local only | Public URL |

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
│  │Users    │ │   6     │ │  3.2K   │ │  100%   │ │   0     │  │
│  │   4     │ │         │ │         │ │         │ │         │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│                                                                 │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐ │
│  │     Products Table          │  │    Query Trends Chart    │ │
│  │  ┌─────────┬─────┬─────┐   │  │         📈               │ │
│  │  │Product  │Score│Risk │   │  │                          │ │
│  │  ├─────────┼─────┼─────┤   │  └──────────────────────────┘ │
│  │  │Customer │100% │  0% │   │                               │
│  │  │Revenue  │100% │  0% │   │  ┌──────────────────────────┐ │
│  │  │Sales    │100% │  0% │   │  │     AI Insights          │ │
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

---

### 2. Backend API

**Local:** `app.py`
**Cloud:** `api/index.py`

The server that handles all requests and connects everything.

**What it does:**
- Serves the web page
- Handles API requests
- Connects to the database
- Talks to the AI model

**Key Endpoints:**

| Endpoint | What it does |
|----------|--------------|
| `GET /` | Serves the dashboard page |
| `GET /api/health` | Health check and config info |
| `GET /api/products` | Returns all products with scores |
| `GET /api/summary` | Returns platform statistics |
| `POST /api/chat` | Handles AI chat messages |

---

### 3. Database Layer

**Local:** SQLite (`analytics.db`)
**Cloud:** Neon PostgreSQL

Stores all the usage data.

**Tables:**

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
```

---

### 4. AI Layer

**Local:** Foundry Local + ChromaDB
**Cloud:** Groq API

#### Local: Foundry Local (Phi-4-mini)

```
┌─────────────────────────────────────────────┐
│           Foundry Local                      │
│           Port: 51122                        │
├─────────────────────────────────────────────┤
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │         Phi-4-mini Model            │   │
│   │                                     │   │
│   │  • Runs locally on your machine     │   │
│   │  • ~4GB memory usage                │   │
│   │  • CPU-based inference              │   │
│   │  • OpenAI-compatible API            │   │
│   └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

#### Cloud: Groq API (Llama 3.3 70B)

```
┌─────────────────────────────────────────────┐
│              Groq API                        │
│     https://api.groq.com/openai/v1          │
├─────────────────────────────────────────────┤
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │       Llama 3.3 70B Model           │   │
│   │                                     │   │
│   │  • Cloud-hosted (fast!)             │   │
│   │  • FREE: 14,400 requests/day        │   │
│   │  • GPU-accelerated                  │   │
│   │  • OpenAI-compatible API            │   │
│   └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

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
│ GET /api/summary  │ ──► Returns {total_products: 6, active_users: 4, ...}
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
│  Step 1: Fetch current product data from database           │
│          ──► Got: 6 products with all their metrics         │
│                                                             │
│  Step 2: Build prompt for AI                                │
│          ┌─────────────────────────────────────────────┐    │
│          │ System: You are a data product analyst...   │    │
│          │ Context: Here's the product data: {...}     │    │
│          │ User: Which products need attention?        │    │
│          └─────────────────────────────────────────────┘    │
│                                                             │
│  Step 3: Send to AI, stream response back                   │
│          Local: Foundry Local (Phi-4-mini)                  │
│          Cloud: Groq API (Llama 3.3 70B)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
User sees: "Based on the data, all products have
           100% adoption. However, some may need
           attention to improve stickiness..."
```

---

## Key Features Explained

### Feature 1: Adoption Score

**What it measures:** How many potential users are actually using the product

```
                    Users who used the product (MAU)
Adoption Score = ─────────────────────────────────── × 100
                      Total potential users

Example:
- Product: Customer 360 Dashboard
- Total users in system: 4
- Users who accessed it: 4
- Adoption Score: 100%
```

### Feature 2: Stickiness Score

**What it measures:** How often users come back

```
                     Daily Active Users (DAU)
Stickiness Score = ───────────────────────────── × 100
                    Monthly Active Users (MAU)

Example:
- DAU: 2 users
- MAU: 4 users
- Stickiness: 50% (users come back half the days)
```

### Feature 3: Abandonment Risk

**What it measures:** Likelihood that users will stop using the product

```
Factors considered:
├── Declining usage trend         (+risk)
├── Low stickiness               (+risk)
├── Decreasing unique users      (+risk)
└── Fewer queries per user       (+risk)

Risk Levels:
├── 0-25%:   Healthy (Green)
├── 25-50%:  Monitor (Yellow)
└── 50-100%: At Risk (Red)
```

### Feature 4: AI-Powered Chat

**What it does:** Answers questions about your data in natural language

```
┌─────────────────────────────────────────────┐
│ User: Which product has the highest risk?   │
│                                             │
│ AI: Based on the current data, all products │
│     show healthy metrics with 100% adoption │
│     scores and 0% abandonment risk.         │
│     Customer 360, Revenue Dashboard, and    │
│     Sales Pipeline are performing well...   │
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
│  ├── FastAPI        - Web framework                         │
│  └── Pydantic       - Data validation                       │
│                                                             │
│  Database                                                   │
│  ├── SQLite         - Local database                        │
│  └── PostgreSQL     - Cloud database (Neon)                 │
│                                                             │
│  AI/ML                                                      │
│  ├── Foundry Local  - Local LLM (Phi-4-mini)               │
│  ├── Groq API       - Cloud LLM (Llama 3.3 70B)            │
│  └── ChromaDB       - Vector store (local only)             │
│                                                             │
│  Deployment                                                 │
│  ├── Vercel         - Serverless hosting (free)            │
│  ├── Neon           - PostgreSQL hosting (free)            │
│  └── Groq           - AI inference (free)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

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
│  GET  /api/health           → Health check                      │
│       Response: {                                               │
│         "status": "ok",                                         │
│         "database": "postgresql",                               │
│         "ai": "groq"                                            │
│       }                                                         │
│                                                                 │
│  GET  /api/summary          → Platform statistics               │
│       Response: {                                               │
│         "total_products": 6,                                    │
│         "active_users_30d": 4,                                  │
│         "total_queries_30d": 3183                               │
│       }                                                         │
│                                                                 │
│  GET  /api/products         → All products with scores          │
│       Response: [{                                              │
│         "id": 1,                                                │
│         "name": "Customer 360",                                 │
│         "adoption_score": 100,                                  │
│         "abandonment_risk": 0                                   │
│       }, ...]                                                   │
│                                                                 │
│  GET  /api/products/{id}    → Single product details            │
│                                                                 │
│  POST /api/chat             → AI chat (streaming)               │
│       Body: {"message": "your question"}                        │
│       Response: Server-Sent Events (streaming)                  │
│                                                                 │
│  POST /api/insights         → Generate AI insights              │
│       Response: Server-Sent Events (streaming)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setup Guide

### Option 1: Use the Live Demo (Easiest)

Just visit: **https://data-product-analytics.vercel.app**

No setup required!

### Option 2: Run Locally

```
STEP 1: Get the Code
────────────────────
git clone https://github.com/pandeyraunak007/data-product-analytics.git
cd data-product-analytics


STEP 2: Create Virtual Environment
───────────────────────────────────
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate


STEP 3: Install Dependencies
────────────────────────────
pip install -r requirements.txt


STEP 4: Start Foundry Local (separate terminal)
───────────────────────────────────────────────
foundry model run Phi-4-mini-instruct

# Wait for "Model loaded successfully"


STEP 5: Start the Application
─────────────────────────────
python app.py

# Open: http://localhost:8001
```

### Option 3: Deploy to Vercel

```
STEP 1: Get Free Accounts
─────────────────────────
☐ Groq API key:    https://console.groq.com/keys
☐ Neon database:   https://neon.tech
☐ Vercel account:  https://vercel.com


STEP 2: Deploy on Vercel
────────────────────────
1. Go to vercel.com
2. Import: github.com/pandeyraunak007/data-product-analytics
3. Add environment variables:
   - GROQ_API_KEY = your_groq_key
   - DATABASE_URL = your_neon_connection_string
4. Deploy!


STEP 3: Done!
─────────────
Your app is live at: https://your-app.vercel.app
```

---

## Troubleshooting

### Common Issues

```
┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: AI chat returns errors (local)                        │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Foundry Local not running                               │
│  SOLUTION:                                                      │
│  1. Open a new terminal                                         │
│  2. Run: foundry model run Phi-4-mini-instruct                 │
│  3. Wait for "Model loaded successfully"                        │
│  4. Try the chat again                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: Database errors on Vercel                             │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Invalid DATABASE_URL                                    │
│  SOLUTION:                                                      │
│  1. Check your Neon connection string                           │
│  2. Make sure it includes ?sslmode=require                     │
│  3. Redeploy on Vercel                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: AI not responding on Vercel                           │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Invalid GROQ_API_KEY                                    │
│  SOLUTION:                                                      │
│  1. Get a new key from console.groq.com/keys                   │
│  2. Update in Vercel environment variables                      │
│  3. Redeploy                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: "DLL load failed" on Windows (local)                  │
├─────────────────────────────────────────────────────────────────┤
│  CAUSE: Missing Visual C++ Redistributable                      │
│  SOLUTION:                                                      │
│  1. Download: https://aka.ms/vs/17/release/vc_redist.x64.exe   │
│  2. Install it                                                  │
│  3. Restart the application                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

This platform provides:

1. **Visibility** - See how all your data products are being used
2. **Intelligence** - AI analyzes patterns and provides recommendations
3. **Flexibility** - Run locally or deploy to cloud for free
4. **Simplicity** - Clean dashboard, easy setup

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     "Turn your data product usage into actionable insights"     │
│                                                                 │
│                    📊 → 🤖 → 💡                                 │
│                                                                 │
│              Data    AI     Insights                            │
│                                                                 │
│     Live Demo: https://data-product-analytics.vercel.app        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*Last updated: December 2024*
*Repository: https://github.com/pandeyraunak007/data-product-analytics*
*Live Demo: https://data-product-analytics.vercel.app*
