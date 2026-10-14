#!/usr/bin/env python3
"""Build the browser-ready analytical snapshot from a compatible SQLite database.

The source file is intentionally supplied with --db; no sibling-repository path
or connection is required at runtime. All order-level delivery metrics aggregate
before joining item rows so multi-item baskets cannot inflate counts.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {
    "all": None,
    "southeast": ["SP", "RJ", "MG", "ES"],
    "northeast": ["BA", "PE", "CE", "MA", "PB", "RN", "AL", "SE", "PI"],
    "south": ["PR", "RS", "SC"],
}
REGION_LABELS = {"all": "All regions", "southeast": "Southeast", "northeast": "Northeast", "south": "South"}


def rows(conn: sqlite3.Connection, query: str, params=()):
    return [dict(row) for row in conn.execute(query, params).fetchall()]


def region_where(region: str, column: str = "c.customer_state"):
    states = REGIONS[region]
    if states is None:
        return "", ()
    marks = ",".join("?" for _ in states)
    return f" AND {column} IN ({marks})", tuple(states)


def build(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        table_counts = rows(conn, """SELECT name AS table_name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name""")
        tables = [{"name": r["table_name"], "rows": conn.execute(f' SELECT COUNT(*) FROM "{r["table_name"]}"').fetchone()[0]} for r in table_counts]

        span = conn.execute("""SELECT MIN(date(order_purchase_timestamp)), MAX(date(order_purchase_timestamp)),
            COUNT(*) FROM orders""").fetchone()
        order_items = conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
        base_cte = """WITH eligible AS (
            SELECT o.order_id, o.customer_id, c.customer_unique_id, o.order_status,
                   substr(o.order_purchase_timestamp,1,7) AS month,
                   c.customer_state, o.order_purchase_timestamp, o.order_approved_at,
                   o.order_delivered_carrier_date, o.order_delivered_customer_date,
                   o.order_estimated_delivery_date
            FROM orders o JOIN customers c ON c.customer_id=o.customer_id
            WHERE o.order_status NOT IN ('canceled','unavailable')
        ), order_value AS (
            SELECT order_id, SUM(price) AS item_sales, SUM(freight_value) AS freight,
                   SUM(price+freight_value) AS gmv, COUNT(*) AS items
            FROM order_items GROUP BY order_id
        )"""

        summaries = {}
        monthly = {}
        funnels = {}
        cohorts = {}
        categories = {}
        fulfillment = {}

        for region in REGIONS:
            condition, params = region_where(region, "e.customer_state")
            common = base_cte + """
            SELECT e.*, COALESCE(v.gmv,0) AS gmv, COALESCE(v.item_sales,0) AS item_sales,
                   COALESCE(v.freight,0) AS freight
            FROM eligible e LEFT JOIN order_value v ON v.order_id=e.order_id WHERE 1=1"""
            # Region applies consistently to the buying customer's order.
            region_rows = rows(conn, common + condition, params)
            orders = len(region_rows)
            gmv = sum(r["gmv"] for r in region_rows)
            customers = len({r["customer_unique_id"] for r in region_rows})
            delivered = [r for r in region_rows if r["order_status"] == "delivered" and r["order_delivered_customer_date"]]
            late = [r for r in delivered if r["order_delivered_customer_date"] > r["order_estimated_delivery_date"]]
            summaries[region] = {
                "eligibleOrders": orders,
                "gmv": round(gmv, 2),
                "aov": round(gmv / orders, 2) if orders else 0,
                "customers": customers,
                "deliveredOrders": len(delivered),
                "lateOrders": len(late),
                "lateRate": round(100 * len(late) / len(delivered), 2) if delivered else 0,
                "averageDeliveryDays": round(sum((sqlite_datetime(r["order_delivered_customer_date"]) - sqlite_datetime(r["order_purchase_timestamp"])).total_seconds() / 86400 for r in delivered) / len(delivered), 1) if delivered else 0,
            }

            month_bins = defaultdict(lambda: {"orders": 0, "gmv": 0.0, "customers": set()})
            for r in region_rows:
                bin_ = month_bins[r["month"]]
                bin_["orders"] += 1
                bin_["gmv"] += r["gmv"]
                bin_["customers"].add(r["customer_unique_id"])
            monthly[region] = [{"month": key, "orders": val["orders"], "gmv": round(val["gmv"], 2), "customers": len(val["customers"])} for key, val in sorted(month_bins.items())]

            # Stage qualification is timestamp-based. Each stage is counted at order grain.
            funnel_condition, funnel_params = region_where(region, "c.customer_state")
            funnel_counts = conn.execute("""SELECT COUNT(*) AS placed,
                SUM(CASE WHEN o.order_approved_at IS NOT NULL THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN o.order_delivered_carrier_date IS NOT NULL THEN 1 ELSE 0 END) AS shipped,
                SUM(CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL THEN 1 ELSE 0 END) AS delivered
                FROM orders o JOIN customers c ON c.customer_id=o.customer_id WHERE 1=1""" + funnel_condition, funnel_params).fetchone()
            placed, approved, shipped, delivered_count = (funnel_counts["placed"] or 0, funnel_counts["approved"] or 0, funnel_counts["shipped"] or 0, funnel_counts["delivered"] or 0)
            stage_rows = [("Orders placed", placed), ("Payment approved", approved), ("Handed to carrier", shipped), ("Delivered", delivered_count)]
            funnels[region] = [{"stage": name, "orders": count, "conversion": round(100 * count / placed, 1) if placed else 0, "dropoff": max(0, stage_rows[i-1][1]-count) if i else 0} for i, (name, count) in enumerate(stage_rows)]

            active_orders = [r for r in region_rows if r["order_status"] not in ("canceled", "unavailable")]
            first_month = {}
            for r in active_orders:
                key = r["customer_unique_id"]
                first_month[key] = min(first_month.get(key, r["month"]), r["month"])
            customer_months = defaultdict(set)
            for r in active_orders:
                customer_months[r["customer_unique_id"]].add(r["month"])
            cohort_members = defaultdict(set)
            cohort_activity = defaultdict(set)
            for customer, cohort in first_month.items():
                cohort_members[cohort].add(customer)
                for month in customer_months[customer]:
                    idx = month_index(cohort, month)
                    if 0 <= idx <= 8:
                        cohort_activity[(cohort, idx)].add(customer)
            cohort_rows = []
            for cohort in sorted(cohort_members):
                size = len(cohort_members[cohort])
                counts = [len(cohort_activity.get((cohort, idx), set())) for idx in range(9)]
                cohort_rows.append({"month": cohort, "size": size, "retention": [round(100 * n / size, 1) if idx == 0 else (round(100 * n / size, 1) if month_index(cohort, span[1][:7]) >= idx else None) for idx, n in enumerate(counts)]})
            cohorts[region] = cohort_rows
            mature_cohorts = [(row["size"], row["retention"][2]) for row in cohort_rows if row["retention"][2] is not None]
            summaries[region]["month2Retention"] = round(sum(size * rate for size, rate in mature_cohorts) / sum(size for size, _ in mature_cohorts), 1) if mature_cohorts else None

            category_condition, category_params = region_where(region, "e.customer_state")
            category_rows = rows(conn, base_cte + """
              SELECT COALESCE(t.product_category_name_english,p.product_category_name,'Uncategorized') AS category,
                     SUM(oi.price+oi.freight_value) AS gmv, COUNT(DISTINCT oi.order_id) AS orders
              FROM eligible e JOIN order_items oi ON oi.order_id=e.order_id
              JOIN products p ON p.product_id=oi.product_id
              LEFT JOIN product_category_name_translation t ON t.product_category_name=p.product_category_name
              WHERE 1=1""" + category_condition + " GROUP BY category ORDER BY gmv DESC", category_params)
            denom = sum(r["gmv"] for r in category_rows)
            running = 0
            categories[region] = []
            for r in category_rows:
                running += r["gmv"]
                categories[region].append({"category": r["category"], "gmv": round(r["gmv"], 2), "share": round(100*r["gmv"]/denom, 2) if denom else 0, "cumulativeShare": round(100*running/denom, 2) if denom else 0, "orders": r["orders"]})

            state_condition, state_params = region_where(region, "c.customer_state")
            state_rows = rows(conn, base_cte + """
              SELECT c.customer_state AS state, COUNT(*) AS deliveredOrders,
                     SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS lateOrders,
                     AVG(julianday(o.order_delivered_customer_date)-julianday(o.order_purchase_timestamp)) AS averageDays
              FROM orders o JOIN customers c ON c.customer_id=o.customer_id
              WHERE o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL""" + state_condition + " GROUP BY c.customer_state ORDER BY lateOrders*1.0/COUNT(*) DESC", state_params)
            fulfillment[region] = [{"state": r["state"], "deliveredOrders": r["deliveredOrders"], "lateOrders": r["lateOrders"], "lateRate": round(100*r["lateOrders"]/r["deliveredOrders"],1) if r["deliveredOrders"] else 0, "averageDays": round(r["averageDays"] or 0,1)} for r in state_rows]

        m2 = summaries["all"]["month2Retention"]
        eligible = summaries["all"]
        funnel = funnels["all"]
        top5_share = round(sum(c["share"] for c in categories["all"][:5]),1)
        return {
            "meta": {"datasetName": "Marketplace operations demo", "provenance": "Synthetic data generated for portfolio demonstration; not the public Olist records.", "currency": "BRL", "periodStart": span[0], "periodEnd": span[1], "tableCount": len(tables), "sourceOrderRows": span[2], "orderItemRows": order_items, "tables": tables},
            "regions": [{"id": key, "label": REGION_LABELS[key]} for key in REGIONS],
            "summaryByRegion": summaries,
            "monthlyByRegion": monthly,
            "funnelByRegion": funnels,
            "cohortsByRegion": cohorts,
            "categoriesByRegion": categories,
            "fulfillmentByRegion": fulfillment,
            "benchmarks": {"month2Retention": m2, "topFiveCategoryShare": top5_share, "funnelConversion": funnel[-1]["conversion"] if funnel else 0, "lateRate": eligible["lateRate"], "gmv": eligible["gmv"]},
        }
    finally:
        conn.close()


def sqlite_datetime(value: str):
    from datetime import datetime
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def month_index(start: str, end: str) -> int:
    sy, sm = map(int, start.split("-")[:2])
    ey, em = map(int, end.split("-")[:2])
    return (ey-sy)*12 + (em-sm)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "data/olist_ecommerce.db", help="SQLite source database")
    parser.add_argument("--out", type=Path, default=ROOT / "public/analytics.json", help="Output JSON snapshot")
    args = parser.parse_args()
    payload = build(args.db)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {args.out} ({args.out.stat().st_size:,} bytes); {payload['meta']['sourceOrderRows']:,} source orders")
