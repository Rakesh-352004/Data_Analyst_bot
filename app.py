import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(
    page_title="AI Data Analyst Dashboard",
    layout="wide"
)

st.title("📊 AI Data Analyst Dashboard")
st.markdown("Power BI–style dashboard with Natural Language Analytics")

# ---------------- SIDEBAR ---------------- #
st.sidebar.header("🔧 Data Source")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV / Excel",
    type=["csv", "xlsx"]
)

st.sidebar.subheader("🗄️ MySQL Connection")
host = st.sidebar.text_input("Host", "localhost")
user = st.sidebar.text_input("User", "root")
password = st.sidebar.text_input("Password", type="password")
database = st.sidebar.text_input("Database", "ai_analytics")
table = st.sidebar.text_input("Table", "sales_data")

load_sql = st.sidebar.button("Load from SQL")

# ---------------- LOAD DATA ---------------- #
def load_file(file):
    if file.name.endswith(".csv"):
        try:
            return pd.read_csv(file, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(file, encoding="latin1")
    else:
        return pd.read_excel(file)

df = None

if uploaded_file:
    df = load_file(uploaded_file)

if load_sql:
    try:
        engine = create_engine(
            f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"
        )
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        st.sidebar.success("✅ Data loaded from MySQL")
    except Exception as e:
        st.sidebar.error(f"❌ SQL Error: {e}")

# ---------------- DASHBOARD ---------------- #
if df is not None:

    st.subheader("📌 Dataset Preview")
    st.dataframe(df, use_container_width=True)

    numeric_cols = df.select_dtypes(include="number").columns
    cat_cols = df.select_dtypes(include="object").columns

    # ---------------- FILTER ---------------- #
    if len(cat_cols) > 0:
        filter_col = st.selectbox("🔍 Filter by", cat_cols)
        filter_vals = st.multiselect(
            "Select values",
            df[filter_col].unique()
        )
        if filter_vals:
            df = df[df[filter_col].isin(filter_vals)]
    else:
        filter_col = None

    # ---------------- KPI CARDS ---------------- #
    st.subheader("📈 Key Metrics")

    if len(numeric_cols) > 0:
        kpi_col = numeric_cols[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total", f"{df[kpi_col].sum():,.0f}")
        c2.metric("Average", f"{df[kpi_col].mean():,.2f}")
        c3.metric("Maximum", f"{df[kpi_col].max():,.0f}")

    # ---------------- VISUALS ---------------- #
    st.subheader("📊 Visual Analysis")

    metric = st.selectbox("Select Metric", numeric_cols)

    fig_bar = px.bar(
        df,
        x=filter_col if filter_col else df.index,
        y=metric,
        title=f"{metric} Distribution"
    )

    fig_pie = px.pie(
        df,
        names=filter_col if filter_col else None,
        values=metric,
        title="Contribution"
    )

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig_bar, use_container_width=True)
    col2.plotly_chart(fig_pie, use_container_width=True)

    # ---------------- NATURAL LANGUAGE ---------------- #
    st.subheader("💬 Ask Question in English")

    user_query = st.text_input(
        "Example: Show total sales by product / Average profit by region"
    )

    def process_query(query, df):
        q = query.lower()

        # aggregation
        if "total" in q or "sum" in q:
            agg = "sum"
        elif "average" in q or "avg" in q or "mean" in q:
            agg = "mean"
        elif "max" in q or "highest" in q:
            agg = "max"
        elif "min" in q or "lowest" in q:
            agg = "min"
        else:
            agg = "sum"

        # metric
        metric = None
        for col in df.select_dtypes(include="number").columns:
            if col.lower() in q:
                metric = col
                break
        if metric is None:
            metric = df.select_dtypes(include="number").columns[0]

        # group by
        group_col = None
        for col in df.select_dtypes(include="object").columns:
            if col.lower() in q:
                group_col = col
                break

        return agg, metric, group_col

    if user_query:
        agg, metric, group_col = process_query(user_query, df)

        if group_col:
            result = df.groupby(group_col)[metric].agg(agg).reset_index()

            st.success(
                f"Showing **{agg.upper()} of {metric} by {group_col}**"
            )
            st.dataframe(result)

            fig_nl = px.bar(
                result,
                x=group_col,
                y=metric,
                title=f"{agg.upper()} {metric} by {group_col}"
            )
            st.plotly_chart(fig_nl, use_container_width=True)
        else:
            value = getattr(df[metric], agg)()
            st.success(f"{agg.upper()} {metric}: {value}")

    # ---------------- AI INSIGHTS ---------------- #
    st.subheader("🧠 AI Business Insights")

    st.success(f"""
    🔹 **{metric}** shows clear variation across categories  
    🔹 Highest values indicate strong performance areas  
    🔹 Dashboard enables fast, data-driven decisions  
    """)

else:
    st.info("⬅️ Upload CSV / Excel or connect to MySQL to start analysis")
