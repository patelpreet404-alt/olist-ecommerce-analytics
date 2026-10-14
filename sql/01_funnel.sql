-- Order-stage counts at transaction grain. Approval and shipment are timestamp milestones.
WITH stage_counts AS (
    SELECT stage_order, stage,
           COUNT(*) FILTER (WHERE qualifies) AS orders
    FROM (
        SELECT 1 AS stage_order, 'Orders placed' AS stage, TRUE AS qualifies FROM orders
        UNION ALL
        SELECT 2, 'Payment approved', order_approved_at IS NOT NULL FROM orders
        UNION ALL
        SELECT 3, 'Handed to carrier', order_delivered_carrier_date IS NOT NULL FROM orders
        UNION ALL
        SELECT 4, 'Delivered', order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL FROM orders
    ) AS milestones
    GROUP BY stage_order, stage
), progression AS (
    SELECT stage_order, stage, orders,
           FIRST_VALUE(orders) OVER (ORDER BY stage_order) AS placed_orders,
           LAG(orders) OVER (ORDER BY stage_order) AS prior_stage_orders
    FROM stage_counts
)
SELECT stage_order, stage, orders,
       ROUND(100.0 * orders / NULLIF(placed_orders, 0), 2) AS conversion_from_placed_pct,
       COALESCE(prior_stage_orders - orders, 0) AS dropoff_from_prior_stage
FROM progression
ORDER BY stage_order;
