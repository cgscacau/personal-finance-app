import streamlit as st
from app.auth import require_login, current_user_id

st.title("⚙️ Configurações")
require_login()
st.write("Por enquanto, centralize **SUPABASE_URL** e **SUPABASE_ANON_KEY** em *Secrets* do Streamlit.")
st.code("""
# .streamlit/secrets.toml (não comitar)
SUPABASE_URL = "https://<your-project>.supabase.co"
SUPABASE_ANON_KEY = "<anon-key>"
""", language="toml")
