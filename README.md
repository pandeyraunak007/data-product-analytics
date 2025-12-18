# Data Product Analytics Platform

A dashboard for tracking adoption, stickiness, and health of internal data products with AI-powered insights.

**Live Demo:** https://data-product-analytics.vercel.app

![Dashboard Preview](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-Deployed-black?style=flat&logo=vercel&logoColor=white)

## Features

- **Usage Analytics Dashboard** - Track DAU, WAU, MAU, adoption scores, and stickiness metrics
- **Product Health Monitoring** - Identify at-risk products with abandonment risk scores
- **Interactive Charts** - Visualize query trends and user behavior patterns
- **AI-Powered Insights** - Get recommendations powered by Llama 3.3 70B (via Groq)
- **AI Chat Interface** - Ask questions about your data products in natural language
- **Dual Deployment** - Run locally or deploy to Vercel for free

## Live Demo

Visit the deployed app: **https://data-product-analytics.vercel.app**

- Browse the dashboard to see product analytics
- Click the chat icon (bottom-right) to ask AI questions
- Try: "Which product has the highest adoption?"

## Quick Start

### Option 1: Use the Live Demo

Just visit https://data-product-analytics.vercel.app - no setup required!

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/pandeyraunak007/data-product-analytics.git
cd data-product-analytics

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start Foundry Local (for AI features)
foundry model run Phi-4-mini-instruct

# Run the application
python app.py
```

Open http://localhost:8001 in your browser.

### Option 3: Deploy Your Own

See [Deployment Guide](#deployment) below.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT MODES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   LOCAL MODE                    CLOUD MODE (Vercel)              │
│   ───────────                   ─────────────────                │
│                                                                  │
│   ┌──────────────┐              ┌──────────────┐                │
│   │   SQLite     │              │   Neon       │                │
│   │   Database   │              │  PostgreSQL  │                │
│   └──────────────┘              └──────────────┘                │
│                                                                  │
│   ┌──────────────┐              ┌──────────────┐                │
│   │Foundry Local │              │   Groq API   │                │
│   │ (Phi-4-mini) │              │(Llama 3.3 70B│                │
│   └──────────────┘              └──────────────┘                │
│                                                                  │
│   Cost: $0                      Cost: $0 (free tiers)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
data-product-analytics/
├── app.py              # Local FastAPI server
├── api/
│   └── index.py        # Vercel serverless function
├── models.py           # Database models (local)
├── analytics.py        # Analytics calculations (local)
├── vector_store.py     # ChromaDB memory (local only)
├── requirements.txt    # Local dependencies
├── vercel.json         # Vercel configuration
└── static/
    └── index.html      # Dashboard UI
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check and config status |
| `/api/summary` | GET | Platform-wide summary statistics |
| `/api/products` | GET | All products with scores |
| `/api/products/{id}` | GET | Detailed analytics for a product |
| `/api/chat` | POST | Chat with AI about data products |
| `/api/insights` | POST | Generate AI insights |

## Deployment

### Deploy to Vercel (Free)

The app is configured for one-click Vercel deployment with free services:

| Service | Provider | Cost |
|---------|----------|------|
| Hosting | Vercel | Free |
| Database | Neon PostgreSQL | Free |
| AI | Groq (Llama 3.3 70B) | Free |

#### Steps:

1. **Get a Groq API Key (FREE)**
   - Go to https://console.groq.com/keys
   - Sign up and create an API key

2. **Get a PostgreSQL Database (FREE)**
   - Go to https://neon.tech
   - Sign up and create a project
   - Copy the connection string

3. **Deploy to Vercel**
   - Go to https://vercel.com
   - Import this GitHub repository
   - Add environment variables:
     - `GROQ_API_KEY` - Your Groq API key
     - `DATABASE_URL` - Your Neon connection string
   - Deploy!

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for AI (Llama 3.3) | Yes (Vercel) |
| `DATABASE_URL` | PostgreSQL connection string | Yes (Vercel) |

For local development, leave these unset to use SQLite + Foundry Local.

## Local Development

### Prerequisites

- Python 3.8+
- [Foundry Local](https://github.com/microsoft/foundry-local) with Phi-4-mini model
- (Optional) [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) for ChromaDB on Windows

### Configuration

Local defaults:
- **Server Port**: 8001
- **Foundry Local URL**: `http://127.0.0.1:51122/v1`
- **AI Model**: `Phi-4-mini-instruct-generic-cpu:5`
- **Database**: SQLite (`analytics.db`)

## Usage

### Dashboard

- **Summary Cards** - Overview of active users, products, queries, and scores
- **Products Table** - Click any product row to see detailed analytics
- **Query Trends Chart** - 30-day query volume visualization
- **AI Insights** - Click "Generate Insights" for AI-powered recommendations

### AI Chat

Click the chat icon (bottom-right corner) to open the AI assistant. Ask questions like:
- "Which product has the highest adoption?"
- "Which products are at risk?"
- "How can I improve stickiness?"

## Tech Stack

| Layer | Local | Cloud |
|-------|-------|-------|
| Frontend | HTML/CSS/JS + Chart.js | Same |
| Backend | FastAPI + Uvicorn | Vercel Serverless |
| Database | SQLite | Neon PostgreSQL |
| AI | Foundry Local (Phi-4-mini) | Groq (Llama 3.3 70B) |
| Memory | ChromaDB | Disabled |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT

---

**Live Demo:** https://data-product-analytics.vercel.app

**Repository:** https://github.com/pandeyraunak007/data-product-analytics
