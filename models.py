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
    """Seed database with comprehensive SaaS analytics demo data"""
    conn = get_db()
    cursor = conn.cursor()

    # Check if data exists
    cursor.execute("SELECT COUNT(*) FROM data_products")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    import random

    # Comprehensive SaaS Data Products (18 products across categories)
    products = [
        # Core Analytics (High Usage)
        ("Customer 360", "Unified customer view across all touchpoints", "Data Team"),
        ("Revenue Dashboard", "Real-time ARR, MRR, and revenue metrics", "Finance"),
        ("Sales Pipeline", "Deal tracking, forecasting, and conversion metrics", "Sales Ops"),
        ("Product Analytics", "Feature adoption, user journeys, and engagement", "Product Team"),

        # Marketing Tools
        ("Marketing Attribution", "Multi-touch attribution and campaign ROI", "Marketing Analytics"),
        ("Campaign Performance", "Email, ads, and content marketing metrics", "Growth Team"),
        ("SEO Dashboard", "Organic traffic, rankings, and keyword analysis", "Content Team"),
        ("Social Media Analytics", "Engagement, reach, and sentiment analysis", "Brand Team"),

        # Operations & Support
        ("Support Ticket Analytics", "CSAT, response times, and ticket trends", "Customer Success"),
        ("Inventory Dashboard", "Stock levels, supply chain, and logistics", "Operations"),
        ("Vendor Scorecard", "Supplier performance and contract metrics", "Procurement"),

        # HR & Internal
        ("HR Analytics", "Headcount, attrition, and hiring funnel", "People Team"),
        ("Employee Engagement", "Survey results and team health scores", "HR"),

        # Technical
        ("API Usage Monitor", "Endpoint usage, latency, and error rates", "Engineering"),
        ("Infrastructure Costs", "Cloud spend, resource utilization", "DevOps"),
        ("Security Dashboard", "Threats, vulnerabilities, and compliance", "Security Team"),

        # Executive
        ("Executive KPI Board", "Company OKRs and strategic metrics", "Leadership"),
        ("Board Reporting", "Investor metrics and quarterly summaries", "CEO Office"),
    ]

    for p in products:
        cursor.execute("INSERT OR IGNORE INTO data_products (name, description, owner) VALUES (?, ?, ?)", p)

    # Comprehensive users (30 users across departments)
    users = [
        # Leadership
        ("ceo@company.com", "executive", "Leadership"),
        ("cfo@company.com", "executive", "Finance"),
        ("cto@company.com", "executive", "Engineering"),
        ("cmo@company.com", "executive", "Marketing"),
        ("coo@company.com", "executive", "Operations"),

        # Data Team
        ("alice.chen@company.com", "data_scientist", "Data Science"),
        ("bob.kumar@company.com", "data_analyst", "Data Science"),
        ("carol.smith@company.com", "analytics_engineer", "Data Science"),
        ("david.lee@company.com", "data_analyst", "Data Science"),

        # Sales
        ("emma.wilson@company.com", "sales_manager", "Sales"),
        ("frank.jones@company.com", "account_exec", "Sales"),
        ("grace.taylor@company.com", "sales_ops", "Sales"),
        ("henry.brown@company.com", "sdr", "Sales"),

        # Marketing
        ("ivy.garcia@company.com", "marketing_manager", "Marketing"),
        ("jack.martinez@company.com", "growth_analyst", "Marketing"),
        ("kate.anderson@company.com", "content_manager", "Marketing"),
        ("leo.thomas@company.com", "seo_specialist", "Marketing"),

        # Product
        ("mia.jackson@company.com", "product_manager", "Product"),
        ("noah.white@company.com", "product_analyst", "Product"),
        ("olivia.harris@company.com", "ux_researcher", "Product"),

        # Engineering
        ("peter.martin@company.com", "engineer", "Engineering"),
        ("quinn.thompson@company.com", "devops", "Engineering"),
        ("rachel.garcia@company.com", "security_engineer", "Engineering"),

        # Finance
        ("sam.rodriguez@company.com", "fp&a_analyst", "Finance"),
        ("tina.lewis@company.com", "controller", "Finance"),

        # Customer Success
        ("uma.walker@company.com", "cs_manager", "Customer Success"),
        ("victor.hall@company.com", "support_lead", "Customer Success"),

        # HR & Operations
        ("wendy.allen@company.com", "hr_analyst", "HR"),
        ("xavier.young@company.com", "ops_manager", "Operations"),
        ("yara.king@company.com", "procurement_analyst", "Operations"),
    ]

    for u in users:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, user_type, department) VALUES (?, ?, ?)", u)

    conn.commit()

    cursor.execute("SELECT id, name FROM data_products")
    products_data = cursor.fetchall()

    cursor.execute("SELECT id, user_id FROM users")
    users_data = cursor.fetchall()

    # Realistic usage patterns for each product
    usage_patterns = {
        # High performers (star products)
        "Customer 360": {"base_users": 18, "queries_per_user": 12, "trend": "growing", "power_users": 5},
        "Revenue Dashboard": {"base_users": 15, "queries_per_user": 8, "trend": "growing", "power_users": 4},
        "Product Analytics": {"base_users": 14, "queries_per_user": 15, "trend": "growing", "power_users": 6},

        # Stable performers
        "Sales Pipeline": {"base_users": 12, "queries_per_user": 18, "trend": "stable", "power_users": 4},
        "Campaign Performance": {"base_users": 8, "queries_per_user": 10, "trend": "stable", "power_users": 2},
        "Support Ticket Analytics": {"base_users": 6, "queries_per_user": 8, "trend": "stable", "power_users": 2},
        "Executive KPI Board": {"base_users": 8, "queries_per_user": 3, "trend": "stable", "power_users": 3},
        "API Usage Monitor": {"base_users": 5, "queries_per_user": 6, "trend": "stable", "power_users": 2},

        # Declining products (need attention)
        "Marketing Attribution": {"base_users": 6, "queries_per_user": 4, "trend": "declining", "power_users": 1},
        "Inventory Dashboard": {"base_users": 4, "queries_per_user": 3, "trend": "declining", "power_users": 1},
        "SEO Dashboard": {"base_users": 5, "queries_per_user": 5, "trend": "declining", "power_users": 1},
        "Vendor Scorecard": {"base_users": 3, "queries_per_user": 2, "trend": "declining", "power_users": 0},

        # New products (recently launched, growing)
        "Social Media Analytics": {"base_users": 7, "queries_per_user": 8, "trend": "new_growing", "power_users": 2},
        "Infrastructure Costs": {"base_users": 4, "queries_per_user": 5, "trend": "new_growing", "power_users": 1},

        # Low engagement (struggling)
        "HR Analytics": {"base_users": 4, "queries_per_user": 3, "trend": "low", "power_users": 1},
        "Employee Engagement": {"base_users": 3, "queries_per_user": 2, "trend": "low", "power_users": 0},
        "Security Dashboard": {"base_users": 3, "queries_per_user": 4, "trend": "low", "power_users": 1},
        "Board Reporting": {"base_users": 5, "queries_per_user": 2, "trend": "periodic", "power_users": 2},
    }

    # Data tables that products query
    tables_by_product = {
        "Customer 360": ["customers", "orders", "subscriptions", "support_tickets", "nps_scores"],
        "Revenue Dashboard": ["revenue", "subscriptions", "invoices", "mrr_history", "churn_events"],
        "Sales Pipeline": ["deals", "opportunities", "contacts", "activities", "forecasts"],
        "Product Analytics": ["events", "sessions", "feature_flags", "user_segments", "experiments"],
        "Marketing Attribution": ["campaigns", "touchpoints", "conversions", "utm_tracking", "ad_spend"],
        "Campaign Performance": ["emails", "campaigns", "clicks", "opens", "conversions"],
        "SEO Dashboard": ["keywords", "rankings", "organic_traffic", "backlinks", "competitors"],
        "Social Media Analytics": ["posts", "engagement", "followers", "mentions", "sentiment"],
        "Support Ticket Analytics": ["tickets", "responses", "csat_scores", "sla_metrics", "agents"],
        "Inventory Dashboard": ["inventory", "orders", "shipments", "suppliers", "warehouses"],
        "Vendor Scorecard": ["vendors", "contracts", "deliveries", "quality_scores", "invoices"],
        "HR Analytics": ["employees", "hiring", "attrition", "compensation", "headcount"],
        "Employee Engagement": ["surveys", "responses", "scores", "comments", "action_items"],
        "API Usage Monitor": ["api_calls", "endpoints", "errors", "latency", "rate_limits"],
        "Infrastructure Costs": ["cloud_resources", "billing", "usage", "reserved_instances", "cost_centers"],
        "Security Dashboard": ["vulnerabilities", "incidents", "compliance", "access_logs", "threats"],
        "Executive KPI Board": ["kpis", "okrs", "targets", "actuals", "commentary"],
        "Board Reporting": ["financials", "metrics", "cap_table", "runway", "benchmarks"],
    }

    # Generate 60 days of usage data
    for day_offset in range(60, 0, -1):
        event_date = datetime.now() - timedelta(days=day_offset)
        is_weekend = event_date.weekday() >= 5
        is_month_end = event_date.day >= 28
        is_monday = event_date.weekday() == 0

        for product in products_data:
            product_id, product_name = product
            pattern = usage_patterns.get(product_name, {"base_users": 3, "queries_per_user": 5, "trend": "stable", "power_users": 1})

            # Calculate trend multiplier
            trend_multiplier = 1.0
            if pattern["trend"] == "growing":
                trend_multiplier = 0.6 + (0.6 * (60 - day_offset) / 60)
            elif pattern["trend"] == "declining":
                trend_multiplier = 1.2 - (0.6 * (60 - day_offset) / 60)
            elif pattern["trend"] == "new_growing":
                # New product: starts low, grows fast
                if day_offset > 45:
                    trend_multiplier = 0.2
                else:
                    trend_multiplier = 0.3 + (0.9 * (45 - day_offset) / 45)
            elif pattern["trend"] == "periodic":
                # Periodic usage (e.g., board reporting - spikes at month end)
                trend_multiplier = 2.5 if is_month_end else 0.3
            elif pattern["trend"] == "low":
                trend_multiplier = 0.5 + random.uniform(-0.2, 0.2)

            # Apply day-of-week patterns
            if is_weekend:
                trend_multiplier *= 0.15  # Very low weekend usage for B2B SaaS
            elif is_monday:
                trend_multiplier *= 1.3  # Monday spike

            # Calculate active users
            num_users = int(pattern["base_users"] * trend_multiplier * random.uniform(0.7, 1.3))
            num_users = max(0, min(num_users, len(users_data)))

            if num_users == 0:
                continue

            active_users = random.sample(users_data, num_users)
            product_tables = tables_by_product.get(product_name, ["data"])

            for idx, user in enumerate(active_users):
                user_db_id = user[0]

                # Power users query more
                is_power_user = idx < pattern.get("power_users", 1)
                queries_multiplier = 2.5 if is_power_user else 1.0

                num_queries = int(pattern["queries_per_user"] * queries_multiplier * random.uniform(0.5, 1.5))

                for _ in range(num_queries):
                    tables_accessed = random.sample(product_tables, min(random.randint(1, 3), len(product_tables)))

                    # Query duration varies by complexity
                    base_duration = 500 if is_power_user else 200
                    query_duration = random.randint(base_duration, base_duration + 3000)

                    # Distribute queries throughout work hours
                    hour = random.choices(
                        range(7, 21),
                        weights=[1, 3, 5, 8, 10, 10, 8, 10, 10, 8, 5, 3, 2, 1]  # Peak 10am-4pm
                    )[0]

                    event_time = event_date.replace(
                        hour=hour,
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )

                    event_type = random.choices(
                        ["query", "view", "export", "share"],
                        weights=[70, 20, 7, 3]
                    )[0]

                    cursor.execute('''
                        INSERT INTO usage_events
                        (product_id, user_id, event_type, tables_accessed, query_duration_ms, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (product_id, user_db_id, event_type, json.dumps(tables_accessed), query_duration, event_time))

    conn.commit()
    conn.close()
    print("Comprehensive SaaS demo data seeded successfully!")
