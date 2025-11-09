import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa

st.title("🧠 Regras de Categorização")
require_login()
uid = current_user_id()

rules = supa().table("categorization_rules").select("*").eq("user_id", uid).order("priority").execute().data
st.dataframe(pd.DataFrame(rules), use_container_width=True)

with st.form("new_rule"):
    pattern = st.text_input("Regex (ex: IFOOD|RAPPI|UBER)")
    category = st.text_input("Categoria", "Alimentação")
    subcat = st.text_input("Subcategoria", "Delivery")
    prio = st.number_input("Prioridade", 1, 999, 100)
    s = st.form_submit_button("Adicionar")
    if s and pattern and category:
        supa().table("categorization_rules").insert({
            "user_id": uid, "pattern": pattern, "category": category,
            "subcategory": subcat or None, "priority": int(prio)
        }).execute()
        st.success("Regra criada."); st.rerun()
