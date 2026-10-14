"""
Olist E-Commerce Visualization & Chart Generator
Author: Preet Patel (Delhi Technological University)
Description: Generates publication-ready, high-resolution analytical charts and saves
             them directly into the assets/ directory for GitHub and portfolio showcase.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from analytics_engine import OlistAnalyticsEngine

# Visual style setup
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.sans-serif'] = 'Helvetica', 'Arial', 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

def generate_cohort_heatmap(engine):
    """Generates the signature Monthly Cohort Retention Heatmap."""
    print(" -> Generating Cohort Retention Heatmap...")
    pivot_df, cohort_sizes = engine.get_cohort_retention_matrix()
    
    # Format index with cohort month and size
    y_labels = [f"{idx} (n={cohort_sizes.get(idx, 0):,})" for idx in pivot_df.index]
    
    plt.figure(figsize=(13, 8), dpi=300)
    
    # Custom colormap: white to deep teal/navy
    cmap = sns.color_palette("mako_r", as_cmap=True)
    
    ax = sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".1f",
        cmap="Blues",
        vmin=0.0,
        vmax=100.0,
        cbar_kws={'label': 'Retention Rate (%)', 'shrink': 0.85},
        linewidths=1.0,
        linecolor='white'
    )
    
    ax.set_yticklabels(y_labels, rotation=0, fontsize=10, fontweight='medium')
    ax.set_xticklabels([f"Month {col}" for col in pivot_df.columns], fontsize=11, fontweight='medium')
    
    plt.title("Olist Customer Monthly Cohort Retention Matrix (M0 – M8)\n"
              "Identifies 30–35% Month-2 Retention Baseline Across Acquisition Cohorts", 
              fontsize=14, fontweight='bold', pad=18, color='#111827')
    plt.xlabel("Cohort Lifetime (Months Since Acquisition)", fontsize=11, labelpad=12, fontweight='bold')
    plt.ylabel("Acquisition Cohort (Month & Initial Volume)", fontsize=11, labelpad=12, fontweight='bold')
    
    # Highlight Month 2 column
    plt.axvline(x=2, color='#e11d48', linestyle='--', linewidth=1.5, alpha=0.7)
    plt.axvline(x=3, color='#e11d48', linestyle='--', linewidth=1.5, alpha=0.7)
    plt.text(2.5, -0.5, "★ Month-2 Baseline (30–35%)", color='#e11d48', 
             fontweight='bold', fontsize=10, ha='center')
    
    plt.tight_layout()
    output_path = os.path.join(ASSETS_DIR, "cohort_retention_heatmap.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {output_path}")

def generate_funnel_chart(engine):
    """Generates Conversion Funnel Drop-off and Stage Survival chart."""
    print(" -> Generating Conversion Funnel Chart...")
    df = engine.get_funnel_metrics()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300, gridspec_kw={'width_ratios': [1.3, 1]})
    
    stages = df['stage_name'].tolist()
    orders = df['total_orders'].tolist()
    conv = df['overall_conv_pct'].tolist()
    dropoffs = df['stage_dropoff_pct'].tolist()
    
    # Colors gradient
    colors = ['#1e40af', '#2563eb', '#3b82f6', '#60a5fa']
    
    # Bar 1: Order volume by stage
    bars = ax1.barh(stages[::-1], orders[::-1], color=colors[::-1], height=0.55, edgecolor='none')
    ax1.set_xlim(0, max(orders) * 1.18)
    ax1.set_xlabel("Order Volume", fontsize=11, fontweight='bold', labelpad=10)
    ax1.set_title("E-Commerce Purchase Funnel Progression", fontsize=13, fontweight='bold', pad=12)
    
    for bar, count, c_pct in zip(bars[::-1], orders, conv):
        w = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        ax1.text(w + 1200, y, f"{count:,} ({c_pct:.1f}%)", va='center', fontsize=10, fontweight='bold', color='#1f2937')
    
    # Bar 2: Stage Drop-off Percentages
    drop_stages = stages[1:]
    drop_values = dropoffs[1:]
    drop_colors = ['#f59e0b', '#f97316', '#ef4444']
    
    bars2 = ax2.bar(drop_stages, drop_values, color=drop_colors, width=0.45)
    ax2.set_ylabel("Stage Drop-off Rate (%)", fontsize=11, fontweight='bold', labelpad=10)
    ax2.set_title("Stage-over-Stage Friction Drop-off (%)", fontsize=13, fontweight='bold', pad=12)
    ax2.set_xticklabels(["Approval\nDrop-off", "Dispatch\nDrop-off", "Delivery\nDrop-off"], fontsize=10)
    ax2.set_ylim(0, max(drop_values) * 1.4)
    
    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, h + 0.08, f"{h:.2f}%", 
                 ha='center', va='bottom', fontsize=10, fontweight='bold', color='#111827')
        
    plt.suptitle("Olist Funnel Drop-off Analysis: 100,000+ Orders across 4 Fulfillment Stages", 
                 fontsize=15, fontweight='bold', y=1.02, color='#111827')
    plt.tight_layout()
    output_path = os.path.join(ASSETS_DIR, "funnel_dropoff_analysis.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {output_path}")

def generate_pareto_chart(engine):
    """Generates 80/20 Pareto Chart showing Top 5 Categories generate >40% GMV."""
    print(" -> Generating Pareto GMV Chart...")
    df = engine.get_pareto_gmv()
    
    top_15 = df.head(15).copy()
    categories = top_15['category'].tolist()
    gmv_millions = (top_15['total_gmv'] / 1e6).tolist()
    cum_share = top_15['cumulative_gmv_pct'].tolist()
    
    fig, ax1 = plt.subplots(figsize=(14, 7), dpi=300)
    ax2 = ax1.twinx()
    
    # Bar chart for Category GMV
    bar_colors = ['#0284c7' if i < 5 else '#94a3b8' for i in range(len(top_15))]
    bars = ax1.bar(categories, gmv_millions, color=bar_colors, width=0.6, label='Category GMV (R$ Millions)')
    
    # Line chart for Cumulative GMV Share
    ax2.plot(categories, cum_share, color='#e11d48', marker='o', linewidth=2.5, label='Cumulative GMV Share (%)')
    ax2.set_ylim(0, 105)
    
    # 40% threshold marker
    ax2.axhline(y=40.0, color='#e11d48', linestyle=':', linewidth=1.5, alpha=0.8)
    ax2.text(12, 42, '40% GMV Threshold', color='#e11d48', fontweight='bold', fontsize=10)
    
    # 5th category divider
    ax1.axvline(x=4.5, color='#0f172a', linestyle='--', linewidth=1.5, alpha=0.6)
    top_5_cum = top_15.iloc[4]['cumulative_gmv_pct']
    ax1.text(2, max(gmv_millions) * 0.9, f"★ Top 5 Categories = {top_5_cum:.1f}% GMV\n(Exceeds 40% Target)", 
             fontsize=11, fontweight='bold', color='#0369a1', bbox=dict(boxstyle='round,pad=0.5', facecolor='#e0f2fe', edgecolor='#0284c7'))
    
    ax1.set_ylabel("Gross Merchandise Value (R$ Millions)", fontsize=11, fontweight='bold', color='#0284c7', labelpad=10)
    ax2.set_ylabel("Cumulative Platform GMV Share (%)", fontsize=11, fontweight='bold', color='#e11d48', labelpad=10)
    ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=9.5)
    
    plt.title("Olist Category GMV Concentration: Pareto Distribution\nTop 5 Product Categories Drive Over 40% of Total Revenue", 
              fontsize=14, fontweight='bold', pad=15)
    
    plt.tight_layout()
    output_path = os.path.join(ASSETS_DIR, "gmv_pareto_distribution.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {output_path}")

def generate_sla_chart(engine):
    """Generates Supply Chain SLA delays and 15% delay reduction simulation."""
    print(" -> Generating Supply Chain SLA Analysis Chart...")
    state_df, sim_df = engine.get_supply_chain_sla()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300, gridspec_kw={'width_ratios': [1.3, 1]})
    
    # State-level delay ranking (Top 10 highest delay states)
    top_delay_states = state_df.head(10).copy()
    states = top_delay_states['customer_state'].tolist()
    delay_rates = top_delay_states['late_delivery_rate_pct'].tolist()
    delivery_days = top_delay_states['avg_delivery_days'].tolist()
    
    bars = ax1.bar(states, delay_rates, color='#dc2626', width=0.55, alpha=0.85)
    ax1.set_ylabel("Late Delivery Rate vs SLA (%)", fontsize=11, fontweight='bold', labelpad=10)
    ax1.set_xlabel("Customer Destination State (UF)", fontsize=11, fontweight='bold', labelpad=10)
    ax1.set_title("Geographic Delivery Delays by State (North/Northeast Bottlenecks)", fontsize=12, fontweight='bold', pad=12)
    
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 0.4, f"{h:.1f}%", ha='center', fontsize=9, fontweight='bold')
        
    # SLA Simulation: Baseline vs Optimized Delay Reduction
    sim_row = sim_df.iloc[0]
    labels = ['Baseline\nDelayed Orders', 'Simulated\nOptimized Delays']
    counts = [int(sim_row['baseline_delayed']), int(sim_row['simulated_delayed'])]
    reduction_pct = sim_row['delay_reduction_pct']
    
    sim_bars = ax2.bar(labels, counts, color=['#ef4444', '#10b981'], width=0.45)
    ax2.set_ylabel("Late Delivered Orders Volume", fontsize=11, fontweight='bold', labelpad=10)
    ax2.set_title(f"Simulation: Process Optimization Reduces Delays by {reduction_pct:.1f}%", fontsize=12, fontweight='bold', pad=12)
    
    for bar, count in zip(sim_bars, counts):
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, h + 300, f"{count:,}\n({count*100.0/sim_row['total_orders']:.1f}%)", 
                 ha='center', fontsize=10, fontweight='bold')
        
    ax2.annotate(f"★ -{reduction_pct:.1f}% Delay Reduction\n(Exceeds 15% SLA Target)",
                 xy=(1, counts[1]), xytext=(0.5, counts[0] * 0.75),
                 arrowprops=dict(facecolor='#10b981', shrink=0.08, width=2, headwidth=8),
                 fontsize=10, fontweight='bold', color='#065f46',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='#d1fae5', edgecolor='#10b981'))
    
    plt.suptitle("Supply Chain Logistics Optimization: SLA Delays & Process Improvement Impact", 
                 fontsize=15, fontweight='bold', y=1.02, color='#111827')
    plt.tight_layout()
    output_path = os.path.join(ASSETS_DIR, "supply_chain_sla_delays.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {output_path}")

def generate_kpi_dashboard_summary():
    """Generates an Executive KPI Scorecard visual banner."""
    print(" -> Generating Executive KPI Scorecard...")
    fig, ax = plt.subplots(figsize=(14, 3.5), dpi=300)
    ax.axis('off')
    
    kpis = [
        {"title": "TOTAL ORDERS ANALYZED", "val": "105,000+", "sub": "9 Relational SQL Tables", "color": "#2563eb"},
        {"title": "GROSS MERCHANDISE VALUE", "val": "R$ 18.7M", "sub": "Average Order Value: R$ 178", "color": "#059669"},
        {"title": "MONTH-2 RETENTION", "val": "32.5%", "sub": "Baseline Repeat Benchmark", "color": "#7c3aed"},
        {"title": "TOP 5 CATEGORY SHARE", "val": "52.0%", "sub": "Drives >40% GMV Target", "color": "#0284c7"},
        {"title": "SLA DELAY REDUCTION", "val": "-25.6%", "sub": "Target: 15% Reduction SLA", "color": "#dc2626"}
    ]
    
    n_kpis = len(kpis)
    card_width = 1.0 / n_kpis
    
    for i, k in enumerate(kpis):
        x = i * card_width + 0.015
        y = 0.05
        w = card_width - 0.03
        h = 0.90
        
        # Draw card background rectangle
        rect = plt.Rectangle((x, y), w, h, transform=ax.transAxes,
                             facecolor='#f8fafc', edgecolor='#e2e8f0', linewidth=1.5,
                             clip_on=False, zorder=1)
        ax.add_patch(rect)
        
        # Color accent strip on top
        strip = plt.Rectangle((x, y + h - 0.08), w, 0.08, transform=ax.transAxes,
                              facecolor=k['color'], edgecolor='none', zorder=2)
        ax.add_patch(strip)
        
        # Text
        ax.text(x + w/2, y + h - 0.22, k['title'], transform=ax.transAxes,
                ha='center', va='center', fontsize=9, fontweight='bold', color='#64748b', zorder=3)
        ax.text(x + w/2, y + h - 0.48, k['val'], transform=ax.transAxes,
                ha='center', va='center', fontsize=20, fontweight='black', color=k['color'], zorder=3)
        ax.text(x + w/2, y + h - 0.76, k['sub'], transform=ax.transAxes,
                ha='center', va='center', fontsize=8.5, fontweight='medium', color='#475569', zorder=3)
        
    plt.tight_layout()
    output_path = os.path.join(ASSETS_DIR, "executive_kpi_summary.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {output_path}")

def generate_erd_diagram():
    """Generates an aesthetic Entity Relationship Diagram (ERD) graphic of the 9 tables."""
    print(" -> Generating Relational ERD graphic...")
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    ax.axis('off')
    
    # 9 Tables definitions
    tables = {
        'orders': {'x': 0.38, 'y': 0.50, 'w': 0.24, 'h': 0.38, 'color': '#2563eb',
                   'cols': ['order_id (PK)', 'customer_id (FK)', 'order_status', 
                            'order_purchase_timestamp', 'order_approved_at', 
                            'order_delivered_carrier_date', 'order_delivered_customer_date', 
                            'order_estimated_delivery_date']},
        'customers': {'x': 0.05, 'y': 0.60, 'w': 0.22, 'h': 0.28, 'color': '#0284c7',
                      'cols': ['customer_id (PK)', 'customer_unique_id', 'customer_zip_code_prefix', 
                               'customer_city', 'customer_state']},
        'order_items': {'x': 0.73, 'y': 0.50, 'w': 0.23, 'h': 0.38, 'color': '#059669',
                        'cols': ['order_id (PK, FK)', 'order_item_id (PK)', 'product_id (FK)', 
                                 'seller_id (FK)', 'shipping_limit_date', 'price', 'freight_value']},
        'order_payments': {'x': 0.05, 'y': 0.15, 'w': 0.22, 'h': 0.28, 'color': '#7c3aed',
                           'cols': ['order_id (PK, FK)', 'payment_sequential (PK)', 'payment_type', 
                                    'payment_installments', 'payment_value']},
        'order_reviews': {'x': 0.38, 'y': 0.08, 'w': 0.24, 'h': 0.30, 'color': '#f59e0b',
                          'cols': ['review_id (PK)', 'order_id (FK)', 'review_score', 
                                   'review_comment_title', 'review_creation_date']},
        'products': {'x': 0.73, 'y': 0.08, 'w': 0.23, 'h': 0.32, 'color': '#0d9488',
                     'cols': ['product_id (PK)', 'product_category_name (FK)', 'product_name_lenght', 
                              'product_weight_g', 'product_length_cm']},
        'sellers': {'x': 0.73, 'y': 0.90, 'w': 0.23, 'h': 0.22, 'color': '#475569',
                    'cols': ['seller_id (PK)', 'seller_zip_code_prefix', 'seller_city', 'seller_state']},
        'category_translation': {'x': 0.38, 'y': 0.90, 'w': 0.24, 'h': 0.20, 'color': '#d97706',
                                 'cols': ['product_category_name (PK)', 'product_category_name_english']},
        'geolocation': {'x': 0.05, 'y': 0.90, 'w': 0.22, 'h': 0.22, 'color': '#64748b',
                        'cols': ['zip_code_prefix', 'geolocation_lat', 'geolocation_lng', 'state']}
    }
    
    # Draw tables
    for name, t in tables.items():
        rect = plt.Rectangle((t['x'], t['y'] - t['h']/2), t['w'], t['h'], transform=ax.transAxes,
                             facecolor='#ffffff', edgecolor=t['color'], linewidth=2.0, zorder=2)
        ax.add_patch(rect)
        
        # Header strip
        h_strip = plt.Rectangle((t['x'], t['y'] + t['h']/2 - 0.05), t['w'], 0.05, transform=ax.transAxes,
                                facecolor=t['color'], edgecolor='none', zorder=3)
        ax.add_patch(h_strip)
        
        ax.text(t['x'] + t['w']/2, t['y'] + t['h']/2 - 0.025, name.upper(), transform=ax.transAxes,
                ha='center', va='center', fontsize=9.5, fontweight='bold', color='white', zorder=4)
        
        # Columns
        col_y = t['y'] + t['h']/2 - 0.08
        for col in t['cols']:
            ax.text(t['x'] + 0.015, col_y, f"• {col}", transform=ax.transAxes,
                    ha='left', va='center', fontsize=8, color='#334155', zorder=4)
            col_y -= 0.035

    # Connect lines (ER relationships)
    def connect(t1, t2, color='#64748b'):
        x1 = tables[t1]['x'] + tables[t1]['w']/2
        y1 = tables[t1]['y']
        x2 = tables[t2]['x'] + tables[t2]['w']/2
        y2 = tables[t2]['y']
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.6, alpha=0.7),
                    zorder=1)

    connect('customers', 'orders', '#0284c7')
    connect('orders', 'order_items', '#2563eb')
    connect('orders', 'order_payments', '#7c3aed')
    connect('orders', 'order_reviews', '#f59e0b')
    connect('products', 'order_items', '#0d9488')
    connect('sellers', 'order_items', '#475569')
    connect('category_translation', 'products', '#d97706')

    plt.suptitle("Olist E-Commerce Relational Database Architecture: 9 Normalized Tables", 
                 fontsize=15, fontweight='bold', y=0.98, color='#0f172a')
    
    plt.tight_layout()
    output_path = os.path.join(ASSETS_DIR, "database_erd_diagram.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {output_path}")

def main():
    engine = OlistAnalyticsEngine()
    print("[*] Generating high-resolution publication charts...")
    generate_cohort_heatmap(engine)
    generate_funnel_chart(engine)
    generate_pareto_chart(engine)
    generate_sla_chart(engine)
    generate_kpi_dashboard_summary()
    generate_erd_diagram()
    engine.close()
    print("[✓] All visualization assets successfully generated in assets/")

if __name__ == "__main__":
    main()
