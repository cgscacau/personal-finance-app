import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa

st.title("🎯 Orçamentos & Metas")
require_login()
uid = current_user_id()

tab1, tab2 = st.tabs(["Orçamentos","Metas"])

with tab1:
    b = supa().table("budgets").select("*").eq("user_id", uid).order("start_date", desc=False).execute().data
    st.dataframe(pd.DataFrame(b), use_container_width=True)
    with st.form("new_budget"):
        name = st.text_input("Nome do orçamento", "Orçamento Alimentação")
        cat = st.text_input("Categoria", "Alimentação")
        period = st.selectbox("Período", ["weekly", "monthly", "yearly"])
        start = st.date_input("Início")
        end = st.date_input("Fim (opcional)", value=None)
        amt = st.number_input("Valor limite (R$)", step=100.0, min_value=0.01)
        if st.form_submit_button("Adicionar"):
            supa().table("budgets").insert({
                "user_id": uid,
                "name": name,
                "category": cat,
                "amount": float(amt),
                "period": period,
                "start_date": str(start),
                "end_date": str(end) if end else None
            }).execute()
            st.success("Orçamento criado."); st.rerun()

with tab2:
    g = supa().table("goals").select("*").eq("user_id", uid).order("created_at", desc=False).execute().data
    st.dataframe(pd.DataFrame(g), use_container_width=True)
    with st.form("new_goal"):
        name = st.text_input("Nome da meta", "Reserva de Emergência")
        target = st.number_input("Alvo (R$)", step=100.0, min_value=0.01)
        curr = st.number_input("Atual (R$)", step=100.0, value=0.0, min_value=0.0)
        tdate = st.date_input("Prazo (opcional)", value=None)
        if st.form_submit_button("Adicionar"):
            supa().table("goals").insert({
                "user_id": uid,
                "name": name,
                "target_amount": float(target),
                "current_amount": float(curr),
                "deadline": str(tdate) if tdate else None
            }).execute()
            st.success("Meta criada."); st.rerun()
