# Olist E-Commerce Relational Data Dictionary
**Author:** Preet Patel (Delhi Technological University)  
**Entities:** 9 Normalized Relational Tables (PostgreSQL / SQLite)

---

## 1. `orders` (Master Entity)
Stores the core transaction metadata and progression lifecycle for every order.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `order_id` | VARCHAR(32) | PK | Unique identifier for each customer purchase order. |
| `customer_id` | VARCHAR(32) | FK | References `customers.customer_id` (transaction-specific). |
| `order_status` | VARCHAR(20) | — | Status: `delivered`, `shipped`, `processing`, `canceled`, `unavailable`. |
| `order_purchase_timestamp` | TIMESTAMP | — | Exact date and time the customer placed the order. |
| `order_approved_at` | TIMESTAMP | — | Timestamp when the payment transaction was approved. |
| `order_delivered_carrier_date` | TIMESTAMP | — | Timestamp when the seller handed the package to the logistics carrier. |
| `order_delivered_customer_date` | TIMESTAMP | — | Timestamp when the package was successfully delivered to the customer. |
| `order_estimated_delivery_date` | TIMESTAMP | — | Guaranteed delivery SLA date communicated to the customer at checkout. |

---

## 2. `customers`
Stores customer profile and geographic residence details.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `customer_id` | VARCHAR(32) | PK | Key that ties an individual transaction to an order. |
| `customer_unique_id` | VARCHAR(32) | — | Permanent unique identifier for the customer (used for cohort tracking). |
| `customer_zip_code_prefix` | INT | — | First 5 digits of the customer's postal code. |
| `customer_city` | VARCHAR(64) | — | City of customer residence. |
| `customer_state` | VARCHAR(2) | — | Two-letter Brazilian state abbreviation (`SP`, `RJ`, `MG`, etc.). |

---

## 3. `order_items`
Stores line-item detail for every product included in an order.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `order_id` | VARCHAR(32) | PK, FK | References `orders.order_id`. |
| `order_item_id` | INT | PK | Sequential integer identifying the item number within the order (1, 2, 3...). |
| `product_id` | VARCHAR(32) | FK | References `products.product_id`. |
| `seller_id` | VARCHAR(32) | FK | References `sellers.seller_id`. |
| `shipping_limit_date` | TIMESTAMP | — | Seller dispatch deadline before order cancellation penalties apply. |
| `price` | NUMERIC(10,2) | — | Base purchase price of the individual item in Brazilian Reais (R$). |
| `freight_value` | NUMERIC(10,2) | — | Shipping and handling freight cost assigned to this line item. |

---

## 4. `order_payments`
Stores payment method, installments, and monetary breakdown for orders.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `order_id` | VARCHAR(32) | PK, FK | References `orders.order_id`. |
| `payment_sequential` | INT | PK | Sequence index for split payments (1, 2...). |
| `payment_type` | VARCHAR(20) | — | Method: `credit_card`, `boleto`, `voucher`, `debit_card`. |
| `payment_installments` | INT | — | Number of monthly credit card installments chosen by customer. |
| `payment_value` | NUMERIC(10,2) | — | Total transaction value processed for this payment sequential. |

---

## 5. `order_reviews`
Stores customer post-fulfillment reviews and satisfaction ratings.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `review_id` | VARCHAR(32) | PK | Unique identifier for the customer review. |
| `order_id` | VARCHAR(32) | FK | References `orders.order_id`. |
| `review_score` | INT | — | Customer satisfaction rating on a 1 to 5 integer scale. |
| `review_comment_title` | VARCHAR(128) | — | Optional header title written by the customer. |
| `review_comment_message` | TEXT | — | Full textual comment message describing the experience. |
| `review_creation_date` | TIMESTAMP | — | Timestamp when the survey request was sent to the customer. |
| `review_answer_timestamp` | TIMESTAMP | — | Timestamp when the customer completed the review survey. |

---

## 6. `products`
Stores product catalog specifications, categories, and physical dimensions.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `product_id` | VARCHAR(32) | PK | Unique product SKU identifier. |
| `product_category_name` | VARCHAR(64) | FK | Portuguese category name, references `product_category_name_translation`. |
| `product_name_lenght` | INT | — | Character length of the product listing title. |
| `product_description_lenght`| INT | — | Character length of the product listing description. |
| `product_photos_qty` | INT | — | Number of published product photos on the listing. |
| `product_weight_g` | NUMERIC(10,2) | — | Product weight in grams (used for freight calculations). |
| `product_length_cm` | NUMERIC(6,2) | — | Product packaging length in centimeters. |
| `product_height_cm` | NUMERIC(6,2) | — | Product packaging height in centimeters. |
| `product_width_cm` | NUMERIC(6,2) | — | Product packaging width in centimeters. |

---

## 7. `sellers`
Registry of third-party marketplace merchants fulfilling orders.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `seller_id` | VARCHAR(32) | PK | Unique identifier for each third-party marketplace merchant. |
| `seller_zip_code_prefix` | INT | — | First 5 digits of the seller's warehouse location. |
| `seller_city` | VARCHAR(64) | — | City where seller fulfillment warehouse is situated. |
| `seller_state` | VARCHAR(2) | — | Two-letter Brazilian state abbreviation for seller origin warehouse. |

---

## 8. `geolocation`
Maps Brazilian postal zip code prefixes to geographic latitude and longitude coordinates.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `geolocation_zip_code_prefix` | INT | — | 5-digit zip code prefix. |
| `geolocation_lat` | NUMERIC(10,6)| — | Decimal latitude coordinate. |
| `geolocation_lng` | NUMERIC(10,6)| — | Decimal longitude coordinate. |
| `geolocation_city` | VARCHAR(64) | — | Brazilian municipality name. |
| `geolocation_state` | VARCHAR(2) | — | Brazilian state code abbreviation. |

---

## 9. `product_category_name_translation`
Maps Portuguese category taxonomy to standardized English category names.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `product_category_name` | VARCHAR(64) | PK | Primary category name in Portuguese. |
| `product_category_name_english`| VARCHAR(64)| — | Corresponding English category translation. |
