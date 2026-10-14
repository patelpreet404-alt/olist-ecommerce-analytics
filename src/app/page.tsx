"use client";

import { useMemo, useState } from "react";
import {
  ArrowDownRight, ArrowUpRight, BarChart3, BookOpen, Boxes, ChevronDown,
  CircleHelp, Download, ExternalLink, Filter, Gauge, LayoutDashboard,
  Menu, PackageCheck, ShoppingBag, Sparkles, Users, X,
} from "lucide-react";
import analyticsJson from "../../public/analytics.json";

type Month = { month: string; orders: number; gmv: number; customers: number };
type FunnelStage = { stage: string; orders: number; conversion: number; dropoff: number };
type Cohort = { month: string; size: number; retention: (number | null)[] };
type Category = { category: string; gmv: number; share: number; cumulativeShare: number; orders: number };
type StateMetric = { state: string; deliveredOrders: number; lateOrders: number; lateRate: number; averageDays: number };
type RegionId = "all" | "southeast" | "northeast" | "south";
type Data = {
  meta: { datasetName: string; provenance: string; currency: string; periodStart: string; periodEnd: string; tableCount: number; sourceOrderRows: number; orderItemRows: number; tables: { name: string; rows: number }[] };
  regions: { id: RegionId; label: string }[];
  summaryByRegion: Record<RegionId, { eligibleOrders: number; gmv: number; aov: number; customers: number; deliveredOrders: number; lateOrders: number; lateRate: number; averageDeliveryDays: number; month2Retention: number | null }>;
  monthlyByRegion: Record<RegionId, Month[]>;
  funnelByRegion: Record<RegionId, FunnelStage[]>;
  cohortsByRegion: Record<RegionId, Cohort[]>;
  categoriesByRegion: Record<RegionId, Category[]>;
  fulfillmentByRegion: Record<RegionId, StateMetric[]>;
  benchmarks: { month2Retention: number | null; topFiveCategoryShare: number; funnelConversion: number; lateRate: number; gmv: number };
};

const data = analyticsJson as Data;
type PageId = "overview" | "funnel" | "retention" | "fulfillment" | "method";
const navItems: { id: PageId; label: string; icon: typeof LayoutDashboard; group: "workspace" | "study" }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard, group: "workspace" },
  { id: "funnel", label: "Order funnel", icon: ShoppingBag, group: "workspace" },
  { id: "retention", label: "Customer cohorts", icon: Users, group: "workspace" },
  { id: "fulfillment", label: "Fulfillment", icon: PackageCheck, group: "workspace" },
  { id: "method", label: "Case study & data", icon: BookOpen, group: "study" },
];
const pageCopy: Record<PageId, { title: string; description: string }> = {
  overview: { title: "Commerce, at a glance.", description: "A clear read on order value, repeat behavior, and the delivery promise." },
  funnel: { title: "Where orders move.", description: "Follow each transaction from checkout approval to the customer’s door." },
  retention: { title: "The return journey.", description: "See how many customers come back after their first eligible purchase." },
  fulfillment: { title: "The delivery promise.", description: "Compare delivery outcomes across customer regions, counting each order once." },
  method: { title: "Read the evidence.", description: "A short case study with the definitions and provenance behind every view." },
};
const brl = (amount: number, compact = false) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "BRL", notation: compact && amount >= 1_000_000 ? "compact" : "standard", maximumFractionDigits: compact && amount >= 1_000_000 ? 1 : 0,
}).format(amount).replace("R$", "R$");
const brlAxis = (amount: number) => amount >= 1_000_000 ? `R$${(amount / 1_000_000).toFixed(1)}M` : amount >= 1_000 ? `R$${Math.round(amount / 1_000)}k` : `R$${Math.round(amount)}`;
const number = (n: number) => new Intl.NumberFormat("en-US").format(n);
const monthLabel = (value: string) => {
  const [year, month] = value.split("-");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[Number(month) - 1]} ${year.slice(-2)}`;
};
const niceCategory = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function BrandMark() { return <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>; }

function Sidebar({ page, setPage, close }: { page: PageId; setPage: (page: PageId) => void; close?: () => void }) {
  return <>
    <div className="brand-lockup"><BrandMark /><div><strong>Fieldnote</strong><small>COMMERCE INTELLIGENCE</small></div></div>
    <div className="side-rule" />
    <div className="nav-group-label">WORKSPACE</div>
    <nav className="side-nav" aria-label="Workspace navigation">
      {navItems.filter((item) => item.group === "workspace").map(({ id, label, icon: Icon }) => <button key={id} className={`nav-link ${page === id ? "active" : ""}`} onClick={() => { setPage(id); close?.(); }} aria-current={page === id ? "page" : undefined}><Icon size={17} strokeWidth={1.8} /><span>{label}</span>{id === "overview" && <span className="nav-dot" />}</button>)}
    </nav>
    <div className="nav-group-label study-label">YOUR STUDY</div>
    <nav className="side-nav" aria-label="Study navigation">
      {navItems.filter((item) => item.group === "study").map(({ id, label, icon: Icon }) => <button key={id} className={`nav-link ${page === id ? "active" : ""}`} onClick={() => { setPage(id); close?.(); }} aria-current={page === id ? "page" : undefined}><Icon size={17} strokeWidth={1.8} /><span>{label}</span></button>)}
    </nav>
    <div className="sidebar-spacer" />
    <div className="source-card"><div className="source-icon"><Boxes size={17} /></div><div><strong>Demo dataset</strong><span>Generated sample · 9 tables</span></div><span className="source-status" /></div>
    <div className="sidebar-foot"><span className="avatar">PP</span><div><strong>Preet Patel</strong><small>Analytics portfolio</small></div><button aria-label="About this study" onClick={() => setPage("method")} className="icon-button"><CircleHelp size={17} /></button></div>
  </>;
}

type ChartMetric = "gmv" | "orders";
function TrendChart({ series, metric }: { series: Month[]; metric: ChartMetric }) {
  const w = 760, h = 228, left = 10, right = 8, top = 14, bottom = 25;
  const valueOf = (item: Month) => metric === "gmv" ? item.gmv : item.orders;
  const max = Math.max(...series.map(valueOf), 1) * 1.15;
  const x = (i: number) => left + (series.length <= 1 ? 0 : i * (w - left - right) / (series.length - 1));
  const y = (value: number) => top + (1 - value / max) * (h - top - bottom);
  const line = series.map((item, i) => `${i ? "L" : "M"}${x(i)},${y(valueOf(item))}`).join(" ");
  const fill = `${line} L${x(series.length - 1)},${h-bottom} L${x(0)},${h-bottom} Z`;
  const labels = series.filter((_, i) => i % Math.max(1, Math.ceil(series.length / 6)) === 0 || i === series.length - 1);
  return <div className="trend-chart-wrap">
    <div className="chart-y-labels"><span>{metric === "gmv" ? brlAxis(max) : number(Math.round(max))}</span><span>{metric === "gmv" ? brlAxis(max * .5) : number(Math.round(max * .5))}</span><span>{metric === "gmv" ? "R$0" : "0"}</span></div>
    <svg className={`trend-chart chart-${metric}`} viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`Monthly ${metric === "gmv" ? "gross merchandise value" : "eligible orders"} trend across ${series.length} months`}>
      {[0, .5, 1].map((t) => <line key={t} x1={left} x2={w-right} y1={top + t * (h-top-bottom)} y2={top + t * (h-top-bottom)} className="chart-grid" />)}
      <path d={fill} className="chart-area" /><path d={line} className="chart-line" />
      {series.map((item, i) => <circle key={item.month} cx={x(i)} cy={y(valueOf(item))} r="3.2" className="chart-point"><title>{`${monthLabel(item.month)} · ${metric === "gmv" ? brl(item.gmv) : `${number(item.orders)} orders`}`}</title></circle>)}
    </svg>
    <div className="chart-x-labels">{labels.map((item) => <span key={item.month}>{monthLabel(item.month)}</span>)}</div>
  </div>;
}

function Metric({ label, value, detail, icon: Icon, tone = "green", footnote }: { label: string; value: string; detail: string; icon: typeof Gauge; tone?: string; footnote?: string }) {
  return <article className={`metric metric-${tone}`}><div className="metric-top"><span>{label}</span><Icon size={17} strokeWidth={1.7} /></div><strong className="metric-value">{value}</strong><div className="metric-detail">{detail}</div>{footnote && <div className="metric-footnote">{footnote}</div>}</article>;
}

function Funnel({ stages, compact = false }: { stages: FunnelStage[]; compact?: boolean }) {
  const max = Math.max(...stages.map((item) => item.orders), 1);
  return <div className={`funnel-list ${compact ? "compact" : ""}`}>
    {stages.map((item, i) => <div className="funnel-row" key={item.stage}>
      <div className="funnel-label"><span className="funnel-index">0{i+1}</span><span>{item.stage}</span><strong>{number(item.orders)}</strong></div>
      <div className="funnel-rail"><span style={{ width: `${Math.max(7, item.orders / max * 100)}%` }} /></div>
      <div className="funnel-meta"><span>{item.conversion.toFixed(1)}% of placed</span>{i > 0 && <span className="dropoff"><ArrowDownRight size={13} /> {number(item.dropoff)} lost</span>}</div>
    </div>)}
  </div>;
}

function CohortTable({ cohorts }: { cohorts: Cohort[] }) {
  const displayed = cohorts.slice(-12);
  return <div className="table-scroll cohort-scroll"><table className="cohort-table"><thead><tr><th>First order</th><th>Size</th>{Array.from({ length: 7 }, (_, i) => <th key={i}>M{i}</th>)}</tr></thead><tbody>
    {displayed.map((cohort) => <tr key={cohort.month}><th>{monthLabel(cohort.month)}</th><td className="cohort-size">{number(cohort.size)}</td>{cohort.retention.slice(0, 7).map((value, i) => <td key={i}>{value === null ? <span className="cohort-blank">—</span> : <span className="cohort-cell" style={{ backgroundColor: value >= 60 ? "#006b5e" : value >= 35 ? "#77c9b8" : value >= 15 ? "#b6e3d9" : "#e6f5f2", color: value >= 60 ? "#ffffff" : "#164a44" }}>{value.toFixed(0)}<small>%</small></span>}</td>)}</tr>)}
  </tbody></table></div>;
}

function Categories({ items, compact = false }: { items: Category[]; compact?: boolean }) {
  const visible = items.slice(0, compact ? 6 : 12);
  const max = visible[0]?.gmv ?? 1;
  return <div className="category-list">{visible.map((item, i) => <div className="category-row" key={item.category}>
    <span className="category-rank">{String(i+1).padStart(2, "0")}</span><span className="category-name">{niceCategory(item.category)}</span>
    <div className="category-rail"><span style={{ width: `${item.gmv / max * 100}%` }} /></div>
    <strong>{brl(item.gmv, true)}</strong><span className="category-share">{item.share.toFixed(1)}%</span>
  </div>)}</div>;
}

function FulfillmentTable({ items }: { items: StateMetric[] }) {
  const visible = items.slice(0, 10);
  return <div className="table-scroll"><table className="data-table"><thead><tr><th>Customer state</th><th>Delivered</th><th>Late share</th><th>Avg. transit</th></tr></thead><tbody>
    {visible.map((item) => <tr key={item.state}><th><span className="state-pill">{item.state}</span></th><td>{number(item.deliveredOrders)}</td><td><span className={`rate ${item.lateRate >= 20 ? "rate-high" : ""}`}>{item.lateRate.toFixed(1)}%</span><span className="sub-cell"> {number(item.lateOrders)} orders</span></td><td>{item.averageDays.toFixed(1)} days</td></tr>)}
  </tbody></table></div>;
}

function Dashboard({ page, region, series, previousSeries, chartMetric, onChartMetric, onPage }: { page: PageId; region: RegionId; series: Month[]; previousSeries: Month[]; chartMetric: ChartMetric; onChartMetric: (metric: ChartMetric) => void; onPage: (page: PageId) => void }) {
  const summary = data.summaryByRegion[region];
  const stages = data.funnelByRegion[region];
  const cohorts = data.cohortsByRegion[region];
  const categories = data.categoriesByRegion[region];
  const fulfillment = data.fulfillmentByRegion[region];
  const topCategory = categories[0];
  const m2 = summary.month2Retention;
  const topFiveShare = categories.slice(0, 5).reduce((sum, category) => sum + category.share, 0);
  const rangeGmv = series.reduce((sum, row) => sum + row.gmv, 0);
  const rangeOrders = series.reduce((sum, row) => sum + row.orders, 0);
  const rangeAov = rangeOrders ? rangeGmv / rangeOrders : 0;
  const previousGmv = previousSeries.reduce((sum, row) => sum + row.gmv, 0);
  const gmvChange = previousGmv ? ((rangeGmv - previousGmv) / previousGmv) * 100 : null;
  const bestMonth = series.reduce<Month | null>((best, row) => !best || row.gmv > best.gmv ? row : best, null);
  const rangeText = series.length ? `${monthLabel(series[0].month)} — ${monthLabel(series[series.length - 1].month)}` : "No months in this range";
  const pageTitle = pageCopy[page];

  return <>
    <div className="page-heading"><div><h1>{pageTitle.title}</h1><p>{pageTitle.description}</p></div><div className="period-note"><span className="live-dot" /> Synthetic snapshot <span className="period-divider">·</span> Jan 2022 — Aug 2023</div></div>
    {page === "overview" && <>
      <section className="metric-grid" aria-label="Selected period metrics">
        <Metric label="Eligible orders" value={number(rangeOrders)} detail={rangeText} icon={ShoppingBag} tone="green" />
        <Metric label="Gross merchandise value" value={brl(rangeGmv, true)} detail={`Selected window · ${regionLabel(region)}`} icon={BarChart3} tone="orange" footnote={gmvChange === null ? "No prior window to compare" : `${gmvChange > 0 ? "↑" : gmvChange < 0 ? "↓" : "→"} ${Math.abs(gmvChange).toFixed(1)}% vs previous ${previousSeries.length}-month window`} />
        <Metric label="Average order value" value={brl(rangeAov)} detail="GMV ÷ eligible orders" icon={Gauge} tone="blue" />
        <Metric label="Month 2 retention" value={m2 === null ? "—" : `${m2.toFixed(1)}%`} detail="Full observation window" icon={Users} tone="plum" footnote="Calculated from repeat orders" />
      </section>
      <section className="quick-stats" aria-label="Additional marketplace statistics">
        <article className="quick-stat quick-stat-teal"><span className="quick-stat-icon"><Gauge size={16} /></span><div><small>Average monthly GMV</small><strong>{brl(series.length ? rangeGmv / series.length : 0, true)}</strong></div></article>
        <article className="quick-stat quick-stat-coral"><span className="quick-stat-icon"><PackageCheck size={16} /></span><div><small>Delivered on time</small><strong>{(100 - summary.lateRate).toFixed(1)}%</strong><em>all-time · delivered orders</em></div></article>
        <article className="quick-stat quick-stat-gold"><span className="quick-stat-icon"><Sparkles size={16} /></span><div><small>Best month in range</small><strong>{bestMonth ? monthLabel(bestMonth.month) : "—"}</strong><em>{bestMonth ? brl(bestMonth.gmv, true) : "No monthly data"} GMV</em></div></article>
      </section>
      <section className="overview-grid">
        <article className="panel sales-panel"><div className="panel-heading"><div><h2>Marketplace activity</h2><p>Monthly {chartMetric === "gmv" ? "GMV" : "eligible orders"} · {rangeText}</p></div><div className="chart-tools"><div className="chart-toggle" role="group" aria-label="Chart metric">{(["gmv", "orders"] as ChartMetric[]).map((metric) => <button key={metric} className={chartMetric === metric ? "selected" : ""} aria-pressed={chartMetric === metric} onClick={() => onChartMetric(metric)}>{metric === "gmv" ? "GMV" : "Orders"}</button>)}</div><span className={`legend legend-${chartMetric}`}><i /> {chartMetric === "gmv" ? "BRL" : "Orders"}</span></div></div>
          {series.length ? <TrendChart series={series} metric={chartMetric} /> : <EmptyState message="No orders fall in this time window." />}
          <div className="panel-foot"><span>{number(rangeOrders)} eligible orders</span><span>{brl(rangeGmv, true)} total GMV</span></div>
        </article>
        <article className="panel funnel-panel"><div className="panel-heading"><div><h2>Order funnel</h2><p>Distinct transactions · all-time view</p></div><button className="text-button" onClick={() => onPage("funnel")}>Explore <span>↗</span></button></div>
          <Funnel stages={stages} compact />
        </article>
      </section>
      <section className="overview-grid lower-grid">
        <article className="panel retention-panel"><div className="panel-heading"><div><h2>Customer return rate</h2><p>Share of each cohort purchasing again</p></div><button className="text-button" onClick={() => onPage("retention")}>Full cohorts <span>↗</span></button></div>
          <CohortTable cohorts={cohorts} />
          <div className="legend-note"><span className="heat-legend"><i /><i /><i /><i /></span><span>Darker cells indicate higher retention</span><span className="legend-spacer" /><span>Latest cohorts are incomplete</span></div>
        </article>
        <article className="panel category-panel"><div className="panel-heading"><div><h2>Where GMV concentrates</h2><p>Category mix · eligible orders</p></div><span className="panel-aside">Top 5 <b>{topFiveShare.toFixed(1)}%</b></span></div>
          <Categories items={categories} compact />
        </article>
      </section>
      <div className="insight-note"><Sparkles size={16} /><p><strong>What stands out</strong>{` ${niceCategory(topCategory?.category ?? "categories")} leads the mix at ${topCategory?.share.toFixed(1) ?? "—"}% of GMV. Delivery lateness is ${summary.lateRate.toFixed(1)}% across ${number(summary.deliveredOrders)} delivered orders in this region.`}</p><button onClick={() => onPage("fulfillment")}>Review delivery <span>→</span></button></div>
    </>}
    {page === "funnel" && <>
      <section className="metric-grid metric-grid-three">
        <Metric label="Orders placed" value={number(stages[0]?.orders ?? 0)} detail="All statuses included" icon={ShoppingBag} />
        <Metric label="Delivered" value={number(stages[3]?.orders ?? 0)} detail={`${(stages[3]?.conversion ?? 0).toFixed(1)}% of orders placed`} icon={PackageCheck} tone="blue" />
        <Metric label="End-to-end drop-off" value={number((stages[0]?.orders ?? 0) - (stages[3]?.orders ?? 0))} detail="Orders not marked delivered" icon={ArrowDownRight} tone="orange" />
      </section>
      <section className="panel deep-panel"><div className="panel-heading"><div><h2>Order progression</h2><p>Each order is counted once at each timestamp milestone.</p></div><span className="unit-tag">REGION · {regionLabel(region)}</span></div><Funnel stages={stages} /></section>
      <section className="overview-grid lower-grid"><article className="panel"><div className="panel-heading"><div><h2>Reading the stages</h2><p>The funnel is operational, not a website visit funnel.</p></div></div><div className="definition-list"><div><b>01</b><div><strong>Orders placed</strong><p>All order records created in the selected corridor.</p></div></div><div><b>02</b><div><strong>Payment approved</strong><p>An approval timestamp is present on the order.</p></div></div><div><b>03</b><div><strong>Handed to carrier</strong><p>A carrier handoff timestamp is present.</p></div></div><div><b>04</b><div><strong>Delivered</strong><p>Status is delivered and a customer delivery timestamp exists.</p></div></div></div></article><article className="panel"><div className="panel-heading"><div><h2>Stage conversion</h2><p>Relative to all orders placed</p></div></div><div className="conversion-list">{stages.map((item, i) => <div key={item.stage}><span>{item.stage}</span><strong>{item.conversion.toFixed(1)}%</strong>{i > 0 && <small>{number(item.dropoff)} fewer than prior stage</small>}</div>)}</div></article></section>
    </>}
    {page === "retention" && <>
      <section className="metric-grid metric-grid-three">
        <Metric label="First-time customers" value={number(summary.customers)} detail="Across eligible orders" icon={Users} tone="green" />
        <Metric label="Month 2 return" value={m2 === null ? "—" : `${m2.toFixed(1)}%`} detail="Weighted across mature cohorts" icon={ArrowUpRight} tone="plum" />
        <Metric label="Observation window" value="20 months" detail="Jan 2022 — Aug 2023" icon={Gauge} tone="blue" />
      </section>
      <article className="panel deep-panel cohort-large"><div className="panel-heading"><div><h2>Monthly customer cohorts</h2><p>Each row starts at 100%; later cells show the share who ordered again.</p></div><span className="unit-tag">{regionLabel(region)}</span></div><CohortTable cohorts={cohorts} />
        <div className="legend-note"><span className="heat-legend"><i /><i /><i /><i /></span><span>0%</span><span className="legend-spacer" /><span>Higher repeat share</span><span>·</span><span>— Not yet observable</span></div>
      </article>
      <article className="insight-note quiet-note"><CircleHelp size={16} /><p><strong>How to read this:</strong> a customer is assigned to their first eligible order month. Month N counts distinct customers with at least one eligible order in that calendar month. Recent cohorts are right-censored where the dataset ends.</p></article>
    </>}
    {page === "fulfillment" && <>
      <section className="metric-grid metric-grid-three">
        <Metric label="Delivered orders" value={number(summary.deliveredOrders)} detail="Each transaction counted once" icon={PackageCheck} tone="green" />
        <Metric label="Late delivery share" value={`${summary.lateRate.toFixed(1)}%`} detail={`${number(summary.lateOrders)} orders after estimate`} icon={ArrowDownRight} tone="orange" />
        <Metric label="Average transit" value={`${summary.averageDeliveryDays.toFixed(1)} days`} detail="Purchase to customer delivery" icon={Gauge} tone="blue" />
      </section>
      <article className="panel deep-panel"><div className="panel-heading"><div><h2>Delivery service by customer state</h2><p>Late means actual customer delivery occurred after the estimated date.</p></div><span className="unit-tag">SORTED BY LATE SHARE</span></div><FulfillmentTable items={fulfillment} /><div className="table-caption">States with fewer orders can show more volatile rates. Use volume alongside percentage.</div></article>
      <div className="insight-note"><Sparkles size={16} /><p><strong>Highest observed late share</strong>{fulfillment[0] ? ` ${fulfillment[0].state} is ${fulfillment[0].lateRate.toFixed(1)}% late across ${number(fulfillment[0].deliveredOrders)} delivered orders.` : " No delivery records in this selection."} This is descriptive sample data, not a causal diagnosis.</p></div>
    </>}
    {page === "method" && <>
      <section className="case-study-intro"><div className="case-illustration"><div className="case-graph"><i /><i /><i /><i /><span /></div><div className="case-stamp">DATA<br />NOTES</div></div><div><span className="case-kicker">PORTFOLIO CASE STUDY</span><h2>From transaction tables to useful signals.</h2><p>This workspace explores the operational shape of a marketplace: how orders progress, which customers return, where category value concentrates, and how delivery promises vary by state.</p><div className="case-meta"><span>PostgreSQL patterns</span><i /> <span>Python aggregation</span><i /> <span>Interactive dashboard</span></div></div></section>
      <section className="method-grid"><article className="panel"><div className="panel-heading"><div><h2>Data provenance</h2><p>Be precise about what this sample represents.</p></div></div><div className="provenance-callout"><span className="notice-mark">i</span><p><strong>Synthetic demonstration data.</strong> The bundled source was generated for portfolio presentation and calibrated to resemble a Brazilian marketplace. It is not the public Olist dataset and does not validate customer, revenue, or service outcomes.</p></div><div className="definition-list"><div><b>Currency</b><div><strong>Brazilian real (BRL)</strong><p>All gross merchandise value includes item price plus freight.</p></div></div><div><b>Period</b><div><strong>{data.meta.periodStart} to {data.meta.periodEnd}</strong><p>{number(data.meta.sourceOrderRows)} order rows across {data.meta.tableCount} related tables.</p></div></div><div><b>Retention</b><div><strong>Distinct customers by calendar month</strong><p>Month 0 is the first eligible order month; repeat months are compared with original cohort size.</p></div></div><div><b>Late delivery</b><div><strong>Order-level comparison</strong><p>Each delivered order is evaluated once against its estimate, regardless of basket line count.</p></div></div></div></article>
        <article className="panel"><div className="panel-heading"><div><h2>Source tables</h2><p>Relational entities included in the generated sample.</p></div><span className="unit-tag">{data.meta.tableCount} TABLES</span></div><div className="source-table-list">{data.meta.tables.map((table) => <div key={table.name}><span>{table.name}</span><strong>{number(table.rows)}</strong></div>)}</div></article></section>
      <section className="panel data-methods"><div className="panel-heading"><div><h2>Metric definitions</h2><p>Keep the denominator visible.</p></div></div><div className="definition-grid"><div><strong>Gross merchandise value</strong><code>SUM(item price + freight)</code><p>Includes eligible orders; excludes canceled and unavailable statuses.</p></div><div><strong>Average order value</strong><code>Eligible GMV ÷ eligible orders</code><p>One denominator order per transaction, including multi-item baskets.</p></div><div><strong>Month 2 retention</strong><code>Active customers in M2 ÷ cohort size</code><p>Weighted across cohorts with a full two-month observation window.</p></div><div><strong>Late delivery share</strong><code>Late delivered orders ÷ delivered orders</code><p>Late when customer delivery timestamp exceeds the estimated date.</p></div></div></section>
      <div className="case-footer"><span>Prepared as a local, read-only portfolio product.</span><button className="text-button" onClick={() => onPage("overview")}>Back to overview <span>↗</span></button></div>
    </>}
  </>;
}

function EmptyState({ message }: { message: string }) { return <div className="empty-state"><Filter size={19} /><p>{message}</p></div>; }
function regionLabel(id: RegionId) { return data.regions.find((r) => r.id === id)?.label ?? "All regions"; }

export default function Home() {
  const [page, setPage] = useState<PageId>("overview");
  const [region, setRegion] = useState<RegionId>("all");
  const [windowSize, setWindowSize] = useState("all");
  const [chartMetric, setChartMetric] = useState<ChartMetric>("gmv");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [exportState, setExportState] = useState(false);
  const series = useMemo(() => {
    const all = data.monthlyByRegion[region];
    const count = windowSize === "all" ? all.length : Number(windowSize);
    return all.slice(Math.max(0, all.length - count));
  }, [region, windowSize]);
  const previousSeries = useMemo(() => {
    const all = data.monthlyByRegion[region];
    const count = windowSize === "all" ? 0 : Number(windowSize);
    return count && all.length >= count * 2 ? all.slice(all.length - count * 2, all.length - count) : [];
  }, [region, windowSize]);
  const copyExport = () => {
    const orders = series.reduce((sum, row) => sum + row.orders, 0);
    const gmv = series.reduce((sum, row) => sum + row.gmv, 0);
    const content = JSON.stringify({ region, months: series, selectedPeriod: { eligibleOrders: orders, gmv: Number(gmv.toFixed(2)), averageOrderValue: orders ? Number((gmv / orders).toFixed(2)) : 0 } }, null, 2);
    const blob = new Blob([content], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `commerce-snapshot-${region}-${windowSize}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
    setExportState(true);
    window.setTimeout(() => setExportState(false), 1800);
  };

  return <div className="app-frame">
    <a className="skip-link" href="#dashboard-content">Skip to content</a>
    <aside className="sidebar"><Sidebar page={page} setPage={setPage} /></aside>
    {mobileOpen && <div className="mobile-scrim" onClick={() => setMobileOpen(false)}><aside className="mobile-sidebar" onClick={(event) => event.stopPropagation()}><button className="mobile-close" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X size={19} /></button><Sidebar page={page} setPage={setPage} close={() => setMobileOpen(false)} /></aside></div>}
    <main className="main-shell" id="dashboard-content" tabIndex={-1}>
      <header className="topbar"><button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu size={20} /></button><div className="crumb"><span>STUDY</span><b>/</b><strong>{navItems.find((item) => item.id === page)?.label}</strong></div><div className="top-actions"><div className="dataset-indicator"><span className="dataset-indicator-dot" /> Local snapshot</div><button className={`export-button ${exportState ? "export-done" : ""}`} onClick={copyExport} title="Download filtered data as JSON"><Download size={15} /><span>{exportState ? "Downloaded" : "Export"}</span></button></div></header>
      <div className="content-shell"><div className="controls-row"><div className="region-control"><label htmlFor="region">Corridor</label><div className="select-shell"><select id="region" value={region} onChange={(e) => setRegion(e.target.value as RegionId)}>{data.regions.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}</select><ChevronDown size={14} /></div></div><div className="range-control" aria-label="Monthly chart range">{[{ id: "3", label: "3M" }, { id: "6", label: "6M" }, { id: "12", label: "12M" }, { id: "all", label: "All" }].map((option) => <button key={option.id} className={windowSize === option.id ? "selected" : ""} onClick={() => setWindowSize(option.id)} aria-pressed={windowSize === option.id}>{option.label}</button>)}</div></div>
        <Dashboard page={page} region={region} series={series} previousSeries={previousSeries} chartMetric={chartMetric} onChartMetric={setChartMetric} onPage={setPage} />
        <footer className="content-footer"><span>FIELDNOTE <i>·</i> COMMERCE INTELLIGENCE</span><span>Sample data · For exploration only</span><button onClick={() => setPage("method")}>Definitions & provenance <ExternalLink size={12} /></button></footer>
      </div>
    </main>
  </div>;
}
