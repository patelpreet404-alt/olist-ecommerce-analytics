"""
Olist E-Commerce Analytics Engine
Author: Preet Patel (Delhi Technological University)
Description: Executes core analytical models: Cohort Retention matrix calculation,
             Conversion Funnel drop-offs, Category GMV Pareto, and Supply Chain SLA metrics.
"""

import sqlite3
import pandas as pd
import numpy as np

class OlistAnalyticsEngine:
    def __init__(self, db_path="data/olist_ecommerce.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def get_funnel_metrics(self):
        """Calculates funnel stages, drop-off volumes, and conversion percentages."""
        query = """
        WITH funnel_stages AS (
            SELECT 1 AS stage_order, '1. Orders Placed' AS stage_name, COUNT(DISTINCT order_id) AS total_orders
            FROM orders
            UNION ALL
            SELECT 2 AS stage_order, '2. Payment Approved' AS stage_name, COUNT(DISTINCT o.order_id) AS total_orders
            FROM orders o
            JOIN order_payments op ON o.order_id = op.order_id
            WHERE o.order_approved_at IS NOT NULL AND o.order_status NOT IN ('canceled', 'unavailable')
            UNION ALL
            SELECT 3 AS stage_order, '3. Shipped to Carrier' AS stage_name, COUNT(DISTINCT order_id) AS total_orders
            FROM orders
            WHERE order_delivered_carrier_date IS NOT NULL AND order_status NOT IN ('canceled', 'unavailable')
            UNION ALL
            SELECT 4 AS stage_order, '4. Delivered to Customer' AS stage_name, COUNT(DISTINCT order_id) AS total_orders
            FROM orders
            WHERE order_delivered_customer_date IS NOT NULL AND order_status = 'delivered'
        ),
        funnel_calc AS (
            SELECT stage_order, stage_name, total_orders,
                   FIRST_VALUE(total_orders) OVER (ORDER BY stage_order) AS top_of_funnel,
                   LAG(total_orders, 1) OVER (ORDER BY stage_order) AS prev_stage
            FROM funnel_stages
        )
        SELECT stage_order, stage_name, total_orders,
               COALESCE(prev_stage - total_orders, 0) AS dropoff_count,
               ROUND(total_orders * 100.0 / top_of_funnel, 2) AS overall_conv_pct,
               ROUND(COALESCE((prev_stage - total_orders) * 100.0 / prev_stage, 0.0), 2) AS stage_dropoff_pct,
               ROUND(COALESCE(total_orders * 100.0 / prev_stage, 100.0), 2) AS stage_retention_pct
        FROM funnel_calc
        ORDER BY stage_order;
        """
        return pd.read_sql_query(query, self.conn)

    def get_cohort_retention_matrix(self):
        """Calculates triangular monthly cohort retention matrix and percentages."""
        query = """
        WITH customer_cohort_base AS (
            SELECT c.customer_unique_id,
                   MIN(STRFTIME('%Y-%m', o.order_purchase_timestamp)) AS cohort_month
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status NOT IN ('canceled', 'unavailable')
            GROUP BY c.customer_unique_id
        ),
        customer_orders AS (
            SELECT c.customer_unique_id,
                   STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status NOT IN ('canceled', 'unavailable')
        ),
        cohort_progression AS (
            SELECT co.customer_unique_id, cb.cohort_month, co.order_month,
                   ((CAST(SUBSTR(co.order_month, 1, 4) AS INT) - CAST(SUBSTR(cb.cohort_month, 1, 4) AS INT)) * 12 + 
                    (CAST(SUBSTR(co.order_month, 6, 2) AS INT) - CAST(SUBSTR(cb.cohort_month, 6, 2) AS INT))) AS month_index
            FROM customer_orders co
            JOIN customer_cohort_base cb ON co.customer_unique_id = cb.customer_unique_id
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(DISTINCT customer_unique_id) AS cohort_size
            FROM customer_cohort_base
            GROUP BY cohort_month
        )
        SELECT cp.cohort_month, cs.cohort_size, cp.month_index,
               COUNT(DISTINCT cp.customer_unique_id) AS active_customers,
               ROUND(COUNT(DISTINCT cp.customer_unique_id) * 100.0 / cs.cohort_size, 2) AS retention_rate_pct
        FROM cohort_progression cp
        JOIN cohort_sizes cs ON cp.cohort_month = cs.cohort_month
        WHERE cp.cohort_month <= '2023-02' AND cp.month_index <= 8
        GROUP BY cp.cohort_month, cs.cohort_size, cp.month_index
        ORDER BY cp.cohort_month, cp.month_index;
        """
        df = pd.read_sql_query(query, self.conn)
        pivot_df = df.pivot(index='cohort_month', columns='month_index', values='retention_rate_pct')
        cohort_sizes = df.groupby('cohort_month')['cohort_size'].first()
        return pivot_df, cohort_sizes

    def get_pareto_gmv(self):
        """Calculates category GMV, cumulative GMV share, and verifies top 5 Pareto share."""
        query = """
        WITH category_sales AS (
            SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'Other') AS category,
                   COUNT(DISTINCT oi.order_id) AS total_orders,
                   ROUND(SUM(oi.price + oi.freight_value), 2) AS total_gmv
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
            WHERE o.order_status NOT IN ('canceled', 'unavailable')
            GROUP BY category
        )
        SELECT category, total_orders, total_gmv,
               ROUND(total_gmv * 100.0 / SUM(total_gmv) OVER(), 2) AS gmv_share_pct,
               ROUND(SUM(total_gmv) OVER (ORDER BY total_gmv DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 / 
                     SUM(total_gmv) OVER(), 2) AS cumulative_gmv_pct,
               DENSE_RANK() OVER (ORDER BY total_gmv DESC) AS category_rank
        FROM category_sales
        ORDER BY total_gmv DESC;
        """
        return pd.read_sql_query(query, self.conn)

    def get_supply_chain_sla(self):
        """Calculates delivery SLA compliance, interstate vs intrastate, and 15% delay reduction."""
        query_state = """
        SELECT c.customer_state,
               COUNT(DISTINCT o.order_id) AS delivered_orders,
               ROUND(AVG(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)), 1) AS avg_delivery_days,
               ROUND(SUM(CASE WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1 ELSE 0 END) * 100.0 / 
                     COUNT(DISTINCT o.order_id), 2) AS late_delivery_rate_pct,
               ROUND(AVG(oi.freight_value), 2) AS avg_freight_cost
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        GROUP BY c.customer_state
        ORDER BY late_delivery_rate_pct DESC;
        """
        
        query_simulation = """
        WITH baseline_delays AS (
            SELECT o.order_id,
                   CASE WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1 ELSE 0 END AS is_delayed_baseline,
                   CASE WHEN ((JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)) - 1.2) > 
                             (JULIANDAY(o.order_estimated_delivery_date) - JULIANDAY(o.order_purchase_timestamp)) 
                        THEN 1 ELSE 0 END AS is_delayed_simulated
            FROM orders o
            WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        )
        SELECT COUNT(order_id) AS total_orders,
               SUM(is_delayed_baseline) AS baseline_delayed,
               ROUND(SUM(is_delayed_baseline) * 100.0 / COUNT(order_id), 2) AS baseline_delay_pct,
               SUM(is_delayed_simulated) AS simulated_delayed,
               ROUND(SUM(is_delayed_simulated) * 100.0 / COUNT(order_id), 2) AS simulated_delay_pct,
               ROUND((SUM(is_delayed_baseline) - SUM(is_delayed_simulated)) * 100.0 / SUM(is_delayed_baseline), 2) AS delay_reduction_pct
        FROM baseline_delays;
        """
        state_df = pd.read_sql_query(query_state, self.conn)
        sim_df = pd.read_sql_query(query_simulation, self.conn)
        return state_df, sim_df

    def close(self):
        self.conn.close()
