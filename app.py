
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="ReQuote | AI Procurement Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .main {background: #f7f8fa;}
    .block-container {padding-top: 2rem; max-width: 1400px;}
    .hero {
        padding: 28px 32px;
        border-radius: 18px;
        background: linear-gradient(135deg, #111827 0%, #263449 100%);
        color: white;
        margin-bottom: 22px;
    }
    .hero h1 {font-size: 42px; margin: 0;}
    .hero p {font-size: 17px; color: #d7dce5; margin-top: 8px;}
    .card {
        background: white;
        border: 1px solid #e6e8ec;
        border-radius: 14px;
        padding: 18px;
        height: 100%;
    }
    .metric-label {font-size: 13px; color: #667085;}
    .metric-value {font-size: 28px; font-weight: 700; margin-top: 4px;}
    .small {font-size: 12px; color: #667085;}
    .recommendation {
        border-left: 5px solid #111827;
        background: white;
        padding: 18px 20px;
        border-radius: 10px;
        border-top: 1px solid #e6e8ec;
        border-right: 1px solid #e6e8ec;
        border-bottom: 1px solid #e6e8ec;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Data helpers ----------
DEMO_QUOTES = pd.DataFrame([
    ["ABC Trading", "Premium Cotton Towels", 500, 18.00, 400, 0.05, 7, 94],
    ["Gulf Supplies", "Premium Cotton Towels", 500, 16.00, 900, 0.05, 10, 88],
    ["Prime Hospitality", "Premium Cotton Towels", 500, 19.00, 0, 0.05, 5, 97],
    ["ABC Trading", "Industrial Cleaner 5L", 120, 42.00, 250, 0.05, 7, 94],
    ["Gulf Supplies", "Industrial Cleaner 5L", 120, 38.50, 400, 0.05, 12, 88],
    ["Prime Hospitality", "Industrial Cleaner 5L", 120, 45.00, 0, 0.05, 5, 97],
    ["ABC Trading", "LED TV 55 inch", 10, 1650.00, 300, 0.05, 7, 94],
    ["Gulf Supplies", "LED TV 55 inch", 10, 1490.00, 500, 0.05, 14, 88],
    ["Prime Hospitality", "LED TV 55 inch", 10, 1725.00, 0, 0.05, 4, 97],
    ["ABC Trading", "Bed Linen Set", 80, 145.00, 300, 0.05, 8, 94],
    ["Gulf Supplies", "Bed Linen Set", 80, 132.00, 450, 0.05, 12, 88],
    ["Prime Hospitality", "Bed Linen Set", 80, 151.00, 0, 0.05, 5, 97],
], columns=["Supplier","Product","Quantity","Unit Price","Delivery Fee","VAT Rate","Lead Time (days)","Supplier Reliability"])

def normalize_columns(df):
    mapping = {}
    for c in df.columns:
        key = str(c).strip().lower().replace("_"," ").replace("-"," ")
        mapping[key] = c
    aliases = {
        "supplier": ["supplier","vendor","supplier name","vendor name"],
        "product": ["product","item","product name","item name","description"],
        "quantity": ["quantity","qty","units"],
        "unit price": ["unit price","price","unit cost","cost"],
        "delivery fee": ["delivery fee","delivery","shipping","shipping fee"],
        "vat rate": ["vat rate","vat","tax","tax rate"],
        "lead time (days)": ["lead time (days)","lead time","delivery days","days"],
        "supplier reliability": ["supplier reliability","reliability","supplier score"],
    }
    out = {}
    for target, choices in aliases.items():
        for choice in choices:
            if choice in mapping:
                out[target] = mapping[choice]
                break
    return out

def prepare_quotes(df):
    df = df.copy()
    cols = normalize_columns(df)
    required = ["supplier","product","quantity","unit price"]
    missing = [x for x in required if x not in cols]
    if missing:
        return None, f"Missing columns: {', '.join(missing)}"
    rename = {v:k for k,v in cols.items()}
    df = df.rename(columns=rename)
    for c in ["quantity","unit price","delivery fee","vat rate","lead time (days)","supplier reliability"]:
        if c not in df.columns:
            df[c] = 0 if c not in ["vat rate","supplier reliability"] else (0.05 if c=="vat rate" else 80)
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["subtotal"] = df["quantity"] * df["unit price"] + df["delivery fee"]
    df["VAT"] = df["subtotal"] * df["vat rate"]
    df["total"] = df["subtotal"] + df["VAT"]
    return df, None

def supplier_summary(df):
    g = df.groupby("supplier", as_index=False).agg(
        Total_Spend=("total","sum"),
        Avg_Reliability=("supplier reliability","mean"),
        Avg_Lead_Time=("lead time (days)","mean"),
        Items=("product","nunique")
    )
    g["Price Score"] = 100 * (g["Total_Spend"].max() - g["Total_Spend"]) / max(g["Total_Spend"].max()-g["Total_Spend"].min(), 1)
    g["Price Score"] = g["Price Score"].fillna(100)
    g["Reliability Score"] = g["Avg_Reliability"].clip(0,100)
    # Balanced score: cost matters most, but reliability and speed matter too.
    max_lead = max(g["Avg_Lead_Time"].max(), 1)
    g["Speed Score"] = 100 * (max_lead - g["Avg_Lead_Time"]) / max(max_lead - g["Avg_Lead_Time"].min(), 1)
    g["Speed Score"] = g["Speed Score"].fillna(100)
    g["Overall Score"] = (0.55*g["Price Score"] + 0.30*g["Reliability Score"] + 0.15*g["Speed Score"]).round(1)
    return g.sort_values("Overall Score", ascending=False)

def product_analysis(df):
    rows=[]
    for product, g in df.groupby("product"):
        cheapest = g.loc[g["total"].idxmin()]
        avg = g["total"].mean()
        saving = max(0, g["total"].max() - cheapest["total"])
        rows.append({
            "Product": product,
            "Recommended Supplier": cheapest["supplier"],
            "Best Total": cheapest["total"],
            "Average Quoted Total": avg,
            "Potential Saving vs Highest": saving,
            "Quoted Suppliers": g["supplier"].nunique()
        })
    return pd.DataFrame(rows)

# ---------- Sidebar ----------
st.sidebar.title("ReQuote")
st.sidebar.caption("AI Procurement Intelligence MVP")
page = st.sidebar.radio("Navigate", ["Overview", "Quote Analyzer", "Supplier Intelligence", "Price Intelligence", "Business Case"])

st.sidebar.divider()
st.sidebar.markdown("### Data")
data_mode = st.sidebar.radio("Choose data", ["Demo dataset", "Upload CSV / Excel"], label_visibility="collapsed")

if data_mode == "Upload CSV / Excel":
    uploaded = st.sidebar.file_uploader("Upload quotation data", type=["csv","xlsx","xls"])
    if uploaded:
        try:
            if uploaded.name.lower().endswith(".csv"):
                raw = pd.read_csv(uploaded)
            else:
                raw = pd.read_excel(uploaded)
            quotes, error = prepare_quotes(raw)
            if error:
                st.sidebar.error(error)
                quotes = DEMO_QUOTES.copy()
                quotes, _ = prepare_quotes(quotes)
            else:
                st.sidebar.success("Quotation data loaded.")
        except Exception as e:
            st.sidebar.error(f"Could not read file: {e}")
            quotes, _ = prepare_quotes(DEMO_QUOTES)
    else:
        quotes, _ = prepare_quotes(DEMO_QUOTES)
else:
    quotes, _ = prepare_quotes(DEMO_QUOTES)

# ---------- Header ----------
st.markdown("""
<div class="hero">
    <h1>ReQuote</h1>
    <p>AI-powered procurement intelligence for SMEs — compare quotations, detect overpricing and make better supplier decisions.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Overview ----------
if page == "Overview":
    total_spend = quotes["total"].sum()
    avg_quote = quotes["total"].mean()
    products = quotes["product"].nunique()
    suppliers = quotes["supplier"].nunique()

    c1,c2,c3,c4 = st.columns(4)
    for col, label, value in [
        (c1,"Quoted procurement value",f"AED {total_spend:,.0f}"),
        (c2,"Average quotation",f"AED {avg_quote:,.0f}"),
        (c3,"Products analyzed",str(products)),
        (c4,"Suppliers compared",str(suppliers)),
    ]:
        with col:
            st.markdown(f'<div class="card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Where can you save?")
        pa = product_analysis(quotes)
        st.dataframe(
            pa.style.format({
                "Best Total":"AED {:,.2f}",
                "Average Quoted Total":"AED {:,.2f}",
                "Potential Saving vs Highest":"AED {:,.2f}"
            }),
            use_container_width=True, hide_index=True
        )
    with right:
        st.subheader("AI recommendation")
        ss = supplier_summary(quotes)
        best = ss.iloc[0]
        st.markdown(f"""
        <div class="recommendation">
        <b>Recommended supplier: {best['supplier']}</b><br><br>
        Overall score: <b>{best['Overall Score']}/100</b><br>
        Total quoted value: <b>AED {best['Total_Spend']:,.2f}</b><br>
        Average lead time: <b>{best['Avg_Lead_Time']:.1f} days</b><br>
        Reliability: <b>{best['Avg_Reliability']:.0f}/100</b><br><br>
        The score balances quoted cost, supplier reliability and delivery speed.
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Procurement workflow")
    cols = st.columns(5)
    steps = [("01","Upload","Bring in supplier quotes"),
             ("02","Normalize","Convert messy quotes into comparable data"),
             ("03","Analyze","Compare price, delivery and reliability"),
             ("04","Detect","Flag unusual or expensive quotes"),
             ("05","Decide","Recommend the best purchasing option")]
    for col,(num,title,desc) in zip(cols,steps):
        with col:
            st.markdown(f'<div class="card"><b>{num} · {title}</b><p class="small">{desc}</p></div>', unsafe_allow_html=True)

# ---------- Quote Analyzer ----------
elif page == "Quote Analyzer":
    st.subheader("Quotation comparison")
    st.caption("Compare every supplier on the same product using landed cost, not just unit price.")

    product = st.selectbox("Select product", sorted(quotes["product"].unique()))
    q = quotes[quotes["product"] == product].copy().sort_values("total")
    q["Difference vs Best"] = q["total"] - q["total"].min()
    q["Premium vs Best"] = (q["total"]/q["total"].min()-1)*100

    st.dataframe(
        q[["supplier","quantity","unit price","delivery fee","VAT","total","lead time (days)","supplier reliability","Difference vs Best","Premium vs Best"]]
        .rename(columns={"supplier":"Supplier","quantity":"Qty","unit price":"Unit Price","delivery fee":"Delivery","VAT":"VAT","total":"Landed Total","lead time (days)":"Lead Time","supplier reliability":"Reliability"})
        .style.format({
            "Unit Price":"AED {:,.2f}","Delivery":"AED {:,.2f}","VAT":"AED {:,.2f}",
            "Landed Total":"AED {:,.2f}","Difference vs Best":"AED {:,.2f}","Premium vs Best":"{:.1f}%"
        }),
        use_container_width=True, hide_index=True
    )

    best = q.iloc[0]
    worst = q.iloc[-1]
    st.success(f"Best landed-cost option: **{best['supplier']}** at **AED {best['total']:,.2f}**. Potential saving versus the highest quote: **AED {worst['total']-best['total']:,.2f}**.")

    st.subheader("AI-style decision explanation")
    reliability_tradeoff = q.sort_values("supplier reliability", ascending=False).iloc[0]
    if reliability_tradeoff["supplier"] != best["supplier"] and reliability_tradeoff["total"] > best["total"]:
        st.info(
            f"{reliability_tradeoff['supplier']} has the highest reliability score ({reliability_tradeoff['supplier reliability']:.0f}/100), "
            f"but costs AED {reliability_tradeoff['total']-best['total']:,.2f} more than the lowest landed-cost option. "
            "The final decision should consider whether the reliability premium is worth the extra cost."
        )
    else:
        st.info("The lowest landed-cost supplier also performs strongly on the available supplier-quality indicators.")

# ---------- Supplier Intelligence ----------
elif page == "Supplier Intelligence":
    st.subheader("Supplier intelligence")
    ss = supplier_summary(quotes)
    st.dataframe(
        ss.rename(columns={
            "supplier":"Supplier","Total_Spend":"Quoted Spend","Avg_Reliability":"Reliability",
            "Avg_Lead_Time":"Avg Lead Time","Items":"Products","Overall Score":"Overall Score"
        }).style.format({
            "Quoted Spend":"AED {:,.2f}","Reliability":"{:.0f}","Avg Lead Time":"{:.1f}",
            "Overall Score":"{:.1f}"
        }),
        use_container_width=True, hide_index=True
    )

    st.subheader("Supplier scorecard")
    selected = st.selectbox("Supplier", ss["supplier"].tolist())
    s = ss[ss["supplier"] == selected].iloc[0]
    a,b,c = st.columns(3)
    a.metric("Overall score", f"{s['Overall Score']:.1f}/100")
    b.metric("Reliability", f"{s['Avg_Reliability']:.0f}/100")
    c.metric("Average lead time", f"{s['Avg_Lead_Time']:.1f} days")

    st.write("")
    st.markdown("**Scoring logic**")
    st.progress(int(min(100, max(0, s["Overall Score"]))) / 100)
    st.caption("55% cost competitiveness · 30% reliability · 15% delivery speed")

# ---------- Price Intelligence ----------
elif page == "Price Intelligence":
    st.subheader("Price intelligence")
    st.caption("A prototype of the future price-history and anomaly engine.")

    pa = product_analysis(quotes)
    st.dataframe(
        pa.style.format({
            "Best Total":"AED {:,.2f}",
            "Average Quoted Total":"AED {:,.2f}",
            "Potential Saving vs Highest":"AED {:,.2f}"
        }),
        use_container_width=True, hide_index=True
    )

    selected = st.selectbox("Inspect product", sorted(quotes["product"].unique()))
    p = quotes[quotes["product"] == selected].copy()
    mean = p["unit price"].mean()
    std = p["unit price"].std()
    threshold = mean + (1.5 * (std if not np.isnan(std) else 0))
    p["Price Flag"] = np.where(p["unit price"] > threshold, "⚠ Above expected range", "Normal")

    st.metric("Average quoted unit price", f"AED {mean:,.2f}")
    if (p["Price Flag"] != "Normal").any():
        st.warning("Potential price anomaly detected. This is a prototype rule-based flag; a production version would use historical transactions and a trained anomaly model.")
    else:
        st.success("No major price anomaly detected in the current quotation set.")

    st.bar_chart(p.set_index("supplier")["unit price"])

# ---------- Business Case ----------
elif page == "Business Case":
    st.subheader("Business case")
    st.caption("Illustrative assumptions for the academic prototype — not market-validated financial forecasts.")

    c1,c2,c3 = st.columns(3)
    with c1:
        monthly_price = st.number_input("Average monthly subscription (AED)", 49.0, 999.0, 149.0, 10.0)
    with c2:
        monthly_fixed = st.number_input("Monthly fixed costs (AED)", 1000.0, 100000.0, 12000.0, 1000.0)
    with c3:
        variable_per_user = st.number_input("Variable cost / customer (AED)", 1.0, 200.0, 18.0, 1.0)

    contribution = monthly_price - variable_per_user
    breakeven = np.ceil(monthly_fixed / contribution) if contribution > 0 else np.inf

    a,b,c = st.columns(3)
    a.metric("Contribution / customer", f"AED {contribution:,.0f}")
    b.metric("Estimated break-even", "Not reached" if np.isinf(breakeven) else f"{breakeven:,.0f} customers")
    c.metric("Break-even MRR", "—" if np.isinf(breakeven) else f"AED {breakeven*monthly_price:,.0f}")

    customers = np.arange(0, 1001, 25)
    revenue = customers * monthly_price
    costs = monthly_fixed + customers * variable_per_user
    chart = pd.DataFrame({"Revenue": revenue, "Total Cost": costs}, index=customers)
    st.line_chart(chart)

    st.markdown("""
    ### Why this can scale
    - Start with quotation comparison for SMEs.
    - Add historical price intelligence.
    - Add supplier performance scoring.
    - Add purchasing workflows and approvals.
    - Add supplier discovery and RFQ automation.
    - Eventually monetize transactions and aggregated procurement intelligence.
    """)

st.sidebar.divider()
st.sidebar.caption("ReQuote MVP · Built for academic prototyping")
