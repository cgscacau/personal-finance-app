import streamlit as st
from app.auth import require_login, ensure_session

st.set_page_config(page_title="Gestor Financeiro", page_icon="💸", layout="wide")
ensure_session()
require_login()

st.sidebar.success("Autenticado!")
st.title("💸 Gestor de Finanças Pessoais & Familiares")
st.write("Use o menu lateral para navegar: importar, dashboard, lançamentos, regras, orçamentos e metas, configurações.")
