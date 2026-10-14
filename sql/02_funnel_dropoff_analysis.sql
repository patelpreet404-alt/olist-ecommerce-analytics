-- ============================================================================
-- OLIST E-COMMERCE CONVERSION FUNNEL & DROPOFF ANALYSIS
-- Author: Preet Patel (Delhi Technological University)
-- Description: Analyzes end-to-end order funnel progression across 4 stages,
--              calculating stage drop-offs, survival rates, and bottleneck friction.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. STAGE METRICS & DROP-OFF WITH WINDOW FUNCTIONS
-- ----------------------------------------------------------------------------
WITH funnel_stages AS (
    SELECT 
        1 AS stage_order,
        '1. Orders Placed' AS stage_name,
        COUNT(DISTINCT order_id) AS total_orders
    FROM orders
    
    UNION ALL
    
    SELECT 
        2 AS stage_order,
        '2. Payment Approved' AS stage_name,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM orders o
    JOIN order_payments op ON o.order_id = op.order_id
    WHERE o.order_approved_at IS NOT NULL
      AND o.order_status NOT IN ('canceled', 'unavailable')
      
    UNION ALL
    
    SELECT 
        3 AS stage_order,
        '3. Shipped to Carrier' AS stage_name,
        COUNT(DISTINCT order_id) AS total_orders
    FROM orders
    WHERE order_delivered_carrier_date IS NOT NULL
      AND order_status NOT IN ('canceled', 'unavailable')
      
    UNION ALL
    
    SELECT 
        4 AS stage_order,
        '4. Delivered to Customer' AS stage_name,
        COUNT(DISTINCT order_id) AS total_orders
    FROM orders
    WHERE order_delivered_customer_date IS NOT NULL
      AND order_status = 'delivered'
),
funnel_calculations AS (
    SELECT
        stage_order,
        stage_name,
        total_orders,
        FIRST_VALUE(total_orders) OVER (ORDER BY stage_order) AS top_of_funnel_orders,
        LAG(total_orders, 1) OVER (ORDER BY stage_order) AS prev_stage_orders
    FROM funnel_stages
)
SELECT
    stage_order,
    stage_name,
    total_orders,
    COALESCE(prev_stage_orders - total_orders, 0) AS stage_dropoff_count,
    ROUND(total_orders * 100.0 / top_of_funnel_orders, 2) AS overall_conversion_pct,
    ROUND(
        COALESCE(
            (prev_stage_orders - total_orders) * 100.0 / prev_stage_orders, 
            0.0
        ), 2
    ) AS stage_dropoff_pct,
    ROUND(
        COALESCE(
            total_orders * 100.0 / prev_stage_orders, 
            100.0
        ), 2
    ) AS stage_retention_pct
FROM funnel_calculations
ORDER BY stage_order;

-- ----------------------------------------------------------------------------
-- 2. CANCELLATION & UNFULFILLED ORDERS ROOT-CAUSE BREAKDOWN
-- ----------------------------------------------------------------------------
SELECT 
    order_status,
    COUNT(order_id) AS order_count,
    ROUND(COUNT(order_id) * 100.0 / SUM(COUNT(order_id)) OVER(), 2) AS status_pct,
    ROUND(SUM(op.payment_value), 2) AS lost_or_realized_revenue,
    ROUND(AVG(op.payment_value), 2) AS avg_ticket_size
FROM orders o
LEFT JOIN order_payments op ON o.order_id = op.order_id
GROUP BY order_status
ORDER BY order_count DESC;

-- ----------------------------------------------------------------------------
-- 3. FULFILLMENT LATENCY BOTTLENECKS (Approval vs Dispatch vs Transit)
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(order_id) AS delivered_orders,
    ROUND(AVG((JULIANDAY(order_approved_at) - JULIANDAY(order_purchase_timestamp)) * 24.0), 2) AS avg_approval_latency_hours,
    ROUND(AVG(JULIANDAY(order_delivered_carrier_date) - JULIANDAY(order_approved_at)), 2) AS avg_dispatch_latency_days,
    ROUND(AVG(JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_delivered_carrier_date)), 2) AS avg_carrier_transit_days,
    ROUND(AVG(JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_purchase_timestamp)), 2) AS avg_total_delivery_days
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_delivered_carrier_date IS NOT NULL
  AND order_approved_at IS NOT NULL;
