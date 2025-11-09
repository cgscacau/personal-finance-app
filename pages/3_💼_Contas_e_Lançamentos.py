import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import select, delete, supa

st.title("💼 Contas & Lançamentos")
require_login()
uid = current_user_id()

accounts = select("accounts", {"user_id": uid})
acc = st.selectbox("Conta", options=["(todas)"]+[a["name"] for a in accounts])
q = supa().table("transactions").select("*").eq("user_id", uid)
if acc!="(todas)":
    aid = [a["id"] for a in accounts if a["name"]==acc][0]
    q = q.eq("account_id", aid)
df = pd.DataFrame(q.order("date", desc=True).execute().data)
st.dataframe(df, use_container_width=True, height=500)

with st.expander("Excluir lançamento"):
    tx_id = st.text_input("ID do lançamento")
    if st.button("Excluir"):
        supa().table("transactions").delete().eq("user_id", uid).eq("id", tx_id).execute()
        st.success("Excluído."); st.rerun()
