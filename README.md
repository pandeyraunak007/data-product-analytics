# Data Product Analytics Platform

A dashboard for tracking adoption, stickiness, and health of internal data products with AI-powered insights using Foundry Local (Phi-4-mini).

![Dashboard Preview](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)

## Features

- **Usage Analytics Dashboard** - Track DAU, WAU, MAU, adoption scores, and stickiness metrics
- **Product Health Monitoring** - Identify at-risk products with abandonment risk scores
- **Interactive Charts** - Visualize query trends and user behavior patterns
- **AI-Powered Insights** - Get recommendations using Phi-4-mini via Foundry Local
- **AI Chat Interface** - Ask questions about your data products in natural language
- **Detailed Product Views** - Drill down into retention cohorts, user types, and table access patterns

## Prerequisites

- Python 3.8+
- [Foundry Local](https://github.com/microsoft/foundry-local) with Phi-4-mini model

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/pandeyraunak007/data-product-analytics.git
cd data-product-analytics
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Foundry Local

Make sure Foundry Local is running with the Phi-4-mini model on port 51122.

```bash
# Install Foundry Local if not already installed
# Follow instructions at: https://github.com/microsoft/foundry-local

# Start Foundry Local with Phi-4-mini
foundry model run Phi-4-mini-instruct
```

Verify Foundry Local is running:
```bash
curl http://127.0.0.1:51122/v1/models
```

### 5. Run the application

```bash
python app.py
```

The application will start on `http://localhost:8001`

## Usage

### Dashboard

Open `http://localhost:8001` in your browser to access the dashboard.

- **Summary Cards** - Overview of active users, products, queries, and scores
- **Products Table** - Click any product row to see detailed analytics
- **Query Trends Chart** - 30-day query volume visualization
- **AI Insights** - Click "Generate Insights" for AI-powered recommendations

### AI Chat

Click the chat icon (bottom-right corner) to open the AI assistant. Ask questions like:
- "Which product has the highest adoption?"
- "Which products are at risk?"
- "How can I improve stickiness?"

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/summary` | GET | Platform-wide summary statistics |
| `/api/products` | GET | All products with scores |
| `/api/products/{id}` | GET | Detailed analytics for a product |
| `/api/track` | POST | Track a usage event |
| `/api/insights` | POST | Generate AI insights |
| `/api/chat` | POST | Chat with AI about data products |

## Project Structure

```
data-product-analytics/
├── app.py              # FastAPI application and routes
├── models.py           # Database models and initialization
├── analytics.py        # Analytics calculations and queries
├── requirements.txt    # Python dependencies
└── static/
    └── index.html      # Dashboard UI
```

## Configuration

The application uses these default settings:

- **Server Port**: 8001
- **Foundry Local URL**: `http://127.0.0.1:51122/v1`
- **AI Model**: `Phi-4-mini-instruct-generic-cpu:5`

To modify these, edit the constants in `app.py`.

## License

MIT
