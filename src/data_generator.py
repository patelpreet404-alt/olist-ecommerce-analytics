"""
Olist E-Commerce Realistic Relational Dataset Generator
Author: Preet Patel (Delhi Technological University)
Description: Generates 100,000+ realistic e-commerce orders across 9 relational tables
             calibrated to match real-world Olist Brazilian E-Commerce dynamics.
"""

import os
import sys
import uuid
import random
import sqlite3
import datetime
import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

# Brazilian States and realistic weights
BRAZILIAN_STATES = {
    'SP': 0.42, 'RJ': 0.13, 'MG': 0.12, 'RS': 0.06, 'PR': 0.05,
    'SC': 0.04, 'BA': 0.035, 'DF': 0.025, 'GO': 0.02, 'ES': 0.02,
    'PE': 0.018, 'CE': 0.015, 'PA': 0.01, 'MT': 0.009, 'MA': 0.008,
    'MS': 0.007, 'PB': 0.006, 'RN': 0.005, 'PI': 0.004, 'AL': 0.004,
    'SE': 0.003, 'TO': 0.003, 'RO': 0.002, 'AM': 0.002, 'AC': 0.001,
    'AP': 0.001, 'RR': 0.0005
}

STATES_LIST = list(BRAZILIAN_STATES.keys())
STATES_PROBS = list(BRAZILIAN_STATES.values())
# Normalize probabilities
total_p = sum(STATES_PROBS)
STATES_PROBS = [p / total_p for p in STATES_PROBS]

# 25 Realistic Categories (Top 5 will drive >40% GMV)
CATEGORIES_TRANSLATION = [
    ('cama_mesa_banho', 'bed_bath_table', 0.110),
    ('beleza_saude', 'health_beauty', 0.095),
    ('esporte_lazer', 'sports_leisure', 0.085),
    ('informatica_acessorios', 'computers_accessories', 0.080),
    ('moveis_decoracao', 'furniture_decor', 0.075),
    # Top 5 cumulative share is ~44.5%
    ('utilidades_domesticas', 'housewares', 0.065),
    ('relogios_presentes', 'watches_gifts', 0.060),
    ('telefonia', 'telephony', 0.055),
    ('automotivo', 'auto', 0.045),
    ('brinquedos', 'toys', 0.040),
    ('bebes', 'baby', 0.035),
    ('perfumaria', 'perfumery', 0.035),
    ('papelaria', 'stationery', 0.030),
    ('ferramentas_jardim', 'garden_tools', 0.030),
    ('pet_shop', 'pet_shop', 0.025),
    ('eletronicos', 'electronics', 0.025),
    ('construcao_ferramentas_construcao', 'construction_tools_construction', 0.020),
    ('fashion_bolsas_e_acessorios', 'fashion_bags_accessories', 0.020),
    ('malas_acessorios', 'luggage_accessories', 0.018),
    ('eletrodomesticos', 'home_appliances', 0.017),
    ('instrumentos_musicais', 'musical_instruments', 0.014),
    ('consoles_games', 'consoles_games', 0.013),
    ('livros_interesse_geral', 'books_general_interest', 0.012),
    ('alimentos', 'food', 0.011),
    ('artigos_de_festas', 'party_supplies', 0.008)
]

def generate_database(output_db_path="data/olist_ecommerce.db", total_orders=105000):
    os.makedirs(os.path.dirname(output_db_path), exist_ok=True)
    if os.path.exists(output_db_path):
        os.remove(output_db_path)
    
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()
    
    print(f"[*] Initializing database generation: {output_db_path}")
    print(f"[*] Target Order Volume: {total_orders:,} orders across 9 relational tables")

    # 1. Product Category Translation Table
    print(" -> Creating product_category_name_translation table...")
    cat_df = pd.DataFrame([
        {'product_category_name': pt, 'product_category_name_english': en}
        for pt, en, _ in CATEGORIES_TRANSLATION
    ])
    cat_df.to_sql('product_category_name_translation', conn, index=False, if_exists='replace')

    # 2. Products Table (3,200 unique products)
    print(" -> Generating products catalog...")
    products = []
    cat_pt_list = [c[0] for c in CATEGORIES_TRANSLATION]
    cat_weights = [c[2] for c in CATEGORIES_TRANSLATION]
    norm_cat_weights = [w / sum(cat_weights) for w in cat_weights]

    for i in range(3500):
        pid = f"prod_{i+1:05d}"
        chosen_cat = np.random.choice(cat_pt_list, p=norm_cat_weights)
        products.append({
            'product_id': pid,
            'product_category_name': chosen_cat,
            'product_name_lenght': int(np.random.randint(20, 65)),
            'product_description_lenght': int(np.random.randint(150, 3500)),
            'product_photos_qty': int(np.random.randint(1, 8)),
            'product_weight_g': int(np.random.exponential(scale=1800) + 100),
            'product_length_cm': int(np.random.randint(10, 80)),
            'product_height_cm': int(np.random.randint(5, 60)),
            'product_width_cm': int(np.random.randint(10, 60))
        })
    products_df = pd.DataFrame(products)
    products_df.to_sql('products', conn, index=False, if_exists='replace')

    # 3. Sellers Table (3,000 sellers)
    print(" -> Generating sellers registry...")
    sellers = []
    for i in range(3000):
        seller_state = np.random.choice(STATES_LIST, p=STATES_PROBS)
        sellers.append({
            'seller_id': f"sell_{i+1:05d}",
            'seller_zip_code_prefix': int(np.random.randint(1000, 99999)),
            'seller_city': f"City_{seller_state}_{i%50}",
            'seller_state': seller_state
        })
    sellers_df = pd.DataFrame(sellers)
    sellers_df.to_sql('sellers', conn, index=False, if_exists='replace')

    # 4. Geolocation Table (representative sample of Brazilian zips)
    print(" -> Generating geolocation coordinates...")
    geolocations = []
    for state in STATES_LIST:
        base_lat = -23.55 if state == 'SP' else (-22.90 if state == 'RJ' else -15.78)
        base_lng = -46.63 if state == 'SP' else (-43.17 if state == 'RJ' else -47.92)
        for z in range(150):
            geolocations.append({
                'geolocation_zip_code_prefix': int(np.random.randint(1000, 99999)),
                'geolocation_lat': float(base_lat + np.random.normal(0, 1.5)),
                'geolocation_lng': float(base_lng + np.random.normal(0, 1.5)),
                'geolocation_city': f"City_{state}_{z%30}",
                'geolocation_state': state
            })
    geolocation_df = pd.DataFrame(geolocations)
    geolocation_df.to_sql('geolocation', conn, index=False, if_exists='replace')

    # 5. Customers & Orders Generation with Realistic Cohorts
    print(" -> Synthesizing 100k+ orders with cohort retention curves...")
    
    start_date = datetime.date(2022, 1, 1)
    end_date = datetime.date(2023, 8, 31)
    total_days = (end_date - start_date).days

    # Customer base: unique customers
    # To model a 30-35% Month-2 retention baseline among repeat shoppers,
    # we simulate customer cohorts by acquisition month
    n_unique_customers = 82000
    customer_uniques = [f"usr_{i+1:06d}" for i in range(n_unique_customers)]
    
    # Assign each customer an acquisition date (month)
    customer_acq_days = np.random.randint(0, total_days - 60, size=n_unique_customers)
    
    orders = []
    customers = []
    order_items = []
    order_payments = []
    order_reviews = []

    order_counter = 1
    item_counter = 1
    
    # Product price base by category
    category_price_multipliers = {
        'bed_bath_table': 115.0,
        'health_beauty': 130.0,
        'sports_leisure': 120.0,
        'computers_accessories': 165.0,
        'furniture_decor': 140.0,
        'housewares': 85.0,
        'watches_gifts': 210.0,
        'telephony': 90.0,
        'auto': 135.0,
        'toys': 95.0
    }

    # Month-2 retention curve probability distribution
    # M0: 100%, M1: 38%, M2: 32.5%, M3: 26%, M4: 21%, M5: 17%, M6: 14%, etc.
    retention_retarget_prob = [0.38, 0.325, 0.26, 0.21, 0.17, 0.14, 0.12, 0.10, 0.08, 0.07, 0.06]

    for u_idx, u_id in enumerate(customer_uniques):
        acq_day = customer_acq_days[u_idx]
        acq_date = start_date + datetime.timedelta(days=int(acq_day))
        cust_state = np.random.choice(STATES_LIST, p=STATES_PROBS)
        
        # Decide how many orders this customer places
        # Approximately 22% of customers place repeat orders
        repeat_shopper = (random.random() < 0.22)
        n_orders_cust = 1
        if repeat_shopper:
            # 2 to 5 orders
            n_orders_cust = np.random.choice([2, 3, 4, 5], p=[0.65, 0.22, 0.09, 0.04])
            
        for o_num in range(n_orders_cust):
            order_id = f"ord_{order_counter:06d}"
            customer_id = f"cust_{order_counter:06d}"
            order_counter += 1
            
            if o_num == 0:
                p_date = acq_date + datetime.timedelta(seconds=random.randint(0, 86400))
            else:
                # Interval based on retention curve: 30 to 60 days for Month 1/2
                offset_days = int(np.random.choice([30, 60, 90, 120, 150, 180], 
                                                   p=[0.38, 0.32, 0.15, 0.08, 0.04, 0.03]))
                p_date = acq_date + datetime.timedelta(days=offset_days, seconds=random.randint(0, 86400))
            
            if p_date > datetime.date(2023, 8, 31):
                continue
            
            p_datetime = datetime.datetime.combine(p_date, datetime.time(
                random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)
            ))

            # Funnel status progression:
            # 1. Placed (100%)
            # 2. Approved (98.8%)
            # 3. Shipped (97.5%)
            # 4. Delivered (96.2%)
            # 5. Canceled / Unavailable (~3.8%)
            rand_funnel = random.random()
            if rand_funnel < 0.962:
                order_status = 'delivered'
            elif rand_funnel < 0.975:
                order_status = 'shipped'
            elif rand_funnel < 0.988:
                order_status = 'processing'
            else:
                order_status = np.random.choice(['canceled', 'unavailable'], p=[0.7, 0.3])
                
            # Lead time modeling (SLA Analysis)
            # Purchase to approval: 10 mins to 24 hrs
            approval_delta = datetime.timedelta(minutes=random.randint(15, 1440))
            approved_at = p_datetime + approval_delta if order_status != 'canceled' else None
            
            # Approval to carrier: 1 to 4 days
            carrier_delta = datetime.timedelta(days=random.randint(1, 4), hours=random.randint(0, 12))
            delivered_carrier_date = approved_at + carrier_delta if order_status in ['shipped', 'delivered'] else None
            
            # Estimated delivery SLA: baseline 18 to 26 days from purchase
            sla_days = random.randint(16, 26)
            estimated_delivery_date = p_datetime + datetime.timedelta(days=sla_days)
            
            # Carrier to customer: depends on route
            # Interstate routes take longer; ~8% of orders exceed SLA
            interstate = (cust_state != 'SP')
            base_transit = random.randint(4, 15) if not interstate else random.randint(8, 22)
            
            # Probability of delivery delay beyond SLA
            is_delayed = (random.random() < (0.12 if interstate else 0.045))
            if is_delayed:
                # Arrives 1 to 7 days past estimated delivery
                actual_transit_days = sla_days + random.randint(1, 8)
            else:
                actual_transit_days = min(sla_days - random.randint(1, 7), base_transit)
                actual_transit_days = max(2, actual_transit_days)
                
            delivered_customer_date = delivered_carrier_date + datetime.timedelta(days=actual_transit_days) if order_status == 'delivered' else None

            orders.append({
                'order_id': order_id,
                'customer_id': customer_id,
                'order_status': order_status,
                'order_purchase_timestamp': p_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'order_approved_at': approved_at.strftime('%Y-%m-%d %H:%M:%S') if approved_at else None,
                'order_delivered_carrier_date': delivered_carrier_date.strftime('%Y-%m-%d %H:%M:%S') if delivered_carrier_date else None,
                'order_delivered_customer_date': delivered_customer_date.strftime('%Y-%m-%d %H:%M:%S') if delivered_customer_date else None,
                'order_estimated_delivery_date': estimated_delivery_date.strftime('%Y-%m-%d %H:%M:%S')
            })

            customers.append({
                'customer_id': customer_id,
                'customer_unique_id': u_id,
                'customer_zip_code_prefix': int(np.random.randint(1000, 99999)),
                'customer_city': f"City_{cust_state}_{random.randint(1, 50)}",
                'customer_state': cust_state
            })

            # Items per order (1 to 3 items)
            n_items = np.random.choice([1, 2, 3], p=[0.88, 0.09, 0.03])
            order_total_value = 0.0
            
            for item_idx in range(n_items):
                # Pick product
                prod_idx = random.randint(0, len(products) - 1)
                prod = products[prod_idx]
                seller_idx = random.randint(0, len(sellers) - 1)
                seller = sellers[seller_idx]
                
                # Price calibration based on category
                cat_en = [en for pt, en, _ in CATEGORIES_TRANSLATION if pt == prod['product_category_name']]
                cat_name_en = cat_en[0] if cat_en else 'housewares'
                base_price = category_price_multipliers.get(cat_name_en, 80.0)
                item_price = round(float(np.random.lognormal(mean=np.log(base_price), sigma=0.55)), 2)
                item_price = max(9.90, min(2490.00, item_price))
                
                # Freight value based on weight & interstate
                freight = round(12.50 + (prod['product_weight_g'] / 1000.0) * 2.2 + (8.50 if seller['seller_state'] != cust_state else 0.0), 2)
                
                order_items.append({
                    'order_id': order_id,
                    'order_item_id': item_idx + 1,
                    'product_id': prod['product_id'],
                    'seller_id': seller['seller_id'],
                    'shipping_limit_date': (p_datetime + datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
                    'price': item_price,
                    'freight_value': freight
                })
                order_total_value += (item_price + freight)

            # Payment records
            pay_type = np.random.choice(['credit_card', 'boleto', 'voucher', 'debit_card'], p=[0.74, 0.19, 0.05, 0.02])
            installments = random.randint(1, 10) if pay_type == 'credit_card' else 1
            order_payments.append({
                'order_id': order_id,
                'payment_sequential': 1,
                'payment_type': pay_type,
                'payment_installments': installments,
                'payment_value': round(order_total_value, 2)
            })

            # Review record
            # Delivered on time -> high score; delayed -> low score
            if order_status == 'delivered':
                if is_delayed:
                    score = np.random.choice([1, 2, 3], p=[0.58, 0.26, 0.16])
                else:
                    score = np.random.choice([4, 5, 3, 1], p=[0.35, 0.55, 0.07, 0.03])
            else:
                score = np.random.choice([1, 2], p=[0.85, 0.15])
                
            rev_date = delivered_customer_date if delivered_customer_date else p_datetime + datetime.timedelta(days=15)
            order_reviews.append({
                'review_id': f"rev_{order_counter:06d}",
                'order_id': order_id,
                'review_score': int(score),
                'review_comment_title': "Great product" if score >= 4 else ("Late delivery" if is_delayed else "Average"),
                'review_comment_message': "Satisfied with purchase" if score >= 4 else "Delivery arrived after SLA",
                'review_creation_date': rev_date.strftime('%Y-%m-%d %H:%M:%S'),
                'review_answer_timestamp': (rev_date + datetime.timedelta(hours=random.randint(2, 72))).strftime('%Y-%m-%d %H:%M:%S')
            })

            if len(orders) >= total_orders:
                break
        if len(orders) >= total_orders:
            break

    print(f" -> Saving {len(orders):,} orders to SQLite database...")
    orders_df = pd.DataFrame(orders)
    orders_df.to_sql('orders', conn, index=False, if_exists='replace')

    customers_df = pd.DataFrame(customers)
    customers_df.to_sql('customers', conn, index=False, if_exists='replace')

    order_items_df = pd.DataFrame(order_items)
    order_items_df.to_sql('order_items', conn, index=False, if_exists='replace')

    order_payments_df = pd.DataFrame(order_payments)
    order_payments_df.to_sql('order_payments', conn, index=False, if_exists='replace')

    order_reviews_df = pd.DataFrame(order_reviews)
    order_reviews_df.to_sql('order_reviews', conn, index=False, if_exists='replace')

    # Create Indexes for fast querying
    print(" -> Creating SQL indexes on primary and foreign keys...")
    indexes = [
        "CREATE INDEX idx_orders_customer ON orders(customer_id);",
        "CREATE INDEX idx_orders_status ON orders(order_status);",
        "CREATE INDEX idx_orders_purchase ON orders(order_purchase_timestamp);",
        "CREATE INDEX idx_items_order ON order_items(order_id);",
        "CREATE INDEX idx_items_product ON order_items(product_id);",
        "CREATE INDEX idx_items_seller ON order_items(seller_id);",
        "CREATE INDEX idx_cust_unique ON customers(customer_unique_id);",
        "CREATE INDEX idx_cust_id ON customers(customer_id);",
        "CREATE INDEX idx_prod_id ON products(product_id);",
        "CREATE INDEX idx_sell_id ON sellers(seller_id);",
        "CREATE INDEX idx_payments_order ON order_payments(order_id);",
        "CREATE INDEX idx_reviews_order ON order_reviews(order_id);"
    ]
    for idx_sql in indexes:
        cursor.execute(idx_sql)
        
    conn.commit()
    conn.close()

    print(f"[✓] Database generation complete: {output_db_path}")
    print(f"    Total Orders: {len(orders):,}")
    print(f"    Total Customers: {len(customers):,}")
    print(f"    Total Order Items: {len(order_items):,}")
    print(f"    Total Payments: {len(order_payments):,}")
    print(f"    Total Reviews: {len(order_reviews):,}")
    print(f"    Total Products: {len(products):,}")
    print(f"    Total Sellers: {len(sellers):,}")
    return output_db_path

if __name__ == "__main__":
    generate_database()
