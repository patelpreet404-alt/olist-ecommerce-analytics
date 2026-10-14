-- Compute at order grain before any line-item joins to avoid duplicating delayed orders.
WITH delivered_orders AS (
    SELECT o.order_id, c.customer_state,
           EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) / 86400.0 AS transit_days,
           (o.order_delivered_customer_date > o.order_estimated_delivery_date) AS is_late
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
)
SELECT customer_state,
       COUNT(DISTINCT order_id) AS delivered_orders,
       COUNT(DISTINCT order_id) FILTER (WHERE is_late) AS late_orders,
       ROUND(100.0 * COUNT(DISTINCT order_id) FILTER (WHERE is_late)
             / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS late_delivery_pct,
       ROUND(AVG(transit_days)::numeric, 1) AS average_transit_days
FROM delivered_orders
GROUP BY customer_state
ORDER BY late_delivery_pct DESC, delivered_orders DESC;
