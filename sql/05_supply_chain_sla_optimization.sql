-- ============================================================================
-- OLIST E-COMMERCE SUPPLY CHAIN & SLA OPTIMIZATION MODEL
-- Author: Preet Patel (Delhi Technological University)
-- Description: Analyzes fulfillment lead times, SLA variance against estimated 
--              delivery dates, and models a 15% reduction in delivery delays.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CARRIER SLA PERFORMANCE & ON-TIME DELIVERY RATE
-- ----------------------------------------------------------------------------
WITH delivery_sla_base AS (
    SELECT 
        order_id,
        order_purchase_timestamp,
        order_delivered_customer_date,
        order_estimated_delivery_date,
        -- Calculate actual delivery duration from purchase
        ROUND(JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_purchase_timestamp), 2) AS actual_delivery_days,
        -- Calculate estimated SLA duration promised to customer
        ROUND(JULIANDAY(order_estimated_delivery_date) - JULIANDAY(order_purchase_timestamp), 2) AS promised_sla_days,
        -- SLA variance: negative means delivered early, positive means delayed past SLA
        ROUND(JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_estimated_delivery_date), 2) AS delay_days_vs_sla,
        CASE 
            WHEN JULIANDAY(order_delivered_customer_date) <= JULIANDAY(order_estimated_delivery_date) THEN 'On-Time / Early'
            ELSE 'Delayed Past SLA'
        END AS sla_compliance_status
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
)
SELECT 
    sla_compliance_status,
    COUNT(order_id) AS total_orders,
    ROUND(COUNT(order_id) * 100.0 / SUM(COUNT(order_id)) OVER(), 2) AS percentage_of_deliveries,
    ROUND(AVG(actual_delivery_days), 1) AS avg_actual_delivery_days,
    ROUND(AVG(promised_sla_days), 1) AS avg_promised_sla_days,
    ROUND(AVG(delay_days_vs_sla), 2) AS avg_sla_variance_days
FROM delivery_sla_base
GROUP BY sla_compliance_status;

-- ----------------------------------------------------------------------------
-- 2. GEOGRAPHIC DELIVERY BOTTLENECKS (Customer State vs SLA Delays)
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS delivered_orders,
    ROUND(AVG(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)), 1) AS avg_delivery_days,
    ROUND(
        SUM(CASE WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(DISTINCT o.order_id), 2
    ) AS late_delivery_rate_pct,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight_cost
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
HAVING COUNT(DISTINCT o.order_id) >= 100
ORDER BY late_delivery_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- 3. INTERSTATE VS INTRASTATE LOGISTICS FRICTION
-- ----------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN s.seller_state = c.customer_state THEN 'Intrastate (Same State)'
        ELSE 'Interstate (Cross-Border)'
    END AS shipping_corridor,
    COUNT(DISTINCT o.order_id) AS total_shipments,
    ROUND(AVG(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_delivered_carrier_date)), 1) AS avg_carrier_transit_days,
    ROUND(
        SUM(CASE WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(DISTINCT o.order_id), 2
    ) AS delayed_orders_pct,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight_value
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_carrier_date IS NOT NULL
GROUP BY shipping_corridor;

-- ----------------------------------------------------------------------------
-- 4. SIMULATION: 15% DELIVERY DELAY REDUCTION VIA OPTIMIZATION
-- Process changes:
--   a) 24-hour seller dispatch SLA (reduces approval-to-carrier handoff by 1.0 day)
--   b) Regional cross-docking fulfillment hubs for high-delay states (BA, RJ, PE)
-- ----------------------------------------------------------------------------
WITH baseline_delays AS (
    SELECT 
        o.order_id,
        c.customer_state,
        JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp) AS actual_days,
        JULIANDAY(o.order_estimated_delivery_date) - JULIANDAY(o.order_purchase_timestamp) AS promised_days,
        CASE WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1 ELSE 0 END AS is_delayed_baseline,
        -- Simulated improved delivery: 1.2 days saved via dispatch cutoff & routing
        (JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)) - 1.2 AS simulated_delivery_days,
        CASE 
            WHEN ((JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)) - 1.2) > 
                 (JULIANDAY(o.order_estimated_delivery_date) - JULIANDAY(o.order_purchase_timestamp)) 
            THEN 1 ELSE 0 
        END AS is_delayed_simulated
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
)
SELECT 
    COUNT(order_id) AS total_orders_delivered,
    SUM(is_delayed_baseline) AS baseline_delayed_orders,
    ROUND(SUM(is_delayed_baseline) * 100.0 / COUNT(order_id), 2) AS baseline_delay_rate_pct,
    SUM(is_delayed_simulated) AS simulated_delayed_orders,
    ROUND(SUM(is_delayed_simulated) * 100.0 / COUNT(order_id), 2) AS simulated_delay_rate_pct,
    ROUND(
        (SUM(is_delayed_baseline) - SUM(is_delayed_simulated)) * 100.0 / SUM(is_delayed_baseline), 
        2
    ) AS total_delay_reduction_pct
FROM baseline_delays;
