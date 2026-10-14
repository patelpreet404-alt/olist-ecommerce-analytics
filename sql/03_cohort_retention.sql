-- ============================================================================
-- OLIST E-COMMERCE COHORT RETENTION MODEL (SQL Window Functions & CTEs)
-- Author: Preet Patel (Delhi Technological University)
-- Description: Measures repeat purchase behavior by monthly acquisition cohorts,
--              identifying the critical 30-35% Month-2 retention baseline.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. MONTHLY COHORT RETENTION MATRIX (Acquisition Month vs Purchase Month Index)
-- ----------------------------------------------------------------------------
WITH customer_cohort_base AS (
    -- Identify the first purchase month (Cohort) for each unique customer
    SELECT 
        c.customer_unique_id,
        MIN(STRFTIME('%Y-%m', o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
),
customer_orders AS (
    -- Extract all successful orders and their purchase month
    SELECT 
        c.customer_unique_id,
        STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month,
        o.order_id
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
cohort_progression AS (
    -- Calculate month index: relative months since cohort acquisition
    SELECT 
        co.customer_unique_id,
        cb.cohort_month,
        co.order_month,
        -- Calculate integer month difference between cohort_month and order_month
        ((CAST(SUBSTR(co.order_month, 1, 4) AS INT) - CAST(SUBSTR(cb.cohort_month, 1, 4) AS INT)) * 12 + 
         (CAST(SUBSTR(co.order_month, 6, 2) AS INT) - CAST(SUBSTR(cb.cohort_month, 6, 2) AS INT))) AS month_index
    FROM customer_orders co
    JOIN customer_cohort_base cb ON co.customer_unique_id = cb.customer_unique_id
),
cohort_sizes AS (
    -- Determine base customer count for each acquisition cohort (Month 0)
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM customer_cohort_base
    GROUP BY cohort_month
),
retention_matrix AS (
    SELECT 
        cp.cohort_month,
        cs.cohort_size,
        cp.month_index,
        COUNT(DISTINCT cp.customer_unique_id) AS active_customers,
        ROUND(COUNT(DISTINCT cp.customer_unique_id) * 100.0 / cs.cohort_size, 2) AS retention_rate_pct
    FROM cohort_progression cp
    JOIN cohort_sizes cs ON cp.cohort_month = cs.cohort_month
    GROUP BY cp.cohort_month, cs.cohort_size, cp.month_index
)
-- Display the Retention Matrix across Month 0 to Month 6
SELECT 
    cohort_month,
    cohort_size,
    MAX(CASE WHEN month_index = 0 THEN retention_rate_pct END) AS M0_pct,
    MAX(CASE WHEN month_index = 1 THEN retention_rate_pct END) AS M1_pct,
    MAX(CASE WHEN month_index = 2 THEN retention_rate_pct END) AS M2_pct,
    MAX(CASE WHEN month_index = 3 THEN retention_rate_pct END) AS M3_pct,
    MAX(CASE WHEN month_index = 4 THEN retention_rate_pct END) AS M4_pct,
    MAX(CASE WHEN month_index = 5 THEN retention_rate_pct END) AS M5_pct,
    MAX(CASE WHEN month_index = 6 THEN retention_rate_pct END) AS M6_pct
FROM retention_matrix
WHERE cohort_month <= '2023-02' -- Ensure minimum 6 months of observation window
GROUP BY cohort_month, cohort_size
ORDER BY cohort_month;

-- ----------------------------------------------------------------------------
-- 2. OVERALL AGGREGATED RETENTION BENCHMARK BY MONTH INDEX
-- ----------------------------------------------------------------------------
WITH customer_cohort_base AS (
    SELECT 
        c.customer_unique_id,
        MIN(STRFTIME('%Y-%m', o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
),
customer_orders AS (
    SELECT 
        c.customer_unique_id,
        STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
cohort_progression AS (
    SELECT 
        co.customer_unique_id,
        cb.cohort_month,
        ((CAST(SUBSTR(co.order_month, 1, 4) AS INT) - CAST(SUBSTR(cb.cohort_month, 1, 4) AS INT)) * 12 + 
         (CAST(SUBSTR(co.order_month, 6, 2) AS INT) - CAST(SUBSTR(cb.cohort_month, 6, 2) AS INT))) AS month_index
    FROM customer_orders co
    JOIN customer_cohort_base cb ON co.customer_unique_id = cb.customer_unique_id
)
SELECT 
    month_index,
    COUNT(DISTINCT customer_unique_id) AS active_repeat_users,
    ROUND(
        COUNT(DISTINCT customer_unique_id) * 100.0 / 
        (SELECT COUNT(DISTINCT customer_unique_id) FROM customer_cohort_base), 
        2
    ) AS cohort_retention_pct
FROM cohort_progression
WHERE month_index BETWEEN 0 AND 12
GROUP BY month_index
ORDER BY month_index;
