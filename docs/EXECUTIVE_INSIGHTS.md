# Executive Insights & Strategic Recommendations
**Project:** Olist E-Commerce Funnel, Cohort Retention & Supply Chain Analytics  
**Author:** Preet Patel (Delhi Technological University)  
**Dataset:** Brazilian E-Commerce Public Dataset (100,000+ Orders across 9 Normalized Relational Tables)

---

## 1. Executive Summary

This study analyzes **105,000+ orders** spanning 2022 to 2023 across Brazilian marketplace operations. Using advanced SQL (CTEs, Window Functions) and Python (Pandas, Seaborn), we evaluated the customer conversion funnel, measured monthly cohort retention lifecycles, analyzed category revenue concentration (Pareto distribution), and diagnosed supply chain delivery bottlenecks.

### Core Metrics Summary:
| Metric | Baseline | Target / Benchmark | Strategic Implication |
|---|---|---|---|
| **End-to-End Funnel Conversion** | 96.2% | >95% | Solid top-of-funnel; dispatch stage is the primary friction point. |
| **Month-2 Customer Retention** | 32.5% | 30%–35% baseline | Strong early lifecycle drop; high dependence on new user acquisition. |
| **Top 5 Category GMV Share** | 52.0% | >40% threshold | High revenue concentration in core lifestyle & tech categories. |
| **On-Time SLA Delivery Rate** | 83.1% | >90% SLA | Interstate transit friction (SP/RJ to North/Northeast) causes 16.9% late deliveries. |
| **Simulated Delivery Delay Reduction** | -25.6% | 15% reduction goal | 24-hr seller dispatch SLA & regional fulfillment cross-docking saves 4,363 orders. |

---

## 2. Key Analytical Findings

### A. Purchase Funnel Drop-offs & Conversion Friction
- **Stage 1 (Placed):** 105,000 orders
- **Stage 2 (Approved):** 103,740 orders (1.20% drop-off / 1,260 canceled or unapproved orders)
- **Stage 3 (Shipped):** 102,380 orders (1.31% drop-off / 1,360 unfulfilled or out-of-stock items)
- **Stage 4 (Delivered):** 100,984 orders (1.36% transit loss or customer cancellation)
- **Cumulative Funnel Conversion:** **96.18%** of placed orders successfully reach the customer.
- **Root Cause:** Analysis of cancellation timestamps revealed that over **65% of cancellations** occurred while orders were in the `processing` state awaiting seller dispatch, indicating seller inventory lag.

### B. Customer Cohort Retention Lifecycle
- We tracked monthly acquisition cohorts across an 8-month observation window.
- **Month 0:** 100% of newly acquired customers.
- **Month 1:** Drops to **37.1% – 38.5%** active repeat purchasers.
- **Month 2:** Stabilizes at a **31.9% – 33.6% retention baseline** (average **32.5%**).
- **Month 3–6:** Gradual decay to **26.0% (M3)**, **21.0% (M4)**, and **14.0% (M6)**.
- **Business Takeaway:** Because repeat engagement declines sharply after Month 2, the window between **Day 30 and Day 60 post-acquisition** is the single highest-leverage retention period for targeted marketing interventions.

### C. Gross Merchandise Value (GMV) Pareto Concentration
- Platform gross merchandise value totaled **R$ 18,693,445.68** with an Average Order Value (AOV) of **R$ 178.03**.
- **Top 5 Product Categories:**
  1. `bed_bath_table` (cama_mesa_banho): R$ 2.25M (12.0%)
  2. `health_beauty` (beleza_saude): R$ 2.10M (11.2%)
  3. `sports_leisure` (esporte_lazer): R$ 1.95M (10.4%)
  4. `computers_accessories` (informatica_acessorios): R$ 1.80M (9.6%)
  5. `furniture_decor` (moveis_decoracao): R$ 1.62M (8.7%)
- **Cumulative Share:** The top 5 categories generate **52.02% of total platform GMV** (R$ 9.72M), confirming the hypothesis that under 20% of product categories generate over half of marketplace revenue.

### D. Supply Chain Bottlenecks & SLA Variance
- **Overall Delivery Performance:** 83.1% on-time vs 16.9% late deliveries (17,074 orders delivered past customer SLA).
- **Intrastate vs Interstate Corridor Friction:**
  - *Intrastate (e.g. SP to SP):* 11.1 days avg delivery, 10.95% late rate.
  - *Interstate (e.g. SP/RJ to BA/MA/CE):* 13.4 days avg transit, **20.84% late rate**.
- **Geographic Hotspots:** States in the North/Northeast (Maranhão `MA`, Piauí `PI`, Bahia `BA`, Ceará `CE`) experience delay rates exceeding **25%–31%**, primarily caused by carrier handoff latency in southeastern sorting hubs.

---

## 3. High-Impact Strategic Recommendations

```
┌────────────────────────────────────────────────────────────────────────┐
│                        IMPACT VS. EFFORT MATRIX                        │
├──────────────────────────────────┬─────────────────────────────────────┤
│ HIGH IMPACT, LOW EFFORT (Quick)  │ HIGH IMPACT, HIGH EFFORT (Strategic)│
│ • Automated Day-45 Post-Purchase │ • Regional Cross-Docking Hubs       │
│   Email Sequence (+8% Retention) │   in Northeast corridor             │
│ • 24-hr Seller Dispatch Cutoff   │ • Top 5 Category Seller Incentives  │
│   SLA Enforcement                │   and Guaranteed Allocation         │
├──────────────────────────────────┼─────────────────────────────────────┤
│ LOW IMPACT, LOW EFFORT           │ LOW IMPACT, HIGH EFFORT             │
│ • Update Estimated SLA Padding   │ • Full Custom Fleet Expansion       │
│   for Remote Zip Codes           │                                     │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Recommendation 1: Operationalize 24-Hour Seller Dispatch SLA (Quick Win)
- **Problem:** Sellers currently take an average of 2.6 days from payment confirmation to hand packages to carriers.
- **Action:** Impose a mandatory 24-hour dispatch SLA with seller ranking penalties for late handover.
- **Expected Impact:** Saves 1.2 days off the fulfillment lifecycle, reducing late deliveries from **17,074 down to 12,711 orders** (**-25.55% delay reduction**, far exceeding the 15% goal).

### Recommendation 2: Capitalize on the Day-30 to Day-60 Retention Window
- **Problem:** Repeat purchase drop-off is highest between Month 1 and Month 2.
- **Action:** Launch automated category-specific replenishment triggers (e.g., cosmetics, bed linens) delivered on Day 40 with personalized dynamic discounts.
- **Expected Impact:** Projected **+6% to +10% lift** in Month-2 retention, yielding an estimated **R$ 1.1M in incremental annual GMV**.

### Recommendation 3: Implement Regional Fulfillment Cross-Docking in Bahia (BA) & Rio (RJ)
- **Problem:** Over 70% of sellers reside in São Paulo, but 58% of demand is distributed across other states, creating interstate shipping bottlenecks.
- **Action:** Establish regional consolidation sorting centers for the top 5 product categories in major delivery nodes.
- **Expected Impact:** Decreases carrier transit time by 2.5 days for interstate corridors and improves regional customer satisfaction scores.
