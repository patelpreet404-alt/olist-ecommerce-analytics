-- Distinct-customer calendar-month cohorts. Recent, not-yet-observable cells stay absent.
WITH eligible_orders AS (
    SELECT c.customer_unique_id,
           DATE_TRUNC('month', o.order_purchase_timestamp)::date AS order_month
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
), customer_cohorts AS (
    SELECT customer_unique_id, MIN(order_month) AS cohort_month
    FROM eligible_orders
    GROUP BY customer_unique_id
), cohort_activity AS (
    SELECT e.customer_unique_id, c.cohort_month, e.order_month,
           (EXTRACT(YEAR FROM AGE(e.order_month, c.cohort_month)) * 12
             + EXTRACT(MONTH FROM AGE(e.order_month, c.cohort_month)))::int AS month_index
    FROM eligible_orders AS e
    JOIN customer_cohorts AS c USING (customer_unique_id)
), cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
), active_customers AS (
    SELECT cohort_month, month_index,
           COUNT(DISTINCT customer_unique_id) AS active_customers
    FROM cohort_activity
    WHERE month_index BETWEEN 0 AND 8
    GROUP BY cohort_month, month_index
)
SELECT a.cohort_month, s.cohort_size, a.month_index, a.active_customers,
       ROUND(100.0 * a.active_customers / NULLIF(s.cohort_size, 0), 2) AS retention_pct
FROM active_customers AS a
JOIN cohort_sizes AS s USING (cohort_month)
ORDER BY a.cohort_month, a.month_index;
