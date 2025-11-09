import streamlit as st
from app.auth import require_login, current_user_id

st.set_page_config(page_title="Gestor Financeiro", page_icon="💸", layout="wide")

# exige login e cria sessão se necessário
require_login()
uid = current_user_id()

st.sidebar.success("Autenticado!")
st.title("💸 Gestor de Finanças Pessoais & Familiares")
st.write("Use o menu lateral para navegar: Importar, Dashboard, Lançamentos, Regras, Orçamentos e Metas, Configurações.")
