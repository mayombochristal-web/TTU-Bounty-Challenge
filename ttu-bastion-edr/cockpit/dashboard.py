import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
DATABASE_URL = st.secrets["db_url"]
st.set_page_config(page_title="TTU BASTION Cockpit", layout="wide")
st.title("️ TTU BASTION EDR – Monitoring de la Courbure k")
conn = psycopg2.connect(DATABASE_URL)
df = pd.read_sql("SELECT app_name, k_factor, adaptive_threshold, last_heartbeat FROM
ttu_core.registry", conn)
conn.close()
st.subheader("Applications enregistrées")
st.dataframe(df, use_container_width=True)
fig = px.line(df, x="app_name", y=["k_factor", "adaptive_threshold"], title="Courbure et seuil
adaptatif")
st.plotly_chart(fig, use_container_width=True)
st.subheader("État de santé global")
st.metric("Applications actives", len(df))
avg_k = df["k_factor"].mean()
st.metric("Courbure moyenne", f"{avg_k:.2f}")