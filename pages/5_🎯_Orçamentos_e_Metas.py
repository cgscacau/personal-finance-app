import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa

st.title("🎯 Orçamentos & Metas")
require_login()
uid = current_user_id()

tab1, tab2 = st.tabs(["Orçamentos","Metas"])

with tab1:
    b = supa().table("budgets").select("*").eq("user_id", uid).order("period_start").execute().data
    st.dataframe(pd.DataFrame(b), use_container_width=True)
    with st.form("new_budget"):
        cat = st.text_input("Categoria", "Alimentação")
        start = st.date_input("Início")
        end = st.date_input("Fim")
        amt = st.number_input("Valor alvo (R$)", step=100.0)
        if st.form_submit_button("Adicionar"):
            supa().table("budgets").insert({
                "user_id": uid, "category": cat, "period_start": str(start),
                "period_end": str(end), "amount_target": float(amt)
            }).execute()
            st.success("Orçamento criado."); st.rerun()

with tab2:
    g = supa().table("goals").select("*").eq("user_id", uid).order("created_at").execute().data
    st.dataframe(pd.DataFrame(g), use_container_width=True)
    with st.form("new_goal"):
        name = st.text_input("Nome da meta", "Reserva de Emergência")
        target = st.number_input("Alvo (R$)", step=100.0)
        curr = st.number_input("Atual (R$)", step=100.0, value=0.0)
        tdate = st.date_input("Data alvo (opcional)")
        notes = st.text_area("Notas")
        if st.form_submit_button("Adicionar"):
            supa().table("goals").insert({
                "user_id": uid, "name": name, "target_amount": float(target),
                "current_amount": float(curr), "target_date": str(tdate),
                "notes": notes or None
            }).execute()
            st.success("Meta criada."); st.rerun()
