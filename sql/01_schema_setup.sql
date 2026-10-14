-- ============================================================================
-- OLIST E-COMMERCE RELATIONAL SCHEMA DEFINITION (PostgreSQL / ANSI SQL)
-- Author: Preet Patel (Delhi Technological University)
-- Description: DDL definitions for 9 core relational tables, primary keys, 
--              foreign keys, constraints, and analytical performance indexes.
-- ============================================================================

-- 1. Product Category Name Translation Table
CREATE TABLE IF NOT EXISTS product_category_name_translation (
    product_category_name VARCHAR(64) PRIMARY KEY,
    product_category_name_english VARCHAR(64) NOT NULL
);

-- 2. Products Catalog Table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(64),
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g NUMERIC(10, 2),
    product_length_cm NUMERIC(6, 2),
    product_height_cm NUMERIC(6, 2),
    product_width_cm NUMERIC(6, 2),
    FOREIGN KEY (product_category_name) REFERENCES product_category_name_translation(product_category_name)
);

-- 3. Customers Directory
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix INT NOT NULL,
    customer_city VARCHAR(64) NOT NULL,
    customer_state VARCHAR(2) NOT NULL
);

-- 4. Sellers Directory
CREATE TABLE IF NOT EXISTS sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix INT NOT NULL,
    seller_city VARCHAR(64) NOT NULL,
    seller_state VARCHAR(2) NOT NULL
);

-- 5. Geolocation Lookup Table
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix INT NOT NULL,
    geolocation_lat NUMERIC(10, 6) NOT NULL,
    geolocation_lng NUMERIC(10, 6) NOT NULL,
    geolocation_city VARCHAR(64) NOT NULL,
    geolocation_state VARCHAR(2) NOT NULL
);

-- 6. Orders Master Table
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    order_status VARCHAR(20) NOT NULL CHECK (order_status IN ('delivered', 'shipped', 'processing', 'canceled', 'unavailable', 'invoiced', 'created')),
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 7. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    order_id VARCHAR(32) NOT NULL,
    order_item_id INT NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    seller_id VARCHAR(32) NOT NULL,
    shipping_limit_date TIMESTAMP NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10, 2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

-- 8. Order Payments Table
CREATE TABLE IF NOT EXISTS order_payments (
    order_id VARCHAR(32) NOT NULL,
    payment_sequential INT NOT NULL,
    payment_type VARCHAR(20) NOT NULL,
    payment_installments INT NOT NULL DEFAULT 1,
    payment_value NUMERIC(10, 2) NOT NULL CHECK (payment_value >= 0),
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- 9. Order Reviews Table
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    review_score INT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title VARCHAR(128),
    review_comment_message TEXT,
    review_creation_date TIMESTAMP NOT NULL,
    review_answer_timestamp TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- ============================================================================
-- PERFORMANCE INDEXES (Optimized for Analytical Window Functions & CTE Joins)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_timestamp ON orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_customers_unique_id ON customers(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(customer_state);
CREATE INDEX IF NOT EXISTS idx_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_items_seller_id ON order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_payments_type ON order_payments(payment_type);
CREATE INDEX IF NOT EXISTS idx_reviews_score ON order_reviews(review_score);
