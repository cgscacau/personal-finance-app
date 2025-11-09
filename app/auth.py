import streamlit as st
from supabase import create_client
import os

def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]  # use service_role só no backend seguro
    return create_client(url, key)

def sign_in(email: str, password: str):
    supa = get_supabase()
    res = supa.auth.sign_in_with_password({"email": email, "password": password})
    return res

def sign_up(email: str, password: str):
    supa = get_supabase()
    res = supa.auth.sign_up({"email": email, "password": password})
    return res

def ensure_session():
    if "session" not in st.session_state:
        st.session_state.session = None

def require_login():
    ensure_session()
    if st.session_state.session is None:
        with st.form("login"):
            st.subheader("🔒 Acesso")
            email = st.text_input("Email", "")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            if submitted:
                try:
                    res = sign_in(email, password)
                    st.session_state.session = res
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha no login: {e}")
        st.stop()

def current_user_id():
    if st.session_state.session is None:
        return None
    return st.session_state.session.user.id


st.write("---")
st.subheader("Ainda não tem conta?")
email_signup = st.text_input("Novo email")
password_signup = st.text_input("Nova senha", type="password")
if st.button("Criar conta"):
    try:
        res = sign_up(email_signup, password_signup)
        st.success("Conta criada! Verifique seu e-mail e faça login.")
    except Exception as e:
        st.error(f"Erro ao criar conta: {e}")

