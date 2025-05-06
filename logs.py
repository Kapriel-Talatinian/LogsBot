# logs.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Config de la page ---
st.set_page_config(
    page_title="Dashboard des Trades",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Chargement des données ---
@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path, parse_dates=["entry_time", "exit_time"])
    df["pnl_cum"] = df["pnl"].cumsum()
    df["trade_duration"] = (
        df["exit_time"] - df["entry_time"]
    ).dt.total_seconds() / 60  # en minutes
    return df

df = load_data("trades_log.csv")

# --- Sidebar : filtres ---
st.sidebar.header("Filtres")
start_date = st.sidebar.date_input(
    "Date de début",
    value=df["entry_time"].dt.date.min()
)
end_date = st.sidebar.date_input(
    "Date de fin",
    value=df["exit_time"].dt.date.max()
)
sides = st.sidebar.multiselect(
    "Type de trade",
    options=df["side"].unique(),
    default=list(df["side"].unique())
)

df_filtered = df[
    (df["entry_time"].dt.date >= start_date) &
    (df["exit_time"].dt.date <= end_date) &
    (df["side"].isin(sides))
]

# --- KPI en en-tête ---
col1, col2, col3, col4 = st.columns(4)
total_trades = len(df_filtered)
net_pnl = df_filtered["pnl"].sum()
win_rate = df_filtered["pnl"].gt(0).mean() * 100 if total_trades else 0
max_dd = (df_filtered["pnl_cum"].cummax() - df_filtered["pnl_cum"]).max()

col1.metric("Total trades", total_trades)
col2.metric("PnL net (USD)", f"{net_pnl:,.2f}")
col3.metric("Taux de réussite", f"{win_rate:.1f}%")
col4.metric("Max Drawdown", f"{max_dd:,.2f} USD")

# --- Winning Days ---
daily_pnl = (
    df_filtered
    .groupby(df_filtered["exit_time"].dt.date)["pnl"]
    .sum()
    .rename("daily_pnl")
)
winning_days = daily_pnl[daily_pnl > 0]
num_winning = len(winning_days)

st.markdown("---")
st.subheader("Jours Gagnants")
wcol1, wcol2 = st.columns([1, 3])
wcol1.metric("Nombre de jours gagnants", num_winning)

df_winning = (
    winning_days
    .to_frame()
    .reset_index()
    .rename(columns={
        "exit_time": "Date",
        "daily_pnl": "PnL journalier"
    })
)

with wcol2:
    st.dataframe(
        df_winning.sort_values("Date", ascending=False),
        use_container_width=True
    )

st.markdown("---")

# --- Tableau interactif ---
st.subheader("Journal des trades")
st.dataframe(
    df_filtered[[
        "entry_time", "exit_time", "side",
        "entry_price", "exit_price", "size", "pnl"
    ]].sort_values("entry_time", ascending=False),
    use_container_width=True
)

# --- Graphiques ---
st.subheader("Évolution de l'équité cumulative")
fig1, ax1 = plt.subplots(figsize=(8, 3))
ax1.plot(df_filtered["exit_time"], df_filtered["pnl_cum"], linewidth=2)
ax1.set_xlabel("Date")
ax1.set_ylabel("Equité (USD)")
ax1.grid(True)
st.pyplot(fig1)

st.subheader("Distribution des PnL par trade")
fig2, ax2 = plt.subplots(figsize=(6, 3))
ax2.hist(df_filtered["pnl"], bins=30)
ax2.set_xlabel("PnL par trade (USD)")
ax2.set_ylabel("Nombre de trades")
ax2.grid(True)
st.pyplot(fig2)

st.subheader("Durée des trades (en minutes)")
fig3, ax3 = plt.subplots(figsize=(6, 3))
ax3.hist(df_filtered["trade_duration"], bins=30)
ax3.set_xlabel("Durée (min)")
ax3.set_ylabel("Nombre de trades")
ax3.grid(True)
st.pyplot(fig3)
