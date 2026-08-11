from datetime import date, timedelta
from typing import Optional

from dateutil.parser import parse as parse_date
from sqlalchemy import func

from app import db
from app.models import Sale


def parse_filter_date(value: Optional[str], fallback: date) -> date:
    if not value:
        return fallback
    try:
        return parse_date(value).date()
    except (ValueError, TypeError):
        return fallback


def default_date_range() -> tuple[date, date]:
    end = date.today()
    start = end - timedelta(days=30)
    return start, end


def apply_filters(query, start_date: date, end_date: date, region: str, product: str):
    query = query.filter(Sale.order_date >= start_date, Sale.order_date <= end_date)
    if region:
        query = query.filter(Sale.region == region)
    if product:
        query = query.filter(Sale.product == product)
    return query


def revenue_expression():
    return Sale.quantity * Sale.unit_price


def get_filter_options() -> dict:
    regions = [row[0] for row in db.session.query(Sale.region).distinct().order_by(Sale.region)]
    products = [row[0] for row in db.session.query(Sale.product).distinct().order_by(Sale.product)]
    return {"regions": regions, "products": products}


def get_kpis(start_date: date, end_date: date, region: str, product: str) -> dict:
    revenue = revenue_expression()
    base_query = apply_filters(db.session.query(Sale), start_date, end_date, region, product)

    total_revenue = base_query.with_entities(func.coalesce(func.sum(revenue), 0.0)).scalar() or 0.0
    order_count = base_query.count()
    avg_order_value = total_revenue / order_count if order_count else 0.0

    period_days = (end_date - start_date).days + 1
    prior_end = start_date - timedelta(days=1)
    prior_start = prior_end - timedelta(days=period_days - 1)

    prior_query = apply_filters(db.session.query(Sale), prior_start, prior_end, region, product)
    prior_revenue = prior_query.with_entities(func.coalesce(func.sum(revenue), 0.0)).scalar() or 0.0

    if prior_revenue:
        revenue_change_pct = ((total_revenue - prior_revenue) / prior_revenue) * 100
    else:
        revenue_change_pct = 100.0 if total_revenue else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "order_count": order_count,
        "avg_order_value": round(avg_order_value, 2),
        "revenue_change_pct": round(revenue_change_pct, 1),
    }


def get_revenue_over_time(start_date: date, end_date: date, region: str, product: str) -> dict:
    revenue = revenue_expression()
    period_days = (end_date - start_date).days + 1
    group_by_month = period_days > 90

    rows = (
        apply_filters(db.session.query(Sale), start_date, end_date, region, product)
        .with_entities(Sale.order_date, func.sum(revenue).label("total"))
        .group_by(Sale.order_date)
        .order_by(Sale.order_date)
        .all()
    )

    # Bucket in Python instead of relying on a database-specific date
    # function (e.g. LEFT(date_format(...)) on MySQL, DATE_TRUNC on
    # PostgreSQL, strftime on SQLite) so it works across all backends.
    buckets: dict[str, float] = {}
    for row in rows:
        if group_by_month:
            period = row.order_date.strftime("%Y-%m")
        else:
            period = row.order_date.strftime("%Y-W%W")
        buckets[period] = buckets.get(period, 0.0) + (row.total or 0)

    return {
        "labels": list(buckets.keys()),
        "values": [round(value, 2) for value in buckets.values()],
        "grouping": "month" if group_by_month else "week",
    }


def get_revenue_by_region(start_date: date, end_date: date, region: str, product: str) -> dict:
    revenue = revenue_expression()
    rows = (
        apply_filters(db.session.query(Sale), start_date, end_date, region, product)
        .with_entities(Sale.region, func.sum(revenue).label("total"))
        .group_by(Sale.region)
        .order_by(func.sum(revenue).desc())
        .all()
    )

    return {
        "labels": [row.region for row in rows],
        "values": [round(row.total or 0, 2) for row in rows],
    }


def get_top_products(start_date: date, end_date: date, region: str, product: str, limit: int = 5) -> dict:
    revenue = revenue_expression()
    rows = (
        apply_filters(db.session.query(Sale), start_date, end_date, region, product)
        .with_entities(Sale.product, func.sum(revenue).label("total"))
        .group_by(Sale.product)
        .order_by(func.sum(revenue).desc())
        .limit(limit)
        .all()
    )

    rows = list(reversed(rows))
    return {
        "labels": [row.product for row in rows],
        "values": [round(row.total or 0, 2) for row in rows],
    }


def get_sales_page(
    start_date: date,
    end_date: date,
    region: str,
    product: str,
    page: int = 1,
    per_page: int = 25,
    sort_by: str = "order_date",
    sort_dir: str = "desc",
) -> dict:
    allowed_sorts = {
        "order_date": Sale.order_date,
        "customer": Sale.customer,
        "product": Sale.product,
        "region": Sale.region,
        "quantity": Sale.quantity,
        "revenue": revenue_expression(),
    }
    sort_column = allowed_sorts.get(sort_by, Sale.order_date)
    order_clause = sort_column.desc() if sort_dir == "desc" else sort_column.asc()

    query = apply_filters(db.session.query(Sale), start_date, end_date, region, product)
    total = query.count()
    sales = query.order_by(order_clause).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": [sale.to_dict() for sale in sales],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


def get_metrics(start_date: date, end_date: date, region: str, product: str) -> dict:
    return {
        "kpis": get_kpis(start_date, end_date, region, product),
        "revenue_over_time": get_revenue_over_time(start_date, end_date, region, product),
        "revenue_by_region": get_revenue_by_region(start_date, end_date, region, product),
        "top_products": get_top_products(start_date, end_date, region, product),
    }
