-- Category revenue mix with ranking and cumulative Pareto share.
WITH category_sales AS (
    SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'Uncategorized') AS category,
           SUM(i.price + i.freight_value) AS gmv,
           COUNT(DISTINCT i.order_id) AS eligible_orders
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_id = i.product_id
    LEFT JOIN product_category_name_translation AS t
        ON t.product_category_name = p.product_category_name
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
), ranked AS (
    SELECT category, gmv, eligible_orders,
           DENSE_RANK() OVER (ORDER BY gmv DESC) AS category_rank,
           SUM(gmv) OVER () AS total_gmv,
           SUM(gmv) OVER (ORDER BY gmv DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_gmv
    FROM category_sales
)
SELECT category, category_rank, eligible_orders, ROUND(gmv, 2) AS gmv,
       ROUND(100.0 * gmv / NULLIF(total_gmv, 0), 2) AS gmv_share_pct,
       ROUND(100.0 * cumulative_gmv / NULLIF(total_gmv, 0), 2) AS cumulative_gmv_share_pct
FROM ranked
ORDER BY category_rank, category;
