import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa

st.title("💳 Contas & Lançamentos")
require_login()
uid = current_user_id()

# --- Selecionar conta do usuário ---
res_accounts = supa().table("accounts").select("*").eq("user_id", uid).execute()
accounts = res_accounts.data or []
account_names = {a["name"]: a["id"] for a in accounts}
account_name = st.selectbox("Conta", list(account_names.keys()) or ["Nenhuma conta encontrada"])
aid = account_names.get(account_name)

# --- Formulário de lançamento manual ---
st.subheader("➕ Novo Lançamento")

with st.form("novo_lancamento"):
    date = st.date_input("Data")
    description = st.text_input("Descrição", placeholder="Ex: Almoço, Uber, Pagamento de conta...")
    amount = st.number_input("Valor (use negativo para despesa, positivo para receita)", step=0.01, format="%.2f")
    category = st.text_input("Categoria (opcional)")
    subcategory = st.text_input("Subcategoria (opcional)")
    tags = st.text_input("Tags (opcional, separadas por vírgula)")
    submit = st.form_submit_button("Adicionar")

    if submit:
        if not description or not amount:
            st.warning("Preencha ao menos a descrição e o valor.")
        else:
            data = {
                "user_id": uid,
                "account_id": aid,
                "date": str(date),
                "description": description.strip(),
                "amount": float(amount),
                "category": category or None,
                "subcategory": subcategory or None,
                "tags": tags or None,
                "source_file": "manual",
            }
            supa().table("transactions").insert(data).execute()
            st.success("Lançamento adicionado com sucesso!")
            st.rerun()

# --- Exibir lançamentos existentes ---
st.subheader("📜 Lançamentos Registrados")

res = supa().table("transactions").select("*").eq("user_id", uid).order("date", desc=True).execute()
data = res.data or []
df = pd.DataFrame(data)

if df.empty:
    st.info("Nenhum lançamento encontrado.")
else:
    st.dataframe(
        df[["date","description","amount","category","subcategory","tags"]],
        use_container_width=True,
        height=500
    )

# --- Botão de exclusão ---
if not df.empty:
    with st.expander("🗑 Excluir lançamento"):
        to_delete = st.selectbox("Selecione o ID do lançamento a excluir", df["id"])
        if st.button("Excluir lançamento"):
            supa().table("transactions").delete().eq("id", to_delete).execute()
            st.success("Lançamento excluído.")
            st.rerun()
