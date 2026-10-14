# Fieldnote — Commerce Intelligence

A locally runnable analytics workspace for the project in the supplied brief: order progression, repeat-purchase cohorts, category GMV concentration, and delivery service levels. The dashboard leads; the case study and metric definitions are a second, inspectable view.

## Live demo

[Open the public read-only dashboard demo](https://fieldnote-commerce-dashboard.wirykiwi11.chatgpt.site).

## Run locally

Use Node.js 20.9 or newer.

```sh
npm install
npm run dev
```

Open the local URL printed by Next.js. The dashboard is read-only and works offline with the included 29 KB analytics snapshot. It does not need Supabase, API keys, or an external service.

## What is included

- Overview with monthly GMV, eligible order count, average order value, customer Month-2 retention, order funnel, cohort heatmap, and category mix.
- Funnel view with timestamp-stage conversion and drop-off.
- Customer cohort view with observable follow-up periods and right-censored recent cohorts.
- Fulfillment view with order-level late-delivery rates by customer state.
- Case study & data view with provenance, nine-table row counts, definitions, and denominator notes.
- Corridor and time-window controls, responsive mobile navigation, and filtered JSON export.
- PostgreSQL reference queries using CTEs and window functions.
- Repeatable SQLite snapshot builder in `scripts/build_data.py`.

## Data provenance

The bundled source snapshot was computed from a generated, Olist-shaped portfolio sample. It is synthetic; it is not the public Brazilian Olist dataset and cannot support claims about actual customer behavior, revenue, or delivery performance. The sample contains 105,000 order rows between January 2022 and August 2023, across nine related tables.

The reference repository's configured cohort curve was intentionally generated. Recalculation gives a **9.2% weighted Month-2 retention** for mature cohorts, not the 32.5% hardcoded in its existing dashboard. The application shows the computed result and labels the dataset. Category share and late-delivery metrics are also recalculated from the table rows.

To build a new snapshot from a compatible SQLite database:

```sh
python3 scripts/build_data.py --db /path/to/compatible.sqlite --out public/analytics.json
```

The builder aggregates order-level delivery facts before joining product lines so baskets with multiple items do not count as multiple late deliveries. No source database or credentials are bundled.

## Metric definitions

- **Eligible order:** order status is not `canceled` or `unavailable`.
- **GMV:** sum of item price plus freight on eligible orders.
- **AOV:** eligible GMV divided by eligible distinct orders.
- **Month-N retention:** distinct customers with an eligible order in the Nth calendar month after first eligible purchase, divided by the original cohort size. The headline Month-2 rate is weighted across cohorts with a full two-month observation period.
- **Late delivery:** delivered order where customer delivery timestamp is later than the estimated date; each order counts once.
- **Funnel:** placed → approval timestamp → carrier handoff timestamp → delivered status and timestamp.

## Project files

- `src/app/` — responsive Next.js interface.
- `public/analytics.json` — calculated browser snapshot.
- `scripts/build_data.py` — SQLite-to-JSON snapshot builder.
- `sql/` — PostgreSQL query references for the study.
- `PRODUCT.md`, `DESIGN.md` — product and visual direction.
