-- ============================================================================
-- OLIST E-COMMERCE GMV PARETO & REVENUE CONCENTRATION ANALYSIS
-- Author: Preet Patel (Delhi Technological University)
-- Description: Analyzes revenue drivers across product categories using Window 
--              Functions to prove top 5 categories generate >40% of Gross Merchandise Value.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CATEGORY PARETO GMV ANALYSIS WITH CUMULATIVE WINDOW FUNCTIONS
-- ----------------------------------------------------------------------------
WITH category_sales AS (
    SELECT 
        COALESCE(t.product_category_name_english, p.product_category_name, 'Other') AS category,
        COUNT(DISTINCT oi.order_id) AS total_orders,
        COUNT(oi.order_item_id) AS items_sold,
        ROUND(SUM(oi.price), 2) AS category_item_gmv,
        ROUND(SUM(oi.freight_value), 2) AS category_freight_value,
        ROUND(SUM(oi.price + oi.freight_value), 2) AS category_total_gmv
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY COALESCE(t.product_category_name_english, p.product_category_name, 'Other')
),
category_ranking AS (
    SELECT 
        category,
        total_orders,
        items_sold,
        category_total_gmv,
        category_item_gmv,
        ROUND(category_total_gmv * 100.0 / SUM(category_total_gmv) OVER(), 2) AS gmv_share_pct,
        ROUND(
            SUM(category_total_gmv) OVER (
                ORDER BY category_total_gmv DESC 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ), 2
        ) AS running_cumulative_gmv,
        ROUND(
            SUM(category_total_gmv) OVER (
                ORDER BY category_total_gmv DESC 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) * 100.0 / SUM(category_total_gmv) OVER(), 2
        ) AS cumulative_gmv_share_pct,
        DENSE_RANK() OVER (ORDER BY category_total_gmv DESC) AS category_rank,
        ROUND(category_total_gmv * 1.0 / total_orders, 2) AS avg_order_value_aov
    FROM category_sales
)
SELECT 
    category_rank,
    category,
    total_orders,
    category_total_gmv,
    avg_order_value_aov,
    gmv_share_pct,
    cumulative_gmv_share_pct,
    CASE 
        WHEN category_rank <= 5 THEN '★ Top 5 Core Driver'
        WHEN cumulative_gmv_share_pct <= 80.0 THEN 'Core Portfolio (80%)'
        ELSE 'Long Tail (20%)'
    END AS pareto_tier
FROM category_ranking
ORDER BY category_rank;

-- ----------------------------------------------------------------------------
-- 2. VERIFY TOP 5 CATEGORY GMV SHARE THRESHOLD (>40% GMV)
-- ----------------------------------------------------------------------------
WITH category_sales AS (
    SELECT 
        COALESCE(t.product_category_name_english, p.product_category_name, 'Other') AS category,
        SUM(oi.price + oi.freight_value) AS total_gmv
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY category
),
ranked_categories AS (
    SELECT 
        category,
        total_gmv,
        DENSE_RANK() OVER (ORDER BY total_gmv DESC) as rk,
        SUM(total_gmv) OVER() AS total_market_gmv
    FROM category_sales
)
SELECT 
    'Top 5 Product Categories' AS segment,
    ROUND(SUM(total_gmv), 2) AS segment_gmv,
    ROUND(MAX(total_market_gmv), 2) AS total_platform_gmv,
    ROUND(SUM(total_gmv) * 100.0 / MAX(total_market_gmv), 2) AS gmv_percentage
FROM ranked_categories
WHERE rk <= 5;

-- ----------------------------------------------------------------------------
-- 3. PAYMENT METHOD REVENUE DISTRIBUTION & INSTALLMENT SPREAD
-- ----------------------------------------------------------------------------
SELECT 
    op.payment_type,
    COUNT(DISTINCT op.order_id) AS total_transactions,
    ROUND(SUM(op.payment_value), 2) AS total_payment_value,
    ROUND(SUM(op.payment_value) * 100.0 / SUM(SUM(op.payment_value)) OVER(), 2) AS payment_share_pct,
    ROUND(AVG(op.payment_installments), 1) AS avg_installments,
    ROUND(AVG(op.payment_value), 2) AS avg_ticket_size
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY op.payment_type
ORDER BY total_payment_value DESC;
