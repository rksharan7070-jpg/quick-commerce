 
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------
st.set_page_config(
    page_title="Quick Commerce Analytics | CA4",
    page_icon="📊",
    layout="wide"
)

# -------------------------------
# 2. LOAD DATA
# -------------------------------
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "quick_commerce_analysis.csv"
    data = pd.read_csv(file_path)

    required_columns = [
        "Order_ID", "Company", "City", "Order_Value",
        "Delivery_Time_Min", "Product_Category",
        "Customer_Rating", "Delivery_Partner_Rating",
        "On_Time_Flag_Assumed_30_Min_SLA"
    ]

    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return data


try:
    df = load_data()
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.info(
        "Keep quick_commerce_analysis.csv in the same folder as app.py."
    )
    st.stop()

# -------------------------------
# 3. DASHBOARD TITLE
# -------------------------------
st.title("📊 Quick Commerce Business Analytics")
st.caption("CA4 Project | Order, Delivery and Customer Experience Analysis")


# -------------------------------
# 4. SIDEBAR FILTERS
# -------------------------------
st.sidebar.header("Dashboard Filters")

companies = st.sidebar.multiselect(
    "Select company",
    options=sorted(df["Company"].dropna().unique()),
    default=sorted(df["Company"].dropna().unique())
)

cities = st.sidebar.multiselect(
    "Select city",
    options=sorted(df["City"].dropna().unique()),
    default=sorted(df["City"].dropna().unique())
)

categories = st.sidebar.multiselect(
    "Select product category",
    options=sorted(df["Product_Category"].dropna().unique()),
    default=sorted(df["Product_Category"].dropna().unique())
)

filtered_df = df[
    df["Company"].isin(companies)
    & df["City"].isin(cities)
    & df["Product_Category"].isin(categories)
].copy()

if filtered_df.empty:
    st.warning("No records match your selected filters.")
    st.stop()

st.caption(f"Showing {len(filtered_df):,} orders after filtering.")

# -------------------------------
# 5. KPI CARDS
# -------------------------------
total_orders = len(filtered_df)
avg_order_value = filtered_df["Order_Value"].mean()
avg_delivery_time = filtered_df["Delivery_Time_Min"].mean()
avg_rating = filtered_df["Customer_Rating"].mean()
on_time_rate = (
    filtered_df["On_Time_Flag_Assumed_30_Min_SLA"].mean() * 100
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Orders", f"{total_orders:,}")
c2.metric("Average Order Value", f"{avg_order_value:,.2f}")
c3.metric("Average Delivery Time", f"{avg_delivery_time:.2f} min")
c4.metric("Average Customer Rating", f"{avg_rating:.2f} / 5")

st.metric(
    "Orders Within Assumed 30-Minute Target",
    f"{on_time_rate:.2f}%"
)

st.divider()

# -------------------------------
# 6. COMPANY PERFORMANCE
# -------------------------------
st.subheader("Company Performance")

company_summary = filtered_df.groupby("Company").agg(
    Total_Orders=("Order_ID", "count"),
    Average_Order_Value=("Order_Value", "mean"),
    Average_Delivery_Time=("Delivery_Time_Min", "mean"),
    Average_Customer_Rating=("Customer_Rating", "mean")
).reset_index().round(2)

left, right = st.columns(2)

with left:
    fig = px.bar(
        company_summary.sort_values(
            "Average_Order_Value", ascending=False
        ),
        x="Company",
        y="Average_Order_Value",
        title="Average Order Value by Company",
        hover_data=["Total_Orders"]
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.bar(
        company_summary.sort_values(
            "Average_Customer_Rating", ascending=False
        ),
        x="Company",
        y="Average_Customer_Rating",
        title="Average Customer Rating by Company",
        hover_data=["Total_Orders"],
        range_y=[0, 5]
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    company_summary.sort_values(
        "Average_Customer_Rating", ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

st.divider()

# -------------------------------
# 7. CITY DELIVERY PERFORMANCE
# -------------------------------
st.subheader("Delivery Performance by City")

city_summary = filtered_df.groupby("City").agg(
    Total_Orders=("Order_ID", "count"),
    Average_Delivery_Time=("Delivery_Time_Min", "mean"),
    Average_Customer_Rating=("Customer_Rating", "mean")
).reset_index().round(2)

fig = px.bar(
    city_summary.sort_values(
        "Average_Delivery_Time", ascending=False
    ),
    x="City",
    y="Average_Delivery_Time",
    title="Average Delivery Time by City",
    hover_data=["Total_Orders", "Average_Customer_Rating"],
    labels={"Average_Delivery_Time": "Minutes"}
)
fig.update_layout(xaxis_tickangle=-35)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 8. PRODUCT CATEGORY ANALYSIS
# -------------------------------
st.subheader("Product Category Analysis")

category_summary = filtered_df.groupby("Product_Category").agg(
    Total_Orders=("Order_ID", "count"),
    Average_Order_Value=("Order_Value", "mean")
).reset_index().round(2)

fig = px.bar(
    category_summary.sort_values(
        "Average_Order_Value", ascending=False
    ),
    x="Product_Category",
    y="Average_Order_Value",
    title="Average Order Value by Product Category",
    hover_data=["Total_Orders"]
)
fig.update_layout(xaxis_tickangle=-30)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 9. DELIVERY TIME VS CUSTOMER RATING
# -------------------------------
st.subheader("Delivery Time and Customer Experience")

rating_data = filtered_df.copy()
rating_data["Delivery_Time_Group"] = pd.cut(
    rating_data["Delivery_Time_Min"],
    bins=[0, 10, 20, 30, float("inf")],
    labels=["5–10 min", "11–20 min", "21–30 min", "Above 30 min"]
)

rating_summary = rating_data.groupby(
    "Delivery_Time_Group", observed=False
).agg(
    Total_Orders=("Order_ID", "count"),
    Average_Customer_Rating=("Customer_Rating", "mean")
).reset_index().round(2)

fig = px.bar(
    rating_summary,
    x="Delivery_Time_Group",
    y="Average_Customer_Rating",
    title="Average Customer Rating by Delivery-Time Group",
    hover_data=["Total_Orders"],
    range_y=[0, 5]
)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 10. DOWNLOAD FILTERED DATA
# -------------------------------
st.subheader("Export Analysis")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Dataset (CSV)",
    data=csv_data,
    file_name="quick_commerce_filtered_data.csv",
    mime="text/csv"
)

st.caption(
    "CA4 educational analysis. Synthetic fields and assumed service "
    "targets must be interpreted as illustrative."
)
