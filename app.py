import streamlit as st
import pandas as pd
import plotly.express as px

# Load Data
def load_data():
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
        return df
    else:
        st.warning("Please upload a valid Excel file.")
        return None

# KPI Cards
def display_kpis(df):
    total_cost = df["Cost"].sum()
    total_weight = df["Weight"].sum()
    avg_cost_per_kg = total_cost / total_weight if total_weight else 0
    top_loss_reason = df["Loss Reason"].mode()[0] if not df["Loss Reason"].isna().all() else "N/A"
    pre_consumer_pct = (df[df["Stage of Processing"] == "Pre-Consumer"].shape[0] / df.shape[0]) * 100

    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)
    col1.metric("Total Cost", f"${total_cost:,.2f}")
    col2.metric("Total Weight", f"{total_weight:,.2f} kg")
    col3.metric("Avg Cost/KG", f"${avg_cost_per_kg:,.2f}")
    col4.metric("Top Loss Reason", top_loss_reason[:30])
    col5.metric("% Pre-Consumer", f"{pre_consumer_pct:.1f}%")

# Filters
def apply_filters(df):
    start_date = st.sidebar.date_input("Start Date", df["Date"].min().date())
    end_date = st.sidebar.date_input("End Date", df["Date"].max().date())
    df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

    regions = df["Region"].dropna().unique()
    selected_region = st.sidebar.selectbox("Select Region", regions)
    df = df[df["Region"] == selected_region]

    sites = df["Site"].dropna().unique()
    selected_site = st.sidebar.selectbox("Select Site", sites)
    df = df[df["Site"] == selected_site]

    locations = df["Location"].dropna().unique()
    selected_location = st.sidebar.selectbox("Select Location", locations)
    df = df[df["Location"] == selected_location]

    operators = df["Operator"].dropna().unique()
    selected_operator = st.sidebar.selectbox("Select Operator", ["All"] + list(operators))
    if selected_operator != "All":
        df = df[df["Operator"] == selected_operator]

    return df

# Visualizations
def render_visualizations(df):
    st.subheader("Wastage Trend Over Time")
    time_series = df.groupby("Date").agg({"Cost": "sum"}).reset_index()
    st.plotly_chart(px.line(time_series, x="Date", y="Cost", title="Wastage Cost Over Time ($)"))

    st.subheader("Wastage by Loss Reason")
    reason_chart = df["Loss Reason"].value_counts().reset_index()
    reason_chart.columns = ["Loss Reason", "Count"]
    st.plotly_chart(px.bar(reason_chart, x="Loss Reason", y="Count", title="Loss Reason Count"))

    st.subheader("Wastage by Food Category and Item")
    category_item_chart = df.groupby(["Food Item Category", "Food Item"]).size().reset_index(name='Count')
    st.plotly_chart(px.sunburst(category_item_chart, path=["Food Item Category", "Food Item"], values="Count", title="Drill-down: Food Category to Item"))

    st.subheader("Disposition Distribution")
    disposition_chart = df["Disposition"].value_counts().reset_index()
    disposition_chart.columns = ["Disposition", "Count"]
    st.plotly_chart(px.pie(disposition_chart, names="Disposition", values="Count", title="Disposition Breakdown"))

    st.subheader("Stage of Processing")
    stage_chart = df["Stage of Processing"].value_counts().reset_index()
    stage_chart.columns = ["Stage", "Count"]
    st.plotly_chart(px.pie(stage_chart, names="Stage", values="Count", title="Processing Stage Breakdown"))

    st.subheader("Cost vs. Weight")
    st.plotly_chart(px.scatter(df, x="Weight", y="Cost", color="Loss Reason", title="Cost ($) vs Weight (kg)", labels={"Weight": "Weight (kg)", "Cost": "Cost ($)"}))

    st.subheader("Monthly Wastage Comparison")
    monthly_chart = df.groupby("Month").agg({"Cost": "sum", "Weight": "sum"}).reset_index()
    st.plotly_chart(px.bar(monthly_chart, x="Month", y=["Cost", "Weight"], barmode='group', title="Monthly Wastage Comparison"))

    st.subheader("Cost per KG by Site")
    site_cost_chart = df.groupby("Site").apply(lambda x: x["Cost"].sum() / x["Weight"].sum() if x["Weight"].sum() else 0).reset_index(name="Cost per KG")
    st.plotly_chart(px.bar(site_cost_chart, x="Site", y="Cost per KG", title="Cost per KG by Site"))

    st.subheader("Wastage Cost by Operator")
    operator_chart = df.groupby("Operator")["Cost"].sum().reset_index().sort_values(by="Cost", ascending=False)
    st.plotly_chart(px.bar(operator_chart, x="Operator", y="Cost", title="Wastage Cost by Operator"))
    
    st.subheader("Estimated CO2 Impact (Based on Weight)")
    df["Estimated CO2 (kg)"] = df["Weight"] * 2.5
    co2_chart = df.groupby("Date")["Estimated CO2 (kg)"].sum().reset_index()
    st.plotly_chart(px.area(co2_chart, x="Date", y="Estimated CO2 (kg)", title="Estimated CO2 Emissions from Food Waste"))
    
    st.subheader("CO2 Emissions by Disposition Method")
    co2_disp_chart = df.groupby("Disposition")["Estimated CO2 (kg)"].sum().reset_index()
    st.plotly_chart(px.bar(co2_disp_chart, x="Disposition", y="Estimated CO2 (kg)", title="CO2 Impact by Disposition Method"))

# Main App
def main():
    st.set_page_config(layout="wide", page_title="Food Wastage Dashboard")
    st.title("\U0001F372 Waste Watch - Analytical Dashboard")
    df = load_data()
    if df is not None:
        df_filtered = apply_filters(df)
        display_kpis(df_filtered)
        render_visualizations(df_filtered)

if __name__ == "__main__":
    main()