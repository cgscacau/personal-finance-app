import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa
from app.charts import by_category_bar, cashflow_line, category_treemap

st.title("📊 Dashboard")
require_login()
uid = current_user_id()

period = st.selectbox("Período", ["Últimos 30 dias","Últimos 90 dias","Ano atual","Tudo"])
q = supa().table("transactions").select("*").eq("user_id", uid)
data = q.execute().data
df = pd.DataFrame(data)

if df.empty:
    st.info("Sem lançamentos ainda. Importe na aba anterior.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
today = pd.Timestamp.today(tz=None).normalize()
if period == "Últimos 30 dias":
    df = df[df["date"]>= (today - pd.Timedelta(days=30))]
elif period == "Últimos 90 dias":
    df = df[df["date"]>= (today - pd.Timedelta(days=90))]
elif period == "Ano atual":
    df = df[df["date"].dt.year == today.year]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Receitas (R$)", f'{df[df["amount"]>0]["amount"].sum():,.2f}')
col2.metric("Despesas (R$)", f'{-df[df["amount"]<0]["amount"].sum():,.2f}')
col3.metric("Saldo (R$)", f'{df["amount"].sum():,.2f}')
col4.metric("Lançamentos", f'{len(df):,}')

st.plotly_chart(by_category_bar(df), use_container_width=True)
st.plotly_chart(category_treemap(df), use_container_width=True)
st.plotly_chart(cashflow_line(df), use_container_width=True)

with st.expander("Tabela"):
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)
