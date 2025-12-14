from datetime import datetime, timedelta
from models import get_db
import json


def get_dau_wau_mau(product_id: int) -> dict:
    """Calculate Daily, Weekly, Monthly Active Users"""
    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # DAU - unique users today
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM usage_events
        WHERE product_id = ? AND DATE(timestamp) = DATE('now')
    ''', (product_id,))
    dau = cursor.fetchone()[0]

    # WAU - unique users in last 7 days
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM usage_events
        WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
    ''', (product_id,))
    wau = cursor.fetchone()[0]

    # MAU - unique users in last 30 days
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM usage_events
        WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-30 days')
    ''', (product_id,))
    mau = cursor.fetchone()[0]

    conn.close()
    return {"dau": dau, "wau": wau, "mau": mau}


def calculate_adoption_score(product_id: int, total_users: int) -> float:
    """
    Adoption Score: What % of potential users are using this product?
    Score 0-100
    """
    if total_users == 0:
        return 0

    metrics = get_dau_wau_mau(product_id)
    mau = metrics["mau"]

    # Adoption = MAU / Total potential users
    adoption = (mau / total_users) * 100
    return min(100, round(adoption, 1))


def calculate_stickiness_score(product_id: int) -> float:
    """
    Stickiness Score: DAU/MAU ratio - how often do users come back?
    Higher = users come back daily
    Score 0-100
    """
    metrics = get_dau_wau_mau(product_id)
    mau = metrics["mau"]
    dau = metrics["dau"]

    if mau == 0:
        return 0

    # DAU/MAU ratio (typically 10-20% is good for enterprise tools)
    stickiness = (dau / mau) * 100
    # Normalize: 20% DAU/MAU = 100 score
    normalized = min(100, (stickiness / 20) * 100)
    return round(normalized, 1)


def calculate_abandonment_risk(product_id: int) -> float:
    """
    Abandonment Risk: Is usage declining?
    Compares recent week vs previous week
    Score 0-100 (higher = more risk)
    """
    conn = get_db()
    cursor = conn.cursor()

    # Users in last 7 days
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM usage_events
        WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
    ''', (product_id,))
    recent_users = cursor.fetchone()[0]

    # Users 7-14 days ago
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM usage_events
        WHERE product_id = ?
        AND DATE(timestamp) >= DATE('now', '-14 days')
        AND DATE(timestamp) < DATE('now', '-7 days')
    ''', (product_id,))
    previous_users = cursor.fetchone()[0]

    # Query frequency trend
    cursor.execute('''
        SELECT COUNT(*) FROM usage_events
        WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
    ''', (product_id,))
    recent_queries = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM usage_events
        WHERE product_id = ?
        AND DATE(timestamp) >= DATE('now', '-14 days')
        AND DATE(timestamp) < DATE('now', '-7 days')
    ''', (product_id,))
    previous_queries = cursor.fetchone()[0]

    conn.close()

    if previous_users == 0 and previous_queries == 0:
        return 50  # New product, uncertain

    # Calculate decline percentages
    user_decline = 0
    if previous_users > 0:
        user_decline = ((previous_users - recent_users) / previous_users) * 100

    query_decline = 0
    if previous_queries > 0:
        query_decline = ((previous_queries - recent_queries) / previous_queries) * 100

    # Combined risk score
    risk = (user_decline * 0.6 + query_decline * 0.4)
    risk = max(0, min(100, risk))

    return round(risk, 1)


def get_usage_trend(product_id: int) -> str:
    """Determine if usage is growing, stable, or declining"""
    risk = calculate_abandonment_risk(product_id)

    if risk < 20:
        return "growing"
    elif risk < 40:
        return "stable"
    else:
        return "declining"


def get_query_frequency(product_id: int, days: int = 30) -> list:
    """Get daily query counts for charting"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM usage_events
        WHERE product_id = ? AND DATE(timestamp) >= DATE('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY date
    ''', (product_id, f'-{days} days'))

    results = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    return results


def get_user_type_breakdown(product_id: int) -> list:
    """Get breakdown of users by type"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.user_type, COUNT(DISTINCT ue.user_id) as count
        FROM usage_events ue
        JOIN users u ON ue.user_id = u.id
        WHERE ue.product_id = ? AND DATE(ue.timestamp) >= DATE('now', '-30 days')
        GROUP BY u.user_type
    ''', (product_id,))

    results = [{"type": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    return results


def get_tables_accessed(product_id: int) -> list:
    """Get most accessed tables"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT tables_accessed FROM usage_events
        WHERE product_id = ? AND DATE(timestamp) >= DATE('now', '-30 days')
    ''', (product_id,))

    table_counts = {}
    for row in cursor.fetchall():
        if row[0]:
            tables = json.loads(row[0])
            for table in tables:
                table_counts[table] = table_counts.get(table, 0) + 1

    conn.close()

    sorted_tables = sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"table": t[0], "count": t[1]} for t in sorted_tables]


def get_retention_cohorts(product_id: int) -> list:
    """Calculate weekly retention cohorts"""
    conn = get_db()
    cursor = conn.cursor()

    cohorts = []

    for week_offset in range(4, 0, -1):
        week_start = f'-{week_offset * 7} days'
        week_end = f'-{(week_offset - 1) * 7} days'

        # Users who first used in this week
        cursor.execute('''
            SELECT DISTINCT user_id FROM usage_events
            WHERE product_id = ?
            AND DATE(timestamp) >= DATE('now', ?)
            AND DATE(timestamp) < DATE('now', ?)
            AND user_id NOT IN (
                SELECT DISTINCT user_id FROM usage_events
                WHERE product_id = ?
                AND DATE(timestamp) < DATE('now', ?)
            )
        ''', (product_id, week_start, week_end, product_id, week_start))

        cohort_users = [row[0] for row in cursor.fetchall()]
        cohort_size = len(cohort_users)

        if cohort_size == 0:
            continue

        # Check retention for subsequent weeks
        retention = [100]  # Week 0 is always 100%

        for future_week in range(week_offset - 1, 0, -1):
            future_start = f'-{future_week * 7} days'
            future_end = f'-{(future_week - 1) * 7} days' if future_week > 1 else 'now'

            if cohort_users:
                placeholders = ','.join('?' * len(cohort_users))
                cursor.execute(f'''
                    SELECT COUNT(DISTINCT user_id) FROM usage_events
                    WHERE product_id = ?
                    AND user_id IN ({placeholders})
                    AND DATE(timestamp) >= DATE('now', ?)
                    AND DATE(timestamp) < DATE('now', ?)
                ''', [product_id] + cohort_users + [future_start, future_end if future_end != 'now' else '+1 day'])

                retained = cursor.fetchone()[0]
                retention_pct = round((retained / cohort_size) * 100)
                retention.append(retention_pct)

        cohorts.append({
            "week": f"Week {5 - week_offset}",
            "cohort_size": cohort_size,
            "retention": retention
        })

    conn.close()
    return cohorts


def get_all_product_scores() -> list:
    """Get scores for all products"""
    conn = get_db()
    cursor = conn.cursor()

    # Get total user count
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT id, name, description, owner FROM data_products")
    products = cursor.fetchall()

    scores = []
    for product in products:
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
    """Get detailed analytics for a single product"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT id, name, description, owner FROM data_products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return None

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
        "query_frequency": get_query_frequency(product_id),
        "user_types": get_user_type_breakdown(product_id),
        "tables_accessed": get_tables_accessed(product_id),
        "retention_cohorts": get_retention_cohorts(product_id)
    }

    conn.close()
    return details
