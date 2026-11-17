import pandas as pd
import plotly.express as px

COLORS = ["#0B192C", "#0284C7", "#8B5CF6", "#38BDF8", "#6366F1", "#10B981"]

def daily_bar(logs_df: pd.DataFrame):
    if logs_df.empty:
        return None
    df = logs_df.groupby("Date").size().reset_index(name="Enquiries")
    fig = px.bar(df, x="Date", y="Enquiries", title="Daily Enquiry Volume", color_discrete_sequence=["#0284C7"], text_auto=True)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=15, r=15, t=40, b=15))
    return fig

def category_donut(logs_df: pd.DataFrame):
    if logs_df.empty:
        return None
    df = logs_df["Category"].value_counts().reset_index()
    df.columns = ["Category", "Count"]
    fig = px.pie(df, names="Category", values="Count", hole=0.48, title="Enquiries by Category", color_discrete_sequence=COLORS)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=15, r=15, t=40, b=15))
    return fig
